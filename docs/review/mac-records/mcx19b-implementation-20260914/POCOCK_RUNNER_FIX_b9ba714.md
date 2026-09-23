# Pocock Runner Fix Record: b9ba714

Scope: `tools/ace_ios_local.py` and `tools/tests/test_ace_ios_local.py` only.

Baseline SHA-256:

- `tools/ace_ios_local.py`: `22ffe41fd705e61729bd3cee78f88188ae2c1c87b738f5f0a505e5b71bb28dd8`
- `tools/tests/test_ace_ios_local.py`: `b48ec6ec4b94d7974045d2759ab4a6d1f85fe1aee9e4ca6f258f24bcc7788d84`

Candidate SHA-256:

- `tools/ace_ios_local.py`: `b4b5b3d6251a8c1b0c7155745becbd2365c98d3fbb973c167621e240fc7137e5`
- `tools/tests/test_ace_ios_local.py`: `6e52a0f3cb59d3a702cff8b681da4364bcaaaef8760a1b1f2100b0d3997fdfd2`

Check: `PYTHONDONTWRITEBYTECODE=1 /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 tools/tests/test_ace_ios_local.py`

Result: passed, 22 tests. `git diff --check` passed.

The timeout test uses a local Python subprocess only. No Xcode, simulator, or native test command ran.