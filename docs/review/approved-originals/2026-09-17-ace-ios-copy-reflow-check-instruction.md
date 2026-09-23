# Codex Instruction: ACE iOS Copy Contrast — Reflow Dependency Check (D2)

Date: 17 September 2026, revised after four Codex reviews.
Author: Fable, from `FABLE-ROOT-CAUSE-BRIEF-20260917.md`, `FABLE-ROOT-CAUSE-RESPONSE-20260917.md` and read-only inspection of the Mac evidence root on 17 September.
Status: Draft For Human Approval. Authorises nothing until the user approves this exact file by its SHA-256. Supersedes the first draft (SHA-256 `11d440d7a2b9c6044ed01c594fee650e69f787f8d04c604b2b3110b8068de3a8`), the second draft (SHA-256 `c578b5ee8e122d13dac61cdb220349f87f004164e96bc2e0fe92fc18820a4b30`) and the third draft (SHA-256 `363e5434378b875c4867cfb1f7fcb1f2bd0069915f1b3c19135c4af3f07096e9`) in full.

Changes from the first draft, each from the Codex review: the outcome table records support or contradiction only and leaves cause, colours and any Apple defect unresolved; the committed initial unrestricted audit is preserved identically in both arms and later calls are described as repeated diagnostic calls within one launch, not independent trials; the harness check is a deliberate native assertion failure with retrieved evidence, followed by a corrected pass, and trial records must survive a thrown audit error; the budget is reconciled to four executions with no retry; compiling the temporary UI test against the verified app is explicit and the native summary must show the exact method executed; and D2 ends with a recommendation, never with P0 or the discovery pilot described as ready.

Changes from the second draft, each from the Codex review: call 0 is excluded from the X and Y comparison and an initial-audit finding is preserved as its own item; a genuine audit finding during a harness execution is not a harness fault; `ACE_D2_MAX_CALLS` counts post-copy calls, 2 for both harness executions giving three records, 30 for each arm giving 31; and the section 1 limit and section 9 estimate are reconciled.

Change from the third draft (SHA-256 `363e5434378b875c4867cfb1f7fcb1f2bd0069915f1b3c19135c4af3f07096e9`), from the Codex review: the harness gate rule now requires native PASS for the corrected check and native FAIL with the deliberate text for the failure check, each with exactly three records and no unexpected findings or errors. A genuine audit finding that prevents either demonstration marks the gate incomplete and stops before arm X and arm Y. It is classified separately and never bypasses the gate.

This instruction defines one diagnostic. It does not change the app, the committed UI tests, the runner, the acceptance audit, the 836-case decision, or any gate in Revision 5. It grants no acceptance or pilot credit.

## 1. Authority And Boundaries

- Approval of this file permits one temporary UI-test variant, kept as a patch outside the candidate, and at most four native executions on the Mac.
- No commit, push, merge, purchase, framework change, Production action or real data.
- No change to any file under `ios/ACEClientApp/ACEClientApp/`. No change to the committed `ACEClientAppUITests.swift` in the delivery checkout.
- The unrestricted `.all` audit remains the only acceptance audit. Arm Y below is diagnostic and never enters a candidate.
- Do not convert any native failure into a pass. Do not filter issues.
- Keep the delivery checkout `/Users/alanrichardson/Developer/sqe-platform-release-layout` untouched. Work in a separate diagnostic worktree.
- Bounded work: report every 15 minutes; hard limit two and a half hours or four native executions, whichever first.

## 2. Read First, Read-Only

Use SSH alias `ace-mac`. Evidence root:

`/Users/alanrichardson/ace-private/mcx19b-orientation-repair-20260915`

Read in this order before writing any code:

1. `08-copy-confirmation-diagnosis/discriminating-diagnostic-result.json` — D1 outcome: A 5 passed, B 5 passed, C1 prerequisite failure, four C repetitions unexecuted.
2. `08-copy-confirmation-diagnosis/native-frame-probe/diagnostic-result.json` — Copy at y 622 before and y 685.67 after a passing unrestricted audit.
3. `11-settings-toggle-diagnosis/copy-failure-52b212a.json` and the run's `batches/001/native.log` lines 560 to 660 — the failed pilot's Copy sequence and the issue at line 641.
4. `12-revision5-discriminating-diagnosis/arm-C/repetition-1/batches/001/native.log` — 16 upward drags at maximum offset; the placement rule was geometrically impossible.
5. `12-revision5-discriminating-diagnosis/arm-A/repetition-1/batches/001/native.log` — the passing isolated baseline, for timing comparison.
6. The D1 patch recorded in the Arm C execution record (`patchSha256` `41a4aa36…`), for the existing `d1IssuePayload`, `frameJSON` and audit-call recording helpers to reuse.

