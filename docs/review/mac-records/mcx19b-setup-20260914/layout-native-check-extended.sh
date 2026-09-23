#!/bin/bash
set -eu
umask 077
tag=$1
appearance=$2
content_size=$3
selector=$4
case "$tag" in *[!a-z0-9-]*|'') exit 2;; esac
case "$appearance" in light|dark) ;; *) exit 2;; esac
case "$selector" in testFictionalReleaseHasApprovedCopyControls|testClippingNoConclusionStandaloneAudit|testClippingNoActionsStandaloneAudit|testNormalDeviceSettings|testReleaseOrientationHooks) ;; *) exit 2;; esac
run_dir=LOCAL_HOME/ace-private/mcx19b-layout-20260914
products="$run_dir/derived/Build/Products"
simulator=2EB0863C-470E-467D-A0C6-CD216DA70C67
xcrun simctl ui "$simulator" appearance "$appearance"
xcrun simctl ui "$simulator" content_size "$content_size"
xcrun simctl ui "$simulator" appearance > "$run_dir/$tag-appearance.txt"
xcrun simctl ui "$simulator" content_size > "$run_dir/$tag-content-size.txt"
xcrun simctl ui "$simulator" increase_contrast > "$run_dir/$tag-increase-contrast.txt"
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 - "$products" "$tag" "$appearance" "$content_size" "$selector" <<'PY'
import hashlib, plistlib, sys
from pathlib import Path
products, tag, appearance = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
source = products/'ACEClientAppUITests_iphonesimulator26.4-x86_64.xctestrun'
data = plistlib.loads(source.read_bytes())
targets = [value for key, value in data.items() if key.endswith('UITests') and isinstance(value, dict)]
if len(targets) != 1:
    raise RuntimeError(f'Expected one generated UI test target; found {len(targets)}. Inspect native run file.')
env = targets[0].setdefault('EnvironmentVariables', {})
if sys.argv[5] == 'testNormalDeviceSettings':
    env.pop('ACE_UI_TEST_APPEARANCE', None)
    env['ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE'] = appearance
    env['ACE_EXPECTED_CONTENT_SIZE_CATEGORY'] = sys.argv[4]
else:
    env['ACE_UI_TEST_APPEARANCE'] = appearance
env['ACE_UI_TEST_RETAIN_INITIAL_AUDIT_SCREENSHOT'] = '1'
output = products/f'{tag}.xctestrun'
output.write_bytes(plistlib.dumps(data))
record = products.parents[2]/f'{tag}-runfile.sha256'
record.write_text(f'{hashlib.sha256(source.read_bytes()).hexdigest()}  {source}\n{hashlib.sha256(output.read_bytes()).hexdigest()}  {output}\n')
PY
date -u +%FT%TZ > "$run_dir/$tag.started"
set +e
caffeinate -i xcodebuild test-without-building \
  -xctestrun "$products/$tag.xctestrun" \
  -destination "platform=iOS Simulator,arch=x86_64,id=$simulator" \
  -resultBundlePath "$run_dir/$tag.xcresult" \
  -only-testing:"ACEClientAppUITests/ACEClientAppUITests/$selector" \
  -parallel-testing-enabled NO -test-timeouts-enabled YES \
  -default-test-execution-time-allowance 300 \
  -maximum-test-execution-time-allowance 300 \
  > "$run_dir/$tag.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/$tag.exit"
date -u +%FT%TZ > "$run_dir/$tag.finished"
if [ -d "$run_dir/$tag.xcresult" ]; then
  xcrun xcresulttool get test-results summary --path "$run_dir/$tag.xcresult" --compact > "$run_dir/$tag-summary.json"
  xcrun xcresulttool get test-results tests --path "$run_dir/$tag.xcresult" --compact > "$run_dir/$tag-tests.json"
  xcrun xcresulttool export attachments --path "$run_dir/$tag.xcresult" --output-path "$run_dir/$tag-attachments" > "$run_dir/$tag-attachments.log" 2>&1
fi
tail -n 35 "$run_dir/$tag.log"
exit "$result"
