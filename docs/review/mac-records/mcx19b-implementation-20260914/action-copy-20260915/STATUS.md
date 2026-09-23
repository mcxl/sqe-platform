# ACE Complete Action Copy Status

Checkpoint: 15 September 2026, 06:29 Sydney.

The approved Copy change is implemented. Overall app acceptance remains incomplete.

## Current Change

Each action has one **Copy action** button. It copies its visible action number, description, owner, target date and status together. Individual field Copy buttons are removed. All displayed fields remain. Confirmation duration remains unchanged.

The clipboard payload uses LF separators and no added trailing LF. Existing local-only and five-minute expiry options remain.

Mac repository: `LOCAL_HOME/Developer/sqe-platform-release-layout`.
Branch: `codex/mcx19b-release-layout`.
Clean local commit: `1b38b90e9a949b7e73965602612c11be6f19e9fc`.
Seven current-task files were committed. No push, merge or phone installation occurred. The separate Windows work remains preserved.

## Focused Verification

| Check | Result |
| --- | --- |
| Native unit and contract suite | 68 passed; zero failed, skipped or expected failures. Includes 43 contract tests. |
| Native complete-action Copy and Paste | One XCTest passed. Action 1, Action 2, then Action 1 each replaced a different clipboard sentinel. All three pasted records matched exactly. |
| Copy images | All 18 captures accounted for; all 17 distinct hashes inspected at full resolution. |
| Source review | Primary inspected the complete diff. Fresh limited Sol review found no material source defect. It binds to the tested hashes. |
| Light release accessibility | Failed after scrolling at ACEClientAppUITests.swift:691. One test failed; no skips. |
| Accessibility images | All 25 captures accounted for; all 10 distinct hashes inspected at full resolution. |

Failing test: `ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls`.

The audit expected no findings. It returned five **Contrast failed** assertions for Release version, its value 1, Action target date, Action status and OPEN. One **Contrast nearly passed** assertion followed the native Copy action lookup.

The native crops show black text on light grey. The Release version crop is clipped at its top. Scroll position changed during the audit. These observations do not establish the audit sampling mechanism or an Apple defect.

The initial audit and later Copy-confirmation audit produced no failure in this run. The whole selected test remains failed. No exception, filter or guessed delay was applied. The Copy change is not an established accessibility correction.

Tests ran before the local commit on the exact committed file hashes. These are focused checks, not the clean final acceptance programme.

## Evidence And Remaining Work

Private Mac evidence:
`LOCAL_HOME/ace-private/mcx19b-implementation-20260914/action-copy-20260915`.

- Copy: `runs/20260914T201002Z-selected-952647e42766`.
- Unit/contract: `runs/20260914T201526Z-selected-8e1eec07c988`.
- Accessibility: `runs/20260914T202103Z-selected-9ee48641147a/FAULT_RECORD.json`.
- Reconciliation: `FINAL_RECONCILIATION.json`.
- Source review: `SOL_CURRENT_SOURCE_REVIEW.json`.
- Commit and exact file list: `COMMIT.json`.

All unsuccessful attempts remain retained: wrong native selectors, stale document records, missing keyboard focus and the wrong native menu element. The retained records distinguish test faults from unresolved application or audit faults.

No native job remains running. Further test batches are paused at the unresolved audit failure. The next diagnosis must identify why the audit reports contrast failures after scrolling before another source correction.

The 22-case pilot and 836-case programme have zero accepted cases. Complete image, physical VoiceOver, clipboard expiry/local-only, signed Keychain, privacy, private-service, server and final review checks remain pending. The historical baseline decision and approved private service inputs remain missing. No automatic merge is permitted.

The iPhone 15 Pro Max remains paired with Developer Mode enabled. Its connection tunnel is unavailable. Reconnect it before installation or physical checks. This change is not on the phone.

The requirement ledger retains all 197 identifiers: 194 pending and three blocked for final acceptance. Passing pending-record tests do not prove runtime behaviour.

Mac free space: 228.46 GiB. Windows free space: 0.78 GiB. Bulk evidence stays on the Mac for at least 30 days. No bulk Windows export or deletion occurred.

This change used about 59 elapsed minutes. Active work and waiting were not separately measured. The passed Copy command used 64.656 seconds for building and 175.113 seconds for test execution. The current unit command used 101.271 seconds for building and 14.149 seconds for test execution. Remaining duration is unknown until the audit fault and pilot are resolved.
