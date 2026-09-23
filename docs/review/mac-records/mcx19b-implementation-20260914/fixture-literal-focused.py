from pathlib import Path
import subprocess,json,time,os
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(root/'tools/ace_ios_local.py'),'selected','--diagnostic-dirty','--device','iPhone 17 Pro Max','--test','ACEClientAppTests/AcceptanceEvidenceContractTests/testFixtureInspection']
record={'question':'Does the reviewed fixture literal set pass after adding the production loading label and removing the now-shared Refresh literal?', 'started':time.time(),'command':cmd}
with (base/'fixture-literal-focused.log').open('w') as out:record['exit']=subprocess.call(cmd,cwd=root,env=dict(os.environ,PYTHONPYCACHEPREFIX=str(base/'python-cache')),stdout=out,stderr=subprocess.STDOUT)
record['finished']=time.time()
(base/'fixture-literal-focused.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
raise SystemExit(record['exit'])
