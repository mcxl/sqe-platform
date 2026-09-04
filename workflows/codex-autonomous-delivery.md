# Autonomous Delivery Workflow

## Purpose And Authority

This workflow delivers one bounded, approved task to merge approval. It does not
merge without separate user approval.

One detailed approval must state:

- The Linear issue.
- The goal and acceptance criteria.
- The baseline branch and commit.
- The allowed files or modules.
- The tests and time limit.
- The exclusions.
- The data and security controls.

One detailed approval permits:

- One initial normal task commit and push.
- Extra normal fix commits and pushes for pre-authorised safe findings only.
- A draft pull request.
- Checks, reviews, readiness work and status updates.

Then stop for merge approval.

This workflow does not grant direct commit or push authority. Use the repository
Commit and Push controls for a direct request.

## G0: Data Gate

Before work, confirm that all task data is fictional, public or AuditCo-owned test
data. G0 blocks real client information. If it is present, stop. Do not copy it into
files, commands, Linear, GitHub or a pull request.

## Required Records

Record these items in the implementation issue:

- Baseline branch and commit.
- Feature branch and pull request.
- Final head.
- Focused tests and complete-suite result.
- Pocock code review.
- Greptile result and `check-pr` result.
- Fresh Sol review.

## Delivery Sequence

### 1. Intake And Isolation

Confirm G0, the approved scope, the baseline branch and commit, the feature branch,
the time limit, required earlier issues, task isolation and no unrelated work.

Set the issue to `In Progress`. Keep dependent issues blocked until their required
earlier issue is `Done`.

### 2. Implementation And Safe Fixes

Implement only approved work. Run focused tests during implementation and after each
safe fix.

A safe fix changes only approved files or modules. It preserves approved behaviour.
It adds no tool or dependency. It does not change architecture, security boundary,
schema or public interface. It uses no real client information.

Use a maximum of two failed corrective attempts for one fault. Stop and ask the user
for any finding outside this boundary.

### 3. Commit, Push And Draft Pull Request

Before you create the draft pull request, set Greptile controls in its dashboard or
existing repository configuration:

- Set automatic reviews to manual-only. Use `skipReview: "AUTOMATIC"` or an
  equivalent dashboard setting.
- Set review retriggers on new commits to off.

Verify both controls before pull request creation. Do not add a config file or
dependency. Keep automatic reviews manual-only and review retriggers off through
readiness. This prevents another automatic review when the draft state changes to
ready.

Inspect the task diff. Verify that staged files and outgoing commits contain only the
approved task. Make the initial normal task commit and push. Create or update the
draft pull request for that head before final validation starts.

### 4. CI, Conflict And Greptile Fixes

Check current CI and pull request conflicts. Apply only safe in-bound fixes. Run
focused tests after each fix. Commit and push each changed head. Then update the draft
pull request.

Start the one intentional Greptile review only by one manual `@greptileai` pull
request comment. Use official `check-pr` to inspect the result. Inspect unresolved
actionable items, current checks and the pull request description. Categorise each
item as actionable, informational or already addressed.

Fix only safe actionable Greptile items. Run focused tests. Commit and push. Update
the draft pull request.

After a Greptile-driven head change, retain the first review as historical finding
evidence only. Do not treat it as current-head approval. Use current-head `check-pr`
only to confirm resolution and current checks after a fix. Do not use `greploop`.

If Phase 4 repeats, use `check-pr` for earlier-item resolution and current checks.
Do not trigger another Greptile review without user approval.

Complete all safe CI, conflict and review fixes before final validation. If an item
needs an unsafe fix, stop and ask the user.

### 5. Final Validation

After the final safe fix, run Pocock code review. If Pocock finds a safe code fix:

- Apply it.
- Run focused tests.
- Commit and push the changed head.
- Update the draft pull request.
- Run Pocock code review again.

This limited repeat applies only after a Pocock-driven head change. Apply the
two-failed-corrective-attempt limit.

