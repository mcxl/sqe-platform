# Snapshot Reconciliation

This is a file comparison, not resolution of the outstanding behaviour or ancestry decisions.

GitHub base: `7da6228dc87ad970aa8d44365fbc3823c58020da`. Windows base: `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a` plus working files.

Line endings are normalised only for the comparison. Source export hashes preserve original bytes.

| Local File | Compared With GitHub Main |
|---|---|
| `.gitignore` | different |
| `.graphifyignore` | local-only |
| `.understandignore` | local-only |
| `ACE_PROGRESS_GUIDE.html` | different |
| `AGENTS.md` | different |
| `DEV_STATE.md` | different |
| `README.md` | different |
| `SQE_DEVELOPER_HUB.html` | local-only |
| `WORKSPACE-GUIDE.md` | local-only |
| `docs/ace/2026-09-16-ace-ios-swift-completion-instruction.md` | local-only |
| `docs/ace/2026-09-17-ace-ios-copy-reflow-check-instruction.md` | local-only |
| `docs/ace/CODE-AND-EVIDENCE-INDEX.md` | local-only |
| `docs/ace/REPOSITORY-MAP-SETUP.md` | local-only |
| `docs/plans/2026-09-14-ace-ios-local-verification.md` | local-only |
| `docs/plans/2026-09-17-ace-ios-discovery-candidate.md` | local-only |
| `docs/plans/2026-09-18-sqe-consolidation-web-showcase-plan.md` | local-only |
| `docs/plans/2026-09-18-sqe-stage-3-execution-proposal.md` | local-only |
| `docs/plans/2026-09-18-sqe-stage-4-execution-proposal.md` | local-only |
| `docs/specs/2026-08-24-ace-ios-read-only-client-application.md` | different |
| `ios/ACEClientApp/ACEClientApp.xcodeproj/xcshareddata/xcschemes/ACEClientAppUITests.xcscheme` | different |
| `ios/ACEClientApp/ACEClientApp/ACEClientAppApp.swift` | different |
| `ios/ACEClientApp/ACEClientApp/DebugScenario.swift` | different |
| `ios/ACEClientApp/ACEClientApp/Views.swift` | different |
| `ios/ACEClientApp/ACEClientAppTests/ACEClientAppTests.swift` | different |
| `ios/ACEClientApp/ACEClientAppTests/AcceptanceEvidenceContractTests.swift` | different |
| `ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift` | different |
| `ios/ACEClientApp/Phase6_1EvidenceRegister.json` | different |
| `ios/ACEClientApp/Phase6_1EvidenceRegister.md` | different |
| `ios/ACEClientApp/RuntimeEvidencePlan.json` | different |
| `ios/ACEClientApp/RuntimeEvidencePlan.md` | different |
| `ios/ACEClientApp/evidence-matrix-audit.md` | different |
| `security/deepsec/results/pr-26/PILOT_RESULT.json` | local-only |
| `security/deepsec/results/pr-26/SUMMARY.md` | local-only |
| `security/deepsec/results/pr-26/findings.json` | local-only |
| `src/ace/domain/assessment.py` | different |
| `src/ace/engine/approval.py` | different |
| `src/ace/workbench/document_toolchain_doctor.py` | different |
| `src/ace/workbench/export_builder.py` | different |
| `src/ace/workbench/relationship_review_storage.py` | different |
| `tests/test_approval_gate.py` | different |
| `tests/test_change_export.py` | different |
| `tests/test_ios_accessibility_layout.py` | local-only |
| `tests/test_ios_action_targets.py` | local-only |
| `tests/test_planning_trace.py` | different |
| `tests/test_relationship_review.py` | different |
| `tests/test_workbench.py` | different |
| `tools/ace_ios_local.py` | local-only |
| `tools/tests/test_ace_ios_local.py` | local-only |

## Main Files Not In The Windows Snapshot

These remain in the unchanged parent commit; their absence is deliberate snapshot scope, not an approved deletion from main.

- `.github/workflows/quality-gates.yml`
- `.github/workflows/release-quality.yml`
- `ACE_VISION_AND_ROADMAP.md`
- `CONTEXT.md`
- `WORKFLOW-NOTES.md`
- `codemagic.yaml`
- `docs/DOCUMENTATION-INVENTORY.md`
- `docs/adr/0001-human-auditor-controls-final-decisions.md`
- `docs/adr/0002-g0-protects-the-data-boundary.md`
- `docs/adr/0003-approved-records-use-versioned-history.md`
- `docs/adr/0004-release-projection-is-read-only.md`
- `docs/agents/domain.md`
- `docs/agents/triage-labels.md`
- `docs/diagrams/README.md`
- `docs/diagrams/controlled/mermaid/approval-review-states.mmd`
- `docs/diagrams/controlled/mermaid/auditor-workflow.mmd`
- `docs/diagrams/controlled/mermaid/evidence-relationship-map.mmd`
- `docs/diagrams/diagram-manifest.json`
- `docs/specs/documentation-control.md`
- `ios/ACEClientApp/Makefile`
- `quality/test-groups.json`
- `tests/test_quality_gates_workflow.py`
- `tests/test_run_tests.py`
- `tools/run_tests.py`
- `workflows/conclusion-review.md`
- `workflows/engagement-setup.md`
- `workflows/evidence-review.md`
- `workflows/field-evidence-capture.md`
- `workflows/mate-assessment.md`
- `workflows/relationship-review.md`
