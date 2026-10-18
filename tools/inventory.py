#!/usr/bin/env python3
"""Read-only Linux inventory. Output contains private identifiers. No assembly/import."""
import json, platform, subprocess, sys
COMMANDS=[['uname','-a'],['lsblk','-b','-J','-o','NAME,PATH,TYPE,SIZE,MODEL,SERIAL,WWN,FSTYPE,MOUNTPOINTS'],
          ['lspci','-nnk'],['lsscsi','-g'],['findmnt','--json'],['cat','/proc/mdstat'],
          ['cat','/proc/cmdline'],['efibootmgr','-v']]
def main():
    if platform.system()!='Linux': sys.exit('Run on the intended Linux maintenance environment.')
    result={'warning':'PRIVATE: redact before sharing. Read operations only; no activation.', 'commands':[]}
    for command in COMMANDS:
        try:
            p=subprocess.run(command,capture_output=True,text=True,timeout=30,check=False)
            item={'argv':command,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
        except (OSError,subprocess.TimeoutExpired) as e:
            item={'argv':command,'error':str(e)}
        result['commands'].append(item)
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
