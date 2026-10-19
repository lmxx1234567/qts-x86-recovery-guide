"""One-shot, host-profiled restoration; Python 2.7/3 compatible.
No firmware installation, reboot, storage configuration or privilege restoration.
"""
from __future__ import print_function
import os,sys,re,json,time,stat,hashlib,subprocess,signal,tempfile,fcntl,glob
import xml.etree.ElementTree as ET
BASE=os.path.dirname(os.path.realpath(__file__))
STATE='/tmp/qts-mods'
MODEL='/etc/model.conf';HAL='/etc/hal.conf';PLATFORM='/etc/platform.conf'
WIDGET='/home/httpd/cgi-bin/js/qos-core-widget.js'
MODULES=['sensors','cpu_widget','memory','cache_candidates','artwork','myqnap']
class Skip(Exception):pass
def need(ok,msg):
    if not ok:raise Skip(msg)
def read(p):
    with open(p,'rb') as f:return f.read()
def txt(p):return read(p).decode('utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def run_result(args,timeout=20):
    # Temporary output avoids pipe deadlocks; isolated process groups bound probes.
    with tempfile.TemporaryFile() as out:
        p=subprocess.Popen(args,stdout=out,stderr=out,preexec_fn=os.setsid)
        end=time.time()+timeout
        while p.poll() is None and time.time()<end:time.sleep(.05)
        if p.poll() is None:
            os.killpg(p.pid,signal.SIGKILL);p.wait();raise Skip('Command timed out: '+args[0])
        out.seek(0);data=out.read(4*1024*1024).decode('utf-8','replace')
        return p.returncode,data

def run(args,timeout=20):
    rc,data=run_result(args,timeout)
    need(rc==0,'Command failed: '+repr(args)+' (exit '+str(rc)+'): '+data[:1000])
    return data


# daemon_mgr can return 1 after changing state. Never treat that code alone as success.
def process_ids(argv,proc='/proc'):
    found=[]
    for path in glob.glob(proc+'/[0-9]*/cmdline'):
        try:
            args=read(path).split(b'\0')
            args=[a.decode('utf-8','replace') for a in args if a]
            if args==argv:found.append(int(path.split('/')[-2]))
        except (IOError,OSError):pass  # Process exited while scanning.
    return found

def monitor_state():
    rows=[]
    for line in txt('/etc/daemon_mgr.conf').splitlines():
        if '=' not in line:continue
        parts=[p.strip() for p in line.split('=',1)[1].split(',',2)]
        if parts and parts[0]=='hal_daemon':rows.append(parts)
    need(len(rows)==1 and len(rows[0])==3 and rows[0][2]=='/sbin/hal_daemon -f',
         'Unknown/duplicate hardware monitor registration')
    need(rows[0][1] in ('start','stop'),'Unknown hardware monitor action')
    return rows[0][1],process_ids(['/sbin/hal_daemon','-f'])

def monitor_matches(action):
    registered,pids=monitor_state()
    return registered==action and (len(pids)==1 if action=='start' else not pids)

def monitor_action(action,timeout=20):
    need(action in ('start','stop'),'Invalid monitor action')
    monitor_state()  # Refuse unfamiliar registrations before any command.
    args=['/sbin/daemon_mgr','hal_daemon',action,'/sbin/hal_daemon -f']
    rc,data=run_result(args,timeout)
    print(json.dumps({'monitor_action':action,'returncode':rc,'output':data[:1000]}));sys.stdout.flush()
    # Only this bounded, explicitly verified daemon_mgr transition accepts exit 1.
    need(rc in (0,1),'Monitor command failed: '+repr(args)+' exit '+str(rc)+': '+data[:1000])
    end=time.time()+timeout
    while True:
        if monitor_matches(action):return
        need(time.time()<end,'Monitor transition unconfirmed: '+repr(args)+' exit '+str(rc)+': '+data[:1000])
        time.sleep(.25)

def restart_monitor():
    try:
        if not monitor_matches('stop'):monitor_action('stop')
    except Exception as original:
        # A stop may have taken effect even when its command failed or timed out.
        # Restore availability before reporting failure; do not suppress the original.
        try:monitor_action('start')
        except Exception as recovery:
            raise Skip('Monitor stop failed: '+str(original)+'; recovery start failed: '+str(recovery))
        raise
    monitor_action('start')

def startup_ready():
    try:
        return (not os.path.exists('/tmp/booting') and
                os.path.isfile('/etc/hal.conf') and os.path.isfile('/tmp/em/em_0.info') and
                len(process_ids(['/sbin/daemon_mgr']))==1 and monitor_matches('start'))
    except (IOError,OSError,Skip):return False

def sections(s):
    out={}
    for m in re.finditer(r'^\[([^\]\r\n]+)\][ \t]*\r?\n(.*?)(?=^\[|\Z)',s,re.M|re.S):
        need(m.group(1) not in out,'Duplicate section '+m.group(1));out[m.group(1)]=m
    return out
def fields(s,name):
    m=sections(s).get(name);need(m is not None,'Missing section '+name);out={}
    for line in m.group(2).splitlines():
        if not line.strip() or line.lstrip().startswith(('#',';')):continue
        need('=' in line,'Unrecognized section syntax '+name)
        k,v=line.split('=',1);k=k.strip();need(k not in out,'Duplicate key '+k);out[k]=v.strip()
    return out
def setfields(s,name,changes,allowed=None,create=False):
    ss=sections(s)
    if name not in ss:
        need(create,'Missing section '+name);s+='\n['+name+']\n';ss=sections(s)
    m=ss[name];old=fields(s,name);body=m.group(2)
    for k,v in changes.items():
        if allowed is not None:need(old.get(k) in allowed[k],'Unknown '+name+'/'+k)
        if old.get(k)==v:continue
        if k in old:body=re.sub(r'^'+re.escape(k)+r'[ \t]*=.*$',k+' = '+v,body,flags=re.M)
        else:body=body.rstrip()+'\n'+k+' = '+v+'\n'
    return s[:m.start(2)]+body+s[m.end(2):]
def remove_sections(s,names):
    for name in names:
        m=sections(s).get(name)
        if m:s=s[:m.start()]+s[m.end():]
    return s

def atomic(p,b,mode=0o644):
    need(not os.path.islink(p),'Refusing symlink target '+p)
    fd,tmp=tempfile.mkstemp(prefix='.qts-mods-',dir=os.path.dirname(p))
    try:
        with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,mode);os.rename(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def private_dir(p):
    if not os.path.exists(p):os.mkdir(p,0o700)
    need(not os.path.islink(p) and stat.S_ISDIR(os.stat(p).st_mode) and os.stat(p).st_uid==os.geteuid(),'Unsafe state directory')
    os.chmod(p,0o700)
def notify(message,warn):
    try:run(['/sbin/notice_log_tool','-a','[QTS Mods] '+message,'-t','4' if warn else '6','-y','17','-G','0','-u','System'])
    except Exception:
        try:run(['/usr/bin/logger','-t','QTS-Mods',message])
        except Exception:pass

def transact(name,updates,expected,verify,check=False,after=None,undo=None,rollback_merge=None):
    changed=[p for p in updates if updates[p]!=expected[p]]
    if check:return {'state':'ready','would_change':changed}
    blocked=STATE+'/'+name+'.blocked'
    need(not os.path.exists(blocked),'Previous failed repair; manual review required this boot')
    modes={p:stat.S_IMODE(os.stat(p).st_mode) if expected[p] is not None else (0o755 if p=='/sbin/ipmitool' else 0o644) for p in changed}
    if changed:
        backups=STATE+'/backups';private_dir(backups)
        folder=tempfile.mkdtemp(prefix=name+'-',dir=backups)
        for i,p in enumerate(changed):
            need(not os.path.islink(p),'Refusing symlink '+p)
            if expected[p] is not None:atomic(folder+'/'+str(i),expected[p],0o600)
        atomic(folder+'/index.json',json.dumps(changed).encode('utf-8'),0o600)
    committed=[]
    try:
        for p in changed:
            need((read(p) if os.path.exists(p) else None)==expected[p],'Concurrent file change: '+p)
            atomic(p,updates[p],modes[p]);committed.append(p)
        if after:after(bool(changed))
        verify()
    except Exception as e:
        conflicts=[]
        for p in reversed(committed):
            if read(p)!=updates[p]:
                if rollback_merge:
                    merged=rollback_merge(p,read(p),expected[p])
                    if merged is not None:atomic(p,merged,modes[p]);continue
                conflicts.append(p);continue
            if expected[p] is None:os.unlink(p)
            else:atomic(p,expected[p],modes[p])
        if undo:
            try:undo(bool(committed))
            except Exception:conflicts.append('runtime rollback failed')
        atomic(blocked,str(e).encode('utf-8'),0o600)
        raise Skip('Repair rolled back: '+str(e)+('; concurrent changes preserved: '+','.join(conflicts) if conflicts else ''))
    return {'state':'restored' if changed else 'ok','changed':changed}

def dimms(dmi,slots):
    devices=[]
    for h,body in re.findall(r'Handle (0x[0-9A-Fa-f]+), DMI type 17,[^\n]*\n(.*?)(?=\nHandle |\Z)',dmi,re.S):
        def field(k):
            m=re.search(r'^\s*'+re.escape(k)+r':\s*([^\n]+)',body,re.M);need(m,'Missing DMI '+k);return m.group(1).strip()
        size=field('Size')
        if size=='No Module Installed':mb=0
        else:
            m=re.match(r'^(\d+) (MB|GB)$',size);need(m,'Unknown DIMM size');mb=int(m.group(1))*(1024 if m.group(2)=='GB' else 1)
        devices.append({'handle':int(h,16),'locator':field('Locator'),'bank':field('Bank Locator'),'mb':mb})
    need(len(devices)==len(slots),'DIMM slot count changed')
    first=devices[0]['handle'];out=[]
    for want in slots:
        found=[d for d in devices if d['locator']==want['locator'] and d['bank']==want['bank']]
        need(len(found)==1,'Ambiguous DIMM topology');d=dict(found[0]);d['offset']=d['handle']-first
        need(d['offset']>=0,'Unexpected DMI handle order');d['channel']=want['channel'];d['dimm']=want['dimm'];out.append(d)
    return out

def widget(s):
    old='if(QNAP.QOS.config.modelName==="TS-X82"){tmpColumns.push({dataIndex:".",header:"CPU"'
    new='if(record && record.get("cpuTempC")>0){tmpColumns.push({dataIndex:".",header:"CPU"'
    a='cls:"cpu-temperacure",dtCls:"show-by-platform"';b='cls:"cpu-temperacure",dtCls:"qts-native-cpu-temperature"'
    need(s.count(old)+s.count(new)==1 and s.count(a)+s.count(b)==1,'Unknown CPU widget structure')
    return s.replace(old,new).replace(a,b)
def svg_ids(b):
    need(len(b)<2*1024*1024,'Oversized artwork');root=ET.fromstring(b)
    need(root.tag.endswith('svg'),'Not SVG')
    return set(x.attrib['id'] for x in root.iter() if 'id' in x.attrib)
def valid_index(p):
    need(os.path.getsize(p)<32*1024*1024,'Oversized repository index');root=ET.parse(p).getroot();items=root.findall('item')
    need(root.tag=='plugins' and items,'Invalid repository XML')
    need(any(x.findtext('platformID')=='TS-NASX86' for it in items for x in it.findall('platform')),'No x86 packages')
    for it in items:
        for x in it.findall('platform'):
            u=x.findtext('location') or '';need(not u or u.startswith('https://'),'Non-HTTPS package URL')
    return len(items)
def cron_replace(s,old,new):
    lines=s.splitlines();out=[];seen=False
    for line in lines:
        stripped=line.strip()
        if stripped in [old,new]:
            if not seen:out.append(new);seen=True
        else:
            need('/qts-profile/mods/refresh.py' not in line and (not old.split(' /bin/sh ')[-1] in line or stripped.startswith('#')),'Conflicting custom repository job')
            out.append(line)
    if not seen:out.append(new)
    return '\n'.join(out)+'\n'

class Context(object):
    def __init__(self,profile,check):self.p=profile;self.check=check;self.firmware=None
    def probe(self,mode,*args):return json.loads(run([sys.executable,BASE+'/probe.py',mode]+list(args),30))
    def gate(self):
        need(self.p.get('format')==1 and self.p.get('enabled') is True,'Host profile not enabled')
        need(len(self.p.get('protected_sections',{}))>=10 and len(self.p.get('identity_tokens',[]))>=2,'Incomplete host identity/mapping profile')
        v=run(['/sbin/getcfg','System','Version']).strip();need(v.startswith(self.p['release_prefix']),'Unsupported QTS release family')
        build=run(['/sbin/getcfg','System','Build Number']).strip();self.firmware=v+' '+build
        dmi=run(['/sbin/dmidecode','-t','2','-t','38'])
        for token in self.p['identity_tokens']:need(token in dmi,'Host identity/KCS mismatch')
        model=txt(MODEL)
        for name,expected in self.p['protected_sections'].items():need(fields(model,name)==expected,'Protected mapping changed: '+name)
        for path in self.p['pci_paths']:need(os.path.isdir(path),'Mapped PCI path absent')
        marker=STATE+'/firmware'
        if os.path.exists(marker):need(txt(marker)==self.firmware,'Firmware changed during this boot; no concurrent repair')
        elif not self.check:atomic(marker,self.firmware.encode('utf-8'),0o600)
    def apply(self,name,updates,verify=lambda:None,after=None,undo=None,expected=None,rollback_merge=None):
        if self.firmware:
            current=run(['/sbin/getcfg','System','Version']).strip()+' '+run(['/sbin/getcfg','System','Build Number']).strip()
            need(current==self.firmware,'Firmware changed during reconciliation')
        if expected is None:expected={p:read(p) if os.path.exists(p) else None for p in updates}
        return transact(name,updates,expected,verify,self.check,after,undo,rollback_merge)
    def sensors(self):
        need(not os.path.exists('/dev/ipmi0') and not os.path.exists('/dev/ipmi/0'),'Native IPMI driver present; direct KCS skipped')
        from kcs_read import command
        readings=[]
        for sensor in [49,97,98]:
            out=command(4,0x2d,[sensor]);need(len(out)>=4 and not out[1]&0x20 and 0<out[0]<100,'BMC reading unavailable');readings.append(out[0])
        cpu=[p for p in glob.glob('/sys/class/hwmon/hwmon*') if txt(p+'/name').strip()=='k10temp']
        need(len(cpu)==1 and 0<int(txt(cpu[0]+'/temp1_input'))<110000,'Native CPU reading unavailable')
        self.probe('symbols','HM_Get_Temperature','HM_Get_Fan')
        original={p:read(p) if os.path.exists(p) else None for p in [MODEL,HAL,'/sbin/ipmitool']}
        current=original['/sbin/ipmitool']
        shim=read(BASE+'/ipmitool')
        need(current is None or sha(current) in self.p['known_shims']+[sha(shim)],'Unknown/native IPMI executable preserved')
        m=original[MODEL].decode('utf-8');h=original[HAL].decode('utf-8')
        need(fields(m,'System Enclosure').get('CPU_TEMP_UNIT')=='DTS:1','Unknown CPU source')
        m=setfields(m,'System Enclosure',{'MAX_TEMP_NUM':'2','MAX_FAN_NUM':'2','SYSTEM_TEMP_UNIT':'IPMI:49'}, {'MAX_TEMP_NUM':['1','2'],'MAX_FAN_NUM':['0','2'],'SYSTEM_TEMP_UNIT':[None,'IPMI:49']})
        if 'System FAN' in sections(m):need(fields(m,'System FAN')=={'FAN_UNIT':'IPMI','FAN_1':'I97','FAN_2':'I98'},'Unknown fan mapping')
        m=setfields(m,'System FAN',{'FAN_UNIT':'IPMI','FAN_1':'I97','FAN_2':'I98'},create=True)
        h=setfields(h,'Enclosure_0',{'max_temp_num':'2','max_fan_num':'2'},{'max_temp_num':['1','2'],'max_fan_num':['0','2']})
        settings_changed=m.encode('utf-8')!=original[MODEL] or h.encode('utf-8')!=original[HAL]
        restarted=[False]
        def restart():
            restart_monitor()
        def after(changed):
            if settings_changed and changed:
                restarted[0]=True;restart();time.sleep(20)
        def undo(changed):
            if restarted[0]:restart()
        def verify():
            p=self.probe('sensors')
            need(all(r==0 and 0<v<110 for r,v in p['temperature']),'HAL temperatures invalid')
            need(all(r==0 and 0<v<10000 for r,v in p['fan']),'HAL fan values invalid')
            raw=[command(4,0x2d,[sid])[0] for sid in [49,97,98]]
            need(abs(p['temperature'][1][1]-raw[0])<8,'HAL/BMC motherboard scale mismatch')
            need(all(abs(p['fan'][i][1]-raw[i+1]*100)<800 for i in range(2)),'HAL/BMC fan scale mismatch')
            cache=fields(txt('/tmp/em/em_0.info'),'INFO')
            need(all(int(cache.get(k,'0'))>0 for k in ['CPUT_1','SYST_1','FANR_1','FANR_2']),'Monitor cache readings absent')
        return self.apply('sensors',{MODEL:m.encode('utf-8'),HAL:h.encode('utf-8'),'/sbin/ipmitool':shim},verify,after,undo,original)
    def cpu_widget(self):
        original=read(WIDGET);desired=widget(original.decode('utf-8')).encode('utf-8')
        return self.apply('cpu_widget',{WIDGET:desired},lambda:need(widget(txt(WIDGET)).encode('utf-8')==read(WIDGET),'Widget verification failed'),expected={WIDGET:original})
    def memory(self):
        rows=dimms(run(['/sbin/dmidecode','-t','17']),self.p['memory_slots'])
        self.probe('symbols','HAL_MB_Mem_Get_Info')
        originals={p:read(p) for p in [MODEL,PLATFORM]}
        m=originals[MODEL].decode('utf-8');platform=originals[PLATFORM].decode('utf-8')
        prior=fields(m,'System Memory')
        need(set(prior).issubset(set(['MAX_CHANNEL_NUM','MAX_SLOT_NUM','DIMM_ACCESS']+['SLOT%d_ADDR'%i for i in range(1,5)])),'Unknown memory configuration')
        changes={'MAX_CHANNEL_NUM':str(len(set(r['channel'] for r in rows))),'MAX_SLOT_NUM':str(len(rows)),'DIMM_ACCESS':'DMI'}
        for i,r in enumerate(rows):changes['SLOT%d_ADDR'%(i+1)]='%d-%d, 0x%x'%(r['channel'],r['dimm'],r['offset'])
        m=setfields(m,'System Memory',changes)
        def match(s):
            for i,r in enumerate(rows):
                f=fields(s,'DIMM '+str(i+1))
                if int(f.get('size','0'))!=r['mb'] or int(f.get('slot_addr','-1'),0)!=r['offset'] or int(f.get('channel_id','0'))!=r['channel']:return False
            return True
        try:stale=not match(platform)
        except Skip:stale=True
        if stale:platform=remove_sections(platform,[n for n in sections(platform) if re.match(r'^DIMM \d+$',n)])
        def verify():
            self.probe('memory',str(len(rows)));need(match(txt(PLATFORM)),'HAL did not populate expected DIMM topology')
        # HAL populates only DIMM sections in the platform cache; rollback must
        # preserve these expected side effects while retaining unrelated keys.
        def merge(path,current,original):
            if path!=PLATFORM:return None
            cur=current.decode('utf-8');old=original.decode('utf-8')
            names=[n for n in sections(cur) if re.match(r'^DIMM \d+$',n)]
            cur=remove_sections(cur,names)
            for name,match in sections(old).items():
                if re.match(r'^DIMM \d+$',name):cur+='\n'+match.group(0)
            return cur.encode('utf-8')
        return self.apply('memory',{MODEL:m.encode('utf-8'),PLATFORM:platform.encode('utf-8')},verify,expected=originals,rollback_merge=merge)
    def cache_candidates(self):
        self.probe('symbols','SE_Get_Cacheable_Port_Bitmap')
        originals={p:read(p) for p in [MODEL,HAL]}
        m=originals[MODEL].decode('utf-8');h=originals[HAL].decode('utf-8')
        need(fields(m,'System Enclosure')['MAX_DISK_NUM']=='8' and fields(h,'Enclosure_0')['max_disk_num']=='8','Unexpected bay count')
        mask=self.p['cache_mask'];need(mask=='0x1FE','Unreviewed cache policy')
        m=setfields(m,'System Enclosure',{'SYSTEM_DISK_CACHEABLE_BITMAP':mask},{'SYSTEM_DISK_CACHEABLE_BITMAP':['0x0',mask]})
        h=setfields(h,'Enclosure_0',{'cache_port_bitmap':mask},{'cache_port_bitmap':['0x0',mask]})
        def verify():
            out=self.probe('cache');need(out['rc']==0 and out['mask']==int(mask,16),'HAL cache-port mask not effective')
        return self.apply('cache_candidates',{MODEL:m.encode('utf-8'),HAL:h.encode('utf-8')},verify,expected=originals)
    def artwork(self):
        updates={};expected={}
        for spec in self.p['artwork']:
            dest=spec['target'];source=BASE+'/'+spec['asset']
            need(dest in ['/home/httpd/v3_menu/layout/'+n for n in ['ts_877_0.svg','TS-877.svg','NAS-877-G.svg']],'Invalid artwork target')
            src=read(source);old=read(dest);need(sha(src)==spec['sha256'],'Artwork asset integrity mismatch')
            need(set(spec['required_ids']).issubset(svg_ids(src)) and any(set(ids).issubset(svg_ids(old)) for ids in spec['target_id_sets']),'Artwork structure changed')
            # ID checks alone do not prove positioning semantics. Recognized
            # vendor/prior artwork hashes bound this cosmetic replacement.
            need(sha(old) in spec['known_target_hashes']+[sha(src)],'Unrecognized artwork; preserving vendor image')
            updates[dest]=src;expected[dest]=old
        return self.apply('artwork',updates,expected=expected)
    def myqnap(self):
        spec=self.p['myqnap'];repo='/etc/config/3rd_pkg_v2.conf';cron='/etc/config/crontab'
        need(os.path.realpath('/home/httpd/RSS/rssdoc')==os.path.realpath('/etc/config/rssdoc'),'Local repository route changed')
        need(os.access('/usr/bin/crontab',os.X_OK) and os.access('/sbin/curl',os.X_OK),'Repository dependencies absent')
        cache='/etc/config/rssdoc/myqnap-local.xml'
        # Missing/bad cache is not silently registered. The separate refresh
        # helper can repopulate it, without ever installing packages.
        cache_problem=None
        try:valid_index(cache)
        except Exception as e:
            cache_problem=str(e)
            if not self.check:
                run([sys.executable,BASE+'/refresh.py'],220);valid_index(cache);cache_problem=None
        originals={p:read(p) if os.path.exists(p) else None for p in [repo,cron]}
        need(originals[cron] is not None,'Missing system crontab')
        s=(originals[repo] or b'').decode('utf-8');section=spec['section']
        if section in sections(s):need(fields(s,section)==spec['fields'],'Repository entry changed; preserving operator settings')
        s=setfields(s,section,spec['fields'],create=True)
        old=spec['old_cron'];new='17 */6 * * * /usr/local/bin/python /qts-profile/mods/refresh.py'
        diskcron=cron_replace(originals[cron].decode('utf-8'),old,new)
        live=run(['/usr/bin/crontab','-l']);newlive=cron_replace(live,old,new)
        installed=[False]
        def install(content):
            p=STATE+'/cron-install';atomic(p,content.encode('utf-8'),0o600);run(['/usr/bin/crontab',p])
        def after(changed):
            if newlive!=live:installed[0]=True;install(newlive)
        def undo(changed):
            if installed[0]:install(live)
        def verify():need(run(['/usr/bin/crontab','-l']).splitlines()==newlive.splitlines(),'Runtime cron did not match intended content')
        result=self.apply('myqnap',{repo:s.encode('utf-8'),cron:diskcron.encode('utf-8')},verify,after,undo,originals)
        if self.check:
            result['runtime_cron_would_change']=newlive!=live
            result['cache_needs_refresh']=cache_problem
        return result

def main():
    if '--startup-ready' in sys.argv:return 0 if startup_ready() else 1
    selected=['sensors'] if '--only-sensors' in sys.argv else MODULES
    need(os.geteuid()==0,'Root required');private_dir(STATE)
    lock=os.open(STATE+'/lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except IOError:os.close(lock);print('Another check is running');return 0
    try:
        check='--check' in sys.argv;c=None;results={}
        try:
            profile=json.loads(txt(BASE+'/profile.json'));c=Context(profile,check);c.gate()
        except Exception as e:results={n:{'state':'skipped','reason':str(e)} for n in selected}
        else:
            for n in selected:
                try:results[n]=getattr(c,n)()
                except Exception as e:results[n]={'state':'skipped','reason':str(e)}
        report={'package':'1.1','scope':selected,'firmware':c.firmware if c else None,'check_only':check,'modules':results,'time':time.strftime('%Y-%m-%d %H:%M:%S')}
        print(json.dumps(report,indent=2))
        if not check:
            old={}
            try:old=json.loads(txt(STATE+'/status.json'))
            except (IOError,ValueError):pass
            if '--only-sensors' in sys.argv:
                report['previous_modules']=old.get('modules',{})
            atomic(STATE+'/status.json',(json.dumps(report,indent=2)+'\n').encode('utf-8'),0o600)
            summary='; '.join(n+': '+r['state']+(' ('+r['reason'][:150]+')' if 'reason' in r else '') for n,r in sorted(results.items()))
            def signature(rs):return {n:(r['state']=='skipped',r.get('reason')) for n,r in rs.items()}
            if signature(old.get('modules',{}))!=signature(results):notify(summary,any(r['state']=='skipped' for r in results.values()))
        return 1 if any(r['state']=='skipped' for r in results.values()) else 0
    finally:os.close(lock)
if __name__=='__main__':sys.exit(main())
