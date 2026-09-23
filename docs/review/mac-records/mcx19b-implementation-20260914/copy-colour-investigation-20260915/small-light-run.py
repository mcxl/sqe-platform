from pathlib import Path
import subprocess,json,datetime,sys
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/copy-colour-investigation-20260915')
repo=Path('LOCAL_HOME/Developer/sqe-platform-copy-colour-trial')
cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(repo/'tools/ace_ios_local.py'),'--evidence-root',str(base/'small-light-runs'),'selected','--diagnostic-dirty','--device','iPhone 17','--test','ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls','--test-env-json',str(base/'light.json')]
record={'startUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'question':'Does the unchanged source pass the release and Copy confirmation audits on the smaller required simulator?','expected':'One test, all11fields,3unrestrictedaudits,0failure0skip.','args':cmd}
(base/'small-light-command.json').write_text(json.dumps(record,indent=2)+chr(10))
result=subprocess.run(cmd,cwd=repo)
record['exit']=result.returncode
record['endUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(base/'small-light-command.json').write_text(json.dumps(record,indent=2)+chr(10))
sys.exit(result.returncode)
