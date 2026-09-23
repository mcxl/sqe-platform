# SQE Stage 3 Execution Proposal

**Date:** 18 September 2026
**Status:** Concrete proposal following the user's instruction to proceed after Stage 2. Execution approval pending.
**Purpose:** Establish the selected Windows workspace without changing Python behaviour or disturbing the Mac delivery candidate.

## Decisions Carried Forward

Use `LOCAL_HOME\Documents\sqe-platform` as the active Windows workspace.
Use Windows commit `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a` as the branch foundation.
Preserve `main`. Create `codex/sqe-workspace-consolidation` from that exact commit.

The user replied “proceed” after the Stage 2 recommendation.
This proposal records the resulting import choices and their limits before execution.
It does not treat that reply as approval to resolve held Python or workflow changes automatically.

The selected Mac source is `40bae2640b23eb05496a093d09a4c20186403879`.
Its original location remains `LOCAL_HOME/Developer/sqe-platform-release-layout`.
The histories have no common ancestor. Use explicit file imports, not an unrelated-history merge.
Keep the historical iOS ancestry decision unresolved.

## Evidence

Stage 2 report on `ace-mac`:

`LOCAL_HOME/ace-private/sqe-consolidation-20260918/stage2/STAGE-2-COMPARISON-REPORT.md`

Report SHA-256:
`73268fb7ed667d3018b835e7806487b4ea738b5858f1c517ba5d1212993774f8`

The same directory contains `10-complete-tree-dispositions.json`, `11-unfinished-work-reconciliation.json` and `MANIFEST.json`.
Stage 1's preservation register remains authoritative for work outside the two compared commits.
The comparison found 93 identical, 60 Mac-only, 16 changed and three Windows-only files.
All 35 Next.js files are identical. Source equality does not establish runtime readiness.

## Exact Source Scope

Import these **29 Mac files** byte-for-byte from the fixed commit:

- All 22 files beneath `ios/ACEClientApp/`, excluding `ios/ACEClientApp/Makefile`.
- `tools/ace_ios_local.py`.
- `tools/tests/test_ace_ios_local.py`.
- `tests/test_ios_accessibility_layout.py`.
- `tests/test_ios_action_targets.py`.
- `docs/plans/2026-09-14-ace-ios-local-verification.md`.
- `docs/plans/2026-09-17-ace-ios-discovery-candidate.md`.
- `docs/specs/2026-08-24-ace-ios-read-only-client-application.md`.

Resolve this list against the fixed tree before writing anything.
Record every path, Git blob, mode, raw SHA-256 and size in the private execution manifest.
The exact tree must produce 29 paths. Stop on any count or identity difference.

The iOS specification is the only existing tracked destination file replaced by this import.
Retain its original bytes in verified recovery storage and its original Git history.
The replacement preserves the Mac's current Copy-action contract, matrix and unresolved acceptance requirements.
It does not approve new product behaviour or change the Swift source.

The Makefile calls `tools.run_tests`, which belongs to the held historical runner family.
Preserve that Makefile in the verified Mac bundle. Do not import an unusable convenience command.
Use the existing Mac delivery workspace for native execution until a separate candidate is verified.

Copy these two approved instructions byte-for-byte from the old Windows `sqe/docs/ace` folder:

| Filename | Approved SHA-256 |
|---|---|
| `2026-09-16-ace-ios-swift-completion-instruction.md` | `252aab6ba1115b72f1fcbd84c3d49f3429550c0845d96c2008088d15bdbbe629` |
| `2026-09-17-ace-ios-copy-reflow-check-instruction.md` | `f7147730b09e0b4daf5d18090abc29d38f780962479dc55a49631af20c1f2179` |

Source root: `LOCAL_HOME\Documents\agentic-os-workspace\sqe\docs\ace`.
Destination root: `LOCAL_HOME\Documents\sqe-platform\docs\ace`.
Keep source copies. Do not normalise line endings or insert notes into approved instructions.

Create `WORKSPACE-GUIDE.md` in the destination.
State application roles, current locations, Mac execution, evidence locations and unresolved imports.
Distinguish an imported source snapshot from the actual verified or failed native candidate.
Include the approved instruction identities and links to the private Stage 2 and Stage 3 records.
This guide is internal. Exclude it from public showcase content.

No other source or documentation edits are permitted by this block.
Keep the main consolidation plan and Fable's Sections 7–10 unchanged.

## Explicit Holds

- Keep every existing Python source and test file unchanged.
- Hold Mac approval, provenance and G0-only rehydration changes as one separate behaviour decision.
- Hold LibreOffice lookup changes and their test until the pinned Windows toolchain is assessed.
- Keep Next.js files, dependency manifests and lockfiles unchanged.
- Import no `.github` workflow, `codemagic.yaml`, historical CI runner or associated CI configuration.
- Leave `AGENTS.md`, `DEV_STATE.md`, `README.md` and existing progress pages unchanged.
- Preserve all other Mac-only documents in their original repository and verified bundle.
- Preserve Windows-only DeepSec records privately. No scan or publication is authorised.
- Preserve all dirty and untracked variants in their original locations.

These are deliberate deferrals, not decisions that older work is disposable or fully integrated.
Developer-hub refresh and the remaining document reconciliation require a later bounded block.
This block therefore completes the initial workspace import, not all consolidation outcomes.

