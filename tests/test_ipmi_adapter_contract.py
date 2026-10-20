"""Adapter protocol tests with an injected transport; no hardware access."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ADAPTER=Path(__file__).resolve().parents[1]/'tools'/'qts-mods'/'ipmitool'
LAUNCHER="""
import json,runpy,sys,types
adapter,args,reply=json.loads(sys.argv[1])
transport=types.ModuleType('kcs_read')
def command(n,c,a):
    if (n,c)!=(4,45) or a[0] not in (49,52,97,98):
        raise AssertionError('unauthorized transport call')
    return reply
transport.command=command
sys.modules['kcs_read']=transport
sys.argv=[adapter]+args
runpy.run_path(adapter,run_name='__main__')
"""

class AdapterContract(unittest.TestCase):
 def run_adapter(self,args,reply):
  return subprocess.run([sys.executable,'-c',LAUNCHER,
                         json.dumps([str(ADAPTER),args,reply])],
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=2)
 def test_native_sensor_arguments_return_one_hex_line_and_eof(self):
  for sensor in [49,52,97,98]:
   result=self.run_adapter(['raw','0x04','0x2d',hex(sensor)],[48,192,192,0])
   self.assertEqual(result.returncode,0)
   self.assertEqual(result.stdout,b'30 c0 c0 00\n')
   self.assertEqual(result.stderr,b'')
 def test_control_commands_fail_without_protocol_output(self):
  for args in [['raw','0x30','0x70','0x66'],
               ['raw','0x04','0x2d','0x99'],['lan','print','2'],
               ['raw','0x04','0x2d','0x31','extra']]:
   result=self.run_adapter(args,[48,192,192,0])
   self.assertEqual(result.returncode,1)
   self.assertEqual(result.stdout,b'')
   self.assertEqual(result.stderr,b'Sensor read only\n')
 def test_unavailable_and_short_reply_fail_and_close_streams(self):
  for reply in [[48,32,192,0],[48,192]]:
   result=self.run_adapter(['raw','0x04','0x2d','0x31'],reply)
   self.assertEqual(result.returncode,1)
   self.assertEqual(result.stdout,b'')
   self.assertEqual(result.stderr,b'Sensor reading unavailable\n')

if __name__=='__main__':unittest.main()
