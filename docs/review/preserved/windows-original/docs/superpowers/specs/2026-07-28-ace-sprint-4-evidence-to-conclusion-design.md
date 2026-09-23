# ACE Sprint 4 Evidence-To-Conclusion Design

## Decision

Sprint 4 will design and, only after separate approval of an implementation
plan, build one fictional, domain-only Evidence-to-Conclusion pilot.

The pilot will connect:

```text
Accepted Sprint 3 Planning Trace
        |
        v
Approved MATE Design Assessment And Rating
        |
        v
One Approved Main Audit Question
        |
        v
Implementation And Effectiveness Sub-Questions
        |
        v
Separate Evidence Matrices
        |
        v
Visible Gaps And Contradictions
        |
        v
Proposed Implementation And Effectiveness Conclusions
        |
        v
Separate Auditor Decisions
        |
        v
Frozen Accepted Evidence-To-Conclusion Record
```

Sprint 4 will not add findings, reports, corrective actions, CONTRA,
persistence, retrieval, graph technology, artificial intelligence, external
services or real audit evidence.

## Governing Principle

Technology must support the methodology without becoming the methodology.

The system may organise approved questions, fictional evidence, provenance,
evidence classifications, gaps, contradictions, proposed conclusions and
auditor decisions. It may not invent an audit question, decide professional
evidence sufficiency, resolve a contradiction, approve a material conclusion
or reinterpret the MATE rating rules.

## Relationship To Earlier Sprints

### Sprint 1

Sprint 1 remains the deterministic MATE rating authority.

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

Sprint 4 will not reproduce, modify or extend these rules.

### Sprint 2

Sprint 2 remains the controlled evidence and auditor approval boundary for
MATE control-design answers.

Sprint 4 will preserve Sprint 2's useful principles:

- precise source provenance;
- proposed records kept separate from auditor decisions;
- exact proposal-version matching;
- visible gaps, contradictions, assumptions and limitations;
- strict canonical UTC decision timestamps; and
- immutable accepted records.

Sprint 4 will not reuse the MATE-specific evidence records to assess
implementation or effectiveness. Those are different professional questions
and require separate records and conclusions.

### Sprint 3

Sprint 3 remains the accepted planning lineage:

```text
Binding Obligation
-> Risk
-> Planning Control
-> Accountable Job Role
-> Approved MATE Assessment
-> Immutable MATE Rating
```

Sprint 4 starts from one complete `AcceptedPlanningTrace`. The control
identifier used by every Sprint 4 question and conclusion must match that
trace.

Sprint 4 does not change, recreate or reapprove the planning relationships.

### Sprint 3.5

Sprint 4 adopts the approved reference-learning principles:

- OSCAL-informed separation of control design, implementation and assessment
  records;
- Auditree-informed separation of raw and derived evidence, with explicit
  provenance and freshness; and
- CISO-Assistant-informed awareness that security and client segregation must
  precede real data and persistence.

These patterns support SQE. They do not replace the SQE methodology.

## Purpose

The pilot will answer one main question:

> Has one fictional control, whose design and planning lineage have already
> been approved, been implemented and operated effectively?

That question will be decomposed into:

1. **Implementation:** What evidence shows that the approved control design
   was put into practice?
2. **Effectiveness:** What evidence shows that the implemented control
   achieved its intended result?

MATE answers whether the control is adequately designed. Sprint 4 does not use
MATE to decide implementation or effectiveness.

## Success Criterion

Sprint 4 is successful when one fictional control can be followed from its
accepted planning trace and MATE result through:

- one approved main audit question;
- one approved implementation sub-question;
- one approved effectiveness sub-question;
- a separate evidence matrix for each sub-question;
- explicit evidence provenance, origin and freshness;
- visible gaps, contradictions, assumptions and limitations;
- separate proposed implementation and effectiveness conclusions;
- separate matching auditor decisions; and
- one frozen accepted Evidence-to-Conclusion record.

No partially accepted record may be returned.

## Approaches Considered

### Approach 1 - Focused Evidence-To-Conclusion Records And Approval Gate

