# SQE Workspace Consolidation And Public Web Showcase

**Date:** 18 September 2026  
**Status:** Revision 4 — storage updated after the user's cleanup. Not implementation approval.  
**File:** `LOCAL_HOME\Documents\sqe-platform\docs\plans\2026-09-18-sqe-consolidation-web-showcase-plan.md`  
**Standing:** Sections 1–6 contain the current proposed plan. Sections 7–9 retain Fable's historical reviews unchanged.  
**Revision:** Retains Revision 3's controls and design. Records recovered C: capacity and makes relocation conditional on measured requirements.

The review findings are accepted as design corrections. They do not establish completed migration, testing or publication.

## 1. Outcomes And Boundaries

Establish one active Windows workspace:

`LOCAL_HOME\Documents\sqe-platform`

Deliver three separately assessed outcomes:

1. **Consolidation:** existing work is preserved, reconciled and clearly located.
2. **Web readiness:** a defined auditor workflow is verified on the selected revision.
3. **Public showcase:** visitors can explore a guided, read-only fictional demonstration.

Continue the Swift iOS application separately. The showcase does not replace the operational web application or establish iOS acceptance.

Retain these boundaries:

- Fictional demonstration data only.
- No public uploads, edits, sign-in or approval actions.
- No Expo, Bolt or Codemagic.
- No automatic merge or Production deployment.
- No deletion of original folders.
- No application-wide redesign or new backend service.
- No public API, database schema or shared domain-contract changes.
- No EVE installation, agent-runtime migration, new dependency or tooling trial.

EVE is deferred. A future product assistant requires a separate purpose, scope and measured pilot.
It is not required for consolidation, the fictional showcase or the unresolved native accessibility diagnosis.

This revision authorises no execution, commit, push, deletion or deployment by itself.
Existing iOS approvals remain limited to their original instructions and candidates.

## 2. Verified Starting Position

The inspected Mac delivery repository contains:

| Component | Current Role |
|---|---|
| Python application | Auditor workbench, domain behaviour and client-release service |
| Next.js application | Relationship-review pilot using Convex |
| Swift application | Read-only iOS client |

The recorded Mac delivery commit is:

`40bae2640b23eb05496a093d09a4c20186403879`

Its delivery worktree was clean when inspected.

The recorded destination `main` commit is `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a`. It must be preserved.

The Mac commit was absent from all three Windows repositories when checked. Their ancestry remains unverified.
Neither commit is the selected consolidation baseline. Recheck both repository states before dependent work.

| Location | Role And Preservation Requirement |
|---|---|
| `LOCAL_HOME\Documents\sqe-platform` | Destination and independent source of tracked web, Python and iOS-specification work; preserve `main`, `.snapshots/` and uncommitted plan material |
| `LOCAL_HOME\Documents\sqe-platform-public-clean` | Separate SQE repository; recorded branch `codex/mcx-19-live-evidence-harness`; preserve modified and untracked work |
| `LOCAL_HOME\Documents\agentic-os-workspace\sqe` | SQE subdirectory of the parent monorepo; contains approved instructions and unfinished work |
| `LOCAL_HOME\Documents\agentic-os-workspace` | Actual Git root for the preceding row; enumerate its linked worktrees without absorbing unrelated projects |
| `LOCAL_HOME/Developer/sqe-platform-release-layout` on `ace-mac` | Native delivery repository; recorded branch `codex/mcx19b-release-layout`; source, builds and bulk evidence remain on the Mac |

Fable recorded 343 dirty entries and 45 linked worktrees in the parent monorepo.
The public-clean repository also owns a worktree within the old SQE `.artifacts` directory.
These are historical inventory inputs, not a complete or current reconciliation.

C: was rechecked on **18 September 2026 at 12:13 AEST**, after the user reported deleting files.
G: and T: retain the earlier observations. Values are observations, not reserved capacity.

| Drive | Observed Free Space | Observed Type | Decision |
|---|---|---|---|
| C: | Approximately 16.18 GiB | Local Windows SSD | Above the 2 GiB reserve; measure each stage's peak requirement before writing |
| G: | Approximately 0.92 GiB | Volume labelled `Google Drive` | Reject as private local working storage |
| T: | Approximately 1280 GiB | Network share `\\192.168.86.114\Files` | Not a local Windows disk; capacity does not prove suitability |

The pasted review's G: capacity differs from Section 9 and the direct check.
Use the direct observation above for planning. Recheck before execution.
No verified alternative local Windows volume has been selected.

The C: checks agreed to within 61,440 bytes:

- `Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"`: 17,369,899,008 bytes free.
- `Get-PSDrive -Name C`: 17,369,837,568 bytes free.

The previous below-reserve blocker is cleared at this observation.
Approximately 14.18 GiB remains above the reserve before stage requirements and concurrent use are deducted.
This does not establish that all bundles, recovery copies, dependencies and builds will fit.
The user performed the cleanup; this task deleted no files and has not audited what was removed.

Windows' Documents known folder resolves to `LOCAL_HOME\OneDrive - AuditCo\Documents`.
The repositories instead reside beneath the literal path `LOCAL_HOME\Documents`.
That directory and the destination repository showed no reparse-point attributes in the direct check.
They are outside the registered OneDrive roots, including `LOCAL_HOME\OneDrive`.
This establishes the observed OneDrive distinction, not the absence of every possible third-party synchronisation tool.
Recheck each chosen scratch path and its parents before use. Avoid the redirected Documents shortcut.

Other Windows locations contain modified source, tests, documents, untracked files and linked worktrees. These cannot be treated as disposable copies.

The existing Next.js relationship-review component directly calls Convex queries. A disconnected showcase therefore requires a deliberate separation between presentation and data loading.

The existing developer hub contains obsolete status statements, historical commits and local file links. It is an internal document, not public showcase content.

The iOS Copy accessibility finding remains unresolved. Consolidation and showcase work must not change that status.

## 3. Consolidation And Web Readiness

### Preserve And Reconcile

**Storage gate, before block one:** measure free space and the proposed block's peak additional use.
Allow for inventory outputs, temporary files and concurrent disk use. Require at least 2 GiB remaining afterwards.
Do not start when the allowance is unknown or exceeds available capacity.
Recheck before each disk-writing stage and stop affected work if the reserve is breached.
Do not delete existing work or prune worktrees to satisfy this gate.
The user's completed space recovery is recorded in Section 2.
Any further agent-performed recovery or relocation requires a separate, explicit disposition.

