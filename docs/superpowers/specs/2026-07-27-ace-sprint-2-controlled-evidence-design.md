# ACE Sprint 2 Controlled Evidence And Auditor Approval Design

## Decision

Sprint 2 will design and, only after a separate implementation-plan approval,
build a fictional, domain-only approval boundary in front of the existing MATE
control evaluator.

The boundary will show where each proposed MATE answer came from, record the
evidence review and require an auditor decision before the existing evaluator
is called.

Sprint 2 will not add a database, web screen, API endpoint, external AI
service, real audit evidence or retrieval system.

## Relationship To Sprint 1

Sprint 1 remains the verified deterministic decision core.

It assesses four Boolean dimensions:

1. Mandate - is the control explicitly codified in a binding framework or
   policy?
2. Accountability - is a single named job role accountable?
3. Trigger - is there an explicit activation event or gateway?
4. Escalation - is there a formal pathway to CRCC or executive oversight?

The existing rating precedence remains authoritative:

1. Zero failed dimensions is `ADEQUATE`.
2. A failed Mandate or Accountability dimension is `INADEQUATE`.
3. Two or more failed dimensions is `INADEQUATE`.
4. Exactly one failed Trigger or Escalation dimension is
   `PARTIALLY_ADEQUATE`.

Sprint 2 must not reproduce, reinterpret or modify these rules. It prepares
auditor-approved inputs and delegates the rating decision to the existing
`evaluate_control()` function.

The existing Sprint 1 application remains a fictional, private-by-default,
read-only demonstration. Its routes and five sample evaluations remain
functionally unchanged.

## Governing Principle

Technology must support the assurance methodology without becoming the
methodology.

The system may organise evidence and enforce review gates. It may not decide
whether evidence is professionally sufficient, silently convert an inference
into fact or approve a material assessment.

## Adopted Ideas

Sprint 2 combines a limited set of approved ideas from the three reviewed
chats.

### Chat 1

- Direct source references.
- Document version and precise source location.
- Separation of documented, reported, inferred and verified information.
- Visibility of supporting, contradictory and missing evidence.
- Auditor validation before a proposed answer becomes an approved input.

### Chat 2

- Separation of source wording, proposed extraction, approved fact, evidence,
  auditor judgement and deterministic result.
- Explicit proposed, reviewed, approved, rejected and changes-required states.
- Material assessments remain under auditor control.
- Previous decisions and results are not silently overwritten.

Chat 2's use of MATE for Map-Assess-Trace-Enhance is rejected. MATE means only
Mandate, Accountability, Trigger and Escalation. Any future use of the four
activities will be described as the Connected Assurance Cycle.

### Chat 3

- Identification of evidence that supports or weakens an answer.
- Explicit recording of assumptions and limitations.
- Separation of evidence not requested, not provided, unavailable, inadequate
  and contradictory.
- Evidence-sufficiency review before an answer can be approved.

Sprint 2 does not include the full CONTRA challenge engine, historical decision
replay or cross-audit comparison.

## Approaches Considered

### Approach 1 - Domain Records And Approval Gate

Add frozen fictional records and a focused approval service. Use no persistence
and leave the application routes unchanged.

This is the approved approach because it proves the professional control with
the smallest change.

### Approach 2 - New API Endpoints

Add routes for creating proposals and recording approvals.

This was rejected for Sprint 2 because it introduces input security, workflow
and interface concerns before the domain control is proven.

### Approach 3 - PostgreSQL Persistence

Store evidence, proposals, reviews and decisions in PostgreSQL.

This was rejected for Sprint 2 because it introduces schema, migration,
authentication and client-data controls before the approval method is proven.

## Scope

### Included

- Fictional source references.
- Proposed answers for each MATE dimension.
- A third `UNRESOLVED` proposal state so uncertainty is not forced into a
  Boolean value.
- Supporting, weakening and contradictory source references.
- Evidence availability, assumptions and limitations.
- A proposed evidence-sufficiency assessment.
- Auditor approval, rejection or request for changes.
- A final auditor decision on evidence sufficiency.
- Clear blocking of incomplete, unresolved or unapproved assessments.
- Construction of the existing `AssuranceDimensions` only after all four
  answers pass the approval gate.
- Delegation to the unchanged Sprint 1 evaluator.
- Frozen approved records.
- Strict canonical UTC review timestamps.
- Comprehensive domain, approval-gate, integration and regression tests.

### Excluded

- Real audit evidence or client-confidential information.
- Document upload, parsing, chunking or extraction.
- PostgreSQL, Supabase or other persistence.
- New FastAPI routes or changes to existing route responses.
- Web screens or other user interfaces.
- External APIs, AI services, telemetry or analytics.
- Full-text search, vector search or pgvector.
- Neo4j, GraphRAG or another graph platform.
- CONTRA independent challenge.
- Historical decision replay.
- Findings, reports, actions or effectiveness reviews.
- Authentication, authorisation or multi-user workflows.
- Automatic approval of any MATE answer.

