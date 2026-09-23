# Codex Instruction: ACE iOS Read-Only Client — Swift Completion Route (Revision 5)

Date: 16 September 2026, revised 22:30 Sydney after the Codex review of Revision 4.
Status: Draft For Human Approval. Supersedes Revisions 1 to 4 of the same date in full.
Author: Fable, from the Codex handover of 20:42, `FABLE-STATE-EVIDENCE-20260916.json`, read-only inspection of the Mac checkout and retained evidence between 20:45 and 21:05 Sydney, and the trial report `UNDERSTAND-ANYTHING-TRIAL-20260916.md`.

Changes from Revision 4, each from the Codex review of 22:15: Fact 4 no longer says the colours are not the problem; the issue-handler screenshot is described only as the screen observed when the callback ran, and it is removed from arm A so the baseline test stays unchanged; the D1 outcome table separates contrast findings from other audit findings and preserves any B or C failure when A passes; and repository record edits move ahead of the final freeze so that F1 cannot create a new head.

Changes from Revision 3, each from the Codex review of 21:55: the issue-handler screenshot is now described as callback-time evidence, not sample-time; D1 outcomes are worded as support or contradiction of a hypothesis, never proof; a non-reproduction no longer triggers a test change; split audits are diagnostic only and cannot replace the unrestricted acceptance audit; the discovery runner is reviewed and committed before the candidate is frozen; completion criteria name the 836-case programme, the physical and service checks, and Pocock before final verification; and section 6 now carries one push rule.

**Authority.** This instruction authorises nothing until the user approves this exact file together with the discovery-mode runner change. Once approved, it permits normal task commits and pushes to `codex/mcx19b-release-layout` only, under the Commit And Push Controls in `AGENTS.md`. It never permits a merge, a purchase, a Codemagic run, a framework change, a Production action or real data.

## 1. Corrections To Revision 1

Revision 1 was written from `DEV_STATE.md` and the 12 September MCX19B records. Those are stale. The handover is right on every point it raised:

| Revision 1 said | Actual state |
|---|---|
| Candidate `7dc7cee` on `codex/mcx-19-live-evidence-harness` | Current work is `52b212aca02190ee0e742debe383fa6016fe36b9` on `codex/mcx19b-release-layout` on the Mac. PR 6 and Windows are stale at `7dc7cee`. |
| Copy scope needs a written amendment and implementation | Already decided on 15 September and implemented. One `Copy action` button per action. Payload is five LF lines. Recorded in the Mac plan of 14 September. |
| 65 unit tests, 136 native commands | 68 unit and contract tests at `a84f670`. The 136-command gate belongs to the abandoned Codemagic route. |
| 192 Codemagic build minutes | Codemagic is rejected. All execution is local on the Mac. |
| "Every application gate has passed; remaining work is evidence only" | False. One native accessibility finding on `Copy action` has no proved cause, and a real scroll-clipping layout defect was found and corrected at `15e4363`. |
| Open item register from 12 September | Replaced by section 4. |

## 2. Fixed Baseline

| Reference | Value |
|---|---|
| Mac checkout | `/Users/alanrichardson/Developer/sqe-platform-release-layout` |
| Branch / HEAD | `codex/mcx19b-release-layout` / `52b212aca02190ee0e742debe383fa6016fe36b9`, clean |
| Views.swift SHA-256 | `3635901a1aa80410bbfeb138a5dafd3b233c2b4b312b8c90ee6fd57a29aa10dd` |
| UI tests SHA-256 | `87fa1c681b2fe70bd04c8cfb938c570f828a1c72bd8702ddc63bb3a0c756766d` |
| Controlling plan | `docs/plans/2026-09-14-ace-ios-local-verification.md` on the Mac |
| Evidence root | `/Users/alanrichardson/ace-private/mcx19b-orientation-repair-20260915` |
| Latest failed pilot | `11-settings-toggle-diagnosis/complete-pilot-runs/20260915T133932Z-pilot-497a5a280dc6` |
| Toolchain | Xcode 26.4.1 (17E202), macOS 26.6.2, iOS Simulator 26.4.1 |
| Coverage decision | 836 unique cases: 512 audited, 324 layout-only. 22-case pilot first. |
| Physical device | iPhone 15 Pro Max. Signing profile recorded as expiring 21 September 2026 12:37 AEST. |

