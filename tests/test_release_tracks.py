import configparser,gzip,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from select_model import select
from prepare_release_overlay import prepare,HOOK
from build_mod_overlay import unpack
from pack_overlay import newc

def parsed(data):
 c=configparser.RawConfigParser();c.optionxform=str;c.read_string(data.decode())
 return {s:dict(c.items(s)) for s in c.sections()}
class ReleaseTracks(unittest.TestCase):
 def setUp(self):self.model=(ROOT/'templates/case-vm-model.conf').read_bytes()
 def test_family_change_preserves_all_nonidentity_settings(self):
  a=parsed(self.model);b=parsed(select(self.model,'x73a'))
  self.assertEqual(b['System Enclosure']['MODEL'],'TS-873A')
  for section in a:
   if section!='System Enclosure':self.assertEqual(a[section],b[section])
  for k,v in a['System Enclosure'].items():
   if k not in ('MODEL','CAP'):self.assertEqual(v,b['System Enclosure'][k])
 def test_idempotence_and_return_to_x77(self):
  beta=select(self.model,'x73a');self.assertEqual(select(beta,'x73a'),beta)
  self.assertEqual(parsed(select(beta,'x77')),parsed(self.model))
 def test_unknown_caps_rejected(self):
  with self.assertRaises(ValueError):select(self.model.replace(b'0x1414db1c',b'0x123'),'x73a')
 def test_duplicate_identity_rejected(self):
  with self.assertRaises(configparser.Error):select(self.model.replace(b'MODEL = TS-877',b'MODEL = TS-877\nMODEL = TS-873A'),'x73a')
 def blob(self,hook=HOOK):
  rows=[('sbin/init',b'identity guard\ngeometry guard\n'+hook+b'exec /bin/busybox init\n',0o100755),('qts-profile/model.conf',self.model,0o100644),('qts-profile/mods/start',b'old optional module',0o100644),('private-file',b'keep unchanged',0o100600),('TRAILER!!!',b'',0)]
  return gzip.compress(b''.join(newc(n,d,m,i) for i,(n,d,m) in enumerate(rows)))
 def test_existing_mods_require_explicit_choice(self):
  with self.assertRaises(ValueError):prepare(self.blob(),'x73a')
 def test_early_guards_and_other_members_preserved(self):
  old={n:(d,m) for n,d,m in unpack(self.blob())};blob,report=prepare(self.blob(),'x73a',True);new={n:(d,m) for n,d,m in unpack(blob)}
  self.assertEqual(old.keys(),new.keys());self.assertEqual(new['sbin/init'],(old['sbin/init'][0].replace(HOOK,b''),old['sbin/init'][1]))
  for name in old:
   if name not in ('sbin/init','qts-profile/model.conf'):self.assertEqual(old[name],new[name])
  self.assertTrue(report['known_optional_startup_disabled'])
 def test_unknown_hook_not_silently_removed(self):
  with self.assertRaises(ValueError):prepare(self.blob(b'/qts-profile/mods/start &\n'),'x73a',True)
 def test_plain_overlay_has_no_init_change(self):
  base=self.blob(b'');blob,report=prepare(base,'x73a')
  self.assertEqual(dict((n,d) for n,d,m in unpack(base))['sbin/init'],dict((n,d) for n,d,m in unpack(blob))['sbin/init'])
  self.assertFalse(report['known_optional_startup_disabled'])
 def test_all_guide_shell_examples_parse(self):
  import re,subprocess
  for path in [ROOT/'docs/02a-release-tracks.md',ROOT/'docs/11-qts61-upgrade.md']:
   for i,block in enumerate(re.findall(r'```(?:sh|bash)\n(.*?)```',path.read_text(),re.S)):
    result=subprocess.run(['bash','-n'],input=block,text=True,capture_output=True)
    self.assertEqual(result.returncode,0,str(path)+': '+str(i)+': '+result.stderr)
class Compatibility(unittest.TestCase):
 def setUp(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('release_compat',ROOT/'tools/qts-mods/reconcile.py')
  self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
 def test_new_release_keeps_identity_and_mapping_gates(self):
  from unittest.mock import patch
  m=self.m
  protected={s:{'value':s} for s in ['Boot Enclosure','Boot Disk 1','System Disk 1','System Network 1']}
  profile={'format':1,'enabled':True,'protected_sections':protected,'identity_tokens':['board','kcs'],'pci_paths':['/fixture']}
  for v in ['5.2.11','6.1.0','7.0.future']:
   def run(args):return v if args[-1]=='Version' else 'build' if args[-1]=='Build Number' else 'board kcs'
   with patch.object(m,'run',side_effect=run),patch.object(m,'txt',return_value='fixture'),patch.object(m,'fields',side_effect=lambda text,n:protected[n]),patch.object(m.os.path,'isdir',return_value=True),patch.object(m.os.path,'exists',return_value=False):
    c=m.Context(profile,True);c.gate();self.assertEqual(c.firmware,v+' build')
    with patch.object(m,'fields',return_value={'wrong':'mapping'}):
     with self.assertRaisesRegex(m.Skip,'Protected mapping changed'):c.gate()
 def test_modern_widget_is_not_patched(self):
  from unittest.mock import patch
  m=self.m
  with patch.object(m.os.path,'isfile',side_effect=lambda p:p!=m.WIDGET),patch.object(m,'txt',return_value='appendTempSensors( if(h.cpuTempC!=null) label:"CPU"'):
   self.assertEqual(m.Context({},True).cpu_widget()['state'],'native')
  with patch.object(m.os.path,'isfile',return_value=False):
   with self.assertRaises(m.Skip):m.Context({},True).cpu_widget()
 def test_missing_sensor_cache_does_not_block_other_modules(self):
  from unittest.mock import patch
  m=self.m
  with patch.object(m.os.path,'exists',return_value=False),patch.object(m.os.path,'isfile',side_effect=lambda p:p=='/etc/hal.conf'),patch.object(m,'process_ids',return_value=[1]),patch.object(m,'monitor_matches',return_value=True):
   self.assertTrue(m.startup_ready())

if __name__=='__main__':unittest.main()