## Methodology Boundary

Sprint 2 concerns control-design assessment.

A source stating that an inspection must occur before mobilisation may support
`Trigger = YES` for control design. It does not prove that the inspection
occurred.

The records and tests must preserve this distinction:

- a documented requirement describes intended design;
- implementation evidence shows whether the control was performed; and
- effectiveness evidence shows whether the performed control achieved its
  intended outcome.

Sprint 2 handles the first category only. Later sprints may connect design,
implementation and effectiveness without changing MATE's meaning.

## Domain Vocabulary

The new enums and records will be placed in
`src/ace/domain/assessment.py`. Their behaviour is fixed by this design.

### MATE Dimension

- `MANDATE`
- `ACCOUNTABILITY`
- `TRIGGER`
- `ESCALATION`

### Proposed Answer

- `YES`
- `NO`
- `UNRESOLVED`

`UNRESOLVED` is valid for a proposal but can never be converted into an
`AssuranceDimensions` Boolean.

### Source Status

- `CURRENT`
- `SUPERSEDED`
- `UNCERTAIN`

A superseded or uncertain source may remain visible but cannot, by itself,
support an approved answer.

### Evidence Availability

- `REVIEWED_SUPPORTIVE`
- `REVIEWED_INADEQUATE`
- `CONTRADICTORY`
- `NOT_REQUESTED`
- `REQUESTED_NOT_PROVIDED`
- `UNAVAILABLE`
- `NOT_APPLICABLE`

These states organise the record. They do not automatically determine a MATE
answer.

### Evidence Sufficiency

- `SUFFICIENT_FOR_DESIGN_ASSESSMENT`
- `INSUFFICIENT`
- `UNRESOLVED`

The evidence review contains a proposed value. The auditor records the final
value using the same controlled vocabulary. The proposed value does not bind
the auditor.

### Contradiction Status

- `NONE_IDENTIFIED`
- `EXPLAINED`
- `UNRESOLVED`

An unresolved contradiction blocks evaluation.

### Auditor Decision Status

- `APPROVED`
- `REJECTED`
- `CHANGES_REQUIRED`

Only `APPROVED` may pass the approval gate.

## Domain Records

All records described below are frozen after construction. A change creates a
new version or new decision rather than mutating the existing record.

### Source Reference

Purpose: identify exactly what material was reviewed.

Required fields:

- source identifier;
- fictional document title;
- version;
- page, section, paragraph or other precise location;
- relevant fictional source wording; and
- source status.

Blank identifiers, titles, versions, locations or wording are invalid.

### Proposed Dimension Assessment

Purpose: record what the preparer or assistant proposes for one MATE
dimension.

Required fields:

- proposal identifier;
- positive proposal version;
- MATE dimension;
- proposed answer;
- plain-English rationale;
- evidence-review-record identifier.

A proposal must link to an evidence review identifying what material was
reviewed. Lack of evidence alone must not automatically produce `NO`.

### Evidence Review Record

Purpose: organise the evidence considered for one proposal without making the
final professional decision.

Required fields:

- review-record identifier;
- one or more source references;
- supporting source identifiers;
- weakening source identifiers;
- contradictory source identifiers;
- evidence-availability classifications;
- contradiction status;
- explanation of any contradiction;
- assumptions checked;
- limitations; and
- proposed evidence-sufficiency status.

An `EXPLAINED` contradiction requires a non-empty explanation. An
`UNRESOLVED` contradiction remains visible and blocks evaluation.
Each source reference represents one precise passage. A source identifier must
not appear in more than one of the supporting, weakening or contradictory
classifications.

### Auditor Decision

Purpose: record the accountable human decision for one proposal version.

Required fields:

- decision identifier;
- proposal identifier and version;
- MATE dimension;
- decision status;
- approved Boolean answer when status is `APPROVED`;
- final evidence-sufficiency decision;
- fictional reviewer identifier;
- review notes; and
- strict canonical UTC review timestamp.

Rules:

- `APPROVED` requires a Boolean answer.
- `APPROVED` requires evidence to be sufficient for design assessment.
- The approved Boolean answer must match the proposal's `YES` or `NO` answer.
- `REJECTED` and `CHANGES_REQUIRED` must not contain an approved answer.
- The decision must refer to the exact proposal version reviewed.
- The decision and review timestamp are immutable.

If the auditor reaches a different answer from the proposal, the auditor
records `CHANGES_REQUIRED`. A new proposal version is then required before
approval.

