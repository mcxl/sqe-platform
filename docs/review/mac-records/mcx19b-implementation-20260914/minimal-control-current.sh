#!/bin/bash
set -u
umask 077
export MODE=all
export DESTINATION='platform=iOS Simulator,arch=x86_64,id=D1BAA05C-52DD-4E57-832F-C0A75718E085'
exec bash LOCAL_HOME/ace-private/mcx19b-implementation-20260914/minimal-audit-repro/run-minimal-control-current.sh