**Updated storage decision:** keep the requested active Windows repository location unchanged.
Stage 0 should assess C: first for compact inventory records and the isolated comparison repository.
Relocation is no longer required solely because of the earlier low-space observation.
Choose exact private paths outside source and sync folders, then verify capacity before creation.
If measured requirements exceed C: capacity, assess private Mac-local storage for bulk comparison, recovery and evidence.
Candidate root: `LOCAL_HOME/ace-private/sqe-consolidation-20260918` on `ace-mac`.
Stage 0 must resolve its existing parent, filesystem, available capacity, access and synchronisation status.
The candidate path is not yet created or approved for use.
Do not infer its backing storage from T:'s advertised capacity.

If that Mac location qualifies, propose comparison and bundle work there through SSH.
This changes the earlier Windows-comparison proposal; record the chosen host before approving Stage 2.
Keep any transfer automated and private. Windows remains the control and review interface.
If Mac storage fails verification, propose a verified local external volume or explicit C: recovery.
Do not silently substitute Google Drive, T:, a junction or a moved Windows repository.
Windows consolidation requires sufficient capacity for its measured peak use, rather than another automatic cleanup requirement.

Use two inventory levels:

1. Enumerate repository and worktree topology across all named sources.
2. Inspect file contents and preservation needs in SQE-relevant locations only.

Record each worktree's path, branch, HEAD, dirty count and relevance.
Classify relevance as SQE, unrelated or unknown. Keep inaccessible paths and unknown relevance unresolved.
Do not run recursive content scans across unrelated monorepo projects.
Preserve unrelated dirty work in place. A prunable label is not deletion permission.

For SQE-relevant locations:

- Record repository roots, remotes, branches, commits and outstanding changes.
- Inventory tracked, untracked, ignored and linked-worktree content.
- Record inaccessible paths explicitly.
- Classify files as identical, unique, conflicting, generated or excluded.
- Record each item's destination or preserved original location.
- Preserve recoverable Git history and unfinished changes outside public source.

Include destination `main`, staged changes, ignored files, nested repositories and `.snapshots/` in the register.
Record staged and unstaged changes separately. Do not assume a Git bundle preserves uncommitted files.
Later recovery copies must retain exact untracked bytes and both forms of tracked changes.
Check hashes and recovery accessibility before relying on those copies.
Keep the register and any private file listings outside public source.

Do not recursively merge directories or overwrite conflicting files.

Keep private documents, credentials, evidence, screenshots, result bundles and recovery material outside tracked source. Preserve required material in its current private location and record references.

Do not copy dependency caches or bulk Mac evidence.

### Compare Histories Before Selecting A Baseline

After inventory, measure bundle and isolated comparison-repository storage on both machines.
Include simultaneous bundle, Git objects, unpacking, checkout and recovery-copy requirements.
Record the method, measured sizes and conservative temporary allowance. Do not assume a bare repository is small.
Require the 2 GiB Windows reserve after peak use. Preserve any stricter existing Mac evidence-storage requirement.

Use the existing SSH connection to transfer a private Git bundle of the recorded Mac branch.
Record its advertised refs, exact tip and SHA-256 on both machines.
Check the outgoing history for credentials or restricted content before transfer.
Stop affected transfer if such content is found; do not rewrite history under this plan.
Do not push Mac history to GitHub for comparison.

Verify the bundle with `git bundle verify` in an isolated comparison repository on the selected host.
If comparison runs on the Mac, transfer a verified Windows committed-history bundle there using SSH.
Create temporary outputs directly on verified storage; avoid a C: staging copy.
If the available transfer method requires C: scratch space, pause until that allowance is established.
If the bundle needs prerequisites, record them and verify availability before import.
Import the two histories into separate named refs in that repository.
Keep the comparison repository outside active source folders and cloud-synchronised folders.
Record its exact path and capacity before creation.

Compare the complete trees of:

- Windows: `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a`.
- Mac: `40bae2640b23eb05496a093d09a4c20186403879`.

Record the merge base, or record that no merge base exists.
Classify identical, Windows-only, Mac-only and conflicting paths, including deletions and renamed files.
Record a disposition for every difference. Preserve pending decisions as blockers to baseline selection.
Do not silently favour the Mac tree or discard destination-only files.

Present the comparison and proposed baseline for review before branch creation.
If histories are unrelated, propose an explicit integration method. Do not automatically merge unrelated histories.
This consolidation decision does not resolve the separate historical iOS ancestry requirement.

### Establish The Active Workspace

Preserve the destination's existing `main` branch.

After the baseline and dispositions are agreed, import the verified history through a named local remote.
Record the remote's local path and fetched refs. Leave the existing GitHub remote unchanged.
Create the consolidation branch from the agreed baseline:

`codex/sqe-workspace-consolidation`

Do not assume the Mac commit is the starting point.
If either source advances, record the difference and revisit affected comparisons before integration.
Protect destination untracked files before checkout; stop rather than overwrite a colliding path.

Copy the approved instructions byte-for-byte from:

`LOCAL_HOME\Documents\agentic-os-workspace\sqe\docs\ace`

to:

`LOCAL_HOME\Documents\sqe-platform\docs\ace`

| Instruction Filename | Approved SHA-256 Of Exact File Bytes |
|---|---|
| `2026-09-16-ace-ios-swift-completion-instruction.md` | `252aab6ba1115b72f1fcbd84c3d49f3429550c0845d96c2008088d15bdbbe629` |
| `2026-09-17-ace-ios-copy-reflow-check-instruction.md` | `f7147730b09e0b4daf5d18090abc29d38f780962479dc55a49631af20c1f2179` |

Authority is the user's explicit Revision 5 and D2 fourth-draft approval in this conversation.
The hashes identify the approved bytes; they do not independently confer authority.
Both source hashes were verified on 18 September 2026. Recheck before and after copying.
Retain `Get-FileHash -Algorithm SHA256 -LiteralPath <full-path>` commands and outputs for both locations.
Do not normalise line endings or insert approval notes into those files.

Preserve Windows-only source changes separately. They require reconciliation before integration. A preserved change is not an incorporated change.

Keep the original Windows folders and linked worktrees intact.

Create a concise workspace guide covering:

- The active Windows folder.
- The role of each application component.
- The Mac build location.
- Private evidence locations.
- Unintegrated changes and their recovery locations.

Update current developer-hub navigation and status. Preserve historical records and approved instruction wording.

