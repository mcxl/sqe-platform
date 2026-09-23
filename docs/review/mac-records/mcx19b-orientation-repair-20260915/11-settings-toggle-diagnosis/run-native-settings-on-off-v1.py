from pathlib import Path
import importlib.util,sys,json,os,subprocess,datetime,hashlib
os.umask(0o077)
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
d=stage/'11-settings-toggle-diagnosis'
spec=importlib.util.spec_from_file_location('settings_focus',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
frozen=json.loads((d/'clean-candidate.json').read_text())
assert m.candidate()==frozen and frozen['status']=='clean'
assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip()
e=d/'native-settings-on-off-v1';e.mkdir(exist_ok=False)
ids={'iPhone 17':'2EB0863C-470E-467D-A0C6-CD216DA70C67','iPhone 17 Pro Max':'D1BAA05C-52DD-4E57-832F-C0A75718E085'}
other='3BF9AAA5-33AA-4EF3-BFEC-65C83DF5D79F'
initial={name:m.simulator_state(uid) for name,uid in ids.items()}
other_state=m.simulator_state(other)
record={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':frozen,'status':'running','question':'Does bounded Settings setup enable and disable the requested flags, retain first-miss evidence, and verify the actual values inside the app?','scope':'Native Settings only; no coverage cases or audits. Deterministic recovery checks are separate.','pilotCredit':0,'correctiveAttempt':1,'initialBootStates':initial,'unrelatedInitialBootState':other_state,'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def save(): (e/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
save()
original=m.command
def retain(args,**kwargs):
 value=original(args,**kwargs)
 if len(args)>2 and args[:2]==['xcrun','simctl'] and args[2] in {'boot','shutdown','bootstatus'}:
  with (e/'simulator-commands.jsonl').open('a') as stream:stream.write(json.dumps(value)+'\n')
 return value
m.command=retain
previous={};native={};template=None;restoration=[];code=2
try:
 env=m.preflight();record['environment']=env;save()
 build=m.build(frozen,e);template=Path(build['template'])
 (e/'build-record.json').write_text(json.dumps(build,indent=2)+'\n')
 for name,uid in ids.items():
  if initial[name]=='Booted':
   previous[name]=m.current_simctl_settings(uid)
   native[name]=m.native_flags(uid,template,e,name+'-read',{'mode':'read'})
   m.checked(['xcrun','simctl','shutdown',uid],timeout=120)
 name='iPhone 17';uid=ids[name]
 m.boot_required_simulator(uid,m.simulator_state(uid))
 previous[name]=m.current_simctl_settings(uid)
 native[name]=m.native_flags(uid,template,e,name+'-read',{'mode':'read'})
 record['initialNativeSettings']=native;record['initialSimctlSettings']=previous;save()
 for phase,enabled in [('001-on',True),('002-off',False)]:
  assert m.candidate()==frozen
  request={'mode':'set','boldText':enabled,'reduceMotion':enabled,'increaseContrast':enabled,'orientation':'portrait'}
  observed=m.native_flags(uid,template,e,phase,request)
  assert observed=={k:v for k,v in request.items() if k!='mode'}
  record[phase]=observed;save()
 code=0
except Exception as exc:
 record['error']=str(exc)
finally:
 if template is not None:
  for name,uid in ids.items():
   try:
    if name in native:
     m.boot_required_simulator(uid,m.simulator_state(uid))
     restoration.extend(m.restore_device_configuration(uid,previous[name],native[name],template,e,name,'final'))
    if initial[name]=='Shutdown':m.restore_boot_state(uid,'Shutdown')
    else:m.boot_required_simulator(uid,m.simulator_state(uid))
   except Exception as exc:restoration.append(name+':'+str(exc))
 record.update(finishedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),nativeExit=code,restorationFailures=restoration,finalBootStates={name:m.simulator_state(uid) for name,uid in ids.items()},unrelatedFinalBootState=m.simulator_state(other),candidateUnchanged=m.candidate()==frozen)
 record['bootStatesRestored']=record['finalBootStates']==initial and record['unrelatedFinalBootState']==other_state
 if restoration or not record['bootStatesRestored'] or not record['candidateUnchanged']:code=2
 record.update(exit=code,status='native passed; evidence inspection pending' if code==0 else 'failed; evidence retained')
 save();print(json.dumps(record),flush=True)
sys.exit(code)
