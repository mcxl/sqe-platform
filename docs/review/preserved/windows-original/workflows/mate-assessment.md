# MATE Assessment Workflow

**Status:** Approved for fictional implementation. Real client use remains held at G0.

## Purpose And Owner

This workflow lets the accountable auditor assess one Control's structural design.

MATE means Mandate, Accountability, Trigger and Escalation.

MATE does not assess implementation, operation or effectiveness. It does not approve relationships or conclusions.

## Trigger

The auditor manually opens the MATE work queue for the active Engagement.

ACE shows the highest material-risk active item first. Within the same priority, ACE shows the oldest item first.

The auditor can select a different Control.

## Required Inputs And Access

- An authenticated auditor session.
- One active Engagement.
- One Control with approved links to its Binding Obligation, Risk and Accountable Role.
- One current proposal for each MATE dimension.
- One Evidence Review Record for each proposal.
- Current Source References with precise passages.
- Supporting, weakening and contradictory evidence classifications.
- Visible Evidence Gaps, limitations and contradiction status.
- One unique decision key for each final decision.

The current pilot uses fictional, public or AuditCo-owned information only.

## Ordered Actions

1. The auditor opens the MATE work queue.
2. ACE shows ready, draft, blocked and approved assessments.
3. ACE orders active work by material risk, then waiting time.
4. The auditor selects one Control.
5. ACE verifies the approved Binding Obligation, Risk and Accountable Role links.
6. ACE shows the linked Binding Obligation, Risk, Control and Accountable Role together.
7. ACE starts with Mandate and shows `Check 1 of 4`.
8. ACE shows the controlled question and current proposal version.
9. ACE shows the proposed `YES` or `NO` answer and rationale.
10. ACE shows supporting, weakening and contradictory evidence.
11. ACE shows Evidence Gaps, limitations, source status and precise passages.
12. ACE shows unresolved contradictions and blocking reasons.
13. The auditor checks the proposal and evidence.
14. The auditor can save incomplete work as a draft.
15. For a final decision, the auditor selects `APPROVED`, `REJECTED` or `CHANGES_REQUIRED`.
16. The auditor records a written review note.
17. ACE validates the proposal, evidence, decision and current version.
18. ACE saves one Auditor Decision and one immutable audit event.
19. A different auditor answer requires `CHANGES_REQUIRED` and a new proposal version.
20. ACE repeats the process for Accountability, Trigger and Escalation.
21. ACE blocks completion until all four current proposals have approved decisions.
22. ACE sends the four approved Boolean answers to the existing deterministic evaluator.
23. ACE shows the calculated rating. The auditor cannot edit it.
24. ACE creates one frozen Approved MATE Assessment.
25. ACE links the assessment to the approved Control trace.
26. ACE shows the saved assessment and updated queue.

## Human Checkpoints

### Entry Check

The auditor confirms that ACE shows the correct Control and approved planning relationships.

### Dimension Evidence Check

The auditor checks the question, proposal, rationale, evidence, gaps, limitations and contradictions.

Missing evidence does not automatically produce a `NO` answer.

### Dimension Decision Check

The auditor selects one decision and records a review note.

Approval requires sufficient evidence for a control-design assessment.

The approved answer must match the current proposal version.

### Rating Check

ACE calculates the rating only after all four dimensions are approved.

The auditor confirms that ACE used the approved answers. The auditor cannot edit the rating.

## Deterministic Rating Rules

- Four `YES` answers produce `ADEQUATE`.
- A `NO` answer for Mandate or Accountability produces `INADEQUATE`.
- Two or more `NO` answers produce `INADEQUATE`.
- One `NO` answer for Trigger or Escalation produces `PARTIALLY_ADEQUATE`.

ACE must use the existing evaluator. It must not reproduce or change these rules in the workbench.

## Outputs And Storage

- Zero or more saved drafts.
- One immutable Auditor Decision for each decided proposal version.
- One immutable audit event for each Auditor Decision.
- One frozen Approved MATE Assessment after all gates pass.
- One immutable deterministic rating.
- One approved link between the Control trace and Approved MATE Assessment.
- Updated queue status.

The Approved MATE Assessment records:

- Control identity;
- four approved proposal and decision references;
- four approved Boolean answers;
- the calculated rating;
- evidence references;
- auditor identity; and
- review times.

All records stay in the external ACE data store. They do not enter the source repository.

The assessment does not create an audit conclusion.

## Idempotency And Retry

- One decision key identifies each final MATE decision attempt.
- A retry with the same key returns the existing Auditor Decision.
- A retry creates no duplicate Auditor Decision or audit event.
- ACE saves the Auditor Decision and audit event as one controlled operation.
- A failed save creates no partial decision or audit event.
- Draft saves create no final decision outcome.
- ACE never edits an Approved MATE Assessment.
- A change starts a new draft assessment version.
- ACE preserves all earlier assessments, ratings and decisions.

## Failure And Escalation Behaviour

