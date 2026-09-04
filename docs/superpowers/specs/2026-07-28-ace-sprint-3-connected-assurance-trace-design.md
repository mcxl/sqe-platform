# ACE Sprint 3 Connected Assurance Trace Design

## Decision

Sprint 3 will design and, only after separate approval of an implementation
plan, build one fictional, domain-only Connected Assurance planning trace.

The trace will connect:

```text
Binding Obligation
        |
        v
       Risk
        |
        v
Planning Control
        |
        v
Accountable Job Role
        |
        v
Approved MATE Assessment And Existing Rating
```

This is a conceptual audit trail rather than a generic graph. The individual
relationships retain their precise professional meaning and require explicit
auditor approval.

Sprint 3 will not add a database, API route, webpage, retrieval system, graph
platform, external service or real audit evidence.

## Governing Principle

Technology must support the methodology without becoming the methodology.

The system may organise facts, source references, proposed relationships,
auditor decisions and an accepted trace. It may not decide that two matters
are related, infer that a control is effective or approve an audit conclusion.

## Relationship To Sprint 1

Sprint 1 remains the deterministic rating authority.

MATE means only:

1. Mandate - is the control explicitly codified in a binding framework or
   policy?
2. Accountability - is a single named job role accountable?
3. Trigger - is there an explicit activation event or gateway?
4. Escalation - is there a formal pathway to CRCC or executive oversight?

The existing rating precedence remains unchanged:

1. Zero failed dimensions is `ADEQUATE`.
2. A failed Mandate or Accountability dimension is `INADEQUATE`.
3. Two or more failed dimensions is `INADEQUATE`.
4. Exactly one failed Trigger or Escalation dimension is
   `PARTIALLY_ADEQUATE`.

Sprint 3 must not reproduce or reinterpret these rules.

## Relationship To Sprint 2

Sprint 2 remains the controlled evidence and auditor approval boundary for
MATE answers.

Sprint 3 will reuse:

- `SourceReference`;
- `ApprovedMATEAssessment`;
- the approved MATE relationship and decision references;
- `evaluate_approved_assessment()`; and
- the unchanged immutable `EvaluationResult`.

Sprint 3 will not weaken or bypass the Sprint 2 approval gate. It will accept
an already-approved MATE assessment and confirm that it concerns the same
planning control represented in the Connected Assurance trace.

## When MATE Is Used

MATE is applied after the binding obligation, risk, planning control and
accountable job role have been identified and their planning relationships
have been approved.

The sequence is:

1. identify the binding obligation;
2. identify the relevant risk;
3. identify the planning control intended to treat the risk;
4. identify the accountable job role;
5. approve those planning relationships;
6. use Sprint 2 to review evidence and approve the four MATE answers for that
   control;
7. use the existing evaluator to produce the deterministic rating; and
8. connect the approved assessment and rating to the accepted planning trace.

MATE assesses the structural adequacy of the identified control's design. It
does not map the Connected Assurance chain and does not approve relationships.

MATE also does not determine whether the control was implemented, operated or
effective, whether the risk was reduced, whether a finding exists or whether
an action was completed.

## Purpose

The Sprint 3 pilot will answer one plain-English planning question:

> Can an auditor start with one binding obligation, follow the approved logic
> through one risk, one control and one accountable job role, and arrive at
> the existing approved MATE assessment and rating?

The same trace must also be understandable in reverse:

> Can an auditor start with the assessed control and explain which risk and
> binding obligation justify its place in the audit plan?

## Success Criterion

Sprint 3 is successful when one complete fictional chain can be accepted only
after:

- every planning fact has precise, current provenance;
- every relationship has been separately proposed;
- every proposed relationship has been explicitly approved by an auditor;
- every relationship connects the correct records;
- the planning control identity matches the approved MATE assessment;
- the existing evaluator returns the unchanged immutable result; and
- the complete accepted trace remains frozen.

## Adopted Ideas From The Reviewed Chats

### Chat 1

- Direct source provenance.
- Audit-question and control-lineage tracing.
- Explicit auditor validation of proposed relationships.
- Visibility of broken or unsupported links.

Sprint 3 adopts the assurance method, not a standalone Neo4j or GraphRAG
architecture.

### Chat 2

- Formal separation of facts, proposed relationships, auditor decisions and
  accepted records.
- Human review states.
- Connected Assurance across obligations, risks, controls and accountable
  roles.

Sprint 3 does not adopt PostgreSQL, Supabase or pgvector yet.

