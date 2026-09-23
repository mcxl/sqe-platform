# SQE Stage 4 Verification Record

Date: 19 September 2026. Result: **Partial — automated viewing checks passed; browser verification blocked.**

## Authority And Candidate

User approved the Stage 4 proposal with SHA-256 `c0d296c1f295f2473dcb69cf281ab4e9b12bc6911e1ffe3e1cb54cf88aae8db0`.

Workspace: `LOCAL_HOME\Documents\sqe-platform`.
Branch: `codex/sqe-workspace-consolidation`.
HEAD: `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a`.
Stage 3 imports and documentation were already uncommitted. `02-source-before.json` identifies the tested working files.
All 150 recorded files and the file set remained unchanged. No repository edit, commit, push or deployment occurred.

## Results

| Required Check | Result | Evidence |
|---|---|---|
| Isolated environment | Passed: 29 packages, pytest 8.4.2; package compatibility check passed | 06–10 logs, resolved requirements and hashes |
| Minimal application startup | Passed: import and HTTP 200 health result | 11-import-health.log |
| Deliberate native failure | Passed as evidence gate: one intended failure, exit 1, no skips/errors | 12-gate-fail.log/xml/html |
| Same probe corrected | Passed: one test, exit 0; only expected identifier changed | 13-gate-pass.log/xml/html; 14-gate-verification.json |
| Seven selected existing tests | Passed: 7, no failures, errors or skips | 15-selected-tests.json; 16-focused.log/xml |
| Three page GETs and two state GETs | Passed: all HTTP 200, matching fictional records | 18-expected.json; 19-*; 20-journey-http-result.json |
| Browser identity, appearance and interaction | Blocked before page rendering | 22-browser-blocker.json |
| Evidence source-version display | Not demonstrated: seeded placeholder has no source context/version | 19-evidence-state.json |
| Source preservation and server shutdown | Passed | 21-owned-server-processes.json; 17-server-stopped.json; 23-integrity-and-stop.json |

The deliberate failure was `test_evidence_gate.py:15`: expected `ENG-FIC-9999`, actual `ENG-FIC-0001`.
The corrected probe expected `ENG-FIC-0001`. Both results retain native logs, JUnit output and the returned page.
These two probe executions are separate from the seven existing tests and five HTTP checks.

## Viewing Journey

All journey GETs used one database:
`LOCAL_HOME\sqe-private\consolidation-20260918\stage4\journey-data\workbench.sqlite3`.

- Engagement `ENG-FIC-0001`: fictional title and `READY_FOR_CAPTURE` state matched.
- Evidence `EVD-FIC-0001`: `PENDING_REVIEW`, no completion, no original media and no source context matched the seed.
- Relationship `REL-FIC-0001`: version 1, source support, gaps, contradictions and no recorded decisions matched.
- The relationship HTML's embedded state equalled its JSON response.

The evidence record is a placeholder. This run does not demonstrate captured media, populated source versions or completed review.
GET initialization created the isolated store. No POST/PUT review action was exercised.
The inspected evidence-review tests perform writes, so they were not included in the seven selected tests.

## Browser Blocker

The in-app browser returned `net::ERR_BLOCKED_BY_CLIENT` for the local Engagement page.
The server recorded HTTP 401 for the browser request; the browser supplied no successful authentication.
HTTP requests carrying the approved fictional Basic credentials succeeded beforehand.
This establishes a browser-access blocker, not a proved application defect or a proved browser-policy cause.
No authentication bypass, alternate browser, route workaround or application change was attempted.
No rendered screenshots, browser console check or navigation interaction passed.
Consequently the complete user journey is **not accepted**.

## Environment Findings

The repository lock omits three declared packages: openpyxl, python-docx and reportlab.
The private environment constrained existing locked packages and resolved the omitted declarations within existing ranges.
The complete private resolved requirements include hashes. The repository lock remains unchanged and incomplete.
The installed TestClient stack emitted a deprecation warning about httpx support. All selected checks passed despite it.
No suggested replacement dependency was added. Resolve this separately before claiming long-term environment readiness.

Python: 3.14.5. uv: 0.11.12. Full versions are in `10-packages.log`.
Each command and exit code is in its paired JSON record. The startup command, PID, port and data path are in `17-server.json`.
The launcher and verified descendants were terminated after the browser stop condition. Port 60097 is closed.

## Time And Capacity

Started: 2026-09-19T05:40:50+10:00.
Finished: 2026-09-19T05:48:23.016092+10:00.
Elapsed: 7.6 minutes, within the 60-minute cap.
Command execution durations are retained in `24-command-durations.json`.
Active human/model work and waiting were not separately instrumented; no invented split is reported.
Retained environment/cache/evidence: approximately 116.5 MiB, below the 2 GiB allowance.
C: free: approximately 10.19 GiB, above the 2 GiB reserve.

## Remaining Work

1. Establish authenticated browser access, then inspect the same three pages and their navigation.
2. Scope a fixture with a populated evidence source version if that acceptance requirement remains mandatory.
3. Reconcile the repository dependency lock in a separate source-change task.

The live Next.js/Convex check remains blocked pending authorised configuration.
Public showcase implementation has not started in this block.
iOS Copy diagnostics, historical ancestry and final iOS acceptance remain unchanged.
These results establish focused fixture-based Python behaviour only, not full web readiness or production acceptance.