| Failure | ACE Behaviour | Auditor Action |
| --- | --- | --- |
| A required approved relationship is missing | Block MATE start | Complete Relationship Review |
| A MATE dimension is missing or duplicated | Block completion | Correct the assessment inputs |
| A current Source Reference is missing | Block the dimension decision | Add or restore the source |
| Evidence is insufficient | Block approval | Gather evidence or request changes |
| A contradiction remains unresolved | Block completion | Resolve and explain the contradiction |
| A proposal remains unresolved | Block completion | Complete or revise the proposal |
| A decision does not match the proposal version | Reject the stale save | Open the current version |
| An approved answer differs from the proposal | Require `CHANGES_REQUIRED` | Create a new proposal version |
| A review note is missing | Block the final decision | Record the note |
| Decision save fails | Save no decision | Retry with the same decision key |
| Audit event save fails | Save no decision | Stop and report the fault |
| Evaluator fails | Create no approved assessment | Stop and report the fault |
| Data store is unavailable | Save no record | Stop and report the fault |

ACE shows the affected MATE dimension and the blocking reason in plain English.

## Privacy And Credential Constraints

- Only the authenticated auditor can make MATE decisions.
- Use fictional, public or AuditCo-owned information until G0 passes.
- Keep evidence, proposals and decisions outside the repository.
- Do not send evidence to public diagram or graph services.
- Do not expose private auditor notes to a future Client View.
- Do not store credentials in evidence, rationale or review notes.
- Keep ACE as the source of truth.
- AI can organise evidence and propose answers.
- AI cannot approve answers, change rating rules or approve conclusions.

## Observability

A successful Approved MATE Assessment proves all these facts:

- the Control had the required approved planning relationships;
- ACE assessed the four dimensions in the controlled order;
- each dimension had a current proposal and Evidence Review Record;
- each dimension had sufficient current evidence;
- no contradiction remained unresolved;
- each proposal had one matching approved Auditor Decision;
- each decision recorded the auditor, time and review note;
- the existing evaluator produced the rating;
- one frozen Approved MATE Assessment exists;
- the assessment links to the approved Control trace; and
- retries created no duplicate decisions or events.

## Acceptance Criteria

1. MATE Assessment is unavailable without authentication.
2. The active Engagement remains visible.
3. The MATE work queue is visible and selectable.
4. The queue shows ready, draft, blocked and approved assessments.
5. ACE orders active work by material risk, then waiting time.
6. The auditor can select another Control.
7. ACE blocks entry until the required planning relationships are approved.
8. ACE shows the Binding Obligation, Risk, Control and Accountable Role together.
9. ACE shows one MATE dimension at a time.
10. ACE uses the fixed Mandate, Accountability, Trigger and Escalation order.
11. ACE shows progress, such as `Check 2 of 4`.
12. Each screen shows the controlled question, proposal, rationale and evidence classifications.
13. Each screen shows gaps, limitations, source status, passages and contradictions.
14. The auditor can save an incomplete draft.
15. Every final decision requires a written review note.
16. Approval requires sufficient evidence and a matching current proposal.
17. Missing evidence does not automatically produce `NO`.
18. A different answer requires `CHANGES_REQUIRED` and a new proposal version.
19. ACE blocks completion for missing inputs or unresolved contradictions.
20. ACE calls the existing evaluator only after all four approvals.
21. The auditor cannot edit the calculated rating.
22. ACE creates one frozen Approved MATE Assessment after all gates pass.
23. The assessment links to the approved Control trace.
24. The assessment does not create a conclusion.
25. A changed input starts a new draft assessment version.
26. ACE preserves all earlier assessments, ratings and decisions.
27. A failed save creates no partial decision.
28. A retry creates no duplicate decision or audit event.
29. AI makes no Auditor Decision.
30. Records remain outside the repository.

## Resolved Decisions

### Entry Gate

Decision: start MATE only after the Control's required planning relationships are approved.

### Screen Order

Decision: show one dimension at a time in the fixed MATE order.

### Evidence Display

Decision: show proposals, rationale, evidence classes, gaps, limitations, contradictions and precise Source References.

### Decision Outcomes

Decision: use `APPROVED`, `REJECTED` and `CHANGES_REQUIRED`. Require a written review note.

### Completion Gate

Decision: require four matching approvals, sufficient evidence and no unresolved contradiction.

### Rating Authority

Decision: use the existing deterministic evaluator. Do not permit rating edits.

### Version Control

Decision: freeze approved assessments. A changed input starts a new draft version.

### Queue Order

Decision: order active work by material risk, then waiting time. Permit Control selection.

### Human Authority

Decision: only the authenticated auditor makes MATE decisions.

## Unresolved Dependencies

### Material-Risk Priority Source

The implementation must use an existing approved material-risk priority.

If no approved priority exists, ACE orders active items by waiting time.

### Durable Identity And Storage

The current domain proof uses fictional reviewer identifiers and in-memory records.

Implementation needs durable auditor identity, storage, version history and audit events.

### Real Client Data

Held at G0. Real client use needs approved storage, retention, access and privacy rules.
