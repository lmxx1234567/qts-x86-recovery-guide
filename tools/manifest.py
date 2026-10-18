#!/usr/bin/env python3
"""Hash explicitly named regular files; output includes private relative filenames."""
import argparse, hashlib, json, stat
from pathlib import Path

def record(root, name):
    root=Path(root).resolve(); p=(root/name).resolve()
    if not p.is_relative_to(root): raise ValueError('Path escapes root')
    if not stat.S_ISREG(p.stat().st_mode): raise ValueError('Not a regular file')
    before=p.stat(); h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    after=p.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ValueError('File changed during read')
    return {'size':after.st_size,'sha256':h.hexdigest()}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('root');p.add_argument('files',nargs='+')
    a=p.parse_args();print(json.dumps({n:record(a.root,n) for n in a.files},indent=2))
if __name__=='__main__': main()
