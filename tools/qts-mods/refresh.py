"""Refresh public metadata only; never installs a QPKG or changes package policy."""
from __future__ import print_function
import os,sys,fcntl,tempfile
from reconcile import STATE,private_dir,run,valid_index,atomic,read,txt,notify

def main():
    if os.geteuid()!=0:raise RuntimeError('Root required')
    private_dir(STATE)
    lock=os.open(STATE+'/refresh.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except IOError:os.close(lock);return 0
    target='/etc/config/rssdoc/myqnap-local.xml';tmp=None;status=STATE+'/refresh-status'
    try:
        if os.path.islink(target):raise RuntimeError('Refusing symlink index')
        fd,tmp=tempfile.mkstemp(prefix='.myqnap-',dir=os.path.dirname(target));os.close(fd)
        run(['/sbin/curl','-4','--compressed','--fail','--location','--proto','=https','--proto-redir','=https','--silent','--show-error','--connect-timeout','20','--max-time','180','--max-filesize','33554432','https://myqnap.org/repo.xml','-o',tmp],200)
        count=valid_index(tmp);atomic(target,read(tmp),0o644)
        if os.path.exists(status) and txt(status)=='failed':notify('MyQNAP metadata refresh recovered.',False)
        atomic(status,b'ok',0o600);print('Validated and refreshed %d applications'%count);return 0
    except Exception as e:
        if not os.path.exists(status) or txt(status)!='failed':notify('MyQNAP metadata refresh failed; last valid index retained. '+str(e),True)
        atomic(status,b'failed',0o600);print(str(e));return 1
    finally:
        if tmp and os.path.exists(tmp):os.unlink(tmp)
        os.close(lock)
if __name__=='__main__':sys.exit(main())
