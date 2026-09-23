# Relationship Review Workflow

**Status:** Approved for fictional implementation. Real client use remains held at G0.

## Purpose And Owner

This workflow lets the accountable auditor decide on one Relationship Version.

It creates an Approved Relationship only after an explicit approval. ACE does not make the decision.

## Trigger

The auditor manually opens the Relationship Review queue for the active Engagement.

ACE shows the highest material-risk proposal first. Within the same priority, ACE shows the oldest proposal first.

The auditor can select a different proposal from the queue.

## Required Inputs And Access

- An authenticated auditor session.
- One active Engagement.
- One Proposed Relationship with a current Relationship Version.
- Both records that the proposal links.
- The relationship type.
- The proposal rationale.
- The source support for the proposal.
- The complete version and decision history.
- Open Evidence Gaps and unresolved contradictions.
- The current material-risk priority, when an approved priority exists.
- One unique decision key for a final save.

The current pilot uses fictional, public or AuditCo-owned material only.

## Ordered Actions

1. The auditor opens the Relationship Review queue.
2. ACE orders proposals by material risk, then waiting time.
3. ACE shows one Proposed Relationship at a time.
4. The auditor can select a different proposal.
5. ACE shows both records that the proposal links.
6. ACE shows the relationship type.
7. ACE shows the current Relationship Version.
8. ACE shows the source support and proposal rationale.
9. ACE shows all earlier versions and Auditor Decisions.
10. ACE shows open Evidence Gaps and unresolved contradictions.
11. ACE warns about a possible duplicate proposal.
12. The auditor checks the records, relationship type, support and rationale.
13. The auditor can save the review as a draft.
14. A draft creates no Auditor Decision or Approved Relationship.
15. For a final decision, the auditor selects `APPROVED`, `REJECTED` or `CHANGES_REQUIRED`.
16. The auditor records a written reason.
17. ACE validates that the displayed Relationship Version is still current.
18. ACE saves one Auditor Decision for that exact version.
19. ACE records one immutable audit event.
20. If the decision is `APPROVED`, ACE creates one Approved Relationship for that version.
21. If the decision is `REJECTED`, ACE closes that proposal version without an Approved Relationship.
22. If the decision is `CHANGES_REQUIRED`, ACE preserves the version and returns the proposal for revision.
23. A revision creates a new Relationship Version.
24. The new version returns to the Relationship Review queue.
25. ACE shows the saved decision and the next queue item.

## Human Checkpoints

### Relationship Identity Check

The auditor confirms that ACE shows the correct two records and relationship type.

### Source Support Check

The auditor checks the source support, proposal rationale and applicable limitations.

### Gap And Contradiction Check

The auditor considers all visible Evidence Gaps and unresolved contradictions.

Warnings do not make or change the decision.

### Final Decision Check

The auditor selects one decision and records the reason.

Approval applies only to the displayed Relationship Version.

## Outputs And Storage

- One saved draft, when requested.
- One Auditor Decision for a final decision.
- One written decision reason.
- One immutable decision audit event.
- One Approved Relationship after `APPROVED` only.
- One closed rejected version after `REJECTED`.
- One revision request after `CHANGES_REQUIRED`.
- One new Relationship Version after a revision.
- Updated queue status.

All records stay in the external ACE data store. They do not enter the source repository.

## Idempotency And Retry

- One decision key identifies each final save attempt.
- A retry with the same key returns the existing Auditor Decision.
- A retry creates no duplicate Auditor Decision, Approved Relationship or audit event.
- A failed save leaves the proposal undecided.
- ACE must save the decision and audit event as one controlled operation.
- Approval cannot transfer from an earlier version to a later version.
- Draft saves create no final decision key outcome.

## Failure And Escalation Behaviour

| Failure | ACE Behaviour | Auditor Action |
| --- | --- | --- |
| A linked record is unavailable | Block the final decision | Check the record or storage |
| Source support cannot open | Block the final decision | Restore access or request changes |
| Relationship type is missing | Keep the review as a draft | Correct the proposal |
| Written reason is missing | Block the final decision | Record the reason |
| Version changed during review | Reject the stale save | Open the current version |
| Possible duplicate found | Show both proposals | Review them separately |
| Evidence Gap exists | Show the warning | Consider it in the decision |
| Contradiction is unresolved | Show the warning | Consider it in the decision |
| Decision save fails | Show an error and keep the proposal undecided | Retry with the same decision key |
| Audit event save fails | Save no final decision | Stop and report the fault |
| Data store is unavailable | Save no decision | Stop and report the fault |

ACE does not merge, delete, approve or reject proposals automatically.

## Privacy And Credential Constraints

- Use fictional, public or AuditCo-owned material until G0 passes.
- Keep linked records and review decisions outside the repository.
- Do not send proposals or evidence to public diagram or graph services.
- Do not expose private auditor notes to a future Client View.
- Do not store credentials in the rationale or decision reason.
- Keep ACE as the source of truth.

## Observability

A successful final decision proves all these facts:

- one Relationship Version was reviewed;
- both linked records and the relationship type were visible;
- source support and rationale were visible;
- gaps, contradictions and possible duplicates were visible;
- the auditor and decision time were recorded;
- one written reason was recorded;
- one Auditor Decision exists for the exact version;
- one immutable audit event exists;
- an approval created one Approved Relationship; and
- a retry created no duplicate record.

## Acceptance Criteria

1. Relationship Review is unavailable without authentication.
2. The active Engagement remains visible.
3. The queue is visible and selectable.
4. The queue orders proposals by material risk, then waiting time.
5. ACE shows one Proposed Relationship at a time.
6. Both linked records and the relationship type appear on one screen.
7. Source support, rationale and version history appear on that screen.
8. Open Evidence Gaps and unresolved contradictions remain visible.
9. A possible duplicate causes a warning only.
10. ACE does not merge or delete possible duplicates automatically.
11. A draft creates no Auditor Decision or Approved Relationship.
12. A final decision requires `APPROVED`, `REJECTED` or `CHANGES_REQUIRED`.
13. Every final decision requires a written reason.
14. `CHANGES_REQUIRED` preserves the reviewed version and decision.
15. A revision creates a new Relationship Version.
16. Approval of an earlier version cannot approve a later version.
17. Only approval of the current version creates an Approved Relationship.
18. Each final decision creates one immutable audit event.
19. A failed save leaves the proposal undecided.
20. A retry with the same decision key creates no duplicate records.
21. Warnings do not make the Auditor Decision.
22. Records remain outside the repository.

## Resolved Decisions

### Review Layout

Decision: show one proposal at a time. Show both records, relationship type, source support, rationale and history together.

### Decision Outcomes

Decision: use `APPROVED`, `REJECTED` and `CHANGES_REQUIRED`. Require a written reason.

### Version Control

Decision: never overwrite an approved or decided version. A revision creates a new Relationship Version.

### Queue Order

Decision: order by material risk, then waiting time. Permit the auditor to select another proposal.

### Warnings

Decision: show gaps, contradictions and possible duplicates. Do not decide, merge or delete automatically.

### Retry Control

Decision: use one decision key. A retry returns the existing result without duplicate records.

## Unresolved Dependencies

### Material-Risk Priority Source

The implementation must use an existing approved material-risk priority. ACE must not invent or recalculate the priority during Relationship Review.

If no approved priority exists, ACE orders those proposals by waiting time.

### Real Client Data

Held at G0. Real client Relationship Review requires approved storage, retention, access and privacy rules.
