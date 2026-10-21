import sys,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'qts-mods'))
import reconcile as m
class Cache(unittest.TestCase):
 def test_only_sensor_fields_removed_no_synthetic_values(self):
  before=b'[INFO]\nCPUT_1 = 61\nTEMP_0 = 61\nTEMP_1 = 48\nFANR_1 = 1400\nFANR_2 = 1800\nFANS_1 = 1\nFANS_2 = 1\nSYST_1 = 48\nUNRELATED = 9\n'
  self.assertEqual(m.without_sensor_cache(before),b'[INFO]\nCPUT_1 = 61\nTEMP_0 = 61\nUNRELATED = 9\n')
 def test_cleanup_is_idempotent(self):
  data=b'[INFO]\nCPUT_1 = 61\nTEMP_0 = 61\n';self.assertEqual(m.without_sensor_cache(data),data)
 def test_refuses_active_monitor_without_reading_or_writing(self):
  with patch.object(m,'monitor_matches',return_value=False),patch.object(m,'read') as read,patch.object(m,'atomic') as write:
   with self.assertRaisesRegex(m.Skip,'monitor runs'):m.clear_sensor_cache()
   read.assert_not_called();write.assert_not_called()
 def test_damaged_cache_refused(self):
  with self.assertRaises(m.Skip):m.without_sensor_cache(b'not an INI cache')

 def test_real_native_contract_accepts_matching_readings(self):
  p={'temp_count':2,'fan_count':2,'temperature':[[0,60],[0,48]],'fan':[[0,1400],[0,1900]]}
  m.validate_sensor_readiness(p,[48,14,19],{'CPUT_1':'60','TEMP_1':'48','FANR_1':'1400','FANR_2':'1900'})
 def test_partial_stale_or_mismatched_sensor_readings_refused(self):
  import copy
  p={'temp_count':2,'fan_count':2,'temperature':[[0,60],[0,48]],'fan':[[0,1400],[0,1900]]}
  cache={'CPUT_1':'60','TEMP_1':'48','FANR_1':'1400','FANR_2':'1900'}
  for key,val in [('temp_count',1),('fan_count',0),('temperature',[[0,60],[-1,0]]),('fan',[[0,1400],[-1,0]])]:
   bad=copy.deepcopy(p);bad[key]=val
   with self.assertRaises(m.Skip):m.validate_sensor_readiness(bad,[48,14,19],cache)
  for bad in [dict(cache,TEMP_1='70'),dict(cache,FANR_2='9999'),{k:v for k,v in cache.items() if k!='TEMP_1'},dict(cache,TEMP_1='0')]:
   with self.assertRaises(m.Skip):m.validate_sensor_readiness(p,[48,14,19],bad)

class BoundedPolicy(unittest.TestCase):
 def test_pending_never_activates(self):
  from unittest.mock import Mock
  context=Mock()
  with patch.object(m.os.path,'exists',return_value=True):
   with self.assertRaisesRegex(m.Skip,'awaiting'):m.run_sensors(context)
  context.sensors.assert_not_called()
 def test_failure_restores_global_deadlines(self):
  from unittest.mock import Mock
  from native_start_window import KNOWN
  context=Mock();context.sensors.side_effect=m.Skip('failure')
  prior=(m.NATIVE_IPC_GRACE,m.WORK_DEADLINE,m.RECOVERY_DEADLINE)
  with patch.object(m.os.path,'exists',return_value=False),patch.object(m,'read',side_effect=lambda p:p),patch.object(m,'sha',side_effect=lambda p:KNOWN[p]),patch.object(m,'monitor_matches',return_value=True),patch.object(m.glob,'glob',return_value=['/cpu']),patch.object(m,'txt',side_effect=lambda p:'k10temp' if p.endswith('/name') else '50000'):
   with self.assertRaisesRegex(m.Skip,'failure'):m.run_sensors(context)
  self.assertEqual((m.NATIVE_IPC_GRACE,m.WORK_DEADLINE,m.RECOVERY_DEADLINE),prior)