### Verify One Existing Web Journey

Assess the operational web application independently from the showcase.

Use the selected revision and one isolated fictional dataset for this **Python workbench** journey:

| Step | Application And Route | Evidence |
|---|---|---|
| Open an Engagement | Python: `/workbench/engagement/summary` | Expected fictional engagement and summary |
| Open an Evidence Item | Python: `/workbench/evidence/{evidence_id}/review` | Matching evidence, version and review state |
| View relationships and gaps | Python: `/workbench/relationship-reviews/{relationship_id}` | Matching relationship, gap and decision state |

Use the existing evidence-review and relationship-review test setup to create the isolated dataset.
Record the startup command, temporary database path, fixture identifiers and selected revision.
Check route and fixture compatibility against that revision before execution.
Use no live workbench database.

This readiness journey covers viewing existing records. Adjacent PUT and POST endpoints do not expand it into write-workflow testing.
Use existing domain tests for fixture validation below. Record any additional operational write testing as separately scoped work.

Assess the live Next.js/Convex pilot separately.
Its live check stays **Blocked** until an authorised, reachable Convex configuration is verified.
Fixture-based showcase success cannot satisfy that live-service check.

Use existing startup procedures and tests. Record unavailable configuration or services as blockers.

Report each capability as:

- Verified on the selected revision.
- Implemented but not verified.
- Demonstrated with fixtures.
- Blocked.
- Planned only.

Do not infer complete web readiness from route definitions, historical test results or an attractive interface.

## 4. Public Showcase Implementation

### First Demonstration

Present one coherent fictional Engagement with two paths:

**Supported path:** evidence supports a relationship, a recorded example auditor decision references the correct version, and an example released result follows.

**Blocked path:** a material evidence gap or contradiction prevents progression to a substantive conclusion.

The visitor can navigate, select records and read explanations. Decisions are recorded examples, not actions performed by the visitor.

Show the relationship between the auditor workflow and the iOS client. Label iOS material as a development preview with outstanding verification.

Use a diagram and labelled prose for the iOS explanation.
Do not publish retained diagnostic screenshots. Any later publication image requires fictional content and a separate content check.

### Technical Approach

Use the existing Next.js application and installed dependencies.

Separate presentational components from their Convex data-loading container. Supply bundled fictional records to the showcase presentation.

Preserve the existing live pilot behaviour. Do not introduce a general-purpose data framework or shared-package restructuring.

Use a dedicated showcase route and an explicit showcase deployment configuration. The deployment must:

- Open the guided demonstration from its landing page.
- Serve only the approved public experience.
- Require no private Python or Convex service connection.
- Contain no private-service credentials.
- Expose no write functionality.

**Stage 5 mechanism:** propose a build-time `SQE_SHOWCASE_BUILD=1` mode within the existing Next.js application.
In that mode, `/` redirects to `/showcase`, which imports only fictional presentation and JSON data.
Select the root's live-pilot implementation at build time; exclude it from the showcase's emitted route and client bundles.
Keep the ordinary build's live-pilot behaviour unchanged. Do not add a second committed Next.js application root.
Do not treat this proposed flag as an existing Next.js route-exclusion feature.
An environment-variable check or redirect alone does not prove exclusion.

The smallest pilot must inspect emitted routes, dependencies and browser requests to prove the proposed exclusion works.
Test the showcase with Convex unset and with an inert, non-private sentinel URL configured.
Both must reach the fictional landing page without mounting the provider or contacting the sentinel.
Check direct URLs and error paths. Do not ship a reachable pilot configuration-alert page as the showcase.
If build-time selection cannot exclude the live pilot using the installed toolchain, stop this pilot.
Present the exact failed evidence and a bounded alternative before changing architecture or dependencies.
No feasibility claim is made until that build and inspection pass.

Store the showcase's fictional records in versioned JSON, consumed by the presentation.
Add a focused pytest that loads those same JSON records.
Validate supported and blocked scenarios through existing Python approval, relationship and client-release behaviour.
Check decision outcomes, exact version references and displayed released values.
Use isolated test storage and existing test helpers. Do not duplicate domain rules in TypeScript.
Approval-gate checks alone do not establish relationship approval or release correctness.

Use these existing modules, confirmed at the recorded destination revision:

| Behaviour | Module And Entry Point | Existing Test Reference |
|---|---|---|
| MATE approval | `src/ace/engine/approval.py`: `build_approved_assessment`, `evaluate_approved_assessment` | `tests/test_approval_gate.py` |
| Accepted planning trace and relationship decisions | `src/ace/engine/tracing.py`: `build_accepted_planning_trace` | `tests/test_planning_trace.py`; workbench-facing checks in `tests/test_relationship_review.py` |
| Released record shapes and values | `src/ace/domain/release.py`: release models | `tests/test_client_release*.py` |
| Release lifecycle and current published result | `src/ace/workbench/client_release_service.py`: `ClientReleaseService` | `tests/test_client_release*.py` |

These paths are relative to the selected repository root.
Recheck their interfaces after baseline reconciliation. Report changed interfaces before adapting the fixture test.
Test supported, blocked and mismatched-version inputs; compare the displayed JSON release with the service result.
Do not assume that exercising the tracing module alone verifies the workbench routes or release lifecycle.

Keep analytics, visitor accounts, uploads and contact-form processing out of the first version.

### Public Content

Display a persistent "Fictional, read-only demonstration" notice.

Distinguish verified capabilities, illustrative examples and planned functionality. Do not publish internal development instructions, evidence paths, issue discussions or obsolete status claims.

Use synthetic organisations and records. Do not imply client endorsement or permission to publish client material.

Provide a short presentation script and a recording as a fallback for live demonstrations.

### Hosting And Publication

Prepare the showcase locally before selecting the exact remote target.

Recorded Vercel account: team **mcxl**, slug **mcxl1**.

| Existing Project | Recorded Association | Standing |
|---|---|---|
| `relationship-review-pilot` | Existing pilot project | Inspection candidate only |
| `project-rr85r` | Linked to GitHub `mcxl/sqe-platform` | Inspection candidate only |

These account details were checked by Codex and were not independently checked by Fable.
Neither project is approved as the showcase target. Recheck current settings before selection.

Inspect both projects without changing their configuration. Record:

- Linked repository and Production branch.
- Root directory, build command, output and runtime requirements.
- Environment-variable names, target environments and inheritance; never values.
- Deployment protection and signed-out access.
- Automatic Preview creation on push.
- Public route list, existing users and recovery procedure.

