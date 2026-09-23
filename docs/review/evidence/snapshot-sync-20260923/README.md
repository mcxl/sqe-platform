# Snapshot Sync: Restore Main's Approval And G0 Gates On The Review Snapshot Branch

Date: 2026-09-23 (UTC). Branch: `vorflux/snapshot-sync-main-gates` from review commit
`cc05ca085e2b3d1e374c13f503bd35e280ba859f` (`codex/vorflux-review-20260923`). Main
(`7da6228dc87ad970aa8d44365fbc3823c58020da`) is untouched. Push and pull request status is
recorded under Branch And Commits.

## Outcome

**Complete for the approved scope.** Both Codex findings reproduce on the snapshot and are
refused on this branch. The branch's Python code now differs from main only by the snapshot's
own four iOS files, the deferred test-runner and CI set, and one new regression test file.
The full suite shows the same four pre-existing iOS test failures before and after; no test
changed state.

Fictional data only (G0). No credentials are stored in this folder.

## Purpose

An external Codex review of pull request 7 raised two P1 findings against files that pull
request did not touch:

1. `src/ace/engine/approval.py`: a hand-built `ApprovedMATEAssessment` (via `model_construct`
   or `model_copy`) passed `evaluate_approved_assessment` without `ApprovalBlockedError`.
2. `src/ace/workbench/relationship_review_storage.py`: the loader read only `snapshot_json` and
   trusted a G0 seed row whose `created_at` or `created_by` had been altered.

Cause: the snapshot's `src` and `tests` equal main's first commit `1084f13` (2026-09-04) plus
four iOS files. Main closed both gaps on 2026-09-04 and 2026-09-05 (`eaa383f`, `6dbf804`,
`38c1790`, `a40d34b`, `25a3035`, pull request 2). This task copies that content forward.
Main is the source because it holds the later, reviewed and merged versions.

## What Changed

