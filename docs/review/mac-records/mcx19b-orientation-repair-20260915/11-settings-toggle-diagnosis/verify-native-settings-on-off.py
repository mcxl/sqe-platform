from pathlib import Path
import json,importlib.util,sys,datetime,hashlib
r=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
d=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/11-settings-toggle-diagnosis')
e=d/'native-settings-on-off-v1'
s=importlib.util.spec_from_file_location('settings_integrity',r/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
x=json.loads((e/'execution.json').read_text())
assert x['exit']==0 and x['candidateUnchanged'] and x['bootStatesRestored'] and not x['restorationFailures']
assert x['candidate']['commit']=='af8c82dc2e7e3faec77e03d8d902e1642943f29c'
b=json.loads((e/'build-record.json').read_text());assert b['candidate']==x['candidate']
for key,pathkey in [('identity','template'),('buildLogSha256','buildLog')]:assert m.sha256(Path(b[pathkey]))==b[key]
for key,pathkey in [('productSha256','products'),('buildResultBundleSha256','buildResultBundle')]:assert m.directory_hash(Path(b[pathkey]))==b[key]
rows=[];images=[]
for p in sorted((e/'native-settings').iterdir()):
 native=json.loads((p/'summary.json').read_text());cmd=json.loads((p/'command.json').read_text())
 assert native['passedTests']==1 and native['failedTests']==native['skippedTests']==native['expectedFailures']==0
 assert cmd['exit']==0 and not cmd.get('timedOut')
 markers=m.marker_records(p/'native.log',m.SETTINGS_MARKER);assert len(markers)==1
 attempts=m.marker_records(p/'native.log','ACE_NATIVE_SWITCH_ATTEMPT')
 results=m.marker_records(p/'native.log','ACE_NATIVE_SWITCH_RESULT')
 assert all(v['attempt']<=2 for v in attempts+results)
 for label in {v['label'] for v in attempts}:
  taps=[v for v in attempts if v['label']==label and v['action']=='tap']
  assert len(taps)<=2 and [v['attempt'] for v in taps]==list(range(1,len(taps)+1))
 for image in sorted((p/'attachments').glob('*.png')):
  images.append({'path':str(image),'bytes':image.stat().st_size,'sha256':m.sha256(image),'phase':p.name})
 rows.append({'phase':p.name,'observed':markers[0],'attempts':attempts,'results':results,'seconds':cmd['seconds'],'bundleSha256':m.directory_hash(p/'result.xcresult'),'attachmentsSha256':m.directory_hash(p/'attachments'),'commandSha256':m.sha256(p/'command.json'),'summarySha256':m.sha256(p/'summary.json'),'logSha256':m.sha256(p/'native.log'),'runfileSha256':m.sha256(p/'ACEClientAppUITests.xctestrun')})
assert len(rows)==6
by={v['phase']:v for v in rows}
for phase,enabled in [('001-on',True),('002-off',False)]:
 assert by[phase]['observed']=={'mode':'set','observed':{'boldText':enabled,'reduceMotion':enabled,'increaseContrast':enabled,'orientation':'portrait'}}
for name in ['iPhone 17','iPhone 17 Pro Max']:
 assert by[name+'-read']['observed']['observed']==by[name+'-restore-final']['observed']['observed']
for p in (e/'restoration').glob('*readback.json'):
 v=json.loads(p.read_text());assert v['expected']==v['observed']
for p in (e/'restoration').glob('*commands.json'):assert all(v['exit']==0 for v in json.loads(p.read_text()))
record={'status':'passed native integrity; inspect retained PNGs if any','verifiedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':x['candidate']['commit'],'checks':6,'unexpectedSkips':0,'coverageCases':0,'audits':0,'pilotCredit':0,'nativeSeconds':sum(v['seconds'] for v in rows),'restoration':'passed','settings':rows,'images':images,'sourceUnchangedDuringRun':True,'limitation':'Native pass confirms requested on/off states. Retry decisions are checked separately. A first-attempt success does not prove recovery of Apple lost input.'}
(e/'native-evidence-integrity.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='settings'}))
