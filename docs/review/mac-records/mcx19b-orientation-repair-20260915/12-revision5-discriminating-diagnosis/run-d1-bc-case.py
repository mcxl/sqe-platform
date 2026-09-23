"""Private Revision 5 B/C evidence wrapper. Never awards acceptance credit."""
import collections
import datetime
import importlib.util
import json
import math
import os
import pathlib
import plistlib
import re
import subprocess
import sys

ROOT = pathlib.Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
STAGE = pathlib.Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/12-revision5-discriminating-diagnosis')
PATCH_HASH = '41a4aa36b13b93ee65011ef8590d9aed0cdf69eac11cbde765c34942a6aca9f1'
TYPES = ('contrast', 'elementDetection', 'hitRegion', 'sufficientElementDescription', 'dynamicType', 'textClipped', 'trait')
VIEWPORTS = ('initial', 'copy-confirmation')
START_CUTOFF = datetime.datetime.fromisoformat('2026-09-16T15:35:44+00:00')
DEADLINE = datetime.datetime.fromisoformat('2026-09-16T15:47:44+00:00')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def read_json(path):
    return json.loads(path.read_text())


def request_environment(environment, arm, repetition):
    environment = dict(environment)
    if 'ACE_COVERAGE_CASES_JSON' in environment:
        environment.update(ACE_D1_ARM=arm, ACE_D1_REPETITION=str(repetition))
    else:
        require(not any(k.startswith('ACE_D1_') for k in environment), 'D1 request in settings configuration')
    return environment


def frame_valid(frame):
    return (isinstance(frame, dict) and set(frame) == {'x', 'y', 'width', 'height'}
            and all(type(v) in (int, float) and math.isfinite(v) for v in frame.values())
            and frame['width'] >= 0 and frame['height'] >= 0)


def validate_diagnostic(arm, repetition, calls, issues, completions, errors, placements):
    """Pure-data gate; attempts with unknown thrown errors are never collected."""
    expected = [(viewport, name) for viewport in VIEWPORTS for name in (TYPES if arm == 'B' else ('all',))]
    require([(c.get('viewport'), c.get('auditName')) for c in calls] == expected,
            'Missing, duplicated, reordered, or unexpected audit calls')
    for item in calls + issues + completions + errors:
        require(item.get('arm') == arm and item.get('repetition') == str(repetition), 'Wrong diagnostic arm/repetition')
    grouped = collections.defaultdict(list)
    for issue in issues:
        key = (issue.get('viewport'), issue.get('requestedAuditName'))
        require(key in expected, 'Unexpected issue audit/viewport')
        require(type(issue.get('auditTypeRawValue')) is int and issue['auditTypeRawValue'] > 0, 'Missing raw audit type')
        for field in ('auditType', 'compactDescription', 'detailedDescription', 'callbackEvidence'):
            require(isinstance(issue.get(field), str) and issue[field], 'Missing issue ' + field)
        element = issue.get('element')
        require(isinstance(element, dict) and all(isinstance(element.get(k), str) for k in ('identifier', 'label', 'type')),
                'Missing issue element identity')
        unavailable = element == {'identifier': '', 'label': '', 'type': 'unavailable'}
        require(unavailable or frame_valid(element.get('frame')), 'Missing or invalid frame for an available audit element')
        for field in ('auditStartUptimeSeconds', 'callbackElapsedSeconds'):
            require(type(issue.get(field)) in (int, float) and math.isfinite(issue[field]) and issue[field] >= 0,
                    'Missing callback timing')
        require('not the audit sample rendering' in issue['callbackEvidence'], 'Callback evidence has incorrect standing')
        grouped[key].append(issue)
    expected_errors = []
    returned_by_viewport = collections.Counter()
    for call in calls:
        key = (call['viewport'], call['auditName'])
        require(type(call.get('returnedNormally')) is bool and type(call.get('issueObserved')) is bool,
                'Audit call flags are invalid')
        require(call['issueObserved'] == bool(grouped[key]), 'Issue count contradicts audit call')
        if call['returnedNormally']:
            require(call.get('error') is None, 'Normal return includes error')
            returned_by_viewport[call['viewport']] += 1
        else:
            error = call.get('error')
            require(isinstance(error, str) and error, 'Thrown audit lacks error')
            # No generic XCTest-error allowlist: exact same-call native finding evidence is required.
            known = {i[k] for i in grouped[key] for k in ('compactDescription', 'detailedDescription')}
            require(error in known, 'Ambiguous/infrastructure audit error: ' + error)
            expected_errors.append({'arm': arm, 'repetition': str(repetition), 'viewport': key[0], 'auditName': key[1], 'error': error})
    require(errors == expected_errors, 'Audit error markers disagree with per-call evidence')
    require(len(completions) == 1, 'Expected exactly one diagnostic completion marker')
    completion = completions[0]
    expected_per_viewport = len(TYPES) if arm == 'B' else 1
    complete_viewports = sorted(v for v in VIEWPORTS if returned_by_viewport[v] == expected_per_viewport)
    aggregate = {
        'expectedAuditCalls': len(expected), 'attemptedAuditCalls': len(calls),
        'returnedNormallyAuditCalls': sum(returned_by_viewport.values()),
        'completedViewports': complete_viewports,
        'bothViewportAuditGroupsCompleted': complete_viewports == sorted(VIEWPORTS),
        'allAuditTypesAttempted': True,
        'allAuditCallsReturnedNormally': sum(returned_by_viewport.values()) == len(expected),
        'callbackIssueCount': len(issues), 'auditErrors': [e['error'] for e in expected_errors],
    }
    for key, value in aggregate.items():
        require(type(completion.get(key)) is type(value) and completion[key] == value, 'Completion mismatch: ' + key)
    if arm == 'C':
        require(len(placements) == 1, 'Missing/duplicate C placement evidence')
        p = placements[0]
        require(p.get('repetition') == str(repetition) and p.get('twoFrameReadsIdentical') is True,
                'C placement repetition or settle check failed')
        require(frame_valid(p.get('firstFrame')) and frame_valid(p.get('secondFrame')) and frame_valid(p.get('viewport')),
                'C placement frames invalid')
        f, v = p['firstFrame'], p['viewport']
        require(f == p['secondFrame'] and f['width'] > 0 and f['height'] > 0
                and p.get('midpoint') == v['y'] + v['height'] / 2
                and f['x'] >= v['x'] and f['x'] + f['width'] <= v['x'] + v['width']
                and f['y'] >= v['y'] and f['y'] + f['height'] < p['midpoint'], 'C placement geometry failed')
    else:
        require(not placements, 'Arm B unexpectedly contains C placement')
    return grouped


