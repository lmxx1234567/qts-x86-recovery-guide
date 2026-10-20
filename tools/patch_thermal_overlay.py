#!/usr/bin/env python3
"""Add independent CPU policy, its bounded lifecycle, and startup invocation."""
import gzip,hashlib
from build_mod_overlay import unpack,PKG
from pack_overlay import newc,regular
ANCHOR=b'   exec /usr/local/bin/python /qts-profile/mods/reconcile.py\n'
HOOK=b'   /usr/local/bin/python /qts-profile/mods/thermal.py\n'
def patch_thermal(base,validated_sensors=False):
 entries=unpack(base);old={n:d for n,d,mode in entries}
 if old.get('sbin/init',b'').count(b'/qts-profile/mods/start')!=1:raise ValueError('Missing unified hook')
 start=old['qts-profile/mods/start']
 if start.count(ANCHOR)!=1:raise ValueError('Unknown startup handoff')
 if HOOK not in start:start=start.replace(ANCHOR,HOOK+ANCHOR)
 if start.count(HOOK)!=1:raise ValueError('Duplicate thermal hook')
 replacements={
  'qts-profile/mods/thermal.py':regular(PKG/'thermal.py'),
  'qts-profile/mods/reconcile.py':regular(PKG/'reconcile.py'),
  'qts-profile/mods/native_start_window.py':regular(PKG/'native_start_window.py'),
  'qts-profile/mods/sensors.pending':b'Sensor cache contract pending validation; no automatic activation.\n'}
 if validated_sensors:
  del replacements['qts-profile/mods/sensors.pending']
  for name in ['probe.py','kcs_read.py','ipmitool']:replacements['qts-profile/mods/'+name]=regular(PKG/name)
 rows=[(n,start if n=='qts-profile/mods/start' else d,mode) for n,d,mode in entries if n not in replacements and not (validated_sensors and n=='qts-profile/mods/sensors.pending')]
 rows.extend((n,d,0o100755 if n.endswith('/ipmitool') else 0o100644) for n,d in sorted(replacements.items()))
 result=gzip.compress(b''.join(newc(n,d,mode,i+1) for i,(n,d,mode) in enumerate(rows+[('TRAILER!!!',b'',0)])),mtime=0)
 return result,{'base_sha256':hashlib.sha256(base).hexdigest(),'sha256':hashlib.sha256(result).hexdigest(),'modified':['qts-profile/mods/start']+sorted(replacements),'removed':['qts-profile/mods/sensors.pending'] if validated_sensors else [],'sensor_policy_enabled':validated_sensors,'other_members_unchanged':True,'reboot_tested':False,'upgrade_tested':False}
if __name__=='__main__':
 import argparse,json
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--validated-sensors',action='store_true');a=p.parse_args()
 blob,report=patch_thermal(regular(a.base),a.validated_sensors)
 with a.output.open('xb') as f:f.write(blob)
 a.output.with_suffix('.review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
