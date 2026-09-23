# ACE Auditor Workbench Build Specification

**Status:** Approved build specification. Real client use remains held at G0.

**Date:** 13 August 2026

## Problem Statement

ACE has a tested decision core and six approved auditor workflows.

The current workbench proves iPhone image capture and evidence review. It does
not yet give the auditor one complete place to perform the six workflows.

The next build must connect the user interface to the approved domain rules.
It must keep each source, relationship, decision and version visible.

The auditor must remain the only approval authority. ACE must help the auditor
see the evidence and apply the approved gates.

The current build uses fictional, public or AuditCo-owned information only.
Real client information remains blocked until G0 is approved.

## Solution

Build one private, responsive auditor workbench in the existing FastAPI
application.

The workbench will support these six approved workflows:

1. Engagement Setup.
2. Field Evidence Capture.
3. Evidence Review.
4. Relationship Review.
5. MATE Assessment.
6. Conclusion Review.

Use the existing ACE domain models and approval engines for controlled
decisions. Do not copy decision rules into the page code.

Add versioned JSON interfaces beside the server-rendered pages. These
interfaces will support the current web page and a possible future SwiftUI
app. FastAPI and the ACE domain engines remain the source of truth.

Keep the current external evidence and database storage boundary. Do not store
captured evidence in source control.

Show the auditor a built-in dashboard. It must show the active Engagement,
work queues, blocks, warnings, progress and approved relationship chain.

## User Stories

### Engagement Setup

1. As an auditor, I can create one fictional Engagement.
2. As an auditor, I can record its authority, purpose and reference.
3. As an auditor, I can record scope, exclusions and review dates.
4. As an auditor, I can select the permitted data classification.
5. As an auditor, I can see the accountable auditor.
6. As an auditor, I can save an incomplete Engagement as `DRAFT`.
7. As an auditor, I can approve a safe Engagement as `READY_FOR_CAPTURE`.
8. As an auditor, I can see the active Engagement near each capture action.
9. As an auditor, I cannot activate real client work before G0 approval.

### Field Evidence Capture

10. As an auditor, I can capture one image from iPhone Safari.
11. As an auditor, I can select an existing image when Safari permits it.
12. As an auditor, I can see preparation and upload status.
13. As an auditor, I cannot submit the same upload twice.
14. As an auditor, I receive one Evidence ID after a successful upload.
15. As an auditor, I can see the saved image preview.
16. As an auditor, I can see the image in the active Engagement inbox.
17. As an auditor, I can retry safely after a network failure.
18. As an auditor, I receive no Evidence Item after a rejected upload.

### Evidence Review

19. As an auditor, I can open each `PENDING_REVIEW` Evidence Item.
20. As an auditor, I can see the original image and its Evidence ID.
21. As an auditor, I can record provider and source details.
22. As an auditor, I can record a factual description.
23. As an auditor, I can classify source freshness.
24. As an auditor, I can record quality limits and Evidence Gaps.
25. As an auditor, I can propose links to Audit Questions.
26. As an auditor, I can state if evidence supports, weakens or contradicts.
27. As an auditor, I must give a reason for each proposed link.
28. As an auditor, I can mark the item `REVIEWED` without approving a link.
29. As an auditor, I can see reviewed items that have no proposed link.

### Relationship Review

30. As an auditor, I can open the Relationship Review queue.
31. As an auditor, I can see both linked records and the relationship type.
32. As an auditor, I can see source support, gaps and contradictions.
33. As an auditor, I can see the full version and decision history.
34. As an auditor, I can save an incomplete review as a draft.
35. As an auditor, I can approve, reject or require changes.
36. As an auditor, I must record a written reason for a final decision.
37. As an auditor, I cannot approve an old Relationship Version.
38. As an auditor, I can see an Approved Relationship only after approval.

### MATE Assessment

39. As an auditor, I can open a MATE queue for approved Control traces.
40. As an auditor, I can review Mandate, Accountability, Trigger and Escalation.
41. As an auditor, I can see each proposal, source passage and limitation.
42. As an auditor, I can see weakening and contradictory evidence.
43. As an auditor, I can approve, reject or require changes for each dimension.
44. As an auditor, I must record a review note for each final decision.
45. As an auditor, I cannot complete MATE with an unresolved block.
46. As an auditor, I can see the deterministic rating after four approvals.
47. As an auditor, I cannot edit the calculated MATE rating.

### Conclusion Review

