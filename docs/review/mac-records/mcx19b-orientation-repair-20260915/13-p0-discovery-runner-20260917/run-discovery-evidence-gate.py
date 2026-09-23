"""Diagnostic input fault; no application, native-test or candidate file changes."""
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.umask(0o077)
sys.dont_write_bytecode = True
repo = Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
stage = Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/13-p0-discovery-runner-20260917')
gate = stage / 'native-evidence-gate'

def now():
    return datetime.now(timezone.utc)

if now() >= datetime.fromisoformat('2026-09-16T21:33:00+00:00'):
    raise SystemExit('Start withheld: insufficient reserved time before block deadline.')
gate.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('ace', repo / 'tools/ace_ios_local.py')
ace = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ace
spec.loader.exec_module(ace)
identity = json.loads((stage / 'clean-candidate.json').read_text())
assert ace.candidate() == identity
case = ace.make_case('evidence-gate', 'iPhone 17', 'signIn', ace.Settings('light', 'large', 'portrait'), False)
original_commands = ace.setting_commands
record = {
    'candidate': identity,
    'startedUTC': now().isoformat(),
    'controllerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'question': 'Does discovery retain and block a deliberate native settings mismatch, then pass the same case after correcting that input?',
    'negativeExpected': 'Native observed-settings assertion fails: requested light; actual dark. Discovery blocks and restores settings.',
    'positiveExpected': 'Same layout-only sign-in case passes with actual light matching requested light; images retained and settings restored.',
    'variable': 'Actual simulator appearance only; app, native assertions, runner file, case payload and requested settings remain unchanged.',
    'acceptanceCredit': 0,
    'scopeLimit': 'This checks native failure/pass capture and blocking. Continuing after a genuine audit finding is covered by parser/orchestration fixtures, not claimed as a live native observation here.',
}

def wrong_appearance(identifier, settings):
    commands = [list(command) for command in original_commands(identifier, settings)]
    assert commands[0][4:] == ['appearance', 'light']
    commands[0][-1] = 'dark'
    return tuple(commands)

try:
    negative = gate / 'negative'
    negative.mkdir()
    ace.setting_commands = wrong_appearance
    print(json.dumps({'phase': 'negative-started', 'atUTC': now().isoformat()}), flush=True)
    try:
        ace.run_discovery((case,), negative, identity)
    except ace.RunnerError as error:
        record['negativeRunnerError'] = str(error)
    else:
        raise RuntimeError('Deliberate settings mismatch did not block discovery.')
    finally:
        ace.setting_commands = original_commands
    batch = negative / 'batches' / '001'
    summary = json.loads((batch / 'native-summary.json').read_text())
    assert (summary['result'], summary['totalTestCount'], summary['failedTests'], summary['passedTests'], summary['skippedTests'], summary['expectedFailures']) == ('Failed', 1, 1, 0, 0, 0)
    failures = summary['testFailures']
    assert failures and all('Observed settings differ from requested settings' in failure['failureText'] for failure in failures)
    restoration = json.loads((negative / 'coverage-final-failure.json').read_text())
    assert restoration['restorationFailures'] == []
    assert ace.candidate() == identity
    record['negative'] = {'status': 'failed-as-designed', 'nativeSummary': summary,
        'bundle': str(batch / 'result.xcresult'), 'bundleSha256': ace.directory_hash(batch / 'result.xcresult'),
        'attachmentsSha256': ace.directory_hash(batch / 'attachments'), 'logSha256': ace.sha256(batch / 'native.log'),
        'restorationFailures': [], 'exportedImages': list(ace.attachment_name_map(batch / 'attachments').values())}
    print(json.dumps({'phase': 'negative-verified', 'atUTC': now().isoformat()}), flush=True)
    if now() >= datetime.fromisoformat('2026-09-16T21:41:00+00:00'):
        raise RuntimeError('Corrected pass withheld to preserve restoration time before block deadline.')
    positive = gate / 'positive'
    positive.mkdir()
    result = ace.run_discovery((case,), positive, identity)
    assert (result['status'], result['passedCaseCount'], result['failedCaseCount'], result['nativeTestCount']) == ('completed', 1, 0, 1)
    assert result['auditInvocationCount'] == 0
    manifest = ace.write_manifest(positive, result, 'evidence-gate-positive')
    assert ace.candidate() == identity
    record['positive'] = {'status': 'passed', 'manifest': str(manifest), 'manifestSha256': ace.sha256(manifest)}
    record['status'] = 'native-capture-passed-image-review-pending'
    exit_code = 0
except Exception as error:
    record.update(status='blocked', error=str(error), errorType=type(error).__name__)
    exit_code = 2
finally:
    ace.setting_commands = original_commands
    record['endedUTC'] = now().isoformat()
    (gate / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'status': record['status'], 'evidence': str(gate / 'result.json')}), flush=True)
sys.exit(exit_code)
