#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
simulator=D1BAA05C-52DD-4E57-832F-C0A75718E085
xcrun simctl shutdown 2EB0863C-470E-467D-A0C6-CD216DA70C67 || exit $?
xcrun simctl boot "$simulator" || exit $?
xcrun simctl bootstatus "$simulator" -b || exit $?
date -u +%FT%TZ > "$run_dir/pro-max-visible.started"
caffeinate -i xcodebuild test-without-building -xctestrun "$run_dir/derived-diagnostic/Build/Products/pro-max-visible.xctestrun" -destination "platform=iOS Simulator,arch=x86_64,id=$simulator" -resultBundlePath "$run_dir/pro-max-visible.xcresult" -only-testing:ACEClientAppUITests/ACEClientAppUITests/testBothAppearances -parallel-testing-enabled NO -test-timeouts-enabled YES -default-test-execution-time-allowance 300 -maximum-test-execution-time-allowance 300 > "$run_dir/pro-max-visible.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/pro-max-visible.exit"
date -u +%FT%TZ > "$run_dir/pro-max-visible.finished"
if [ -d "$run_dir/pro-max-visible.xcresult" ]; then
 xcrun xcresulttool get test-results summary --path "$run_dir/pro-max-visible.xcresult" --compact > "$run_dir/pro-max-visible-summary.json"
 xcrun xcresulttool export attachments --path "$run_dir/pro-max-visible.xcresult" --output-path "$run_dir/pro-max-visible-attachments" > "$run_dir/pro-max-visible-attachments.log" 2>&1
fi
tail -n 15 "$run_dir/pro-max-visible.log"
exit "$result"
