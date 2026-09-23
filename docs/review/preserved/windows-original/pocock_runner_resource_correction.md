# Pocock Runner Resource Correction: b9ba714 Pass 2

Scope: `tools/ace_ios_local.py` and `tools/tests/test_ace_ios_local.py` only.

This correction changes the raw evidence projection to use the retained largest pilot batch as a named upper bound for each remaining case. It does not identify that value as a measured per-case value.

It also reviews every retained PNG/JPG hash. It uses marker associations for per-case image counts and separately retains a per-batch unmapped-image upper bound.

Check: `PYTHONDONTWRITEBYTECODE=1 /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 tools/tests/test_ace_ios_local.py`

Result: passed, 24 tests. `git diff --check` passed.

Candidate SHA-256:

- `tools/ace_ios_local.py`: `941849ed593aac7bcff6153e7ae9d9e3fb2cb87d278a65cea986775b002b5a3f`
- `tools/tests/test_ace_ios_local.py`: `32fa082804578796995421e5520275e723bdd8dad8d2d672103712a1cac3bebe`

The fixture uses six pilot setting batches and all 22 approved pilot cases. It proves an affordable gate pass, changed image rejection, and unreviewed retained image rejection. No Xcode or simulator command ran.