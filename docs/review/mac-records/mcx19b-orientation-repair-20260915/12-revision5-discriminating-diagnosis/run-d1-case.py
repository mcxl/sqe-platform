"""One approved D1 case using unchanged runner primitives; not an acceptance run."""
import datetime, hashlib, importlib.util, json, os, pathlib, subprocess, sys, time

os.umask(0o077)
ROOT = pathlib.Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
STAGE = pathlib.Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/12-revision5-discriminating-diagnosis')
arm, repetition = sys.argv[1], int(sys.argv[2])
assert arm in {'A', 'B', 'C'} and 1 <= repetition <= 5
assert datetime.datetime.now(datetime.timezone.utc) < datetime.datetime.fromisoformat('2026-09-16T15:35:44+00:00')
assert not subprocess.run(['pgrep', '-x', 'xcodebuild'], capture_output=True, text=True).stdout.strip()
spec = importlib.util.spec_from_file_location('ace_local', ROOT / 'tools/ace_ios_local.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
preflight = json.loads((STAGE / 'preflight.json').read_text())
candidate = m.candidate()
assert candidate == preflight['candidate']
evidence = STAGE / f'arm-{arm}' / f'repetition-{repetition}'
evidence.mkdir(parents=True, exist_ok=False)
build = preflight['build'] if arm == 'A' else json.loads((STAGE / f'arm-{arm}-build.json').read_text())
template = pathlib.Path(build['template'])
assert m.sha256(template) == build['identity']
identifier = preflight['environment']['devices']['iPhone 17']['udid']
settings = m.Settings('light', 'large', 'portrait')
case = m.make_case('pilot', 'iPhone 17', 'copyConfirmation', settings, True)
question = {
    'A': 'Does unchanged copyConfirmation reproduce the native contrast finding?',
    'B': 'Does contrast fail when audit types execute separately, contrast first?',
    'C': 'Does unrestricted auditing fail with Copy placed in the upper viewport?',
}[arm]
record = {'arm': arm, 'repetition': repetition, 'case': case.payload(), 'question': question,
          'candidate': candidate['commit'], 'sourceHashes': candidate['sourceHashes'],
          'startedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'status': 'running', 'pilotCredit': 0, 'buildTemplate': str(template),
          'scriptSha256': m.sha256(pathlib.Path(__file__))}
def save():
    (evidence / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
def boot_states():
    data = json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json'],text=True))
    return {d['udid']:d['state'] for group in data['devices'].values() for d in group}
initial_states = boot_states()
record['initialBootStates'] = initial_states
save()
original_command = m.command
def observed_command(args, **kwargs):
    is_case = '-only-testing:' + m.COVERAGE_SELECTOR in args
    if is_case:
        kwargs['timeout'] = 360
    print(json.dumps({'phase':'native-case' if is_case else 'support', 'command':args[:3], 'time':datetime.datetime.now(datetime.timezone.utc).isoformat()}), flush=True)
    result = original_command(args, **kwargs)
    with (evidence / 'command-index.jsonl').open('a') as stream:
        stream.write(json.dumps({k:v for k,v in result.items() if k not in {'stdout','stderr'}}) + '\n')
    return result
m.command = observed_command
previous = None
previous_flags = None
restoration_failures = []
exit_code = 2
try:
    m.boot_required_simulator(identifier, initial_states[identifier])
    previous = m.current_simctl_settings(identifier)
    previous_flags = m.native_flags(identifier, template, evidence, 'initial-read', {'mode':'read'})
    record['originalSimctlSettings'] = previous
    record['originalNativeSettings'] = previous_flags
    save()
    desired = {'boldText':False,'reduceMotion':False,'increaseContrast':False,'orientation':'portrait'}
    if previous_flags != desired:
        m.native_flags(identifier, template, evidence, 'requested-set', {'mode':'set',**desired})
    try:
        batch = m.run_batch('iPhone 17', identifier, settings, (case,), build, evidence, 1)
        record['batch'] = batch
        record['status'] = 'native-pass; image inspection pending'
        exit_code = 0
    except m.RunnerError as error:
        record['nativeError'] = str(error)
        batch_root = evidence / 'batches/001'
        command_file = batch_root / 'native-command.json'
        summary_file = batch_root / 'native-summary.json'
        assert command_file.is_file() and summary_file.is_file(), 'Missing native command or summary evidence'
        process = json.loads(command_file.read_text())
        summary = json.loads(summary_file.read_text())
        log = batch_root / 'native.log'
        issues = m.marker_records(log, 'ACE_A11Y_ISSUE ')
        manifest = batch_root / 'attachments/manifest.json'
        assert manifest.is_file(), 'Missing attachment manifest'
        assert summary.get('totalTestCount') == 1 and summary.get('skippedTests') == 0, 'Incomplete native test count'
        assert process.get('exit') == 65 and not process.get('timedOut') and issues, 'Non-audit failure or incomplete case'
        record.update(status='native-audit-findings; image inspection pending', findings=issues,
                      nativeExit=process['exit'], nativeSummary=summary,
                      resultBundle=str(batch_root/'result.xcresult'),
                      resultBundleSha256=m.directory_hash(batch_root/'result.xcresult'),
                      attachmentSha256=m.directory_hash(batch_root/'attachments'))
        exit_code = 0
except Exception as error:
    record.update(status='blocked', error=str(error))
finally:
    try:
        if m.simulator_state(identifier) == 'Booted':
            restoration_failures.extend(m.restore_device_configuration(identifier, previous, previous_flags, template, evidence, 'iPhone 17', 'D1'))
        m.restore_boot_state(identifier, initial_states[identifier])
    except Exception as error:
        restoration_failures.append(str(error))
    record['finalBootStates'] = boot_states()
    record['restorationFailures'] = restoration_failures
    record['candidateUnchanged'] = m.candidate() == candidate
    if restoration_failures or record['finalBootStates'] != initial_states or not record['candidateUnchanged']:
        exit_code = 2
        record['status'] = 'blocked integrity or restoration'
    record.update(finishedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), orchestrationExit=exit_code)
    save()
    print(json.dumps({k:record.get(k) for k in ['arm','repetition','status','nativeError','error','findings','restorationFailures','candidateUnchanged','orchestrationExit']}), flush=True)
sys.exit(exit_code)
