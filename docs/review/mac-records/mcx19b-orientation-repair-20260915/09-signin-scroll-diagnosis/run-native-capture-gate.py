from pathlib import Path
import importlib.util,sys,json,subprocess,datetime,os
os.umask(0o077)
s=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
repo=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
probe=s/'09-signin-scroll-diagnosis/capture-negative-worktree'
out=s/'09-signin-scroll-diagnosis/native-capture-evidence-gate'
out.mkdir(mode=0o700,exist_ok=False)
def load(root,name):
    sp=importlib.util.spec_from_file_location(name,root/'tools/ace_ios_local.py')
    module=importlib.util.module_from_spec(sp);sys.modules[name]=module;sp.loader.exec_module(module);return module
m=load(repo,'shutdown_positive');n=load(probe,'shutdown_negative')
def retain_simctl_commands(module, label):
    original=module.command
    def recorded(args, **kwargs):
        value=original(args, **kwargs)
        if len(args)>2 and args[:2]==['xcrun','simctl'] and args[2] in {'boot','shutdown','bootstatus'}:
            with (out/'simulator-commands.jsonl').open('a') as stream:
                stream.write(json.dumps({'phase':label, 'record':value})+'\n')
        return value
    module.command=recorded
retain_simctl_commands(m, 'positive')
retain_simctl_commands(n, 'negative')
original_negative_candidate=n.candidate
n.candidate=lambda allow_dirty=False:original_negative_candidate(allow_dirty=True)
positive=m.candidate();negative=n.candidate()
assert positive['commit']=='c8b10875658e5fbd6a66dea1fbcec9bb4a2f5b0d'
focus=s/'09-signin-scroll-diagnosis/native-screen-focus-v1'
focus_execution=json.loads((focus/'execution.json').read_text())
assert focus_execution['exit']==0 and focus_execution['candidateUnchanged'] and focus_execution['bootStatesRestored']
assert json.loads((focus/'image-inspection.json').read_text())['status']=='passed'
focus_result=json.loads((focus/'result.json').read_text())
assert focus_result['candidate']==positive
build_record=focus_result['build']
assert m.sha256(Path(build_record['template']))==build_record['identity'] and m.directory_hash(Path(build_record['products']))==build_record['productSha256']
(out/'reused-positive-build.json').write_text(json.dumps(build_record,indent=2)+'\n')
def positive_build(current,evidence,scheme=m.SCHEME):
    assert current==positive and scheme==m.SCHEME
    assert m.directory_hash(Path(build_record['products']))==build_record['productSha256']
    return build_record
m.build=positive_build
assert positive['status']=='clean'
different=[p for p,h in positive['sourceHashes'].items() if negative['sourceHashes'].get(p)!=h]
assert different==['ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift'],different
assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip()
result={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'running','positiveCandidate':positive,'negativeCandidate':negative,'question':'Does the new full-screen capture survive a deliberate native failure with its exact assertion, and does the identical case pass without the injection?','scope':'One medium-text portrait/light release layout case on iPhone17. No audits or pilot acceptance credit.','checks':{}}
def save(phase):
    result['phase']=phase
    (out/'progress.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'phase':phase,'evidence':str(out)}),flush=True)
def boot_states():
    return {name:m.simulator_state(identifier) for name,identifier in [('iPhone17','2EB0863C-470E-467D-A0C6-CD216DA70C67'),('iPhone17ProMax','D1BAA05C-52DD-4E57-832F-C0A75718E085'),('unrelated16ProMax','3BF9AAA5-33AA-4EF3-BFEC-65C83DF5D79F')]}
try:
    result['initialBootStates']=boot_states()
    assert result['initialBootStates']=={'iPhone17':'Shutdown','iPhone17ProMax':'Booted','unrelated16ProMax':'Booted'}
    power=subprocess.check_output(['pmset','-g','custom'],text=True)
    assert all(x.split()[-1]=='0' for x in power.splitlines() if 'lowpowermode' in x)
    result['lowPowerSettings']=power
    case=next(c for c in n.pilot_cases() if c.device=='iPhone 17' and not c.audit)
    failure_root=out/'negative';failure_root.mkdir()
    save('deliberate failure after full-screen capture; expected native failure')
    caught=None
    try:n.run_coverage((case,),failure_root,frozen_candidate=negative)
    except n.RunnerError as error:caught=str(error)
    assert caught is not None,'Deliberate negative unexpectedly passed'
    final=json.loads((failure_root/'coverage-final-failure.json').read_text())
    assert final['restorationFailures']==[] and final['completedBatches']==[],final
    command=json.loads((failure_root/'batches/001/native-command.json').read_text())
    summary=json.loads((failure_root/'batches/001/native-summary.json').read_text())
    assert command['exit']==65 and summary['failedTests']==1 and summary['passedTests']==0 and summary['skippedTests']==0,summary
    assert len(summary['testFailures'])==1 and 'ACE_CAPTURE_GATE_INTENTIONAL_FAILURE after retained initial viewport' in summary['testFailures'][0]['failureText'],summary
    assert boot_states()==result['initialBootStates']
    assert n.candidate()==negative and m.candidate()==positive
    result['checks']['deliberateFailure']={'status':'expected failure verified','error':caught,'nativeSummary':summary,'finalFailure':final,'bootStates':boot_states()}
    save('same release layout case without injected failure; expected pass')
    pass_root=out/'positive';pass_root.mkdir()
    positive_case=next(c for c in m.pilot_cases() if c.device=='iPhone 17' and not c.audit)
    actual=m.run_coverage((positive_case,),pass_root,frozen_candidate=positive)
    assert actual['caseCount']==1 and actual['executedCaseCount']==1 and actual['auditCount']==0 and actual['layoutCount']==1
    assert actual['auditInvocationCount']==0 and actual['nativeTestCount']==1 and len(actual['batches'])==1
    assert boot_states()==result['initialBootStates']
    result['checks']['correctedCase']={'status':'passed','result':actual,'manifest':str(m.write_manifest(pass_root,actual,'diagnostic')),'bootStates':boot_states()}
    result['status']='native gate passed; image inspection pending'
except Exception as error:
    result['status']='failed';result['error']=str(error)
finally:
    result['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['finalBootStates']=boot_states()
    result['positiveCandidateUnchanged']=m.candidate()==positive
    result['negativeCandidateUnchanged']=n.candidate()==negative
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    save('complete')
print(json.dumps({'status':result['status'],'error':result.get('error'),'evidence':str(out)}),flush=True)
sys.exit(0 if result['status'].startswith('native gate passed') and result['positiveCandidateUnchanged'] and result['negativeCandidateUnchanged'] and result['finalBootStates']==result['initialBootStates'] else 2)
