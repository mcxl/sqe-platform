#!/bin/bash
set -u
umask 077
repo=LOCAL_HOME/Developer/sqe-platform
evidence=LOCAL_HOME/ace-private/mcx19b-local-20260914
cd "$repo" || exit 1
git diff --binary > "$evidence/pilot-build-generic-source.patch"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/pilot-build-generic.started"
caffeinate -i xcodebuild build-for-testing \
  -project ios/ACEClientApp/ACEClientApp.xcodeproj \
  -scheme ACEClientApp -configuration Debug -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath "$evidence/derived-debug" \
  -resultBundlePath "$evidence/pilot-build-generic.xcresult" \
  -only-testing:ACEClientAppTests/ACEClientAppTests/testRequestIsGETAndHasNoCache \
  ACE_PREVIEW_ORIGIN=https://preview.example.invalid ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp \
  ARCHS=x86_64 ONLY_ACTIVE_ARCH=YES CODE_SIGN_IDENTITY= CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO \
  > "$evidence/pilot-build-generic.log" 2>&1
result=$?
printf '%s\n' "$result" > "$evidence/pilot-build-generic.exit"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/pilot-build-generic.finished"
tail -n 25 "$evidence/pilot-build-generic.log"
exit "$result"
