# SQE Stage 4 Execution Proposal

**Date:** 18 September 2026
**Status:** Prepared following “proceed”. Execution approval pending for the environment setup and bounded verification below.
**Result:** Establish whether one existing Python viewing journey works with isolated fictional data.

## Baseline And Preparation Findings

Workspace: `LOCAL_HOME\Documents\sqe-platform`.

Branch: `codex/sqe-workspace-consolidation`.

HEAD: `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a`.

Stage 3 imports and documentation remain uncommitted. Record source hashes and dirty status; HEAD alone does not identify this workspace.
Keep the held Mac Python changes outside this task.

Read-only preparation confirmed:

- All three routes and their fictional seed records exist.
- Existing tests use `ACE_DATA_DIR` outside the repository and a fictional auditor password.
- Python 3.14.5 and uv are available. Record uv's version before use.
- Global pytest is 9.1.1; the project requires `>=8.0,<9.0`. The lock records 8.4.2.
- `uv.lock` omits declared `openpyxl`, `python-docx` and `reportlab` dependencies. It cannot establish a complete locked installation.
- ReportLab is absent from the global environment. No installation has been attempted.
- C: had 11,194,138,624 free bytes, approximately 10.43 GiB, during preparation. Recheck before writes.

These are environment findings, not application test failures.

## Scope And Limits

Planning allowance: 15–25 active minutes for checks and reporting after environment setup succeeds.
Dependency download, resolution and browser access remain unestimated.
Hard limit: 60 elapsed minutes from execution start, including setup and waiting.

Permitted repository changes: this proposal only. Do not change application code, existing tests, dependencies, locks or configuration.
Use temporary verification scripts and isolated environments under:

`LOCAL_HOME\sqe-private\consolidation-20260918\stage4`

Allow at most 2 GiB of new environment, cache and evidence data. Preserve at least 2 GiB free on C:.
Stop before exceeding either limit. Delete no existing work.

Approval covers installing the project's already-declared dependencies into a private environment.
Use the existing lock versions as constraints wherever applicable. Resolve omitted declared packages within their existing version ranges.
Retain the exact resolved versions and installation output. Do not modify the repository lock or global Python environment.
Do not claim reproducibility from the stale lock. Treat dependency reconciliation as a separate outstanding deliverable.
If resolution requires changing declared ranges or adding dependency names, stop environment setup and report the conflict.

Exclude Mac/iOS tests, live databases, Convex connections, deployment, write-workflow testing, code corrections, commits and pushes.
Do not introduce Atomic, EVE, a new runner framework or another tooling trial for this verification task.

## Execution

1. Record time, free space, tools, revision, working-tree hashes and the exact selected test list.
2. Create the private environment and retain its resolved package inventory.
3. Set isolated data and fictional credentials before importing the application.
4. Confirm the application imports and its local health request completes.
5. Run one temporary deliberately failing assertion against the Engagement response. Expect an intentionally incorrect engagement identifier.
6. Retrieve its native failure, expected and actual values, exit code and JUnit record.
7. Correct only that temporary expectation. Require the same test to pass with retained evidence.
8. Run the focused existing checks listed below once. Retain logs, counts, exit code and JUnit results.
9. Start the existing app on loopback only, using a fresh isolated fictional store.
10. Inspect the three viewing steps and their GET responses. Save page, state and request evidence.
11. Stop the task-owned server. Record results and verify application hashes remain unchanged.

Use a process-scoped `ACE_DATA_DIR` under the evidence root, never the default application database.
Use `PYTHONDONTWRITEBYTECODE=1` and disable pytest cache and automatic third-party plugin loading.
Place pytest temporary files outside the repository. Give each run a new path.

Proposed startup command, after recording the selected available loopback port:

```powershell
<private-environment>\Scripts\python.exe -B -m uvicorn src.ace.app:app --host 127.0.0.1 --port <selected-port>
```

Launch any background helper with a hidden window. Record its PID and stop only that task-owned process.

The earlier browser policy rejection concerned the local developer-hub file.
Do not serve that file through this application or use an alternative route to bypass the rejection.
Browser access to the operational app is a separate check. If rejected, stop browser work and report visual verification as blocked.
Successful HTTP checks alone do not establish browser interaction or layout correctness.

## Selected Checks

Run these seven existing tests without changing them:

- `tests/test_engagement_summary.py::test_summary_page_requires_auditor_authentication`
- `tests/test_engagement_summary.py::test_summary_page_is_read_only_html`
- `tests/test_engagement_summary.py::test_seeded_engagement_is_shown`
- `tests/test_engagement_summary.py::test_summary_has_no_write_actions`
- `tests/test_workbench.py::test_relationship_review_page_and_json_share_current_state`
- `tests/test_workbench.py::test_relationship_review_page_renders_workflow_fields_as_html`
- `tests/test_relationship_review.py::test_queue_and_item_show_current_fictional_relationship_state`

Existing evidence-review tests inspected during preparation perform capture or context writes.
Do not select those write flows merely to obtain an evidence-page result.
Instead, use the existing store's seeded `EVD-FIC-0001` for the viewing journey.
Retain a focused temporary check of its HTML page and GET review state.

All three journey steps use one shared fictional store:

| Step | Route | Required Observation |
|---|---|---|
| Engagement | `/workbench/engagement/summary` | `ENG-FIC-0001`, fictional title and current state |
| Evidence | `/workbench/evidence/EVD-FIC-0001/review` | Matching identifier, current version and pending review state, reconciled with GET review data |
| Relationships | `/workbench/relationship-reviews/REL-FIC-0001` | Matching engagement, version 1, source support, gaps and pending decision |

Record exact expected fields from the existing seed and service definitions before asserting them.
Do not weaken expectations to match unexpected output.
The seed evidence is a placeholder without captured media. Report that limitation explicitly.
Read-only browsing may initialise the fresh SQLite store. It does not authorise POST or PUT review actions.
Do not click Save, Approve, Complete Review or other write controls.

## Acceptance And Stop Rules

Require accessible failure/pass evidence before expanding beyond the minimal probe.
Require all seven selected tests to pass with no skips or unexpected collection changes.
Require HTTP success and matching state for all three viewing steps.
Require browser inspection before claiming the complete user journey works.
Retain screenshots only of fictional operational pages; inspect them before citing them.

Classify failures as environment, verification-script or application findings after retrieving exact evidence.
A passing retry does not establish a cause. Permit at most two corrective attempts for one temporary setup fault.
Application corrections require a separate bounded scope; preserve their failures without editing application source here.
Stop at the hard limit, missing required evidence, unavailable access or scope expansion.

The report must include commands, versions, timings, hashes, fixture IDs, database path, test counts and evidence locations.
Distinguish automated checks, browser observations and fixture-only demonstrations.
Leave live Next.js/Convex verification blocked until authorised configuration is available.
Leave iOS Copy diagnostics, full iOS acceptance and historical ancestry unchanged.
Do not describe this focused result as production readiness, showcase completion or full regression acceptance.
