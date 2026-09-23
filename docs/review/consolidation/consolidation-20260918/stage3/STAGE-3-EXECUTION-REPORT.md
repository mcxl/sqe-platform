# SQE Stage 3 Execution Report

**Result:** Approved initial workspace import completed. Full consolidation and application acceptance remain incomplete.
**Recorded:** 2026-09-18T14:57:13.282854+10:00
**Authority:** User replied “Proceed” to the Stage 3 proposal.
**Approved proposal SHA-256:** `e3003ce2da0fc22503b5b3afc8b38c5781526ef97b9d7616b41b685f1cfa9372`.

## Result And Location

Use `LOCAL_HOME\Documents\sqe-platform` for subsequent approved Windows SQE work.
Branch: `codex/sqe-workspace-consolidation`.
HEAD and preserved `main`: `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a`.
All current-task file changes remain unstaged and uncommitted.

Imported 29 files byte-for-byte from Mac commit `40bae2640b23eb05496a093d09a4c20186403879`.
Copied both approved instruction files without changing their bytes.
Added the internal [Workspace Guide](LOCAL_HOME/Documents/sqe-platform/WORKSPACE-GUIDE.md).

There are 31 new task files and one modified tracked file.
The only modified tracked file is `docs/specs/2026-08-24-ace-ios-read-only-client-application.md`.
The five pre-existing untracked files remain unchanged and are not new task outputs.
No commit, push, merge, deployment, app build, simulator test or original-folder deletion occurred.

## Verification

| Check | Result | Record |
|---|---|---|
| SSH, exact source identity, storage and collisions | Passed | `01-preflight.json` |
| Bounded recovery-content review | Passed; not exhaustive security certification | `02-recovery-content-review.json` |
| Deliberately wrong transfer hash | Rejected with exit 1, as required | `03-integrity-fail-pass.json` |
| Same payload with correct hash | Passed with exit 0 | `03-integrity-fail-pass.json` |
| Recovery archive and all 120 members | Hashes and CRC checks passed | `04-recovery-manifest.json` |
| Representative restore of old specification and proposal | Byte-for-byte match | `04-recovery-manifest.json` |
| Mac recovery copy and retrieval | Matching SHA-256 | `05-recovery-remote-receipt.json`, `06-retrieval.json` |
| Mac bundle transfer and native verification | Passed; exact advertised ref and tip | `06-retrieval.json`, `07-git-operations.json` |
| All 29 imported files | Raw SHA-256 and Git blob identities match | `09-import-manifest.json`, `10-windows-verification.json` |
| Both approved instructions | Source and destination hashes match | `09-import-manifest.json`, `10-windows-verification.json` |
| Other 116 original working files | Unchanged, including Python, web, plans and snapshots | `10-windows-verification.json` |
| Original refs, main and existing Git configuration | Unchanged; only authorised additions | `10-windows-verification.json` |
| Git index | Original entries unchanged; nothing staged | `10-windows-verification.json` |
| Imported structured documents | Two JSON, two schemes and one plist parsed | `10-windows-verification.json` |
| Mac delivery candidate | HEAD, refs, status and index unchanged; all 169 tracked files match | `11-mac-verification.json` |
| Complete change-list and specification-diff inspection | Completed by primary session | `12-primary-inspection.json` |
| Report and manifest retrieval | Verified in final handover receipt | `14-handover-receipt.json` |

The integrity fail/pass check validates the transfer verifier only.
It does not substitute for the required application build-and-test evidence gate.
The OpenStep Xcode project file was not validated by Xcode. No runtime acceptance is claimed.

## Recorded Verification Fault

The first final Windows verification command failed on `local_remote_scope_exact`.
The expected value was the private bundle path; Python's generic INI parser retained Git's escaped backslashes.
That produced a textual mismatch despite the correct configured local remote.

`10a-verification-failure.json` preserves the expected and observed values.
The correction used `git config --get` and `--get-all`, which decode Git configuration natively.
The exact URL and sole fetch mapping then matched. One corrective attempt was made.
No application, Git configuration or source correction was needed.
This was a verification-script defect, not an app or transfer defect.

## Recovery And Git Metadata

Windows recovery root:
`LOCAL_HOME\sqe-private\consolidation-20260918\stage3`.

Mac recovery and evidence root:
`LOCAL_HOME/ace-private/sqe-consolidation-20260918/stage3`.

Archive: `destination-before.zip`.
Archive bytes: 2,402,323.
Archive SHA-256: `5ffd08dc8ba8444bf8f62fc7ae3895960187195e215e5e47616f19794ce68b15`.

The archive contains all original destination tracked working files, the five existing untracked snapshot/plan files and config/HEAD/index recovery bytes.
Original committed history remains in the verified Stage 2 Windows bundle on the Mac.
This is targeted destination recovery, not a backup of every older dirty or inaccessible worktree.

New local remote: `mac-consolidation-source`.
URL: `LOCAL_HOME\sqe-private\consolidation-20260918\stage3\mac-delivery-40bae26.bundle`.
Only `refs/heads/codex/mcx19b-release-layout` is mapped to its named remote-tracking ref.
The existing GitHub `origin` remains unchanged.
Git object storage grew by 1,100,368 bytes.
No unrelated-history merge occurred; the Windows branch does not acquire Mac ancestry from this file import.

## Scope And Unfinished Work

Completed in this block:

- Windows foundation and named feature branch established.
- Selected Swift source and local runner imported with exact identities.
- Current iOS specification and local/discovery plans imported.
- Approved Revision 5 and D2 instructions preserved and copied.
- Workspace guide, recovery archive and private evidence records produced.

Still deferred under the approved proposal:

- Dirty-file reconciliation and retirement decisions across the original repositories and worktrees.
- Mac Python approval/provenance/G0 rehydration changes and their associated tests.
- LibreOffice lookup changes and their test.
- Historical CI workflows, provider runner family and remaining reference documents.
- Developer-hub refresh and current development-state reconciliation.
- Operational web readiness and the fictional public showcase.

The old Makefile was excluded because it calls the held historical runner.
No Codemagic configuration or GitHub workflow was imported.
The inaccessible locations and missing worktree registrations remain unresolved and preserved.

The Mac delivery worktree remains `LOCAL_HOME/Developer/sqe-platform-release-layout` at its original candidate.
The Windows import is not an automatically synchronised Mac checkout.
Use an approved, verified transfer before testing any later Windows changes on the Mac.

The iOS Copy finding, historical ancestry decision, pilot/matrix work, signed-device checks and private-service checks remain unchanged.
No imported historical result is represented as acceptance of the consolidation branch.

## Time And Storage

Start: 2026-09-18T14:45:10+10:00.
Report generation: 2026-09-18T14:57:13.282854+10:00.
Elapsed to report: 12.1 minutes, within the 60-minute hard limit.
Active analysis, command execution and waiting were not separately metered.
Application test execution: none.
No persistent process was started by this block.

Windows free space at verification: 10.61 GiB.
Mac free space at verification: 211.73 GiB.
Final retained-output totals and transfer receipts are recorded in the manifests and handover receipt.
The 256 MiB Stage 3 output cap, 2 GiB Windows reserve and 20 GiB Mac reserve remain the limits.

## Next Work

Review the imported state using this report and the Workspace Guide.
The next bounded consolidation block should reconcile the current developer hub and development-state records.
Keep the held Python behaviour decision separate from documentation cleanup.
Select the operational web journey checks after that source choice is explicit.
Continue native iOS diagnosis under its existing exact instructions and candidate controls.
