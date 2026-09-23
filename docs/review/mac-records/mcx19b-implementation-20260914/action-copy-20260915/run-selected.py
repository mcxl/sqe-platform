from pathlib import Path
import subprocess,sys,json,datetime
root=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/action-copy-20260915')
label=sys.argv[1]
assert label.replace('-','').replace('_','').isalnum()
args=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3','LOCAL_HOME/Developer/sqe-platform-release-layout/tools/ace_ios_local.py','--evidence-root',str(root/'runs'),'selected','--diagnostic-dirty','--device','iPhone 17 Pro Max']+sys.argv[2:]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
proc=subprocess.run(args)
(root/(label+'-command.json')).write_text(json.dumps({'command':args,'startedAtUTC':start,'finishedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':proc.returncode},indent=2)+'\n')
sys.exit(proc.returncode)
