# SQE Developer Roadmap

## Start Here

This is the developer entry point for the whole SQE platform, current work, and dependent steps.
Open the [Development Hub](SQE_DEVELOPER_HUB.html). Whole Picture is the default view, followed by Development State, Milestones, and Evidence And Updates.
This file remains the planning source. Linear supplies issue status, owner, and due date. DEV_STATE.md supplies technical result history.
It expands the [Platform Vision](ACE_VISION_AND_ROADMAP.md). The identifiers below are local roadmap identifiers, not new tracker issues.
The sequence is proposed planning. It does not grant implementation, paid-run, merge, or release approval.

Evidence update: 9 September 2026, from the [M4 Native Run Report](../Codex/2026-09-08/mcx19-functional-accessibility/M4-NATIVE-RUN.md).
MCX19-A is Done at 3259048186916941bf3557d55503e7375e432c57. The M4 run finished in 7m 54s: three native tests passed, none failed or skipped, and no accessibility issues were reported.
At 3259048: 12 focused checks passed; full local suite 901 passed, one platform skip, one existing warning. GitHub Quality Gates 34220925126 passed.
Estimated cost: US$0.9006 (about US$0.90) before tax and billing rounding. Actual charge is unconfirmed. David was updated; support follow-up is paused. The separate M2 queue is not confirmed resolved.
UNVERIFIED — UI QA INCOMPLETE: screenshots, dark mode, large Dynamic Type, and normal device-setting behaviour remain unverified for this candidate.
Source-code links retain the earlier 838ae6a snapshot. M4 results apply only to 3259048.

The full Linear snapshot dates from 8 September 2026. MCX-19 was rechecked on 9 September and remains In Progress. MCX-15 and MCX-19 are In Progress and assigned to Alan Richardson.
MCX-10 is Todo and has no assignee. All 17 returned SQE issues have no due date. Both returned projects have no target date.
Now, Next, and Later indicate order, not promised dates. Execution roles below do not create separate assignments.

## Whole Picture

The product goal is controlled auditor review with traceable evidence and human decisions.
The domain workflow is Engagement → Evidence → Relationship Review → MATE Assessment → Conclusion Review.
Client release and iOS delivery follow their separate specifications. The workflow is not one automatic approval process.
See [System Context](CONTEXT.md) and [Workflow Order](WORKFLOW-NOTES.md).

