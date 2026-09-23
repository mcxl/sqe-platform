# SQE Stage 1 Inventory Result

**Recorded:** 2026-09-18T12:37:33.764963+10:00
**Result:** Bounded inventory delivered, with explicit access and coverage gaps. No consolidation, history import or baseline selection performed.

## Authority And Boundaries

The user approved Stage 1 with a 60-minute cap and 100 MiB of records. After C: fell below reserve, the user approved storing records on the Mac. The original 13:22:09 AEST hard stop was retained. Source repositories stayed in place.

No repository edits, commits, pushes, branch switches, source copies, deletions, builds or tests were performed. Git used GIT_OPTIONAL_LOCKS=0. Only private inventory records were created; no Windows output writes continued after the reserve stop.

## Findings

| Item | Result |
|---|---|
| Windows worktree registrations | 45: 36 SQE-relevant or mixed-history, 9 unrelated |
| Missing Windows registrations | 2; registrations retained, not pruned |
| Mac worktrees | 25 |
| Mac unfinished work | 30 modified files in 20 diagnostic worktrees |
| Windows file/subtree metadata records | 4339; this is not a recursive file total |
| Windows tracked modifications in SQE scope | 15: public-clean 6, old SQE 7, historical simulator probe 2 |
| Instruction hashes | Revision 5 and D2 both match their approved exact bytes |
| Mac delivery | Clean at initial capture; HEAD remains 40bae2640b23eb05496a093d09a4c20186403879 |
| Baseline decision | Pending Stage 2 Windows/Mac tree comparison |

Windows index variants contain 128 paths with identical index blobs across locations, 53 paths with different historical index versions, and 70 paths observed in one index location. These are not semantic merge conflicts. Working changes have separate hashes. No Mac-versus-Windows tree comparison was performed.

## Coverage And Limitations

All registered Windows worktrees received existence and dirty-status checks. Missing paths have no dirty count. Untracked directories are grouped by Git status; counts are not individual-file totals. Eight initially uncertain worktrees were classified as mixed-history SQE-relevant using their last committed path metadata; unrelated contents were not recursively inspected.

Five directory-access gaps remain in the old SQE tree: three permission-denied test-output folders and two overlong retained xcresult paths. Exact Git warnings and commands are retained in 08-file-inventory-commands.json and 02-worktrees.json.

Generated, ignored, private, binary and retained-evidence subtrees remain in their original locations. Many were represented by a directory record without recursive enumeration or size. This is not proof of a complete recovery copy or permission to delete them. A per-item integration/publication decision remains pending.

No bundled history or raw source content was transferred. Hashes and Git index object identities do not establish that a later recovery copy is complete. Stage 2 must preserve staged, unstaged and untracked work separately, and retain detached worktree heads.

Missing registered locations:

- `LOCAL_HOME/AppData/Local/Temp/ace-ios-spec-pocock-17c7e71a` — gitdir file points to non-existent location
- `LOCAL_HOME/AppData/Local/Temp/sqe-phase6b1-preview-ac5f9f6` — gitdir file points to non-existent location

## Storage And Timing

Windows C: was 10.73 GiB free at the first Stage 1 check, then fell below 2 GiB. The local inventory save was rejected before any JSON record was written. A small collector script and storage-probe text file remain in the original Windows inventory folder. No cleanup was performed. The cause of C: consumption was not investigated.

Total elapsed since the original start: 15.4 minutes, including the storage interruption and user response. Active reasoning and waiting were not separately instrumented; no exact split is claimed. Test execution time was zero. Captured Git command durations are recorded; overlapping durations must not be added as wall time.

Inventory output has a 100 MiB cap. Mac writes enforce a 20 GiB reserve. All new evidence is under:

```text
LOCAL_HOME/ace-private/sqe-consolidation-20260918/inventory
```

Windows Git storage observations: destination pack storage 295,907 KiB; public-clean loose/pack storage 3,997/467 KiB; monorepo loose/pack storage 584,804/303,699 KiB, plus 668,105 KiB reported as garbage. These are observations, not bundle-size estimates or deletion candidates. Full recovery and temporary space still need sizing.

## Record Index

- `01-repository-metadata.json`: Windows roots, branches, remotes, refs, object storage and worktree registrations.
- `14-final-worktree-classification.json`: authoritative Windows topology classification; earlier 02/06 classifications are intermediate.
- `19-preservation-register.json`: authoritative Windows file/subtree classification; earlier 07/15 records are intermediate.
- `16-windows-index-variants.json`: historical Windows index identities, without integration decisions.
- `04-mac-metadata.json`, `05-mac-unfinished-files.json`, `11-mac-delivery-files.json`: Mac delivery and diagnostic records.
- `18-windows-preservation-recheck.json`, `20-mac-preservation-recheck.json`: final source-identity checks.
- `21-stage1-summary.json`: bounded-stage totals and limits.
- `MANIFEST.json`: SHA-256 and size for retained files; excludes itself.

## Next Bounded Work

Stage 2 requires its own proposal. Its first deliverables are measured storage, a reviewed outgoing-history scope, private verified bundles, and comparison of Windows 478a7d8cd9c97d0bc43bd4d41ea460d589d4003a with Mac 40bae2640b23eb05496a093d09a4c20186403879 in an isolated repository. Use Mac storage for bulky outputs while Windows remains below reserve.

Do not select a baseline or create the consolidation branch before reviewing the tree comparison. Keep the five access gaps and two missing registrations open. Do not retire any source folder until required recovery evidence exists.
