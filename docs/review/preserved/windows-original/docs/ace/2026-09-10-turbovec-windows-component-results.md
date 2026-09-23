# Turbovec Windows Component Results

## Result

Focused Windows Component Checks Passed — Stage 1 iOS Acceptance Remains Pending.

The user confirmed Windows after the initial Mac access check.

The task tested the same named library through its official prebuilt Windows Python binding.

The temporary pilot uses generated vectors only. It does not use SQE documents or client data.

## What Passed

| Check | Observed Result |
| --- | --- |
| Package load | turbovec `1.0.0` loaded from the isolated vendor directory. |
| Deliberate failure | `smoke self-search ID` failed with expected ID `9999` and actual ID `1001`. The process returned exit code `1`. |
| Corrected probe | The same assertion passed with expected ID `1001`. The process returned exit code `0`. |
| Add and remove | Added 100 generated vectors. Removed IDs `1010`, `1055` and `1099`. |
| Stable IDs | Each of the 97 remaining vectors returned its original ID when searched. |
| Deleted IDs | All three removed IDs were absent from search results. |
| Allowlist | Results contained exactly the three permitted IDs. Each matching vector ranked first for its own search. |
| Empty metadata matches | The wrapper returned empty results without removing the filter. |
| Unknown allowlist ID | The binding raised the expected `KeyError`. |
| Persistence | Saved the baseline, removed the three IDs and saved again with `sync()`. |
| Fresh process | A separate Python process loaded the saved index. The 97 IDs, deletion state and filters passed again. |

The deliberate failure occurred at `pilot.py:142`. Its traceback and Expected/Actual values were retrieved before the corrected run.

It was an intentional diagnostic check, not an application defect.

The primary inspection corrected one harness expectation before execution. A request for three permitted results must check all three IDs.

## Environment

- Windows: `Windows-11-10.0.26200-SP0`.
- Python: `3.12.14`.
- Existing NumPy: `2.5.1`.
- turbovec: `1.0.0`.
- Dimensions: `768`.
- Bit width: `4`.
- Input: 100 deterministic unit vectors.
- Index: `IdMapIndex`.

No Rust compiler, Swift compiler or Xcode build ran. The Windows test used a prebuilt native library.

## Package And Script Identity

Official package metadata: <https://pypi.org/pypi/turbovec/1.0.0/json>.

Wheel: `turbovec-1.0.0-cp39-abi3-win_amd64.whl`.

Wheel SHA-256, verified against the registry metadata:

`cd855e0b318a57dc57c733f9a62ae98de5192f4f6c2c760e305523e8ceb1b090`

Tested `pilot.py` SHA-256:

`10D1A13A0115C2DE9463B3FC189DEBEFEA8F92F5E02787D98D31E1838490F8E5`

The reviewed Rust source commit remains a reference from the earlier research. This task did not rebuild that source.

## Commands And Evidence

The isolated workspace is:

`LOCAL_HOME\AppData\Local\Temp\sqe-turbovec-stage1-20260910-192739\windows-core`

The Python executable is:

`LOCAL_HOME\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

The commands below ran with that executable and absolute pilot paths:

```text
pilot.py smoke --output-dir results --deliberate-failure
pilot.py smoke --output-dir results
pilot.py create --output-dir results
pilot.py reopen --output-dir results
```

| Evidence | Purpose |
| --- | --- |
| `package-source.json` | Official package URL, version and wheel hash. |
| `load-preflight.json` | Loaded module path and runtime versions. |
| `smoke-deliberate-failure.log` | Deliberate failing assertion, source line and values. |
| `smoke-pass.log` | Corrected passing probe. |
| `create-pass.log` | Add, delete, filter and persistence checks. |
| `reopen-pass.log` | Checks after loading in a separate process. |
| `results/create-result.json` | Structured creation result. |
| `results/index.tvim` | Saved generated-data index. |
| `evidence-manifest.json` | File hashes and command exit codes. |

## Review

The primary agent inspected the complete final test script and executed the checks.

Fresh Sol returned `ship` with no findings. Its scope is the Windows component check only.

The reviewer confirmed the exact script hash and the failure, pass, creation and reopen evidence.

Separate-process execution is supported by the parent command record. Individual process IDs were not captured.

## Limits And Remaining Work

This confirms basic index behaviour on the tested Windows package and generated vectors.

It does not prove useful retrieval from IMS Sources, embedding quality, iPhone speed, secure erasure or crash recovery.

It does not prove the Rust-to-Swift bridge, simulator operation, device-target compilation or physical-device operation.

The approved Stage 1 iOS acceptance criteria remain incomplete. Do not record Stage 1 as complete or adopt the library into SQE.

No app source, app dependency, audit authority or production data changed. No commit, push, merge, deployment or paid build ran.

No build or test process remains active. The task preserves the temporary pilot and evidence for later work.
