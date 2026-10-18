#!/usr/bin/env python3
"""Pack supplied, reviewed files. Does not access disks or validate hardware."""
import argparse, gzip, stat
from pathlib import Path

def regular(path):
    path = Path(path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError('Input must be a regular file, not a symlink/device')
    data = path.read_bytes()
    if b'REPLACE_' in data:
        raise ValueError('Unresolved template marker')
    return data

def newc(name, data, mode, ino):
    if name.startswith('/') or '..' in name.split('/'):
        raise ValueError('Unsafe archive path')
    n = name.encode() + b'\0'
    fields = [ino, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(n), 0]
    b = b'070701' + b''.join(f'{v:08x}'.encode() for v in fields) + n
    b += b'\0' * (-len(b) % 4)
    b += data
    return b + b'\0' * (-len(data) % 4)

def build(model, init):
    entries = [('qts-profile', b'', 0o40755), ('qts-profile/model.conf', model, 0o100644),
               ('sbin', b'', 0o40755), ('sbin/init', init, 0o100755), ('TRAILER!!!', b'', 0)]
    return gzip.compress(b''.join(newc(n,d,m,i+1) for i,(n,d,m) in enumerate(entries)), mtime=0)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True); p.add_argument('--init', required=True)
    p.add_argument('--output', required=True); a=p.parse_args()
    model, init=regular(a.model),regular(a.init)
    if not init.startswith(b'#!/bin/sh\n'):
        raise ValueError('Expected a POSIX shell init wrapper')
    result=build(model,init)
    with open(a.output,'xb') as f: f.write(result)
    print(f'Wrote {len(result)} bytes; hardware validation still required.')
if __name__=='__main__': main()
