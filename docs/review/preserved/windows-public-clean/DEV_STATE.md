# Development State

Developer navigation: [Roadmap, Code Locations, And Next Steps](DEVELOPER_ROADMAP.md).
Combined view: [SQE Development Hub](SQE_DEVELOPER_HUB.html).
Linear issue: [MCX-19 — Run Live iOS Evidence Before Leaving G0](https://linear.app/mcxi-co/issue/MCX-19/sqe-run-live-ios-evidence-before-leaving-g0).
The roadmap separates planned work from the verified results retained below.

## Current Handover — 9 September 2026

MCX19-A is Done at 3259048186916941bf3557d55503e7375e432c57. The M4 run finished in 7m 54s: three native tests passed, none failed or skipped, and no accessibility issues were reported.
Native process exit: 0. Result counts: [3, 0, 0]. Accessibility issues: [].
Codemagic displays failed because this diagnostic deliberately exits 1 after publishing results. It cannot approve release.
At 3259048: 12 focused checks passed; full local suite 901 passed, one platform skip, one existing warning. GitHub Quality Gates 34220925126 passed.
Estimated cost: US$0.9006 (about US$0.90) before tax and billing rounding. Actual charge is unconfirmed. David was updated; support follow-up is paused. The separate M2 queue is not confirmed resolved.
The temporary approval variable was removed. No second M4 run was submitted.
Source: [M4 Native Run Report](../Codex/2026-09-08/mcx19-functional-accessibility/M4-NATIVE-RUN.md). Results apply only to the recorded commit.

Next action: MCX19-B — define and obtain the remaining full candidate visual QA within approved scope.
UNVERIFIED — UI QA INCOMPLETE: screenshots, dark mode, large Dynamic Type, and normal device-setting behaviour remain unverified for this candidate.
MCX19-C remains blocked by full candidate evidence and required reviews. G0 remains in force; no merge is approved.
MCX-19 remains In Progress in Linear, checked on 9 September 2026. MCX19-A is a local milestone within that issue.

## Earlier Hub And Handover Records — Superseded

The following records describe the earlier state. The M4 result above supersedes their pending functional diagnosis.

### Historical Hub Reconciliation Snapshot — 8 September 2026

Linear MCX-19 and MCX-15 are In Progress and assigned to Alan Richardson. Their due dates are not set.
The inspected checkout is `838ae6af5933495c49f74d3e47109e6159bb951b`, with uncommitted app and diagnostic work present.
Another task moved the checkout to `3105a63b95aec0b04b36b0181abfc4b94539aa7e` during Hub checks. Its results were not verified in this update.
The appearance result below applies to `b6eabcd`, not all later source changes.
The latest fetched Linear MCX-19 comment is the older dark diagnostic at `1dc21a3`.
Next action: reconcile the active task's retained outcomes and candidate before repeating work or requesting further validation.
This documentation update does not establish new test results, live build status, or execution authority.

### Historical Handover — 8 September 2026

The light and dark test repair is complete at commit `b6eabcdc36e80ba55ff0f6dd1201b96a0547b44e`.
Both appearance checks passed in one Mac simulator test. See the verified result below.
Earlier failed appearance results are retained as history, not the current repair status.

Remaining work:

- Diagnose the separate functional and accessibility failures from the earlier full UI run.
- Do not treat the focused appearance pass as a pass for those tests.
- Verify normal device-setting changes separately; the test override does not prove that behaviour.
- Obtain approval for a new bounded plan before further paid validation. The previous one-run approval is spent and removed.
- Keep the full release goal incomplete and G0 in force. No merge is approved.

This handover update is local and uncommitted. It preserves the existing development history.

## MCX-19 Light And Dark Test Repair — Passed

The user approved this bounded repair and at most one paid validation run on 8 September 2026 (AEST).
Work started at 22:50:16 UTC on 7 September. The 60-minute limit was not reached.
Commit `b6eabcdc36e80ba55ff0f6dd1201b96a0547b44e` is pushed to `codex/mcx-19-live-evidence-harness`.
The DEBUG-only override selects the real root view's colour scheme for a valid UI-test scenario.
Missing or invalid appearance values return nil. Production behaviour continues to use the system setting.
The separate `testBothAppearances` checks the view environment in light and dark mode, then terminates each app.
The indicator does not read the requested string. Functional tests no longer contain the shared appearance assertion.
The existing functional matrix remains. The controlled inventory now includes the separate appearance test.

Paid build [6a9f43549bb9204b8f700da2](https://codemagic.io/app/6a9ab144bb26ca57986419f0/build/6a9f43549bb9204b8f700da2) finished in 3m39s at this exact commit.
The simulator test process returned 0. The xcresult summary reports 1 passed, 0 failed, 0 skipped; test failure details are empty.
That single test checks both modes. The workflow deliberately exits 1 because it remains a non-release diagnostic.
The filtered console's assertion source lines are not failed tests; the process result and xcresult counts establish the outcome.
One paid run was used. The temporary exact-commit approval was removed; Codemagic confirmed no existing application variables.

Verification: focused checks 73 passed and 1 Windows skip. Full local suite 891 passed, 1 Windows skip and 1 existing warning; exit 0.
GitHub [Quality Gates 34168789531](https://github.com/mcxl/sqe-platform/actions/runs/34168789531) completed successfully at the repair commit.
Independent plan review accepted the design. A fresh independent code review returned ship with no findings.
No additional builds or local commands remain active. No merge occurred. Existing unrelated DEV_STATE.md edits remain uncommitted.
The appearance test setup is fixed. Normal device-setting changes and the separate functional UI failures were not validated by this run.
The full MCX-19 release goal remains incomplete and G0 remains in force.

## MCX-19 Window Appearance Repair Result

The user approved a targeted repair and one paid diagnostic run on 8 September 2026 (AEST).
Commit `d7955042870c5458778bf57c4bccc5703aa0a08b` moves the debug appearance indicator into a window child view.
It adds a source regression check. It does not force appearance or change the UI assertion.
Only the app source and `tests/test_run_tests.py` were committed and pushed.

Build [6a9f257c68c651950fedc937](https://codemagic.io/app/6a9ab144bb26ca57986419f0/build/6a9f257c68c651950fedc937) finished after 5m56s.
The single dark orientation test failed: process exit 65; counts 0 passed, 1 failed, 0 skipped.
The console and xcresult report the same line 20 assertion: `("light") is not equal to ("dark")`.
Moving the indicator did not resolve the mismatch. Do not claim that appearance selection is fixed.
The workflow remains diagnostic only, not release evidence. No additional paid test started.
The temporary approval variable was removed. Codemagic confirmed no existing application variables.

Verification: focused checks passed (73 passed, 1 Windows skip, 96 subtests).
GitHub Quality Gates [34161181306](https://github.com/mcxl/sqe-platform/actions/runs/34161181306) passed at this commit: 892 Python tests and 68 iOS contract tests.
The local full suite used system Python by mistake: 886 passed, 5 failed, 1 skipped.
All five failures reported missing ReportLab. Those five checks passed in the existing project environment (23.36s).
No dependency was installed. The document toolchain probe passed. All task commands and the paid build have finished.

Next proposed step: set and check the simulator appearance directly, then run the same selector once.
This needs approval for another paid run. Do not repeat the full matrix or negative check.
The separate light-mode failures remain unresolved. PR 6 remains draft. G0 remains in place. Nothing was merged.

## MCX-19 Dark Orientation Diagnostic Result

Build [6a9f1efdeed0ec7a04ab9549](https://codemagic.io/app/6a9ab144bb26ca57986419f0/build/6a9f1efdeed0ec7a04ab9549) finished after 5m21s. Gate duration4m49s.
Exact head: `1dc21a3481de549f338b34ee298f67c3adb0bc5d`.
Branch: `codex/mcx-19-live-evidence-harness`. PR6 remains draft; G0 remains in place.

The single dark-mode `testReleaseOrientationHooks` test failed with process exit65.
Counts: 0passed,1failed,0skipped.
Both the redacted log and xcresult failure record identify the same assertion:
`ACEClientAppUITests.swift:20: XCTAssertEqual failed: ("light") is not equal to ("dark")`.

This proves a mismatch between requested dark appearance and the app's reported effective appearance.
It occurs in the shared launch check. The evidence does not yet distinguish ineffective appearance selection from an incorrect appearance indicator.
Do not claim that every dark test failed for this reason without its own failure evidence.
This diagnostic does not explain the three light-mode selector failures.
No negative check ran; its last full-run result remains passed.
Provider status is failed and script exit1 is intentional for this non-release diagnostic; the UI failure is independently proven above.

Exact-head GitHub Quality Gates34159542491 passed before launch. Local focused7passed; complete suite890passed,1Windows skip. Independent review accepted the unchanged diagnostic.
No app code or UI assertions changed. Existing security checks remained unchanged.
After terminal state, the disposable approval variable was verified by app, name and group `mcx19_diagnostic`, then deleted. Codemagic confirmed `No existing variables`.
No replacement run, post-launch code change, merge, Production action, dependency installation or payment-setting change occurred.
The user activated the paid subscription themselves.

Next bounded work requires separate approval: inspect and repair only the dark appearance selection/measurement path, preserving the actual dark assertion.
Candidate files: `ios/ACEClientApp/ACEClientApp/ACEClientAppApp.swift`, `ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift`; change harness files only if tracing proves they are involved.
First distinguish the requested appearance, actual window appearance and indicator reading. Do not hard-code the indicator to the requested input.
Use a focused regression, required full local validation and fresh review. Any subsequent Mac run requires approval.
Do not repeat the full20-command run or reopen the passing negative check. Keep unrelated light-mode failures separate.

PR result: https://github.com/mcxl/sqe-platform/pull/6#issuecomment-5575450031
Linear comment: `151a44df-482d-4168-ab46-b12a4a58817b`.
This terminal result supersedes the active/prepared entries below. No build remains active.

## Dark Diagnostic Started — 8 September 2026 AEST

The user requested launch after activating a paid Codemagic subscription themselves.
Active Pay-as-you-go status was verified. No subscription or payment setting was changed by the agent.
Reviewed commit `1dc21a3481de549f338b34ee298f67c3adb0bc5d` was pushed to `codex/mcx-19-live-evidence-harness`.
Only `codemagic.yaml`, `tests/test_diagnose_ios.py`, and `tools/diagnose_ios.py` were committed.
The complete diff matched the accepted review; seven focused tests passed again. Prior full validation: 890 passed, one Windows skip.
GitHub Quality Gates `34159542491` passed at this exact head. PR 6 remains draft.

One diagnostic build was queued at approximately 20:30:53 UTC on 7 September.
Build `6a9f1efdeed0ec7a04ab9549` confirms the exact head and dark orientation workflow on Mac mini M2.
URL: https://codemagic.io/app/6a9ab144bb26ca57986419f0/build/6a9f1efdeed0ec7a04ab9549
Scope: only `testReleaseOrientationHooks`, dark. No negative build or full matrix.
The diagnostic always returns 1; provider failure alone is not proof of a UI failure.
Read the retained redacted assertion and counts before classifying the result.

The run-only approval variable exists in `mcx19_diagnostic`. Verify its identity and delete it after this run ends.
Cancel this build if still active at 20:46 UTC. Stop monitoring work by 20:50 UTC. No replacement run.
The two-minute monitor `mcx-19-approved-full-run-monitor` now targets only this diagnostic.
Working Chrome tab: `2072740825`; stale billing tab `2072740865` times out.
No further code change, commit, push, merge, installation, payment action, or Production work is authorised.
Record results in PR 6, Linear MCX-19, and this file, then pause the monitor.
This section supersedes the prepared/paused state below. Existing DEV_STATE.md changes remain uncommitted.

## Dark Orientation Diagnostic Prepared — 8 September 2026 AEST

The user approved the proposed single dark-mode orientation diagnostic.
The diagnostic changes remain uncommitted on `codex/mcx-19-live-evidence-harness` at head `3a52b52c0e6124137f2f25a9ce810fb489c7adcf`.
Only `tools/diagnose_ios.py`, `tests/test_diagnose_ios.py`, and `codemagic.yaml` changed for this diagnostic.
The existing script now selects `testReleaseOrientationHooks` with dark appearance and omits the negative build.
All app code, UI assertions, approval gates, redaction controls, and artifact boundaries remain unchanged.
The manual diagnostic retains its 15-minute provider limit and six-minute UI process limit.
It remains explicitly not release evidence and returns 1 by design.

The regression test first failed on the old selector and unwanted negative build.
After the scoped change, all seven focused tests passed.
One complete suite in the existing `.venv` finished with exit 0: 890 passed, one Windows Unix-shell skip, one existing Starlette/httpx warning.
Duration: 647.09 seconds. Independent read-only review found no blocking findings.
Primary inspection covered the complete three-file diff. No code changed during validation.

Chrome access failed twice: the prior tab was absent, then creation of a billing tab timed out and reset the browser tool.
The launch is paused. Current free capacity is unverified. No temporary approval variable was created.
No commit, push, Mac run, payment, dependency installation, or merge occurred in this chunk.
No test process remains active. Existing unrelated state changes remain preserved.
The user was asked to restart Chrome and leave Codemagic open.

Next: confirm final review, exact outgoing files and authority, commit/push the reviewed diagnostic, and verify required GitHub checks at its exact head.
Then verify free capacity before the approved one-selector Mac run. Never substitute Windows tests for Mac evidence.
Existing repository-owned security checks remain unchanged. No launch while required checks or free-capacity evidence are missing.
Do not run the full UI matrix or repeat the passing negative check. Do not merge.

## MCX-19 Final Mac Result — 7 September 2026

The approved run finished with status **failed** after 41m 44s. The live gate exited 1 after 41m 17s.
Build: [6a9e9688c43deced06210ec7](https://codemagic.io/app/6a9ab144bb26ca57986419f0/build/6a9e9688c43deced06210ec7).
Head: `3a52b52c0e6124137f2f25a9ce810fb489c7adcf`.
Branch: `codex/mcx-19-live-evidence-harness`.
Baseline: `main` at `7da6228dc87ad970aa8d44365fbc3823c58020da` (recorded baseline, not new merge approval).
PR: https://github.com/mcxl/sqe-platform/pull/6 remains draft. G0 remains in place.

### Verified Results

All 65 Mac unit tests passed, process exit 0. All 42 Mac evidence-contract tests passed, process exit 0.
The negative check passed: process exit 65, logical exit 0, reason `negative-configuration-rejected`.
It rejected invalid configuration as required. This result is separate from the UI failures.

All 20 UI commands completed. Four passed and 16 failed.
Each pass below executed one test and exited 0.
Each failure exited 65, logical exit 1, reason `command-nonzero`, diagnostic `test-failures-recorded`.
Failed-test counts and assertion text are not present in these safe records.

| UI Method | SE Light | SE Dark | 16 Pro Max Light | 16 Pro Max Dark |
|---|---|---|---|---|
| testLaunchShowsSafeConfigurationState | Pass | Fail | Pass | Fail |
| testSignInPasswordFieldIsSecure | Fail | Fail | Fail | Fail |
| testFictionalReleaseHasApprovedCopyControls | Fail | Fail | Fail | Fail |
| testAllControlledScenariosShowExpectedStateAndAudit | Fail | Fail | Fail | Fail |
| testReleaseOrientationHooks | Pass | Fail | Pass | Fail |

SE means iPhone SE (3rd generation). Each cell identifies one command.
The command name is `ios-release-{device}-{light|dark}-{method}`.

Exact-head GitHub [Quality Gates 34112191464](https://github.com/mcxl/sqe-platform/actions/runs/34112191464) passed, including 890 Python tests.
GitHub now separately reports this Codemagic check as FAILURE.
Earlier local validation: 889 passed, one Windows skip. Independent review accepted the reporting repair.
No new review or test run occurred during this monitoring chunk.

### Cleanup And Evidence Limits

After the build ended, the run-only approval variable was verified by app, name and group.
Only `ACE_LIVE_EVIDENCE_APPROVED_COMMIT` in `mcx19_live_evidence` was deleted.
Codemagic then showed `No existing variables`. Its value was not displayed.
No replacement run, payment, dependency installation, code change, commit, push, merge or Production action occurred.
The build is no longer active.

Safe progress records retained all 23 command outcomes through completion.
Codemagic lists `sqe-platform_10_artifacts.zip` (740 B). Its contents were not independently inspected.
The failed gate did not establish final artifact, checksum or redaction acceptance.
The progress record remains incomplete and `releaseEvidence: false`; it is not release approval.

The UI failure causes remain unknown. Test failures do not distinguish application faults from test setup or environment faults.
All dark commands failed. Three light selectors failed on both devices. These are observed patterns, not proven causes.
The negative-check fault did not recur. No further negative-check repair is supported by this result.

### Next Bounded Plan — Requires Separate Approval

Use a 30-minute read-only diagnosis, with a 45-minute hard limit. Do not start another full run.
Inspect `ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift` and the related launch setup in `tools/run_tests.py`.
Compare dark-mode setup and the three failing light selectors with the passing launch and orientation selectors.
Inspect related application files only when those assertions identify the relevant code.
First use existing permitted evidence. If assertions remain unavailable, specify the smallest single-selector diagnostic needed.
Do not implement another reporting repair merely to repeat this full run.
Any later code repair needs scoped files, focused tests, one final full suite, fresh independent review, and separate live-run approval.
Keep the two-failed-attempt stop rule. Do not merge this head.

Acceptance for the next plan: identify a supported cause, or identify the exact missing assertion and smallest permitted evidence step.

Final result comment: https://github.com/mcxl/sqe-platform/pull/6#issuecomment-5570031930
Linear result comment: `97f4fe91-9f9a-4760-974d-3d7d130d1769`.
This terminal result supersedes all active-run entries below. The monitor is verified PAUSED after cleanup and records.
The chunk finished at approximately 11:37 UTC, after 51 minutes, within the 60-minute hard limit.

## Current Run — 7 September 2026, 10:53 UTC

This section takes precedence over the historical run records below.
The current pushed head is `3a52b52c0e6124137f2f25a9ce810fb489c7adcf`.
Branch: `codex/mcx-19-live-evidence-harness`. PR 6 remains draft. G0 remains in place.

After Chrome restarted, one approved full Codemagic run started at approximately 10:48:40 UTC.
Build: `6a9e9688c43deced06210ec7`; app: `6a9ab144bb26ca57986419f0`.
The build overview confirmed the exact head and manual live-evidence workflow on Mac mini M2.
URL: https://codemagic.io/app/6a9ab144bb26ca57986419f0/build/6a9e9688c43deced06210ec7

Before launch, Codemagic showed 435 of 500 free minutes used, no enabled subscription, and no transactions.
GitHub Quality Gates run `34112191464` passed for this head, including 890 Python tests.
Local validation recorded 889 passes and one Windows skip. Independent review accepted the unchanged repair.
The repair changes only `tools/run_tests.py`, `tests/test_run_tests.py`, and `codemagic.yaml`.

Safe console progress confirms that all 65 unit tests passed with process exit 0.
At 10:58 UTC, three UI commands completed for iPhone SE (3rd generation), light.
`testLaunchShowsSafeConfigurationState` passed: one test, process exit 0.
`testSignInPasswordFieldIsSecure` failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
`testFictionalReleaseHasApprovedCopyControls` failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
The safe records do not identify either failed assertion or establish an application, harness, or environment cause.
At 11:04 UTC, seven of 20 UI commands have completed: two passed and five failed.
Additional iPhone SE (3rd generation), light results:
`testAllControlledScenariosShowExpectedStateAndAudit` failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
`testReleaseOrientationHooks` passed: one test, process exit 0.
Additional iPhone SE (3rd generation), dark results:
`testLaunchShowsSafeConfigurationState` failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
`testSignInPasswordFieldIsSecure` failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
At 11:06 UTC, eight UI commands have completed: two passed and six failed.
The dark `testFictionalReleaseHasApprovedCopyControls` command failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
At 11:09 UTC, nine UI commands have completed: two passed and seven failed.
The dark `testAllControlledScenariosShowExpectedStateAndAudit` command failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
At 11:15 UTC, 12 UI commands have completed: three passed and nine failed.
The iPhone SE (3rd generation), dark `testReleaseOrientationHooks` command failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
The iPhone 16 Pro Max, light `testLaunchShowsSafeConfigurationState` command passed: one test, process exit 0.
The iPhone 16 Pro Max, light `testSignInPasswordFieldIsSecure` command failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
At 11:21 UTC, 15 UI commands have completed: four passed and 11 failed.
The iPhone 16 Pro Max, light `testFictionalReleaseHasApprovedCopyControls` command failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
The iPhone 16 Pro Max, light `testAllControlledScenariosShowExpectedStateAndAudit` command failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
The iPhone 16 Pro Max, light `testReleaseOrientationHooks` command passed: one test, process exit 0.
At 11:27 UTC, 18 UI commands have completed: four passed and 14 failed.
The iPhone 16 Pro Max, dark `testLaunchShowsSafeConfigurationState` command failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
The iPhone 16 Pro Max, dark `testSignInPasswordFieldIsSecure` command failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
The iPhone 16 Pro Max, dark `testFictionalReleaseHasApprovedCopyControls` command failed: process exit 65, reason `command-nonzero`, diagnostic `test-failures-recorded`.
The iPhone 16 Pro Max, dark `testAllControlledScenariosShowExpectedStateAndAudit` command is active. The remaining UI results are unknown.
About 30 minutes of the approved chunk have elapsed. About 30 minutes remain before the hard stop.
The browser tab was unavailable; one replacement monitor tab, `2072740846`, restored access to this same build.
No contract result or negative-check result is established yet.
Progress records are incomplete evidence, not final gate acceptance or proof that the application works.

The temporary `ACE_LIVE_EVIDENCE_APPROVED_COMMIT` variable exists only for this run in group `mcx19_live_evidence`.
After the run ends, verify its identity, delete only that variable, and verify absence. Never display its value.
This cleanup and result updates to PR 6, Linear MCX-19, and this file are authorised.

The resumed chunk began at 10:45:32 UTC. Cancel this build if still active at 11:40 UTC.
The hard stop is 11:45:32 UTC. Do not extend or start a replacement run.
The active five-minute monitor is `mcx-19-approved-full-run-monitor` and targets only this build.
Report progress at 11:00:32, 11:15:32, and 11:30:32 UTC, or on a material result or blocker.
Preserve each completed command result separately. Treat missing results as unknown.
No code change, installation, payment, commit, push, merge, or Production action is authorised during monitoring.
After terminal results and cleanup, update the records and pause the monitor.
If successful, prepare an exact-head merge decision for user approval. Otherwise, report a bounded repair plan.

## Controlled Branch

The current delivery branch is `codex/mcx-19-live-evidence-harness`.
Its baseline is `main` at `7da6228dc87ad970aa8d44365fbc3823c58020da`.
The reviewed candidate head is `18ec5a0456c1392022f27007dab3fd071266b9f7`.

## Current Controls

G0 blocks client data. Use fictional, public, or AuditCo-owned test data only.
The accountable auditor makes final decisions.

Do not run DeepSec without new approval and an approved isolation design.
Do not deploy to Production. Do not merge without separate approval.

## Verified Platform

The Python core records assessment, planning, review, and approval controls.
The web workbench records controlled evidence review work.
The iOS client source is a read-only, controlled snapshot.

The candidate passed focused tests, the complete test suite, and GitHub quality gates.
Pocock found no issues. Fresh Sol gave a `ship` result before the live run.

The release service and release projection retain their approved ownership boundaries.
See [Approved Specifications](docs/specs/) and [Architecture Decisions](docs/adr/).

## Current Delivery Goal

MCX-19 must obtain successful live iOS evidence before work leaves G0.

Codemagic build `6a9e11ee6cd6ecb1a925e278` ran at prior head `40f04d96311d6cc3f384d3afe06eb9329df33859`.
It failed after 51 minutes and 33 seconds.
The controlled result found one negative-check failure and 20 UI command failures.
No retry, payment request, Production deployment, or merge occurred.

Pull request 6 remains open and draft. Linear MCX-19 remains In Progress.
The prior temporary approval variable was deleted. Its absence was verified.

The reviewed reporting repair changed only `tools/run_tests.py` and `tests/test_run_tests.py`.
Terra implemented it. Final local validation recorded 878 passes and one Windows platform skip.
Fresh Sol/High gave `ship` with no findings after the final change.
The primary task inspected the full diff and reran relevant focused checks.
The reviewed file hashes matched before commit. Unrelated state changes stayed outside the commit.
Exact-head GitHub Quality Gates run `34084158901` passed all jobs.

The user authorised one new live run after the checks and free-capacity gate passed.
Codemagic build `6a9e427c9b37efb3f35c7f9a` started at 04:50 UTC on 2026-09-07.
Its build overview confirms the candidate commit, manual MCX-19 workflow, and Mac mini M2.
Final status: failed after 41 minutes 22 seconds. The live gate exited 1 after 40 minutes 58 seconds.
All 20 UI commands exited 65 with `command-nonzero` and `test-failures-recorded` diagnostics.
Their readable result summaries contained positive failed-test counts.
The safe output did not identify the failed assertions, launch faults, or setup faults.
The negative check separately exited 65 with `negative-configuration-unrelated-nonzero`.
Its available bounded log did not contain the required rejection text. The actual build error remains unknown.
Matching exit codes do not prove one shared cause.
Application, test-harness, and environment causes remain unresolved. Improved reporting does not prove that the application works.
Unit and contract success is not independently established by the inspected failure summary.
The separate Codemagic check now reports failure on GitHub. G0 remains in place.

The temporary approval variable was verified by application, name, and group, then deleted after the run ended.
Codemagic confirmed `No existing variables` and `Success Settings updated`. Its value was not displayed.
No replacement run, post-commit code change, dependency installation, payment, merge, or Production action occurred.
The per-command record and bounded plan are in [PR result comment](https://github.com/mcxl/sqe-platform/pull/6#issuecomment-5565562308).
Linear MCX-19 has the same verified result and remains In Progress.

The two-failed-attempt stop rule applies to the repeated broad UI/negative failure pattern.
The next proposed chunk is a 45-minute diagnostic repair. It requires separate approval and excludes a live run.
First check safe access to existing details. If unavailable, specify fixed UI and negative-build error categories.
Proposed repair files are `tools/run_tests.py` and `tests/test_run_tests.py` only.
Do not change application behaviour or project settings without supported failure evidence.
Use SQE Sol Advisor, Terra, focused tests, one final complete suite, and Fresh Sol review.
Stop with the reviewed repair and a proposed smallest Mac validation scope.
Any later repair, later live run, and exact-head merge require separate authority. Do not merge this failed live candidate.

## Source Of Truth

### Latest Two-Command Diagnostic

The user approved one 15-minute diagnostic after existing error files were unavailable.
Commits `c22c246` and `18ec5a0` added only the diagnostic script, tests, and isolated manual workflow.
Build `6a9e55095539729b111ebdc4` ran at the current candidate head and finished after 4 minutes 31 seconds.
It retained the actual redacted error records as a provider artifact. No full 20-command run occurred.

The single UI test failed at `ACEClientAppUITests.swift:7`:
`ACE_UI_TEST_APPEARANCE must be light or dark`.
Its appearance input did not reach the runner as a valid value. The result summary records 0 passed, 1 failed, 0 skipped.
This proves a test input fault for this selector, not an application fault or every other selector's cause.

The negative build separately failed because signing requires a development team.
Its required configuration rejection was absent. The next repair should use an unsigned simulator build, not paid signing.
Both processes exited 65. The causes are separate.

Final local suite: 884 passed, 1 Windows-only skip, 1 existing warning. Fresh independent review: ship.
Exact-head GitHub Quality Gates run `34089033757` passed all jobs.
Existing repository security checks remain unchanged. No app behaviour changed.
The diagnostic temporary variable in `mcx19_diagnostic` was deleted and absence was verified.
No live process remains. No payment, install, replacement run, merge, or Production action occurred.
Next: separately approve the small appearance-forwarding and unsigned-negative-build repair, then review it.
Any later Mac run requires separate approval. G0 remains in place.

Code and approved specifications control when records differ.

### Two Setup Repairs Ready Locally

The user approved repair of the two identified setup faults.
The uncommitted repair forwards `TEST_RUNNER_ACE_UI_TEST_APPEARANCE` through the controlled runner and Makefile.
It removes the conflicting appearance macro from the UI scheme. UI assertions remain unchanged.
Apple documents this forwarding mechanism in its Xcode environment-variable reference.
All three negative-check entry points now share an unsigned `iphonesimulator` build command.
The invalid origin and exact required rejection text remain unchanged. No app behaviour or Production signing setting changed.

Focused checks: 68 passed and one Windows-only skip. The scheme XML is valid.
Final complete suite in the existing `.venv`: 885 passed, one Windows-only skip, one existing dependency warning.
The final suite exited 0 after 17 minutes 8 seconds. `git diff --check` passed.
Fresh independent read-only review: ship, no blocking findings. The primary inspected the complete repair diff.
This is local verification only. GitHub checks and Mac verification do not yet cover the uncommitted repair.
No commit, push, live run, dependency installation, payment, merge, or Production action occurred in this repair chunk.
Next: obtain approval to commit/push the reviewed repair and run one short two-command Mac verification.
Do not infer that all UI tests or the application pass from the local tests.

### Two Setup Repairs Verified On Mac

The next approved chunk committed and pushed the five reviewed files as `c8dc459c20472092b80b83d44d980b5670dc61fa`.
Branch: `codex/mcx-19-live-evidence-harness`. PR #6 remains draft. Base remains `7da6228dc87ad970aa8d44365fbc3823c58020da`.
No repair code changed after review. Existing DEV_STATE.md changes stayed outside the commit.
GitHub Quality Gates run `34094774767` passed for this exact commit. Python Core: 886 passed, two warnings.

Codemagic build `6a9e67f28b2f99f12085ab02` used the exact commit and the isolated two-command workflow.
It finished in 3 minutes 25 seconds, within the 15-minute limit.
The light UI selector `testLaunchShowsSafeConfigurationState` exited 0: one passed, zero failed, zero skipped.
The result summary recorded no test failures. The appearance-input setup fault did not recur.
The negative check exited 65 and found the exact required approved-HTTPS-origin rejection.
The unsigned simulator build reached the intended rejection instead of the signing fault.

Both scoped acceptance checks passed. The diagnostic script deliberately returns 1, so the provider badge remains red.
This is not release evidence. Do not change the report just to make that badge green.
The provider retained `sqe-platform_2_artifacts.zip` (990 bytes). Safe console output supplied the verified results.
The artifact was not separately downloaded or checksum-verified.
The run-only variable in `mcx19_diagnostic` was deleted after identity checks. `No existing variables` confirmed cleanup.
No value was displayed. No run remains active. No payment, replacement run, merge, or Production action occurred.

PR result: https://github.com/mcxl/sqe-platform/pull/6#issuecomment-5566957681
Linear MCX-19 contains the same result and remains In Progress. G0 remains in place.
The two setup repairs are verified for the small approved scope. The other UI commands remain unverified at this head.
Next: seek separate approval for one full controlled iOS evidence run at this exact head.
Recheck unchanged gates and free capacity before launch. Do not change code or start another run under the completed chunk.

### Approved Full Run Active — 7 September 2026

The user approved one full controlled iOS run after both setup repairs passed the small Mac check.
Build: `6a9e77d0e034b85447977f51`, workflow `ace-ios-live-evidence-manual`.
URL: https://codemagic.io/app/6a9ab144bb26ca57986419f0/build/6a9e77d0e034b85447977f51
Provider metadata confirmed commit `c8dc459c20472092b80b83d44d980b5670dc61fa` on `codex/mcx-19-live-evidence-harness`.
The unchanged GitHub Quality Gates run `34094774767` passed. PR base and draft status are unchanged.
Before launch, Codemagic showed 384 of 500 free minutes used, no enabled subscription, and no previous transactions.
No code changed. The full gate includes 65 unit tests, 20 UI commands, 42 evidence-contract tests, and the negative check.
The reviewed harness keeps raw files outside Git and checks artifacts, checksums, and redaction before success.

Chunk start: 08:33:39 UTC. Run start: approximately 08:37 UTC. Hard stop: 09:33:39 UTC on 7 September 2026.
Cancel the exact run at or after 09:28 UTC if it remains active, then verify terminal state and cleanup.
The provider workflow has a 90-minute timeout, but this chunk uses the stricter 60-minute limit.
The current status is building; no final test results are available. Do not infer pass or failure.
The temporary ACE_LIVE_EVIDENCE_APPROVED_COMMIT variable exists only in `mcx19_live_evidence` for this run.
Cleanup is pending: verify app, variable name, and group before deleting it after the run ends. Never display its value.

Thread monitor `mcx-19-approved-full-run-monitor` checks every five minutes and must stop after terminal reporting and cleanup.
Report elapsed and remaining time at 15-minute milestones, and report terminal or actionable changes promptly.
Record verified results in PR #6, Linear MCX-19 and this file. Separate every UI-command result from the negative result.
No replacement run, code change, dependency installation, payment, commit, push, merge, or Production action is authorised.
If the run passes, prepare the exact-head merge decision with remaining gates. If it fails, give a bounded repair plan.
G0 remains in place. Pause the monitor after completion or after recording an unresolved hard-limit blocker.

### Full Run Stopped — Final Result

Build `6a9e77d0e034b85447977f51` was cancelled just after 09:28 UTC at the stated cancellation deadline.
Codemagic confirmed terminal `canceled`, duration 50 minutes 31 seconds. The test gate used 49 minutes 57 seconds.
This is an operator cancellation, not a proven test failure. No final console results or retained artifact entry were available.
Each of the 20 UI-command outcomes is unknown. Unit, evidence-contract, negative-check and artifact-check outcomes are also unknown.
The earlier small diagnostic passes do not establish this full-run result. No application, test, or environment fault is proven here.
The exact head remains `c8dc459c20472092b80b83d44d980b5670dc61fa`; GitHub Quality Gates passed at that head.

Cleanup completed: the run-only variable in `mcx19_live_evidence` was identified and deleted after terminal cancellation.
Codemagic confirmed `No existing variables`. Its value was not displayed. No run remains active.
PR #6 and Linear MCX-19 now contain the full separate-outcome record and bounded next plan.
Result: https://github.com/mcxl/sqe-platform/pull/6#issuecomment-5568546126
The monitor is being paused. No code change, replacement run, payment, dependency installation, commit, push, merge, or Production action occurred.

Next permitted step requires separate approval: a bounded local reporting repair in tools/run_tests.py, tests/test_run_tests.py, and codemagic.yaml.
Record each completed command immediately in a safe summary and retain that summary on interruption.
Keep all assertions and data controls unchanged. Use focused interruption/redaction tests, one final complete suite, and fresh review.
Do not repeat the unchanged full run. Which command consumed the time and which commands completed remain unknown.
G0 remains in place. PR #6 remains draft and MCX-19 remains In Progress. No merge decision is ready.

### Immediate Progress Repair — Local, Validation Incomplete

The user approved a local reporting repair after the cancelled full run.
Three files changed: tools/run_tests.py, tests/test_run_tests.py, and codemagic.yaml. No application code changed.
The runner records each completed command immediately, updates its external manifest, and flushes safe console events.
An atomic live-evidence-progress.json file records completed results and the active command.
The file always declares incomplete status and releaseEvidence false. Only this safe file is listed for provider publication.
Raw logs, bundles, assertions, command order, counts, exact-head controls and acceptance checks remain unchanged.
Focused regression tests cover interruption, abrupt process exit, safe fields, flushing, atomic replacement failure and bounded Windows retries.
A reproduced Windows WinError 5 on file replacement led to three bounded replacement attempts, with at most two 0.1-second waits.

Final focused checks: 71 passed, one Windows-only skip in 8.19 seconds.
Independent read-only review: no blocking code findings. Overall acceptance remains blocked by incomplete suite evidence.
The primary inspected the complete three-file diff. git diff --check passed.
One premature complete-suite start was cancelled when the earlier focused failure arrived.
The next complete-suite invocation emitted failure/error markers and was stopped before its final traceback report.
That early stop lost the precise failure details. No complete-suite pass is claimed, and the failure cause remains unknown.
Safe focused diagnosis: the PDF test passed; the export module passed 40 tests with one existing dependency warning.
The C drive had approximately 986 MB free. This is a risk, not a proven failure cause.
No Python or soffice processes remained in the final process snapshot. No live run occurred.

The repair remains uncommitted. No push, payment, installation, cleanup, merge, or Production action occurred.
Existing DEV_STATE.md work was preserved. The old live-run monitor remains paused.
Next approval required: one complete-suite attempt with stop-on-first-failure and retained diagnostics, after a disk-space check.
Do not start another Codemagic run or commit this repair before validation and acceptance are complete.

### Progress Repair — Complete Local Validation Passed

The user approved one stop-on-first-failure complete-suite attempt with a retained report.
No code changed during this attempt. The existing .venv ran pytest -x -q --tb=short with an external JUnit report.
Final result: 889 passed, one Windows-only skip, one existing dependency warning; exit 0 after 364.70 seconds.
The retained XML independently records 890 tests, zero errors, zero failures, and one skip.
Report: LOCAL_HOME/Documents/Codex/2026-09-07/mcx19-diagnostic-reporting/outputs/local-suite-first-failure.xml
The primary verified that report and git diff --check. The independent reviewer rechecked the unchanged three-file diff and XML.
Final review: accept the local repair, no blocking findings. Earlier interrupted suite failures remain unexplained.
The current complete-suite pass resolves the local validation blocker; it does not diagnose those earlier failures.

The repair remains uncommitted in tools/run_tests.py, tests/test_run_tests.py, and codemagic.yaml.
Existing repository-owned security checks remain unchanged. Exact-head GitHub checks are still required after a separately approved push.
No live Mac cancellation or artifact collection has been verified for this repair. Progress is not release evidence.
No cleanup, payment, installation, commit, push, Codemagic run, merge, or Production action occurred in this validation chunk.
Next: obtain approval to commit/push the reviewed repair and check the new exact head. A later Mac run requires separate approval.

### Progress Repair Pushed — Exact-Head GitHub Checks Passed

The user approved commit/push and GitHub checks. Commit `3a52b52c0e6124137f2f25a9ce810fb489c7adcf` contains only the three reviewed repair files.
Branch remains `codex/mcx-19-live-evidence-harness`. DEV_STATE.md stayed outside the commit.
The primary reread the complete diff and verified the outgoing one-commit range before normal push.
Exact-head GitHub Quality Gates run `34112191464` passed. Python Core: 890 passed, two warnings in 65.93 seconds.
All PR checks passed. PR #6 remains draft. No new Codemagic run or merge occurred.
PR/Linear record: https://github.com/mcxl/sqe-platform/pull/6#issuecomment-5569369090
The repair is now remote and CI-verified. Mac progress retention and full iOS test outcomes still require a separately approved run.
Next: one separately approved controlled Mac run at this exact head, after free-capacity and unchanged-gate checks.
No payment, installation, force-push, history rewrite, merge, or Production action occurred.

### Next Mac Run Approved — Launch Blocked Before Any Run

The user approved one Mac run at `3a52b52c0e6124137f2f25a9ce810fb489c7adcf`.
At 10:39 UTC on 7 September 2026, the exact PR head/base and passing GitHub run `34112191464` were verified.
Browser creation failed with FILE_ERROR_NO_SPACE. A read-only drive check showed about 1.16 GB free, not zero.
The existing Codemagic settings tab was found, but selecting it timed out. The browser method stopped after these two failures.
Current free Codemagic capacity could not be verified. No temporary variable was created and no run was launched.
No cleanup is pending for this attempted launch. No code, commit, push, merge, payment, or Production action occurred.
Resume the already approved single run only after browser access works and free capacity is verified. Do not assume a run exists.

Provider records, Linear, GitHub, and test outputs record delivery evidence.
Generated artefacts remain outside version control.
