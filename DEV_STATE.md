# Development State

ACE is a private, deterministic WHS auditor workbench for the Squadron Energy engagement. This file is the verified development handover. `ACE_PROGRESS_GUIDE.html` is the visual roadmap. Code, provider records, Linear, and test evidence control when records disagree.

## Current Controls

The client has not accepted the review. G0 blocks real client information. Use only fictional, public, or AuditCo-owned information. The auditor remains the only approval authority. Interface code must use the existing domain gates. Do not run DeepSec without new approval and an approved isolation design.

## Repository State

The current controlled branch is `origin/codex/ace-sprint-1`. It points to
the ACE iOS read-only client specification merge commit
`436fed942d1b45da7473f98930de11b33f861d13`.

PRs [#54](https://github.com/mcxl/agentic-os-workspace/pull/54),
[#55](https://github.com/mcxl/agentic-os-workspace/pull/55), and
[#56](https://github.com/mcxl/agentic-os-workspace/pull/56) delivered the
three-stage release-engine refactor. PR
[#57](https://github.com/mcxl/agentic-os-workspace/pull/57) completed the
required visual progress record. PR
[#59](https://github.com/mcxl/agentic-os-workspace/pull/59) completed the
Phase 6B2 read-only client release projection. PR
[#61](https://github.com/mcxl/agentic-os-workspace/pull/61) merged the ACE iOS
read-only client specification. It changed no application code.

## Verified Core

The tested Python core covers ratings, MATE approval, planning traces, evidence conclusions, Engagement setup, image capture, and evidence review. The FastAPI workbench uses authentication, external storage, immutable decisions, version-specific approvals, and unique retry keys. Core files are `src/ace/app.py`, `src/ace/domain/assessment.py`, `src/ace/engine/approval.py`, and `src/ace/workbench/`.

## Phase 1 Final Test Suite

On 18 August 2026, Python 3.12.3 and pytest 8.4.2 passed all **365 tests**. One Starlette TestClient deprecation warning remains. The suite covers:

- **10 offline draft tests** (`test_offline_drafts.py`): Sync endpoint, idempotency, G0 rejection, authentication, duplicate reference, offline badge, IndexedDB storage, reconnect sync, duplicate prevention key
- **39 evidence review tests** (`test_evidence_review.py`): Full record review — authentication, page controls, context rules, audit questions, versions, decisions, proposed links, completion, immutability, G0 media, atomic completion
- **28 engagement setup tests** (`test_engagement_setup.py`)
- **24 workbench tests** (`test_workbench.py`): Capture, media retrieval, review, relationship review
- **7 app-level tests** (`test_app.py`): Route map, controls, evaluations
- **257 core domain/engine/storage tests**

## Protected Offline Drafts

Pull request 38 is open on branch `vorflux/offline-drafts`, based on `codex/ace-sprint-1`. The reviewed head is `0daa2f2`. It adds protected fictional offline Engagement drafts, IndexedDB storage, reconnect sync, and the `POST /workbench/api/v1/engagements/sync` endpoint.

On 18 August 2026:
- Focused PR test set passed 10 of 10 tests.
- Full evidence review suite passed 39 of 39 tests.
- Complete suite passed 365 of 365 tests.
- Code review found and fixed a variable shadowing bug in the sync function.
- Added transaction-level error handling to all IndexedDB operations.
- Added 409 conflict handling to remove permanently-orphaned IndexedDB drafts.

PR #38 acceptance criteria:
- [x] Offline save works in Chrome DevTools Offline mode
- [x] Draft remains after reload
- [x] Reconnect sync creates one server draft (idempotent key: 201)
- [x] Repeated sync creates no duplicate
- [x] Real-client data returns HTTP 403
- [x] G0 controls remain active

## Full Record Review

The evidence review workflow is complete. Browser test on 18 August 2026 verified:

- [x] Full record review page loads with all controls
- [x] Captured evidence section displays evidence ID, filename, engagement
- [x] Source Context And Gaps section has all fields (Provider, Origin, Source Date, Source Version, Source Location, Freshness, Duplicate Evidence ID, Source Evidence IDs, Gap Status, Gap Materiality, Description, Limitations, Gap Explanation)
- [x] Audit Questions section with Control ID, Question Type, MAIN Parent, Question Text, Purpose
- [x] Question Version controls
- [x] Decisions And Proposed Links section (APPROVED/REJECTED/CHANGES_REQUIRED, SUPPORTS/WEAKENS/CONTRADICTS)
- [x] Complete Review section with Review Notes and completion

A focused integration test (`test_full_record_review_flow_capture_to_completion`) covers the complete flow: capture → source context → audit questions → versions → decisions → proposed links → completion → verified final state.

Browser evidence:
- Screenshot: `/code/.generated_artifacts/images/evidence-review-loaded.png`
- Recording: `/code/.generated_artifacts/recordings/full-record-review.webm`

## Known Limits

The pilot uses fictional information only. It has no approval, decision, edit, delete, upload, or public write action. G0 approval is required before real client use.

## Phase 1 Delivery

MCX-1 through MCX-4 are Linear onboarding tasks. MCX-5, MCX-6, MCX-7, and MCX-8 are complete. MCX-9 is Canceled. MCX-10 is Todo.

MCX-11 (Relationship Details) was merged as PR #37 on 17 August 2026. Merge commit: `d71693a3`.

PR #38 (Protected Offline Drafts) is open with full review and testing complete. Head: `0daa2f2`. Base: `1742cb0` (codex/ace-sprint-1).

Do not merge without final approval. Do not deploy to Production. Do not use real client information.

## Phase 2 — Engagement Control Summary (PR #39)

Pull request 39 merged on 19 August 2026. Merge commit: `bcc5db6`. Merged head: `a4fd72e`. Base: `4ba9a8a`.

The Engagement Control Summary is a read-only HTML page at `GET /workbench/engagement/summary`. It answers four auditor questions from existing server database records:

- What is this Engagement?
- What is complete?
- What needs attention?
- What should the auditor do next?

### Data Sources

Reads existing records only from `engagement_setups`, `evidence`, `relationships`, `evidence_review_contexts`, and `engagement_audit_events`. No duplicate summary records. No schema changes.

### Fields Shown

| Field | Source |
|---|---|
| Engagement title, reference, state, data classification | `engagement_setups` (current) |
| Authority, purpose, scope, exclusions | `engagement_setups` (current) |
| Review dates (start, end, cut-off) | `engagement_setups` (current) |
| Accountable auditor | `engagement_setups` (current) |
| Evidence captured, pending review, reviewed | `evidence` WHERE `is_capture=1` |
| Open relationship conflicts | `relationships` WHERE `relationship_type='CONTRA'` AND `status='OPEN'`, scoped to capture evidence |
| Open gaps (controlled source only) | `evidence_review_contexts` JOIN `evidence` |
| Recent activity | `engagement_audit_events` |
| Recommended next action | Derived from state (DRAFT, no evidence, pending review, conflicts, gaps) |

### Changed Files

- `sqe/src/ace/workbench/storage.py` — `engagement_summary()` and `_derive_recommendation()` methods
- `sqe/src/ace/workbench/routes.py` — `GET /workbench/engagement/summary` route, HTML renderer, and `ENGAGEMENT_SUMMARY_PAGE` template
- `sqe/tests/test_app.py` — route map updated
- `sqe/tests/test_engagement_summary.py` — 13 focused tests

### Test Results

On 19 August 2026:
- Focused tests: 13/13 passed
- Full test suite: 378/378 passed (365 original + 13 new)
- Unauthenticated access returns HTTP 401
- Browser verification: page renders with all sections — Engagement, Evidence, Open Items, Recent Activity, Recommended Next Action

### Safety Controls

- No write actions on the page (no forms, no POST/PUT links)
- No approval, delete, upload, or decision actions
- G0 blocks real-client data
- Authentication required (HTTP Basic)
- Read-only: no database writes from the summary endpoint
- Fictional data only

### Browser Evidence

- Screenshot: `/code/.generated_artifacts/images/engagement-summary.png`
- Recording: `/code/.generated_artifacts/recordings/engagement-summary.webm`

### Phase 2 Status: COMPLETE

Merged into `codex/ace-sprint-1` at `bcc5db6`. All acceptance criteria met.

### Phase 3 — Review Enhancements

On 19 August 2026, three read-only enhancements were applied at `8bf191a`:

- **Pending Evidence preview**: Shows up to 5 most recent pending items with filename and captured date, linking to individual evidence review pages.
- **Conflict capture-only note**: Open Items section explains that relationship conflicts appear only for linked captured evidence, with a link to the Relationship Review queue.
- **Recommendation navigation links**: Recommendation text includes a link to the workbench (for pending review) or Relationship Review (for conflicts).

All changes are additive, read-only, G0-protected, and use existing routes only.

### Known Limits (Phase 2)

- **Relationship conflicts** appear only when conflicting records are linked to evidence with `is_capture=1`. Trace-level conflicts without captured evidence will not surface on the summary.
- **Recent activity** may be empty on seeded engagements when no audit events have been recorded for that engagement. The page shows the correct empty state in this case.

### Phase 4 — Deterministic Review Suggestions

On 19 August 2026, a deterministic review suggestions feature was added at `112b9e6`:

- **Extraction adapter** (`extraction.py`): Zero-dependency regex-based `EvidenceExtractionAdapter` with 11 pattern rules returning `FACT` and `WARNING` suggestions with exact character spans (`start`, `end`). No external API calls, no API keys, no non-determinism.
- **Source text column**: `source_text TEXT DEFAULT NULL` added to the `evidence` table schema. Seeded on EVD-FIC-0001 with fictional source text.
- **Suggestions endpoint**: `GET /workbench/api/v1/evidence/{evidence_id}/suggestions` returns `{api_version, evidence_id, suggestions: [{type, text, source_start, source_end}]}`.
- **Review panel**: Advisory section on the evidence review page between Captured Evidence and Source Context. Renders FACT/WARNING items with emoji labels, quoted text, and span positions. Shows empty state for evidence without source text.
- **Evidence seeding**: `evidence_suggestions()` method on `WorkbenchStore` reads `source_text` from the evidence table and runs the adapter.

All changes are additive and read-only. The endpoint is authenticated but does not use G0 engagement validation — it looks up evidence directly by ID. The panel is advisory only — ACE does not save, approve or apply suggestions.

#### Test Results

| Suite | Count | Status |
|---|---|---|
| Phase 1–3 baseline | 382 | Passed |
| Phase 4 full suite | 397 | Passed |
| Phase 4 focused (extraction.py) | 15 | Passed |

#### Browser Verification

- Desktop (1280×800): 7 suggestions rendered — 5 FACT, 2 WARNING with exact span positions
- Mobile (375×812): Same 7 suggestions with emoji labels rendering correctly
- Empty state: Verified via API (empty list for nonexistent evidence)
- No write paths: POST/PUT return 405

### Phase 5 — Engagement Graph Projection

On 19 August 2026, a read-only graph projection was added:

- **Graph query** (`WorkbenchStore.graph_projection()`): Collects all fictional records (engagement, evidence, obligations, risks, controls, owners, mates, conclusions) as nodes and all relationships as edges. Generates warnings for CONTRA/OPEN conflicts, evidence without source text, and non-field-captured evidence.
- **Graph page** (`GET /workbench/engagement/graph`): G0-validated, server-rendered HTML with inline SVG (no external libraries, no CDN). Shows a vertical flow of nodes connected by directional arrows — arrows only render when an actual relationship edge exists. Below the SVG: a Records table with node details, and a Warnings table for excluded/incomplete records.
- **XLSX export** (`GET /workbench/engagement/graph/export`): Airtable-compatible workbook with 5 sheets (Records, Evidence, Relationships, Warnings, Read Me). Uses openpyxl. No formulas, no merged cells, no embedded photos. Export identifier is `{engagement_id}-{iso_timestamp}`.
- **Photo metadata only**: Evidence sheet exports media type and capture status. No photo embedding, no file:// links, no upload.
- **Shared snapshot**: Both HTML graph and XLSX export call `graph_projection()` once per request — content parity guaranteed.
- **Navigation links**: Evidence nodes in the Records table link to their review pages.

All changes are read-only, G0-validated, use existing records only. No Neo4j, no paid provider, no external API calls.

#### Test Results

| Suite | Count | Status |
|---|---|---|
| Phase 1–4 baseline | 401 | Passed |
| Phase 5 full suite | 435 | Passed |
| Phase 5 focused (graph_projection.py) | 34 | Passed |

Includes approved-relationship filtering (edges exclude CONTRA/OPEN), snapshot identity (SHA-256 hash + full node/edge comparison between HTML and XLSX), and relationship direction tests on all 6 approved edges. HTML now includes an explicit Relationships direction table alongside the SVG.

#### Browser Verification

- Desktop (1280×800): SVG with 8 node boxes, Records table, Warnings section, export download link
- Unauthenticated access: HTTP 401 confirmed
- XLSX export: Correct MIME type, 5 sheets, all headers present, no formulas, no embedded images
- Screenshot: `/code/.generated_artifacts/images/phase5-graph-desktop.png`

### Phase 5B — ACE Change Record And Export Authorities

On 19 August 2026, a snapshot-based change detection engine and export package were added:

- **Snapshot engine**: `_capture_snapshot()` reads 8 record types + relationships directly from SQLite (self-contained, no dependency on `graph_projection()`). `create_snapshot()` stores an immutable snapshot with SHA-256 content hash. `detect_changes()` diffs current vs prior snapshot for added/removed/modified records and relationship edges, scoped to the same engagement.
- **Change records**: `change_records` table with immutable triggers (no UPDATE, no DELETE). `ChangeRecord` frozen dataclass with time-based `change_id` (SHA-256 12-hex fragment), `export_id`, `record_id`, `snapshot_id`, `evidence_id`, `idempotency_key`, `timestamp`, `change_type`, `record_type`, `label`, `detail`.
- **Idempotency**: Uses the proven `creation_attempt_key` pattern — check-before-create, return existing on collision — for both snapshot deduplication (by content hash) and change record reuse (by idempotency key). Export IDs use 12-hex-char SHA-256 fragments from engagement + timestamp + idempotency key.
- **Export package builder** (`export_builder.py`): Produces a ZIP with up to 10 files: Summary.xlsx, Change-Log.xlsx, Summary.docx, Summary.pdf, Change-Log.docx, Change-Log.pdf, Changes.csv, Changes.json, Read-Me.txt, manifest.json. Australian English throughout with AuditCo Capital Case headings. PDF via LibreOffice headless (gated by `document-toolchain-doctor -Probe`; fails explicitly when tools are missing). Formula injection escaped via `_xlsx_safe` on user-facing CSV and XLSX values (labels, details, warning text).
- **Notion test double** (`notion_publisher.py`): Fictional one-way boundary with stable publication IDs and duplicate prevention.
- **Routes**: `POST /workbench/api/v1/engagements/export` (create snapshot + detect changes + publish, idempotent), `GET /workbench/api/v1/engagements/export/{id}` (ZIP download). Both require `Depends(require_auditor)` — fails 503 when `ACE_AUDITOR_PASSWORD` is unset. ZIP download reads the snapshot's engagement rather than the potentially-changed current engagement.
- **Read-Me.txt**: Lists only files actually packaged (conditionally omits PDF entries when `skip_pdf=True`).

All changes are additive. No writes to existing tables beyond the new `snapshots` and `change_records` tables. Both tables have immutable triggers. No photos, secrets, or real client data in exports.

#### Test Results

| Suite | Count | Status |
|---|---|---|
| Phase 1–5 baseline | 435 | Passed |
| Phase 5B full suite | 436 | Passed |
| Phase 5B focused (test_change_export.py) | 39 | Passed |

#### Acceptance Criteria

- Snapshot consistency (same projection → same hash) ✅
- Idempotency (same key → same result) ✅
- Snapshots immutable (UPDATE/DELETE blocked by triggers) ✅
- Change records immutable (UPDATE/DELETE blocked by triggers) ✅
- Export ZIP integrity (all 10 files present, checksums match) ✅
- Fictional data protection (no real org names, client data, or secrets) ✅

### Phase 6A — Minimal Client Release View

On 20 August 2026, two read-only client endpoints were added behind independent HTTP Basic auth:

- **Client auth** (`client_auth.py`): `require_client()` dependency with `secrets.compare_digest`, 503 fail-closed when `ACE_CLIENT_PASSWORD` is missing or empty, generic 403 on auth failure (no credential enumeration).
- **Client page** (`GET /client`): HTML page showing engagement name, review status, release version, published date, approved conclusion (title, summary, evidence reference), and a fictional-data notice. All dynamic values HTML-escaped.
- **Client API** (`GET /client/api/v1/release/current`): JSON endpoint returning `ClientReleaseResponse` with `engagement_name`, `review_status`, `release_version`, `published_at`, and optional `conclusion` (title, summary, evidence_reference_id).
- **Release tables**: `client_release_packages` (DRAFT/PUBLISHED/WITHDRAWN) and `client_release_entries` with constrained immutability trigger (PUBLISHED→WITHDRAWN allowed when content unchanged), unique partial index for one current release per engagement.
- **Schema**: `conclusions` extended with `engagement_id`, `evidence_id`, `version`, `conclusion_type`, `summary`, `approved_by`, `approved_at`, `created_at`.
- **Audit events**: `engagement_audit_events` CHECK constraint extended with `CONCLUSION_APPROVED`, `RELEASE_CREATED`, `RELEASE_PUBLISHED`, `RELEASE_WITHDRAWN`. Fictional event records exist for CON-FIC-0001 approval and all three release packages.
- **Seed data**: CON-FIC-0001 (APPROVED with event), CON-FIC-0002 (CANDIDATE), ENG-FIC-0002, REL-FIC-DRAFT, REL-FIC-PUBLISHED, REL-FIC-WITHDRAWN, with migration UPDATE for legacy CON-FIC-0001 rows.

#### Changed Files

9 files, +1,420 / −5 (cumulative across all Phase 6A PRs):

| File | Change |
|---|---|
| `sqe/src/ace/domain/release.py` | +106 (new) — pydantic models |
| `sqe/src/ace/workbench/client_auth.py` | +57 (new) — HTTP Basic auth dependency |
| `sqe/src/ace/workbench/client_routes.py` | +247 (new) — HTML page + JSON API + G0 guard |
| `sqe/src/ace/workbench/storage.py` | +437/−3 — schema, seed data, audit events, CHECK migration |
| `sqe/tests/test_client_release.py` | +568 (new) — 33 tests (26 release + 5 events + G0 + migration) |
| `sqe/src/ace/app.py` | +2 — client_router include |
| `sqe/tests/test_app.py` | +2 — route whitelist |
| `sqe/tests/test_engagement_summary.py` | −1 — relaxed approve check for event feed |
| `sqe/tests/test_relationship_review.py` | +1/−1 — INSERT OR IGNORE |

#### Test Results

| Suite | Count | Status |
|---|---|---|
| Phase 6A focused | 33 | Passed |
| Complete suite | 507 | Passed |

#### Merge Records

| PR | Merge Commit | Head Commit | Branch | What |
|---|---|---|---|---|
| [#46](https://github.com/mcxl/agentic-os-workspace/pull/46) | `1ef19ea` | `1ef19ea` | `vorflux/phase6a-reconcile` | Phase 6A reconciliation |
| [#48](https://github.com/mcxl/agentic-os-workspace/pull/48) | `5d82b39` | `5d82b39` | `vorflux/phase6a-codex-fixes` | G0 guard + CHECK migration |
| [#49](https://github.com/mcxl/agentic-os-workspace/pull/49) | `814bbd8` | `814bbd8` | `vorflux/phase6a-test-isolation` | Test isolation |
| [#50](https://github.com/mcxl/agentic-os-workspace/pull/50) | `38760a6` | `38760a6` | `vorflux/phase6a-finalize-docs` | Doc finalization |
| [#51](https://github.com/mcxl/agentic-os-workspace/pull/51) | `7032cad` | `5221daa` | `vorflux/phase6a-inventory-fix` | File inventory + merge records |

Target: `codex/ace-sprint-1`. All merges via squash. Final head: `7032cad`.
Base: `codex/ace-sprint-1` at `ca1f7de`.
Tests: 507 passed.
Linear: [MCX-13](https://linear.app/mcxi-co/issue/MCX-13/) (merged), [MCX-12](https://linear.app/mcxi-co/issue/MCX-12/) (merged).

#### Safety Controls

- G0: fictional data only — no real client information
- No write paths from client endpoints
- Client auth independent of auditor auth
- Fictional pilot notice on every page
- `html.escape()` on all dynamic values (XSS protection)
- All release lifecycle events recorded as immutable audit trail

### Phase 6A Status: PILOT COMPLETE

Reconciled onto controlled baseline. All acceptance criteria met.

### Phase 6B1 — Approved Actions

On 23 August 2026, Phase 6B1 added approved actions to the immutable client release view:

- **Approved action source**: fictional action records include version, description, owner, target date, approval status, delivery status, approver, and approval time.
- **Client release snapshot**: action description, owner, target date, and delivery status are copied into the release entry. Client routes read the immutable snapshot, not the live action.
- **Client API and HTML**: the current client release shows approved actions with owner, target date, and `OPEN` or `COMPLETE` delivery status.
- **Approval integrity**: action and conclusion entries require approved sources, matching engagement and version, exact visible values, complete approval attribution, and matching approval events.
- **Publication integrity**: release creation, publication metadata, chronology, entry cardinality, release versions, source lineage, and terminal history are validated before publication.
- **Migration safety**: the Phase 6A published conclusion snapshot moves into a new version without changing the approved source or historical published and withdrawn records.
- **Stable entry identity**: new and rebuilt schemas require `release_entry_id TEXT NOT NULL PRIMARY KEY`. Legacy NULL IDs fail closed before mutation.
- **Reopen safety**: corrected triggers are replaced after schema work. Valid migrations preserve entries and audit events on repeated opening.

#### Phase 6B1 Changed Files

4 files, +8,654 / -147 in PR #52:

| File | Change |
|---|---|
| `sqe/src/ace/domain/release.py` | +44/-3 — approved action client response fields |
| `sqe/src/ace/workbench/client_routes.py` | +92/-27 — immutable action snapshot API and HTML output |
| `sqe/src/ace/workbench/storage.py` | +1,456/-96 — action schema, release lifecycle, validation triggers, migration, and seed controls |
| `sqe/tests/test_client_release.py` | +7,062/-21 — release, migration, integrity, API, and HTML regression tests |

#### Phase 6B1 Test Results

| Gate | Result |
|---|---|
| Focused client release and initialisation safety | 289 passed |
| Complete suite | 762 passed, 1 Starlette deprecation warning |
| API and HTML | 27 passed |
| Controlled document toolchain probe | Passed |
| `git diff --check` | Clean |

#### Phase 6B1 Reviews

- Pocock review: READY, no findings
- Controlled Greptile review: completed; finding fixed and resolved
- Fresh Sol review: SHIP, no findings
- Exact-head Codex review: no major issues
- GitHub review threads before merge: zero unresolved

#### Phase 6B1 Merge Record

| PR | Merge Commit | Head Commit | Branch | Linear |
|---|---|---|---|---|
| [#52](https://github.com/mcxl/agentic-os-workspace/pull/52) | `1898e347` | `1d832a5` | `vorflux/phase6b1-approved-actions` | [MCX-14](https://linear.app/mcxi-co/issue/MCX-14/) — Done, merged |

Approved base: `d99791f`. GitHub merged the exact approved base and head on 23 August 2026 at 01:47 UTC.

#### Phase 6B1 Safety Controls

- G0 remains active. Only fictional data is present.
- Client access remains read-only and separate from auditor authentication.
- Approved action and conclusion sources are immutable.
- Published and withdrawn packages and entries remain immutable.
- Release entry IDs, release IDs, source values, versions, approval events, dates, actors, and chronology fail closed.
- No client editing, comments, limitations, exports, real data, Production, or new authentication were added.

### Phase 6B1 Status: COMPLETE

PR #52 merged at exact approved head. MCX-14 is Done with the `merged` label.

### Phase 6 — Release Engine Refactor Complete

On 23 August 2026, the three-stage release-engine refactor and its final
documentation follow-up were merged into `codex/ace-sprint-1`.

#### Final Architecture

- `ClientReleaseService` owns draft creation, validation, publication,
  withdrawal, current-release selection, history, version allocation, and
  creation/withdrawal audit coordination.
- `ClientReleaseStorage` owns parameterised release SQL and always uses the
  caller-supplied SQLite connection.
- Web routes contain no release SQL. They retain HTTP, authentication, G0,
  error translation, one connection, service reads, and HTML rendering.
- `begin_release_write()` acquires caller-owned `BEGIN IMMEDIATE` before
  version-allocation reads. The caller retains commit and rollback ownership.
- `client_release_packages_auto_publish_event` remains the owner of
  `RELEASE_PUBLISHED` audit creation.
- `WorkbenchStore` remains the release migration and trigger-installation
  owner.

#### Database And Migration Controls

- All 18 release-related triggers were retained. Removing any trigger would
  weaken direct-SQL, migration, lineage, engagement-isolation, immutability,
  uniqueness, cardinality, version, or publication-audit protection.
- Fresh, Phase 6A, Phase 6B1, predecessor-trigger, and repeated-reopen states
  retain the exact trigger inventory with no stale `_old` references.
- Complete immutable audit snapshots and supported nullable-ID legacy release
  history remain preserved across upgrades and reopens.
- Direct-SQL package deletion, release-entry update/deletion, and audit-event
  deletion are covered by durable trigger regression tests.

#### Final Verification

| Gate | Result |
|---|---|
| Stage 1 focused / complete | 303 / 777 passed |
| Stage 2 focused / complete | 311 / 785 passed |
| Stage 3 corrected focused / complete | 318 / 792 passed |
| Phase 6B2 focused / complete | 325 / 799 passed |
| API and HTML compatibility | Passed |
| Migration and repeated reopen | Passed |
| Exact trigger inventory and immutable audit snapshots | Passed |
| Pocock standards and specification | Approved |
| Fresh Sol | SHIP |
| Exact-head Codex | Approved |
| Controlled Greptile finding | Resolved |
| Final Fresh Sol | Approved |
| Final Codex | Approved |
| Open review threads before Phase 6 PRs #54–#57 merged | Zero |
| Phase 6B2 PR #59 Greptile thread | Finding fixed; thread outdated but not marked resolved before merge |

The pytest runs retained one existing Starlette/HTTPX deprecation warning.

#### Final Merge Records

| Stage | Pull Request | Approved Head | Merge Commit |
|---|---|---|---|
| Service boundary | [#54](https://github.com/mcxl/agentic-os-workspace/pull/54) | `7e67ee62` | `48829602` |
| Workflow migration | [#55](https://github.com/mcxl/agentic-os-workspace/pull/55) | `761b0cb9` | `6f88ce3d` |
| Trigger ownership and final design | [#56](https://github.com/mcxl/agentic-os-workspace/pull/56) | `2887c0ce` | `a2f8a308` |
| Progress-guide completion record | [#57](https://github.com/mcxl/agentic-os-workspace/pull/57) | `727243d8` | `57a669a6` |
| Read-only client release projection | [#59](https://github.com/mcxl/agentic-os-workspace/pull/59) | `ddd1b69d84cdc36cb7a28f3aed6ae83a5119b0dd` | `a1d52c6148b64106ed1a4516aec8e72aea4ef666` |

Final target head after Phase 6B2: `a1d52c6148b64106ed1a4516aec8e72aea4ef666`.

#### Lessons And Residual Boundary

- Acquire SQLite write intent before version-allocation reads. Upgrading an
  already-read deferred transaction is not a safe concurrency contract.
- Pass one active connection through every service and storage call. Opening a
  second connection inside a transaction risks lock failures.
- Compare complete immutable audit rows, not counts alone, when proving
  migration and reopen stability.
- Direct SQL can perform a minimal `PUBLISHED` to `WITHDRAWN` transition
  without complete withdrawal metadata or a withdrawal audit event. The
  service-owned workflow guarantees completeness. Adding database enforcement
  is a separately scoped behaviour change.

#### Phase 6B2 — Read-Only Client Release Projection

On 23 August 2026, PR [#59](https://github.com/mcxl/agentic-os-workspace/pull/59)
merged at approved head `ddd1b69d84cdc36cb7a28f3aed6ae83a5119b0dd` as
`a1d52c6148b64106ed1a4516aec8e72aea4ef666` at 19:53:25 UTC.

- `ClientReleaseProjection` is the pure, transport-neutral owner of the
  existing `ClientReleaseResponse` projection, including unavailable and
  missing-engagement responses and immutable conclusion/action snapshots.
  It performs no SQL, connection or transaction work, authentication, G0
  evaluation, package selection, HTML rendering, or writes.
- The route owns authentication, G0, its single `store.connect()` connection,
  service reads on that connection, HTTP translation, and unchanged HTML
  rendering. `ClientReleaseStorage` remains the sole release SQL owner.
- The compatibility snapshots are unchanged: `GET
  /client/api/v1/release/current` is 599 bytes with `application/json` and
  SHA-256 `5e19bc98c09286a2eb8181650462cfb5ae6952eb342da080643d54a8ab6856af`;
  `GET /client` is 3156 bytes with `text/html; charset=utf-8` and SHA-256
  `017f19c4e4ebf5e98cb2c9493deec789a5bbf2107a39f6326c6d4fb8b0788e3d`.
- 325 focused tests and the 799-test full suite passed with one existing
  Starlette/HTTPX deprecation warning. No-mutation snapshots passed, and all
  18 release triggers remain present. The controlled Greptile finding was
  resolved; final Codex and Fresh Sol approvals were recorded.

No mobile application, client editing, real client information, Production
controls, authentication change, schema change, migration, trigger change, or
write path was added.

#### ACE iOS Read-Only Client Specification

On 24 August 2026, PR [#61](https://github.com/mcxl/agentic-os-workspace/pull/61)
merged exact head `c2f3de05fb317d15f563356aaf8305be25fe434e` as
`436fed942d1b45da7473f98930de11b33f861d13` at 11:04:09 UTC.

- The pull request added only
  `docs/specs/2026-08-24-ace-ios-read-only-client-application.md`.
- The independent Security review approved the exact Git blob
  `5e0df37037aef24bb55ef9cbafd670d601410de0`.
- A separate R3 Security review explicitly approved the clipboard and
  app-switcher controls in that exact blob. The independent quality gate passed
  at 10/10 after one verifier repair cycle. The approval record is in
  [MCX-15](https://linear.app/mcxi-co/issue/MCX-15/sqe-implement-ace-ios-read-only-client-application).
- `localOnly` limits Handoff to other devices. It is not a same-device
  confidentiality boundary. Approval applies to the eleven listed field types,
  not unknown future values or an unimplemented runtime. Implementation must
  prove the clipboard and app-switcher controls.
- The acceptance catalogue has 197 identifiers and 197 unique identifiers.
  It has no duplicates or sequence gaps. `IOS-AUTH-001` through
  `IOS-AUTH-070` are complete.
- The user approved the exact pull request head for merge.
- The available controlled record does not contain Pocock approval of the
  exact specification commit.
- Linear issue
  [MCX-15](https://linear.app/mcxi-co/issue/MCX-15/sqe-implement-ace-ios-read-only-client-application)
  records the implementation scope, tests, ten-working-day limit, exclusions,
  data controls, delivery workflow, and pending inputs. It remains `Todo` with
  `needs-info` and `ready-for-human`. It is not approved for implementation.
- The user confirmed an approved Mac on 24 August 2026. Exact Xcode 26 host
  evidence is due from Codemagic. iOS 26 simulator evidence is due from Revyl.
- PR [#62](https://github.com/mcxl/agentic-os-workspace/pull/62) records the
  final specification delivery state on branch `codex/ios-spec-state-sync`.
- After provider approval, Codemagic receives only the approved private source.
  It performs Xcode 26 builds and automated tests.
- Revyl receives only the compiled simulator `.app`. It provides iOS 26
  simulator evidence.
- Final device evidence uses the approved Mac and an iPhone 15 Pro or later.
- Sift-KG and OpenViking remain separate fictional-data pilots. They are not
  build dependencies.
- Do not transfer personal information, client evidence, passwords,
  certificates, Production credentials, or usable tokens to these providers.

PR [#62](https://github.com/mcxl/agentic-os-workspace/pull/62) now records the
final specification artifact:

- File SHA-256:
  `15B65ECE3306E6D6918A2233001CE534A64590E9F9B3464BBA0DACA997639943`.
- Git blob: `a60efb08bdf4056bddab837f1e0f831fe8f273c6`.
- Independent Pocock review: `APPROVED`, with no remaining findings after one
  repair cycle.
- Independent Security review: `APPROVED`, with no findings against the final
  artifact.
- Catalogue: 197 identifiers, 197 unique identifiers, no duplicates, no
  sequence gaps, and complete `IOS-AUTH-001` through `IOS-AUTH-070`.
- The final commit identity remains part of the PR #62 commit-and-push check.

This specification does not authorise implementation. Security has approved
the Keychain, clipboard, and app-switcher specification controls. Security and
ACE operations must approve the private test server and certificate. The
bundle identifier, signing team, signed entitlements, Xcode 26, and iOS 26
simulator remain required inputs.

### Phase 6 Status: COMPLETE

All approved implementation and documentation pull requests were merged at
their approved exact heads. The authoritative Phase 6 completion criteria are
satisfied.

## Next Goal

Record the final PR #62 commit, then obtain user approval. Approve MCX-15 before
implementation. Approve Codemagic before private-source transfer. Approve Revyl
before compiled-application transfer. Approve the private test server and
certificate before network testing. Approve the exact bundle identifier, signing
team, and entitlements before a physical-device build. Record exact Xcode 26 host
evidence from Codemagic and iOS 26 simulator evidence from Revyl. After
implementation, use the approved Mac and an iPhone 15 Pro or later model for final
device evidence. Keep fictional-only data, G0, no client editing, and no Production
controls unless new approval changes these decisions.
