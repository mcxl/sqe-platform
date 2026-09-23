# ACE Workflow Notes

These notes describe the current reality for the private ACE Auditor Workbench. Use [CONTEXT.md](CONTEXT.md) for canonical domain terms.

## Owner And Purpose

The accountable auditor owns each workflow and every professional decision. ACE records work, displays relationships and enforces approval gates.

## Workflow Map

1. **Engagement Setup** — create the engagement, authority, scope and active review period.
2. **Field Evidence Capture** — capture an image and create a controlled Evidence Item.
3. **Evidence Review** — record source details, relevance, gaps, contradictions and limitations.
4. **Relationship Review** — propose, approve, reject or change versioned relationships.
5. **MATE Assessment** — assess control design for mandate, accountability, trigger and escalation.
6. **Conclusion Review** — separately propose and approve implementation and effectiveness conclusions.

Each workflow needs its own implementation specification. Do not combine all six into one screen or one automatic process.

## Current Tools And Channels

- ACE is an auditor-facing FastAPI web application.
- iPhone Safari supports fictional image capture through the rear camera.
- The desktop workbench supports evidence review and later relationship work.
- Original media and the SQLite database stay outside the source repository.
- The HTML progress guide shows build status. It is not an audit record.
- Mermaid CLI renders the controlled local diagram source as SVG files.
- Diagram Design creates faithful presentation copies for auditor guidance only.
- Neither diagram layer stores evidence or changes an approval decision.

## Current Controls

- HTTP Basic authentication remains the local control.
- The hosted fictional test also used a private session login.
- Image capture creates an Evidence ID.
- New captures start as `PENDING_REVIEW`.
- A completed media review changes the item to `REVIEWED`.
- `REVIEWED` does not mean that a relationship or conclusion is approved.
- MATE and conclusion approval gates remain authoritative.

## Privacy And Scope Constraints

- Client acceptance has not been received.
- Use only fictional, public or AuditCo-owned material.
- Do not put evidence in the repository, Explorer folders or temporary build folders.
- Do not use public hosting or public tunnels.
- Do not give the client access yet.
- Do not add LangExtract, Neo4j or LangGraph to the first workflows.

## Known Failure Cases

- The phone loses its connection during upload.
- Safari or the user submits the same capture twice.
- The upload succeeds, but the phone does not receive the response.
- The image is damaged, too large or has the wrong media type.
- The evidence store is unavailable.
- The capture is assigned to the wrong engagement.
- A reviewed item remains unlinked to an audit question.
- An unresolved contradiction or material gap is hidden from the conclusion review.

## Approved Domain Rules

The ten approved rules in the progress guide control all workflow designs. Important controls include:

- Evidence Providers and Accountable Roles are separate.
- Accountable Roles are stable job roles with dated Role Assignments.
- Relationships are many-to-many, versioned and independently decided.
- Evidence can support, weaken or contradict an Audit Question.
- Evidence Gaps remain visible and are not automatic findings.
- MATE assesses control design only.
- Implementation and Effectiveness Conclusions remain separate.
- Approved records are never overwritten.
- Open material gaps and unresolved contradictions block substantive conclusions.

## Approved Workflow Decision

The first detailed workflow is Field Evidence Capture. It requires an active Engagement but permits relationship classification later.

## Approved Engagement Workflow Decisions

The second detailed workflow is Engagement Setup.

- Several Engagements can remain open, but each session has one selected capture context.
- Scope can be edited while the Engagement is `DRAFT`.
- After activation, a scope change creates a new version, records the reason and requires approval before more capture.

## Approved Evidence Review Decisions

The third detailed workflow is Evidence Review.

- A reviewed item can remain unlinked in a visible queue.
- An unlinked item cannot support a conclusion.
- Draft reviews are editable.
- A correction after `REVIEWED` creates a new review version and preserves the earlier record.
- Evidence Review can create proposals, but Relationship Review approves them.

## Approved Relationship Review Decisions

- ACE shows one Proposed Relationship at a time.
- ACE shows its source support, rationale and version history beside the proposal.
- The auditor chooses `APPROVED`, `REJECTED` or `CHANGES_REQUIRED`.
- Every Auditor Decision requires a written reason.
- `CHANGES_REQUIRED` never changes the existing proposal.
- ACE creates a new Relationship Version and keeps the previous version and Auditor Decision visible.
- ACE shows open Evidence Gaps and unresolved contradictions before the auditor decides.
- These warnings do not make or change the Auditor Decision automatically.
- ACE creates an Approved Relationship only when the auditor approves the current Relationship Version.
- An Auditor Decision for an earlier version cannot approve a later version.
- Before approval, ACE shows both linked records, the relationship type, source support and auditor rationale together on one screen.
- Relationship Review uses a visible queue.
- ACE orders proposals by material risk first, then by the oldest waiting proposal.
- The auditor can select a different proposal from the queue.
- Proposals that link the same records with the same relationship type are possible duplicates.
- ACE warns the auditor but does not merge or delete possible duplicates automatically.
- The auditor can save a Relationship Review as a draft.
- A draft makes no Auditor Decision and creates no Approved Relationship.
- After a decision, ACE records an immutable audit event.
- The event records the auditor, date, time, Relationship Version, decision and written reason.
- If a decision save fails, ACE shows an error and keeps the proposal undecided.
- A retry with the same decision key creates no duplicate Auditor Decision or audit event.
The Relationship Review workflow is approved for fictional implementation.

