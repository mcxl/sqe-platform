# Engagement Setup Workflow

**Status:** Approved for fictional implementation. Real client use remains held at G0.

## Purpose And Owner

This workflow creates the controlled Engagement that holds scope, evidence and decisions. The accountable auditor owns setup and approves activation.

## Trigger

The accountable auditor manually selects **New Engagement** before field capture or evidence registration starts.

The current pilot permits fictional Engagements only. Real client Engagements remain held at G0.

## Required Inputs And Access

- An authenticated auditor session.
- An Engagement title.
- A unique Engagement reference.
- The review purpose and authority reference.
- A scope statement and explicit exclusions.
- Included sites, business units or activities.
- The review period and evidence cut-off date.
- The accountable auditor.
- The permitted data classification.
- A clear fictional or real-client indicator.

## Ordered Actions

1. The auditor selects **New Engagement**.
2. ACE creates one draft Engagement ID and one creation-attempt key.
3. The auditor records the title, reference, purpose and authority.
4. The auditor records the included scope and exclusions.
5. The auditor records included sites, business units or activities.
6. The auditor records the review period and evidence cut-off date.
7. The auditor confirms the accountable auditor.
8. The auditor selects the permitted data classification.
9. The auditor marks the Engagement as fictional or real-client work.
10. ACE applies G0 and blocks real-client activation when acceptance or data rules are missing.
11. ACE saves the Engagement as `DRAFT`.
12. ACE shows one setup summary for auditor review.
13. The auditor confirms the authority, scope, exclusions and data boundary.
14. ACE records the setup approval and changes the state to `READY_FOR_CAPTURE`.
15. The auditor selects the Engagement as the current capture context.
16. ACE shows the selected Engagement beside every capture action.

## Human Checkpoints

### Authority And Scope Check

The accountable auditor decides whether:

- the authority is current;
- the scope and exclusions are clear;
- the review period is correct; and
- the Engagement is safe to use for capture.

### G0 Data Check

The accountable auditor confirms whether the work uses fictional, public, AuditCo-owned or real-client material.

ACE blocks real-client activation until client acceptance and data rules are approved.

### Capture Context Check

The auditor selects the current Engagement for field capture. The selected context must remain visible on the phone.

## Outputs And Storage

- One Engagement ID.
- One current Engagement record.
- One scope and exclusion record.
- One authority reference.
- One accountable auditor reference.
- One data-classification decision.
- One setup approval record.
- Engagement creation and activation audit events.

These records stay in the external ACE data store. They do not enter the source repository.

## Idempotency And Retry

- The creation-attempt key prevents duplicate Engagements after a retry.
- A repeated request with the same key returns the existing Engagement ID.
- A unique Engagement reference blocks accidental duplicates.
- Draft saves can retry without creating a new Engagement.
- Activation can occur once for each approved scope version.

## Failure And Escalation Behaviour

| Failure | ACE Behaviour | Auditor Action |
| --- | --- | --- |
| Required field missing | Keep the Engagement in `DRAFT` | Complete the missing field |
| Duplicate reference | Show the existing Engagement | Open it or use a different reference |
| Authority is uncertain | Block `READY_FOR_CAPTURE` | Check the authority |
| Scope or exclusion is unclear | Keep the Engagement in `DRAFT` | Correct the scope wording |
| Real-client G0 check fails | Block activation | Use no client evidence |
| Data store unavailable | Save no approval or activation | Stop and report the fault |
| Activation response lost | Return the existing approved state after retry | Confirm the displayed context |
| Wrong capture context selected | Record the selection change | Select the correct Engagement |

ACE must not silently activate, close or delete an Engagement.

## Privacy And Credential Constraints

- Keep fictional and real-client indicators explicit.
- Keep client acceptance and data approval separate from setup completion.
- Do not store client evidence before G0 approval.
- Do not put Engagement records, evidence or credentials in the repository.
- Do not expose Engagements through public ports or client-facing access.

## Observability

A successful run proves all of these facts:

- one Engagement ID exists;
- one authority and scope record exists;
- exclusions are visible;
- one data-classification decision exists;
- one setup approval exists;
- the Engagement is `READY_FOR_CAPTURE`;
- the current capture context is visible; and
- creation and activation audit events exist.

## Acceptance Criteria

1. Setup is unavailable without authentication.
2. A creation retry produces one Engagement.
3. Each Engagement has a unique reference.
4. Required authority, scope and exclusion fields cannot be empty.
5. Fictional and real-client Engagements are clearly different.
6. G0 blocks real-client activation when acceptance or data rules are missing.
7. The auditor approves setup before `READY_FOR_CAPTURE`.
8. The selected capture context is visible on desktop and iPhone.
9. Capture is blocked when no current Engagement is selected.
10. Engagement records remain outside the repository.
11. Activation creates an audit event.
12. A scope change after activation preserves the earlier approved scope.

## Resolved Decisions

### Open And Selected Engagements

Decision: several Engagements can remain open, but each auditor session has one selected capture context.

### Scope Changes After Activation

Decision: direct edits are permitted while the Engagement is `DRAFT`.

After activation, create a new scope version, record the reason and require auditor approval before more capture.

## Unresolved Dependencies

### Real Client Data

Held at G0. Real client activation requires acceptance and approved storage, security, retention and access rules.
