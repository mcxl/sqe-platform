# SQE Workspace Guide

**Updated:** 18 September 2026
**Audience:** Internal development and review. Do not publish this guide in the public showcase.

## Start Here

Use this Windows folder for consolidation and subsequent approved SQE work:

`LOCAL_HOME\Documents\sqe-platform`

The consolidation branch is `codex/sqe-workspace-consolidation`.
Its starting commit is `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a`.
The original `main` branch remains at that commit.

Stage 3 imports are unstaged and uncommitted. They are not a verified application release.
The current Stage 3 execution report records the final integrity checks and remaining work.

## Application Roles

| Component | Location In This Folder | Current Position |
|---|---|---|
| Python auditor workbench | `src/ace/` | Existing Windows behaviour retained; no new runtime acceptance claimed |
| Next.js relationship-review pilot | `apps/relationship-review-pilot/` | Existing source retained; Convex access and public showcase isolation remain unverified |
| Swift iPhone client | `ios/ACEClientApp/` | Source imported from the fixed Mac candidate; consolidation does not resolve its accessibility failure |
| Local iOS runner | `tools/ace_ios_local.py` | Exact Mac source imported; native execution still belongs on the Mac |

The public showcase is planned work. Do not expose the Python workbench as a public demonstration.
It contains authenticated write routes beyond the proposed read-only journey.
Do not publish private evidence, internal records, signing material or real client information.

## Mac Execution

Connect through the existing SSH host `ace-mac`.

The native delivery workspace remains:

`LOCAL_HOME/Developer/sqe-platform-release-layout`

Its recorded candidate is `40bae2640b23eb05496a093d09a4c20186403879`.
Stage 3 leaves that worktree unchanged.
Windows contains an imported source snapshot; the two working directories are not automatically synchronised.
Do not assume Windows edits appear on the Mac or inherit the Mac candidate's evidence.
Use an approved, hash-verified transfer before testing a changed candidate.

The old Mac Makefile was deliberately excluded from the Windows import.
It calls the held historical runner `tools.run_tests`.
No Codemagic workflow or GitHub CI configuration was imported.
Use the approved local workflow on the Mac; do not start historical provider commands from retained documents.

## Instructions And Evidence

Approved instructions now have byte-identical copies under this folder's `docs/ace/`:

| Instruction | Approved SHA-256 |
|---|---|
| `2026-09-16-ace-ios-swift-completion-instruction.md` | `252aab6ba1115b72f1fcbd84c3d49f3429550c0845d96c2008088d15bdbbe629` |
| `2026-09-17-ace-ios-copy-reflow-check-instruction.md` | `f7147730b09e0b4daf5d18090abc29d38f780962479dc55a49631af20c1f2179` |

Their original files remain in the old Windows SQE folder.
The current iOS specification and local/discovery plans were imported from the fixed Mac commit.
Historical test counts or completion statements in imported documents apply only to their recorded candidates.
They do not establish acceptance of this consolidation branch.

Private consolidation records on the Mac:

`LOCAL_HOME/ace-private/sqe-consolidation-20260918`

- `inventory/`: Stage 1 topology and unfinished-work preservation register.
- `stage2/STAGE-2-COMPARISON-REPORT.md`: complete history/tree comparison and proposed dispositions.
- `stage2/PATH-DISPOSITIONS.md`: recommendations for each differing path.
- `bundles/`: verified committed-history recovery bundles.
- `stage3/`: private recovery and Stage 3 evidence copies.

Private Stage 3 records on Windows:

`LOCAL_HOME\sqe-private\consolidation-20260918\stage3`

The execution report is `STAGE-3-EXECUTION-REPORT.md` in that private folder.
`destination-before.zip` preserves the original destination working files, plans and selected Git metadata.
The recovery manifest records member hashes and representative restoration checks.

Native diagnostic evidence remains at its original private Mac locations.
The inventory and approved diagnostic instructions identify those locations.
No bulk native evidence was copied into this repository.

## Preserved Work And Deferred Decisions

| Location Or Change | Disposition |
|---|---|
| `LOCAL_HOME\Documents\sqe-platform-public-clean` | Preserve modified and untracked work; do not delete or treat as fully integrated |
| `LOCAL_HOME\Documents\agentic-os-workspace\sqe` | Preserve SQE work within the parent monorepo, including original approved instructions |
| Other Windows and Mac worktrees | Preserve at original paths; use the Stage 1 register before any retirement |
| Mac approval and G0 rehydration changes | Held as one behaviour decision; existing Windows Python files remain active |
| Mac LibreOffice lookup changes | Held pending Windows toolchain assessment |
| Historical CI, provider runners and remaining Mac-only documents | Retained in the original Mac repository and bundle; not automatically activated or imported |
| Existing development-state and hub pages | Unchanged historical material; current navigation and status reconciliation remain pending |
| Inaccessible locations and missing worktree registrations | Unresolved; no cleanup or disposal authority |

The local remote `mac-consolidation-source` points to a private verified bundle, not GitHub.
Its path is `LOCAL_HOME\sqe-private\consolidation-20260918\stage3\mac-delivery-40bae26.bundle`.
It exposes only the imported Mac branch through the recorded fetch mapping.
The existing `origin` remote remains unchanged.

## Remaining Delivery Work

The initial file import is separate from complete consolidation and application verification.
Remaining work includes dirty-file reconciliation, developer-hub updates, web readiness and the fictional showcase.
The iOS Copy finding, historical ancestry decision, native coverage, physical checks, signing and private-service checks remain open.
No commit, push, merge, Production deployment or original-folder deletion occurred in this block.

See the accepted consolidation plan and the Stage 3 execution report before choosing the next bounded task.
