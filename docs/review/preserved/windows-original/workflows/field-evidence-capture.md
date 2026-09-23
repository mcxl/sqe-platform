# Field Evidence Capture Workflow

**Status:** Approved for fictional implementation. Real client use remains held at G0.

## Purpose And Owner

This workflow creates one controlled Evidence Item from an iPhone photograph. The accountable auditor owns the workflow and confirms the capture context.

## Trigger

The auditor manually taps **Capture Evidence** while an Engagement is active.

ACE blocks capture when no Engagement is active. ACE does not require the auditor to select relationships before capture.

## Required Inputs And Access

- An authenticated auditor session.
- One active Engagement.
- iPhone Safari with camera access.
- A private connection to ACE.
- An available external evidence store.
- Fictional, public or AuditCo-owned subject matter during the current pilot.

## Ordered Actions

1. The auditor opens the active Engagement.
2. ACE shows the Engagement name beside **Capture Evidence**.
3. The auditor taps **Capture Evidence**.
4. Safari opens the rear camera or image picker.
5. The auditor takes or selects one image.
6. ACE shows **Preparing capture**.
7. ACE validates the image type and size before upload.
8. ACE shows **Uploading** and disables duplicate submission.
9. The server validates the image content.
10. The server creates one Evidence ID.
11. The server stores the original image in the external evidence store.
12. The server records the Evidence Item against the active Engagement.
13. The Evidence Item starts as `PENDING_REVIEW`.
14. ACE records a capture audit event.
15. ACE shows the Evidence ID and a direct preview.
16. ACE places the item in the Engagement Evidence Inbox.
17. The auditor can add context now or continue capturing.

Relationship classification occurs later during Evidence Review. Capture does not approve evidence, relationships or conclusions.

## Human Checkpoints

### Capture Context Check

After a successful upload, the auditor checks:

- the displayed Engagement;
- the photograph preview; and
- the Evidence ID.

The auditor decides whether the capture belongs to the intended Engagement. A correction must create an audit event.

## Outputs And Storage

- One original image in the external evidence store.
- One Evidence Item with an Evidence ID and `PENDING_REVIEW` status.
- One reference to the active Engagement.
- One capture audit event.
- One item in the Engagement Evidence Inbox.

No image or database file is stored in the source repository.

## Idempotency And Retry

- The phone creates one capture-attempt key before upload.
- A retry with the same key returns the existing Evidence ID.
- ACE must not create a second Evidence Item for the same successful attempt.
- Cancelling the camera creates no record.
- A rejected upload creates no Evidence Item.
- If storage fails, ACE fails closed and reports the failure.

## Failure And Escalation Behaviour

| Failure | ACE Behaviour | Auditor Action |
| --- | --- | --- |
| Camera cancelled | Return to the workbench without a record | Continue or try again |
| Image cannot be read | Show a clear failure message | Take another photograph |
| Image type or size rejected | Create no Evidence Item | Use an allowed image |
| Connection lost before success | Keep the attempt key | Retry the same attempt |
| Upload stored but response lost | Return the existing Evidence ID after retry | Confirm the preview |
| Evidence store unavailable | Create no completed capture record | Stop capture and report the fault |
| Wrong Engagement selected | Record a correction event | Reassign during review |

ACE must not silently move, replace or delete an Evidence Item.

## Privacy And Credential Constraints

- Keep the connection private.
- Do not put passwords in source files, URLs or audit records.
- Do not use real client evidence before G0 approval.
- Keep original media outside the repository.
- Do not send captured media to extraction, graph or external builder services.

## Observability

A successful run proves all of these facts:

- one Evidence ID was returned;
- one original image exists;
- one Evidence Item exists;
- its status is `PENDING_REVIEW`;
- it references the active Engagement;
- one capture audit event exists; and
- the auditor can open the preview.

## Acceptance Criteria

1. Capture is unavailable without authentication.
2. The active Engagement is visible before and after capture.
3. The input remains compatible with the iPhone rear camera.
4. Only valid image content is accepted.
5. Duplicate submissions create one Evidence Item.
6. A successful capture shows its Evidence ID.
7. The original image remains outside the repository.
8. The new item enters `PENDING_REVIEW`.
9. The item appears in the correct Engagement Evidence Inbox.
10. Preview opens the image in one step.
11. Capture creates no relationship approval or conclusion.
12. A fictional iPhone test passes for ten consecutive captures.

## Resolved Decisions

### Active Engagement Requirement

Decision: **Yes.** Permit rapid capture into the active Engagement's Evidence Inbox. Defer detailed relationship classification until Evidence Review.

## Unresolved Dependencies

### Real Client Data

Held at G0. Real client use requires client acceptance and approved storage, security, retention and access rules.

### Offline Capture

Not included. A protected offline queue requires a separate workflow and security decision.
