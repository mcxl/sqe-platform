#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
simulator=2EB0863C-470E-467D-A0C6-CD216DA70C67
xcrun simctl bootstatus "$simulator" -b || exit $?
xcrun simctl ui "$simulator" appearance > "$run_dir/contrast-original-appearance.txt"
xcrun simctl ui "$simulator" content_size > "$run_dir/contrast-original-size.txt"
xcrun simctl ui "$simulator" increase_contrast > "$run_dir/contrast-original-contrast.txt"
xcrun simctl ui "$simulator" appearance light || exit $?
xcrun simctl ui "$simulator" content_size large || exit $?
date -u +%FT%TZ > "$run_dir/no-conclusion-contrast-diagnostic.started"
caffeinate -i xcodebuild test-without-building -xctestrun "$run_dir/derived-diagnostic/Build/Products/no-conclusion-contrast-diagnostic.xctestrun" -destination "platform=iOS Simulator,arch=x86_64,id=$simulator" -resultBundlePath "$run_dir/no-conclusion-contrast-diagnostic.xcresult" -only-testing:ACEClientAppUITests/ACEClientAppUITests/testClippingNoConclusionStandaloneAudit -parallel-testing-enabled NO -test-timeouts-enabled YES -default-test-execution-time-allowance 300 -maximum-test-execution-time-allowance 300 > "$run_dir/no-conclusion-contrast-diagnostic.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/no-conclusion-contrast-diagnostic.exit"
date -u +%FT%TZ > "$run_dir/no-conclusion-contrast-diagnostic.finished"
if [ -d "$run_dir/no-conclusion-contrast-diagnostic.xcresult" ]; then
 xcrun xcresulttool get test-results summary --path "$run_dir/no-conclusion-contrast-diagnostic.xcresult" --compact > "$run_dir/no-conclusion-contrast-diagnostic-summary.json"
 xcrun xcresulttool get test-results tests --path "$run_dir/no-conclusion-contrast-diagnostic.xcresult" --compact > "$run_dir/no-conclusion-contrast-diagnostic-tests.json"
 xcrun xcresulttool export attachments --path "$run_dir/no-conclusion-contrast-diagnostic.xcresult" --output-path "$run_dir/no-conclusion-contrast-diagnostic-attachments" > "$run_dir/no-conclusion-contrast-diagnostic-attachments.log" 2>&1
fi
xcrun simctl ui "$simulator" appearance "$(cat "$run_dir/contrast-original-appearance.txt")"
xcrun simctl ui "$simulator" content_size "$(cat "$run_dir/contrast-original-size.txt")"
tail -n 20 "$run_dir/no-conclusion-contrast-diagnostic.log"
exit "$result"
