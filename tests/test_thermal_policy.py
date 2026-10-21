import importlib.util,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
PKG=Path(__file__).resolve().parents[1]/'tools'/'qts-mods'
sys.path.insert(0,str(PKG));import thermal as t
import patch_thermal_overlay as overlay
from build_mod_overlay import unpack
from pack_overlay import newc
import gzip
CONFIG=b'[SHUTDOWN TEMP]\nCPU_TEMP = 85\nSYS_TEMP = 70\nDISK_TEMP = 60\nPOWER_TEMP = 55\n'
class Thermal(unittest.TestCase):
 def test_exact_cpu_only_and_idempotent(self):
  data=CONFIG+b'\n[Other]\nCPU_TEMP = 25\n'
  want=data.replace(b'CPU_TEMP = 85',b'CPU_TEMP = 90')
  self.assertEqual(t.desired(data),want);self.assertEqual(t.desired(want),want)
 def test_incompatible_inputs_refused(self):
  for data in [CONFIG.replace(b'70',b'71'),CONFIG.replace(b'85',b'91'),CONFIG+b'CPU_TEMP = 85\n',CONFIG+b'NEW_TEMP = 50\n',CONFIG.replace(b'POWER_TEMP = 55\n',b''),CONFIG+CONFIG]:
   with self.assertRaises(t.m.Skip):t.desired(data)
 def test_no_restart_if_already_loaded(self):
  with patch.object(t,'gate',return_value=('5.2.10',50000)),patch.object(t.m,'read',return_value=t.desired(CONFIG)),patch.object(t,'loaded',return_value=True),patch.object(t,'restart') as restart:
   self.assertEqual(t.apply()['state'],'ok');restart.assert_not_called()
 def test_sensor_block_does_not_block_thermal_and_failure_restores(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'hal_util.conf';p.write_bytes(CONFIG);(Path(d)/'sensors.blocked').write_text('existing')
   calls=[]
   def restart(cpu):
    calls.append((cpu,p.read_bytes()))
    if cpu==90:raise t.m.Skip('failed-load')
   with patch.object(t,'CONFIG',str(p)),patch.object(t,'BACKUPS',d+'/backups'),patch.object(t.m,'STATE',d),patch.object(t,'gate',return_value=('5.2.10',50000)),patch.object(t,'restart',side_effect=restart):
    with self.assertRaisesRegex(t.m.Skip,'original threshold and monitor restored'):t.apply()
   self.assertEqual(p.read_bytes(),CONFIG);self.assertEqual(calls,[(90,t.desired(CONFIG)),(85,CONFIG)])
   self.assertTrue((Path(d)/'thermal.blocked').exists())
   self.assertEqual((Path(d)/'sensors.blocked').read_text(),'existing')
 def test_readiness_check_does_not_write_or_restart(self):
  with patch.object(t,'gate',return_value=('5.2.10',50000)),patch.object(t.m,'read',return_value=CONFIG),patch.object(t.m,'atomic') as write,patch.object(t,'restart') as restart:
   self.assertEqual(t.apply(True)['cpu_after'],90);write.assert_not_called();restart.assert_not_called()
 def test_overlay_preserves_every_unrelated_member(self):
  rows=[('sbin/init',b'/qts-profile/mods/start\n',0o100755),('qts-profile/mods/start',b'header\n'+overlay.ANCHOR,0o100644),('qts-profile/mods/reconcile.py',b'unchanged pending sensor code',0o100644),('qts-profile/model.conf',b'disk mappings',0o100644)]
  base=gzip.compress(b''.join(newc(n,d,mode,i) for i,(n,d,mode) in enumerate(rows+[('TRAILER!!!',b'',0)])))
  blob,report=overlay.patch_thermal(base);new={n:(d,mode) for n,d,mode in unpack(blob)}
  for n,data,mode in rows:
   if n not in ('qts-profile/mods/start','qts-profile/mods/reconcile.py'):self.assertEqual(new[n],(data,mode))
  self.assertEqual(new['qts-profile/mods/reconcile.py'][0],(PKG/'reconcile.py').read_bytes())
  self.assertIn('qts-profile/mods/native_start_window.py',new)
  self.assertIn('qts-profile/mods/sensors.pending',new)
  self.assertEqual(new['qts-profile/mods/start'][0].count(overlay.HOOK),1)
  again,_=overlay.patch_thermal(blob);self.assertEqual(blob,again)
 def test_validated_sensor_overlay_removes_pending_preserves_unrelated(self):
  rows=[('sbin/init',b'/qts-profile/mods/start\n',0o100755),('qts-profile/mods/start',overlay.HOOK+overlay.ANCHOR,0o100644),('qts-profile/mods/sensors.pending',b'pending',0o100644),('qts-profile/model.conf',b'original disk mapping',0o100644)]
  base=gzip.compress(b''.join(newc(n,d,mode,i) for i,(n,d,mode) in enumerate(rows+[('TRAILER!!!',b'',0)])))
  blob,report=overlay.patch_thermal(base,True);new={n:(d,mode) for n,d,mode in unpack(blob)}
  self.assertNotIn('qts-profile/mods/sensors.pending',new)
  self.assertEqual(new['qts-profile/model.conf'],(b'original disk mapping',0o100644))
  self.assertEqual(new['qts-profile/mods/ipmitool'][1],0o100755)
  self.assertEqual(new['qts-profile/mods/kcs_read.py'][0],(PKG/'kcs_read.py').read_bytes())
  self.assertTrue(report['sensor_policy_enabled'])
  self.assertEqual(new['qts-profile/mods/start'][0].count(overlay.HOOK),1)
if __name__=='__main__':unittest.main()
