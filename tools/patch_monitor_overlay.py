#!/usr/bin/env python3
"""Refresh only monitor recovery sources in an existing reviewed unified overlay.
Builds a new archive; never mounts or writes a boot device.
"""
import argparse,gzip,hashlib,json,stat
from pathlib import Path
from build_mod_overlay import unpack,PKG
from pack_overlay import newc,regular
FILES=('reconcile.py','start')
def patch_monitor(base):
 entries=unpack(base);old={n:d for n,d,m in entries}
 if old.get('sbin/init',b'').count(b'/qts-profile/mods/start')!=1:
  raise ValueError('Expected existing unified startup hook')
 replacements={}
 for name in FILES:
  key='qts-profile/mods/'+name
  if key not in old:raise ValueError('Missing monitor source: '+key)
  replacements[key]=regular(PKG/name)
 updated=[(n,replacements.get(n,d),mode) for n,d,mode in entries]
 for (n,d,mode),(newname,newdata,newmode) in zip(entries,updated):
  assert n==newname and mode==newmode
  if n not in replacements:assert d==newdata
 result=gzip.compress(b''.join(newc(n,d,mode,i+1) for i,(n,d,mode) in enumerate(updated+[('TRAILER!!!',b'',0)])),mtime=0)
 return result,{'base_sha256':hashlib.sha256(base).hexdigest(),'sha256':hashlib.sha256(result).hexdigest(),'modified':sorted(replacements),'other_members_unchanged':True,'cold_boot_verified':False}
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--base',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();result,report=patch_monitor(regular(args.base))
 with args.output.open('xb') as f:f.write(result)
 args.output.with_suffix('.review.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