| Commit | Files | Change |
|---|---|---|
| `46cfb42` | `baseline/*`, `scripts/*` | Baseline full test run and two disposable probes that demonstrate each finding on `cc05ca0`. |
| `faa1774` | `src/ace/domain/assessment.py`, `src/ace/engine/approval.py`, `src/ace/workbench/relationship_review_storage.py`, `src/ace/workbench/document_toolchain_doctor.py`, `src/ace/workbench/export_builder.py`, `tests/test_approval_gate.py`, `tests/test_change_export.py`, `tests/test_planning_trace.py`, `tests/test_relationship_review.py`, `tests/test_workbench.py` | Main's versions, content identical (`git diff --ignore-all-space` against main is empty for each file), line endings converted to the snapshot's CRLF. 665 insertions, 41 deletions. Also carries main's Windows `soffice.com` probe fix, which travels with the same test files. |
| `7ed849f` | `docs/adr/0001` to `0004` | Main's four architecture decision records, byte-identical to main. |
| `2f341d3` | `tests/test_g0_snapshot_metadata.py` | New file (LF, like the snapshot's other new test files). Two tests: altered `created_at` and altered `created_by` each make the loader return `None` and make completing approval answer `RELATIONSHIP_MATE_REQUIRED`. Main has no equivalent test. |

Not changed: `docs/review/**` (except this folder), `AGENTS.md`, `README.md`, `DEV_STATE.md`,
`ios/**`, `pyproject.toml`, `uv.lock`, the three files pull request 7 edits, and every
line-ending-only difference between main and the snapshot.

## Results

| Check | Baseline (`cc05ca0`) | After (`2f341d3`) | Evidence |
|---|---|---|---|
| Full `pytest` | 804 collected, 800 passed, 4 failed | 824 collected, 820 passed, 4 failed (same four) | `baseline/pytest-baseline.txt`, `after/pytest-after.txt` |
| The 4 failures | `tests/test_ios_accessibility_layout.py` (2), `tests/test_ios_action_targets.py` (2): snapshot-only tests that read `ios/**` Swift files which no longer match | Unchanged | Same files |
| `tests/test_approval_gate.py` | 40 functions, 64 items | 55 functions, 80 passed | `after/pytest-approval-gate.txt` |
| Focused Set 1 files | not run | 276 passed | `after/pytest-set1-focused.txt` |
| Probe 1: forged `model_construct` assessment | `forged assessment evaluated: EvaluationResult` | `forged assessment blocked: Evaluation blocked: approved assessment invariants are invalid.` | `baseline/probe-finding-1.txt`, `after/probe-finding-1.txt` |
| Probe 2: seed row with altered `created_at` | `tampered row loaded: True` | `tampered row loaded: False` | `baseline/probe-finding-2.txt`, `after/probe-finding-2.txt` |
| New regression test | 2 failed against a `cc05ca0` export | 2 passed | `after/pytest-g0-metadata-on-snapshot.txt`, `after/pytest-g0-metadata-on-branch.txt` |
| Whitespace-insensitive diff against main (`src tests tools quality .github docs/adr`) | 10 changed, 6 deleted, 4 snapshot-only | Only: 6 deferred Set 2 files (deleted), 4 snapshot-only iOS files, `tests/test_g0_snapshot_metadata.py` | `after/diff-vs-main-stat.txt` |
| Diff against the snapshot | | 15 files, 770 insertions, 41 deletions | `after/diff-vs-snapshot-stat.txt` |
| Line endings of replaced files | CRLF | CRLF on all 10 replaced files; the new test file is LF | `after/line-endings.txt` |
| Overlap with pull request 7 file list | | Empty | `after/pr7-overlap.txt` |
| `uv.lock`, `pyproject.toml` | | Not modified | `git status` clean before each commit |

Every probe prints `code under test:` and shows this worktree's path, because the shared
`.venv` editable install would otherwise import the pull request 7 checkout.

## Branch And Commits

```
2f341d3 Add G0 seed metadata regression tests
7ed849f Restore the four architecture decision records
faa1774 Restore main's MATE approval boundary and G0 seed verification
46cfb42 Record snapshot baseline test run and finding probes
```

A fifth commit records this README and `commands.md`. Blob hashes on the final head:
`src/ace/engine/approval.py` `f876d7f79b4791e65ece0f39fd84e6a8d6d2403e`,
`src/ace/workbench/relationship_review_storage.py` `e141c8b409a98da22f95e87d7f8b8a4496f4ff60`
(CRLF versions; whitespace-insensitive content equals main).

Work ran in a separate `git worktree` at `/code/mcxl/sqe-platform-sync`, so the pull request 7
checkout was never modified. Push and pull request creation require user approval and are
recorded in `commands.md` when they happen.

## Review Record

Roles per AGENTS.md "Implementation And Review Roles":

| Role | Identity | Outcome |
|---|---|---|
| Implementation owner | Vorflux agent, session `fcbc5fd9-1849-448d-bad3-98848678b555` | Four commits plus this record |
| Independent standards reviewer | Vorflux review subagent (same session) | Recorded below when complete |
| Exact-candidate final reviewer | Vorflux review subagent (same session) | Recorded below when complete |

## Human Decisions Recorded

The user approved the plan "Restore Main Safety Gates On The Review Snapshot Branch" with the
recommended options:

- D1: defer the test runner and CI set (`tools/run_tests.py`, `tests/test_run_tests.py`,
  `tests/test_quality_gates_workflow.py`, `quality/test-groups.json`,
  `.github/workflows/quality-gates.yml`, `.github/workflows/release-quality.yml`).
- D2: keep the finding 2 probe as a permanent test file.
- D3: defer the other missing documents.
- D4: open the pull request in parallel with pull request 7.
- D5: hard time limit 90 minutes.

## Follow-Ups

- Set 2, test runner and CI. Main's `tests/test_run_tests.py` fails 8 of 31 on the snapshot
  because it reads `ios/ACEClientApp/Makefile` (absent) and asserts on
  `ACEClientAppUITests.xcscheme`, `RuntimeEvidencePlan.json` and `Phase6_1EvidenceRegister.json`,
  which differ on the snapshot. Restore this set after the iOS files are reconciled.
- The four pre-existing failures in `tests/test_ios_accessibility_layout.py` and
  `tests/test_ios_action_targets.py`. They belong to the snapshot's iOS work, not to this task.
- Deferred documents: `workflows/{conclusion-review,engagement-setup,evidence-review,field-evidence-capture,mate-assessment,relationship-review}.md`,
  `CONTEXT.md`, `docs/agents/domain.md`, `docs/agents/triage-labels.md`,
  `ACE_VISION_AND_ROADMAP.md`, `WORKFLOW-NOTES.md`, `codemagic.yaml`,
  `docs/DOCUMENTATION-INVENTORY.md`, `docs/diagrams/**`, `docs/specs/documentation-control.md`.
- The ancestry decision: whether `codex/vorflux-review-20260923` or `main` carries the project.
- Port `tests/test_g0_snapshot_metadata.py` to main if wanted.

## What This Does Not Prove

- That the snapshot branch descends from, or should replace, main. `docs/review/RECONCILIATION.md`
  leaves that open and this task does not close it.
- That the two CI workflows run. They trigger only on `main`, `codex/sqe-pivot-integration` and
  pull requests to `main`, and they are not on this branch.
- That the snapshot's iOS files satisfy main's runner contracts (8 tests show they do not) or
  the snapshot's own iOS tests (4 fail before and after).
- That the remaining differences in `AGENTS.md`, `README.md`, `DEV_STATE.md`, `ios/**` and the
  deferred documents are intended. They are untouched.
- Protection against hostile code inside the same Python process. Main's own docstring says the
  approval boundary binds issued objects to content and is not a process-isolation control.

## Cleanup

- Temporary export `/var/tmp/snapbase` deleted after the regression test check.
- The worktree `/code/mcxl/sqe-platform-sync` is removed after the pull request opens.
- No temporary data directories remain; both probes use `tempfile.TemporaryDirectory`.