def validate_native(process, summary, issues, calls, case_records):
    require(not process.get('timedOut') and process.get('exit') in (0, 65), 'Native execution incomplete/abnormal')
    for field, expected in {'totalTestCount': 1, 'skippedTests': 0, 'expectedFailures': 0}.items():
        require(type(summary.get(field)) is int and summary[field] == expected, 'Incomplete native count: ' + field)
    failed = bool(issues)
    for field, expected in {'passedTests': int(not failed), 'failedTests': int(failed),
                            'result': 'Failed' if failed else 'Passed'}.items():
        require(type(summary.get(field)) is type(expected) and summary[field] == expected, 'Native outcome contradiction: ' + field)
    require(process['exit'] == (65 if failed else 0), 'Native exit does not match findings')
    failures = summary.get('testFailures')
    require(isinstance(failures, list), 'Native failure list absent')
    if failed:
        require(not case_records, 'A native finding must not have a passed case marker')
        require(bool(failures), 'Native finding lacks native failure record')
        allowed = {i[k] for i in issues for k in ('compactDescription', 'detailedDescription')}
        if any(not c['returnedNormally'] for c in calls):
            allowed.add('D1 did not complete every required audit call')
        for failure in failures:
            require(failure.get('targetName') == 'ACEClientAppUITests'
                    and failure.get('testIdentifierString') == 'ACEClientAppUITests/testCoverageBatch()'
                    and failure.get('failureText') in allowed, 'Unclassified native failure: ' + str(failure))
        require(all(any(f.get('failureText') in {i['compactDescription'], i['detailedDescription']} for f in failures) for i in issues),
                'A callback finding lacks a matching native failure')
    else:
        require(not failures and len(case_records) == 1, 'Clean case missing pass evidence')
    return 'FAILED' if failed else 'PASSED'