## Approved MATE Assessment Decisions

- ACE assesses one Control at a time.
- MATE can start only after the Control has approved links to its Binding Obligation, Risk and Accountable Role.
- ACE shows the linked Binding Obligation, Risk, Control and Accountable Role together before MATE starts.
- MATE does not approve these relationships.
- ACE shows one MATE dimension at a time.
- ACE uses the fixed order Mandate, Accountability, Trigger and Escalation.
- ACE shows the current position, such as `Check 2 of 4`.
- The auditor can return to an incomplete dimension.
- An approved Auditor Decision is immutable.
- Each dimension screen shows the controlled question, proposed `YES` or `NO` answer and plain-English rationale.
- Each dimension screen shows supporting, weakening and contradictory evidence.
- Each dimension screen shows Evidence Gaps, limitations, unresolved contradictions, source status and precise passage references.
- ACE does not select the MATE answer.
- For each MATE dimension, the auditor selects `APPROVED`, `REJECTED` or `CHANGES_REQUIRED`.
- Every Auditor Decision requires a written review note.
- Approval requires sufficient evidence for a control-design assessment.
- An approved answer must match the current proposal.
- If the auditor selects a different answer, the decision is `CHANGES_REQUIRED` and a new proposal version is required.
- ACE blocks MATE completion when a dimension has no current source or sufficient evidence.
- ACE blocks MATE completion when a contradiction remains unresolved.
- ACE blocks MATE completion when a dimension or Auditor Decision is missing.
- ACE blocks MATE completion when a proposal and Auditor Decision do not match.
- The auditor can save incomplete MATE work as a draft.
- Missing evidence does not automatically produce a `NO` answer.
- After all four dimensions are approved, ACE uses the existing deterministic evaluator.
- All four `YES` answers produce `ADEQUATE`.
- A `NO` answer for Mandate or Accountability produces `INADEQUATE`.
- Two or more `NO` answers produce `INADEQUATE`.
- One `NO` answer for Trigger or Escalation produces `PARTIALLY_ADEQUATE`.
- The auditor cannot edit the calculated MATE rating.
- ACE creates one frozen Approved MATE Assessment after calculation.
- The assessment records the Control identity, four approved decisions, four approved answers and calculated rating.
- The assessment records its evidence references, auditor and review times.
- ACE links the assessment to the approved Control trace.
- An Approved MATE Assessment does not create an audit conclusion.
- ACE never edits an Approved MATE Assessment.
- A change to the Control, source evidence or approved answers starts a new assessment version.
- ACE preserves the earlier assessment, rating and decisions.
- A new assessment version remains a draft until all four dimensions pass the approval gate again.
- Each MATE Auditor Decision creates an immutable audit event.
- The event records the auditor, date, time, Control, assessment version, MATE dimension, proposal version, decision and review note.
- A failed save creates no partial decision or audit event.
- A retry with the same decision key creates no duplicate Auditor Decision or audit event.
- ACE uses a visible MATE work queue.
- The queue shows Controls ready for MATE, draft assessments, blocked assessments and approved assessments requiring no action.
- ACE orders active MATE work by material risk, then by the oldest waiting item.
- The auditor can select a different Control from the queue.
- Only the authenticated auditor can make MATE decisions.
- The current build uses fictional, public or AuditCo-owned information only.
- Real client information remains blocked at G0.
- AI can organise evidence and propose answers.
- AI cannot approve answers, change the deterministic rating rules or approve conclusions.

The MATE Assessment workflow is approved for fictional implementation.

## Approved Conclusion Review Decisions

