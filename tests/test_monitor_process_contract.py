"""Real local processes exercising the synchronous manager/daemon boundary.

These fixtures model the observed control flow, not QTS or hardware behavior.
No NAS commands, devices, configuration, or network access.
"""
import importlib.util
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

PKG=Path(__file__).resolve().parents[1]/'tools'/'qts-mods'
spec=importlib.util.spec_from_file_location('process_contract',PKG/'reconcile.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

@unittest.skipUnless(hasattr(os,'fork'),'POSIX process contract')
class ProcessContract(unittest.TestCase):
 def stop_child(self,path):
  if path.exists():
   try:os.kill(int(path.read_text()),signal.SIGKILL)
   except ProcessLookupError:pass

 def test_detached_writer_does_not_hold_command_open(self):
  with tempfile.TemporaryDirectory() as folder:
   pid=Path(folder)/'pid'
   # Child deliberately retains stdout/stderr; parent exits like daemonization.
   code="""import os,sys,time
p=os.fork()
if p:
 open(sys.argv[1],'w').write(str(p))
 sys.exit(1)
os.setsid()
print('child-ready',flush=True)
time.sleep(10)
"""
   try:
    rc,out=m.run_result([sys.executable,'-u','-c',code,str(pid)],2,kill_group=False)
    self.assertEqual(rc,1)
    os.kill(int(pid.read_text()),0)  # It really is alive after command return.
   finally:self.stop_child(pid)

 def test_sync_wait_times_out_even_when_child_pid_exists(self):
  with tempfile.TemporaryDirectory() as folder:
   pid=Path(folder)/'pid'
   code="""import os,sys,time
p=os.fork()
if p:
 open(sys.argv[1],'w').write(str(p))
 print('waiting-before-registration',flush=True)
 os.waitpid(p,0)
 sys.exit(1)
time.sleep(10)
"""
   events=[]
   def capture(root):
    # Executed before killing the manager client.
    os.kill(root,0)
    events.append(root)
    return [{'pid':root,'state':'S'}]
   try:
    with patch.object(m,'timeout_processes',side_effect=capture):
     with self.assertRaises(m.CommandTimeout) as caught:
      m.run_result([sys.executable,'-u','-c',code,str(pid)],.5,kill_group=False)
    self.assertEqual(len(events),1)
    self.assertEqual(caught.exception.processes,[{'pid':events[0],'state':'S'}])
    self.assertIn('waiting-before-registration',caught.exception.output)
    os.kill(int(pid.read_text()),0)  # Timeout must preserve prospective monitor.
   finally:self.stop_child(pid)

 def test_real_child_cannot_inherit_reconciler_lock(self):
  import fcntl
  with tempfile.TemporaryDirectory() as folder:
   lock=Path(folder)/'lock'
   with lock.open('w') as held:
    fcntl.flock(held,fcntl.LOCK_EX)
    os.set_inheritable(held.fileno(),True)  # Reproduce Python 2's default.
    code="""import os,sys
fd=int(sys.argv[1])
try:
 s=os.fstat(fd)
 print(s.st_dev,s.st_ino)
except OSError:print('closed')
"""
    rc,out=m.run_result([sys.executable,'-c',code,str(held.fileno())],2)
    identity='%s %s'% (os.fstat(held.fileno()).st_dev,os.fstat(held.fileno()).st_ino)
    self.assertEqual(rc,0)
    self.assertNotEqual(out.strip(),identity)

 def test_proc_snapshot_keeps_wait_chain_and_detached_hal_only(self):
  with tempfile.TemporaryDirectory() as folder:
   for pid,name,parent in [(20,'daemon_mgr',1),(21,'sh',20),(22,'helper',21),
                           (30,'hal_daemon',1),(40,'unrelated',1)]:
    p=Path(folder)/str(pid);p.mkdir()
    (p/'stat').write_text('%d (%s) S %d 0 0'%(pid,name,parent))
    (p/'wchan').write_text('do_wait\n')
    (p/'syscall').write_text('61 0xSECRET_ADDRESS 0xOTHER\n')
   result=m.timeout_processes(20,folder)
   self.assertEqual([r['pid'] for r in result],[20,21,22,30])
   self.assertTrue(all(r['syscall']=='61' for r in result))
   self.assertNotIn('SECRET',str(result))

 def test_diagnostic_error_does_not_prevent_timeout_cleanup(self):
  with patch.object(m,'timeout_processes',side_effect=OSError('unavailable')):
   with self.assertRaises(m.CommandTimeout) as caught:
    m.run_result([sys.executable,'-c','import time;time.sleep(10)'],.1,kill_group=False)
  self.assertEqual(caught.exception.processes,[])

if __name__=='__main__':unittest.main()
