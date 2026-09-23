# Commands And Exit Codes

All commands ran in `/code/mcxl/sqe-platform-sync` unless noted. `$PY` is
`/code/mcxl/sqe-platform/.venv/bin/python`. `uv sync` was never run. Times are approximate
(start of the command, to the minute). Before every commit, `git status --short` and
`git diff --cached --name-only` were run and the staged list was checked against the plan's
file sets; the lists are in the session record and match the commit contents shown by `git show --stat`.

| Time (UTC) | Command | Exit | Note |
|---|---|---|---|
| 10:34 | `git worktree add /code/mcxl/sqe-platform-sync -b vorflux/snapshot-sync-main-gates cc05ca0` | 0 | Pull request 7 checkout untouched |
| 10:34 | `$PY -c "import src.ace; print(src.ace.__file__)"` | 0 | Printed the worktree path |
| 10:35 | `$PY -m pytest -q -p no:cacheprovider` | 1 | Baseline: 800 passed, 4 failed (iOS tests), 314 s |
| 10:36 | `PYTHONPATH=$PWD $PY docs/review/evidence/snapshot-sync-20260923/scripts/probe_finding_1.py` | 0 | `forged assessment evaluated: EvaluationResult` |
| 10:36 | `PYTHONPATH=$PWD $PY docs/review/evidence/snapshot-sync-20260923/scripts/probe_finding_2.py` | 0 | `tampered row loaded: True` |
| 10:38 | `git commit -m "Record snapshot baseline test run and finding probes"` | 0 | `46cfb42` |
| 10:39 | `git show origin/main:<file> \| perl -pe 's/\r?\n/\r\n/' > <file>` for the 10 Set 1 files | 0 | `file` confirmed CRLF; whitespace-insensitive diff against main empty |
| 10:39 | `comm -12 <(git diff --name-only \| sort) <(git diff --name-only cc05ca0 vorflux/client-mobile-proof \| sort)` | 0 | Empty. The plan's `grep -E 'test_app'` check matched `test_approval_gate.py` by substring and was replaced by this exact comparison |
| 10:39 | `$PY -m pytest -q -p no:cacheprovider tests/test_approval_gate.py tests/test_change_export.py tests/test_planning_trace.py tests/test_relationship_review.py tests/test_workbench.py` | 0 | 276 passed, 51 s |
| 10:40 | `git commit -m "Restore main's MATE approval boundary and G0 seed verification"` | 0 | `faa1774`, 10 files |
| 10:40 | `git show origin/main:docs/adr/<n>.md > docs/adr/<n>.md` (4 files); `git commit -m "Restore the four architecture decision records"` | 0 | `7ed849f`; `git diff origin/main HEAD -- docs/adr` empty |
| 10:41 | `$PY -m pytest -q -p no:cacheprovider tests/test_g0_snapshot_metadata.py` | 0 | 2 passed |
| 10:41 | `git archive cc05ca0 \| tar -x -C /var/tmp/snapbase`; copy the new test; `PYTHONPATH=/var/tmp/snapbase $PY -m pytest -q -p no:cacheprovider tests/test_g0_snapshot_metadata.py` (in `/var/tmp/snapbase`) | 1 | 2 failed: loader returned the tampered inputs on the snapshot |
| 10:41 | `git commit -m "Add G0 seed metadata regression tests"` | 0 | `2f341d3` |
| 10:42 | `$PY -m pytest -q -p no:cacheprovider` | 1 | Final head: 820 passed, 4 failed (same four iOS tests), 322 s |
| 10:47 | Both probes again | 0 | `blocked` and `tampered row loaded: False` |
| 10:47 | `git diff --ignore-all-space --ignore-blank-lines --stat origin/main HEAD -- src tests tools quality .github docs/adr` | 0 | See `after/diff-vs-main-stat.txt` |
| 10:47 | `git diff --stat cc05ca0 HEAD -- src tests tools quality .github docs/adr` | 0 | 15 files, 770 insertions, 41 deletions |
| 10:47 | `file <each changed src/tests file>` | 0 | CRLF on the 10 replaced files; new test LF |
| 10:48 | `$PY -m pytest -q -p no:cacheprovider tests/test_approval_gate.py` | 0 | 80 passed |
| 10:48 | `rm -rf /var/tmp/snapbase` | 0 | Cleanup |
| 10:49 | `git commit -m "Record snapshot sync evidence and review roles"` | 0 | `40b1b5f` |
| 10:50 | Two review subagents dispatched on `cc05ca0..40b1b5f` (standards; final with risk) | | Both: fit to push / `ship`, risk 2/10 |
| 10:56 | Edit `tests/test_g0_snapshot_metadata.py` (public `trace_inputs()`, positive control); `$PY -m pytest -q -p no:cacheprovider tests/test_g0_snapshot_metadata.py` | 0 | 2 passed |
| 10:56 | Same file against a fresh `cc05ca0` export | 1 | 2 failed (excerpt retained); export deleted |
| 10:57 | `git commit -m "Use the public loader path and a positive control in the G0 metadata tests"` | 0 | `07e6c79` |
| 10:57 | `$PY -m pytest -q -p no:cacheprovider` on `07e6c79` | 1 | See `after/pytest-after.txt`; expected same four iOS failures |
| 11:00 | `$PY -m pytest -q -p no:cacheprovider tests/test_g0_snapshot_metadata.py tests/test_approval_gate.py` | 0 | 82 passed |
| 11:02 | README and `commands.md` corrections from both reviews; `git commit -m "Record review verdicts and correct the snapshot sync README"` | 0 | Final head |
