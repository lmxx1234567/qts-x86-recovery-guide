#!/usr/bin/env python3
"""Build only: preserve reviewed early boot guards, install one-shot mod sources.
Private profile, vendor artwork and an existing host overlay must be supplied.
Never mounts disks, installs firmware, or reboots.
"""
import argparse,gzip,hashlib,json,stat,sys
from pathlib import Path
from pack_overlay import newc,regular
PKG=Path(__file__).resolve().parent/'qts-mods'
sys.path.insert(0,str(PKG))
import reconcile as mods
FILES=['reconcile.py','probe.py','kcs_read.py','ipmitool','refresh.py','start']

def unpack(blob):
 b=gzip.decompress(blob);o=0;entries=[];seen=set()
 while o+110<=len(b):
  h=b[o:o+110]
  if h[:6]!=b'070701':raise ValueError('Expected newc archive')
  a=[int(h[6+i*8:14+i*8],16) for i in range(13)]
  end=o+110+a[11];name=b[o+110:end-1].decode();start=(end+3)&~3;data=b[start:start+a[6]];o=(start+a[6]+3)&~3
  if name=='TRAILER!!!':return entries
  if name.startswith('/') or '..' in name.split('/') or name in seen:raise ValueError('Unsafe/duplicate entry')
  if not (stat.S_ISREG(a[1]) or stat.S_ISDIR(a[1])):raise ValueError('Unexpected archive member type')
  if len(data)!=a[6]:raise ValueError('Truncated entry')
  seen.add(name);entries.append((name,data,a[1]))
 raise ValueError('Missing trailer')
def build(base,profile,assets):
 entries=unpack(base);old={n:d for n,d,m in entries}
 if profile.get('format')!=1 or profile.get('enabled') is not True:raise ValueError('Private host profile not enabled')
 model=old['qts-profile/model.conf'].decode()
 for n,fields in profile['protected_sections'].items():
  if mods.fields(model,n)!=fields:raise ValueError('Base mapping differs: '+n)
 # Optional memory/cache features start neutral and are gated after QTS starts.
 model=mods.remove_sections(model,['System Memory'])+'\n[System Memory]\nMAX_CHANNEL_NUM = 1\nMAX_SLOT_NUM = 1\n'
 model=mods.setfields(model,'System Enclosure',{'SYSTEM_DISK_CACHEABLE_BITMAP':'0x0'})
 for n,fields in profile['protected_sections'].items():assert mods.fields(model,n)==fields
 init=old['sbin/init'];anchor=b'exec /bin/busybox init'
 if init.count(anchor)!=1:raise ValueError('Unknown init handoff')
 legacy=[b'/bin/busybox sh /qts-profile/apply-preview &\n',b'/bin/busybox sh /qts-profile/sensor-check/start > /tmp/qts-sensor-start.log 2>&1 &\n']
 cleaned=init
 for line in legacy:cleaned=cleaned.replace(line,b'')
 launch=b'/bin/busybox sh /qts-profile/mods/start > /tmp/qts-mods-start.log 2>&1 &\n'
 if b'/qts-profile/mods/start' in cleaned:raise ValueError('Already has unified hook; use reviewed base')
 updated=cleaned.replace(anchor,launch+anchor)
 assert updated.replace(launch,b'')==cleaned
 replacement={'sbin/init':updated,'qts-profile/model.conf':model.encode()}
 entries=[(n,replacement.get(n,d),m) for n,d,m in entries if not n.startswith('qts-profile/sensor-check/') and n!='qts-profile/sensor-check']
 entries.append(('qts-profile/mods',b'',0o40700))
 for n in FILES:entries.append(('qts-profile/mods/'+n,regular(PKG/n),0o100644))
 entries.append(('qts-profile/mods/profile.json',(json.dumps(profile,indent=2)+'\n').encode(),0o100600))
 entries.append(('qts-profile/mods/assets',b'',0o40700))
 for art in profile['artwork']:
  n=art['asset']
  if not n.startswith('assets/') or len(Path(n).parts)!=2:raise ValueError('Invalid asset path')
  data=regular(assets/Path(n).name)
  if hashlib.sha256(data).hexdigest()!=art['sha256']:raise ValueError('Asset hash mismatch')
  entries.append(('qts-profile/mods/'+n,data,0o100644))
 names=[n for n,d,m in entries]
 if len(names)!=len(set(names)):raise ValueError('Duplicate output name')
 entries.append(('TRAILER!!!',b'',0))
 result=gzip.compress(b''.join(newc(n,d,m,i+1) for i,(n,d,m) in enumerate(entries)),mtime=0)
 return result,{'sha256':hashlib.sha256(result).hexdigest(),'base_sha256':hashlib.sha256(base).hexdigest(),'modified':['sbin/init: replace legacy optional helpers with one-shot hook','qts-profile/model.conf: neutral optional memory/cache defaults'],'protected_mapping_unchanged':True,'early_guard_code_unchanged':True,'package_files':FILES,'firmware_install':False,'automatic_reboot':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',required=True,type=Path);p.add_argument('--profile',required=True,type=Path);p.add_argument('--assets',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 result,report=build(regular(a.base),json.loads(a.profile.read_text()),a.assets)
 with a.output.open('xb') as f:f.write(result)
 a.output.with_suffix('.review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
