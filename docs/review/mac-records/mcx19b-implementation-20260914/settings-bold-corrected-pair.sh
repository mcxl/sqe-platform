#!/bin/bash
set -u
umask 077
p=LOCAL_HOME/ace-private/mcx19b-implementation-20260914
bash "$p/settings-bold-corrected.sh"
change_exit=$?
bash "$p/settings-bold-restored.sh"
restore_exit=$?
printf 'change_exit=%s restore_exit=%s\n' "$change_exit" "$restore_exit"
if [ "$change_exit" -ne 0 ]; then exit "$change_exit"; fi
exit "$restore_exit"