- ACE starts Conclusion Review from one Accepted Planning Trace.
- The trace includes the Approved MATE Assessment and immutable MATE rating.
- One approved Main Audit Question, Implementation Question and Effectiveness Question are required.
- All three questions must use the same Control as the Accepted Planning Trace.
- ACE shows the full trace, MATE rating and three approved questions before review.
- The MATE rating provides context. It does not decide implementation or effectiveness.
- ACE separates Implementation Review from Effectiveness Review.
- Each review has its own Audit Question, evidence matrix, classifications, gaps, contradictions, proposal and Auditor Decision.
- Evidence can appear in both reviews only through separate matrix entries and separate rationales.
- Each evidence matrix shows the Evidence ID, precise source, origin, collection date, validity period and freshness.
- Each matrix entry records `SUPPORTS`, `WEAKENS` or `CONTRADICTS` with a plain-English rationale.
- Each evidence matrix shows assumptions and limitations.
- Evidence origin is `RAW`, `DERIVED` or `AUDITOR_AUTHORED`.
- Evidence freshness is `CURRENT`, `STALE`, `SUPERSEDED` or `UNCERTAIN`.
- Derived evidence must link directly to its raw source.
- Evidence origin does not determine evidential weight or sufficiency.
- ACE shows every Evidence Gap and contradiction.
- Each gap records its status, explanation and materiality.
- Each gap disposition is `OPEN`, `RESOLVED` or `ACCEPTED_LIMITATION`.
- A resolved or accepted-limitation gap requires an auditor rationale.
- An open material gap blocks a substantive conclusion.
- An unresolved contradiction blocks a substantive conclusion.
- A gap or contradiction does not automatically create a negative conclusion.
- Implementation outcomes are `IMPLEMENTED`, `PARTIALLY_IMPLEMENTED`, `NOT_IMPLEMENTED` and `NOT_DETERMINED`.
- Effectiveness outcomes are `EFFECTIVE`, `PARTIALLY_EFFECTIVE`, `INEFFECTIVE` and `NOT_DETERMINED`.
- `NOT_DETERMINED` records that available evidence cannot support a substantive conclusion.
- A `NOT_DETERMINED` outcome states the applicable evidence limitation.
- `NOT_DETERMINED` is not a pass or failure.
- ACE shows one exact Conclusion Proposal version at a time.
- Each proposal records its proposed outcome, relied-upon evidence, considered gaps, reasoning, assumptions and limitations.
- The auditor selects `APPROVED`, `REJECTED` or `CHANGES_REQUIRED`.
- Every Auditor Conclusion Decision records a review note and final evidence-sufficiency decision.
- Approval must match the current proposal version.
- A different outcome requires `CHANGES_REQUIRED` and a new proposal version.
- Implementation and Effectiveness Conclusions require separate Auditor Decisions.
- Effectiveness depends on the approved Implementation Conclusion.
- `IMPLEMENTED` or `PARTIALLY_IMPLEMENTED` can proceed to a substantive Effectiveness Conclusion.
- `NOT_IMPLEMENTED` requires the Effectiveness outcome to be `NOT_DETERMINED`.
- A `NOT_DETERMINED` Implementation Conclusion requires a `NOT_DETERMINED` Effectiveness Conclusion.
- ACE blocks an inconsistent conclusion pair.
- ACE does not approve Effectiveness automatically. The auditor approves its separate proposal.
- A substantive conclusion requires sufficient evidence and at least one current relied-upon Evidence Item.
- A substantive conclusion requires no unresolved contradiction and no open material Evidence Gap.
- An approved `NOT_DETERMINED` outcome requires insufficient or unresolved evidence and an explicit limitation.
- A `NOT_DETERMINED` outcome cannot claim that the Control passed or failed.
- ACE creates no final record until both conclusion proposals have approved Auditor Decisions.
- ACE returns no partly accepted Evidence-to-Conclusion record.
- ACE creates one frozen Accepted Evidence-to-Conclusion Record after all gates pass.
- The record contains the Accepted Planning Trace, MATE rating and three approved Audit Questions.
- The record contains both evidence matrices, evidence, gaps, contradictions and limitations.
- The record contains both exact Conclusion Proposal versions, both Auditor Decisions and both approved outcomes.
- ACE never edits an Accepted Evidence-to-Conclusion Record.
- A later change starts new proposal and record versions. ACE preserves the earlier record.
- ACE uses a visible Conclusion Review queue.
- The queue shows ready, draft, blocked, awaiting-one-decision and accepted records.
- ACE orders active work by material risk, then by waiting time.
- Each final conclusion decision creates one immutable audit event.
- A failed save creates no partial decision or audit event.
- A retry with the same decision key creates no duplicate decision or audit event.
- ACE uses the Requirement-Evidence-Reasoning Chain for each proposed conclusion.
- The chain records the Requirement, Question, Claim, Evidence, Reasoning Link, Alternative, Challenge, Limits and Auditor Decision.
- ACE can use a fictional AI Advisory Panel for material cases.
- The proposed AI roles are Requirements Interpreter, Evidence Analyst, Alternative-Outcome Challenger, Operational Context Reviewer and Traceability Checker.
- Each AI role creates a separate labelled guidance note.
- AI role agreement does not create approval or independent assurance.
- ACE does not use an AI vote to approve a record.
- ACE can call a Human Review Council when legal applicability is disputed, specialist competence is required or consequences are high.
- The proposed human roles are Accountable Auditor, Legal Adviser, Technical Specialist, Operations Representative and Independent Audit Reviewer.
- The Accountable Auditor chairs the Human Review Council and makes the ACE decision.
- ACE records each view before group discussion and keeps disagreement visible.
- Ordinary challenge remains inside Conclusion Review.
- The formal CONTRA engine remains outside Conclusion Review until SQE separately approves it.
- Both council designs require fictional pilot testing before implementation approval.
- AI can reference approved Applicable Requirements.
- AI can provide traceable guidance, reasoning and alternative conclusions.
- Human specialists can advise on disputed matters.
- The Accountable Auditor decides applicability and evidence sufficiency.
- The Accountable Auditor approves every conclusion.
- AI agreement and council votes cannot approve ACE records.
- Real client information remains blocked at G0.

The Conclusion Review workflow is approved for fictional implementation.
