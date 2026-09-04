# Mandatory AuditCo Document Rules

Apply these rules to every Word document created or edited in this workspace, with no exceptions:

- Use Capital Case for all headings, running headers, table headers and footers.
- Use Australian English throughout.
- Do not use Word text boxes. Move all text into ordinary paragraphs, lists or genuine data tables.
- Every cover page must remain editable. Do not flatten cover wording into an image.
- Use the retained AuditCo template as the visual authority.
  Recreate editable covers with Word-native paragraphs, table shading and rules.

## Sol Advisor implementation lane

For implementation, refactoring, debugging, pipeline, template, and test changes, start
a fresh Codex task and invoke `$sol-advisor:orchestration`.

- Use the installed Terra lane for implementation and obtain the Fresh Sol review.
- These document rules, specialist SQE workflow, human decisions, and final review
  requirements remain authoritative; Sol Advisor does not replace professional review.
- The primary session must inspect the complete diff and rerun the relevant verification
  before accepting the Sol verdict.

## Bounded Work Policy

Apply this policy to all Codex work in this repository.

Before work that can take more than 30 minutes:

- State the acceptance criteria.
- Give a time estimate.
- Set a hard time limit.
- Identify commands that can use much time, compute, storage, or tokens.
- Separate pilot work from production hardening.
- Wait for user approval before execution.

Use 60 minutes as the default hard limit when the user gives no limit.

During the work:

- Give a progress update every 15 minutes.
- State the elapsed time and estimated remaining time.
- Stop after two failed attempts at the same problem.
- Stop before an architecture or security-boundary change.
- Stop when the hard time limit expires.
- Do not increase the scope without user approval.
- Under an approved Autonomous Delivery Workflow, fix only pre-authorised safe findings.
  Stop for a finding outside its safe boundary.
- Do not add tools, controls, or dependencies without user approval.
- Do not continue only because earlier work used much time or many tokens.

For validation:

- Review the test harness before the real operation.
- Use focused tests during development.
- Run the complete suite once for each final candidate head.
- The Autonomous Delivery Workflow permits one safe Fresh Sol fix and one new Fresh
  Sol review.
- Run each external scan one time.
- Run each external review one time.
- Do not repeat a scan after a review without user approval.
- Keep generated locks, caches, logs, and outputs outside AI review context.
- Validate generated files with mechanical tools when possible.

For DeepSec:

- Do not use DeepSec unless the user gives new, explicit approval.
- Require an approved isolation design and test harness before a real scan.
- Run one real scan only after the harness passes review.
- Stop DeepSec work at the first hard-limit or stop-condition event.

For commit and push requests:

- Treat a direct `commit and push` request as approval for one normal commit and push.
- An approved Autonomous Delivery Workflow authorises one initial normal task commit
  and push.
- It authorises extra normal fix commits, pushes and pull request updates only for
  pre-authorised safe findings.
- Include only files that the current task created or changed.
- Do not include unrelated staged, unstaged, untracked, ignored, or generated files.
- Show and verify the exact staged file list before the commit.
- Show and verify all outgoing commits and files in `upstream..HEAD` before the push.
- Stop if the outgoing range contains work outside the current task or blocked data.
- Push only to the current approved feature branch.
- Do not force-push or rewrite published history.
- Do not push secrets, restricted client information, environment files, or other blocked data.
- Do not ask for a second commit or push approval when these conditions pass.
- Treat words such as `anything` or `all` as current-task scope only.
- Require separate user approval for each pull request merge.
- Stop if the branch, remote, file ownership, or task scope is not clear.

## Autonomous Delivery Workflow

Use [workflows/codex-autonomous-delivery.md](workflows/codex-autonomous-delivery.md)
for one approved delivery task. Keep the detailed rules in that specification.

The workflow approval permits only its stated bounded delivery actions. Direct request
authority stays in the Commit and Push controls above. Do not use real client
information. G0 blocks it.

When work stops:

- Stop all task commands.
- Preserve the current state.
- Do not clean, delete, or merge without user approval.
- Do not commit, push or update a pull request unless a direct request or an approved
  Autonomous Delivery Workflow permits it.
- Report completed work, active processes, blockers, and remaining steps.
- Ask for approval before work resumes.

## Agent skills

- Use `docs/agents/issue-tracker.md` for issue-tracker rules.
- Use `docs/agents/triage-labels.md` for triage labels.
- Use `docs/agents/domain.md` for domain-document locations.