Add a small set of frozen domain records and a focused approval service. Link
them to one existing accepted planning trace and keep all information
fictional and in memory.

This is the approved approach because it proves the professional method before
adding platform technology.

### Approach 2 - Reuse The MATE Evidence Records

Adapt the Sprint 2 evidence records for implementation and effectiveness.

This was rejected because those records deliberately concern MATE
control-design assessment. Reuse would blur design, implementation and
effectiveness.

### Approach 3 - Add Formal Persistence

Create PostgreSQL records for questions, evidence and conclusions.

This was rejected for Sprint 4 because the evidence-to-conclusion method
should be proven before it is fixed into a persistent schema. Persistence also
requires a separately approved security and client-segregation design.

## Scope

### Included

- One existing fictional `AcceptedPlanningTrace`.
- One proposed main audit question.
- One proposed implementation sub-question.
- One proposed effectiveness sub-question.
- A separate auditor decision on each exact question version.
- Separate implementation and effectiveness evidence matrices.
- Raw, derived and auditor-authored evidence classifications.
- Direct provenance for every evidence item.
- Explicit collection time, validity period and freshness status.
- Supporting, weakening and contradictory evidence classifications.
- Explicit evidence-gap states.
- Explicit contradiction review.
- Proposed evidence-sufficiency status for each matrix.
- Separate proposed implementation and effectiveness conclusions.
- Separate auditor decisions on each exact conclusion proposal version.
- Explicit `NOT_DETERMINED` outcomes.
- A focused approval gate.
- One frozen accepted Evidence-to-Conclusion record.
- Comprehensive domain, gate, integration, regression and privacy tests.

### Excluded

- More than one planning trace or control.
- Real audit evidence or client-confidential information.
- Findings, recommendations or report generation.
- Corrective actions, follow-up or action-effectiveness review.
- Risk-reduction or residual-risk claims.
- CONTRA independent challenge.
- Historical decision replay or cross-audit comparison.
- Document upload, parsing, extraction or automated evidence collection.
- Automated audit-question generation.
- Automated evidence classification or conclusion generation.
- PostgreSQL, Supabase or another persistent store.
- Filesystem evidence storage.
- Full-text search, vector search or pgvector.
- Neo4j, GraphRAG or another graph platform.
- New FastAPI routes or changes to existing route responses.
- A webpage or other user interface.
- External APIs, AI services, telemetry or analytics.
- Authentication, authorisation or multi-user workflow.
- Automatic approval of any question, evidence judgement or conclusion.

## Methodology Boundary

Sprint 4 preserves three separate assurance layers:

1. **Design:** the approved MATE assessment asks whether the control is
   structurally adequate.
2. **Implementation:** the implementation conclusion asks whether the approved
   design was put into practice.
3. **Effectiveness:** the effectiveness conclusion asks whether the
   implemented control achieved its intended result.

An adequate MATE rating does not prove implementation or effectiveness.
Implementation does not prove effectiveness. An effectiveness conclusion
cannot bypass the implementation question.

Sprint 4 does not determine whether a finding exists. Later finding
reconstruction may use accepted facts and conclusions, but it requires a
separately approved method and decision gate.

## Domain Vocabulary

The implementation plan will use focused records in
`src/ace/domain/conclusion.py`.

### Audit Question Type

- `MAIN`
- `IMPLEMENTATION`
- `EFFECTIVENESS`

Exactly one of each type is required. The implementation and effectiveness
questions must identify the main question as their parent.

### Evidence Origin

- `RAW`
- `DERIVED`
- `AUDITOR_AUTHORED`

Raw evidence is the original fictional record. Derived evidence is a summary,
calculation or transformation and must identify at least one raw evidence
source. Auditor-authored evidence is a fictional interview note, observation
or professional analysis recorded by the auditor.

Evidence origin does not determine evidential weight or sufficiency.

### Evidence Freshness

- `CURRENT`
- `STALE`
- `SUPERSEDED`
- `UNCERTAIN`

Freshness remains visible. A stale, superseded or uncertain item cannot be the
sole basis for a substantive conclusion.

### Evidence Relevance

- `SUPPORTS`
- `WEAKENS`
- `CONTRADICTS`