Chat 2's use of MATE for Map-Assess-Trace-Enhance remains rejected. If those
activities are used later, they will be called the Connected Assurance Cycle.

### Chat 3

- Controlled traceability.
- Clear assumptions and limitations.
- Human approval before a relationship becomes accepted.

Sprint 3 does not add historical decision replay, cross-audit comparison or a
CONTRA challenge engine.

## Approaches Considered

### Approach 1 - Frozen Records And A Trace Approval Gate

Add focused domain records for the four planning facts, proposed
relationships, auditor relationship decisions and one accepted trace. Use a
small approval service and no persistence.

This is the approved approach because it extends the proven Sprint 2 pattern
without making graph technology the method.

### Approach 2 - Generic In-Memory Graph

Represent facts as generic nodes and relationships as generic edges.

This was rejected because generic graph vocabulary would hide the professional
meaning of each connection and introduce unnecessary flexibility.

### Approach 3 - PostgreSQL Relationship Model

Store facts and accepted relationships in formal tables.

This was rejected for Sprint 3 because it would introduce schema, migrations,
authentication and client-data segregation before the planning trace has been
proven.

## Scope

### Included

- One fictional binding obligation.
- One fictional risk.
- One fictional planning control.
- One fictional accountable job role.
- One precise current source reference for each planning fact.
- Four controlled relationship types.
- A separate versioned proposal for each relationship.
- Supporting source identifiers and a plain-English rationale for each
  relationship proposal.
- A separate auditor decision for each relationship proposal version.
- Approved, rejected and changes-required relationship states.
- Strict canonical UTC decision timestamps.
- A trace approval gate.
- Forward and reverse traceability.
- Control-identity matching to the approved MATE assessment.
- Delegation to the existing MATE evaluator.
- One frozen accepted planning trace.
- Comprehensive record, gate, integration, regression and privacy tests.

### Excluded

- More than one obligation, risk, control or accountable role in a trace.
- Real audit evidence or client-confidential information.
- Control implementation evidence.
- Control operating evidence.
- Control effectiveness evidence.
- Risk reduction claims.
- Findings, recommendations or report generation.
- Corrective actions or follow-up.
- CONTRA independent challenge.
- Historical decision replay or cross-audit comparison.
- Document upload, parsing, extraction or automated relationship proposal.
- PostgreSQL, Supabase or another persistent store.
- Full-text search, vector search or pgvector.
- Neo4j, GraphRAG or another graph platform.
- New FastAPI routes or changes to existing route responses.
- A webpage or other user interface.
- External APIs, AI services, telemetry or analytics.
- Authentication, authorisation or multi-user workflow.
- Automatic approval of any relationship.

## Methodology Boundary

Sprint 3 concerns audit planning and control-design lineage.

An accepted relationship stating that a control treats a risk means that an
auditor approved that planning connection. It does not prove that:

- the control was implemented;
- the control operated;
- the control achieved its intended outcome;
- the residual risk is acceptable; or
- management fulfilled the binding obligation.

Those matters require different evidence and later, separately approved
workflow stages.

## Domain Vocabulary

The new enums and records will be placed in `src/ace/domain/trace.py`.

### Accountability Subject Type

- `JOB_ROLE`
- `NAMED_PERSON`

The factual record may represent what was proposed, but the trace gate accepts
only `JOB_ROLE`. This avoids unreliable attempts to guess from text whether a
title is a role or a person's name.

### Trace Relationship Type

- `OBLIGATION_APPLIES_TO_RISK`
- `CONTROL_TREATS_RISK`
- `ROLE_ACCOUNTABLE_FOR_CONTROL`
- `CONTROL_HAS_APPROVED_MATE_ASSESSMENT`

These are the only relationship types in Sprint 3.

Generic node, edge, parent, child or related-to relationship types are not
permitted.

### Relationship Decision Status

The new auditor relationship decision will reuse the controlled states already
established in Sprint 2:

- `APPROVED`
- `REJECTED`
- `CHANGES_REQUIRED`

Only `APPROVED` may enter an accepted trace.

## Planning Fact Records

All records are frozen after construction. A correction creates a new record
or version rather than changing the accepted object.

### Binding Obligation

Purpose: represent the binding requirement that justifies the planning line.

Required information:

- obligation identifier;
- title;
- binding instrument or policy;
- clause, section or other precise location;
- exact fictional obligation wording; and
- one `SourceReference`.

The gate requires the source to be `CURRENT`.

The record does not decide whether the control meets the obligation.

### Risk

Purpose: represent the risk to which the binding obligation and control are
connected.

Required information:

- risk identifier;
- title;
- plain-English risk statement; and
- one `SourceReference`.

The gate requires the source to be `CURRENT`.

The record does not contain an inherent or residual risk rating in Sprint 3.

### Planning Control

Purpose: identify the control whose place in the audit plan is being traced.

Required information:

- control identifier;
- title;
- control-design statement; and
- one `SourceReference`.

The control identifier must exactly match
`ApprovedMATEAssessment.control_id`.

The record describes intended control design. It is not implementation or
effectiveness evidence.

### Accountable Role

Purpose: identify the job role accountable for the planning control.

Required information:

- accountability identifier;
- subject type;
- job-role title or proposed named-person description;
- accountability statement; and
- one `SourceReference`.

The record may capture a `NAMED_PERSON` proposal so that the gate can reject it
in plain English. An accepted trace requires `JOB_ROLE`.

Sprint 3 will not store a real person's name. Fictional named-person examples
may be used only in negative tests.

## Proposed Trace Relationship

Purpose: keep a proposed connection separate from the auditor's decision.

Required information:

- relationship identifier;
- positive relationship version;
- one authorised relationship type;
- source record identifier;
- target record identifier;
- one or more supporting source identifiers; and
- plain-English rationale.

The proposal is frozen.

### Required Endpoints

The gate will enforce these exact meanings:

| Relationship Type | Source Endpoint | Target Endpoint |
|---|---|---|
| `OBLIGATION_APPLIES_TO_RISK` | Binding obligation | Risk |
| `CONTROL_TREATS_RISK` | Planning control | Risk |
| `ROLE_ACCOUNTABLE_FOR_CONTROL` | Accountable role | Planning control |
| `CONTROL_HAS_APPROVED_MATE_ASSESSMENT` | Planning control | Approved MATE assessment |

For the final relationship, the approved MATE endpoint will use a stable,
locally derived reference in the form:

```text
MATE:<control_id>
```

The gate derives this reference from the supplied
`ApprovedMATEAssessment.control_id`. A caller cannot use it to connect a
different control.

### Supporting Sources

Every supporting source identifier must resolve to a source reference
belonging to one of the connected planning facts.

For the MATE relationship:

- the planning-control source supports the identity of the control; and
- the supplied frozen `ApprovedMATEAssessment` and its four decision
  references support the assessment endpoint.

Source resolution organises the record. It does not automatically approve the
relationship.

## Auditor Relationship Decision

Purpose: record the human auditor's decision on one exact relationship
proposal version.

Required information:

- decision identifier;
- relationship identifier and version;
- relationship type;
- decision status;
- fictional reviewer identifier;
- non-empty review notes; and
- strict canonical UTC review timestamp.

Rules:

- the decision must match the exact relationship identifier, version and
  type;
- `APPROVED` may pass the trace gate;
- `REJECTED` blocks the trace;
- `CHANGES_REQUIRED` blocks the trace;
- decision identifiers must be unique; and
- the record is immutable.

If the auditor changes an endpoint, relationship type, supporting source or
rationale, the decision is `CHANGES_REQUIRED`. A new relationship proposal
version is then required.

## Accepted Planning Trace

Purpose: represent one complete, approved planning chain.

Required information:

- one binding obligation;
- one risk;
- one planning control;
- one accountable job role;
- exactly four approved relationship proposals;
- exactly four matching auditor relationship decisions;
- one existing `ApprovedMATEAssessment`;
- one existing immutable `EvaluationResult`; and
- references to every relationship decision used to construct the trace.

The trace is frozen.

The trace may be created only through the trace approval workflow. This is a
controlled application boundary, not an authentication or security boundary.

## Trace Approval Gate

A focused service will be placed in `src/ace/engine/tracing.py`.

Its public workflow will:

1. receive the four fictional planning facts;
2. receive exactly four relationship proposals;
3. receive exactly four auditor relationship decisions;
4. receive one existing `ApprovedMATEAssessment`;
5. confirm each planning fact has one precise current source;
6. confirm planning identifiers and source identifiers are unique;
7. reject an accountability subject that is not `JOB_ROLE`;
8. confirm every authorised relationship type appears exactly once;
9. confirm every relationship uses the required source and target endpoint;
10. confirm supporting source identifiers resolve to the connected facts;
11. confirm every decision matches the exact relationship identifier, version
    and type;