Stop if HEAD, either source hash, or the evidence root differ. Record what was found and ask.

## 2A. Reference Material And Its Standing

| Material | Location | Standing |
|---|---|---|
| Mac local verification plan of 14 September | `docs/plans/2026-09-14-ace-ios-local-verification.md` | Controlling record for coverage, copy design and final gates. This instruction does not override it. |
| Codex handover of 16 September | `MCX19B-FABLE-REVIEW/FABLE-HANDOVER-CURRENT-20260916.md` and the companion JSON | Factual state at 20:35 Sydney. Verified by Fable against the Mac. |
| Understand Anything code map and explanations | `MCX19B-FABLE-REVIEW/ACE-IOS-CODE-MAP-20260916.json`, `ACE-IOS-CODE-EXPLANATIONS-20260916.md`, `ACE-IOS-CODE-MAP-REVIEW-20260916.md` | Navigation aid only. Snapshot of `52b212a` runtime files. Excludes the UI tests, so it cannot describe the failure mechanism. Not an acceptance gate. Do not integrate the tool into SQE, its lockfile, hooks or CI under this instruction. |
| Retained diagnostic records under `08-copy-confirmation-diagnosis/` | Mac evidence root | Primary evidence for section 3. Read before D1. |

When the map and the source disagree, the source is right. When a summary and a retained run disagree, the run is right.

## 3. What The Retained Evidence Shows About The Copy Finding

Fable read these records on the Mac without changing anything. The facts below are from the records themselves, not from the handover summary.

**Fact 1. The application did not change between a passing and a failing run.** `git diff 15e4363 52b212a` touches only `ACEClientAppUITests.swift`. `Views.swift` has the same hash in the passing prefix record and the failed pilot. The five commits between them change scrolling helpers, screenshot capture, target-size precision and Settings toggling.

**Fact 2. The same sequence produced both outcomes.** Both runs drag the release ScrollView about three seconds before tapping `Copy action 1`, wait for `Copied Action 1.`, capture, then call the unrestricted audit. The passing prefix at `15e4363` recorded nine audit invocations and exit 0. The failed pilot at `52b212a` recorded the contrast issue on the same case. Codex's own record at `08-copy-confirmation-diagnosis/native-uninstrumented-prefix-probe/diagnostic-result.json` concludes the failure is intermittent.

**Fact 3. The unrestricted audit itself moves the layout.** `native-frame-probe/diagnostic-result.json` shows `copyAction` at y 622 before the audit and y 685.67 after it, a 63.67-point shift, in a passing run. `video-inspection.json` describes the audit period frame by frame: "text visibly smaller", then "text grows", then "larger text places Copy below the viewport". The failing callback frame in both the 15 September failure record and the 52b212a failure is y 685.67. That is the post-shift position.

**Fact 4. One retained rendering measured adequate contrast.** The retained crop measures black on `#c6c6cb` at 12.34:1 in one settled rendering. It does not show what the checker sampled, and it does not show that every rendering had adequate contrast. The failing element is the `Copy action` static text inside a `.bordered` button with `.tint(.primary)` on a `secondarySystemBackground` card inside a `.clipped()` ScrollView.

**Working hypothesis, not a conclusion.** `performAccessibilityAudit(for: .all)` runs the Dynamic Type audit, which rescales text and reflows the release screen while the contrast audit samples pixels. When the reflow pushes the Copy button to the clipped bottom edge of the ScrollView at sample time, the sampled region mixes button, card and clipped background and the contrast check fails. Whether it fails depends on the exact scroll offset left by the drag, which explains intermittency on identical code. This is consistent with every retained record. It is not proved, and the handover is right that a later pass cannot prove the cause of an earlier failure.

What this hypothesis rules in and out:

- It predicts the same finding can appear on any bordered control near the bottom of a scrolled viewport. The historical six Copy contrast findings on the no-conclusion screen, when there were eleven per-field buttons, fit this.
- It predicts a contrast-only audit on a settled screen passes every time.
- It predicts the finding disappears when the button sits in the upper half of the viewport before the audit, with no change to colours.
- If those predictions fail, the hypothesis is wrong and the app or the checker is back under suspicion.

## 4. Open Item Register

| ID | Item | Class | Evidence | Stage |
|---|---|---|---|---|
| C1 | `Copy action` contrast finding, intermittent, cause unproved | Unresolved | Section 3 | D1 |
| C2 | Historical no-conclusion, light post-scroll and max-text post-scroll contrast findings from the per-field era | Unresolved, may share C1's mechanism | Mac plan, Historical Diagnostics | D1 then P1 |
| C3 | Bold Text toggle tap missed once at `c0e5373`; recovery added; mechanism unknown | Test harness | `af8c82d`, `52b212a` | P1 |
| C4 | Historical timeouts: noActions -56, release-final, Settings snapshot | Test harness or environment, separate faults | Mac plan | P1, observe only |
| C5 | Baseline ancestry gap: `6b0160be` has no common ancestor with the imported harness history | Acceptance blocker, needs user decision | Mac plan | User |
| C6 | PR 6 head is older than the Mac work | Repository | Handover | F1 |
| C7 | Windows `DEV_STATE.md` and Mac `DEV_STATE.md` both stale | Records | Handover | F1 |
| C8 | Signing profile expiry 21 September, not revalidated | Environment | Mac plan | Before P2 |
| C9 | Preview server, certificate, fictional account unverified | User input | Mac plan | Before P2 |
| C10 | Physical VoiceOver, eight journeys | Device access | Mac plan | P2 |
| C11 | Video from the failed pilot retained but not fully inspected | Evidence | Handover | D1 |
| C12 | Understand Anything viewer still running as long-run job `1789556825253-ua-sqe-trial-123f6a9e` on the Windows computer | Housekeeping | Trial report | F1, or earlier at user request |
| C13 | Trial tool installed with Node 26.2.0 and pnpm 11.19.0 against a manifest that specifies pnpm 10.6.2 | Environment, out of scope | Trial report | None. Record only. |

Add to this register only with a run path, test name, source line, expected and actual text.

## 5. Stages

Sequence: **Understand → Specify → Test → Build → Verify → Freeze → Review → Release.** Each stage has an exit gate.

### D1 — Discriminating Diagnostic For The Copy Finding

No application change. No runner change. One temporary UI-test variant, kept outside the candidate as a patch under `08-copy-confirmation-diagnosis/`, reviewed by the primary before execution, with a deliberate-failure check retained.

Written question: **Does the Copy contrast finding depend on the audit's own layout reflow rather than on the control's colours?**

Three arms, each the single `copyConfirmation` case on iPhone 17, light, default text, portrait, toggles off, on the unchanged `52b212a` application:

| Arm | One changed variable | Repetitions | Predicted if hypothesis true | Predicted if false |
|---|---|---|---|---|
| A. Baseline | None. Current test as committed. | 5 | At least one contrast failure across five | Same |
| B. Split audits | Replace the single `.all` call with sequential calls: `.contrast` alone, then each other audit type alone, in a fixed order, on the same settled screen. All types still run. | 5 | Contrast arm passes 5 of 5; the Dynamic Type arm may report layout findings of its own | Contrast still fails intermittently |
| C. Upper-viewport placement | Keep `.all`. Before the audit, scroll so the Copy button's frame bottom is above 50 percent of the ScrollView height, then verify two frame reads 0.5 s apart are identical. | 5 | Passes 5 of 5 | Still fails |

Arms B and C are diagnostic procedures. Neither is an acceptance procedure. The controlling plan requires the unrestricted audit before acceptance, and nothing in D1 changes that. Every audit type still runs in arm B, but a pass in arm B is not a pass of the acceptance audit.

Arm A runs the committed test unchanged. No instrumentation is added to it, because any addition would change the baseline being measured.

