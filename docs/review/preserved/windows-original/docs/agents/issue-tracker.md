# Issue Tracker

Use Linear team `Mcxi_co` for SQE build specifications and tickets.

Use project `SQE Phase 2 - Relationship View` for the current Phase 2 work.

Use GitHub pull requests for code review, checks and merge records.

Use `workflows/codex-autonomous-delivery.md` for the standing delivery authority and merge gate.

Prefix SQE issue titles with `[SQE]`.

Keep controlled workflow specifications in the SQE workspace. Link each issue to its local specification.

Record the baseline branch, baseline commit, feature branch, pull request and final head commit in each implementation issue.

Use separate states for work, review and completion. Approval does not mean merge.

Add the `approved` label after the accepted reviews.

Add the `ready-to-merge` label only for the exact pull request head that is ready for merge approval.

Add the `merged` label only after GitHub confirms that exact head was merged.

Set an issue to `Done` only after it has the `merged` label.

Block each dependent issue until the required earlier issue is `Done`.

Do not place client evidence, secrets or private auditor notes in Linear or GitHub.
