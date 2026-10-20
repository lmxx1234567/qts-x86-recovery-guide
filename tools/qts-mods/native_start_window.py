"""Explicit opt-in, one-time HAL IPC-cleanup startup grace.

The gated policy wrappers opt in per transaction. Observations contain metadata only. This
matches a cleanup-stage signature, not a captured userspace instruction pointer.
The caller must retain rollback and require fresh HAL readiness after return.
"""
from __future__ import print_function
KNOWN={
 '/sbin/hal_util':'9403c09b9aa356665d68f1a26db461e35068e16785eda9eb8d15205aa51847ab',
 '/sbin/daemon_mgr':'c10576544bfa1b2ba16facc960ac620ec92c615b2942eeca73b428a40c520563',
 '/lib/libuLinux_hal.so':'963e31daeefa092aa42129957a35e315b05666e94b38c357ea7e9bb75a35736b'}
ARGS=['/sbin/daemon_mgr','hal_daemon','start','/sbin/hal_daemon -f']

def cleanup_signature(baseline, sample, manager):
    """Fail closed on missing, conflicting or unrelated lifecycle evidence."""
    try:
        if baseline['hashes']!=KNOWN or baseline['architecture']!='x86_64':return False
        if baseline['registered']!='stop' or baseline['hal_pids']:return False
        if baseline['service_mode']!='0' or baseline['queue_id'] is None:return False
        if sample['service_mode']!='0' or sample['queue_id'] is not None:return False
        if sample['registered']!='stop':return False
        rows=sample['processes']
        # Exactly the waiting manager and its un-daemonized child. No shell,
        # helper, competing HAL, unknown state, or incomplete snapshot accepted.
        if len(rows)!=2:return False
        parents=[r for r in rows if r['pid']==manager]
        children=[r for r in rows if r['ppid']==manager]
        if len(parents)!=1 or len(children)!=1:return False
        p=parents[0];c=children[0]
        if p['name']!='daemon_mgr' or p['state']!='S' or p['syscall']!='61':return False
        if c['name']!='hal_daemon' or c['state']!='S' or c['syscall']!='35':return False
        if sample['hal_pids']!=[c['pid']]:return False
        return True
    except (KeyError,TypeError):return False

class StartWindow(object):
    """Seconds are monotonic elapsed time supplied by the lifecycle runner.

    All commands default to 20s. Only the exact native start can receive one
    5s grace, based on two qualifying snapshots within its last second. Sampling
    and scheduling delays never move the fixed 25s ceiling.
    """
    def __init__(self,args,baseline,manager):
        self.eligible=args==ARGS
        self.baseline=baseline;self.manager=manager;self.samples=[]
        self.decision=None;self.limit=20.0
    def observe(self,elapsed,sample):
        if self.decision is not None:return
        if not self.eligible or not cleanup_signature(self.baseline,sample,self.manager):
            self.samples=[];return
        if self.samples and elapsed<=self.samples[-1]:self.samples=[]
        self.samples.append(elapsed);self.samples=self.samples[-2:]
    def expired(self,elapsed):
        if elapsed<20:return False
        if self.decision is None:
            good=(self.eligible and len(self.samples)==2 and
                  19<=self.samples[0]<self.samples[1]<=20 and
                  self.samples[1]-self.samples[0]>=.2 and
                  self.samples[1]>=19.5)
            self.decision=bool(good)
            if good:self.limit=25.0
        return elapsed>=self.limit

def ready(returncode,registered,pids,old_pids,fresh_threshold_log,cache_fresh):
    """A sleeping child, command exit, or PID alone is never readiness."""
    return (returncode in (0,1) and registered=='start' and len(pids)==1 and
            pids[0] not in old_pids and fresh_threshold_log and cache_fresh)

def snapshot(m,manager=None,baseline=False):
    registered,pids=m.monitor_state()
    rows=[]
    for line in m.txt('/proc/sysvipc/msg').splitlines()[1:]:
        values=line.split()
        if values and values[0]==str(0x48414c55):rows.append(int(values[1]))
    m.need(len(rows)<=1,'Ambiguous HAL IPC queue')
    result={'registered':registered,'hal_pids':pids,
            'service_mode':m.fields(m.txt(m.HAL),'Global').get('Service Mode'),
            'queue_id':rows[0] if rows else None}
    if baseline:
        result.update(architecture=m.os.uname()[4],hashes={p:m.sha(m.read(p)) for p in KNOWN})
    if manager is not None:result['processes']=m.timeout_processes(manager)
    return result

def execute(m,action,timeout):
    """One lifecycle command, with an inclusive state-confirmation deadline."""
    args=['/sbin/daemon_mgr','hal_daemon',action,'/sbin/hal_daemon -f']
    start=m.monotonic();wall=m.time.time();baseline={}
    if action=='start' and timeout==20:
        try:baseline=snapshot(m,baseline=True)
        except Exception:baseline={}  # Missing evidence denies grace.
        m.monitor_event(action,'ipc_baseline',wall,evidence=baseline)
    m.need(m.work_remaining()>0,'Lifecycle transaction budget exhausted')
    with m.tempfile.TemporaryFile() as out:
        p=m.subprocess.Popen(args,stdout=out,stderr=out,preexec_fn=m.os.setsid,close_fds=True)
        window=StartWindow(args,baseline,p.pid)
        next_sample=19.1;decision_reported=False
        while p.poll() is None:
            elapsed=m.monotonic()-start
            if action=='start' and timeout==20 and next_sample<=elapsed<20:
                try:sample=snapshot(m,p.pid)
                except Exception:sample={}
                observed=m.monotonic()-start
                window.observe(observed,sample)
                m.monitor_event(action,'ipc_phase',wall,evidence=sample,observed_elapsed=observed)
                next_sample=observed+.3
                elapsed=m.monotonic()-start
            expired=window.expired(elapsed) if action=='start' and timeout==20 else elapsed>=timeout
            if window.decision is not None and not decision_reported:
                m.monitor_event(action,'ipc_grace_decision',wall,granted=window.decision,absolute_limit=window.limit)
                decision_reported=True
            if expired or m.work_remaining()<=0:break
            m.time.sleep(.05)
        limit=window.limit if action=='start' and timeout==20 else timeout
        end=min(start+limit,m.WORK_DEADLINE)
        if p.poll() is None:
            try:evidence=m.timeout_processes(p.pid)
            except Exception:evidence=[]
            p.kill();p.wait();out.seek(0)
            raise m.CommandTimeout(args,limit,out.read(4*1024*1024).decode('utf-8','replace'),evidence)
        out.seek(0)
        return p.returncode,out.read(4*1024*1024).decode('utf-8','replace'),end
