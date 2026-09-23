# SQE Stage 2 Comparison Report

**Status:** Stage 2 comparison complete. Baseline recommendation awaits the user's decision.
**Completed:** 2026-09-18T13:07:38.881823+10:00
**Authority:** User approved the Stage 2 execution proposal by replying “proceed”.
**Proposal SHA-256:** `d3b4d79f1425eb9222ef785ca0680061c0a52a65454ac9fe2b93280ced6423c2`.

## Recommendation

Keep `LOCAL_HOME\Documents\sqe-platform` and its Windows `main` history as the consolidation foundation.
Later, import selected Mac files on a new approved feature branch. Preserve both original histories in verified private bundles.
Do not replace the destination with the Mac tree or merge unrelated histories automatically.

This is a recommendation, not a selected baseline or permission to change source.
No consolidation branch, source import, commit, push, build, test or deployment occurred.

## Fixed Sources And Ancestry

| Source | Exact Commit | Imported Comparison Ref |
|---|---|---|
| Windows destination | `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a` | `refs/heads/windows-main` |
| Mac delivery | `40bae2640b23eb05496a093d09a4c20186403879` | `refs/heads/mac-delivery` |

The Mac source remains `LOCAL_HOME/Developer/sqe-platform-release-layout`.
The comparison repository is `LOCAL_HOME/ace-private/sqe-consolidation-20260918/comparison.git`.

`git merge-base --all windows-main mac-delivery` returned exit 1 and no output: no common ancestor exists in these complete selected histories.
`git rev-list --left-right --count windows-main...mac-delivery` returned `152 117`.
Neither result establishes or waives the separate historical iOS ancestry requirement.
The two bundles passed native verification and require no missing prerequisite objects.

## Complete Tree Comparison

| Classification | Files |
|---|---:|
| Identical blob and mode | 93 |
| Mac only | 60 |
| Different on both sides | 16 |
| Windows only | 3 |
| Union | 172 |

Windows has 112 files; Mac has 169.
Git rename detection reported no renames. No shared-path mode changes were found.
All 35 files under `apps/relationship-review-pilot/` have identical blobs and modes.
This proves source equality, not that the web app builds, connects to Convex or is safe for public hosting.

Every differing path has a proposed disposition in [Path Dispositions](PATH-DISPOSITIONS.md).
Every path, including identical paths, has both object identities in [Complete Tree Dispositions](10-complete-tree-dispositions.json).

## Material Decisions

1. **Swift and local verification:** propose preserving the exact Mac iOS tree, local runner and associated tests as a coherent import family.
   Compare dirty variants and dependencies first. Existing evidence belongs to its actual candidate; integrated source needs required verification.
2. **Python approval behaviour:** hold the seven related source/test changes for an explicit coherent decision.
   Mac restricts approved-object construction, tracks issued objects in memory and detects changed content.
   Its persisted rehydration accepts one exact G0 seed fixture, timestamp, author and digest.
   This affects saved-assessment behaviour and is not merely an iOS addition.
   Some relationship/workbench tests inject a provider, so their names alone cannot prove the default persistence path.
   Keep the current Windows files until this family is reviewed and its required behaviour is agreed.
3. **Document exports:** separately reconcile the two LibreOffice lookup changes and their test with the pinned Windows toolchain.
4. **CI and Codemagic:** preserve historical files, but exclude `codemagic.yaml` from the proposed active import.
   It contains automatic push, pull-request and tag triggers despite the newer local-only route.
   Hold GitHub workflows and their runner/config/test family until dependencies and provider assumptions are reconciled.
   No workflow was executed or enabled.
5. **Documentation:** combine platform history with current Swift status. Do not blindly overwrite the long Windows `DEV_STATE.md`.
   Preserve current Mac Copy-action and 836-case requirements, plus historical specification provenance.
   Reconcile instructions against current user authority; historical model-routing wording does not override current instructions.
6. **Windows-only records:** retain the three historical DeepSec result files and original history privately.
   They are excluded from public showcase content. No new scan, deletion or public history push is authorised.

These findings are source comparisons. No new runtime failure, security certification or correction is claimed.

## Transfer And Content Review

Only the selected Windows main and Mac delivery histories were bundled.
No parent-monorepo history, unrelated ref, dirty source or ignored evidence was imported.
Windows bytes streamed directly through SSH; no Windows bundle or scratch pack was written by this task.
No GitHub or cloud transport was used.

The outgoing review covered reachable object inventories, historical paths and all reachable blobs using bounded credential-pattern checks.
Windows: 152 commits, 660 trees and 427 blobs, with 24,524,860 raw object bytes.
Mac: 117 commits, 518 trees and 526 blobs, with 18,689,183 raw object bytes.
All selected blobs decoded as UTF-8. No binary client archives were observed in those selected objects.

