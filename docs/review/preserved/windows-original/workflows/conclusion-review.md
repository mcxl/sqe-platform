# Conclusion Review Workflow

**Status:** Approved for fictional implementation. Real client use remains held at G0.

## Purpose And Owner

This workflow lets the Accountable Auditor approve separate Implementation and Effectiveness Conclusions.

The workflow starts from one Accepted Planning Trace. It does not change planning relationships or the MATE rating.

It does not create findings, recommendations, actions or reports.

## Trigger

The auditor manually opens the Conclusion Review queue for the active Engagement.

ACE shows the highest material-risk active review first. Within the same priority, ACE shows the oldest review first.

The auditor can select another review.

## Required Inputs And Access

- An authenticated auditor session.
- One active Engagement.
- One Accepted Planning Trace.
- One Approved MATE Assessment and immutable MATE rating.
- One approved Main Audit Question.
- One approved Implementation Question.
- One approved Effectiveness Question.
- The same Control identifier across the trace and questions.
- One Implementation evidence matrix.
- One Effectiveness evidence matrix.
- One current Conclusion Proposal for each conclusion type.
- One unique decision key for each final decision.

The current pilot uses fictional, public or AuditCo-owned information only.

## Ordered Actions

1. The auditor opens the Conclusion Review queue.
2. ACE shows ready, draft, blocked, awaiting-one-decision and accepted records.
3. ACE orders active work by material risk, then waiting time.
4. The auditor selects one review.
5. ACE validates the Accepted Planning Trace and Control identity.
6. ACE shows the full planning trace and immutable MATE rating.
7. ACE shows the three approved Audit Questions.
8. ACE starts the separate Implementation Review.
9. ACE shows the Implementation Question and evidence matrix.
10. ACE shows each evidence source, origin, freshness and relevance.
11. ACE shows gaps, contradictions, assumptions and limitations.
12. ACE shows the current Implementation Conclusion Proposal.
13. ACE shows the Requirement-Evidence-Reasoning Chain.
14. The auditor can save incomplete work as a draft.
15. The auditor selects `APPROVED`, `REJECTED` or `CHANGES_REQUIRED`.
16. The auditor records a review note and final evidence-sufficiency decision.
17. ACE validates the exact proposal version and conclusion type.
18. ACE saves one Auditor Conclusion Decision and one audit event.
19. ACE then opens the separate Effectiveness Review.
20. ACE repeats the evidence, reasoning and decision checks.
21. ACE checks the dependency between both approved outcomes.
22. ACE creates no final record until both decisions are approved.
23. ACE creates one frozen Accepted Evidence-to-Conclusion Record.
24. ACE shows the accepted record and updated queue.

## Separate Review Parts

### Implementation Review

This review asks whether the approved Control was put into practice.

It uses its own question, evidence matrix, proposal and Auditor Decision.

### Effectiveness Review

This review asks whether the implemented Control achieved its intended result.

It uses its own question, evidence matrix, proposal and Auditor Decision.

The same Evidence Item can appear in both matrices. Each use needs a separate entry and rationale.

## Evidence Matrix Rules

Each Evidence Item records:

- Evidence ID;
- title and description;
- source title or originator;
- source version or date;
- precise source location;
- collection time;
- validity period;
- origin; and
- freshness.

Evidence origin is `RAW`, `DERIVED` or `AUDITOR_AUTHORED`.

Evidence freshness is `CURRENT`, `STALE`, `SUPERSEDED` or `UNCERTAIN`.

Each matrix entry records `SUPPORTS`, `WEAKENS` or `CONTRADICTS`. It also records a plain-English rationale.

Derived evidence must identify its raw source. Origin does not determine evidential weight or sufficiency.

## Gap And Contradiction Rules

Each Evidence Gap records its status, explanation, materiality and disposition.

Gap disposition is `OPEN`, `RESOLVED` or `ACCEPTED_LIMITATION`.

A resolved or accepted-limitation gap requires an auditor rationale.

An open material gap blocks a substantive conclusion.

An unresolved contradiction also blocks a substantive conclusion.

A gap or contradiction does not automatically create a negative conclusion.

## Controlled Outcomes

Implementation outcomes are:

- `IMPLEMENTED`;
- `PARTIALLY_IMPLEMENTED`;
- `NOT_IMPLEMENTED`; and
- `NOT_DETERMINED`.

Effectiveness outcomes are:

- `EFFECTIVE`;
- `PARTIALLY_EFFECTIVE`;
- `INEFFECTIVE`; and
- `NOT_DETERMINED`.

`NOT_DETERMINED` records that evidence cannot support a substantive conclusion.

It must state the evidence limitation. It is not a pass or failure.

## Human Checkpoints

### Entry Check

The auditor confirms the trace, Control, MATE rating and three approved questions.

The MATE rating provides context. It does not decide Implementation or Effectiveness.

### Evidence Check

