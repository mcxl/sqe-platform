# Autonomous Delivery Workflow Repair

## Problem Statement

The current Autonomous Delivery Workflow can use stale tests and reviews after a pull request changes.

The rules also use different terms for the same ideas.

The workflow is not safe to use for an autonomous implementation run.

## Solution

Create one clear Autonomous Delivery Workflow.

Create the draft pull request before final validation.

Treat every head change as a new validation candidate.

Run final tests and reviews only after the last change.

Keep one explicit merge approval for the exact ready head.

## User Stories

1. As the user, I want one detailed approval to start a task, so that Codex does not ask repeated questions.
2. As the user, I want safe fixes inside the approved scope, so that minor findings do not stop work.
3. As the user, I want every changed head revalidated, so that stale evidence cannot approve a merge.
4. As the user, I want one merge question, so that the last irreversible action remains controlled.
5. As the user, I want changed heads to need new approval, so that approval stays bound to exact code.
6. As an agent, I want one workflow name, so that I apply the correct rules.
7. As an agent, I want one pull request term, so that instructions have one meaning.
8. As an agent, I want one Fresh Sol review term, so that review evidence stays clear.
9. As a reviewer, I want the final diff after all safe fixes, so that my report stays current.
10. As a reviewer, I want the exact baseline and head, so that I can inspect the correct change.
11. As a Linear user, I want readiness removed after a head change, so that stale work cannot merge.
12. As a Linear user, I want the final branch and commit evidence, so that task history remains traceable.

## Implementation Decisions

- Use `Autonomous Delivery Workflow` as the only workflow name.
- Use `pull request` as the only term for a pull request.
- Use `Fresh Sol review` as the only term for the final Sol review.
- Keep the complete workflow in one workflow specification.
- Keep repository instructions short and link them to the workflow specification.
- Keep issue-tracker instructions limited to task state and required evidence.
- Create the draft pull request before final validation.
- Complete safe CI, conflict and review fixes before final validation.
- Clear `approved` and `ready-to-merge` after each head change.
- Invalidate prior test and review evidence after each head change.
- Run focused tests after each safe fix.
- Run Pocock code-review after the final safe fix.
- Run the complete test suite after the final Pocock result and any accepted safe fix.
- Run Fresh Sol review after the complete test suite passes.
- Do not permit a code change after Fresh Sol returns `ship`.
- Bind merge approval to the exact ready head.
- Record the baseline branch, baseline commit, feature branch, pull request, final head, tests and reviews.
- Keep direct commit authority outside the Autonomous Delivery Workflow.
- Define G0 as the gate that blocks real client information.

## Testing Decisions

- Use document checks for required headings, terms and evidence fields.
- Use a negative check for deprecated workflow terms.
- Use a state-sequence test for head changes and readiness removal.
- Use a state-sequence test that rejects stale tests or reviews.
- Use Pocock code-review for standards and specification checks.
- Use Fresh Sol review after all accepted repairs.
- Inspect the complete final diff before commit.

## Out Of Scope

- Application code changes.
- Relationship Review implementation.
- Convex or Vercel setup.
- Pull request merge without explicit approval.
- Architecture or security-boundary changes.

## Further Notes

This repair must merge before the first Autonomous Delivery Workflow run.

