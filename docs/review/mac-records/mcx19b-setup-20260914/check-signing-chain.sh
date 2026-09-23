#!/bin/bash
set -u
umask 077
run_dir=LOCAL_HOME/ace-private/mcx19b-local-20260914
security find-certificate -c 'Apple Development' -p > "$run_dir/development-public.pem"
security verify-cert -c "$run_dir/development-public.pem" -p codeSign -v > "$run_dir/signing-chain-check.log" 2>&1
result=$?
printf '%s\n' "$result" > "$run_dir/signing-chain-check.exit"
cat "$run_dir/signing-chain-check.log"
security find-certificate -a -c 'Apple Worldwide Developer Relations' -p > "$run_dir/wwdr-public.pem"
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 - <<'PY'
import re, subprocess
from pathlib import Path
certs = re.findall(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', Path('LOCAL_HOME/ace-private/mcx19b-local-20260914/wwdr-public.pem').read_text(), re.S)
for cert in certs:
    r = subprocess.run(['openssl', 'x509', '-noout', '-subject', '-issuer', '-dates'], input=cert, text=True, capture_output=True)
    print(r.stdout)
PY