In arms B and C only, take `XCUIScreen.main.screenshot()` inside the audit issue handler when an issue fires and attach it. Describe it in every record as the screen observed when the callback ran. It is not the rendering Apple measured, and one still image cannot establish whether the layout was moving. Record its timestamp against the audit start. Complete the C11 video inspection from the failed pilot in the same stage, because the video is the only continuous record across the sampling window.

**What the arms can and cannot establish.** Five repetitions are a small sample of an intermittent fault. A pass in five is consistent with the hypothesis and does not prove it. A failure in any arm is stronger evidence than a pass in any arm. No outcome proves a cause. The retained 12.34:1 crop shows adequate contrast in one settled rendering. It does not show that every rendering the checker sampled had adequate contrast.

**Failure classification.** Every audit finding in any arm is recorded with its audit type, element label, frame and repetition. For the outcome table, "B fails on contrast" means the `.contrast` audit alone reported a finding on a settled screen. "B fails on another type" means the `.contrast` audit passed and a different audit type reported a finding. The two are separate outcomes and are never merged. Any finding in any arm is preserved in the record with its classification, whatever the outcome row.

Outcome table. Each row names the next action and the claim that may be recorded:

| Outcome | Recordable claim | Next action |
|---|---|---|
| A fails at least once; B and C pass 5 of 5 | The hypothesis is supported. The finding was not observed when the audit ran on a settled screen or with the control placed higher. | Go to P0. The permitted harness change is arm C's placement and settle check only, because it keeps the unrestricted audit. Arm B's split procedure is not carried into the candidate. No app change. |
| A fails; B passes; C fails | The hypothesis is partly supported. Placement did not remove the finding; separating audit types did. | Stop. Report with all images and the video inspection. The user decides whether a further diagnostic is worth running. No candidate change. |
| A fails; B fails on contrast | The hypothesis is contradicted. A contrast finding reproduces with a contrast-only audit on a settled screen. The app control or the checker is under suspicion. | Stop. Report the callback screens with a measured contrast of the failing rendering. The user decides between an app change limited to `ActionCopyControl` colours or style, and a documented checker-defect exception under the controlling plan's rule. |
| A fails; B fails on another type only | The contrast hypothesis is not contradicted. A separate finding of another audit type exists and is a new register item. | Stop. Report both findings separately. The user decides whether to proceed to P0 with the new item open. |
| A passes 5 of 5; B and C pass 5 of 5 | The finding was not observed in fifteen executions. Nothing is fixed. Nothing is changed. | Go to P0 on the committed test without any harness change. Record the non-observation. Discovery mode in P1 will show whether it recurs across 22 cases. |
| A passes 5 of 5; B or C fails | Not a non-reproduction. A finding was observed under a diagnostic procedure and is preserved with its classification. | Stop. Report the finding with its arm, audit type and images. The user decides the next step. No candidate change. |
| Any arm cannot complete | Environment or harness fault. | Stop after two attempts. Report. |

Limits: 15 native executions, each under six minutes. Stop after two failed corrective attempts on the diagnostic harness itself. Restore simulator settings and boot state after each arm. Retain every result bundle.

Exit gate: the outcome table has been applied and the outcome written to `08-copy-confirmation-diagnosis/discriminating-diagnostic-result.json` with candidate, arm, repetition results, every finding with its audit type, hashes, the callback screens from arms B and C, and the video inspection record.

### P0 — Runner Change, Then Freeze The Pilot Candidate

Order matters. The discovery-mode runner is part of the candidate. It is reviewed, tested and committed before the freeze so that P1 runs on the frozen HEAD and does not create a second candidate.

