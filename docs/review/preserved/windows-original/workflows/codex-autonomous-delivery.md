# Codex Autonomous Delivery

## Purpose And Owner

This workflow moves one approved SQE task to a confirmed merge. The user owns scope,
architecture, security decisions and merge approval. Codex owns bounded delivery,
safe fixes, checks, reviews, PR work and Linear updates.

## Trigger And Inputs

Start only after one detailed approval for one Linear issue. It must state the goal
and acceptance criteria. It must state the baseline branch and commit. It must state
the allowed files or modules, tests, time limit and exclusions. It must state data and
security controls.

Require connected Linear and GitHub access. Require a clean task branch or worktree.
Require an approved specification and Sol Advisor companion agents. Require Pocock,
controlled Greptile, the official `check-pr` skill and PR Completion.

## Approved Task Authority

One detailed approval authorises in-bound implementation, diagnosis and safe recovery.
It authorises compatible version correction, focused verification, commits and pushes.
It authorises PR updates, reviews and status updates. Use this authority only inside
the approved file boundary.

It authorises bounded Preview deployment retries. It authorises temporary official
tools. Pin each tool version. Isolate each tool outside repository dependencies.
It authorises temporary exports of tracked files outside the repository. It authorises
automatic cleanup of task-created temporary files and temporary credentials. Do not
request approval again for these in-bound actions.

Before opening a deployment URL, target Preview explicitly. Confirm that the provider
reports a Preview deployment.

Safe recovery can move generated dependency, cache or build folders to a recoverable
location outside source scan paths. It can then reinstall cleanly from the approved
lock. Do not delete these folders. Do not request approval again for this recovery.

A compatible version correction can change versions only for approved dependency
names. Use direct compatibility evidence. Select the nearest supported stable version.
It can update the approved lock, configuration and tests inside the approved boundary.

This authority cannot add a dependency name or repository tool. It cannot change
architecture, security boundaries, schemas, public interfaces or production actions.
It cannot deploy to Production. It does not permit DeepSec, force pushes, history
rewrites or automatic merges.

## Nine Delivery Phases

1. **Intake, Dependencies, Baseline, Isolation, Linear State And Sol Preflight.**
   Confirm that the issue and its required earlier issues are not blocked. Confirm the
   approved baseline, task isolation and no unrelated changes. Set Linear to `In
   Progress`. Run Sol Advisor preflight and confirm the required roles and routing.

2. **Terra Implementation And Focused Tests.** Delegate bounded implementation to
   Terra / High. Run focused tests during work and after each safe corrective fix.

3. **Primary Inspection, Pocock Review And Safe Fixes.** Inspect the complete task
   diff against the approval. Run Pocock code review. Apply only safe findings and
   rerun focused tests after each fix.

4. **Commit, Push And Draft PR.** Use PR Completion to verify task-only staged files,
   commit and push. Create or update the draft review-candidate PR for that head.

5. **Controlled Greptile Review And Safe Fixes.** Control Greptile update-triggering
   before one intentional review of the draft head. Use `check-pr` to inspect the
   latest summary, inline comments, current checks and PR-description completeness.
   Report only unresolved actionable findings and a compact checks summary. Do not
   print unchanged raw comments. Categorise items as actionable, informational or
   already addressed. Apply only safe actionable fixes, run focused tests, then use PR
   Completion to push them and update the draft PR. Use `check-pr` only to confirm
   resolution and current checks. Do not use `greploop` or run another Greptile review.

6. **Final Suite And Fresh Sol Review.** Run the complete suite once on the normal
   final candidate head. Before the first Sol review, the primary session must inspect
   the complete final diff. Include Greptile safe fixes and verification evidence. Then
   obtain a fresh Sol / High review. For one safe Sol fix that changes code, run focused
   tests. Rerun the complete suite on the changed head. Push it with PR Completion and
   update the draft PR. Before one fresh Sol review, the primary session must inspect
   the changed complete final diff and verification evidence. Do not rerun Greptile.
   Stop unless the final Sol verdict is `ship`. When both revisions exist, give Sol the
   explicit base and head revisions instead of a pasted diff.