| Capability | Implementation Or Task State | Verification State | Sequence And Tracker |
|---|---|---|---|
| Platform And Delivery Controls | MCX-17 is Done and merged in Linear. MCX-18 and MCX-20–22 are also Done and merged. | Historical gate and merge evidence is recorded in MCX-17. This is not a current full-product test. | Delivered foundation; maintain. [MCX-17](https://linear.app/mcxi-co/issue/MCX-17/sqe-extract-sqe-platform-and-introduce-tiered-quality-gates). |
| Auditor Workbench | Domain workflows and workbench source are present. | End-to-end acceptance for the whole workbench was not assessed in this update. | Existing capability; preserve controls. No dedicated active workbench issue identified. |
| Client Release Service | MCX-12, MCX-13, and MCX-14 are Done and merged in Linear. | Historical release-view tests are recorded in MCX-12; current-head compatibility was not rerun. | Delivered foundation for clients. [MCX-12](https://linear.app/mcxi-co/issue/MCX-12/sqe-phase-6a-minimal-client-release-view). |
| iOS Read-Only Client | MCX19-A is Done at 3259048. Parent issues remain In Progress in the tracker snapshot. | Three native tests passed; no accessibility issues reported. Full visual QA remains incomplete. | Now: MCX19-B. Then MCX19-C. |
| Relationship Review Pilot | MCX-5, MCX-6, MCX-8, and MCX-11 are Done and merged. MCX-10 remains Todo. | Historical pilot delivery is recorded. The live Preview was not checked in this update. | Separate workstream. Reconcile [MCX-10](https://linear.app/mcxi-co/issue/MCX-10/sqe-decide-relationship-review-pilot-next-phase) before planning further work. |
| Future Retrieval And New Capabilities | Planned direction only. No implementation or active issue established for this scope. | Not assessed. | Later: approved fictional pilot and separate specification required. |

### Dependencies And Gates

- Linear records MCX-17 as a prerequisite for MCX-19. MCX-17 is Done; that prerequisite is satisfied in the tracker.
- MCX19-A → MCX19-B → MCX19-C is a proposed local milestone order within MCX-19, not three new Linear issues.
- The relationship pilot is a separate workstream. No Linear dependency on the iOS milestones was found in the inspected issues.
- Keep G0 and human decision controls active across all capabilities.
- New data boundaries, providers, schemas, security changes, or Production use need their applicable approval.
- Completing MCX-19 does not automatically approve client data, merge, an installable build, or Production release.

### Capability Locations And Reading Maps

| Capability | Where | How To Understand It |
|---|---|---|
| Platform | [Quality Gate Workflow](.github/workflows/quality-gates.yml), [Delivery Workflow](workflows/codex-autonomous-delivery.md) | Read MCX-17 and its recorded [GitHub Checks](https://github.com/mcxl/sqe-platform/actions/runs/33937548422). |
| Workbench | [Routes](src/ace/workbench/routes.py), [Storage](src/ace/workbench/storage.py), [Domain](src/ace/domain/) | Follow [Workflow Notes](WORKFLOW-NOTES.md). Use CodeGraph for exact symbols. The small Understand Anything pilot does not cover the full workbench. |
| Release | [Service](src/ace/workbench/client_release_service.py), [Projection](src/ace/workbench/client_release_projection.py), [Routes](src/ace/workbench/client_routes.py) | Understand Anything steps 2–3. [Service Boundary](docs/specs/phase6-stage1-release-service-boundary.md). |
| iOS | [App](ios/ACEClientApp/ACEClientApp/), [UI Tests](ios/ACEClientApp/ACEClientAppUITests/), [Diagnostic](tools/diagnose_ios.py) | Understand Anything steps 7–9 for session and transport. Views and tests need current source inspection. |
| Relationship Pilot | [Workbench](apps/relationship-review-pilot/components/relationship-review-workbench.tsx), [Queries](apps/relationship-review-pilot/convex/relationships.ts) | Understand Anything steps 4–6. [MCX-11](https://linear.app/mcxi-co/issue/MCX-11/sqe-reconcile-relationship-details-pilot-source). |
| Future Work | [Vision](ACE_VISION_AND_ROADMAP.md) | No implementation location or source-map coverage established. |

## Next Action

**Action:** Define the remaining MCX19-B visual checks for the exact candidate and obtain any required run approval.
**Owner:** Alan Richardson, from Linear MCX-19. **Due date:** Not set in Linear.
**Blocker:** Full visual QA remains incomplete. Screenshots, dark mode, large Dynamic Type, and normal device-setting behaviour need evidence.
**Approval:** The M4 one-run authority is spent. This records update does not authorise another paid run or merge.
**Completion:** Retain the required full candidate evidence before the MCX19-C readiness decision.

## Delivery Sequence

Shared Linear issue for MCX19-A, MCX19-B, and MCX19-C: [MCX-19 — Run Live iOS Evidence Before Leaving G0](https://linear.app/mcxi-co/issue/MCX-19/sqe-run-live-ios-evidence-before-leaving-g0).
These milestones are parts of that issue. They are not separate Linear issues.

**MCX19-A: Done → MCX19-B: Verify The Full Candidate → MCX19-C: Review Release Readiness**

### MCX19-A — Resolve Functional Evidence

- **What:** Establish the current functional and accessibility result. Resolve supported faults within an approved task scope.
- **Status:** Done. MCX19-A is Done at 3259048186916941bf3557d55503e7375e432c57. The M4 run finished in 7m 54s: three native tests passed, none failed or skipped, and no accessibility issues were reported.
- **Result:** [M4 Native Run Report](../Codex/2026-09-08/mcx19-functional-accessibility/M4-NATIVE-RUN.md). Estimated cost: US$0.9006 (about US$0.90) before tax and billing rounding. Actual charge is unconfirmed. David was updated; support follow-up is paused. The separate M2 queue is not confirmed resolved.
- **Where:** [Views.swift](ios/ACEClientApp/ACEClientApp/Views.swift), [UI Tests](ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift), and [Diagnostic Runner](tools/diagnose_ios.py).
- **When:** Completed on 8 September 2026 UTC, recorded on 9 September AEST.
- **Owner:** Alan Richardson, inherited from Linear MCX-19. The user controls further paid-run approval.
- **How:** Read the latest retained assertions and task result. Match each failure to its selector and exact commit. Use the smallest relevant check. Keep appearance, functional, and accessibility results separate.
- **Acceptance:** Record each in-scope selector outcome and its evidence. Verify any repair on its exact candidate. If evidence is missing, identify the exact missing result; do not mark this milestone complete.
- **Dependency:** Current task evidence and valid scope approval. The roadmap is not a replacement approval.
- **Task And Evidence:** [PR 6](https://github.com/mcxl/sqe-platform/pull/6), [State Record](DEV_STATE.md), [Historical Full-Run Result](https://github.com/mcxl/sqe-platform/pull/6#issuecomment-5570031930).
- **Code Map:** Understand Anything steps 7–8 explain session and transport context. Its 19-file pilot omits Views.swift and tests. Use current source and CodeGraph for those files.

### MCX19-B — Verify The Full Candidate

- **What:** Obtain the required complete iOS evidence after the focused faults are resolved.
- **Status:** Next. MCX19-A is complete. Full visual QA remains incomplete.
- **Where:** [Controlled Runner](tools/run_tests.py), [Runner Tests](tests/test_run_tests.py), [Codemagic Workflow](codemagic.yaml), and [iOS Specification](docs/specs/2026-08-24-ace-ios-read-only-client-application.md).
- **When:** After MCX19-A passes and a bounded validation run is authorised. Target date unassigned.
- **Owner:** Alan Richardson, inherited from Linear MCX-19. Developer collects evidence; user approves any new paid run.
- **How:** Confirm the exact head, required gates, current test inventory, run scope, and capacity. Execute only the approved validation. Retain separate command outcomes and required artifact checks.
- **Acceptance:** The required candidate checks pass with retained evidence. Record normal device-setting behaviour separately. A focused appearance pass or an incomplete progress report is insufficient.
- **Dependency:** MCX19-A, current acceptance requirements, and applicable run approval. The linked specification is marked draft; reconcile it with approved task decisions.
- **Task And Evidence:** [PR 6](https://github.com/mcxl/sqe-platform/pull/6) and [State Record](DEV_STATE.md).
- **Code Map:** Understand Anything steps 2–3 and 7–9 explain Python release and Swift request paths. The Swift/Python connection is inferred from matching paths, not a proven live connection.

### MCX19-C — Review Release Readiness

- **What:** Present the exact candidate evidence for a human readiness decision.
- **Status:** Blocked by MCX19-B. G0 remains in force. No merge approval is recorded here.
- **Where:** [PR 6](https://github.com/mcxl/sqe-platform/pull/6), [State Record](DEV_STATE.md), [Delivery Workflow](workflows/codex-autonomous-delivery.md), and [Decision Authority](docs/adr/0001-human-auditor-controls-final-decisions.md).
- **When:** After MCX19-B passes and required reviews are complete. Target date unassigned.
- **Owner:** Alan Richardson, inherited from Linear MCX-19. Developer prepares evidence; the authorised human makes the decision.
- **How:** Reconcile the head, tests, reviews, unresolved limits, and approvals. Present the exact-head decision. Keep installable-build and Production decisions separate.
- **Acceptance:** A recorded decision identifies the exact head and allowed next action. A changed head needs a new decision. No automatic merge or Production action follows from this roadmap.
- **Dependency:** MCX19-B and required independent reviews.
- **Code Map:** Use the source maps to explain scope. Maps do not establish readiness.

## Later — Screenshot And Recording Presentation

- **What:** Evaluate [frames-cli](https://github.com/viticci/frames-cli) for adding Apple device frames to existing SQE screenshots and recordings.
- **Status:** Planned. Start after MCX19-B verification; this task does not block MCX19-C.
- **Purpose:** Prepare demonstration images, side-by-side screen comparisons, and release presentation material.
- **Scope:** Use copies of approved fictional screenshots or recordings. Keep original diagnostic evidence unchanged.
- **Acceptance:** Produce one framed image and one side-by-side comparison from verified captures. Confirm readable content and retain links to the originals.
- **Limits:** This tool does not build the app, run UI tests, diagnose accessibility failures, or replace CI artifact retention.
- **Approval:** Roadmap entry only. Installation, implementation, and publication require their applicable approval.

## Supporting Maps

- [Understand Anything Pilot Guide](../Codex/2026-09-08/sqe-understand-pilot/README.md): source explanations, nine tour steps, restart instructions in the completion receipt.
- [Understand Anything Completion And Restart](../Codex/2026-09-08/sqe-understand-pilot/COMPLETION.md): the pilot snapshot is at `b6eabcd`; it omits later changes.
- [Archify Build Map](../Codex/2026-09-08/ace-build-visuals/ace-build-archify.html): retained build sequence at `b6eabcd`; use as historical context.
- [Archify Editable Source](../Codex/2026-09-08/ace-build-visuals/ace-build.workflow.json): this roadmap maps its functional, matrix, and approval stages to A, B, and C.
- CodeGraph: run `codegraph explore "<file or symbol>"` from this repository. Check freshness before relying on results. The index is a navigation aid, not test evidence.

## Maintenance

### Changes In This Update

- Recorded MCX19-A as Done from the M4 run report at 3259048.
- Advanced the next action to MCX19-B and retained incomplete visual QA.
- Recorded the cost estimate, unconfirmed charge, David update, and paused support checks.

### Earlier Hub Changes — 8 September 2026

- Added the Whole Picture view, six capability areas, and explicit dependency types.
- Added Linear owner and date snapshots, plus separate implementation and verification fields.
- Added one next action, freshness details, and evidence links for each milestone.
- Added wider issue coverage, including completed work, the open relationship decision, and cancelled MCX-9.
- Recorded source conflicts rather than resolving them through assumptions. No new application test result is claimed.

### Source Limits

The two Linear projects report Backlog even though their issues include Done and In Progress. Use issue-level states for this view.
MCX-15 still says Planning only in its description, while its structured state is In Progress. It needs record reconciliation.
MCX-10 contains approved decisions but remains Todo. Related completed issues do not authorise marking MCX-10 Done.
The M4 run report supersedes earlier diagnostic status. MCX-19 remains In Progress in the live tracker check.
M4 results apply only to 3259048. This update does not establish results for later source changes.
GitHub and Codemagic evidence links were retained from records; their live status was not refreshed.

Keep milestone scope, dependencies, and acceptance criteria in this file. Keep execution history and verified results in DEV_STATE.md.
After a work chunk, reconcile both records with exact-head evidence. Refresh the visual from this roadmap.
Refresh source maps when relevant source changes. Keep snapshot dates visible. Do not copy old pass results onto a new head.
The current roadmap visual is a manual snapshot. No automatic refresh, provider polling, or task assignment is configured.
