#!/bin/bash
set -u
umask 077
repo=LOCAL_HOME/Developer/sqe-platform
evidence=LOCAL_HOME/ace-private/mcx19b-local-20260914
cd "$repo" || exit 1
git diff --binary > "$evidence/pilot-build-for-testing-source.patch"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/pilot-build-for-testing.started"
caffeinate -i xcodebuild build-for-testing \
  -project ios/ACEClientApp/ACEClientApp.xcodeproj \
  -scheme ACEClientApp -configuration Debug -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,arch=x86_64,id=2EB0863C-470E-467D-A0C6-CD216DA70C67' \
  -derivedDataPath "$evidence/derived-debug" \
  -resultBundlePath "$evidence/pilot-build-for-testing.xcresult" \
  -only-testing:ACEClientAppTests/ACEClientAppTests/testRequestIsGETAndHasNoCache \
  ACE_PREVIEW_ORIGIN=https://preview.example.invalid ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp \
  ARCHS=x86_64 ONLY_ACTIVE_ARCH=YES CODE_SIGN_IDENTITY= CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO \
  > "$evidence/pilot-build-for-testing.log" 2>&1
result=$?
printf '%s\n' "$result" > "$evidence/pilot-build-for-testing.exit"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/pilot-build-for-testing.finished"
tail -n 25 "$evidence/pilot-build-for-testing.log"
exit "$result"