Assess `NEXT_PUBLIC_CONVEX_URL` inheritance explicitly.
Prefer a showcase configuration with this variable unset and no Convex provider mounted.
An inherited variable is acceptable only with evidence that the showcase ignores it and cannot reach live pilot routes.
Variable absence alone is insufficient; inspect built routes and runtime requests.
Check deep links, reloads and error paths as well as the landing page.

Do not reuse a target that exposes private routes or depends on private-service configuration.
Public route isolation must be demonstrated before selecting a deployment target.
If the existing application cannot provide it within scope, stop hosting work and present the required change.

If a suitable isolated target cannot be established within existing authority, finish the local build and report the specific hosting decision required.

Record the exact Preview target and deployment method before requesting publication approval.
Check automatic deployment behaviour before any later feature-branch push.
Push or deployment is not authorised by this planning document.
Once authorised, verify the provider reports **Preview**, then test the exact link while signed out.
Do not assume a Preview URL is publicly accessible.
Share only the verified fictional showcase, with the approved access setting.

Production deployment, custom domains, paid services and merging remain outside this plan.

## 5. Verification, Delivery And Work Controls

### Small Pilot Before Expansion

First implement one fictional relationship-detail page with navigation and a blocked-state example.

Prove:

- A minimal build succeeds.
- One deliberate test failure produces retrievable diagnostic evidence.
- The corrected test passes.
- The page works without private-service configuration.
- Existing relationship-review tests still pass where affected.
- The JSON fixture passes the existing Python domain rules.
- Only approved showcase routes are reachable in the proposed deployment configuration.

Reuse valid existing checks when their conditions remain unchanged.
Record the exact command, exit code, revision or hashes, environment and retained evidence for each reused check.
Keep the deliberate failure in temporary test work; remove it before the candidate is frozen.
Do not treat fixture assertions as runtime proof of the operational web application.

Expand to the complete guided story only after this pilot passes.

### Final Checks

| Area | Required Evidence |
|---|---|
| Preservation | Inventory reconciles every item to a destination, original location or explicit blocker |
| Git history | Tree comparison, merge-base result, baseline decision and verified recovery material; original branches remain available |
| Instructions | Revision 5 and D2 approval hashes match |
| Web behaviour | Selected auditor journey has revision-specific results |
| Fixture rules | The same JSON used by the showcase passes approval, relationship and release checks |
| Showcase | Every step, record link, direct URL, reload and browser-history action works |
| Accessibility | Keyboard operation, focus, zoom, mobile layout and relevant automated results are inspected |
| Isolation | Built routes and browser requests show no operational endpoints, private-service connections or write operations |
| Public content | Generated pages and assets contain no restricted records, credentials or internal evidence links |
| Regression | Affected existing web checks pass; unrelated historical failures remain explicitly recorded |
| iOS continuity | Mac HEAD and worktree state checked before and after; native source, tests and service contracts unchanged |
| Deployment | Exact Preview identity, public-access result and recovery procedure are recorded |

A screenshot does not establish functionality. A retry does not establish a correction. An unrelated failure must not silently disappear or automatically invalidate independent work.

### Deliverables

- One active Windows workspace with a component map.
- A complete migration and reconciliation register.
- A web-readiness assessment tied to the selected revision.
- A guided fictional showcase and presentation script.
- A recording of the verified fictional story for presentation fallback.
- A verified Preview, or an explicit publication blocker.
- An iOS continuation record with its unchanged candidate and outstanding work.
- A release record identifying source revision, fixture version and verification results.

Keep technical documentation in approved repository locations. Keep logs, screenshots, handovers and private recovery records outside tracked source.

Before execution, record exact private locations for inventory, comparison, recovery and verification records.
Do not put these records in public showcase assets or a GitHub push.
Reconcile every deliverable as passed, failed, pending or blocked before handover.
An inventory completed within its time limit is not completed consolidation.

### Time And Stop Rules

Use these stages with bounded execution scopes. One approval may cover several explicitly defined stages.
Reuse existing explicit authority where it covers the exact scope; do not request duplicate approval.

| Stage | Allowed Work | Exit Evidence |
|---|---|---|
| 0 — Storage decision | Read-only host, capacity, path and synchronisation checks | Named suitable location, relocation recommendation and measured allowance, or a specific access/storage blocker |
| 1 — Inventory | Repository/worktree metadata and SQE file classification only | Scoped inventory, inaccessible items, unknown relevance and remainder |
| 2 — Comparison | Private recovery, bundle transfer and isolated history/tree comparison | Verified bundle, full difference register and proposed baseline |
| 3 — Consolidation | Agreed dispositions, branch creation, exact instruction copies and workspace guide | Preservation reconciliation, hashes and one active Windows entry point |
| 4 — Web readiness | The three Python viewing steps with isolated fictional data | Revision-specific results; separate live Convex status |
| 5 — Showcase pilot | One fixture detail, navigation and blocked example | Minimal build, failure/pass evidence, domain and isolation checks |
| 6 — Complete showcase | Remaining approved story, accessibility checks, script and recording | Complete local acceptance record |
| 7 — Preview | Separately authorised target and deployment | Exact Preview, signed-out checks and recovery record |

**Stage 1 has a 60-minute hard limit.** This is a cap, not a completion estimate.
It permits no branch switching, imports, recovery copying, application changes, pruning or deletion.
Writing compact private inventory records is permitted once storage is verified.
Do not begin stage 2 because time remains in stage 1.

### Stage 0 Execution Proposal

**Objective:** choose where inventory, bundles, comparison and recovery records can safely reside.
**Scope:** read-only Windows and SSH checks of the named locations; no repository changes or transfers.
**Planning estimate:** 10–20 minutes if SSH and filesystem metadata respond normally; recovery work is excluded.
**Hard limit:** 20 minutes. Stop earlier if required access is unavailable.
**Cost limits:** no recursive inventory, clone, bundle creation, build, install, scan or test run.

Check Windows known-folder redirection and the candidate paths' actual backing storage.
Check Mac-local path resolution, available space, private access and known sync roots.
Distinguish local storage on the Mac from a Windows network-drive mapping.
Record a conservative allowance for Stage 1's compact metadata outputs.
Defer bulk Stage 2 sizing until inventory provides the required sizes.

