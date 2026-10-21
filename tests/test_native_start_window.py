import sys,unittest,copy,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'qts-mods'))
import native_start_window as w
import reconcile as m

def evidence():
 baseline={'hashes':dict(w.KNOWN),'architecture':'x86_64','registered':'stop','hal_pids':[],'service_mode':'0','queue_id':14}
 sample={'registered':'stop','hal_pids':[101],'service_mode':'0','queue_id':None,'processes':[
 {'pid':100,'ppid':99,'name':'daemon_mgr','state':'S','syscall':'61'},
 {'pid':101,'ppid':100,'name':'hal_daemon','state':'S','syscall':'35'}]}
 return baseline,sample
class NativeWindow(unittest.TestCase):
 def window(self):
  b,s=evidence();x=w.StartWindow(w.ARGS,b,100)
  x.observe(19.4,s);x.observe(19.8,s);return x
 def test_native_clear_ipc_non_stop_mode_takes_21_sleeps(self):
  # Model the captured post-increment CMP/JLE at 0x413c10..0x413c1c.
  count=0;sleeps=0
  while True:
   sleeps+=1;old=count;count+=1
   if old>19:break
  self.assertEqual(sleeps,21)
  x=self.window();self.assertFalse(x.expired(20));self.assertFalse(x.expired(sleeps))
  self.assertTrue(w.ready(1,'start',[102],[90],True,True))
 def test_no_unconditional_extension(self):
  b,s=evidence();x=w.StartWindow(w.ARGS,b,100)
  self.assertTrue(x.expired(20));x.observe(20.1,s);self.assertTrue(x.expired(20.1))
 def test_stop_and_unrelated_commands_never_extend(self):
  for args in [w.ARGS[:2]+['stop']+w.ARGS[3:],['helper']]:
   b,s=evidence();x=w.StartWindow(args,b,100);x.observe(19.4,s);x.observe(19.8,s)
   self.assertTrue(x.expired(20))
 def test_bad_or_stale_or_single_snapshot_fails_closed(self):
  for times in [(18,18.5),(19.9,),(19.8,19.9),(19.8,19.4)]:
   b,s=evidence();x=w.StartWindow(w.ARGS,b,100)
   for t in times:x.observe(t,s)
   self.assertTrue(x.expired(20))
 def test_unknown_binary_queue_mode_and_helpers_refused(self):
  b,s=evidence()
  mutations=[('b','hashes',{}),('b','architecture','aarch64'),('b','queue_id',None),('b','hal_pids',[7]),('s','queue_id',15),('s','service_mode','2'),('s','registered','start'),('s','hal_pids',[7]),('s','processes',s['processes']+[{'name':'ipmitool'}])]
  for target,key,value in mutations:
   bb,ss=copy.deepcopy(b),copy.deepcopy(s);(bb if target=='b' else ss)[key]=value
   self.assertFalse(w.cleanup_signature(bb,ss,100),(target,key))
  for key,value in [('syscall','61'),('state','D'),('ppid',1)]:
   ss=copy.deepcopy(s);ss['processes'][1][key]=value
   self.assertFalse(w.cleanup_signature(b,ss,100),key)
 def test_intervening_contradiction_cancels_evidence(self):
  b,s=evidence();x=w.StartWindow(w.ARGS,b,100);x.observe(19.2,s);x.observe(19.4,{})
  x.observe(19.8,s);self.assertTrue(x.expired(20))
 def test_grace_is_absolute_and_never_renews(self):
  x=self.window();self.assertFalse(x.expired(20));self.assertFalse(x.expired(24.99))
  self.assertTrue(x.expired(25));x.observe(25,evidence()[1]);self.assertTrue(x.expired(26))
  self.assertTrue(self.window().expired(100))
 def test_deadline_failure_rolls_back_before_recovery(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m,'STATE',d):
   p=Path(d)/'config';p.write_bytes(b'old');events=[];x=self.window()
   def startup(changed):
    self.assertFalse(x.expired(21));self.assertTrue(x.expired(25))
    events.append('timeout-snapshot');raise m.Skip('native start reached absolute 25s cap')
   def recover(changed):events.append(p.read_bytes())
   with self.assertRaisesRegex(m.Skip,'25s cap'):
    m.transact('sensors',{str(p):b'new'},{str(p):b'old'},lambda:None,after=startup,undo=recover)
   self.assertEqual(events,['timeout-snapshot',b'old']);self.assertEqual(p.read_bytes(),b'old')
   self.assertTrue((Path(d)/'sensors.blocked').exists())
 def test_ready_needs_fresh_monitor_log_and_cache(self):
  self.assertTrue(w.ready(1,'start',[2],[1],True,True))
  for args in [(1,'stop',[2],[1],True,True),(1,'start',[1],[1],True,True),(1,'start',[2,3],[1],True,True),(1,'start',[2],[1],False,True),(1,'start',[2],[1],True,False),(2,'start',[2],[1],True,True)]:
   self.assertFalse(w.ready(*args))