1. Implement discovery mode in the local runner, as defined in P1. Add runner tests for: a failed case stays failed; later cases still run; the pilot stops on lost evidence, unrestorable simulator or failed app launch; the acceptance-mode path is unchanged.
2. Apply the permitted harness change from D1 to the UI tests, if the D1 outcome table permitted one. Otherwise no UI test change.
2A. Prepare every repository record edit that the final candidate must carry, so that no later commit is needed on the candidate: the Mac `DEV_STATE.md`, the progress guide, the closed Expo and Bolt route with its reason, and the specification cross-references. Write them to describe the candidate and its planned verification, not results that do not yet exist. Results from P1 onward are retained outside the candidate under the evidence root and referenced by run path and hash.
3. Primary inspects the complete diff of steps 1, 2 and 2A. Fresh Sol review. Focused native check of any changed UI-test procedure on one case.
4. Commit on `codex/mcx19b-release-layout`. Record HEAD and source hashes. This is the pilot candidate.
5. Run the 68 unit and contract tests and the runner tests on that HEAD. Do not reuse the `a84f670` result for changed files.

Exit gate: clean HEAD containing the runner change; unit, contract and runner tests passed on that HEAD; Sol `ship`.

### P1 — 22-Case Pilot In Discovery Mode

Run the 22 cases from the Mac plan on the frozen HEAD.

**Discovery mode, defined.** Each case runs to completion independently. A failed case stays failed in the record. The runner does not stop the pilot at the first failure. It does stop when evidence retrieval fails, when a simulator cannot be restored, or when a case cannot launch the app. It changes no assertion, filters no finding, and uses the unrestricted audit exactly as acceptance mode does. It was reviewed and committed in P0.

Why discovery mode: the stop-at-first-failure policy has hidden 17 of 22 outcomes on every pilot since 12 September. The next decision needs the full outcome set more than it needs the first failure.

Discovery output is not acceptance. Acceptance requires zero failed and zero skipped cases on one unchanged candidate, which is the existing rule.

Exit gate: 22 case records with pass or fail, each with images and audit results. A classified list of every failure by the section 3 method: app, harness or environment.

### P2 — Correct, Then Accept

1. For each P1 failure, apply the Standard Operating Procedure: exact assertion, expected versus actual, image, classification. Harness faults are fixed before any app change.
2. Any app change goes through P0 again. A changed candidate invalidates the earlier pilot.
3. Run the 22 cases in acceptance mode on the final candidate. Require 22 of 22.
4. Only then run the complete 836-case programme on the same unchanged candidate, in the Mac plan's group order: Standard, Text sweep, Difficult layouts, Individual settings, Combined settings. Apply the plan's space, time and image-inspection rules. Do not reduce the case count.

Exit gate: 22 of 22 accepted, then 836 of 836 accepted, both on one unchanged candidate, with every image inspected under the plan's deduplication rule.

### P3 — Physical Device And Service

Prerequisites from the user: C8 renewed if needed, C9 supplied, iPhone 15 Pro Max available.

1. Signed development build on the approved Mac. Install on the iPhone.
2. Eight VoiceOver journeys, screen-recorded with captions.
3. Clipboard on device: local-only, five-minute expiry, absent from Universal Clipboard on a paired Mac.
4. App-switcher privacy cover, sign-out Keychain deletion, 403 sign-out path against the approved Preview server.
5. Settings combinations the simulator could not apply.

### F1 — Records, Review, Release Decision

The controlling plan's final gates apply in its order: focused checks, freeze, Pocock review, pilot and programme, primary inspection, fresh Sol, reconciliation, signed install, then merge approval. Pocock review therefore happens on the frozen candidate before the P2 programme is treated as final verification. If Pocock requires a change, the candidate is refrozen and P2 repeats.

**No commit on the candidate after the freeze.** Repository records were written in P0 step 2A. Everything produced after the freeze, including pilot results, programme results, device results, review records and the reconciliation, is retained under the evidence root and in the Windows review folder, and is referenced from the pull request description. If a record inside the repository must change after the freeze, that is a new candidate, and the controlling plan's renewal of gates 2 to 8 applies.