The result must name the selected host and absolute paths for inventory, bundles, comparison and recovery.
It must state whether the location passed, failed or remains unknown, with supporting command output.
It must state which later stages can proceed and which still require C: capacity.
If no location qualifies, return the specific recovery or volume decision required.
Do not call storage resolved merely because a drive reports free space.

Return the proposal in this conversation. Persist execution records only after their storage location passes and is authorised.
This planning revision does not itself start Stage 0 or approve the proposed relocation.

Later execution proposals must state acceptance checks, allowed files, estimate, hard limit and exclusions.
Base estimates on measured inventory and pilot results. Unknown access or configuration work remains unestimated.
Identify storage-heavy bundle operations, dependency installation, builds, recordings and complete tests before approval.
Install nothing during inventory. Do not add dependencies to make the showcase easier.

Record elapsed, active and waiting time separately. Give progress at least every 15 minutes during execution.
Stop at the hard limit or after two failed corrective attempts for one fault.
Retrieve exact errors and relevant evidence before correction. A running process is not a failed command.
Stop application changes when an architecture, security, schema or public-interface change would be required.

Stop affected work for insufficient storage, inaccessible required files, unexplained conflicts, missing authority or a binding limit. Preserve completed work and report the exact remainder.

Do not add testing frameworks, dependencies, tooling trials or infrastructure merely to complete consolidation.

Follow applicable repository review and commit controls for any later implementation.
Do not describe historical reviews as reviews of the new candidate.

### Current Open Decisions And Evidence

| Item | Current Status | Blocks |
|---|---|---|
| Storage allowance and suitable private locations | C: rechecked at 16.18 GiB; below-reserve blocker cleared; exact paths and stage allowances pending | Stage 1 outputs need a measured allowance; bulk stages need peak sizing; relocation only if required |
| Windows/Mac tree comparison and ancestry | Not performed; Mac object absent locally at last check | Baseline selection and consolidation |
| Per-file integration dispositions | Pending inventory and comparison | Stage 3 |
| Instruction copies | Source hashes verified historically; copies pending | Consolidation acceptance |
| Hosting suitability and exact target | Inspection pending; no target selected | Preview deployment |
| Showcase build-time exclusion | Mechanism proposed; emitted bundles and routes not yet verified | Showcase pilot acceptance and publication |
| Fixture module mapping | Modules named and inspected; selected-baseline tests pending | Showcase pilot acceptance |
| Live Convex access | No verified configuration in this plan | Live Next.js readiness only |
| iOS Copy finding, historical ancestry and device/service verification | Unresolved or pending under the separate iOS instructions | iOS acceptance; not an independent fictional showcase |

Do not assume a historically recorded signing profile remains valid for current device work.
Check signing validity and device access when native work resumes under its own instructions.

## 6. Fable Review Focus

Fable should assess:

1. Whether the reconciliation procedure protects all unique work and Git history.
2. Whether the selected baseline preserves the web platform as well as iOS.
3. Whether the showcase separation prevents accidental private-service use.
4. Whether the fictional journey accurately represents approval and release rules.
5. Whether the operational web application and showcase have distinct acceptance criteria.
6. Whether verification is sufficient without repeating the previous testing loop.
7. Whether publication boundaries and unresolved decisions are explicit.
8. Whether another implementer can execute each bounded stage without making unrecorded scope decisions.

For this revision, Fable should specifically check:

- Whether the main plan resolves every F1–F7 and R1–R5 correction, including R1b.
- Whether storage and worktree scope prevent another open-ended consolidation task.
- Whether both committed trees and unfinished work survive baseline selection.
- Whether the JSON checks cover approval, relationship and release behaviour without duplicating rules.
- Whether public route isolation and Preview approval are concrete enough for implementation.

Sections 7–9 below are retained review history. Their earlier observations and proposals are not current execution instructions.
Any remaining disagreement must be recorded before the affected stage starts.

The intended result is a clear working environment and a credible demonstration, not a claim that the entire platform is finished.

## 7. Fable Review (18 September 2026)

**Reviewer:** Claude Fable 5.1, inspecting the destination repository at `main` = `478a7d8`, clean apart from an untracked `.snapshots/` directory.

**Verdict:** The plan is sound in intent and boundaries, but it is not yet executable by another implementer without unrecorded scope decisions. Four findings block approval and three should be fixed before the first block. Findings are ordered by severity.

### 7.1 Findings that block approval

**F1. The destination is not an empty target. The baseline choice discards content from `main` unless reconciled.**
The destination already tracks 112 files covering the same three concerns as the Mac repository: the Python application under `src/ace/`, the Next.js pilot under `apps/relationship-review-pilot/`, docs, security results and the iOS specification at `docs/specs/2026-08-24-ace-ios-read-only-client-application.md`. The three most recent commits on `main` all concern ACE iOS verification gates. Starting `codex/sqe-workspace-consolidation` from the Mac commit `40bae26` means the active branch contains whatever the Mac has and none of what `main` has that the Mac lacks. Section 3 treats Windows-only changes as living in other Windows locations. It does not treat `main` itself as a source of unique work. Required addition: before creating the branch, record whether `40bae26` and `478a7d8` share a merge base, produce a file-level diff between them, and classify every `main`-only path exactly as for the other locations. Review focus items 1 and 2 cannot be answered yes until this is done.

**F2. The Revision 5 and D2 approval hashes have no recorded source of truth.**
No file in the destination repository mentions Revision 5, D2 or an approval hash. The step to verify existing approval hashes is unexecutable unless the plan names where the approved hashes are recorded, as a file path or private location, and the hash algorithm. Add both to Section 3.

**F3. The Mac-to-Windows transfer mechanism is unspecified.**
The plan says to import the Mac delivery history but not how the Mac repository becomes reachable from Windows. The options carry different risk. Pushing to `origin` (github.com/mcxl/sqe-platform) would make the Mac history visible on the shared remote before review. A `git bundle` file copied across, or a network share, would not. Recommend creating a bundle on the Mac, verifying it with `git bundle verify` on Windows, and fetching it into the destination as a named remote. Record the chosen mechanism and the bundle hash.

**F4. The web-readiness journey does not name which application serves each step.**
Two web-facing components exist: the Python auditor workbench under `src/ace/workbench` and the Next.js relationship-review pilot backed by Convex. The journey of Engagement, then Evidence Item, then relationships, gaps and decision state spans concepts present in both. The Next.js pilot's queue and detail views come from Convex functions in `convex/relationships.ts` and require `NEXT_PUBLIC_CONVEX_URL`. Verifying that path on the selected revision needs a reachable Convex deployment or must be recorded as Blocked. State, per step, the application, the route or command, and the fixture source. Without this, review focus item 5 is only nominally satisfied.

