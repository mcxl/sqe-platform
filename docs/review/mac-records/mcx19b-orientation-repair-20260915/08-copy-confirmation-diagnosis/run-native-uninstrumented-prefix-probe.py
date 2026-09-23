from pathlib import Path
import importlib.util, sys, os, json, datetime, subprocess, hashlib
os.umask(0o077)
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
evidence=stage/'08-copy-confirmation-diagnosis/native-uninstrumented-prefix-probe'
evidence.mkdir(parents=True, exist_ok=False)
spec=importlib.util.spec_from_file_location('margin_focus',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
candidate=m.candidate()
assert candidate['commit']=='15e4363c2ac074ceeea71599d1f2b64f67446487'
assert m.candidate()==candidate and candidate['status']=='clean'
assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip()
def states():
 data=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json'],text=True))['devices']
 wanted={'iPhone17':'2EB0863C-470E-467D-A0C6-CD216DA70C67','iPhone17ProMax':'D1BAA05C-52DD-4E57-832F-C0A75718E085','unrelated16ProMax':'3BF9AAA5-33AA-4EF3-BFEC-65C83DF5D79F'}
 return {n:next(d['state'] for group in data.values() for d in group if d['udid']==uid) for n,uid in wanted.items()}
record={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':candidate,'status':'running','question':'Does the original five-case sequence reproduce the contrast failure without the extra diagnostic frame queries?','scope':'original five-case iPhone17 light/large/portrait prefix, all flags off; diagnostic only','pilotCredit':0,'appCorrectionAttempt':0,'diagnosticProbe':3,'observerEffect':'Original test without extra frame logging; no app correction or pilot credit. A passing retry leaves cause unresolved.','initialBootStates':states(),'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
assert record['initialBootStates']=={'iPhone17':'Shutdown','iPhone17ProMax':'Booted','unrelated16ProMax':'Booted'}
(evidence/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
original=m.command
def observed(args,**kwargs):
 value=original(args,**kwargs)
 if len(args)>2 and args[:2]==['xcrun','simctl'] and args[2] in {'boot','shutdown','bootstatus'}:
  with (evidence/'simulator-commands.jsonl').open('a') as stream:stream.write(json.dumps(value)+'\n')
 return value
m.command=observed
cases=tuple(c for c in m.pilot_cases() if c.device=='iPhone 17' and c.settings.appearance=='light' and c.settings.contentSize=='large')
assert len(cases)==5
assert [c.scenario for c in cases]==['signIn','release','noConclusion','noActions','copyConfirmation']
code=2
try:
 result=m.run_coverage(cases,evidence,frozen_candidate=candidate)
 (evidence/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 assert result['caseCount']==5 and result['auditCount']==5 and result['auditInvocationCount']==9
 code=0
except Exception as exc:
 record['error']=str(exc)
finally:
 record.update(finishedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=code,status='native passed; image inspection pending' if code==0 else 'failed; evidence retained',candidateUnchanged=m.candidate()==candidate,finalBootStates=states())
 record['bootStatesRestored']=record['initialBootStates']==record['finalBootStates']
 if not record['candidateUnchanged'] or not record['bootStatesRestored']:code=2;record.update(exit=2,status='failed integrity or restoration')
 (evidence/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps(record,indent=2),flush=True)
sys.exit(code)