1. Update the Windows `DEV_STATE.md` copy and the Windows review folder from the retained results. These are outside the Mac candidate.
2. Decide C5 with the user. Options are: accept the blob-matched import as the baseline with a written waiver, or reconstruct ancestry from the original Windows repository. Do not infer. C5 may stay pending through D1, P0, P1 and P2, which are simulator work. It blocks final acceptance and merge.
3. Bring PR 6 to the accepted head by a normal push to the feature branch, or open one PR on the current branch and close 6. User decides which. Either is a push to the feature branch under the section 6 rule; neither is a merge.
4. One Greptile and a fresh Sol on the exact frozen head, after Pocock.
5. Reconcile every requirement as passed, failed, pending or blocked.
6. Merge only on separate exact-head approval.
7. Stop the retained viewer job (C12). Keep the two saved map files in the review folder. Remove the trial scratch folder only if the user asks.

TestFlight and App Store are outside this instruction.

## 6. Bounded Work Controls

- Local Mac execution only. No Codemagic. No paid service.
- D1 hard limit: 15 native executions or four hours, whichever first. P1: one pilot run plus one rerun if evidence retrieval fails. Report every 15 minutes.
- Stop after two failed corrective attempts on one fault. Different validation failures are different faults.
- No app file other than `Views.swift` `ActionCopyControl` may change, and only after the D1 decision table permits it.
- No further tooling trials, code-map regeneration or benchmark work under this instruction. Codex may read the saved map to locate code. It may not cite the map as evidence of behaviour.
- No change to authentication, Keychain, API contract, clipboard rules, security boundaries, displayed values or the 836-case decision.
- Never convert a failed native result to a pass. Never filter audit issues. Sequential audit types in arm B still run every type.
- Retain raw evidence on the Mac for 30 days. Windows receives compact records only.
- Restore simulator settings and boot state after every run. Record it.
- **One push rule.** Approval of this file permits normal task commits and pushes to `codex/mcx19b-release-layout` only, as the controlling plan already expects. Stage only current-task files. Verify the staged list and `upstream..HEAD` before every push. No force push. No push to any other branch. No merge under this instruction.
- Any harness change carried into a candidate must keep the unrestricted audit for acceptance. A split or restricted audit is diagnostic only and never enters the candidate's acceptance path.
- A non-reproduction is not a reason to change the candidate. Change the candidate only when a retained failure identifies the defect, or when the D1 outcome table names the change.

## 7. Stop Conditions

Stop and ask when: the baseline differs; D1 lands on any Stop row of its outcome table; a correction needs a file outside the permitted set; any evidence retrieval fails; a machine or simulator cannot be restored; a result-bundle attachment contains non-fictional data; C5 needs a decision; the signing profile has expired; scope needs expansion.

## 8. Completion Criteria

This instruction is complete only when all of the following hold on one unchanged candidate:

1. D1 has a written outcome against its outcome table with retained evidence.
2. Unit, contract and runner tests passed on the frozen HEAD.
3. Pocock review passed on the frozen HEAD before final verification.
4. 22 of 22 pilot cases accepted in acceptance mode with the unrestricted audit.
5. 836 of 836 programme cases accepted, images inspected under the plan's rule.
6. Physical device checks on the iPhone 15 Pro Max: eight VoiceOver journeys, clipboard behaviour, privacy cover, Keychain deletion, Settings combinations the simulator could not apply.
7. Service checks against the approved Preview server with the approved certificate and fictional account.
8. C5 decided and recorded.
9. Greptile once and fresh Sol on the exact head after Pocock.
10. Every register item in section 4 closed or carrying a recorded reason it cannot close.
11. Both `DEV_STATE.md` copies and the progress guide match the records.
12. Nothing is presented as verified that was not observed.

Partial completion is reported as partial, with the unmet items listed.

## 9. Estimate

| Stage | Executions | Elapsed | Blocking input |
|---|---|---|---|
| D1 | 15 native cases | 3 to 4 hours | User approval of this file and the runner change |
| P0 | Runner tests, 1 focused case, unit suite | 3 hours | Sol availability |
| P1 | 22 cases | 2 hours run, 2 hours review | P0 exit gate |
| P2 | 22 cases, then 836 | 1 day plus programme time | Depends on P1 failures |
| P3 | Device | 1 to 2 days | C8, C9, iPhone |
| F1 | None | 4 hours | C5 decision, reviewer availability |

The D1 estimate is the only one with confidence. Everything after depends on what P1 reveals. No completion date is offered.
