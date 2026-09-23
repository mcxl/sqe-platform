#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-layout-20260914
mkdir -p "$run_dir"
cd LOCAL_HOME/Developer/sqe-platform-release-layout || exit 1
git rev-parse HEAD > "$run_dir/ui-build-restored-v2.commit"
git diff --binary > "$run_dir/ui-build-restored-v2-source.patch"
shasum -a 256 ios/ACEClientApp/ACEClientApp/*.swift ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift > "$run_dir/ui-build-restored-v2-source.sha256"
date -u +%FT%TZ > "$run_dir/ui-build-restored-v2.started"
caffeinate -i xcodebuild build-for-testing \
  -project ios/ACEClientApp/ACEClientApp.xcodeproj \
  -scheme ACEClientAppUITests -configuration Debug -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath "$run_dir/derived" \
  -resultBundlePath "$run_dir/ui-build-restored-v2.xcresult" \
  -only-testing:ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls \
  -only-testing:ACEClientAppUITests/ACEClientAppUITests/testClippingNoConclusionStandaloneAudit \
  -only-testing:ACEClientAppUITests/ACEClientAppUITests/testClippingNoActionsStandaloneAudit \
  ACE_PREVIEW_ORIGIN=https://preview.example.invalid \
  ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp \
  ARCHS=x86_64 ONLY_ACTIVE_ARCH=YES \
  CODE_SIGN_IDENTITY= CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO \
  > "$run_dir/ui-build-restored-v2.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/ui-build-restored-v2.exit"
date -u +%FT%TZ > "$run_dir/ui-build-restored-v2.finished"
tail -n 30 "$run_dir/ui-build-restored-v2.log"
exit "$result"
