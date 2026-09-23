#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
cd LOCAL_HOME/Developer/sqe-platform-release-layout || exit 1
date -u +%FT%TZ > "$run_dir/signin-prompt-build.started"
caffeinate -i xcodebuild build-for-testing -project ios/ACEClientApp/ACEClientApp.xcodeproj -scheme ACEClientAppUITests -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath "$run_dir/derived-diagnostic" -resultBundlePath "$run_dir/signin-prompt-build.xcresult" ACE_PREVIEW_ORIGIN=https://preview.example.invalid ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp ARCHS=x86_64 ONLY_ACTIVE_ARCH=YES CODE_SIGN_IDENTITY= CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO > "$run_dir/signin-prompt-build.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/signin-prompt-build.exit"
date -u +%FT%TZ > "$run_dir/signin-prompt-build.finished"
tail -n 12 "$run_dir/signin-prompt-build.log"
exit "$result"