Relevance is recorded in the evidence matrix for one precise question. The
same evidence item may be considered for both sub-questions only through two
separate matrix entries with separate rationales.

### Evidence Gap Status

- `NOT_REQUESTED`
- `REQUESTED_NOT_PROVIDED`
- `UNAVAILABLE`
- `STALE`
- `INADEQUATE`
- `NOT_APPLICABLE`

Each gap includes a plain-English explanation and an explicit materiality
classification. A gap state does not automatically produce a positive or
negative conclusion.

### Evidence Gap Disposition

- `OPEN`
- `RESOLVED`
- `ACCEPTED_LIMITATION`

An open material gap blocks a substantive conclusion. `RESOLVED` identifies a
gap that has been closed by supplied evidence. `ACCEPTED_LIMITATION` records
the auditor's explicit view that the gap remains visible but the available
evidence is still sufficient for the specific conclusion.

Resolved and accepted-limitations dispositions require a plain-English
rationale. A disposition does not automatically make evidence sufficient; the
auditor must still approve the final sufficiency decision.

### Evidence Sufficiency

- `SUFFICIENT`
- `INSUFFICIENT`
- `UNRESOLVED`

The evidence matrix contains a proposed sufficiency status. The conclusion
decision contains the auditor's final sufficiency decision.

### Contradiction Status

- `NONE_IDENTIFIED`
- `EXPLAINED`
- `UNRESOLVED`

An explained contradiction requires an explanation. An unresolved
contradiction prevents approval of a substantive conclusion.

### Implementation Conclusion

- `IMPLEMENTED`
- `PARTIALLY_IMPLEMENTED`
- `NOT_IMPLEMENTED`
- `NOT_DETERMINED`

### Effectiveness Conclusion

- `EFFECTIVE`
- `PARTIALLY_EFFECTIVE`
- `INEFFECTIVE`
- `NOT_DETERMINED`

`NOT_DETERMINED` is a valid conclusion. It records that the auditor cannot
reach a substantive conclusion from the available evidence. It is not a pass,
failure or substitute for missing work.

### Decision Status

Question and conclusion decisions will use the established controlled states:

- `APPROVED`
- `REJECTED`
- `CHANGES_REQUIRED`

Only `APPROVED` may enter the accepted record.

## Domain Records

All Sprint 4 records are frozen after construction. A correction requires a
new proposal version or a new decision.

### Proposed Audit Question

Purpose: record one precise question before auditor approval.

Required information:

- question identifier;
- positive question version;
- question type;
- precise plain-English wording;
- purpose;
- control identifier;
- parent question identifier for each sub-question; and
- required conclusion type for each sub-question.

The main question has no parent. The two sub-questions must point to the main
question. All three questions must use the planning control identifier from
the accepted Sprint 3 trace.

### Auditor Question Decision

Purpose: record the auditor's decision on one exact question version.

Required information:

- decision identifier;
- question identifier and version;
- question type;
- decision status;
- fictional reviewer identifier;
- non-empty review notes; and
- strict canonical UTC review timestamp.

The decision must match the exact question identifier, version and type.

### Evidence Item

Purpose: identify one fictional item considered during fieldwork.

Required information:

- evidence identifier;
- title and plain-English description;
- evidence origin;
- fictional source title or originator;
- source version or date;
- precise source location;
- collected-at timestamp;
- validity start and end when applicable;
- evidence freshness; and
- source evidence identifiers when applicable.

Rules:

- raw evidence has no source evidence identifier;
- derived evidence identifies at least one supplied raw evidence item;
- every derived source identifier resolves to a raw evidence item in this
  pilot;
- an auditor-authored item may cite supplied evidence but must remain clearly
  identified as auditor-authored;
- evidence identifiers are unique; and
- timestamps use strict canonical UTC where a timestamp is required.

Sprint 4 stores only fictional metadata and wording needed by tests. It does
not store or ingest evidence files.

### Evidence Matrix Entry

Purpose: record how one evidence item relates to one sub-question.

Required information:

- matrix-entry identifier;
- sub-question identifier;
- evidence identifier;
- evidence relevance;
- plain-English rationale; and
- reviewer limitations when applicable.

