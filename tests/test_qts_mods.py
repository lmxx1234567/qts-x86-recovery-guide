import importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
PKG=Path(__file__).resolve().parents[1]/'tools'/'qts-mods'
spec=importlib.util.spec_from_file_location('qts_mods',PKG/'reconcile.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Mods(unittest.TestCase):
 def test_ini_preserves_disk_sections(self):
  s='[System Enclosure]\nMAX_FAN_NUM = 0\n[System Disk 1]\nDEV_PORT = 4\n'
  new=m.setfields(s,'System Enclosure',{'MAX_FAN_NUM':'2'},{'MAX_FAN_NUM':['0','2']})
  self.assertEqual(m.fields(new,'System Disk 1'),m.fields(s,'System Disk 1'));self.assertEqual(m.setfields(new,'System Enclosure',{'MAX_FAN_NUM':'2'}),new)
 def test_ini_duplicates_and_unknown_values_rejected(self):
  with self.assertRaises(m.Skip):m.fields('[X]\na=1\na=2\n','X')
  with self.assertRaises(m.Skip):m.setfields('[X]\na=9\n','X',{'a':'2'},{'a':['0','2']})
 def test_duplicate_section_rejected(self):
  with self.assertRaises(m.Skip):m.sections('[X]\na=1\n[X]\na=2\n')
 def test_widget_unknown_and_idempotent(self):
  with self.assertRaises(m.Skip):m.widget('new widget')
  s='if(QNAP.QOS.config.modelName==="TS-X82"){tmpColumns.push({dataIndex:".",header:"CPU" cls:"cpu-temperacure",dtCls:"show-by-platform"'
  self.assertEqual(m.widget(m.widget(s)),m.widget(s))
 def test_memory_handles_rederived(self):
  s='Handle 0x0030, DMI type 17, 92 bytes\nMemory Device\n Locator: DIMM 0\n Bank Locator: P0 CHANNEL A\n Size: No Module Installed\n\nHandle 0x0035, DMI type 17, 92 bytes\nMemory Device\n Locator: DIMM 1\n Bank Locator: P0 CHANNEL A\n Size: 32 GB\n'
  rows=m.dimms(s,[{'bank':'P0 CHANNEL A','locator':'DIMM '+str(i),'channel':1,'dimm':i+1} for i in range(2)])
  self.assertEqual([r['offset'] for r in rows],[0,5]);self.assertEqual(rows[1]['mb'],32768)
  with self.assertRaises(m.Skip):m.dimms(s,[{'bank':'other','locator':'DIMM 0','channel':1,'dimm':1}]*2)
 def test_cron_preserves_unrelated_and_deduplicates(self):
  old='17 */6 * * * /bin/sh /share/example/refresh.sh';new='17 */6 * * * /usr/local/bin/python /qts-profile/mods/refresh.py'
  s='# keep\n0 4 * * * /sbin/auto_update\n'+old+'\n'+old+'\n'
  out=m.cron_replace(s,old,new)
  self.assertIn('0 4 * * * /sbin/auto_update\n',out);self.assertEqual(out.count(new),1);self.assertEqual(m.cron_replace(out,old,new),out)
  with self.assertRaises(m.Skip):m.cron_replace('0 1 * * * /bin/sh /share/example/refresh.sh\n',old,new)
 def test_svg_validation(self):
  self.assertEqual(m.svg_ids(b'<svg><g id="hd_0"/></svg>'),{'hd_0'})
  with self.assertRaises(m.Skip):m.svg_ids(b'<html/>')
 def test_repository_validation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'index';p.write_text('<plugins><item><platform><platformID>TS-NASX86</platformID><location>https://example.com/x</location></platform></item></plugins>');self.assertEqual(m.valid_index(str(p)),1)
   p.write_text(p.read_text().replace('https://','http://'))
   with self.assertRaises(m.Skip):m.valid_index(str(p))
 def test_transaction_rollback(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m,'STATE',d):
   p=Path(d)/'config';p.write_bytes(b'original')
   def fail():raise m.Skip('probe failed')
   with self.assertRaises(m.Skip):m.transact('test',{str(p):b'new'},{str(p):b'original'},fail)
   self.assertEqual(p.read_bytes(),b'original');self.assertTrue((Path(d)/'test.blocked').exists())
 def test_transaction_read_only_and_mode(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m,'STATE',d):
   p=Path(d)/'config';p.write_bytes(b'old');p.chmod(0o640)
   m.transact('t',{str(p):b'new'},{str(p):b'old'},lambda:None,True)
   self.assertEqual(p.read_bytes(),b'old')
   m.transact('t',{str(p):b'new'},{str(p):b'old'},lambda:None)
   self.assertEqual(p.stat().st_mode&0o777,0o640)
 def test_concurrent_file_is_not_overwritten(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m,'STATE',d):
   p=Path(d)/'config';p.write_bytes(b'concurrent')
   with self.assertRaises(m.Skip):m.transact('t',{str(p):b'new'},{str(p):b'old'},lambda:None)
   self.assertEqual(p.read_bytes(),b'concurrent')
 def test_symlink_target_refused(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m,'STATE',d):
   p=Path(d)/'real';p.write_bytes(b'old');q=Path(d)/'link';q.symlink_to(p)
   with self.assertRaises(m.Skip):m.transact('t',{str(q):b'new'},{str(q):b'old'},lambda:None)
   self.assertEqual(p.read_bytes(),b'old')
 def test_probe_timeout(self):
  with self.assertRaises(m.Skip):m.run([sys.executable,'-c','import time; time.sleep(2)'],.05)
 def test_module_failure_does_not_stop_others(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m,'STATE',d),patch.object(m,'BASE',d),patch.object(m.os,'geteuid',return_value=os.geteuid()),patch.object(m,'notify') as notify,patch.object(m.Context,'gate'):
   (Path(d)/'profile.json').write_text('{}');patches=[];called=[]
   for name in m.MODULES:
    def call(c,n=name):
     called.append(n)
     if n=='sensors':raise m.Skip('interface changed')
     return {'state':'ok','changed':[]}
    pp=patch.object(m.Context,name,call);pp.start();patches.append(pp)
   try:
    with patch.object(m.os,'geteuid',return_value=0),patch.object(m,'private_dir'),patch.object(sys,'argv',['reconcile.py']):self.assertEqual(m.main(),1)
   finally:
    for p in patches:p.stop()
   self.assertEqual(called,m.MODULES);self.assertEqual(notify.call_count,1)
 def test_no_installer_or_privilege_restoration(self):
  for name in ['reconcile.py','refresh.py','start']:
   s=(PKG/name).read_text()
   self.assertNotIn('/sbin/reboot',s);self.assertNotIn('/sbin/auto_update',s);self.assertNotIn('/usr/etc/sudoers',s);self.assertNotIn('mkfs',s)

class MemoryRecovery(unittest.TestCase):
 def exercise(self,fail):
  with tempfile.TemporaryDirectory() as d,patch.object(m,'STATE',d):
   model=Path(d)/'model';platform=Path(d)/'platform'
   model.write_text('[System Memory]\nMAX_CHANNEL_NUM = 1\nMAX_SLOT_NUM = 1\n[System Disk 1]\nDEV_PORT = 7\n')
   platform.write_text('[Unrelated]\nkeep = yes\n[DIMM 1]\nvalid = 0\nslot_addr = 0x0\n')
   before=model.read_text();old_platform=platform.read_text()
   rows=[{'offset':0,'channel':1,'dimm':1,'mb':0},{'offset':2,'channel':1,'dimm':2,'mb':32768}]
   c=m.Context({'memory_slots':[]},False)
   def probe(mode,*args):
    if mode=='memory':
     platform.write_text('[Unrelated]\nkeep = yes\n[DIMM 1]\nslot_addr = 0x0\nchannel_id = 1\n[DIMM 2]\nslot_addr = 0x2\nchannel_id = 1\nsize = '+('0' if fail else '32768')+'\n')
    return {}
   with patch.object(m,'MODEL',str(model)),patch.object(m,'PLATFORM',str(platform)),patch.object(m,'dimms',return_value=rows),patch.object(m,'run',return_value='fixture'),patch.object(c,'probe',side_effect=probe):
    if fail:
     with self.assertRaises(m.Skip):c.memory()
     self.assertEqual(model.read_text(),before)
     self.assertEqual(m.fields(platform.read_text(),'DIMM 1'),m.fields(old_platform,'DIMM 1'))
     self.assertNotIn('DIMM 2',m.sections(platform.read_text()))
    else:
     self.assertEqual(c.memory()['state'],'restored')
     self.assertEqual(m.fields(model.read_text(),'System Memory')['SLOT2_ADDR'],'1-2, 0x2')
    self.assertEqual(m.fields(model.read_text(),'System Disk 1'),{'DEV_PORT':'7'})
    self.assertEqual(m.fields(platform.read_text(),'Unrelated'),{'keep':'yes'})
 def test_neutral_memory_profile_restored(self):self.exercise(False)
 def test_hal_cache_side_effects_rolled_back(self):self.exercise(True)

class OverlayBuilder(unittest.TestCase):
 def test_boot_guards_preserved_and_legacy_helper_removed(self):
  sys.path.insert(0,str(PKG.parent))
  import build_mod_overlay as b
  from pack_overlay import newc
  init=b'#!/bin/sh\n# guard\n[ "$serial" = expected ] || exit 1\n/sbin/dmsetup create dom --table "$mapping"\n/bin/busybox sh /qts-profile/apply-preview &\nexec /bin/busybox init\n'
  model=b'[System Enclosure]\nSYSTEM_DISK_CACHEABLE_BITMAP = 0x1FE\n[System Disk 1]\nDEV_PORT = 4\n[System Memory]\nMAX_CHANNEL_NUM = 2\nMAX_SLOT_NUM = 4\n'
  import gzip
  blob=gzip.compress(b''.join(newc(n,data,mode,i) for i,(n,data,mode) in enumerate([('qts-profile',b'',0o40755),('qts-profile/model.conf',model,0o100644),('sbin',b'',0o40755),('sbin/init',init,0o100755),('TRAILER!!!',b'',0)])))
  profile={'format':1,'enabled':True,'protected_sections':{'System Disk 1':{'DEV_PORT':'4'}},'artwork':[]}
  with tempfile.TemporaryDirectory() as d:built,report=b.build(blob,profile,Path(d))
  entries={n:data for n,data,mode in b.unpack(built)}
  self.assertIn(b'[ "$serial" = expected ] || exit 1',entries['sbin/init'])
  self.assertIn(b'/sbin/dmsetup create dom --table "$mapping"',entries['sbin/init'])
  self.assertNotIn(b'apply-preview &',entries['sbin/init'])
  self.assertEqual(entries['sbin/init'].count(b'/qts-profile/mods/start'),1)
  self.assertEqual(m.fields(entries['qts-profile/model.conf'].decode(),'System Disk 1'),{'DEV_PORT':'4'})
  self.assertEqual(m.fields(entries['qts-profile/model.conf'].decode(),'System Enclosure')['SYSTEM_DISK_CACHEABLE_BITMAP'],'0x0')

if __name__=='__main__':unittest.main()