Stop and ask if any of these records are missing or their hashes differ from the D1 result file.

## 3. Fixed Baseline

| Reference | Value |
|---|---|
| Application under test | `52b212aca02190ee0e742debe383fa6016fe36b9`, the failed pilot candidate |
| Views.swift SHA-256 | `3635901a1aa80410bbfeb138a5dafd3b233c2b4b312b8c90ee6fd57a29aa10dd` |
| Committed UI tests SHA-256 | `87fa1c681b2fe70bd04c8cfb938c570f828a1c72bd8702ddc63bb3a0c756766d` |
| Current delivery HEAD | `40bae2640b23eb05496a093d09a4c20186403879`; its app and UI-test hashes equal `52b212a`; its two contract failures are the separate documentation fault and are out of scope here |
| Simulator | iPhone 17, id `2EB0863C-470E-467D-A0C6-CD216DA70C67`, iOS 26.4.1 (23E254a) |
| Case | `pilot.iPhone-17.copyConfirmation.light.large.portrait.0.0.0`: light, large, portrait, Bold Text off, Reduce Motion off, Increase Contrast off |
| Build product | The temporary UI-test method does not exist in any retained test bundle, so the UI-test target must be compiled once from the D2 worktree with the patch applied. Preserve the verified app: record the built app bundle's hash and confirm the app source hashes equal `52b212a` before any execution. The D1 template may not be reused for D2 |
| Execution proof | Every execution's native summary must list `ACEClientAppUITests/testCopyReflowCheck()` as the executed method, with the expected pass or fail. A summary naming any other method, or none, is an incomplete execution |
| Evidence output | `/Users/alanrichardson/ace-private/mcx19b-orientation-repair-20260915/14-copy-reflow-check-20260917/` |

The existing worktree `/Users/alanrichardson/Developer/sqe-platform-r5-diagnostic` holds the D1 patch as an uncommitted modification. Do not build on it in place. Create a new worktree at `52b212a` for D2, or restore the r5 worktree to clean first and record that restoration.

## 4. Written Question

**Does the Copy contrast finding require the Dynamic Type sub-audit to run inside the same audit call?**

Why this question: the audit-induced 63.67-point shift is present in every copy-confirmation run, passing or failing, so it is a constant of the procedure. The colours of the settled control measure 12.34:1 and the same control passed the release-final audit in the failed run. What has never been tested is whether a contrast finding can occur at all when the reflow is absent from the call. Five repetitions per arm in D1 were too few against an observed rate of roughly one failure in ten copy-confirmation audits.

## 5. Design

One temporary UI-test method, `testCopyReflowCheck`, added by patch. Unchanged app. One launch per execution. No Settings helper; default settings only, verified through the existing `observedSettings` read.

**Initial sequence, identical in both arms and identical to the committed procedure.** Using the existing committed helpers unchanged:

1. Launch the `copyConfirmation` scenario exactly as `runCoverageCase` does: orientation, `waitForCoverageState`, `assertRequestedOrientation`, the observed-settings check, and the `initial` viewport capture.
2. Run the committed initial unrestricted audit through `runCoverageAudit(in:scenario:viewport:)` with viewport `initial`, exactly as the committed case does before any scrolling. Its result is recorded as call 0 of the arm. It is the same `.all` call in both arms.
3. `scrollUntilVisible` the `Copy action 1` button, tap it, wait for `Copied Action 1.`, `scrollUntilVisible` the confirmation, assert `isFullyVisible`, then the `copy-confirmation` viewport capture. This is the committed pre-audit state.
4. Call 1 is the arm's audit call on that state, with no added drag or delay, so that call 1 matches the committed procedure's second audit as closely as the arm allows. In arm X, call 1 is the committed procedure exactly.

**Repeated diagnostic calls, 2 to 30, within the same launch.** These are not independent trials. Each call starts from the layout the previous call left, after one re-scroll. Record them as repeated calls and never describe the 30 as a sample of independent runs. Environment variable `ACE_D2_ARM` selects the arm.

For each call n from 2 to 30:

1. One `drag(scrollView, upward: true)` to return to the maximum offset, then `Thread.sleep(0.5)`. Record that this drag and delay are additions not present in the committed procedure.
2. Read and record the Copy button frame and the scroll view frame. Record `ProcessInfo.processInfo.systemUptime`.
3. Call the audit for the arm's type set, with an issue handler that records every issue through the D1 `d1IssuePayload` shape, adds one `XCUIScreen.main.screenshot()` attachment per issue named `D2 <arm> call <n> callback`, and returns `false` so XCTest records the failure natively.
4. Read and record the Copy button frame again. Record uptime and compute duration.
5. Emit one `ACE_D2_CALL` JSON line with arm, call number, pre-frame, post-frame, delta y, duration, issue count and each issue's audit type, label and frame. Emit this line in a `defer` block or equivalent so that it is written even when `performAccessibilityAudit` throws. Wrap the call in `do`/`catch`; on a thrown error, record the error text in the same line, then `XCTFail` with it. A thrown error must never lose the call's frames or the preceding calls' lines.
6. If any issue in this call has label `Copy action` or `Copy action 1` and audit type contrast, emit `ACE_D2_STOP` and end the loop. The native test still fails; that is intended.

Equal frames before and after a call do not show that the layout was still during the call. Record them as settled-state positions only.

Arms, one execution each:

| Arm | Audit call for calls 1 to 30 | Purpose |
|---|---|---|
| X | `performAccessibilityAudit(for: .all, handler)` | Unrestricted, as acceptance uses it |
| Y | `performAccessibilityAudit(for: XCUIAccessibilityAuditType.all.subtracting(.dynamicType), handler)` | Every other type still runs; only the Dynamic Type type is removed. Diagnostic only |

Call 0 is `.all` in both arms, so it can never distinguish the arms. Comparative conclusions in section 6 apply to calls 1 to 30 only. A Copy contrast finding at call 0 in either arm is recorded separately as an initial-audit finding with its arm and frame, is never counted for or against the section 4 question, and does not stop the loop. Record in every result that arm Y is not the acceptance audit and that its pass or fail carries no acceptance meaning.

`ACE_D2_MAX_CALLS` is the number of post-copy calls. The method always makes call 0 and then calls 1 to `ACE_D2_MAX_CALLS`, so an execution produces `ACE_D2_MAX_CALLS` plus one `ACE_D2_CALL` records unless stopped early.

**Harness check, two executions before either arm.**

1. Deliberate native failure: run arm Y with `ACE_D2_FORCE_FAIL=1` and `ACE_D2_MAX_CALLS=2`. After call 2 the method executes `XCTFail("D2 deliberate harness failure")`. The native summary must show `testCopyReflowCheck()` failed with that text, the log must contain exactly three `ACE_D2_CALL` records for calls 0, 1 and 2, and the result bundle and log must be retrieved into the evidence folder. This proves native failure reporting and evidence retrieval, not only logging.
2. Corrected pass: run arm Y with `ACE_D2_FORCE_FAIL` absent and `ACE_D2_MAX_CALLS=2`. The native summary must show the method passed, and exactly three `ACE_D2_CALL` records for calls 0, 1 and 2 must be present.

Harness gate rule:

- The deliberate-failure execution requires native FAIL with the deliberate failure text, exactly three records, and no other failure, finding or thrown error.
- The corrected-pass execution requires native PASS, exactly three records, and no unexpected findings or errors.
- If either harness execution encounters a genuine audit finding, preserve its native result unchanged and classify the finding separately with its call number, audit type, label and frame: a call 0 finding as an initial-audit finding, a call 1 or 2 finding in arm Y as a Y finding for section 6.
- If that finding prevents the required failure or pass demonstration, the harness gate is incomplete. Stop before arm X and arm Y. Report the evidence and the classified finding without calling it a harness defect. A failed native test never satisfies the corrected-pass check, and the finding classification never becomes permission to bypass the gate.

Only after both harness executions are recorded may arm X and arm Y run with `ACE_D2_MAX_CALLS=30`, producing 31 records each unless stopped early.

## 6. Predicted Outcomes And Next Action

Every row records support or contradiction of the section 4 question. No row proves a cause, clears the control's colours, or establishes an Apple defect. Those three remain unresolved after D2 whatever the outcome. D2 ends with the record and a recommendation to the user. It does not restart P0, whose two documentation failures and expired work block are unresolved, and it does not make the discovery pilot ready.