12. require every relationship decision to be `APPROVED`;
13. confirm the planning control identifier matches the MATE-assessed control;
14. derive and verify the `MATE:<control_id>` endpoint;
15. call the existing `evaluate_approved_assessment()` function;
16. receive the unchanged immutable `EvaluationResult`;
17. confirm the result control identifier matches the trace control; and
18. return one frozen accepted planning trace.

The gate will not infer a missing relationship, select a likely endpoint or
substitute a default approval.

## Forward And Reverse Traceability

The accepted record will support two deterministic traversals without a graph
database.

### Forward

```text
Binding obligation
-> approved obligation-to-risk relationship
-> risk
-> approved control-to-risk relationship
-> planning control
-> approved role-to-control relationship
-> accountable job role
-> approved control-to-MATE relationship
-> approved MATE assessment
-> immutable rating
```

### Reverse

```text
Immutable rating
-> approved MATE assessment
-> accountable job role
-> planning control
-> risk
-> binding obligation
```

Sprint 3 may expose these as domain methods or service functions. It will not
add a generic query language, graph traversal library or search engine.

## Failure Behaviour

Invalid individual records will use normal Pydantic validation errors.

The trace service will use a focused domain exception named
`TraceApprovalBlockedError` when valid records do not form an acceptable
trace.

Evaluation is blocked when:

- a planning fact is missing;
- a required source is not current;
- a planning identifier is duplicated;
- a source identifier is duplicated;
- the accountability subject is a named person;
- a relationship type is missing;
- a relationship type appears more than once;
- a relationship identifier and version are duplicated;
- an endpoint does not match the required records;
- a supporting source does not resolve;
- a supporting source belongs to an unrelated endpoint;
- an auditor relationship decision is missing;
- an auditor relationship decision is rejected;
- an auditor relationship decision requires changes;
- a decision does not match the proposal identifier, version or type;
- a decision identifier is duplicated;
- the planning control differs from the MATE-assessed control;
- the MATE endpoint reference is incorrect; or
- the evaluation result refers to a different control.

Messages must identify the affected relationship or record in plain English,
for example:

> Trace blocked: the Control Treats Risk relationship has not been approved.

or:

> Trace blocked: planning control ACE-FICTIONAL-001 does not match the
> approved MATE assessment.

The gate must never return a partial trace.

## Domain-Only Limitations

Sprint 3 does not claim to provide a production Connected Assurance platform.

- Records exist only in memory.
- Frozen objects do not create a durable audit log.
- Fictional reviewer identifiers do not authenticate real users.
- Existing Python callers can still call earlier services directly.
- The system cannot determine from wording alone whether a role title hides a
  person's name; the explicit subject type and auditor approval provide the
  pilot control.
- The Sprint 2 approved assessment retains Boolean MATE decisions and decision
  references, not a machine-readable accountable role title. Sprint 3
  therefore relies on the separately approved Role Accountable For Control
  relationship rather than claiming an automated semantic match.
- The single-chain design does not support portfolio, cross-control or
  cross-audit analysis.
- No AI proposes facts or relationships.

These limitations are deliberate.

## Proposed File Boundaries

### `src/ace/domain/trace.py`

Owns:

- Connected Assurance trace enums;
- binding obligation record;
- risk record;
- planning control record;
- accountable role record;
- proposed relationship record;
- auditor relationship decision record; and
- accepted planning trace record.

It must not import FastAPI, access files, use a database, create network
clients, approve relationships or calculate a rating.

### `src/ace/engine/tracing.py`

Owns:

- trace completeness checks;
- endpoint validation;
- source resolution;
- relationship decision matching;
- control-identity matching;
- construction of the accepted trace;
- forward and reverse deterministic trace views; and
- delegation to `evaluate_approved_assessment()`.

It must not duplicate the MATE rating rules.

### `tests/test_planning_trace.py`

Owns:

- record validation tests;
- relationship proposal tests;
- auditor relationship decision tests;
- approval-gate tests;
- forward and reverse trace tests;
- evaluator-integration tests; and
- privacy and regression checks specific to Sprint 3.

### Existing Files

Only required exports may be added to:

- `src/ace/domain/__init__.py`; and
- `src/ace/engine/__init__.py`.

Sprint 3 must not change the behaviour of:

- `src/ace/domain/assessment.py`;
- `src/ace/engine/approval.py`;
- `src/ace/engine/evaluator.py`;
- `src/ace/app.py`;
- `tests/test_approval_gate.py`;
- `tests/test_rating_engine.py`; or
- `tests/test_app.py`.

The application continues to expose exactly `/` and `/evaluations`.

## Testing Strategy

### Planning Fact Validation

Tests will confirm:

- required identifiers and descriptions cannot be blank;
- each fact contains one source reference;
- fact records are frozen;
- source identifiers are unique within the trace;
- a job role is accepted; and
- a named-person accountability subject is blocked by the trace gate.

### Relationship Validation

Tests will confirm:

- relationship identifiers and rationale cannot be blank;
- relationship versions are positive strict integers;
- only the four controlled types are accepted;
- source and target identifiers cannot be blank;
- at least one supporting source identifier is required;
- proposal identity pairs are unique;
- decision identifiers are unique;
- decisions match the exact proposal version and type;
- timestamps are strict canonical UTC; and
- proposals and decisions are frozen.

### Trace Approval Gate

Tests will confirm:

- all four facts are required;
- all four relationships are required exactly once;
- every endpoint is correct;
- supporting sources resolve to connected records;
- unrelated supporting sources are rejected;
- stale and uncertain sources are rejected;
- named-person accountability is rejected;
- rejected relationships are blocked;
- changes-required relationships are blocked;
- mismatched decision versions are blocked;
- control identifiers match;
- the MATE endpoint reference is derived and verified;
- no relationship is automatically inferred;
- partial traces are never returned; and
- failure messages identify the affected record or relationship.

### Connected Trace

Tests will confirm:

- the accepted record contains one complete chain;
- the accepted record is frozen;
- forward trace order is deterministic;
- reverse trace order is deterministic;
- every accepted relationship retains its decision reference; and
- the trace retains the existing approved MATE assessment and immutable
  result.

### Evaluator Integration

Tests will confirm:

- the trace gate calls `evaluate_approved_assessment()`;
- the existing `EvaluationResult` is returned;
- all 16 MATE combinations retain their Sprint 1 ratings;
- two or more failed dimensions remain `INADEQUATE`; and
- `src/ace/engine/tracing.py` contains no second rating implementation.

### Regression And Privacy

Verification will confirm:

- the complete existing suite still passes;
- the application still exposes only the two approved GET routes;
- existing response bodies remain unchanged;
- all new fixtures are clearly fictional;
- no real audit evidence appears;
- no external API, telemetry or analytics integration is added;
- no database, persistence or network access is introduced; and
- no graph or vector platform is introduced.

## Acceptance Criteria

Sprint 3 implementation will be acceptable only when:

1. one complete fictional planning chain is represented;
2. every planning fact has precise current provenance;
3. every material relationship has a separate proposal and auditor decision;
4. no unapproved, rejected or changes-required relationship enters the trace;
5. the accountable subject is one job role rather than a person;
6. the planning control matches the approved MATE assessment;
7. the existing evaluator remains the only rating authority;
8. forward and reverse traceability are deterministic;
9. planning lineage is not represented as implementation or effectiveness
   evidence;
10. all accepted records and results are immutable;
11. existing FastAPI behaviour remains unchanged;
12. the complete test suite passes;
13. the source compiles;
14. both localhost endpoints are verified;
15. the server is stopped and port 8000 is confirmed closed; and
16. verification shows no external calls, real evidence or unrelated changes.

## Implementation Verification Boundary

Before any future claim that Sprint 3 implementation is complete, the
implementing agent must:

1. run the complete tests using the retained local environment;
2. compile the source;
3. start the application on `127.0.0.1:8000`;
4. verify `/`;
5. verify `/evaluations`;
6. stop the server;
7. confirm port 8000 is closed;
8. inspect the exact diff;
9. confirm the protected Sprint 1 and Sprint 2 files remain behaviourally
   unchanged; and
10. confirm only approved Sprint 3 files changed.

The known non-blocking FastAPI/Starlette TestClient deprecation warning must
remain visible. Dependency replacement requires separate approval if a
download is needed.

## Deferred Roadmap

After the single-chain method has been proven, later separately approved work
may consider:

- multiple obligations, risks, controls and accountable roles;
- implementation and effectiveness verification;
- evidence-gap and contradiction challenge through CONTRA;
- findings and controlled report generation;
- corrective-action and effectiveness tracing;
- historical decision replay;
- PostgreSQL as the authoritative formal record;
- full-text and pgvector retrieval; and
- an optional rebuildable graph projection or GraphRAG layer.

None of these items is part of Sprint 3.

## Approved Design Summary

Sprint 3 is one fictional, domain-only Connected Assurance planning trace.

It connects a binding obligation, risk, planning control, accountable job
role and approved MATE assessment through four separately proposed and
auditor-approved relationships. It ends with the existing immutable rating.

It proves the assurance method before adding platform technology.
