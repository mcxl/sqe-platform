#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
simulator=D1BAA05C-52DD-4E57-832F-C0A75718E085
date -u +%FT%TZ > "$run_dir/settings-bold-restored.started"
caffeinate -i xcodebuild test-without-building -xctestrun "$run_dir/derived-diagnostic/Build/Products/settings-bold-restored.xctestrun" -destination "platform=iOS Simulator,arch=x86_64,id=$simulator" -resultBundlePath "$run_dir/settings-bold-restored.xcresult" -only-testing:ACEClientAppUITests/ACEClientAppUITests/testConfigureAccessibilitySettings -parallel-testing-enabled NO -test-timeouts-enabled YES -default-test-execution-time-allowance 300 -maximum-test-execution-time-allowance 300 > "$run_dir/settings-bold-restored.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/settings-bold-restored.exit"
date -u +%FT%TZ > "$run_dir/settings-bold-restored.finished"
if [ -d "$run_dir/settings-bold-restored.xcresult" ]; then
 xcrun xcresulttool get test-results summary --path "$run_dir/settings-bold-restored.xcresult" --compact > "$run_dir/settings-bold-restored-summary.json"
 xcrun xcresulttool export attachments --path "$run_dir/settings-bold-restored.xcresult" --output-path "$run_dir/settings-bold-restored-attachments" > "$run_dir/settings-bold-restored-attachments.log" 2>&1
fi
tail -n 15 "$run_dir/settings-bold-restored.log"
exit "$result"