### Approved MATE Assessment

Purpose: represent the complete, approved input to the existing evaluator.

Required information:

- control identity and fictional descriptive metadata needed to construct the
  existing `Control`;
- exactly four auditor decisions;
- one decision for each MATE dimension;
- the resulting frozen `AssuranceDimensions`; and
- references to the four decisions from which the dimensions were created.

The record may be created only by the approval gate. Callers must not supply
the resulting `AssuranceDimensions` directly to this workflow.

## Approval Gate

A new focused approval service will sit beside, not inside, the existing
evaluator.

Its approved public workflow will:

1. receive fictional control metadata, proposals, evidence reviews and auditor
   decisions;
2. validate that every proposal links to an evidence review and every source
   identifier in the review resolves to a supplied source reference;
3. validate that each decision matches the relevant proposal identifier,
   version and dimension;
4. confirm that Mandate, Accountability, Trigger and Escalation each appear
   exactly once;
5. confirm that each decision is approved;
6. confirm that each approved Boolean answer matches its proposal;
7. confirm that each dimension has at least one current source in the evidence
   reviewed;
8. confirm that evidence is sufficient for a control-design assessment;
9. confirm that no proposed answer remains unresolved;
10. confirm that no contradiction remains unresolved;
11. convert approved `YES` and `NO` answers to strict Boolean values;
12. construct the existing `AssuranceDimensions`;
13. construct the existing `Control`;
14. call the existing `evaluate_control()` function; and
15. return the unchanged immutable `EvaluationResult`.

The Sprint 1 evaluator remains directly callable for backward compatibility
and its fictional demonstration. The new gate is therefore a controlled
workflow boundary, not an authentication or security boundary.

## Domain-Only Limitations

Sprint 2 does not claim to provide a production approval system.

- Records exist only in memory and disappear when the process ends.
- Immutability prevents an object from being changed; it does not provide a
  durable audit log.
- The fictional reviewer identifier does not authenticate a real person.
- The new workflow cannot prevent other Python code from calling the existing
  evaluator directly.
- Proposals are supplied as fictional test data or by a local caller; no AI
  creates them.
- Client confidentiality, access control and durable version history remain
  future requirements.

These limitations are deliberate. Sprint 2 proves the shape and behaviour of
the professional approval boundary before persistent or multi-user technology
is considered.

## Failure Behaviour

Invalid individual records will use normal Pydantic validation errors.

The approval service will use a focused domain exception named
`ApprovalBlockedError` for a valid set of records that is not ready for
evaluation.

Evaluation is blocked when:

- a MATE dimension is missing;
- a MATE dimension appears more than once;
- a proposal remains `UNRESOLVED`;
- an auditor decision is missing;
- a decision is `REJECTED`;
- a decision is `CHANGES_REQUIRED`;
- the final evidence-sufficiency decision is not sufficient for design
  assessment;
- a contradiction remains unresolved;
- a source reference is missing;
- a dimension has no current source in the evidence reviewed;
- a decision does not match the proposal identifier, version or dimension;
- an approved answer does not match the proposal;
- an approved decision lacks a Boolean answer;
- a review timestamp is not strict canonical UTC; or
- a reviewer identifier is missing.

Failure messages must identify the affected dimension and reason in plain
English, for example:

> Evaluation blocked: Trigger remains unresolved.

or:

> Evaluation blocked: Escalation has not been approved by the auditor.

The gate must never substitute a default answer, ignore an invalid decision or
produce a partial rating.

## Data Flow

```text
Fictional Source Reference
          |
          v
Proposed Dimension Assessment
          |
          v
Evidence Review Record
          |
          v
Auditor Decision
          |
          v
Approval Gate
          |
          v
Approved MATE Assessment
          |
          v
Existing Control And AssuranceDimensions
          |
          v
Existing evaluate_control()
          |
          v
Existing Immutable EvaluationResult
```

Each proposal and decision remains available as a separate object. The
evaluation result does not replace its supporting records.

## Proposed File Boundaries

The implementation plan will use these focused files.

### `src/ace/domain/assessment.py`

Owns the new enums and frozen domain records:

- source references;
- proposed dimension assessments;
- evidence review records;
- auditor decisions; and
- approved MATE assessments.

It must not import FastAPI, access files, create network clients or calculate a
control rating.

### `src/ace/engine/approval.py`

Owns the approval-gate checks, conversion of approved answers into
`AssuranceDimensions`, construction of the existing `Control` and delegation
to `evaluate_control()`.

It must not duplicate the rating decision table.

Its public interface will provide:

- `build_approved_assessment(...) -> ApprovedMATEAssessment`; and
- `evaluate_approved_assessment(...) -> EvaluationResult`.

