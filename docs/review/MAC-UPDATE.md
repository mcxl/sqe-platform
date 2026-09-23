# Mac Evidence Update — 23 September 2026

This update supersedes earlier statements that current Mac access and the final D2 outcome were not inspected. Those statements remain in dated source records for transparency.

## Connection And Source

The saved numeric SSH address was stale. Resolving the Mac hostname found its current address. Login succeeded against the original pinned ED25519 host key. The saved connection now uses the hostname, with strict host-key checking retained.

Mac HEAD is `40bae2640b23eb05496a093d09a4c20186403879`; the delivery worktree is clean. All 24 present Windows iOS/runner files checked against the Mac match byte-for-byte. The historical iOS Makefile remains intentionally absent from the root snapshot.

[The Mac source manifest](MAC-SOURCE-MANIFEST.json) accounts for every tracked file at this candidate. Identical source resolves to the repository root; substantive Mac-only or differing files are retained under `mac-variants/`. Environment files are excluded. These variants are reference material, not accepted changes to Windows behaviour. Nested historical workflows are not active GitHub workflows.

## Retained Diagnostic Findings

| Record | Exact Outcome | Interpretation |
|---|---|---|
| [D1](mac-evidence/08-copy-confirmation-diagnosis/discriminating-diagnostic-result.json) | 10 successful diagnostic cases; C1 failed its placement prerequisite; C2–C5 not run | No correction established; no acceptance credit |
| [D2, 17 September](mac-evidence/14-copy-reflow-check-20260917/d2-result.json) | XCTest failed to initialise while loading Accessibility; zero audit calls | Environment/test-service startup failure; the Copy hypothesis was not tested |
| [Fresh-simulator recovery, 18 September](mac-evidence/15-fresh-simulator-recovery-20260918/ACE-IOS-FRESH-SIM-RESULT-20260918.md) | Test entered; call 1 reported Copy contrast; native exit 65 | A genuine native finding prevented the deliberate-failure gate; X/Y comparison was not completed |

For the September 18 run, test `ACEClientAppUITests/testCopyReflowCheck()` failed at diagnostic `ACEClientAppUITests.swift:94` with `Contrast failed`. Expected: calls 0, 1 and 2, then only the deliberate failure. Actual: calls 0 and 1; Copy contrast stopped the sequence before that assertion.

Call 1 excluded Dynamic Type. The Copy frame moved downward by approximately 63.67 points. Call 0 had remained unrestricted, so carry-over effects are not excluded. This evidence does not prove an Apple defect, clear all renderings, or establish a root cause. The recorded CPU competition is an observation, not a causal finding.

The [native log](mac-evidence/15-fresh-simulator-recovery-20260918/native.log), [native test summary](mac-evidence/15-fresh-simulator-recovery-20260918/native-summary.json), [review record](mac-evidence/15-fresh-simulator-recovery-20260918/review.json), [diagnostic method](mac-evidence/14-copy-reflow-check-20260917/D2-method.swift) and [patch](mac-evidence/14-copy-reflow-check-20260917/D2-test.patch) are included. The temporary diagnostic code is not part of the delivery app or its acceptance test suite.

## Limits

Forty-five retained diagnostic records were retrieved and verified by SHA-256 before export. Public copies remove personal home-directory prefixes. Their original and export hashes are recorded in EXPORT-MANIFEST.json.

Raw result bundles, screenshots and recordings remain on the Mac. No continuous video inspection or new image inspection was performed during this retrieval. Other historical dirty worktrees are not automatically covered by the clean delivery-worktree check.

No app source change, build, simulator run, signing renewal, service check or acceptance result followed from restoring SSH. Copy, pilot completion, full coverage and the remaining physical/service/ancestry gates remain unresolved.

## Expanded Access Audit

The later [master update](../../MASTER_UPDATE.md) expands the original 45-record selection to 6,328 available text records, using hash-based duplicate links. It adds 25 worktree records and latest-failure PNGs/video. Earlier statements above describe the first retrieval. Most raw bundles and historical media remain local, and Vorflux execution access is unverified.
