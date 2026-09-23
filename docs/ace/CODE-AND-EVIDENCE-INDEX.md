# SQE Code And Evidence Index

Updated 23 September 2026. Internal navigation and provenance record, not a release certificate.

## Current Decision

The owner requests independent investigation of mobile alternatives and web/mobile sequencing. The [complete Vortex brief](LOCAL_HOME/sqe-private/handoffs/2026-09-23-vortex-full-review-brief.md) contains the full instructions and evidence background. It has not been sent to Vortex. No verdict, rewrite or migration is assumed.

## Repository And Candidate Identities

| Identifier | Meaning | Standing |
|---|---|---|
| `https://github.com/mcxl/sqe-platform.git` | Separate SQE origin remote | Confirmed from local Git configuration; remote contents not refreshed |
| `LOCAL_HOME\Documents\sqe-platform` | Main Windows consolidation workspace | Current local working folder; contains modified and untracked work |
| `codex/sqe-workspace-consolidation` | Windows branch | Checked September 23 |
| `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a` | Windows HEAD | August 25 commit; does not include all imported September files |
| `LOCAL_HOME\Documents\agentic-os-workspace\sqe` | Older SQE folder inside parent monorepo | Preserve; not a second authoritative current workspace |
| `LOCAL_HOME\Documents\sqe-platform-public-clean` | Older separate checkout | Preserved; its hub links to the current workspace |
| `LOCAL_HOME/Developer/sqe-platform-release-layout` | Recorded Mac delivery worktree | Current access and HEAD not checked in this update |
| `40bae2640b23eb05496a093d09a4c20186403879` | Mac candidate checked during consolidation | Historical identity; not asserted as current HEAD |
| `8a06ae2756fa7034091937828667d3fd0c6210c1` | Public Zauner Site source, version 3 | Separate static presentation source, not an SQE release |

## Code Locations

All application paths below are under `LOCAL_HOME\Documents\sqe-platform`. Presence in this table means inspected source exists, not that current runtime acceptance passed.

| Capability | File Or Symbol | Boundary |
|---|---|---|
| Python application | `src/ace/app.py` | FastAPI application and route registration |
| Engagements, capture and review pages | `src/ace/workbench/routes.py` | Authenticated auditor routes, including write operations |
| Evidence review | `src/ace/workbench/evidence_review.py` / `EvidenceReviewService` | Context, questions, decisions and completion |
| MATE approval | `src/ace/engine/approval.py` / `evaluate_approved_assessment` | Approved inputs before rating |
| Rating rules | `src/ace/engine/evaluator.py` / `evaluate_control` | Deterministic control-design rating |
| Planning trace | `src/ace/engine/tracing.py` | Approved obligation/risk/control/role connections |
| Relationship review | `src/ace/workbench/relationship_review.py` / `RelationshipReviewService` | Review decisions and accepted-trace coordination |
| Client release lifecycle | `src/ace/workbench/client_release_service.py` / `ClientReleaseService` | Draft, validate, publish, withdraw, current release and history |
| Client projection | `src/ace/workbench/client_release_projection.py` | Transport-neutral release response |
| Client web/API | `src/ace/workbench/client_routes.py` | Read-only `/client` and `/client/api/v1/release/current` |
| Next.js pilot | `apps/relationship-review-pilot/` | Narrow read-only Convex relationship-review pilot |
| Swift networking | `ios/ACEClientApp/ACEClientApp/Network.swift` / `HTTPCurrentReleaseRepository` | Reads the configured release endpoint |
| Swift session and views | `ios/ACEClientApp/ACEClientApp/SessionState.swift`, `Views.swift` | Session handling and release presentation |
| Swift credential handling | `ios/ACEClientApp/ACEClientApp/KeychainStore.swift` | Native Keychain implementation; signed-device acceptance remains distinct |
| Native local runner | `tools/ace_ios_local.py` | Imported Mac runner; Windows import does not prove native execution |

## Existing Verification References

- `tests/test_evidence_review.py::test_full_record_review_flow_capture_to_completion` exercises capture through controlled review completion.
- `tests/test_approval_gate.py` and `tests/test_planning_trace.py` cover approval and trace rules.
- `tests/test_client_release.py` and `tests/test_client_release_projection.py` cover release lifecycle, integrity and output.
- [September 19 verification](LOCAL_HOME/sqe-private/consolidation-20260918/stage4/STAGE-4-VERIFICATION-REPORT.md): startup, seven selected tests and HTTP viewing checks passed; complete browser/write journey not accepted.
- [Source-version follow-up](LOCAL_HOME/sqe-private/consolidation-20260918/stage4/followup-20260919/FOLLOWUP-REPORT.md): populated source version verified over HTTP; browser rendering unverified.
- [Zauner presentation verification](LOCAL_HOME/sqe-private/zauner-example-20260919/correspondence/CONVERSATION-LAYOUT-20260923.md): 21 focused checks, fresh review and native publication success; not browser or SQE operational acceptance.

