#!/bin/bash
set -u
umask 077
export PYTHONPYCACHEPREFIX=LOCAL_HOME/ace-private/mcx19b-implementation-20260914/python-cache
base=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
cd LOCAL_HOME/Developer/sqe-platform-release-layout || exit 1
cmp ios/ACEClientApp/ACEClientAppTests/ACEClientAppTests.swift "$base/runner-deliberate-original-test.swift" || exit 1
date -u +%FT%TZ > "$base/runner-restored-pass.started"
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 tools/ace_ios_local.py selected --diagnostic-dirty --device 'iPhone 17 Pro Max' --test ACEClientAppTests/ACEClientAppTests/testRequestIsGETAndHasNoCache > "$base/runner-restored-pass.log" 2>&1
result=$?
printf '%s\n' "$result" > "$base/runner-restored-pass.exit"
date -u +%FT%TZ > "$base/runner-restored-pass.finished"
tail -n 4 "$base/runner-restored-pass.log"
exit "$result"
