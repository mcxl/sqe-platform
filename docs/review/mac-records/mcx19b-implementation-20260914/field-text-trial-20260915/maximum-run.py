from pathlib import Path
import subprocess,json,datetime,sys
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/field-text-trial-20260915')
repo=Path('LOCAL_HOME/Developer/sqe-platform-field-text-trial')
device='D1BAA05C-52DD-4E57-832F-C0A75718E085'
record={'startUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':[]}
def native(args):
 p=subprocess.run(args,capture_output=True,text=True)
 record['commands'].append({'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 if p.returncode:raise RuntimeError('Native setting command failed')
 return p.stdout.strip()
original={k:native(['xcrun','simctl','ui',device,k]) for k in ['content_size','appearance']}
record['original']=original
assert original['appearance']=='light','Expected current light appearance'
status=2
try:
 native(['xcrun','simctl','ui',device,'content_size','accessibility-extra-extra-extra-large'])
 assert native(['xcrun','simctl','ui',device,'content_size'])=='accessibility-extra-extra-extra-large'
 cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(repo/'tools/ace_ios_local.py'),'--evidence-root',str(base/'maximum-runs'),'selected','--diagnostic-dirty','--device','iPhone 17 Pro Max','--test','ACEClientAppUITests/ACEClientAppUITests/testNormalDeviceSettings','--test-env-json',str(base/'maximum.json')]
 record['testCommand']=cmd
 (base/'maximum-command.json').write_text(json.dumps(record,indent=2)+chr(10))
 result=subprocess.run(cmd,cwd=repo)
 status=result.returncode
 record['runnerExit']=status
finally:
 native(['xcrun','simctl','ui',device,'content_size',original['content_size']])
 restored={k:native(['xcrun','simctl','ui',device,k]) for k in ['content_size','appearance']}
 record['restored']=restored
 record['settingsRestored']=restored==original
 if restored!=original:status=2
 record['endUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (base/'maximum-command.json').write_text(json.dumps(record,indent=2)+chr(10))
sys.exit(status)
