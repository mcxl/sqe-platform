#!/bin/bash
set -u
umask 077
repo=LOCAL_HOME/Developer/sqe-platform
evidence=LOCAL_HOME/ace-private/mcx19b-local-20260914
mkdir -p "$evidence"
cd "$repo" || exit 1
git rev-parse HEAD > "$evidence/baseline-commit.txt"
git status --porcelain=v1 > "$evidence/baseline-status.txt"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/build-baseline.started"
caffeinate -i xcodebuild build \
  -project ios/ACEClientApp/ACEClientApp.xcodeproj \
  -scheme ACEClientApp -configuration Debug \
  -destination 'platform=iOS Simulator,id=2EB0863C-470E-467D-A0C6-CD216DA70C67' \
  -derivedDataPath "$evidence/derived-debug" \
  -resultBundlePath "$evidence/build-baseline.xcresult" \
  ONLY_ACTIVE_ARCH=YES CODE_SIGN_IDENTITY= CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO \
  > "$evidence/build-baseline.log" 2>&1
result=$?
printf '%s\n' "$result" > "$evidence/build-baseline.exit"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/build-baseline.finished"
tail -n 18 "$evidence/build-baseline.log"
exit "$result"
