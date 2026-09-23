# Issue Tracker

Use Linear team `Mcxi_co` for SQE work.

Use GitHub pull requests for code review, checks and merge records.

Use the [Autonomous Delivery Workflow](../../workflows/codex-autonomous-delivery.md)
for delivery authority and the merge gate.

Record the baseline branch and commit, feature branch, pull request, final head,
validated base commit, tests and reviews in each implementation issue.

Use Linear issue labels `approved`, `ready-to-merge` and `merged`. Keep pull request
draft and ready state in GitHub.

Add `approved` and `ready-to-merge` only for the exact final head and validated base
commit. Remove both labels after a head or base change. Add `merged` only after GitHub
confirms that exact head and base pair merged.

Set the issue to `Done` only after it has the `merged` label. Keep dependent issues
blocked until then.

Do not put real client information, secrets or private auditor notes in Linear or
GitHub.
