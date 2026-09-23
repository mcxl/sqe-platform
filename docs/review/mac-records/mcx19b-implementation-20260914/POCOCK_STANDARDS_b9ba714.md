# Pocock Standards Review

Candidate: b9ba714d99862e9ef5572b7eb2a1b1d6471d0932.
Base: 7dc7cee7654ae8cc002da54324c3d1475a8494e6.

HEAD and the merge base match these identifiers. The worktree is clean. No nested AGENTS.md files were found under ios, tools, or docs.

Result: One actionable finding.

1. [P2] Retain command output after a timeout.

File: LOCAL_HOME/Developer/sqe-platform-release-layout/tools/ace_ios_local.py, lines 195-198.

The timeout handler discards TimeoutExpired.stdout and TimeoutExpired.stderr. Callers then write empty build.log, native.log, or selected.log files. Thus, a timed-out build or test loses output already captured before the timeout. If the result bundle is incomplete, this can remove the only available failure detail.

Applicable rule: Global AGENTS.md, Mandatory Development And Build Controls: "Retrieve the exact failed assertion, expected result, actual result and relevant logs or images before corrective changes."

Keep the captured partial output in the command record. Mark the timeout separately from a completed non-zero exit. Verify this with a small subprocess that writes both streams, then exceeds its timeout. Check that the retained record and log contain both messages.

No additional architecture, cohesion, or naming defect was found in the changed source. This review does not assess specification compliance. It does not diagnose the four native release audit failures.

This was a read-only source review. No native build or test ran. Previous focused checks do not establish final acceptance. The pilot, complete programme, physical checks, baseline decision, service inputs, and final Sol review remain separate gates.
