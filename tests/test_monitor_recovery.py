import importlib.util,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
PKG=Path(__file__).resolve().parents[1]/'tools'/'qts-mods'
spec=importlib.util.spec_from_file_location('monitor_mods',PKG/'reconcile.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Monitor(unittest.TestCase):
 def test_timeout_keeps_output_and_full_action(self):
  with self.assertRaises(m.CommandTimeout) as caught:
   m.run_result([sys.executable,'-u','-c','import time; print("diagnostic"); time.sleep(2)'],.1,kill_group=False)
  self.assertIn('diagnostic',caught.exception.output)
  self.assertIn('time.sleep',str(caught.exception))
 def test_monitor_timeout_logs_state_and_never_succeeds(self):
  error=m.CommandTimeout(['daemon_mgr','hal_daemon','start'],20,'python missing')
  with patch.object(m,'monitor_state',return_value=('start',[9])),patch.object(m,'run_result',side_effect=error) as run,patch.object(m,'monitor_event') as event:
   with self.assertRaises(m.CommandTimeout):m.monitor_action('start')
   self.assertFalse(run.call_args.kwargs['kill_group'])
   self.assertEqual([c.args[1] for c in event.call_args_list],['begin','timeout'])
   self.assertEqual(event.call_args.kwargs['output'],'python missing')
 def test_failed_stop_does_not_restart_already_running_monitor(self):
  with patch.object(m,'monitor_matches',side_effect=[False,True]),patch.object(m,'monitor_action',side_effect=m.Skip('timeout')) as action:
   with self.assertRaisesRegex(m.Skip,'timeout'):m.restart_monitor()
   self.assertEqual([c.args[0] for c in action.call_args_list],['stop'])
 def test_monitor_timeout_does_not_kill_descendant_group(self):
  from unittest.mock import MagicMock
  process=MagicMock();process.poll.return_value=None;process.pid=999999
  with patch.object(m.subprocess,'Popen',return_value=process) as popen,patch.object(m.os,'killpg') as killpg:
   with self.assertRaises(m.CommandTimeout):m.run_result(['client'],0,kill_group=False)
   process.kill.assert_called_once();killpg.assert_not_called();process.wait.assert_called_once()
   self.assertTrue(popen.call_args.kwargs['close_fds'])
 def test_startup_path_includes_verified_python_directory(self):
  self.assertIn('/usr/local/bin',(PKG/'start').read_text().split('PATH=',1)[1].splitlines()[0])
 def test_generic_exit_one_still_fails(self):
  with self.assertRaises(m.Skip):m.run([sys.executable,'-c','raise SystemExit(1)'])
 def test_stop_one_confirmed_then_start(self):
  state={'action':'start','pids':[5]};calls=[]
  def command(args,timeout,kill_group=True):
   calls.append(args[2]);state.update(action=args[2],pids=[] if args[2]=='stop' else [6]);return 1,'accepted'
  with patch.object(m,'monitor_state',side_effect=lambda:(state['action'],state['pids'])),patch.object(m,'run_result',side_effect=command):m.restart_monitor()
  self.assertEqual(calls,['stop','start'])
 def test_exit_one_without_transition_fails(self):
  with patch.object(m,'monitor_state',return_value=('start',[5])),patch.object(m,'run_result',return_value=(1,'not stopped')):
   with self.assertRaisesRegex(m.Skip,'unconfirmed'):m.monitor_action('stop',0)
 def test_exit_zero_without_transition_fails(self):
  with patch.object(m,'monitor_state',return_value=('stop',[])),patch.object(m,'run_result',return_value=(0,'')):
   with self.assertRaisesRegex(m.Skip,'unconfirmed'):m.monitor_action('start',0)
 def test_unexpected_return_code_rejected_even_if_state_matches(self):
  with patch.object(m,'monitor_state',return_value=('stop',[])),patch.object(m,'run_result',return_value=(2,'')):
   with self.assertRaisesRegex(m.Skip,'exit 2'):m.monitor_action('stop',0)
 def test_stop_timeout_attempts_recovery_and_reports_original(self):
  with patch.object(m,'monitor_matches',return_value=False),patch.object(m,'monitor_action',side_effect=[m.Skip('timed out'),None]) as action:
   with self.assertRaisesRegex(m.Skip,'timed out'):m.restart_monitor()
   self.assertEqual([c.args[0] for c in action.call_args_list],['stop','start'])
 def test_recovery_failure_reported(self):
  with patch.object(m,'monitor_matches',return_value=False),patch.object(m,'monitor_action',side_effect=[m.Skip('stop failure'),m.Skip('start failure')]):
   with self.assertRaisesRegex(m.Skip,'recovery start failed'):m.restart_monitor()
 def test_already_stopped_still_started(self):
  with patch.object(m,'monitor_matches',return_value=True),patch.object(m,'monitor_action') as action:m.restart_monitor()
  action.assert_called_once_with('start')
 def test_rollback_restores_files_before_monitor_recovery(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m,'STATE',d):
   p=Path(d)/'model';p.write_bytes(b'old');calls=[]
   def after(changed):raise m.Skip('start failed')
   def undo(changed):calls.append(p.read_bytes())
   with self.assertRaisesRegex(m.Skip,'start failed'):m.transact('sensors',{str(p):b'new'},{str(p):b'old'},lambda:None,after=after,undo=undo)
   self.assertEqual(calls,[b'old']);self.assertTrue((Path(d)/'sensors.blocked').exists())
 def test_monitor_registration_and_process_both_required(self):
  for state in [('stop',[5]),('start',[]),('start',[5,6])]:
   with patch.object(m,'monitor_state',return_value=state):self.assertFalse(m.monitor_matches('start'))
 def test_process_exact_match(self):
  with tempfile.TemporaryDirectory() as d:
   for i,cmd in enumerate([b'/sbin/hal_daemon\0-f\0',b'/sbin/hal_daemon\0--help\0',b'/other/hal_daemon\0-f\0']):
    p=Path(d)/str(i);p.mkdir();(p/'cmdline').write_bytes(cmd)
   self.assertEqual(m.process_ids(['/sbin/hal_daemon','-f'],d),[0])
 def test_registration_unknown_rejected(self):
  for config in ['DAEMON0 = hal_daemon, start, /other/hal_daemon -f','DAEMON0 = hal_daemon, start, /sbin/hal_daemon -f\nDAEMON1 = hal_daemon, stop, /sbin/hal_daemon -f']:
   with patch.object(m,'txt',return_value=config):
    with self.assertRaises(m.Skip):m.monitor_state()
 def test_boot_in_progress_blocks_readiness(self):
  with patch.object(m.os.path,'exists',return_value=True):self.assertFalse(m.startup_ready())
 def test_readiness_requires_running_monitor(self):
  with patch.object(m.os.path,'exists',return_value=False),patch.object(m.os.path,'isfile',return_value=True),patch.object(m,'process_ids',return_value=[1]):
   with patch.object(m,'monitor_matches',return_value=False):self.assertFalse(m.startup_ready())
   with patch.object(m,'monitor_matches',return_value=True):self.assertTrue(m.startup_ready())
 def test_startup_rechecks_after_settle_and_reopens_log(self):
  s=(PKG/'start').read_text()
  self.assertEqual(s.count('--startup-ready'),2)
  self.assertLess(s.index('sleep 30'),s.rindex('--startup-ready'))
  self.assertIn('exec > /tmp/qts-mods-start.log 2>&1',s)
 def test_only_sensors_does_not_run_other_modules(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m,'BASE',d),patch.object(m,'STATE',d),patch.object(m.os,'geteuid',return_value=0),patch.object(m,'private_dir'),patch.object(m.Context,'gate'),patch.object(m.Context,'sensors',return_value={'state':'ok'}) as sensors,patch.object(m.Context,'myqnap') as other,patch.object(m,'notify'),patch.object(sys,'argv',['reconcile.py','--only-sensors']),patch.object(m,'run_sensors',side_effect=lambda c:c.sensors()):
   (Path(d)/'profile.json').write_text('{}');self.assertEqual(m.main(),0);sensors.assert_called_once();other.assert_not_called()
if __name__=='__main__':unittest.main()