if __name__=='__main__':unittest.main()

class IntegratedRunner(unittest.TestCase):
 def execute(self,finish=21,qualifies=True,action='start',overall=60):
  from unittest.mock import MagicMock
  clock=[0.0];b,s=evidence();process=MagicMock();process.pid=100
  process.poll.side_effect=lambda: 1 if clock[0]>=finish else None
  process.returncode=1
  def snapshot(*args,**kw):return b if kw.get('baseline') else (s if qualifies else {})
  def sleep(value):clock[0]+=value
  with patch.object(w,'snapshot',side_effect=snapshot),patch.object(m,'monotonic',side_effect=lambda:clock[0]),patch.object(m,'WORK_DEADLINE',overall),patch.object(m.time,'sleep',side_effect=sleep),patch.object(m,'monitor_event') as events,patch.object(m.subprocess,'Popen',return_value=process) as popen,patch.object(m,'timeout_processes',return_value=s['processes']):
   try:result=w.execute(m,action,20)
   except m.CommandTimeout as e:result=e
  return result,clock[0],process,events,popen
 def test_real_supervisor_accepts_21_second_completion_only_with_signature(self):
  result,elapsed,p,event,popen=self.execute()
  self.assertEqual(result[0],1);self.assertEqual(result[2],25)
  self.assertGreaterEqual(elapsed,21);self.assertLess(elapsed,21.1)
  p.kill.assert_not_called();self.assertTrue(popen.call_args.kwargs['close_fds'])
  self.assertTrue(any(c.kwargs.get('granted') is True for c in event.call_args_list))
 def test_unqualified_sleep_is_killed_at_normal_deadline(self):
  result,elapsed,p,event,_=self.execute(qualifies=False)
  self.assertIsInstance(result,m.CommandTimeout);self.assertLess(elapsed,20.1);p.kill.assert_called_once()
  self.assertEqual(result.processes,evidence()[1]['processes'])
 def test_qualified_hang_is_killed_once_at_absolute_25(self):
  result,elapsed,p,event,_=self.execute(finish=100)
  self.assertIsInstance(result,m.CommandTimeout);self.assertGreaterEqual(elapsed,25);self.assertLess(elapsed,25.1)
  p.kill.assert_called_once();p.wait.assert_called_once()
 def test_stop_never_receives_grace(self):
  result,elapsed,p,_,_=self.execute(action='stop')
  self.assertIsInstance(result,m.CommandTimeout);self.assertLess(elapsed,20.1)
 def test_overall_transaction_cap_overrides_grace(self):
  result,elapsed,p,_,_=self.execute(finish=100,overall=22)
  self.assertIsInstance(result,m.CommandTimeout);self.assertLess(elapsed,22.1)
 def test_snapshot_reads_only_target_queue_and_safe_metadata(self):
  b,s=evidence()
  texts={'/proc/sysvipc/msg':'key msqid\n1212238933 14\n999 18\n',m.HAL:'[Global]\nService Mode = 0\n'}
  with patch.object(m,'monitor_state',return_value=('stop',[])),patch.object(m,'txt',side_effect=lambda p:texts[p]),patch.object(m,'timeout_processes',return_value=s['processes']):
   got=w.snapshot(m,100)
  self.assertEqual(got['queue_id'],14);self.assertEqual(got['service_mode'],'0')
 def test_integrated_readiness_rejects_stale_cache(self):
  clock=[0]
  def sleep(v):clock[0]+=v
  class Stat:st_mtime=10
  config='[SHUTDOWN TEMP]\nCPU_TEMP = 85\nSYS_TEMP = 70\nDISK_TEMP = 60\nPOWER_TEMP = 55\n'
  log='hal_daemon start. (pid=2)\nSHUTDOWN TEMP CPU:SYS:DISK:PWR = 85:70:60:55'
  texts={'/etc/hal_util.conf':config,'/var/log/hal_daemon.log':log,'/tmp/em/em_0.info':'[INFO]\nCPUT_1 = 60\n'}
  with patch.object(m,'NATIVE_IPC_GRACE',True),patch.object(m,'WORK_DEADLINE',60),patch.object(m,'monitor_state',side_effect=[('start',[1])]+[('start',[2])]*200),patch.object(m,'monitor_matches',return_value=False),patch.object(m,'monitor_action'),patch.object(m.os,'stat',return_value=Stat()),patch.object(m,'txt',side_effect=lambda p:texts[p]),patch.object(m,'monotonic',side_effect=lambda:clock[0]),patch.object(m.time,'sleep',side_effect=sleep):
   with self.assertRaisesRegex(m.Skip,'readiness timed out'):m.restart_monitor()
  self.assertGreaterEqual(clock[0],15);self.assertLess(clock[0],15.2)