### 7.2 Findings to fix before the first block

**F5. Fixture validation against domain rules needs a concrete mechanism.**
Approval and release logic lives in Python, in `src/ace/engine/approval.py` and the tests `tests/test_approval_gate.py` and `tests/test_client_release*.py`. The showcase fixtures will be TypeScript or JSON in the Next.js app. Validating fixtures against domain rules without duplicating logic is achievable one way: store the fixture as JSON, and add a pytest that loads that JSON and runs the supported and blocked scenarios through the existing Python gate. Name this explicitly, or the implementer will either duplicate logic in TypeScript or skip validation.

**F6. The Windows source locations and hosting account are unnamed.**
Section 2 refers to other Windows locations and Section 4 to the existing hosting account without naming either. The repository contains no Vercel, Railway or Netlify configuration. Both must be enumerated in the plan or in a referenced private inventory before block one starts. Otherwise the implementer is choosing scope. A Railway token is configured in the local environment. That does not by itself establish Railway as the intended target.

**F7. The 60-minute first block cannot cover consolidation.**
Inventorying several Windows locations plus linked worktrees, reconciling `main` against the Mac commit (F1), and importing the branch is not a 60-minute task. Recommend block one be inventory and classification only, with branch creation and the instruction copy in block two once inventory size is measured. This matches the plan's own rule to estimate later work from measured inventory.

### 7.3 Confirmed strengths

- **Showcase separation is feasible and low-risk.** The Convex provider is not in the root layout. It is a standalone client component in `components/convex-client-provider.tsx` taking a `url` prop, so a dedicated showcase route can omit it entirely. The existing workbench test already mocks `convex/react`, so the presentational split matches how the component is already tested. Review focus item 3 is answerable yes provided the showcase route has its own layout segment and the build is run with `NEXT_PUBLIC_CONVEX_URL` unset to prove independence.
- **iOS continuity is protected.** No step touches the Swift source or the iOS specification. The unresolved Copy accessibility finding is correctly held out of scope.
- **Publication boundaries are explicit and adequate.** No Production, no custom domain, no merge, signed-out Preview check.
- **Verification approach avoids the previous loop.** The pilot-first rule, the deliberate-failure proof and reuse of valid existing checks are the right controls. One addition: record the exact command and exit code for each reused check, not just the fact of reuse.

### 7.4 Minor

- The untracked `.snapshots/` directory at the destination root is a tooling directory holding `config.json`, `readme.md` and `sponsors.md`. Classify it in the inventory and either ignore or exclude it.
- Section 4 says to show the relationship between the auditor workflow and the iOS client. State what artefact does this: a diagram, static screenshots labelled preview, or prose. Screenshots of the iOS candidate are private evidence under Section 3 rules unless produced from fictional data specifically for publication.

### 7.5 Answers to the Section 6 questions

| # | Question | Answer |
|---|---|---|
| 1 | Reconciliation protects unique work and history | Not yet. `main` itself is unaccounted for (F1). Transfer mechanism unspecified (F3). |
| 2 | Baseline preserves web and iOS | Not yet. Depends on the F1 diff result. |
| 3 | Showcase separation prevents private-service use | Yes, with the layout-segment and unset-variable conditions in 7.3. |
| 4 | Fictional journey represents approval and release rules | Only if F5 is adopted. |
| 5 | Distinct acceptance criteria | Partially. F4 must name the application per step. |
| 6 | Verification sufficient without repeating the loop | Yes. |
| 7 | Publication boundaries and unresolved decisions explicit | Boundaries yes. Unresolved decisions no: hosting account, hash source, Windows locations (F2, F6). |
| 8 | Executable without unrecorded scope decisions | No, until F1 to F6 are closed. |

## 8. Finding Response And Second Fable Review (18 September 2026)

Section 7 is preserved unchanged. This section records the author's response to each finding, Fable's verification of the response, and further refinements arising from that verification.

### 8.1 Verification performed for this review

Checked from the Windows machine on 18 September 2026:

- `478a7d8` resolves to `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a` in the destination.
- `40bae2640b23eb05496a093d09a4c20186403879` is absent from all three Windows repositories. Ancestry is unverified, as the author states.
- SHA-256 of both instruction files in `agentic-os-workspace\sqe\docs\ace` matches the approved values in F2.
- All three Python routes named in F4 exist in `src/ace/workbench/routes.py` at the destination revision: `/engagement/summary`, `/evidence/{evidence_id}/review`, `/relationship-reviews/{relationship_id}`.
- The Vercel team, slug and project names were not independently verified; they are recorded as author-verified.

### 8.2 Finding-response table

| Finding | Author response | Fable assessment | Status |
|---|---|---|---|
| F1 Destination `main` as a source | Compare full trees of `478a7d8c…` and `40bae264…`; record merge base or its absence; classify destination-only and conflicting files; no branch until dispositions reviewed | Accepted. Correct sequencing. | Open until comparison performed |
| F2 Hash source of truth | Authority is explicit approval in conversation; algorithm SHA-256 over exact bytes; source `agentic-os-workspace\sqe\docs\ace`; Revision 5 `252aab6b…e629`; D2 fourth draft `f7147730…2179` | Accepted. Both hashes verified locally this session. | Closed, subject to byte-exact copy check |
| F3 Transfer mechanism | Private Git bundle over existing SSH; record advertised refs and SHA-256; `git bundle verify`; import to isolated comparison repo first; later fetch via named local remote; no GitHub push | Accepted. See 8.3 R2 on where the comparison repo can live. | Closed as design |
| F4 Journey application | Python only, three named routes; one isolated fictional dataset drawn from existing evidence-review and relationship-review tests; Next.js pilot assessed separately, live check Blocked | Accepted. Routes exist at the destination revision. See 8.3 R3 on the write endpoints beside the read route. | Closed as design |
| F5 Fixture validation | JSON fixture loaded into Python checks covering approval, relationship and release behaviour; verify outcomes, version references, displayed release values; no TypeScript duplication | Accepted. Broader than Fable's original proposal and correct. | Closed as design |
| F6 Sources and hosting | Three Windows sources named; Vercel team `mcxl`, slug `mcxl1`, project `relationship-review-pilot`; `project-rr85r` linked to `mcxl/sqe-platform`; neither approved yet; inspect first | Accepted. See 8.3 R1: the inventory scope is materially larger than the three paths suggest. | Sources closed; hosting open until inspected |
| F7 Block one scope | Inventory-only, 60 minutes, no branch switching, imports, copying or application changes | Accepted. | Closed |
| Minor `.snapshots/` | Classify | Accepted | Closed as design |
| Minor iOS artefact | Diagram and labelled prose; no diagnostic screenshots by default | Accepted | Closed as design |

