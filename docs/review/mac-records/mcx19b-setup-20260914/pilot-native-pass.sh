#!/bin/bash
set -u
umask 077
evidence=LOCAL_HOME/ace-private/mcx19b-local-20260914
runfile="$evidence/derived-debug/Build/Products/ACEClientApp_iphonesimulator26.4-x86_64.xctestrun"
shasum -a 256 "$runfile" "$evidence/derived-debug/Build/Products/Debug-iphonesimulator/ACEClientAppTests.xctest/ACEClientAppTests" > "$evidence/pilot-native-pass-products.sha256"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/pilot-native-pass.started"
caffeinate -i xcodebuild test-without-building \
  -xctestrun "$runfile" \
  -destination 'platform=iOS Simulator,arch=x86_64,id=2EB0863C-470E-467D-A0C6-CD216DA70C67' \
  -resultBundlePath "$evidence/pilot-native-pass.xcresult" \
  -only-testing:ACEClientAppTests/ACEClientAppTests/testRequestIsGETAndHasNoCache \
  -parallel-testing-enabled NO -test-timeouts-enabled YES \
  -default-test-execution-time-allowance 60 -maximum-test-execution-time-allowance 60 \
  > "$evidence/pilot-native-pass.log" 2>&1
result=$?
printf '%s\n' "$result" > "$evidence/pilot-native-pass.exit"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/pilot-native-pass.finished"
tail -n 25 "$evidence/pilot-native-pass.log"
exit "$result"