48. As an auditor, I can open the Conclusion Review queue.
49. As an auditor, I can see the Accepted Planning Trace and MATE rating.
50. As an auditor, I can review Implementation and Effectiveness separately.
51. As an auditor, I can see each evidence matrix, gap and contradiction.
52. As an auditor, I can see the Requirement-Evidence-Reasoning Chain.
53. As an auditor, I can see alternatives, challenges, assumptions and limits.
54. As an auditor, I can use an optional AI Advisory Panel for suggestions.
55. As an auditor, I can use an optional Human Review Council for challenge.
56. As an auditor, I can see that advice has no approval authority.
57. As an auditor, I can approve, reject or require changes for each conclusion.
58. As an auditor, I must record my reason and evidence-sufficiency decision.
59. As an auditor, I cannot save an inconsistent conclusion pair.
60. As an auditor, I receive one frozen accepted record after all gates pass.

### Dashboard And Navigation

61. As an auditor, I can see the active Engagement on the dashboard.
62. As an auditor, I can see counts for each work queue.
63. As an auditor, I can see blocked work and the blocking reason.
64. As an auditor, I can move from a record to its source and related records.
65. As an auditor, I can move forward and backward through the approved chain.
66. As an auditor, I can see current status with text and symbols.
67. As an auditor, I can use the workbench at iPhone portrait widths.
68. As an auditor, I can reach the capture action with one hand.
69. As an auditor, I can see the same controlled terms on each screen.
70. As an auditor, I can see my saved decision and its audit event.

## Implementation Decisions

1. Keep the existing FastAPI application and routes.
2. Keep HTTP Basic authentication during the fictional pilot.
3. Keep image-only capture in the current build.
4. Keep external local media and database storage.
5. Keep the evidence states `PENDING_REVIEW` and `REVIEWED`.
6. Add Engagement context before more workflow records enter the workbench.
7. Use the approved workflow documents as interaction rules.
8. Use the existing domain engines for MATE, trace and conclusion gates.
9. Keep proposed records separate from approved records.
10. Keep every approved decision immutable and version-specific.
11. Require unique retry keys for final saves and capture attempts.
12. Create no partial final record after a failed gate or save.
13. Record one immutable audit event for each final decision.
14. Use Australian English labels.
15. Use responsive server-rendered pages for the current interface.
16. Add versioned JSON interfaces for workbench data and actions.
17. Use one service layer for page routes and JSON routes.
18. Do not let a future mobile client copy approval logic.
19. Keep the Requirement-Evidence-Reasoning Chain visible before conclusions.
20. Mark all advisory AI and council content as advice only.
21. Keep the Accountable Auditor as the only approval authority.
22. Keep real client information blocked at G0.
23. Keep the native SwiftUI app on the roadmap only.

## Testing Decisions

Use the FastAPI application boundary as the main integration-test seam.

Use the existing pure approval-engine tests for controlled domain rules.

Add tests for:

1. Authentication on every workbench page and JSON interface.
2. Fictional Engagement creation and activation.
3. G0 rejection of unapproved real client Engagements.
4. Active Engagement checks during capture and review.
5. Capture retry keys and duplicate prevention.
6. Image validation and external storage.
7. Evidence review state changes and audit events.
8. Proposed Relationship creation and version checks.
9. Approval, rejection and changes-required paths.
10. Immutable approved records and decisions.
11. MATE gate blocks and deterministic ratings.
12. Conclusion gate blocks and accepted records.
13. No partial records after a failed transaction.
14. JSON and page routes returning the same controlled state.
15. Mobile layout contracts and accessible text labels.
16. Fictional evidence controls and prohibited capability checks.

Use temporary external storage for tests. Do not write test evidence into the
source workspace.

Test the complete fictional path:

`Engagement → Capture → Evidence Review → Relationship Review → MATE → Conclusion`.

Keep a physical iPhone Safari test for capture, preview, touch position and
safe-area behaviour. Automated tests cannot prove all Safari camera behaviour.

## Out Of Scope

- Real client Engagements or evidence.
- Client-facing access.
- A native SwiftUI app in the current build.
- Offline queues.
- Audio, video, OCR or transcription.
- LangExtract connection.
- Neo4j, Semantica or another graph database.
- LangGraph workflow control.
- Public hosting or tunnels for real evidence.
- Automatic approval by AI or another software tool.
- Findings, recommendations, actions or final reports.

## Further Notes

The future SwiftUI app will use the Xcode iOS App template with SwiftUI and
Swift. It will use the shared ACE JSON API. FastAPI will remain the source of
truth.

The first future app can use Home, Work, Capture and Map areas. It must use
Keychain for credentials. It must not store a second authoritative audit
record.

The next Pockock step can convert this specification into small tickets. Do
not start implementation until the ticket order and acceptance checks are
approved.