An entry can refer only to the implementation or effectiveness sub-question.
The gate will not infer relevance from the evidence wording.

### Evidence Gap

Purpose: retain missing or inadequate evidence without turning absence into a
failed conclusion.

Required information:

- gap identifier;
- sub-question identifier;
- gap status;
- plain-English description;
- whether the gap is material; and
- materiality rationale;
- gap disposition; and
- disposition rationale when the gap is resolved or accepted as a limitation.

### Evidence Matrix Review

Purpose: record the complete evidence-sufficiency review for one
sub-question.

Required information:

- review identifier;
- sub-question identifier;
- zero or more evidence matrix entries;
- zero or more evidence gaps;
- contradiction status;
- evidence identifiers involved in a contradiction when applicable;
- contradiction explanation when applicable;
- assumptions;
- limitations; and
- proposed evidence sufficiency.

Every matrix entry and contradiction evidence identifier must resolve to a
supplied evidence item. A matrix review must contain at least one evidence
entry or one explicit evidence gap. This permits an honest `NOT_DETERMINED`
conclusion when requested evidence was not provided or is unavailable.

### Proposed Implementation Conclusion

Purpose: propose an answer to the implementation sub-question.

Required information:

- proposal identifier;
- positive proposal version;
- implementation question identifier;
- proposed implementation outcome;
- evidence-matrix review identifier;
- evidence identifiers relied upon;
- gap identifiers considered;
- plain-English reasoning;
- assumptions; and
- limitations.

### Proposed Effectiveness Conclusion

Purpose: propose an answer to the effectiveness sub-question.

It contains the same controlled information as the implementation proposal,
but uses an effectiveness outcome and must refer to the effectiveness
sub-question and evidence matrix.

### Auditor Conclusion Decision

Purpose: record the human auditor's decision on one exact conclusion proposal
version.

Required information:

- decision identifier;
- proposal identifier and version;
- conclusion type;
- decision status;
- approved outcome when the decision is approved;
- final evidence-sufficiency decision;
- fictional reviewer identifier;
- non-empty review notes; and
- strict canonical UTC review timestamp.

Rules:

- an approved outcome must match the proposed outcome;
- a differing auditor view requires `CHANGES_REQUIRED` and a new proposal
  version;
- a substantive approved outcome requires `SUFFICIENT` evidence;
- a substantive approved outcome relies on at least one `CURRENT` evidence
  item;
- a substantive approved outcome cannot contain an unresolved contradiction;
- a substantive approved outcome cannot contain an open material gap;
- an accepted material limitation remains visible and requires an explicit
  rationale;
- an approved `NOT_DETERMINED` outcome records the evidence limitation and
  must not claim that the control passed or failed;
- an approved `NOT_DETERMINED` outcome has a final evidence-sufficiency
  decision of `INSUFFICIENT` or `UNRESOLVED`;
- rejected and changes-required decisions contain no approved outcome; and
- decision identifiers are unique.

### Accepted Evidence-To-Conclusion Record

Purpose: represent one complete, approved evidence-to-conclusion chain.

Required information:

- one existing `AcceptedPlanningTrace`;
- exactly three approved audit questions;
- the matching question decisions;
- all fictional evidence items used by the two evidence matrices;
- one implementation evidence matrix review;
- one effectiveness evidence matrix review;
- one implementation conclusion proposal;
- one effectiveness conclusion proposal;
- one approved decision for each conclusion;
- references to every question and conclusion decision used; and
- the two approved outcomes.

The record may be created only through the Sprint 4 approval gate.

## Approval Gate

A focused service will be placed in `src/ace/engine/conclusion.py`.

Its public workflow will:

1. receive one existing accepted planning trace;
2. receive exactly three question proposals and matching decisions;
3. confirm the main, implementation and effectiveness question types each
   appear exactly once;
4. confirm the two sub-questions identify the main question as their parent;
5. confirm every question uses the planning control identifier;
6. confirm every question decision matches the exact identifier, version and
   type;