| Outcome | Recordable claim | Next action |
|---|---|---|
| X records at least one Copy contrast finding in calls 1 to 30; Y records none in calls 1 to 30 | Supports a relationship between the finding and the audit types selected in one call. It does not show that Dynamic Type causes the finding, does not clear the colours, and does not identify an Apple defect. Arm C's placement idea remains closed on geometry alone. | Stop. Report with the record. Recommend that the user decide whether the P0 documentation correction and remaining P0 gates proceed with this observation attached, and whether the checker-exception question is put separately. No app change. |
| Y records a Copy contrast finding in calls 1 to 30 | Contradicts a dependence on the Dynamic Type type. The finding occurs without it. `ActionCopyControl` colours, another audit type's interaction, or the checker remain possible. | Stop. Measure the callback crop of the failing call. Report. User decides whether an `ActionCopyControl` change or a documented checker exception is worth pursuing. |
| Any Y call shows a non-zero delta y between its settled pre and post reads | The settled shift has a source other than the Dynamic Type type. The section 4 reasoning is incomplete. | Stop and report with frames. |
| A Copy contrast finding at call 0 in either arm | An initial-audit finding on the unscrolled viewport, which has no retained precedent. It is outside the section 4 comparison because call 0 is `.all` in both arms. | Record separately with arm and frame. Continue the loop. Report it as its own register item. |
| X and Y both record nothing in calls 1 to 30 | Not observed under repeated calls in one launch. Weight moves toward batch length and timing. Nothing is fixed. | Stop. Report. Recommend to the user that the next evidence source is the discovery pilot, once P0 is complete on its own terms. No candidate change. |
| A finding of another audit type on any element, in any arm | Separate register item. Never merged with the contrast outcome. | Record separately; continue the loop. |
| Either harness execution does not show the required failure text, pass state or record count, with no genuine audit finding involved | Harness fault. | Stop after one correction attempt of the patch and report. No further execution under this instruction. |
| A genuine audit finding during a harness execution prevents the required failure or pass demonstration | Harness gate incomplete. Not a harness defect. The finding is classified separately under section 5. | Stop before arm X and arm Y. Report the native result and the classified finding. No further execution under this instruction. |
| An arm cannot complete | Environment or harness fault. | Stop and report. No retry exists in the budget. |

Also record, without treating it as an outcome row: whether X findings coincide with longer call durations, and at which call number a finding occurred. Both are supporting observations only.

## 7. Limits And Stop Conditions

- Exactly four native executions in this order: deliberate native failure, corrected pass, arm X, arm Y. There is no retry. If any execution is lost, stop and report.
- Each execution under fifteen minutes. 30 calls at about nine seconds each is about five minutes after launch.
- Stop an arm at its first Copy contrast finding or at 30 calls.
- Restore simulator boot state after every execution and record it, using the existing restoration records as the template.
- Stop and ask if the baseline hashes differ, if the D1 patch helpers cannot be reused without touching app code, if any attachment contains non-fictional data, or if the simulator cannot be restored.

## 8. Required Records

Under the evidence output folder, for each of the four executions: `execution.json` with candidate hashes, built app bundle hash, arm, xctestrun path and hash, native summary showing `testCopyReflowCheck()` as the executed method, every `ACE_D2_CALL` line parsed, every issue with audit type and frame, any thrown audit error, boot restoration; `native.log`; `result.xcresult`; an `image-inspection.json` for every callback screenshot inspected at original resolution.

One `d2-result.json` at the folder root applying section 6 to the observed results, with the patch SHA-256, the harness check outcomes, the arms' call counts, findings, the recommendation to the user, and the claim limits: no acceptance credit, no pilot credit, arm Y is diagnostic only, calls within one launch are not independent, a non-reproduction is not a fix, cause and colours and any Apple defect remain unresolved, and P0 is not restarted by this record.

Then update the Windows review folder with a compact record only. Raw evidence stays on the Mac.

## 9. Estimate

Estimated 115 minutes of activity: 30 minutes to write and review the patch, 15 minutes to compile the UI-test target and verify the app hash, 20 minutes for the two harness executions, 10 minutes per arm, 30 minutes for records, image inspection and the recommendation. The section 1 hard limit of two and a half hours allows 35 minutes of margin for simulator restoration and evidence retrieval. Blocking input: approval of this file.
