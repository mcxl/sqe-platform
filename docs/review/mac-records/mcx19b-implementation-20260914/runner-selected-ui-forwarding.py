from pathlib import Path
import subprocess,json,time,os
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(root/'tools/ace_ios_local.py'),'selected','--diagnostic-dirty','--device','iPhone 17','--test-env-json',str(base/'selected-ui-dark-input.json'),'--test','ACEClientAppUITests/ACEClientAppUITests/testSignInPasswordFieldIsSecure']
record={'question':'Does the public selected-test command pass the secure-password regression on iPhone 17 and forward the retained dark appearance input? Does it restore the initially shutdown simulator?', 'started':time.time(),'command':cmd,'acceptedCoverageCases':0}
with (base/'runner-selected-ui-forwarding.log').open('w') as out:record['exit']=subprocess.call(cmd,cwd=root,env=dict(os.environ,PYTHONPYCACHEPREFIX=str(base/'python-cache')),stdout=out,stderr=subprocess.STDOUT)
record['finished']=time.time()
(base/'runner-selected-ui-forwarding.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
raise SystemExit(record['exit'])