7. require all question decisions to be approved;
8. receive the fictional evidence items and two evidence matrix reviews;
9. confirm evidence, matrix-entry, gap and review identifiers are unique;
10. confirm derived evidence resolves directly to supplied raw evidence;
11. confirm every matrix entry refers to the correct sub-question and a
    supplied evidence item;
12. confirm every gap belongs to the correct sub-question;
13. confirm each matrix review contains at least one evidence entry or one
    explicit gap;
14. confirm every resolved or accepted-limitation gap has a disposition
    rationale;
15. confirm contradiction references resolve;
16. receive one implementation and one effectiveness proposal;
17. confirm each proposal refers to the correct question and evidence review;
18. confirm every relied-upon evidence and gap identifier resolves;
19. receive one decision for each exact conclusion proposal version;
20. require both conclusion decisions to be approved;
21. require sufficient evidence, at least one current relied-upon evidence
    item, no unresolved contradiction and no open material gap for a
    substantive outcome;
22. allow an approved `NOT_DETERMINED` outcome only when its evidence
    limitation remains explicit and its final sufficiency is `INSUFFICIENT` or
    `UNRESOLVED`;
23. confirm the effectiveness conclusion does not bypass the implementation
    conclusion or claim effectiveness when implementation is
    `NOT_IMPLEMENTED` or `NOT_DETERMINED`; and
24. return one frozen accepted Evidence-to-Conclusion record.

The gate will not infer a question, classify evidence from its wording,
resolve a contradiction, select a likely conclusion or substitute a default
approval.

## Implementation And Effectiveness Dependency

The effectiveness conclusion depends on the implementation conclusion.

- `IMPLEMENTED` or `PARTIALLY_IMPLEMENTED` may proceed to a substantive
  effectiveness conclusion when the effectiveness evidence is sufficient.
- `NOT_IMPLEMENTED` means there is no implemented control whose operating
  effectiveness can be assessed. The effectiveness outcome must be
  `NOT_DETERMINED`.
- `NOT_DETERMINED` implementation prevents a substantive effectiveness
  conclusion. The effectiveness outcome must also be `NOT_DETERMINED`.

This dependency does not automatically decide effectiveness. It prevents an
internally inconsistent accepted record.

## Data Flow

```text
Accepted Planning Trace And Approved MATE Result
                    |
                    v
          Proposed Audit Questions
                    |
                    v
          Auditor Question Decisions
                    |
                    v
       Fictional Evidence Items And Matrices
                    |
                    v
          Gaps And Contradiction Review
                    |
                    v
  Proposed Implementation And Effectiveness Conclusions
                    |
                    v
          Auditor Conclusion Decisions
                    |
                    v
             Approval Gate
                    |
                    v
 Frozen Accepted Evidence-To-Conclusion Record
```

The accepted record does not replace the planning trace, MATE assessment,
evidence, proposals or decisions. It retains their identities and connections.

## Failure Behaviour

Invalid individual records will use normal Pydantic validation errors.

The approval service will use a focused domain exception named
`ConclusionApprovalBlockedError` when valid records do not form an acceptable
chain.

Acceptance is blocked when:

- a required question is missing or duplicated;
- a sub-question has the wrong parent;
- a question concerns a different control;
- a question decision is missing, rejected, changes-required or mismatched;
- an evidence identifier is duplicated;
- derived evidence does not identify supplied raw evidence;
- an evidence matrix refers to the wrong question;
- a matrix entry, gap or contradiction reference does not resolve;
- an implementation or effectiveness proposal is missing or duplicated;
- a proposal refers to the wrong question or evidence matrix;
- relied-upon evidence or gap references do not resolve;
- a conclusion decision is missing, rejected, changes-required or mismatched;
- an approved outcome differs from its proposal;
- a substantive conclusion lacks sufficient evidence;
- a substantive conclusion has no current relied-upon evidence;
- a substantive conclusion contains an unresolved contradiction;
- a substantive conclusion contains an open material evidence gap;
- a `NOT_DETERMINED` conclusion hides its evidence limitation;
- the effectiveness outcome conflicts with the implementation outcome; or
- any Sprint 4 control identifier differs from the accepted planning trace.

Messages must identify the affected question, evidence record or conclusion in
plain English, for example:

> Conclusion blocked: the effectiveness evidence contains an unresolved
> contradiction.

or:

> Conclusion blocked: implementation question AQ-IMP-001 concerns a different
> control from the accepted planning trace.

The gate must never return a partially accepted record.

## Domain-Only Limitations

Sprint 4 does not claim to provide a production assurance platform.

- Records exist only in memory.
- Frozen objects do not provide a durable audit log.
- Fictional reviewer identifiers do not authenticate real users.
- No evidence files are collected, stored or displayed.
- Questions, classifications and conclusions are supplied as fictional test
  data; no AI proposes them.
- The pilot cannot enforce client segregation or role-based access.
- The single-chain design does not support portfolio analysis.
- Existing Python callers can still call earlier services directly.

These limitations are deliberate.

## Proposed File Boundaries

### `src/ace/domain/conclusion.py`

Owns:

- question, evidence, gap, sufficiency and conclusion enums;
- proposed audit-question records;
- auditor question decisions;
- evidence items and matrix records;
- proposed implementation and effectiveness conclusions;
- auditor conclusion decisions; and
- the accepted Evidence-to-Conclusion record.

It must not import FastAPI, access files, use a database, create network
clients, approve questions or conclusions, or calculate a MATE rating.

### `src/ace/engine/conclusion.py`

Owns:

- exact question and decision matching;
- control-identity matching;
- evidence and provenance resolution;
- evidence-matrix integrity checks;
- gap and contradiction gates;
- conclusion and decision matching;
- implementation-to-effectiveness consistency checks; and
- construction of the accepted record.

It must not duplicate the MATE evaluator or make professional judgements from
evidence wording.

### `tests/test_evidence_to_conclusion.py`

Owns:

- record validation tests;
- question-approval tests;
- evidence provenance and matrix tests;
- gap and contradiction tests;
- conclusion-approval tests;
- implementation-to-effectiveness consistency tests;
- accepted-record tests;
- integration tests; and
- Sprint 4 privacy and regression checks.

### Existing Files

Only required exports may be added to:

- `src/ace/domain/__init__.py`; and
- `src/ace/engine/__init__.py`.

Sprint 4 must not change the behaviour of:

- `src/ace/domain/assessment.py`;
- `src/ace/domain/trace.py`;
- `src/ace/engine/approval.py`;
- `src/ace/engine/tracing.py`;
- `src/ace/engine/evaluator.py`;
- `src/ace/app.py`;
- existing Sprint 1, Sprint 2 and Sprint 3 tests; or
- the two existing application routes.

## Testing Strategy

### Question Records And Decisions

Tests will confirm:

- exactly one main, implementation and effectiveness question is required;
- question identifiers and wording cannot be blank;
- question versions are positive strict integers;
- sub-questions identify the correct main question;
- every question uses the planning control identifier;
- decisions match the exact question identifier, version and type;
- rejected and changes-required questions are blocked;
- decision timestamps use strict canonical UTC; and
- records are frozen.

### Evidence Provenance

Tests will confirm:

- evidence identifiers are unique;
- required provenance fields cannot be blank;
- raw evidence has no source evidence identifier;
- derived evidence identifies at least one supplied raw evidence item;
- missing or non-raw derivation sources are blocked;
- auditor-authored evidence remains clearly classified;
- stale, superseded and uncertain states remain visible; and
- evidence records are frozen.

### Evidence Matrices

Tests will confirm:

- implementation and effectiveness use separate matrix reviews;
- every entry resolves to supplied evidence;
- entries refer only to the relevant sub-question;
- the same evidence used for both questions requires separate entries;
- a matrix without evidence entries contains at least one explicit evidence
  gap;
- support, weakening and contradiction classifications are retained;
- gaps use controlled states and retain materiality reasoning;
- contradiction references resolve;
- an explained contradiction includes an explanation; and
- assumptions and limitations remain visible.

### Conclusion Approval

Tests will confirm:

