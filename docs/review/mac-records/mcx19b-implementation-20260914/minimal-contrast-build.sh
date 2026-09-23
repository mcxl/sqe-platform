#!/bin/bash
set -u
umask 077
export MODE=build
exec bash LOCAL_HOME/ace-private/mcx19b-implementation-20260914/minimal-audit-repro/run-minimal-contrast-build.sh
