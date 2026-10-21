import errno,fcntl,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'qts-mods'))
import kcs_read as k
class Lock(unittest.TestCase):
 def test_competing_reader_can_finish_before_deadline(self):
  with tempfile.NamedTemporaryFile() as f:
   script='import fcntl,sys,time;f=open(sys.argv[1],"r+");fcntl.flock(f,fcntl.LOCK_EX);print("ready",flush=True);time.sleep(.12)'
   child=subprocess.Popen([sys.executable,'-c',script,f.name],stdout=subprocess.PIPE,text=True)
   try:
    self.assertEqual(child.stdout.readline().strip(),'ready')
    start=time.monotonic();k.acquire_lock(f.fileno());elapsed=time.monotonic()-start
    self.assertGreater(elapsed,.05);self.assertLess(elapsed,.5)
   finally:child.wait();child.stdout.close()
 def test_busy_lock_timeout_never_touches_hardware(self):
  with tempfile.NamedTemporaryFile() as f:
   other=open(f.name,'r+')
   try:
    fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
    start=time.monotonic()
    with self.assertRaisesRegex(RuntimeError,'bounded lock wait'):k.acquire_lock(f.fileno())
    self.assertLess(time.monotonic()-start,.7)
   finally:other.close()
 def test_unrelated_lock_error_is_not_retried(self):
  with patch.object(k.fcntl,'flock',side_effect=OSError(errno.EBADF,'bad descriptor')) as flock:
   with self.assertRaises(OSError):k.acquire_lock(-1)
   self.assertEqual(flock.call_count,1)
