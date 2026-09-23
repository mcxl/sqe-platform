#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
simulator=D1BAA05C-52DD-4E57-832F-C0A75718E085
date -u +%FT%TZ > "$run_dir/settings-bold-corrected.started"
caffeinate -i xcodebuild test-without-building -xctestrun "$run_dir/derived-diagnostic/Build/Products/settings-bold-corrected.xctestrun" -destination "platform=iOS Simulator,arch=x86_64,id=$simulator" -resultBundlePath "$run_dir/settings-bold-corrected.xcresult" -only-testing:ACEClientAppUITests/ACEClientAppUITests/testConfigureAccessibilitySettings -parallel-testing-enabled NO -test-timeouts-enabled YES -default-test-execution-time-allowance 300 -maximum-test-execution-time-allowance 300 > "$run_dir/settings-bold-corrected.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/settings-bold-corrected.exit"
date -u +%FT%TZ > "$run_dir/settings-bold-corrected.finished"
if [ -d "$run_dir/settings-bold-corrected.xcresult" ]; then
 xcrun xcresulttool get test-results summary --path "$run_dir/settings-bold-corrected.xcresult" --compact > "$run_dir/settings-bold-corrected-summary.json"
 xcrun xcresulttool export attachments --path "$run_dir/settings-bold-corrected.xcresult" --output-path "$run_dir/settings-bold-corrected-attachments" > "$run_dir/settings-bold-corrected-attachments.log" 2>&1
fi
tail -n 15 "$run_dir/settings-bold-corrected.log"
exit "$result"
