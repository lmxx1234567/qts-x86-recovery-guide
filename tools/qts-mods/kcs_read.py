#!/usr/local/bin/python
# Read-only IPMI commands over this board's SMBIOS-declared KCS port.
from __future__ import print_function
import os,sys,time,fcntl
BASE=0xca2
ALLOWED={(6,1),(4,0x2d),(4,0x23)}
def command(netfn,cmd,args):
    if (netfn,cmd) not in ALLOWED: raise ValueError('Read-only command allowlist')
    if os.path.exists('/dev/ipmi0') or os.path.exists('/dev/ipmi/0'):
        raise RuntimeError('Kernel IPMI interface detected; direct KCS disabled')
    lock=os.open('/var/lock/qts-sensor-kcs.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except IOError:
        os.close(lock);raise RuntimeError('KCS reader busy; try next sample')
    fd=os.open('/dev/port',os.O_RDWR)
    deadline=time.time()+3
    def rd(port):
        os.lseek(fd,port,0);return ord(os.read(fd,1))
    def wr(port,value):
        os.lseek(fd,port,0);os.write(fd,bytes(bytearray([value])))
    def wait(obf=False):
        while time.time()<deadline:
            s=rd(BASE+1)
            if s==255: raise RuntimeError('KCS unavailable')
            if not s&2 and (not obf or s&1): return s
            time.sleep(.001)
        raise RuntimeError('KCS timeout; no retries or reset attempted')
    def writing():
        s=wait()
        if s&0xc0!=0x80: raise RuntimeError('Unexpected KCS write state')
        if s&1: rd(BASE)
    try:
        s=wait()
        if s&0xc0: raise RuntimeError('KCS busy; refusing to interrupt existing transaction')
        if s&1: rd(BASE)
        packet=[netfn<<2,cmd]+args
        wr(BASE+1,0x61);writing()
        for x in packet[:-1]: wr(BASE,x);writing()
        wr(BASE+1,0x62);writing();wr(BASE,packet[-1])
        out=[]
        while True:
            s=wait()
            if s&0xc0==0:
                if s&1: rd(BASE)
                break
            if s&0xc0!=0x40: raise RuntimeError('Unexpected KCS read state')
            wait(True);out.append(rd(BASE));wr(BASE,0x68)
            if len(out)>256: raise RuntimeError('Oversized reply')
        if len(out)<3 or out[:2]!=[(netfn+1)<<2,cmd] or out[2]: raise RuntimeError('Bad IPMI reply '+repr(out))
        return out[3:]
    finally: os.close(fd);os.close(lock)
if __name__=='__main__':
    vals=[int(x,0) for x in sys.argv[1:]]
    print(' '.join('%02x'%x for x in command(vals[0],vals[1],vals[2:])))
