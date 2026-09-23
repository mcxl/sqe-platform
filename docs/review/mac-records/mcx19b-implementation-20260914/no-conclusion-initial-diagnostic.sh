#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
simulator=2EB0863C-470E-467D-A0C6-CD216DA70C67
xcrun simctl shutdown D1BAA05C-52DD-4E57-832F-C0A75718E085 || exit $?
xcrun simctl boot "$simulator" || exit $?
xcrun simctl bootstatus "$simulator" -b || exit $?
xcrun simctl ui "$simulator" appearance > "$run_dir/diagnostic-original-appearance.txt"
xcrun simctl ui "$simulator" content_size > "$run_dir/diagnostic-original-size.txt"
xcrun simctl ui "$simulator" increase_contrast > "$run_dir/diagnostic-original-contrast.txt"
xcrun simctl ui "$simulator" appearance light || exit $?
xcrun simctl ui "$simulator" content_size large || exit $?
date -u +%FT%TZ > "$run_dir/no-conclusion-initial-diagnostic.started"
caffeinate -i xcodebuild test-without-building -xctestrun "$run_dir/derived-diagnostic/Build/Products/no-conclusion-initial-diagnostic.xctestrun" -destination "platform=iOS Simulator,arch=x86_64,id=$simulator" -resultBundlePath "$run_dir/no-conclusion-initial-diagnostic.xcresult" -only-testing:ACEClientAppUITests/ACEClientAppUITests/testClippingNoConclusionStandaloneAudit -parallel-testing-enabled NO -test-timeouts-enabled YES -default-test-execution-time-allowance 300 -maximum-test-execution-time-allowance 300 > "$run_dir/no-conclusion-initial-diagnostic.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/no-conclusion-initial-diagnostic.exit"
date -u +%FT%TZ > "$run_dir/no-conclusion-initial-diagnostic.finished"
if [ -d "$run_dir/no-conclusion-initial-diagnostic.xcresult" ]; then
 xcrun xcresulttool get test-results summary --path "$run_dir/no-conclusion-initial-diagnostic.xcresult" --compact > "$run_dir/no-conclusion-initial-diagnostic-summary.json"
 xcrun xcresulttool get test-results tests --path "$run_dir/no-conclusion-initial-diagnostic.xcresult" --compact > "$run_dir/no-conclusion-initial-diagnostic-tests.json"
 xcrun xcresulttool export attachments --path "$run_dir/no-conclusion-initial-diagnostic.xcresult" --output-path "$run_dir/no-conclusion-initial-diagnostic-attachments" > "$run_dir/no-conclusion-initial-diagnostic-attachments.log" 2>&1
fi
xcrun simctl ui "$simulator" appearance "$(cat "$run_dir/diagnostic-original-appearance.txt")"
xcrun simctl ui "$simulator" content_size "$(cat "$run_dir/diagnostic-original-size.txt")"
tail -n 20 "$run_dir/no-conclusion-initial-diagnostic.log"
exit "$result"
