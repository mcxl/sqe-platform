#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
date -u +%FT%TZ > "$run_dir/contracts-after.started"
caffeinate -i xcodebuild test-without-building -xctestrun "$run_dir/derived-functional/Build/Products/ACEClientApp_iphonesimulator26.4-x86_64.xctestrun" -destination 'platform=iOS Simulator,arch=x86_64,id=D1BAA05C-52DD-4E57-832F-C0A75718E085' -resultBundlePath "$run_dir/contracts-after.xcresult" -only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests/testCopyControlsUITest -only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests/testProjectConfiguration -only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests/testSourceBoundaryInspection -only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests/testComposedCredentialStoreSessionLifecycle -parallel-testing-enabled NO -test-timeouts-enabled YES -default-test-execution-time-allowance 300 -maximum-test-execution-time-allowance 300 > "$run_dir/contracts-after.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/contracts-after.exit"
date -u +%FT%TZ > "$run_dir/contracts-after.finished"
if [ -d "$run_dir/contracts-after.xcresult" ]; then
 xcrun xcresulttool get test-results summary --path "$run_dir/contracts-after.xcresult" --compact > "$run_dir/contracts-after-summary.json"
 xcrun xcresulttool get test-results tests --path "$run_dir/contracts-after.xcresult" --compact > "$run_dir/contracts-after-tests.json"
fi
tail -n 20 "$run_dir/contracts-after.log"
exit "$result"
