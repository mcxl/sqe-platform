#!/bin/bash
set -u
umask 077
repo=LOCAL_HOME/Developer/sqe-platform
evidence=LOCAL_HOME/ace-private/mcx19b-local-20260914
cd "$repo" || exit 1
git diff --binary > "$evidence/pilot-fail-booted-source.patch"
shasum -a 256 ios/ACEClientApp/ACEClientAppTests/ACEClientAppTests.swift > "$evidence/pilot-fail-booted-source.sha256"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/pilot-fail-booted.started"
caffeinate -i xcodebuild test \
  -project ios/ACEClientApp/ACEClientApp.xcodeproj \
  -scheme ACEClientApp -configuration Debug -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,id=2EB0863C-470E-467D-A0C6-CD216DA70C67' \
  -derivedDataPath "$evidence/derived-debug" \
  -resultBundlePath "$evidence/pilot-fail-booted.xcresult" \
  -only-testing:ACEClientAppTests/ACEClientAppTests/testRequestIsGETAndHasNoCache \
  -parallel-testing-enabled NO -test-timeouts-enabled YES \
  -default-test-execution-time-allowance 60 -maximum-test-execution-time-allowance 60 \
  ACE_PREVIEW_ORIGIN=https://preview.example.invalid ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp \
  ARCHS=x86_64 ONLY_ACTIVE_ARCH=YES CODE_SIGN_IDENTITY= CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO \
  > "$evidence/pilot-fail-booted.log" 2>&1
result=$?
printf '%s\n' "$result" > "$evidence/pilot-fail-booted.exit"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/pilot-fail-booted.finished"
tail -n 25 "$evidence/pilot-fail-booted.log"
exit "$result"
