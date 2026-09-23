# Turbovec Native Pilot Preparation Results

## Status

Prepared And Reviewed For Native Verification. Stage 1 Remains Incomplete.

The user authorised this continuation on 10 September 2026. It follows the approved Stage 1 proposal.
This continuation started at 8:50 pm Sydney time. Its 60-minute limit ends at 9:50 pm.

Windows has no installed Rust toolchain, Swift compiler, Xcode or accessible Mac host.
No native build, simulator test, Rust unit test or device build ran during this continuation.

The earlier [Windows Component Results](2026-09-10-turbovec-windows-component-results.md) remain valid for that separate component check.

## Prepared Output

Pilot Root:

`LOCAL_HOME\AppData\Local\Temp\sqe-turbovec-stage1-20260910-192739\native`

See the [Pilot Readme](LOCAL_HOME/AppData/Local/Temp/sqe-turbovec-stage1-20260910-192739/native/README.md).

| Output | Purpose |
| --- | --- |
| Rust Library And C Header | Expose nine C functions with explicit ownership and error handling. |
| Swift Wrapper | Own the handle and serialise calls on the main actor. |
| Swift Package | Link the generated bridge XCFramework into an isolated test target. |
| Focused XCTest Cases | Check IDs, deletion, allowlists, open errors and a fresh-process reopen. |
| Mac Runner | Retain commands, exit codes, tool versions, hashes, logs and result bundles. |
| Windows Preparation Checks | Check source structure and runner stop conditions. |

The Rust dependency names turbovec 1.0.0 and pins commit `ccab9f325e6ce2a270a87daf01ae4e443bcf2d49`.
The Mac must resolve the dependency and create `Cargo.lock`. No lock or compiled XCFramework exists yet.

The pilot uses 100 generated vectors, 768 dimensions, 4-bit storage and stable UInt64 IDs.
It contains no documents, client data, embedding service or app integration.

## Checks Completed On Windows

Runtime: Bundled Python 3.12.14.

Repository Baseline: `29b62df901af9833be334392d97a6b45a42d1962`. No task commit was created.
The isolated source files are identified by their recorded SHA-256 hashes.

Working Directory: The native pilot root above.

```text
LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe scripts/check_preparation.py
LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe scripts/test_runner_gates.py
```

| Check | Result | Evidence |
| --- | --- | --- |
| Python Syntax, Dependency Pin, C Function Names And Required Files | 14 Checks Passed; Exit 0 | `evidence/preparation-checks.json` and `evidence/preparation-checks.log` |
| Missing Test Bundle Stops Further Tests | Passed | `evidence/runner-gates.log` |
| Zero Executed Tests Cannot Pass | Passed | `evidence/runner-gates.log` |
| One Passing Simulated Test Is Accepted | Passed | `evidence/runner-gates.log` |
| Missing Probe Diagnostics Restores The Source And Stops | Passed | `evidence/runner-gates.log` |
| Cargo Cache Remains Inside The Pilot | Passed After Correction | `evidence/review-regressions-before.log` and `evidence/runner-gates.log` |
| Each Core Test Must Supply Its Execution Marker | Passed After Correction | `evidence/review-regressions-before.log` and `evidence/runner-gates.log` |
| Older Python Stops Before Native Tool Calls | Passed After Correction | `evidence/python-version-before.log` and `evidence/runner-gates.log` |

The runner checks use simulated Xcode output. They do not prove Apple tool behaviour.
The structural check compares function names. It does not compile their parameter types or verify linkage.

Three focused checks reproduced runner defects before correction. These are harness faults; no app code was involved.

| Failing Check | Source Line In Failure Log | Expected | Actual Before Correction |
| --- | --- | --- | --- |
| `RunnerGates.test_cargo_cache_stays_in_pilot` | `scripts/test_runner_gates.py:59` | Cargo Cache Inside The Temporary Pilot | `LOCAL_HOME\.cargo` |
| `RunnerGates.test_each_core_test_needs_its_marker` | `scripts/test_runner_gates.py:66` | Stop When The Validation Test Marker Is Missing | `StopRun` Was Not Raised |
| `RunnerGates.test_old_python_stops_before_tools` | `scripts/test_runner_gates.py:64` | Reject Python 3.10 Before Other Checks | The Mac Requirement Check Ran First |

The two diagnostic runs exited with code 1 and retained the exact assertion details.
The corrected runner uses a pilot-local `CARGO_HOME`, requires each test marker and rejects Python versions below 3.11.
It records the interpreter's full version and executable path in each run manifest.

Final file hashes are in [Preparation Evidence](LOCAL_HOME/AppData/Local/Temp/sqe-turbovec-stage1-20260910-192739/native/evidence/preparation-checks.json).

## Review

Astra remained the primary agent. Terra produced the Rust library; the primary agent produced the Swift code and runner.
Requested settings: Terra / high for the C interface; Sol / high for the fresh review.
Runtime model and effort were not exposed by the native tools.

The primary agent inspected the complete source set and ran the available focused checks.
The first Sol review requested changes to Cargo cache isolation and individual test evidence. Both defects were corrected.
Two other findings were incorrect: `verifySurvivors` and the missing/corrupt-file open checks already existed in the reviewed source.
The retained source hash and line references establish this. No duplicate helper or open tests were added.
The second full review found only a missing Python version record and check. Both were corrected.
Fresh Sol Review Of The Final Correction: Ship For Preparation Only; No Findings.

The final reviewer confirmed the Python correction and reused the preceding complete source review for unchanged code.
The primary agent then compared all 11 source hashes. Every hash matched; exit code 0.
See [Final Review Evidence](LOCAL_HOME/AppData/Local/Temp/sqe-turbovec-stage1-20260910-192739/native/evidence/final-review.json).

## Storage Event

An optional Windows manifest write could not finish at `scripts/run_macos.py:63`.
Expected: A complete JSON manifest. Actual: `OSError: [Errno 28] No space left on device`.
This was an environment fault. The earlier source checks and seven runner tests had passed.

A later disk check showed 636,751,872 bytes available. One targeted retry passed with exit code 0.
It recorded Python 3.12.14 and its executable path. Its native command list was empty.
No files were deleted. The source and prior evidence were preserved.

See the initial `evidence/python-manifest-check.log` and the [Successful Manifest Check](LOCAL_HOME/AppData/Local/Temp/sqe-turbovec-stage1-20260910-192739/native/evidence/20260910T114114Z-9244cef0/manifest.json).

## Required Native Checks

1. Use an authorised Mac with compatible installed Rust tools, Xcode and one booted iOS simulator.
2. Resolve and retain the dependency lock. Build the simulator bridge and the minimal Swift harness.
3. Run the deliberate smoke failure and retain its exact assertion, source line and result bundle.
4. Restore the expected ID and prove the same test passes.
5. Run the ID, deletion, filter and error checks. Reopen saved data in a fresh test process.
6. Run the focused Rust unit tests and compile the iOS device bridge.
7. Build the combined XCFramework and verify the final simulator build.

The runner stops at the first unexpected failure, missing evidence or the 60-minute limit.
It preserves prior output. It does not install tools or retry failed checks.

## Recommendation

Stop Before Stage 2. Complete the native Stage 1 checks first.

The current result prepares those checks. It does not establish native compatibility, semantic search quality or device performance.
No SQE app source, app dependencies, production data, commits, pushes or deployments changed.
No task build or test process remains running.
