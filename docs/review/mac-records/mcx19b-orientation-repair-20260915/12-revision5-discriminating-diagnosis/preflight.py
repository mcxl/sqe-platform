import importlib.util, json, os, pathlib, sys, datetime

os.umask(0o077)
repo = pathlib.Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
stage = pathlib.Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
out = stage / '12-revision5-discriminating-diagnosis'
spec = importlib.util.spec_from_file_location('ace_local', repo / 'tools/ace_ios_local.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
candidate = m.candidate()
assert candidate['commit'] == '52b212aca02190ee0e742debe383fa6016fe36b9'
environment = m.preflight()
build = json.loads((stage / '11-settings-toggle-diagnosis/complete-pilot-build.json').read_text())
m.reuse_build(candidate, {'candidate': candidate, 'build': build})
gate = json.loads((stage / '11-settings-toggle-diagnosis/readiness/evidence-gate-readiness.json').read_text())
assert gate['candidate'] == candidate and gate['status'] == 'passed'
checked = []
for item in gate['evidence']:
    p = pathlib.Path(item['path'])
    assert p.is_file(), str(p)
    actual = m.sha256(p)
    assert actual == item['sha256'], str(p)
    checked.append({'path': str(p), 'sha256': actual})
    if p.name == 'capture-gate-integrity.json':
        print('CAPTURE_GATE ' + p.read_text(), flush=True)
record = {'checkedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'candidate': candidate, 'environment': environment, 'build': build,
          'existingEvidenceGate': checked, 'sourceAndBuildIdentityVerified': True,
          'scope': 'D1; existing build and extraction path reused for unchanged arm A only',
          'diagnosticCaseExecutions': 0}
(out / 'preflight.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'status': 'preflight passed', 'candidate': candidate['commit'],
                  'devices': environment['devices'], 'freeGiB': round(environment['freeBytes']/1024**3,2),
                  'buildReused': build['template'], 'evidenceReferencesChecked': len(checked)}, indent=2), flush=True)
