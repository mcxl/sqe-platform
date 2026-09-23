from pathlib import Path
import importlib.util,sys,json,os,subprocess,datetime,hashlib
os.umask(0o077)
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
d=stage/'10-target-size-diagnosis'
spec=importlib.util.spec_from_file_location('capture_pilot',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
candidate=json.loads((d/'clean-candidate.json').read_text())
assert m.candidate()==candidate and candidate['status']=='clean'
assert candidate['commit']=='c0e53738d15f677f9fd69b4d1eeba9f228ac51d1'
focus=d/'native-measurement-focus-v1'
x=json.loads((focus/'execution.json').read_text())
assert x['exit']==0 and x['candidateUnchanged'] and x['bootStatesRestored']
assert json.loads((focus/'image-inspection.json').read_text())['status']=='passed'
f=json.loads((focus/'result.json').read_text());assert f['candidate']==candidate
assert (f['caseCount'],f['auditCount'],f['auditInvocationCount'])==(1,0,0)
gate=json.loads((d/'capture-gate-integrity.json').read_text())
assert gate['status']=='passed' and gate['candidate']==candidate['commit']
assert json.loads((d/'gate-image-inspection.json').read_text())['status']=='passed'
paths={role:d/'readiness'/(role+'-readiness.json') for role in m.READINESS_ROLES}
m.pilot_readiness(candidate,paths)
# Current Pocock readiness is required above. Fresh final Sol review follows native and image verification.
assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip()
def states():
 all_devices=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json'],text=True))['devices']
 wanted={'iPhone17':'2EB0863C-470E-467D-A0C6-CD216DA70C67','iPhone17ProMax':'D1BAA05C-52DD-4E57-832F-C0A75718E085','unrelated16ProMax':'3BF9AAA5-33AA-4EF3-BFEC-65C83DF5D79F'}
 return {name:next(v['state'] for group in all_devices.values() for v in group if v['udid']==uid) for name,uid in wanted.items()}
power=subprocess.check_output(['pmset','-g','custom'],text=True)
assert all(line.split()[-1]=='0' for line in power.splitlines() if 'lowpowermode' in line)
record={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':candidate,'status':'running','scope':'22 cases,20 audited cases,2 layout-only cases,36 unrestricted native audit invocations','initialBootStates':states(),'lowPowerSettings':power,'executionScriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'purpose':'Complete approved 22-case pilot after focused numerical comparison correction. Historical failures remain retained and unresolved causes remain explicit. No836 expansion.','historicalCauses':'Intermittent Copy contrast, Settings missed tap, prior timeout remain unexplained. This execution does not prove their causes.','acceptance':'Pending native results, complete image inspection, evidence integrity, restoration, private archive/retrieval and final review.'}
assert record['initialBootStates']=={'iPhone17':'Shutdown','iPhone17ProMax':'Booted','unrelated16ProMax':'Booted'}
execution=d/'complete-pilot-execution.json';execution.write_text(json.dumps(record,indent=2)+'\n')
build_record=f['build']
assert m.sha256(Path(build_record['template']))==build_record['identity']
assert m.directory_hash(Path(build_record['products']))==build_record['productSha256']
assert m.directory_hash(Path(build_record['buildResultBundle']))==build_record['buildResultBundleSha256']
(d/'complete-pilot-reused-build.json').write_text(json.dumps(build_record,indent=2)+'\n')
def reuse_build(current,evidence,scheme=m.SCHEME):
 assert current==candidate and scheme==m.SCHEME
 assert m.environment_identity(m.preflight())==m.environment_identity(f['environment'])
 assert m.sha256(Path(build_record['template']))==build_record['identity']
 assert m.directory_hash(Path(build_record['products']))==build_record['productSha256']
 return build_record
m.build=reuse_build
original=m.command
def retain(args,**kwargs):
 value=original(args,**kwargs)
 if len(args)>2 and args[:2]==['xcrun','simctl'] and args[2] in {'boot','shutdown','bootstatus'}:
  with (d/'complete-pilot-simulator-commands.jsonl').open('a') as stream:stream.write(json.dumps(value)+'\n')
 return value
m.command=retain
args=['--evidence-root',str(d/'complete-pilot-runs'),'pilot','--pocock-evidence',str(paths['pocock']),'--functional-evidence',str(paths['functional']),'--evidence-gate',str(paths['evidence-gate']),'--private-input-record',str(paths['private-input'])]
code=m.main(args)
record.update(finishedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=code,status='native passed; image/evidence review pending' if code==0 else 'failed; evidence retained',candidateUnchanged=m.candidate()==candidate,finalBootStates=states())
record['bootStatesRestored']=record['initialBootStates']==record['finalBootStates']
execution.write_text(json.dumps(record,indent=2)+'\n')
sys.exit(code if record['candidateUnchanged'] and record['bootStatesRestored'] else 2)