7. **Readiness Confirmation.** Confirm the final head, checks, conflicts, base
   freshness and accepted reviews. Add Linear `approved` and `ready-to-merge` labels
   for the exact ready head.

8. **Exact-Head Merge.** Show the repository, PR, exact head, merge method, tests and
   review results. Request merge approval for that exact head. Submit the approved
   protected merge and confirm GitHub merged that exact head.

9. **Linear Closure.** Record the PR, final head, tests and reviews in Linear. Add
   `merged`, set the issue to `Done`, and keep dependants blocked until completion.

## Safe Fix, Recovery And Correction Boundary

A safe fix changes only approved files or modules. It preserves approved behaviour.
It uses no real client information. It adds no dependency name or repository tool.
It changes no architecture, security boundary, schema, public interface or production
action. A temporary official tool is permitted only under Approved Task Authority.

Safe recovery and compatible version correction are safe only when they meet the
Approved Task Authority rules. Continue automatically after a recoverable local
failure when a safe in-bound remedy exists. Do not request approval for that remedy.
Stop and ask the user for any other finding.

## Diagnostic Probes

Use diagnostic probes only for an approved delivery task and use
`matt-skills-curated:diagnosing-bugs`. State one suspected cause and expected evidence
before each probe. Use at most five changed probes for one fault. Change each later
probe from earlier evidence. Use read-only or temporary reversible changes. Remove
temporary changes before final validation. Keep probes separate from corrective fixes.
Do not count probes as corrective attempts. Stop before dependency installation.
An Approved Task Authority can permit a clean reinstall from the approved lock.
This exception permits no new dependency name, non-temporary tool or unapproved
installation. Stop before irreversible deletion of non-temporary data, blocked access,
scope expansion, architecture or security change. Stop after five probes without a
confirmed cause.

## Human Checkpoint

Merge approval is the required late checkpoint. The user approves or rejects the
exact ready head. A head change needs new approval.

## Retry And Stop Rules

Stop after two failed corrective attempts for one fault. Stop at the time limit. Stop
before an architecture, security, public schema, public interface, dependency name or
repository tool change. Different validation failures are separate faults. A running
process is not failed. Only a completed non-zero exit proves failure.

Use at most two Preview recovery retries for one deployment fault. Retry automatically
within the hard limit when new provider evidence changes the retry. Do not request
approval for an allowed Preview recovery retry. Do not open a deployment URL before explicit
Preview targeting and provider confirmation.

Stop for real client data, unavailable required access and material scope expansion.
Stop for irreversible deletion of non-temporary data. Stop for a Production target,
Production deployment or merge approval. Stop if isolation, access, role routing or
review isolation cannot be verified. Preserve non-temporary work. Remove task-created
temporary files and temporary credentials. Do not merge, delete non-temporary data,
clean non-temporary work or rewrite history after a stop. Run each external scan and
review once. Do not rerun any scan without new user approval. Phase 6 permits only one
extra complete suite run and one fresh Sol review after the permitted code-changing
fix. Stop task commands and report completed work, active processes, blockers and
remaining steps. Ask for approval before work resumes.

## Privacy And Credentials

Use fictional, public or AuditCo-owned test information only. Keep real client
information blocked at G0. Do not store secrets, client evidence or private auditor
notes in Linear or GitHub. Do not run DeepSec without new, explicit approval.

## Completion Evidence

A complete delivery has these records:

- The Linear issue gives the baseline and final head commits.
- Focused tests passed during delivery.
- The complete suite passed on the actual final code head.
- Pocock completed its standards and specification review.
- Greptile update-triggering was controlled before one intentional review.
- `check-pr` recorded unresolved actionable findings and a compact checks summary.
- Each Greptile item has a category.
- Fresh Sol returned `ship` for the final head.
- The PR and exact head were confirmed merged.
- Linear has `merged` and `Done`.
