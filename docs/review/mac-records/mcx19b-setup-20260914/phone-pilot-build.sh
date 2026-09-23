#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-local-20260914
cd LOCAL_HOME/Developer/sqe-platform || exit 1
git diff --exit-code || exit 1
git rev-parse HEAD > "$run_dir/phone-pilot-build.commit"
date -u +%FT%TZ > "$run_dir/phone-pilot-build.started"
caffeinate -i xcodebuild build \
  -project ios/ACEClientApp/ACEClientApp.xcodeproj \
  -scheme ACEClientApp -configuration Debug -sdk iphoneos \
  -destination 'platform=iOS,id=00008130-00142D3C3A13803A' \
  -derivedDataPath "$run_dir/derived-phone" \
  -resultBundlePath "$run_dir/phone-pilot-build.xcresult" \
  -allowProvisioningUpdates -allowProvisioningDeviceRegistration \
  DEVELOPMENT_TEAM=85SMJXHMJ5 CODE_SIGN_STYLE=Automatic \
  'CODE_SIGN_IDENTITY=Apple Development' \
  ACE_PREVIEW_ORIGIN=https://preview.example.invalid \
  ACE_BUNDLE_IDENTIFIER=com.alanrichardson.aceclientapp \
  ACE_EXPECTED_ACCESS_GROUP=85SMJXHMJ5.com.alanrichardson.aceclientapp \
  ARCHS=arm64 ONLY_ACTIVE_ARCH=YES \
  > "$run_dir/phone-pilot-build.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/phone-pilot-build.exit"
date -u +%FT%TZ > "$run_dir/phone-pilot-build.finished"
tail -n 45 "$run_dir/phone-pilot-build.log"
exit "$result"
