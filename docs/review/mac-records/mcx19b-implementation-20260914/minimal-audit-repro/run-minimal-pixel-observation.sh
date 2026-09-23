#!/bin/bash
# Private native-audit diagnostic runner. Do not use this script for release acceptance.
set -u
umask 077

run_dir="$(cd "$(dirname "$0")" && pwd)"
project_dir="$run_dir/ACEClientApp"
derived_data="$run_dir/derived-minimal-audit-repro"
results_dir="$run_dir/results-minimal-audit-repro"
mode="${MODE:?Set MODE to build, all, or contrast}"

mkdir -p "$results_dir"

build() {
  local result=0
  date -u +%FT%TZ > "$results_dir/minimal-audit-repro-pixel-build.started"
  caffeinate -i xcodebuild build-for-testing \
    -project "$project_dir/ACEClientApp.xcodeproj" \
    -scheme ACEClientAppUITests \
    -configuration Debug \
    -sdk iphonesimulator \
    -destination 'generic/platform=iOS Simulator' \
    -derivedDataPath "$derived_data" \
    -resultBundlePath "$results_dir/minimal-audit-repro-pixel-build.xcresult" \
    ACE_PREVIEW_ORIGIN=https://preview.example.invalid \
    ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp \
    ARCHS=x86_64 \
    ONLY_ACTIVE_ARCH=YES \
    CODE_SIGN_IDENTITY= \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGNING_ALLOWED=NO \
    > "$results_dir/minimal-audit-repro-pixel-build.log" 2>&1
  result=$?
  printf '%s\n' "$result" > "$results_dir/minimal-audit-repro-pixel-build.exit"
  date -u +%FT%TZ > "$results_dir/minimal-audit-repro-pixel-build.finished"
  tail -n 12 "$results_dir/minimal-audit-repro-pixel-build.log"
  return "$result"
}

prepare_xctestrun() {
  local generated flat format
  generated="$(find "$derived_data/Build/Products" -maxdepth 1 -type f -name 'ACEClientAppUITests_*.xctestrun' -print -quit)"
  if [ -z "$generated" ]; then
    echo 'No generated ACEClientAppUITests xctestrun was found.' >&2
    return 1
  fi
  flat="$(dirname "$generated")/minimal-audit-repro.xctestrun"
  cp "$generated" "$flat"
  format="$(/usr/libexec/PlistBuddy -c 'Print :__xctestrun_metadata__:FormatVersion' "$flat")"
  if [ "$format" != 1 ]; then
    echo "Expected observed format 1; found $format" >&2
    return 1
  fi
  /usr/libexec/PlistBuddy -c 'Print :ACEClientAppUITests:TestBundlePath' "$flat" >/dev/null || return 1
  /usr/libexec/PlistBuddy -c 'Delete :ACEClientAppUITests:EnvironmentVariables:ACE_UI_TEST_APPEARANCE' "$flat" >/dev/null 2>&1 || true
  /usr/libexec/PlistBuddy -c 'Add :ACEClientAppUITests:EnvironmentVariables:ACE_UI_TEST_APPEARANCE string light' "$flat"
  format="$(/usr/libexec/PlistBuddy -c 'Print :__xctestrun_metadata__:FormatVersion' "$flat")"
  if [ "$format" != 1 ]; then
    echo "Expected format-1 xctestrun, found $format." >&2
    return 1
  fi
  plutil -lint "$flat"
  printf '%s\n' "$flat" > "$results_dir/minimal-audit-repro.xctestrun-path"
}

retain_test_evidence() {
  local name="$1" bundle="$results_dir/$1.xcresult"
  if [ -d "$bundle" ]; then
    xcrun xcresulttool get test-results summary --path "$bundle" --compact > "$results_dir/$name-summary.json" 2> "$results_dir/$name-summary.stderr" || true
    mkdir -p "$results_dir/$name-attachments"
    xcrun xcresulttool export attachments --path "$bundle" --output-path "$results_dir/$name-attachments" > "$results_dir/$name-attachments.log" 2>&1 || true
  fi
}

run_selected_test() {
  local name="$1" selector="$2" flat="$derived_data/Build/Products/minimal-audit-repro.xctestrun" result=0
  local destination="${DESTINATION:?Set DESTINATION to a booted simulator UDID before a test mode}"
  if [ ! -f "$flat" ]; then
    echo "Missing prepared xctestrun: $flat. Run MODE=build first." >&2
    return 1
  fi
  date -u +%FT%TZ > "$results_dir/$name.started"
  caffeinate -i xcodebuild test-without-building \
    -xctestrun "$flat" \
    -destination "$destination" \
    -parallel-testing-enabled NO \
    -test-timeouts-enabled YES \
    -default-test-execution-time-allowance 300 \
    -maximum-test-execution-time-allowance 300 \
    -resultBundlePath "$results_dir/$name.xcresult" \
    "-only-testing:ACEClientAppUITests/ACEClientAppUITests/$selector" \
    > "$results_dir/$name.log" 2>&1
  result=$?
  printf '%s\n' "$result" > "$results_dir/$name.exit"
  date -u +%FT%TZ > "$results_dir/$name.finished"
  retain_test_evidence "$name"
  tail -n 12 "$results_dir/$name.log"
  return "$result"
}

case "$mode" in
  build)
    build || exit $?
    prepare_xctestrun
    ;;
  all)
    run_selected_test minimal-audit-repro-pixel-stable testMinimalAuditReproPixelStableAllAudits
    ;;
  contrast)
    run_selected_test minimal-audit-repro-contrast testMinimalAuditReproContrastOnlyAfterScroll
    ;;
  *)
    echo 'MODE must be build, all, or contrast.' >&2
    exit 2
    ;;
esac