The auditor checks provenance, freshness, relevance, gaps, contradictions, assumptions and limitations.

### Proposal Check

The auditor checks the exact proposal version and its Requirement-Evidence-Reasoning Chain.

### Conclusion Decision Check

The auditor selects one controlled decision and records the review note.

Approval must match the displayed proposal outcome.

A different outcome requires `CHANGES_REQUIRED` and a new proposal version.

Implementation and Effectiveness require separate decisions.

### Final Consistency Check

The auditor confirms that both outcomes are internally consistent.

## Requirement-Evidence-Reasoning Chain

Each proposal shows these elements:

1. **Requirement** — the approved source, clause, version, jurisdiction and applicability.
2. **Question** — the approved Implementation or Effectiveness Question.
3. **Claim** — the proposed controlled outcome.
4. **Evidence** — supporting, weakening and contradictory evidence.
5. **Reasoning Link** — why each item supports or challenges the claim.
6. **Alternative** — at least one plausible different outcome.
7. **Challenge** — assumptions, gaps, contradictions and disconfirming evidence.
8. **Limits** — uncertainty, accepted limitations and unresolved matters.
9. **Auditor Decision** — the final professional decision.

## Evidence Sufficiency Gate

A substantive conclusion requires:

- `SUFFICIENT` evidence;
- at least one current relied-upon Evidence Item;
- no unresolved contradiction; and
- no open material Evidence Gap.

An approved `NOT_DETERMINED` outcome requires `INSUFFICIENT` or `UNRESOLVED` evidence.

It must state the evidence limitation. It cannot claim that the Control passed or failed.

## Implementation And Effectiveness Dependency

`IMPLEMENTED` and `PARTIALLY_IMPLEMENTED` can proceed to a substantive Effectiveness Conclusion.

`NOT_IMPLEMENTED` requires the Effectiveness outcome to be `NOT_DETERMINED`.

A `NOT_DETERMINED` Implementation Conclusion also requires `NOT_DETERMINED` Effectiveness.

ACE blocks an inconsistent pair. ACE does not approve Effectiveness automatically.

## Advisory Guidance

### AI Advisory Panel

For material fictional cases, ACE can pilot these guidance roles:

- Requirements Interpreter;
- Evidence Analyst;
- Alternative-Outcome Challenger;
- Operational Context Reviewer; and
- Traceability Checker.

Each role creates a separate labelled guidance note.

These roles are not independent people. Agreement creates no approval or independent assurance.

### Human Review Council

For selected fictional cases, ACE can pilot these roles:

- Accountable Auditor as chair;
- Legal Adviser;
- Technical Specialist;
- Operations Representative; and
- Independent Audit Reviewer.

Use the council when legal applicability is disputed or specialist competence is required.

It can also be used when consequences are high.

ACE records each view before discussion. It keeps disagreement visible.

Only the Accountable Auditor makes the ACE decision.

Ordinary challenge remains inside Conclusion Review.

The formal CONTRA engine remains outside this workflow until SQE approves it.

## Outputs And Storage

- Zero or more saved drafts.
- One immutable Implementation Auditor Decision.
- One immutable Effectiveness Auditor Decision.
- One audit event for each final decision.
- One frozen Accepted Evidence-to-Conclusion Record after all gates pass.
- Updated queue status.

The accepted record contains:

- the Accepted Planning Trace and MATE rating;
- three approved Audit Questions;
- both evidence matrices;
- evidence, gaps, contradictions and limitations;
- both exact Conclusion Proposal versions;
- both Auditor Decisions; and
- both approved outcomes.

All records stay in the external ACE data store. They do not enter the source repository.

ACE returns no partly accepted record.

## Idempotency And Retry

- One decision key identifies each final decision attempt.
- A retry with the same key returns the existing decision.
- A retry creates no duplicate decision or audit event.
- ACE saves each decision and audit event as one controlled operation.
- A failed save creates no partial decision or audit event.
- A draft creates no final decision outcome.
- ACE never edits an accepted record.
- A later change starts new proposal and record versions.
- ACE preserves all earlier records and decisions.

## Failure And Escalation Behaviour

| Failure | ACE Behaviour | Auditor Action |
| --- | --- | --- |
| Accepted Planning Trace is missing | Block review | Complete the planning trace |
| Control identifiers do not match | Block review | Correct the question or trace |
| An Audit Question is not approved | Block review | Complete question approval |
| Evidence matrix is missing | Keep the review as draft | Complete the matrix |
| Derived evidence lacks a raw source | Block the conclusion | Correct the evidence lineage |
| Current relied-upon evidence is missing | Block a substantive conclusion | Gather current evidence |
| Material Evidence Gap is open | Block a substantive conclusion | Resolve or accept the limitation |
| Contradiction remains unresolved | Block a substantive conclusion | Resolve and explain it |
| Proposal and decision versions differ | Reject the stale save | Open the current proposal |
| Approved outcome differs from proposal | Require `CHANGES_REQUIRED` | Create a new proposal version |
| Outcome pair is inconsistent | Block the final record | Correct the Effectiveness proposal |
| Review note is missing | Block the decision | Record the note |
| Decision save fails | Save no decision | Retry with the same decision key |
| Audit event save fails | Save no decision | Stop and report the fault |
| Data store is unavailable | Save no record | Stop and report the fault |