### 8.3 Further refinements from verification

**R1. Storage stop rule is already triggered.** The `C:` drive reported 1.3 GiB free at review time against a 475 GiB capacity. The plan's threshold is 2 GiB remaining after the proposed operation. Block one cannot proceed as written until space is recovered or the working location is moved to another volume. Recommend: before block one, record free space, identify recoverable space (the prunable worktrees in R1b are candidates only after their dispositions are recorded), and re-measure. Do not delete anything to make room during block one itself.

**R1b. The inventory scope is one large monorepo, not three folders.** `agentic-os-workspace\sqe` is a subdirectory of the `agentic-os-workspace` repository, whose top level is on `codex/ace-sprint-1` with 343 dirty status entries and 45 linked worktrees. Those worktrees span `C:\tmp`, `.codex\worktrees`, `AppData\Local\Temp` and several `Documents` siblings, two are marked prunable, and many are audit-concierge rather than SQE. `sqe-platform-public-clean` is on `codex/mcx-19-live-evidence-harness` with 10 dirty entries and itself owns a linked worktree inside `agentic-os-workspace\sqe\.artifacts`. Block one must therefore: enumerate every worktree of both repositories with branch, HEAD and dirty count; tag each as SQE-relevant or out of scope; and treat the 343-entry dirty state as unfinished work to be preserved, not noise. The 60-minute limit will likely be consumed by this enumeration alone. That is acceptable for an inventory-only block.

**R2. Comparison repository location.** With 1.3 GiB free, the isolated comparison repository from F3 also needs measured space. A bare clone of the destination plus the bundle fetch is small, but record the number before creating it.

**R3. The Python journey has write endpoints beside the read route.** `routes.py` exposes `PUT /api/v1/evidence/{id}/review/context` and `POST /api/v1/evidence/{id}/review/complete` alongside the read route. This does not affect the operational journey, which is expected to exercise them. It reinforces that the showcase must not be served from the Python application in any form, which the plan already requires.

**R4. Cross-branch instruction status.** The approved instruction files live only in `agentic-os-workspace\sqe\docs\ace`. The destination has no `docs/ace` directory. The byte-exact copy in a later block should land at the same relative path under the destination, and the hash check should be recorded as a command with output, not as a statement.

**R5. Vercel inspection checklist.** For both `relationship-review-pilot` and `project-rr85r`, record: linked Git repository and production branch; root directory; build command and output; every environment variable name (not value) and which environments inherit it; deployment protection setting; whether Preview deployments are automatically created on push. A project that inherits `NEXT_PUBLIC_CONVEX_URL` into Preview fails the isolation requirement unless the showcase build ignores it.

### 8.4 Revised open items

1. F1 comparison of `478a7d8c…` and `40bae264…` (requires bundle transfer, blocks baseline selection).
2. Hosting suitability (requires R5 inspection).
3. Storage recovery to at least 2 GiB remaining after planned operations (R1, blocks block one).

Everything else in Section 7 is closed or closed as design pending execution evidence.

## 9. Third Fable Review Of Revision 2 (18 September 2026)

Sections 7 and 8 were re-read and are intact. Sections 1 to 6 were reviewed in full against the F1 to F7 and R1 to R5 corrections.

### 9.1 Verdict

Revision 2 resolves every accepted correction in the main instructions. The stage table, storage gate, two-level inventory, history comparison and hosting checklist are concrete enough for another implementer to execute Stages 0 to 3 without unrecorded scope decisions. Three items still need a recorded decision before Stages 0, 2 and 5 respectively. None requires further plan redesign.

### 9.2 Correction coverage

| Correction | Where resolved | Assessment |
|---|---|---|
| F1 | Section 3, Compare Histories Before Selecting A Baseline; Stage 2 | Resolved as design. Baseline is no longer presumed. |
| F2 | Section 3, instruction table with SHA-256, source and destination paths, authority statement | Resolved. Destination `docs/ace` confirmed absent, so the copy creates no collision. |
| F3 | Section 3, bundle over SSH, content check, isolated comparison repository, named local remote | Resolved as design. |
| F4 | Section 3, Python journey table; Convex pilot Blocked separately | Resolved. Routes confirmed present at `478a7d8`. |
| F5 | Section 4, versioned JSON plus pytest over approval, relationship and release behaviour | Resolved as design. See 9.3 item 3 for module names. |
| F6 | Section 2 location table; Section 4 Vercel table and inspection list | Resolved. Hosting remains an inspection candidate, correctly. |
| F7 | Stage table; Stage 1 cap and exclusions | Resolved. |
| R1 | Storage gate; Stage 0 | Resolved as design. See 9.3 item 1. |
| R1b | Two-level inventory; monorepo row in location table | Resolved. |
| R2 | Comparison-repository capacity and path recording | Resolved as design. |
| R3 | Python journey scoped to viewing; write endpoints recorded, not exercised | Resolved. |
| R4 | Copy destination path and hash command retention | Resolved. |
| R5 | Vercel inspection list with inheritance and route checks | Resolved. |
| Minor | `.snapshots/` in register; iOS diagram and prose | Resolved. |

### 9.3 Items needing a recorded decision before the named stage

**1. Stage 0 must produce a relocation decision, not just a measurement.** Free space on `C:` read 2.1 GiB by one tool and 0.99 GiB by another within the same minute. `G:` reads 0.94 GiB free. Both are below the reserve before any write. `T:` reads about 1280 GiB free. Any inventory record, bundle, comparison repository or recovery copy therefore needs a volume other than `C:` or a prior explicit space-recovery disposition. Stage 0 should name the candidate volume and confirm it is local, not a cloud-mirrored drive, before Stage 1 writes anything.

**2. Record the OneDrive relationship of the working folders before Stage 2.** The Windows Documents known folder resolves to `LOCAL_HOME\OneDrive - AuditCo\Documents`. The three repositories sit in `LOCAL_HOME\Documents`, which is a different folder. The plan requires the comparison repository to stay outside cloud-synchronised folders. Stage 0 should record that the repository folders are not under OneDrive redirection and choose the comparison path accordingly.

