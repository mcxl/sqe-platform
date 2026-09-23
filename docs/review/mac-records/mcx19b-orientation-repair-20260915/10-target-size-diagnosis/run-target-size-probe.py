from pathlib import Path
import importlib.util, sys, os, json, datetime, subprocess, hashlib
os.umask(0o077)
root=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/10-target-size-diagnosis/target-size-probe-worktree')
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
evidence=stage/'10-target-size-diagnosis/native-target-probe'
evidence.mkdir(parents=True, exist_ok=False)
spec=importlib.util.spec_from_file_location('margin_focus',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
candidate=m.candidate()
assert candidate['commit']=='f5bd9c43cb1bf6dfb45986b9e5df420be28ad9d2'
assert m.candidate()==candidate and candidate['status']=='clean'
assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip()
def states():
 data=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json'],text=True))['devices']
 wanted={'iPhone17':'2EB0863C-470E-467D-A0C6-CD216DA70C67','iPhone17ProMax':'D1BAA05C-52DD-4E57-832F-C0A75718E085','unrelated16ProMax':'3BF9AAA5-33AA-4EF3-BFEC-65C83DF5D79F'}
 return {n:next(d['state'] for group in data.values() for d in group if d['udid']==uid) for n,uid in wanted.items()}
record={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':candidate,'status':'running','question':'What exact frame and numeric deficit does the medium-text Refresh target check measure?','scope':'single iPhone17 release,light/medium/portrait,all flags off; diagnostic only','pilotCredit':0,'appCorrectionAttempt':0,'testHelperCorrectionAttempt':0,'diagnosticProbe':1,'observerEffect':'Diagnostic test captures one native frame for checks and logs its exact dimensions. Criteria and app are unchanged. Query timing changes; no pilot credit.','initialBootStates':states(),'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
assert record['initialBootStates']=={'iPhone17':'Shutdown','iPhone17ProMax':'Booted','unrelated16ProMax':'Booted'}
(evidence/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
original=m.command
def observed(args,**kwargs):
 value=original(args,**kwargs)
 if len(args)>2 and args[:2]==['xcrun','simctl'] and args[2] in {'boot','shutdown','bootstatus'}:
  with (evidence/'simulator-commands.jsonl').open('a') as stream:stream.write(json.dumps(value)+'\n')
 return value
m.command=observed
cases=tuple(c for c in m.pilot_cases() if c.device=='iPhone 17' and c.scenario=='release' and not c.audit)
assert len(cases)==1
assert cases[0].settings.orientation=='portrait' and not cases[0].audit
code=2
try:
 result=m.run_coverage(cases,evidence,frozen_candidate=candidate)
 (evidence/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 assert result['caseCount']==1 and result['auditCount']==0 and result['auditInvocationCount']==0
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