ACE shows the blocked conclusion type and reason in plain English.

## Privacy And Credential Constraints

- Only the Accountable Auditor can approve conclusions.
- Use fictional, public or AuditCo-owned information until G0 passes.
- Keep evidence, guidance, proposals and decisions outside the repository.
- Do not send evidence to public reasoning, diagram or graph services.
- Do not expose private auditor notes to a future Client View.
- Do not store credentials in evidence, reasoning or review notes.
- Keep ACE as the source of truth.
- AI can reference approved requirements and provide traceable guidance.
- AI cannot decide applicability, sufficiency or conclusions.
- AI and council votes cannot approve records.

## Observability

A successful accepted record proves all these facts:

- the planning trace and MATE rating were visible;
- the three Audit Questions were approved;
- the same Control identifier was used throughout;
- Implementation and Effectiveness used separate matrices and proposals;
- evidence provenance, origin and freshness remained visible;
- gaps, contradictions, assumptions and limitations remained visible;
- each conclusion used the Requirement-Evidence-Reasoning Chain;
- both decisions matched exact proposal versions;
- each decision recorded the auditor, time, note and sufficiency decision;
- both outcomes passed the dependency check;
- one frozen accepted record exists; and
- retries created no duplicate decisions or events.

## Acceptance Criteria

1. Conclusion Review is unavailable without authentication.
2. The active Engagement remains visible.
3. The queue shows ready, draft, blocked, awaiting and accepted records.
4. ACE orders active work by material risk, then waiting time.
5. The auditor can select another review.
6. ACE shows the trace, MATE rating and three questions before review.
7. All questions use the same Control identifier.
8. Implementation and Effectiveness remain separate.
9. Each review uses its own evidence matrix and proposal.
10. Evidence used twice has separate entries and rationales.
11. Evidence origin, freshness and relevance remain visible.
12. Derived evidence links to raw evidence.
13. Gaps and contradictions remain visible.
14. Open material gaps block substantive conclusions.
15. Unresolved contradictions block substantive conclusions.
16. Gaps do not automatically create negative conclusions.
17. Controlled outcomes match the approved vocabulary.
18. `NOT_DETERMINED` states its evidence limitation.
19. The auditor can save a draft.
20. Every final decision requires a review note and sufficiency decision.
21. Approval matches the exact current proposal.
22. A different outcome creates a new proposal version.
23. Both conclusion decisions remain separate.
24. ACE blocks an inconsistent outcome pair.
25. ACE creates no partly accepted record.
26. ACE creates one frozen record after all gates pass.
27. Later changes create new versions.
28. A failed save creates no partial decision.
29. A retry creates no duplicate decision or audit event.
30. AI guidance creates no approval.
31. Records remain outside the repository.

## Resolved Decisions

### Entry Gate

Decision: require one accepted trace, MATE rating and three approved questions for the same Control.

### Review Separation

Decision: keep Implementation and Effectiveness evidence, proposals and decisions separate.

### Evidence Matrix

Decision: show origin, provenance, freshness, relevance, gaps, contradictions, assumptions and limitations.

### Controlled Outcomes

Decision: use the approved Implementation, Effectiveness and `NOT_DETERMINED` outcomes.

### Approval Gate

Decision: require current evidence and no unresolved material blocker for a substantive conclusion.

### Dependency Gate

Decision: prevent Effectiveness from bypassing an unimplemented or undetermined Control.

### Reasoning Method

Decision: use the Requirement-Evidence-Reasoning Chain for every proposal.

### Advisory Review

Decision: pilot AI and human councils with fictional cases. Council agreement creates no approval.

### Version Control

Decision: freeze accepted records. A later change creates new versions.

### Human Authority

Decision: the Accountable Auditor decides applicability, sufficiency, outcomes and approval.

## Unresolved Dependencies

### Material-Risk Priority Source

The implementation must use an existing approved material-risk priority.

If no approved priority exists, ACE orders active reviews by waiting time.

### Applicable Requirement Library

Implementation needs controlled reference metadata, licences, versions and applicability decisions.

### Advisory Council Pilot

The proposed AI and human council roles require fictional pilot tests and approval.

### Durable Identity And Storage

Implementation needs durable auditor identity, storage, version history and audit events.

### Formal CONTRA

The formal CONTRA engine remains outside this workflow. It needs separate design and approval.

### Real Client Data

Held at G0. Real client use needs approved storage, retention, access and privacy rules.