The implementation plan will define the typed arguments from the approved
domain records without widening the design scope.

### `tests/test_approval_gate.py`

Owns the new record-validation, approval-gate and integration tests.

### Existing Files

The implementation will add only the exports required for the approved domain
records and approval-service functions to the domain and engine `__init__.py`
files.
It must not change the behaviour of:

- `src/ace/engine/evaluator.py`;
- `src/ace/app.py`;
- `tests/test_rating_engine.py`; or
- `tests/test_app.py`.

The existing application continues to expose exactly `/` and `/evaluations`.

## Testing Strategy

### Record Validation

Tests will confirm:

- source identifiers, titles, versions, locations and wording cannot be blank;
- proposal identifiers and rationale cannot be blank;
- proposal versions are positive;
- only the four authorised MATE dimensions are accepted;
- proposed answers and review states use controlled values;
- an explained contradiction includes an explanation;
- source identifiers do not overlap between supporting, weakening and
  contradictory classifications;
- approved decisions contain a Boolean answer;
- approved answers match their proposals;
- rejected or changes-required decisions do not contain an approved answer;
- approved decisions require sufficient evidence for design assessment;
- approved records are immutable;
- decision timestamps use strict canonical UTC; and
- surrounding timestamp whitespace and non-zero UTC offsets are rejected.

### Approval Gate

Tests will confirm:

- all four dimensions are required;
- each dimension appears once;
- each proposal resolves to its named evidence review;
- each decision matches its proposal identifier and version;
- unresolved proposals are blocked;
- rejected decisions are blocked;
- changes-required decisions are blocked;
- inadequate evidence is blocked;
- unresolved contradictions are blocked;
- missing source references are blocked;
- a dimension without a current reviewed source is blocked;
- approved `YES` becomes `True`;
- approved `NO` becomes `False`; and
- the approved values appear in stable MATE order.

### Evaluator Integration

Tests will confirm:

- the gate constructs the existing `AssuranceDimensions`;
- the gate constructs a valid existing `Control`;
- the gate calls the existing evaluator;
- returned results use the existing `EvaluationResult`;
- the existing rating precedence remains unchanged; and
- the gate contains no second rating implementation.

### Regression And Privacy

Verification will confirm:

- the complete existing Sprint 1 suite still passes;
- all 16 dimension combinations retain their existing ratings;
- the application still exposes only the two approved routes;
- existing response bodies remain unchanged;
- all new fixtures are clearly fictional;
- no real audit evidence appears in source or tests;
- no external API, telemetry or analytics integration is added; and
- no database, file persistence or network access is introduced.

## Acceptance Criteria

Sprint 2 implementation will be acceptable only when:

1. the four MATE answers can be traced to separate fictional proposals,
   evidence reviews and auditor decisions;
2. uncertain, incomplete or unapproved answers cannot reach the evaluator;
3. missing evidence is not automatically converted into a failed dimension;
4. documented design is not represented as proof of implementation;
5. all approved records and results are immutable;
6. the existing evaluator remains the only rating authority;
7. the existing FastAPI behaviour remains unchanged;
8. the complete test suite passes;
9. the source compiles;
10. both localhost endpoints are verified;
11. the server is stopped and port 8000 is confirmed closed; and
12. verification shows no external calls, real evidence or unrelated changes.

## Implementation Verification Boundary

Before any future claim that Sprint 2 implementation is complete, the
implementing agent must:

1. run the complete tests using the retained local verification environment;
2. compile the source;
3. start the application on `127.0.0.1:8000`;
4. verify `/`;
5. verify `/evaluations`;
6. stop the server;
7. confirm port 8000 is closed;
8. inspect the exact diff; and
9. confirm that only approved Sprint 2 files changed.

The known non-blocking FastAPI/Starlette TestClient deprecation warning must
remain visible. Dependency replacement requires separate approval if a
download is needed.

## Deferred Roadmap

This design deliberately leaves room for later, separately approved work:

- Connected Assurance tracing across obligations, risks, controls, owners,
  evidence, verification, escalation, decisions, findings and actions.
- PostgreSQL as the authoritative record for accepted facts and relationships.
- Full-text and pgvector retrieval.
- CONTRA independent challenge.
- Corrective-action and effectiveness tracing.
- Findings and controlled report generation.
- Historical decision replay.
- Optional rebuildable graph projections or GraphRAG.

None of these items is part of Sprint 2.

## Approved Design Summary

Sprint 2 is a fictional, domain-only approval boundary that proves where MATE
answers come from, records the evidence review and auditor decision, and
prevents unapproved or uncertain answers from reaching the existing
deterministic evaluator.

It strengthens professional control without turning technology into the
methodology.