The Mac scan found 72 repeated credentialed-URL matches across historical versions of three deliberate rejection/redaction test literals.
Their test contexts were inspected and classified; matched values were not included in records.
The shared `.env.example` contains an empty `NEXT_PUBLIC_CONVEX_URL` setting.
No unresolved candidate prevented this private transfer. This bounded review is not exhaustive security certification or publication approval.
See records 01–06 for exact scope, checks and decisions.

| Bundle | Bytes | SHA-256 |
|---|---:|---|
| `LOCAL_HOME/ace-private/sqe-consolidation-20260918/bundles/windows-main-478a7d8.bundle` | 641,992 | `971b35017becc953fbf4a7922fa0f4463e024af2973cb30795d14ef48615ea98` |
| `LOCAL_HOME/ace-private/sqe-consolidation-20260918/bundles/mac-delivery-40bae26.bundle` | 1,062,189 | `f0e4a471530900ab29248c456f5442f16f9394c68499c84f6588bf936ebc76f7` |

Native `git bundle verify`, advertised refs and isolated fetch results are retained in `08-native-comparison-commands.json`.
The Windows producer/receiver hash agreement is retained in `07-windows-transfer.json`.

## Preservation And Reconciliation

The original repositories and diagnostic worktrees remain in place.
Post-checks match both source HEADs, refs, index entries and working status against the retained pre-existing records.
Index comparisons use Stage 1 entries; a raw pre-stage index-file checksum was not captured.
Seventeen Windows changed/transfer files and thirty Mac diagnostic files retain their Stage 1 SHA-256 values.
Both approved instruction files retain their approved hashes:

- Revision 5: `252aab6ba1115b72f1fcbd84c3d49f3429550c0845d96c2008088d15bdbbe629`.
- D2 fourth draft: `f7147730b09e0b4daf5d18090abc29d38f780962479dc55a49631af20c1f2179`.

The instructions remain untracked in the old Windows `sqe/docs/ace` folder. They are not in either bundle.
Stage 3 must preserve and copy their exact bytes, with hash verification, before relying on destination copies.

`11-unfinished-work-reconciliation.json` links 2,632 Stage 1 Windows entries to canonical comparison paths.
It also records all thirty dirty Mac files; five match current delivery bytes exactly and twenty-five differ.
Matching index objects do not establish matching dirty working files.
No dirty variant was promoted to delivery source.

All 4,339 Stage 1 Windows file/subtree entries retain their preservation status.
Two missing worktree registrations and five inaccessible locations remain open.
Grouped, ignored and inaccessible trees were not exhaustively rehashed.
The bundles cover committed objects only. They are not full recovery copies of unfinished work.
No original folder may be retired or overwritten based on this comparison alone.

## Acceptance Reconciliation

| Stage 2 Deliverable | Result | Evidence |
|---|---|---|
| Fixed source identity and pre/post comparison | Passed, with stated index-check limit | 01, 02, 12, 13 and Stage 1 records |
| Outgoing-history scope and bounded content review | Passed for private transfer | 01–06 |
| Measured capacity and private transfer | Passed | 07–09, 13 |
| Bundle verification and isolated refs | Passed | 08–09 |
| Merge-base determination | Passed: none exists | 08–09 |
| Complete tree comparison and per-path proposals | Passed | 10 and PATH-DISPOSITIONS.md |
| Unfinished-work reconciliation | Passed within Stage 1 inventory limits | 11–13 |
| Baseline recommendation | Delivered; user decision pending | This report |
| Report retrieval and file hashes | Checked in separate retrieval receipt | 15-report-retrieval.json |
| Application or iOS acceptance | Not assessed | No builds or tests in this block |

## Resources And Time

Stage 2 started at 12:52:14 AEST. This report was generated after 15.4 minutes elapsed, within the 60-minute limit.
Before report generation, retained Stage 2 outputs occupied 5.38 MiB against the 2 GiB cap. Mac free space was 207.42 GiB against the 20 GiB reserve.
Final output sizes are in the manifest. Active analysis, command execution and waiting were not independently metered.
There was no application test execution and no paid run.
No persistent process was started for this block.

## Next Work

Review the Windows-foundation recommendation and the path dispositions before Stage 3.
Prepare Stage 3 as a separate bounded proposal, naming exact imports, recovery copies, dirty-file decisions and verification checks.
Keep unresolved Python behaviour and CI activation outside any simple file-copy step.
Preserve the approved instruction bytes and link historical evidence to its original candidate.

The Copy finding, historical iOS ancestry requirement, remaining pilot/matrix work, signing, physical-device checks and private-service checks remain unchanged.
Consolidation does not resolve or waive them.
