# Evidence Review Workflow

**Status:** Approved for fictional implementation. Real client use remains held at G0.

## Purpose And Owner

This workflow lets the accountable auditor inspect one Evidence Item, confirm its source context and record its review status. The auditor can also propose how it relates to Audit Questions.

Evidence Review does not approve a relationship, MATE Assessment or conclusion.

## Trigger

The auditor manually opens an item from the active Engagement Evidence Inbox.

ACE can show the next `PENDING_REVIEW` item. It must not mark an item as reviewed automatically.

## Required Inputs And Access

- An authenticated auditor session.
- One active Engagement.
- One Evidence Item in that Engagement.
- Access to the original image or source reference.
- The Evidence Provider, when known.
- Source title or originator.
- Source version, date or capture time.
- Source location or capture context.
- A description of what the item shows or records.
- Freshness or currency status.
- Applicable Audit Questions, when known.

## Ordered Actions

1. The auditor opens one Evidence Item from the active Engagement Evidence Inbox.
2. ACE shows the original image or exact source reference.
3. ACE shows the Evidence ID and Engagement.
4. ACE shows capture or registration details.
5. The auditor confirms or records the Evidence Provider.
6. The auditor confirms or records source title, version or date and location.
7. The auditor records a factual description of the item.
8. The auditor classifies freshness as current, stale, superseded or uncertain.
9. The auditor records source limitations or quality concerns.
10. The auditor checks for a duplicate or a derived Evidence Item.
11. The auditor selects zero or more applicable Audit Questions.
12. For each selected question, the auditor proposes one Evidence Relevance classification: supports, weakens or contradicts.
13. The auditor records a rationale for each proposed classification.
14. ACE saves each link as a versioned Proposed Relationship.
15. The auditor records any missing, unavailable, stale or inadequate evidence as an Evidence Gap.
16. The auditor confirms the Evidence Item review.
17. ACE changes the item from `PENDING_REVIEW` to `REVIEWED`.
18. ACE records the reviewer, time, notes and one review audit event.
19. ACE sends proposed links to the Relationship Review queue.
20. If the item has no proposed link, ACE places it in the Reviewed Unlinked queue.

The `REVIEWED` state confirms inspection of the Evidence Item. It does not mean that a relationship or conclusion is approved.

## Human Checkpoints

### Source Identity Check

The auditor decides whether the displayed material matches the Evidence ID and Engagement.

### Source Context Check

The auditor decides whether the provider, origin, version or date, location and freshness are sufficiently recorded.

### Relevance Proposal Check

For each proposed link, the auditor decides whether the item supports, weakens or contradicts the selected Audit Question and records why.

This is a proposal checkpoint. Relationship Review gives the approval decision.

### Review Completion Check

The auditor confirms that the item is ready to leave `PENDING_REVIEW`.

## Outputs And Storage

- One reviewed Evidence Item.
- One source-context record.
- One Evidence Provider reference, when known.
- One freshness classification.
- Zero or more versioned Proposed Relationships.
- Zero or more Evidence Gaps.
- One Evidence Review record.
- One review audit event.
- One Relationship Review queue entry for each proposal.
- One Reviewed Unlinked queue entry when no relationship is proposed.

All records and media remain in the external ACE data store.

## Idempotency And Retry

- One review-attempt key identifies each save attempt.
- A retry with the same key returns the saved Evidence Review.
- ACE must not create duplicate Proposed Relationships for one attempt.
- Leaving the page before confirmation keeps the work as a draft.
- Reopening a draft returns the last saved fields.
- A correction after `REVIEWED` must preserve the earlier review record.

## Failure And Escalation Behaviour

| Failure | ACE Behaviour | Auditor Action |
| --- | --- | --- |
| Original cannot open | Block review completion | Check storage or source reference |
| Wrong Engagement | Block completion and offer correction | Reassign with an audit event |
| Required source context missing | Keep review as draft | Complete or mark the field unknown with a reason |
| Duplicate item suspected | Show both items and block silent deletion | Confirm duplicate handling |
| Freshness uncertain | Permit review with `UNCERTAIN` | Record the limitation |
| Proposed link lacks rationale | Do not create that proposal | Add the rationale |
| Save response lost | Return the existing review after retry | Confirm the review state |
| Data store unavailable | Save no completed review | Stop and report the fault |

ACE must not delete, overwrite or silently merge Evidence Items.

## Privacy And Credential Constraints

- Use fictional, public or AuditCo-owned material until G0 passes.
- Keep media and review records outside the repository.
- Do not send evidence to extraction, graph or external builder services.
- Do not expose private auditor notes to a future Client View.
- Do not store credentials in evidence metadata or notes.

## Observability

A successful run proves all of these facts:

- the original or source reference was available;
- the Evidence Item is `REVIEWED`;
- the reviewer and time are recorded;
- source context and freshness are recorded;
- every proposed relevance classification has a rationale;
- every proposal enters Relationship Review;
- an unlinked reviewed item remains visible; and
- one review audit event exists.

## Acceptance Criteria

1. Review is unavailable without authentication.
2. The Evidence ID and active Engagement remain visible.
3. Review cannot complete when the original or source reference is unavailable.
4. Source context and freshness are recorded.
5. Evidence Provider and Accountable Role remain separate concepts.
6. Evidence can support, weaken or contradict several Audit Questions.
7. Each proposed classification has its own rationale and version.
8. Evidence Review creates no Approved Relationship.
9. `REVIEWED` does not approve MATE or a conclusion.
10. Evidence Gaps remain separate from Evidence Items and findings.
11. Save retries create no duplicate review or proposal.
12. Corrections preserve previous completed review records.
13. Unlinked reviewed items remain visible for later classification.
14. Review creates an audit event.

## Resolved Decisions

### Review Without A Proposed Relationship

Decision: **Yes.** Mark it `REVIEWED` and place it in a visible Reviewed Unlinked queue. Do not permit it to support a conclusion until a relationship is approved.

### Corrections After Review

Decision: edit drafts directly.

After `REVIEWED`, create a new review version, record the correction reason and preserve the earlier record.

## Unresolved Dependencies

### Duplicate Handling

The duplicate merge or cross-reference process needs a separate workflow. Evidence Review must not silently delete duplicates.

### Real Client Data

Held at G0. Real client Evidence Review requires approved storage, retention, access and privacy rules.
