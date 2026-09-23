from pathlib import Path
import subprocess,json,datetime,sys
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/copy-colour-investigation-20260915')
repo=Path('LOCAL_HOME/Developer/sqe-platform-copy-colour-trial')
cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(repo/'tools/ace_ios_local.py'),'--evidence-root',str(base/'dark-runs'),'selected','--diagnostic-dirty','--device','iPhone 17 Pro Max','--test','ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls','--test','ACEClientAppUITests/ACEClientAppUITests/testClippingNoActionsStandaloneAudit','--test','ACEClientAppUITests/ACEClientAppUITests/testClippingNoConclusionStandaloneAudit','--test-env-json',str(base/'dark.json')]
record={'startUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'question':'Does primary tint keep release, Copy confirmation, no-actions and no-conclusion audits passing in dark appearance?','expected':'Three tests, all eleven release fields, five unrestricted audits, no failures or skips.','args':cmd}
(base/'dark-command.json').write_text(json.dumps(record,indent=2)+chr(10))
result=subprocess.run(cmd,cwd=repo)
record['exit']=result.returncode
record['endUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(base/'dark-command.json').write_text(json.dumps(record,indent=2)+chr(10))
sys.exit(result.returncode)