def validate_attachments(directory, case_id, arm, repetition, grouped):
    manifest = read_json(directory / 'manifest.json')
    require(isinstance(manifest, list) and len(manifest) == 1, 'Attachment manifest test count differs')
    entry = manifest[0]
    require(entry.get('testIdentifier') == 'ACEClientAppUITests/testCoverageBatch()', 'Wrong attachment test')
    values = entry.get('attachments')
    require(isinstance(values, list) and values, 'No attachment entries')
    names = collections.defaultdict(list)
    exports = set()
    for value in values:
        human, exported = value.get('suggestedHumanReadableName'), value.get('exportedFileName')
        require(isinstance(human, str) and isinstance(exported, str)
                and re.fullmatch(r'[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}(?:\.[A-Za-z0-9]{1,10})?', exported, re.I)
                and exported not in exports, 'Invalid/duplicate attachment export')
        path = directory / exported
        require(path.is_file() and path.stat().st_size > 0, 'Missing/empty exported attachment')
        if path.suffix.lower() == '.png':
            require(path.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n', 'Invalid PNG signature')
        names[human].append(exported)
        exports.add(exported)
    def matches(prefix):
        return [e for name, files in names.items() if name == prefix or name.startswith(prefix + '_') for e in files]
    retained = {}
    for viewport in VIEWPORTS:
        prefix = f'Coverage {case_id} viewport {viewport}'
        files = matches(prefix)
        require(len(files) == 1 and files[0].lower().endswith('.png'), 'Missing/ambiguous coverage PNG: ' + prefix)
        retained[prefix] = files
    for (viewport, audit), findings in grouped.items():
        if not findings:
            continue
        prefix = f'D1 {arm} repetition {repetition} {viewport} {audit} callback-time evidence'
        files = matches(prefix)
        require(len(files) == len(findings) and all(f.lower().endswith('.png') for f in files),
                'Callback PNG count differs from native findings: ' + prefix)
        retained[prefix] = files
    return retained


def load_runner():
    spec = importlib.util.spec_from_file_location('ace_local', ROOT / 'tools/ace_ios_local.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def diagnostic_test_paths(target, template):
    """Resolve XCTest's TestBundlePath relative to its test host bundle."""
    host = pathlib.Path(target['TestHostPath'].replace('__TESTROOT__', str(template.parent))).resolve()
    bundle = pathlib.Path(target['TestBundlePath'].replace('__TESTROOT__', str(template.parent))
                          .replace('__TESTHOST__', str(host))).resolve()
    return {'TestHostPath': host, 'TestBundlePath': bundle}


def verify_build(m, preflight, build, arm):
    original = preflight['build']
    for record in (original, build):
        for name, hash_name, directory in (
            ('template', 'identity', False), ('products', 'productSha256', True),
            ('buildResultBundle', 'buildResultBundleSha256', True), ('buildLog', 'buildLogSha256', False)):
            path = pathlib.Path(record[name])
            require(path.is_dir() if directory else path.is_file(), 'Missing retained build artifact: ' + name)
            require((m.directory_hash(path) if directory else m.sha256(path)) == record[hash_name], 'Build artifact changed: ' + name)
        require(record.get('buildExit') == 0, 'Build was not successful')
    require(build.get('patchSha256') == PATCH_HASH and build.get('diagnosticArm') == arm and build.get('diagnosticOnly') is True,
            'Build does not bind approved diagnostic patch/arm')
    require(m.sha256(STAGE / 'variant/ACEClientAppUITests.r5-d1.correction2.patch') == PATCH_HASH, 'Reviewed patch changed')
    require(build['candidate']['commit'] == preflight['candidate']['commit'] and build['candidate']['patchSha256'] == PATCH_HASH,
            'Variant build candidate differs')
    source = pathlib.Path(build['candidate']['workingTree']) / 'ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift'
    require(m.sha256(source) == build['testSourceSha256'] == build['candidate']['sourceHashes']['ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift'],
            'Diagnostic source changed since build')
    original_template = pathlib.Path(original['template'])
    original_target = plistlib.loads(original_template.read_bytes())['ACEClientAppUITests']
    app = pathlib.Path(original_target['UITargetAppPath'].replace('__TESTROOT__', str(original_template.parent)))
    target = plistlib.loads(pathlib.Path(build['template']).read_bytes())['ACEClientAppUITests']
    require(target['UITargetAppPath'] == str(app) == build['applicationBundle'], 'Diagnostic application is not original bundle')
    require(m.directory_hash(app) == build['applicationBundleSha256'], 'Application bundle changed')
    products = pathlib.Path(build['products']).resolve()
    for key, path in diagnostic_test_paths(target, pathlib.Path(build['template'])).items():
        require(path.exists() and path.is_relative_to(products), 'Diagnostic test bundle/host outside retained products')
    require(str(app) in target['DependentProductPaths'], 'Original app missing from dependent products')
    require(not any(k.startswith('ACE_D1_') for k in original_target.get('EnvironmentVariables', {})), 'Original settings template has D1 request')
    return original_template


def main():
    os.umask(0o077)
    require(len(sys.argv) == 3, 'Usage: run-d1-bc-case.py B|C 1..5')
    arm, repetition = sys.argv[1], int(sys.argv[2])
    require(arm in ('B', 'C') and 1 <= repetition <= 5, 'Invalid arm/repetition')
    require(now() < START_CUTOFF, 'Insufficient time before fixed D1 deadline')
    require(not subprocess.run(['pgrep', '-x', 'xcodebuild'], capture_output=True, text=True).stdout.strip(), 'xcodebuild already active')
    m = load_runner()
    preflight = read_json(STAGE / 'preflight.json')
    candidate = m.candidate()
    require(candidate == preflight['candidate'], 'Candidate changed')
    previous_records = [read_json(p) for p in STAGE.glob('arm-*/repetition-*/execution.json')]
    require(len(list(STAGE.glob('arm-*/repetition-*/batches/*/native-command.json'))) < 15, 'D1 native execution limit reached')
    require(all(r.get('orchestrationExit') == 0 and r.get('candidateUnchanged') is True and not r.get('restorationFailures')
                and not r.get('findings') and r.get('nativeOutcome') != 'FAILED' for r in previous_records),
            'Prior failure, active case, or incomplete restoration requires primary decision')
    require(all(any(r.get('arm') == 'A' and r.get('repetition') == n for r in previous_records) for n in range(1, 6)),
            'All five Arm A records are required')
    required_previous = [('B', n) for n in range(1, 6)] if arm == 'C' else []
    required_previous += [(arm, n) for n in range(1, repetition)]
    require(all(any(r.get('arm') == a and r.get('repetition') == n for r in previous_records) for a, n in required_previous),
            'Previous approved repetitions are missing')
    build = read_json(STAGE / f'arm-{arm}-build.json')
    settings_template = verify_build(m, preflight, build, arm)
    template = pathlib.Path(build['template'])
    evidence = STAGE / f'arm-{arm}' / f'repetition-{repetition}'
    evidence.mkdir(parents=True, exist_ok=False)
    identifier = preflight['environment']['devices']['iPhone 17']['udid']
    settings = m.Settings('light', 'large', 'portrait')
    case = m.make_case('pilot', 'iPhone 17', 'copyConfirmation', settings, True)
    record = {'arm': arm, 'repetition': repetition, 'case': case.payload(), 'candidate': candidate['commit'],
              'sourceHashes': candidate['sourceHashes'], 'startedUTC': now().isoformat(), 'status': 'running',
              'pilotCredit': 0, 'acceptanceCredit': 0, 'buildTemplate': str(template),
              'settingsTemplate': str(settings_template), 'scriptSha256': m.sha256(pathlib.Path(__file__)),
              'patchSha256': PATCH_HASH, 'findings': [], 'settingsHelperExecutions': 0}
    def save():
        (evidence / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
    def boot_states():
        data = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', '--json'], text=True))
        return {d['udid']: d['state'] for group in data['devices'].values() for d in group}
    initial_states = boot_states()
    record['initialBootStates'] = initial_states
    save()
    original_command, original_configure = m.command, m.configure_xctestrun
    def configure(source, output, environment, target_name='ACEClientAppUITests'):
        environment = request_environment(environment, arm, repetition)
        if 'ACE_COVERAGE_CASES_JSON' in environment:
            require(pathlib.Path(source) == template, 'Unexpected coverage template')
        else:
            require(pathlib.Path(source) == settings_template, 'Settings must use original test bundle')
        original_configure(source, output, environment, target_name)
        actual = plistlib.loads(output.read_bytes())[target_name]['EnvironmentVariables']
        if 'ACE_COVERAGE_CASES_JSON' in environment:
            require(actual.get('ACE_D1_ARM') == arm and actual.get('ACE_D1_REPETITION') == str(repetition), 'D1 injection missing')
        else:
            require(not any(k.startswith('ACE_D1_') for k in actual), 'D1 request leaked into settings helper')
    def observed_command(args, **kwargs):
        is_case = '-only-testing:' + m.COVERAGE_SELECTOR in args
        is_settings = '-only-testing:' + m.SETTINGS_SELECTOR in args
        if is_case:
            require(now() < START_CUTOFF, 'Native case launch exceeds D1 cutoff')
            require(len(list(STAGE.glob('arm-*/repetition-*/batches/*/native-command.json'))) < 15, 'D1 native execution limit reached')
            kwargs['timeout'] = 360
        if is_settings:
            record['settingsHelperExecutions'] += 1
            save()
        result = original_command(args, **kwargs)
        with (evidence / 'command-index.jsonl').open('a') as stream:
            stream.write(json.dumps({k: v for k, v in result.items() if k not in ('stdout', 'stderr')}) + '\n')
        return result
    m.configure_xctestrun, m.command = configure, observed_command
    previous = previous_flags = None
    restoration_failures = []
    exit_code = 2
    try:
        m.boot_required_simulator(identifier, initial_states[identifier])
        previous = m.current_simctl_settings(identifier)
        previous_flags = m.native_flags(identifier, settings_template, evidence, 'initial-read', {'mode': 'read'})
        record.update(originalSimctlSettings=previous, originalNativeSettings=previous_flags)
        save()
        desired = {'boldText': False, 'reduceMotion': False, 'increaseContrast': False, 'orientation': 'portrait'}
        if previous_flags != desired:
            m.native_flags(identifier, settings_template, evidence, 'requested-set', {'mode': 'set', **desired})
        native_error = None
        try:
            record['batch'] = m.run_batch('iPhone 17', identifier, settings, (case,), build, evidence, 1)
        except m.RunnerError as error:
            native_error = str(error)
            record['nativeError'] = native_error
        batch = evidence / 'batches/001'
        process, summary = read_json(batch / 'native-command.json'), read_json(batch / 'native-summary.json')
        record.update(nativeExit=process.get('exit'), nativeSummary=summary,
                      nativeOutcome='FAILED' if summary.get('result') == 'Failed' else 'UNVALIDATED',
                      resultBundle=str(batch / 'result.xcresult'))
        save()
        markers = lambda name: m.marker_records(batch / 'native.log', name + ' ')
        calls, issues = markers('ACE_D1_AUDIT_CALL'), markers('ACE_D1_A11Y_ISSUE')
        record.update(findings=issues, auditCalls=calls, diagnosticCompletions=markers('ACE_D1_DIAGNOSTIC_COMPLETE'),
                      auditErrors=markers('ACE_D1_AUDIT_ERROR'), placements=markers('ACE_D1_C_PLACEMENT'))
        save()
        grouped = validate_diagnostic(arm, repetition, calls, issues, record['diagnosticCompletions'], record['auditErrors'], record['placements'])
        case_records = markers('ACE_CASE_RESULT')
        outcome = validate_native(process, summary, issues, calls, case_records)
        record.update(nativeOutcome=outcome, nativeExit=process['exit'], nativeSummary=summary)
        expected_error = 'native batch 1 failed after evidence collection: native result summary is not a complete pass; native process failed'
        require(native_error == (expected_error if issues else None), 'Runner reported unexpected or incomplete evidence failure')
        if not issues:
            m.verify_case_markers((case,), case_records)
        record['imageFiles'] = validate_attachments(batch / 'attachments', case.id, arm, repetition, grouped)
        require((batch / 'result.xcresult').is_dir(), 'Result bundle missing')
        record.update(resultBundle=str(batch / 'result.xcresult'), resultBundleSha256=m.directory_hash(batch / 'result.xcresult'),
                      attachmentSha256=m.directory_hash(batch / 'attachments'), logSha256=m.sha256(batch / 'native.log'),
                      summarySha256=m.sha256(batch / 'native-summary.json'), runfileSha256=m.sha256(batch / 'ACEClientAppUITests.xctestrun'),
                      collectionComplete=True, status='native-audit-findings; image inspection pending' if issues else 'native-pass; image inspection pending',
                      stopRequired=bool(issues))
        exit_code = 0  # Collection only. nativeOutcome/nativeExit preserve every native failure.
    except Exception as error:
        record.update(status='blocked', error=str(error), stopRequired=True, collectionComplete=False)
    finally:
        try:
            if m.simulator_state(identifier) == 'Booted':
                restoration_failures.extend(m.restore_device_configuration(identifier, previous, previous_flags, settings_template, evidence, 'iPhone 17', 'D1'))
            m.restore_boot_state(identifier, initial_states[identifier])
        except Exception as error:
            restoration_failures.append(str(error))
        try:
            record['finalBootStates'] = boot_states()
            record['candidateUnchanged'] = m.candidate() == candidate
            verify_build(m, preflight, build, arm)
        except Exception as error:
            restoration_failures.append('Final identity/readback: ' + str(error))
        record['restorationFailures'] = restoration_failures
        if restoration_failures or record.get('finalBootStates') != initial_states or not record.get('candidateUnchanged'):
            exit_code = 2
            record.update(status='blocked integrity or restoration', stopRequired=True, collectionComplete=False)
        if now() >= DEADLINE:
            exit_code = 2
            record.update(status='blocked D1 hard deadline', stopRequired=True)
        record.update(finishedUTC=now().isoformat(), orchestrationExit=exit_code)
        save()
        print(json.dumps({k: record.get(k) for k in ('arm', 'repetition', 'status', 'nativeOutcome', 'nativeExit', 'error', 'restorationFailures', 'candidateUnchanged', 'stopRequired', 'orchestrationExit')}), flush=True)
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