When Pocock needs no code fix, run the complete test suite once for that final
candidate head. If it passes, obtain a Fresh Sol review for that head. The primary
session must inspect the complete diff and test evidence before the Fresh Sol review.

If Fresh Sol review first returns `fix-first` with a safe code fix:

- Treat it as a head change.
- Run focused tests.
- Commit and push the changed head.
- Update the draft pull request.
- Run Pocock code review.
- Run the complete test suite once.
- Obtain a new Fresh Sol review.

Allow one safe Fresh Sol fix and one new Fresh Sol review only. A further `fix-first`
result stops the task.

Do not run Greptile again. Stop for `rethink`, a failed test or an unsafe finding.

After Fresh Sol review returns `ship`, do not change code. A code change makes the
head a new candidate and needs the complete final-validation sequence again.

### 6. Readiness And Merge Approval

After Fresh Sol review returns `ship`, mark the draft pull request ready for review.
Keep both automatic Greptile controls off through readiness.

Confirm these items:

- The final head.
- The current GitHub base commit.
- Passing checks.
- No conflicts.
- Base freshness.
- Accepted reviews.

If stale base, conflict, CI or review evidence needs repair, use a safe in-bound fix
only. Run focused tests. Return through Phase 4. Then complete all of Phase 5. Do not
mark readiness until it completes. Stop for an unsafe repair.

Record the final head and validated GitHub base commit. Add Linear issue labels
`approved` and `ready-to-merge` only for this exact pair.

Show the repository, pull request, exact ready head, validated base commit, merge
method, tests and reviews. Ask the user for merge approval of that exact pair. A later
head or base change clears that approval and needs a new approval.

### 7. Merge Confirmation And Closure

Immediately before the normal protected merge:

- Read the current GitHub pull request head.
- Read the current GitHub base commit.
- Compare both values with the user-approved pair.
- Require exact equality for both values.

If either value differs, stop readiness. Clear Linear issue labels and merge approval.
Change the pull request back to draft. Revalidate through Phase 4 and all of Phase 5.
Request new exact-pair approval.

After equality, use one immediate normal protected merge. The landing method must
reject a changed head or base pair. If GitHub cannot enforce the approved pair for the
immediate merge, stop and request user direction.

Do not use a merge queue, auto-merge, bypass, admin or force behaviour.

After GitHub confirms that exact approved head and base pair merged, record the
confirmation. Add the Linear issue label `merged` and set the issue to `Done`. Keep
dependent issues blocked until this step completes.

## Head And Base-Change Invariant

A head change includes any commit, amend, rebase, merge-base update or pushed code
revision that changes the pull request head. A base commit change requires the same
action even when the pull request head does not change.

After every head or base commit change, clear Linear issue labels `approved` and
`ready-to-merge`. Clear merge approval. Invalidate all candidate validation and review
evidence. This includes focused tests, the complete suite, Pocock code review,
Greptile, `check-pr` confirmation and Fresh Sol review.

Update the draft pull request to the new head. Run focused tests after the safe fix.
Do not use stale evidence to mark readiness or request a merge.

If the head or base commit changes after readiness, change the pull request back to
draft before Phase 4 and Phase 5. Clear labels and merge approval first.

## Diagnostic Probes

Use `matt-skills-curated:diagnosing-bugs` for diagnostic probes. Use diagnostics only
for an approved task. State the suspected cause and expected evidence before each
probe. Keep each probe read-only or reversible. Keep probes separate from corrective
fixes. Remove temporary changes before final validation.

Use at most five changed probes for one fault. Change later probes from earlier
evidence. Stop after five probes without a confirmed cause. Probes do not count as
corrective attempts.

Stop before dependency installation, destructive action, blocked-data access, scope
expansion, architecture change or security-boundary change.

## Stop Rules

Stop at the time limit, after two failed corrective attempts, before an out-of-scope
change, or when access, isolation or required review evidence is not available.

Do not merge, delete, clean or rewrite history after a stop. Preserve the task state.
Report completed work, active processes, blockers and remaining steps. Ask the user
before more work.