Historical counts in DEV_STATE.md apply to their recorded revisions. No full application or native suite was rerun for this documentation update.

## Native Instructions And Evidence

The approved instructions remain unchanged. Their hashes were checked on September 23:

| Record | SHA-256 |
|---|---|
| `docs/ace/2026-09-16-ace-ios-swift-completion-instruction.md` | `252aab6ba1115b72f1fcbd84c3d49f3429550c0845d96c2008088d15bdbbe629` |
| `docs/ace/2026-09-17-ace-ios-copy-reflow-check-instruction.md` | `f7147730b09e0b4daf5d18090abc29d38f780962479dc55a49631af20c1f2179` |

The owner subsequently reopened alternatives for investigation. Those approved diagnostic documents remain evidence of earlier execution authority; their hashes were not changed to reflect a new product decision.

Native evidence root: `LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915`.

D1 disposition: `08-copy-confirmation-diagnosis/discriminating-diagnostic-result.json` under that root. P0 runner record: `13-p0-discovery-runner-20260917`.

Unresolved: Copy root cause, latest D2 outcome not inspected here, acceptance coverage, physical/device checks, service readiness and historical ancestry. Recorded signing expired September 21; renewal is unknown.

## Architecture And Code Maps

September 23 generation update: Graphify 0.9.13, Understand Anything 2.9.7 and CodeGraph 1.1.1 have generated maps for the main repository.
See [Repository Map Setup](LOCAL_HOME/Documents/sqe-platform/docs/ace/REPOSITORY-MAP-SETUP.md).
Use the [Hub's Repository Maps section](../../SQE_DEVELOPER_HUB.html#repository-maps) for current links and freshness information.
Graphify and Understand Anything include tests and development records. CodeGraph indexes supported code formats, including tests.
Use the linked validation records to check each source snapshot. Historical map limitations below remain.

| Map | Location | What It Can Establish |
|---|---|---|
| ACE System Atlas | `LOCAL_HOME\Documents\agentic-os-workspace\sqe\docs\ace\atlas` | Historical architecture illustration. Source is `data.mjs`; `SYSTEM.md` and `atlas.html` are generated. Its historical client-view description is superseded by August implementation. |
| Understand Anything runtime map | `LOCAL_HOME\OneDrive - AuditCo\Documents\MCX19B-FABLE-REVIEW\ACE-IOS-CODE-MAP-20260916.json` | Navigation snapshot identified by Revision 5 as runtime files at `52b212a`. UI tests are excluded; it cannot prove the failure mechanism. Not regenerated. |
| Map explanations | `LOCAL_HOME\OneDrive - AuditCo\Documents\MCX19B-FABLE-REVIEW\ACE-IOS-CODE-EXPLANATIONS-20260916.md` | Supporting historical navigation, not current behaviour or acceptance. Not regenerated. |
| Archify | `LOCAL_HOME\.codex\skills\archify\SKILL.md`; upstream `https://github.com/tt-a1i/archify` | Diagram-authoring skill, separately identified on September 23. Not the historical Code Atlas; setup is not a generated SQE diagram. |
| CodeGraph | `LOCAL_HOME\Documents\sqe-platform\.codegraph\codegraph.db` | September 23 index: 91 code files. Symbols and relationships; not runtime acceptance. |
| Understand Anything current map | `LOCAL_HOME\Documents\sqe-platform\.ua\knowledge-graph.json` | September 23 snapshot: 145 files, architecture layers and guided tour. |
| Graphify current map | `LOCAL_HOME\Documents\sqe-platform\graphify-out\graph.html` | September 23 snapshot: code and document relationships. Coverage limitations are linked from the Hub. |

Source beats maps. Retained native results beat summaries. A map update is not application verification.

## Publication And Data Boundaries

Zauner is the approved sample engagement. The public showcase is at https://zauner-ims-review.alan-richardson.chatgpt.site/ and its source is at `LOCAL_HOME\sqe-private\zauner-example-20260919\public-site`.

It presents supplied evidence and historical report outcomes. It does not submit RFIs, record operational replies or update the ACE database. Current operational data controls are unchanged. Internal navigation, evidence paths and signing material are not public-site content.

## Update Limits

This record, the hub and current documentation were updated for transparency. Historical records are labelled, not rewritten as current passes. Existing application code, approved instructions and source maps retain their identities. No commit, push, deployment or automatic task dispatch is part of this update.