- one implementation and one effectiveness proposal are required;
- each proposal resolves to the correct question and evidence review;
- every relied-upon evidence and gap identifier resolves;
- decisions match the exact proposal identifier, version and conclusion type;
- rejected and changes-required conclusions are blocked;
- substantive outcomes require sufficient evidence;
- substantive outcomes require at least one current relied-upon evidence item;
- unresolved contradictions block substantive outcomes;
- open material gaps block substantive outcomes;
- accepted material limitations retain their rationale;
- missing evidence is not automatically converted into a negative outcome;
- `NOT_DETERMINED` preserves the evidence limitation;
- `NOT_DETERMINED` uses an insufficient or unresolved final sufficiency;
- approved outcomes match their proposals; and
- accepted conclusions and decisions are frozen.

### Cross-Layer Consistency

Tests will confirm:

- every Sprint 4 record concerns the accepted planning control;
- the accepted trace retains the existing MATE assessment and immutable
  rating;
- MATE is not called or reused to determine implementation or effectiveness;
- effectiveness cannot bypass implementation;
- an unimplemented or undetermined control cannot be accepted as effective;
  and
- the gate never returns a partial record.

### Regression And Privacy

Verification will confirm:

- the complete existing suite still passes;
- all 16 MATE combinations retain their existing ratings;
- the application still exposes only the two approved GET routes;
- existing response bodies remain unchanged;
- all new fixtures are clearly fictional;
- no real audit evidence appears;
- no external API, telemetry or analytics integration is added;
- no database, file persistence or network access is introduced; and
- no graph or vector platform is introduced.

## Acceptance Criteria

Sprint 4 implementation will be acceptable only when:

1. one accepted fictional Sprint 3 trace is used as the starting point;
2. three exact audit questions are separately approved;
3. implementation and effectiveness evidence remain separate;
4. every evidence item retains origin, provenance and freshness;
5. raw and derived evidence cannot be confused;
6. gaps and contradictions remain visible;
7. missing evidence is not treated as proof of failure;
8. substantive conclusions require sufficient evidence and at least one
   current relied-upon evidence item;
9. unresolved contradictions and open material gaps block substantive
   conclusions;
10. `NOT_DETERMINED` accurately preserves an evidence limitation;
11. the implementation and effectiveness outcomes are internally consistent;
12. every material decision matches an exact proposal version;
13. the accepted record is complete and immutable;
14. MATE remains unchanged and limited to control-design assessment;
15. existing FastAPI behaviour remains unchanged;
16. the complete test suite passes;
17. the source compiles;
18. both localhost endpoints are verified;
19. the server is stopped and port 8000 is confirmed closed; and
20. verification shows no external calls, real evidence or unrelated changes.

## Implementation Verification Boundary

Before any future claim that Sprint 4 implementation is complete, the
implementing agent must:

1. run the complete tests using the retained local environment;
2. compile the source;
3. start the application on `127.0.0.1:8000`;
4. verify `/`;
5. verify `/evaluations`;
6. stop the server;
7. confirm port 8000 is closed;
8. inspect the exact diff;
9. confirm protected Sprint 1, Sprint 2 and Sprint 3 behaviour is unchanged;
   and
10. confirm only approved Sprint 4 files changed.

The known non-blocking FastAPI/Starlette TestClient deprecation warning must
remain visible. Dependency replacement requires separate approval if a
download is needed.

## Deferred Roadmap

After the Evidence-to-Conclusion method is proven, later separately approved
work may consider:

- CONTRA independent challenge;
- finding reconstruction and controlled report generation;
- corrective-action and effectiveness tracing;
- historical decision replay and cross-audit consistency;
- PostgreSQL as the authoritative formal record;
- security, role-based access and client-data segregation;
- full-text and pgvector retrieval; and
- an optional rebuildable graph projection or GraphRAG layer.

None of these items is part of Sprint 4.

## Approved Design Summary

Sprint 4 is one fictional, domain-only Evidence-to-Conclusion pilot.

It starts with an existing accepted planning trace and MATE design assessment.
It then uses separately approved questions, separate implementation and
effectiveness evidence matrices, explicit gaps and contradictions, controlled
conclusion proposals and separate auditor decisions.

It ends with one frozen accepted record. It does not create a finding or
report and does not add platform technology.