## Storage And Recovery

Use private Windows root:
`LOCAL_HOME\sqe-private\consolidation-20260918\stage3`.

Use private Mac root:
`LOCAL_HOME/ace-private/sqe-consolidation-20260918/stage3`.

Check each path and its parents for links and cloud redirection before creation.
Refuse unexpected existing Stage 3 outputs. Do not overwrite a previous attempt.
C: reported approximately 10.64 GiB free during proposal preparation; recheck before execution.

Cap total Stage 3 working outputs at **256 MiB**, including recovery, transfer and imported Git objects.
Require at least **2 GiB free on C:** after the conservative peak allowance.
Retain at least **20 GiB free on the Mac**.
Measure destination recovery inputs before copying. Stop if their size or safe handling is unknown.
Do not delete files, use G:, or redirect the active repository to make room.

Before repository changes, retain:

1. Exact destination HEAD, branch, refs, remote configuration, index entries and working status.
2. Recoverable Git configuration, HEAD and index bytes, after checking for credentials.
3. All destination tracked working files, with modes and hashes.
4. Exact destination `.snapshots/` and untracked `docs/plans/` contents, including this proposal.
5. The existing verified Windows committed-history bundle and its manifest reference.

Inspect recovery inputs for restricted material before transfer.
Keep recovery copies private. Do not print configuration credentials or private content.
Verify archive members, byte hashes and retrieval before relying on recovery.
Restore representative files into a separate scratch directory and compare them byte-for-byte.
Include the specification being replaced and an untracked planning file in that check.

No original dirty worktree is modified, so its retained location remains its preservation disposition.
The five inaccessible locations and two missing registrations remain unresolved.
This block cannot authorise retirement of those locations or any other original folder.

## Transfer And Import Sequence

1. Check SSH first, then capacity, source identities, refs, status and target collisions.
2. Verify Stage 2 report and bundle hashes against their retained records.
3. Complete recovery and verify representative restoration.
4. Retrieve the Mac bundle privately through SSH into the private Windows Stage 3 root.
5. Compare sender and receiver SHA-256, then run native `git bundle verify`.
6. Add named local remote `mac-consolidation-source`, pointing to that verified local bundle.
7. Fetch only the approved Mac branch into its explicit remote-tracking ref. Leave `origin` unchanged.
8. Create `codex/sqe-workspace-consolidation` from the fixed Windows commit.
9. Export only allowlisted Git blobs through binary-safe writes; preserve exact bytes and modes.
10. Copy the two approved instructions and verify both source and destination hashes.
11. Write the internal workspace guide and preserve an external execution manifest.
12. Compare the complete destination tree and Git metadata against the before-state and allowlist.

Do not use a broad checkout, recursive directory merge, reset, clean or automatic conflict resolution.
Keep imported files unstaged. Leave the destination index content unchanged.
Refuse a pre-existing remote or branch unless its exact purpose and identity match this recorded attempt.
Stop on destination changes by another process. Preserve completed work for review.

## Verification And Acceptance

First prove the transfer verifier rejects a deliberately mismatched expected hash on a tiny scratch payload.
Correct the expected hash and verify the same payload passes. Retain both records.
This checks copy integrity only; it is not the application's build-and-test evidence gate.

Require all of the following:

- Native bundle verification succeeds, with the advertised Mac tip unchanged.
- The 29 imported files match the fixed Mac blobs and raw hashes.
- Both instruction hashes match their approved values at both Windows locations.
- The original specification can be restored from retained recovery bytes.
- All unchanged destination tracked files retain their original raw hashes.
- `.snapshots/` and existing plan files retain their original hashes.
- Python, Next.js, dependencies and existing instructions remain unchanged.
- The only new files are the 28 additive Mac files, two instructions and workspace guide.
- The only modified tracked file is the named iOS specification.
- `main`, existing refs, `origin`, index entries and the Mac delivery worktree remain unchanged.
- Only the named branch, local remote and fetched tracking ref are added.
- The report reconciles every scoped deliverable and every held item.
- The final report and manifests are retrievable and their hashes verify.

Run no app builds, simulator tests, full suites or external reviews in this file-import block.
Parse imported JSON and XML/plist documents without executing their contents.
Inspect the complete change list and specification diff before reporting the import complete.
No runtime acceptance can be inferred from these integrity checks.

## Time, Limits And Authority

**Planning allowance:** 20–40 minutes if preflight, transfer and recovery checks pass.
This is an operating estimate for under-one-MiB selected source, not an established runtime duration.
Unknown recovery, access and collision resolution are excluded from the estimate.
**Hard limit:** 60 elapsed minutes from the first approved execution command, including waiting.

Potentially costly commands are recovery enumeration/copy, bundle verification, fetch and hash verification.
No dependency installation, simulator launch, CI run, paid service or native build is permitted.
Stop at the time or storage limit, unexpected source changes, restricted material or missing evidence.
Stop after two failed corrective attempts for the same fault.
Do not expand the import or alter application code to make checks pass.

Execution approval covers this exact scope, private recovery, named Git metadata changes and allowlisted file writes.
It does not authorise commits, pushes, merges, original-folder deletion, Production, Python behaviour changes or iOS acceptance exceptions.

After approval, proceed through all in-scope steps without asking again.
Report completed work, active processes, failed checks and remaining decisions at any required stop.
