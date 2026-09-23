from pathlib import Path
import subprocess,json,datetime,sys
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/copy-colour-investigation-20260915')
repo=Path('LOCAL_HOME/Developer/sqe-platform-copy-colour-trial')
cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(repo/'tools/ace_ios_local.py'),'--evidence-root',str(base/'light-runs'),'selected','--diagnostic-dirty','--device','iPhone 17 Pro Max','--test','ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls','--test-env-json',str(base/'light.json')]
record={'startUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'question':'Does replacing lower-contrast neighbouring release link tint clear Copy and confirmation findings without changing either control?','expected':'One test, all11fields,3unrestrictedaudits,0failure0skip.','args':cmd}
(base/'light-command.json').write_text(json.dumps(record,indent=2)+chr(10))
result=subprocess.run(cmd,cwd=repo)
record['exit']=result.returncode
record['endUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(base/'light-command.json').write_text(json.dumps(record,indent=2)+chr(10))
sys.exit(result.returncode)
