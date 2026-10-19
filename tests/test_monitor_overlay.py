import sys,unittest,gzip
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import patch_monitor_overlay as p
from pack_overlay import newc
from build_mod_overlay import unpack
class MonitorOverlay(unittest.TestCase):
 def blob(self,hook=True):
  rows=[('sbin/init',b'guard\n/qts-profile/mods/start\n' if hook else b'other',0o100755),('qts-profile/mods/reconcile.py',b'old',0o100644),('qts-profile/mods/start',b'old',0o100644),('qts-profile/mods/profile.json',b'private profile',0o100600),('qts-profile/model.conf',b'disk map',0o100644),('TRAILER!!!',b'',0)]
  return gzip.compress(b''.join(newc(n,d,m,i) for i,(n,d,m) in enumerate(rows)))
 def test_only_two_sources_change(self):
  base=self.blob();result,report=p.patch_monitor(base);old={n:(d,m) for n,d,m in unpack(base)};new={n:(d,m) for n,d,m in unpack(result)}
  self.assertEqual(set(old),set(new))
  self.assertEqual(sorted(n for n in old if old[n]!=new[n]),report['modified'])
  self.assertEqual(len(report['modified']),2)
  for n in old:self.assertEqual(old[n][1],new[n][1])
 def test_missing_hook_rejected(self):
  with self.assertRaises(ValueError):p.patch_monitor(self.blob(False))
if __name__=='__main__':unittest.main()
