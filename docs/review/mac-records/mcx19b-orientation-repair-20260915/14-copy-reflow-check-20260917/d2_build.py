from pathlib import Path
import hashlib, json, os, signal, subprocess, time

ROOT = Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/14-copy-reflow-check-20260917')
WORK = Path('LOCAL_HOME/Developer/sqe-platform-d2-reflow-20260917')
source = json.loads((ROOT / 'candidate-source.json').read_text())
assert not (ROOT / 'build-command.json').exists(), 'D2 compilation was already started'
for rel, digest in source['appSources'].items():
    assert hashlib.sha256((WORK / rel).read_bytes()).hexdigest() == digest, rel
test = WORK / 'ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift'
assert hashlib.sha256(test.read_bytes()).hexdigest() == source['testSourceSha256']
cmd = ['xcodebuild', 'build-for-testing', '-project', str(WORK / 'ios/ACEClientApp/ACEClientApp.xcodeproj'),
       '-scheme', 'ACEClientAppUITests', '-configuration', 'Debug', '-sdk', 'iphonesimulator',
       '-destination', 'generic/platform=iOS Simulator', '-parallel-testing-enabled', 'NO',
       '-derivedDataPath', str(ROOT / 'build'), '-resultBundlePath', str(ROOT / 'build.xcresult'),
       'ACE_PREVIEW_ORIGIN=https://preview.example.invalid', 'ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp',
       'ARCHS=x86_64', 'ONLY_ACTIVE_ARCH=YES', 'CODE_SIGN_IDENTITY=', 'CODE_SIGNING_REQUIRED=NO', 'CODE_SIGNING_ALLOWED=NO']
(ROOT / 'build-command.json').write_text(json.dumps(cmd, indent=2))
start = time.monotonic()
with (ROOT / 'build.log').open('w') as log:
    process = subprocess.Popen(cmd, cwd=WORK, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        code = process.wait(timeout=900)
        timed_out = False
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        code = process.returncode
        timed_out = True
record = {'exit': code, 'timedOut': timed_out, 'elapsedSeconds': time.monotonic() - start,
          'candidate': source['candidate'], 'patchSha256': source['patchSha256'], 'source': source}
(ROOT / 'build-record.json').write_text(json.dumps(record, indent=2))
if code != 0:
    raise SystemExit(code if code > 0 else 1)
templates = list((ROOT / 'build').rglob('*.xctestrun'))
assert len(templates) == 1, 'Expected exactly one new D2 xctestrun'
record['template'] = str(templates[0])
record['templateSha256'] = hashlib.sha256(templates[0].read_bytes()).hexdigest()

def bundle_manifest(directory):
    assert directory.is_dir(), str(directory)
    files = {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(directory.rglob('*')) if p.is_file()}
    assert files
    encoded = json.dumps(files, sort_keys=True, separators=(',', ':')).encode()
    return {'path': str(directory), 'sha256': hashlib.sha256(encoded).hexdigest(),
            'hashMethod': 'SHA256 of compact sorted JSON mapping relative paths to file SHA256', 'files': files}

products = ROOT / 'build/Build/Products/Debug-iphonesimulator'
record['appBundle'] = bundle_manifest(products / 'ACEClientApp.app')
record['testBundle'] = bundle_manifest(products / 'ACEClientAppUITests-Runner.app/PlugIns/ACEClientAppUITests.xctest')
for rel, digest in source['appSources'].items():
    assert hashlib.sha256((WORK / rel).read_bytes()).hexdigest() == digest, rel
record['appSourcesVerifiedAfterBuild'] = True
(ROOT / 'build-record.json').write_text(json.dumps(record, indent=2))
print(json.dumps({k: record[k] for k in ['exit', 'elapsedSeconds', 'template', 'templateSha256', 'appSourcesVerifiedAfterBuild']}), flush=True)
