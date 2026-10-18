#!/usr/bin/env python3
"""Inspect/copy GPT partitions in regular image files only (512-byte sectors)."""
import argparse, json, os, stat, struct, uuid, zlib
from pathlib import Path
SECTOR=512

def open_regular(path, writable=False):
    flags=(os.O_RDWR if writable else os.O_RDONLY)|os.O_NOFOLLOW|os.O_NONBLOCK
    fd=os.open(path,flags)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd);raise ValueError('Only regular files are accepted; never block devices')
    return os.fdopen(fd,'r+b' if writable else 'rb')

def geometry(f):
    total=os.fstat(f.fileno()).st_size
    f.seek(SECTOR);h=bytearray(f.read(SECTOR))
    if len(h)!=512 or h[:8]!=b'EFI PART':raise ValueError('Expected 512-byte-sector GPT image')
    n,crc=struct.unpack_from('<II',h,12)
    if not 92<=n<=512:raise ValueError('Invalid header length')
    h[16:20]=b'\0'*4
    if zlib.crc32(h[:n])!=crc:raise ValueError('GPT header CRC mismatch')
    current,backup,first,last=struct.unpack_from('<QQQQ',h,24)
    lba,count,size,tablecrc=struct.unpack_from('<QIII',h,72)
    if current!=1 or backup*512>=total or first>last or last>=backup:
        raise ValueError('GPT bounds invalid')
    if count<1 or count>4096 or size<128 or size>4096 or size%8:
        raise ValueError('GPT table dimensions invalid')
    if lba<2 or lba*512+count*size>first*512:raise ValueError('GPT table bounds invalid')
    f.seek(lba*512);table=f.read(count*size)
    if len(table)!=count*size or zlib.crc32(table)!=tablecrc:raise ValueError('GPT table CRC mismatch')
    parts={}
    for i in range(count):
        e=table[i*size:(i+1)*size]
        if e[:16]==b'\0'*16:continue
        start,end=struct.unpack_from('<QQ',e,32)
        if not first<=start<=end<=last:raise ValueError('Partition outside usable range')
        parts[i+1]={'start':start,'sectors':end-start+1,'bytes':(end-start+1)*512,
                    'guid':str(uuid.UUID(bytes_le=e[16:32]))}
    ordered=sorted(parts.values(),key=lambda p:p['start'])
    for a,b in zip(ordered,ordered[1:]):
        if a['start']+a['sectors']>b['start']:raise ValueError('Overlapping partitions')
    return parts

def transfer(src,dst,n):
    while n:
        data=src.read(min(n,1024*1024))
        if not data:raise ValueError('Unexpected short read')
        dst.write(data);n-=len(data)

def extract(image,number,output):
    with open_regular(image) as f:
        p=geometry(f)[number];f.seek(p['start']*512)
        with open(output,'xb') as out:transfer(f,out,p['bytes'])

def replace(image,number,input_path):
    with open_regular(image,True) as f,open_regular(input_path) as src:
        if os.path.samefile(image,input_path):raise ValueError('Source and destination are identical')
        p=geometry(f)[number]
        if os.fstat(src.fileno()).st_size!=p['bytes']:raise ValueError('Replacement must have exact partition length')
        f.seek(p['start']*512);transfer(src,f,p['bytes']);f.flush();os.fsync(f.fileno())
        src.seek(0);f.seek(p['start']*512);remaining=p['bytes']
        while remaining:
            n=min(remaining,1024*1024)
            if f.read(n)!=src.read(n):raise ValueError('Readback mismatch')
            remaining-=n

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('inspect');a.add_argument('image')
    for name in ['extract','replace']:
        a=sub.add_parser(name);a.add_argument('image');a.add_argument('partition',type=int);a.add_argument('file')
    a=p.parse_args()
    if a.action=='inspect':
        with open_regular(a.image) as f:print(json.dumps(geometry(f),indent=2))
    elif a.action=='extract':extract(a.image,a.partition,a.file)
    else:replace(a.image,a.partition,a.file)
if __name__=='__main__':main()