**3. Name the Python modules the fixture pytest must exercise.** The plan says approval, relationship and release behaviour. The corresponding code at the destination revision is `src/ace/engine/approval.py` for MATE approval, `src/ace/engine/tracing.py` for relationship decisions and the accepted planning trace, and `src/ace/domain/release.py` with `src/ace/workbench/client_release_service.py` for release values. Recording these removes the last interpretive choice from Stage 5 and ties the fixture check to the existing tests `test_approval_gate.py`, `test_relationship_review.py` and `test_client_release*.py`.

**4. Pre-record the route-isolation mechanism for Stage 5.** The pilot root page already renders a configuration alert when `NEXT_PUBLIC_CONVEX_URL` is unset, so a showcase build succeeds without the variable. It does not make `/` open the showcase, and the pilot route remains built and reachable. Isolation therefore needs one of two mechanisms, and the plan should choose or explicitly defer the choice: a build-time showcase flag that redirects `/` to the showcase route and excludes the pilot page from the build, or a separate Next.js root directory for the showcase. The first stays within the existing application. The second edges toward restructuring, which Section 4 excludes. Recommend the first, recorded as the intended approach, with the stop rule already in Section 4 applying if it cannot be achieved.

### 9.4 Section 6 answers for Revision 2

| # | Question | Answer |
|---|---|---|
| 1 | Reconciliation protects unique work and history | Yes as design. Execution evidence pending Stages 1 and 2. |
| 2 | Baseline preserves web and iOS | Yes as design. Baseline decision deferred to reviewed comparison. |
| 3 | Showcase separation prevents private-service use | Yes, once 9.3 item 4 is recorded. |
| 4 | Journey represents approval and release rules | Yes, once 9.3 item 3 is recorded. |
| 5 | Distinct acceptance criteria | Yes. |
| 6 | Verification sufficient without repeating the loop | Yes. |
| 7 | Boundaries and unresolved decisions explicit | Yes. Section 5 open-decision table is adequate. |
| 8 | Executable without unrecorded scope decisions | Stages 0 to 3 yes, subject to 9.3 items 1 and 2. Stages 4 to 7 yes, subject to items 3 and 4. |

Revision 2 is fit to proceed to a Stage 0 execution proposal once 9.3 items 1 and 2 are recorded. Items 3 and 4 can be recorded any time before Stage 5.

## 10. Fourth Fable Review Of Revision 4 (18 September 2026)

Sections 7 to 9 are present and intact. Sections 1 to 6 were reviewed against the four items in 9.3 and re-verified where the claims were locally checkable.

### 10.1 Verification performed

- `Win32_LogicalDisk` at review time: C: DriveType 3, volume `Windows-SSD`, 16.17 GiB free. G: DriveType 3, volume `Google Drive`, 15.36 GiB free. T: DriveType 4, provider `\192.168.86.114\Files`, 1277.42 GiB free. The C: and T: figures agree with Section 2. The G: figure has moved from under 1 GiB to over 15 GiB in step with C:, which is consistent with a Google Drive virtual volume reporting the host disk's free space. This confirms the plan's rejection of G: as private working storage and shows its reported capacity is not independent.
- All four module entry points in the Section 4 fixture table exist at `478a7d8`: `build_approved_assessment` and `evaluate_approved_assessment` in the approval engine, `build_accepted_planning_trace` in the tracing engine, and the `ClientReleaseService` class in the client-release service. The release domain module holds Pydantic models for release packages, entries and client responses. The referenced tests exist.
- `next.config.ts` contains no redirect or showcase flag. The Stage 5 mechanism is correctly described as proposed, not existing.

### 10.2 Disposition of the 9.3 items

| 9.3 item | Revision 4 treatment | Assessment |
|---|---|---|
| 1 Storage decision | C: recovered to about 16 GiB by the user; relocation conditional on measured peak; Mac-local candidate path named but unapproved; G: and T: rejected as substitutes; Stage 0 proposal with 20-minute cap | Resolved as design. Correctly avoids calling storage resolved on a free-space reading alone. |
| 2 OneDrive relationship | Known-folder redirection recorded; repository path confirmed outside registered OneDrive roots and free of reparse points; recheck required for each scratch path | Resolved. |
| 3 Fixture modules | Module and entry-point table with test references; interface recheck after baseline reconciliation; mismatched-version case added | Resolved. Entry points verified. |
| 4 Route isolation | `SQE_SHOWCASE_BUILD=1` build-time mode; root redirect; build-time selection of the root implementation; emitted-route and bundle inspection; sentinel URL test; stop rule if the toolchain cannot exclude the pilot | Resolved as design. Feasibility correctly left unclaimed. |

### 10.3 Remaining observations

None blocks a Stage 0 proposal. Two are worth recording.

**O1. Stage 0 cap versus SSH latency.** The 20-minute hard limit covers Windows checks and Mac checks over SSH. If the Mac is asleep or SSH prompts for a key passphrase, the limit can be consumed by waiting. The plan already separates waiting time from active time and treats missing access as a blocker, so no change is needed. Record the SSH probe result first so a Mac-side blocker is known within the first minutes.

**O2. Sentinel URL semantics.** The Stage 5 test with an inert sentinel Convex URL is a strong isolation check. It should use a non-routable address, for example a `.invalid` hostname, so that a failure to exclude the provider produces a visible connection error in the browser request log rather than a silent timeout. This is a test-design note, not a plan gap.

### 10.4 Section 6 answers for Revision 4

| # | Question | Answer |
|---|---|---|
| 1 | Reconciliation protects unique work and history | Yes as design. Execution evidence pending Stages 1 and 2. |
| 2 | Baseline preserves web and iOS | Yes as design. |
| 3 | Showcase separation prevents private-service use | Yes as design. Feasibility proof is correctly deferred to the Stage 5 pilot. |
| 4 | Journey represents approval and release rules | Yes. Modules and entry points verified. |
| 5 | Distinct acceptance criteria | Yes. |
| 6 | Verification sufficient without repeating the loop | Yes. |
| 7 | Boundaries and unresolved decisions explicit | Yes. |
| 8 | Executable without unrecorded scope decisions | Yes for Stages 0 to 7 as designed. Each later stage still requires its own bounded execution proposal, as the plan states. |

Revision 4 is fit for a Stage 0 execution proposal. No further plan revision is required before Stage 0. The plan itself grants no execution authority, and this review does not change that.
