from pathlib import Path
import importlib.util,sys,json,os,subprocess,datetime,hashlib
os.umask(0o077)
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
spec=importlib.util.spec_from_file_location('shutdown_pilot',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
candidate=json.loads((stage/'shutdown-clean-candidate.json').read_text())
assert m.candidate()==candidate and candidate['status']=='clean'
paths={role:stage/'shutdown-readiness'/(role+'-readiness.json') for role in m.READINESS_ROLES}
m.pilot_readiness(candidate,paths)
gate=json.loads((stage/'06-shutdown-native-gate/result.json').read_text())
assert gate['status']=='native gate passed; image inspection pending'
inspection=json.loads((stage/'06-shutdown-native-gate/image-inspection.json').read_text())
assert inspection['status']=='passed' and inspection['candidate']==candidate
assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip()
def states():
    all_devices=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json'],text=True))['devices']
    wanted={'iPhone17':'2EB0863C-470E-467D-A0C6-CD216DA70C67','iPhone17ProMax':'D1BAA05C-52DD-4E57-832F-C0A75718E085','unrelated16ProMax':'3BF9AAA5-33AA-4EF3-BFEC-65C83DF5D79F'}
    return {name:next(d['state'] for group in all_devices.values() for d in group if d['udid']==uid) for name,uid in wanted.items()}
power=subprocess.check_output(['pmset','-g','custom'],text=True)
assert all(line.split()[-1]=='0' for line in power.splitlines() if 'lowpowermode' in line)
record={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':candidate,'status':'running','scope':'22cases,20auditcases,2layout-onlycases,36nativeauditinvocations','initialBootStates':states(),'lowPowerSettings':power,'executionScriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
assert record['initialBootStates']=={'iPhone17':'Shutdown','iPhone17ProMax':'Booted','unrelated16ProMax':'Booted'}
(stage/'shutdown-pilot-execution.json').write_text(json.dumps(record,indent=2)+'\n')
args=['--evidence-root',str(stage/'shutdown-pilot-runs'),'pilot','--pocock-evidence',str(paths['pocock']),'--functional-evidence',str(paths['functional']),'--evidence-gate',str(paths['evidence-gate']),'--private-input-record',str(paths['private-input'])]
original_command=m.command
def retain_simctl_commands(args, **kwargs):
    value=original_command(args, **kwargs)
    if len(args)>2 and args[:2]==['xcrun','simctl'] and args[2] in {'boot','shutdown','bootstatus'}:
        with (stage/'shutdown-pilot-simulator-commands.jsonl').open('a') as stream:
            stream.write(json.dumps(value)+'\n')
    return value
m.command=retain_simctl_commands
code=m.main(args)
record.update(finishedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=code,status='native passed; inspection pending' if code==0 else 'failed; evidence retained',candidateUnchanged=m.candidate()==candidate,finalBootStates=states())
record['bootStatesRestored']=record['initialBootStates']==record['finalBootStates']
(stage/'shutdown-pilot-execution.json').write_text(json.dumps(record,indent=2)+'\n')
sys.exit(code if record['candidateUnchanged'] and record['bootStatesRestored'] else 2)
