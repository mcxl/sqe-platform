from pathlib import Path
import subprocess,json,datetime,sys
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/field-text-trial-20260915')
repo=Path('LOCAL_HOME/Developer/sqe-platform-field-text-trial')
plan=json.loads((base/'focused-plan.json').read_text())
cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(repo/'tools/ace_ios_local.py'),'--evidence-root',str(base/'focused-runs'),'selected','--diagnostic-dirty','--device','iPhone 17 Pro Max']
for name in plan['selectors']:cmd+=['--test','ACEClientAppUITests/ACEClientAppUITests/'+name]
cmd+=['--test-env-json',str(base/'light.json')]
record={'startUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'args':cmd}
(base/'focused-command.json').write_text(json.dumps(record,indent=2)+chr(10))
result=subprocess.run(cmd,cwd=repo)
record['exit']=result.returncode
record['endUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(base/'focused-command.json').write_text(json.dumps(record,indent=2)+chr(10))
sys.exit(result.returncode)
