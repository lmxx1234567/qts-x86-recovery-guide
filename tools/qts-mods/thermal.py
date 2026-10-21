#!/usr/local/bin/python
"""Host-gated CPU-only 90 C policy; independent of optional sensor repair."""
from __future__ import print_function
import os,sys,re,time,json,stat,tempfile,subprocess,fcntl
sys.dont_write_bytecode=True
import reconcile as m
CONFIG='/etc/hal_util.conf'
LOG='/var/log/hal_daemon.log'
BACKUPS='/mnt/HDA_ROOT/.qts-thermal-backups'
EXPECTED={'CPU_TEMP':('85','90'),'SYS_TEMP':('70',),'DISK_TEMP':('60',),'POWER_TEMP':('55',)}
PATTERN=r'SHUTDOWN TEMP CPU:SYS:DISK:PWR = (\d+):(\d+):(\d+):(\d+)'

def desired(data):
    text=data.decode('utf-8')
    m.need(text.count('[SHUTDOWN TEMP]')==1,'Unknown shutdown section')
    values=m.fields(text,'SHUTDOWN TEMP')
    m.need(set(values)==set(EXPECTED),'Unknown shutdown fields')
    for key,allowed in EXPECTED.items():m.need(values[key] in allowed,'Unexpected '+key)
    pattern=r'(?m)^(\s*CPU_TEMP\s*=\s*)(85|90)(\s*)$'
    # Restrict the edit to the shutdown section; preserve every other byte.
    start=text.index('[SHUTDOWN TEMP]');end=text.find('\n[',start+1)
    if end<0:end=len(text)
    section=text[start:end]
    m.need(len(re.findall(pattern,section))==1,'Ambiguous CPU threshold')
    section=re.sub(pattern,lambda match:match.group(1)+'90'+match.group(3),section)
    return (text[:start]+section+text[end:]).encode('utf-8')

def loaded(cpu):
    try:
        rows=re.findall(PATTERN,m.txt(LOG))
        return bool(rows) and tuple(rows[-1])==(str(cpu),'70','60','55')
    except (IOError,OSError):return False

def restart(cpu):
    m.restart_monitor()
    m.need(loaded(cpu),'Fresh HAL did not confirm expected CPU threshold')

def gate():
    os.environ['PATH']='/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/sbin:/usr/local/bin'
    from native_start_window import KNOWN
    for path,digest in KNOWN.items():m.need(m.sha(m.read(path))==digest,'Unverified native lifecycle binary: '+path)
    profile=json.loads(m.txt(m.BASE+'/profile.json'))
    context=m.Context(profile,True);context.gate()
    m.need('AMD Ryzen 7 5800X' in m.txt('/proc/cpuinfo'),'Unexpected CPU')
    m.need(m.fields(m.txt(m.MODEL),'System Enclosure').get('CPU_TEMP_UNIT')=='DTS:1','Unknown CPU source')
    m.need(m.monitor_matches('start'),'Hardware monitor not healthy')
    m.need(not os.path.islink(CONFIG) and stat.S_ISREG(os.stat(CONFIG).st_mode),'Unexpected threshold file')
    m.need('SHUTDOWN TEMP CPU:SYS:DISK:PWR' in m.read('/sbin/hal_util').decode('latin1'),'Unknown HAL verification format')
    sensors=[p for p in m.glob.glob('/sys/class/hwmon/hwmon*') if m.txt(p+'/name').strip()=='k10temp']
    m.need(len(sensors)==1,'Unknown CPU temperature sensor')
    temp=int(m.txt(sensors[0]+'/temp1_input'))
    m.need(0<temp<75000,'CPU too hot or invalid for monitor restart')
    return context.firmware,temp

def apply(check=False):
    firmware,temp=gate();before=m.read(CONFIG);after=desired(before)
    oldcpu=int(m.fields(before.decode('utf-8'),'SHUTDOWN TEMP')['CPU_TEMP'])
    if before==after and loaded(90):return {'state':'ok','loaded_cpu':90,'firmware':firmware,'tctl_mC':temp}
    if check:return {'state':'ready','restart_required':True,'firmware':firmware,'tctl_mC':temp,'cpu_before':oldcpu,'cpu_after':90}
    blocked=m.STATE+'/thermal.blocked'
    m.need(not os.path.exists(blocked),'Thermal policy previously failed this boot')
    m.private_dir(BACKUPS)
    folder=tempfile.mkdtemp(prefix=time.strftime('%Y%m%d-%H%M%S-'),dir=BACKUPS)
    m.atomic(folder+'/hal_util.conf',before,0o600)
    m.atomic(folder+'/manifest.json',json.dumps({'firmware':firmware,'before_sha256':m.sha(before),'after_sha256':m.sha(after),'cpu_before':oldcpu}).encode('utf-8'),0o600)
    mode=stat.S_IMODE(os.stat(CONFIG).st_mode)
    prior=(m.NATIVE_IPC_GRACE,m.WORK_DEADLINE,m.RECOVERY_DEADLINE)
    m.NATIVE_IPC_GRACE=True
    began=m.monotonic();m.WORK_DEADLINE=began+60;m.RECOVERY_DEADLINE=began+120
    try:
        m.need(m.read(CONFIG)==before,'Threshold changed concurrently')
        if before!=after:m.atomic(CONFIG,after,mode)
        restart(90)
        m.need(m.read(CONFIG)==after,'Threshold changed after restart')
    except Exception as error:
        recovery='not attempted'
        try:
            m.WORK_DEADLINE=m.RECOVERY_DEADLINE
            current=m.read(CONFIG)
            m.need(current in (before,after),'Concurrent threshold edit; not overwritten')
            if current!=before:m.atomic(CONFIG,before,mode)
            restart(oldcpu)
            recovery='original threshold and monitor restored'
        except Exception as restore:recovery='RECOVERY FAILED: '+str(restore)
        message=str(error)+'; '+recovery
        m.atomic(blocked,message.encode('utf-8'),0o600)
        raise m.Skip(message)
    finally:m.NATIVE_IPC_GRACE,m.WORK_DEADLINE,m.RECOVERY_DEADLINE=prior
    return {'state':'restored','loaded_cpu':90,'firmware':firmware,'backup':folder,'tctl_mC':temp}

def main():
    m.need(os.geteuid()==0,'Root required');m.private_dir(m.STATE)
    fd=os.open(m.STATE+'/lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=apply('--check' in sys.argv)
    except Exception as error:result={'state':'failed','reason':str(error)}
    finally:os.close(fd)
    print(json.dumps(result));sys.stdout.flush()
    if '--check' not in sys.argv:
        m.atomic(m.STATE+'/thermal-status.json',(json.dumps(result)+'\n').encode('utf-8'),0o600)
        if result['state']=='failed':m.notify('CPU 90 C thermal policy skipped/failed: '+result['reason'],True)
    return 1 if result['state']=='failed' else 0
if __name__=='__main__':sys.exit(main())
