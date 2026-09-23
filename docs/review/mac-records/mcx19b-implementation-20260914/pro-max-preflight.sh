#!/bin/bash
set -eu
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
simulator=D1BAA05C-52DD-4E57-832F-C0A75718E085
app=LOCAL_HOME/ace-private/mcx19b-layout-20260914/derived/Build/Products/Debug-iphonesimulator/ACEClientApp.app
date -u +%FT%TZ > "$run_dir/pro-max-preflight.started"
xcrun simctl boot "$simulator"
xcrun simctl bootstatus "$simulator" -b
xcrun simctl install "$simulator" "$app"
SIMCTL_CHILD_ACE_UI_TEST_SCENARIO=release SIMCTL_CHILD_ACE_UI_TEST_SHOW_DIAGNOSTICS=1 xcrun simctl launch "$simulator" com.example.aceclientapp
xcrun simctl io "$simulator" screenshot "$run_dir/pro-max-preflight.png"
date -u +%FT%TZ > "$run_dir/pro-max-preflight.finished"
