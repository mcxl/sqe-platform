# ACE Sprint 4 Evidence-To-Conclusion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one fictional, local and human-controlled
Evidence-to-Conclusion chain that links an accepted Sprint 3 planning trace to
separate approved implementation and effectiveness conclusions.

**Architecture:** Add frozen Pydantic records in one focused domain module and
one approval service beside the existing MATE and planning-trace services.
The service validates exact question, evidence, proposal and decision
identities before constructing one protected immutable accepted record. It
does not change the evaluator, application routes or earlier approval gates.

**Tech Stack:** Python 3.11 or later, Pydantic v2, Pytest, the existing ACE
domain and engine modules, and PowerShell for local verification.

## Global Constraints

- Work only on branch `codex/ace-sprint-1`, starting from approved design
  commit `11a38954b6762283d0923382e99560508e770fde`.
- Keep execution local and private.
- Use fictional evidence and fictional reviewer identifiers only.
- Do not introduce telemetry, analytics, external API calls or network
  clients.
- Do not add PostgreSQL, Supabase, persistence, file evidence storage,
  full-text search, pgvector, Neo4j, GraphRAG or another graph platform.
- Do not add AI, automated question generation, automated evidence
  classification or automated conclusions.
- Do not add or change FastAPI routes or response bodies.
- MATE means only Mandate, Accountability, Trigger and Escalation.
- Do not change the MATE evaluator or its rating precedence.
- Keep audit questions, evidence records, proposals, decisions and accepted
  results immutable.
- Use strict canonical UTC timestamps.
- Do not create findings, reports, corrective actions, risk-reduction claims
  or CONTRA.
- Preserve unrelated modified and untracked files.
- Do not reset, clean, discard, stage or commit unrelated work.
- Do not push, deploy, publish, open a tunnel or contact an external service.
- Do not suppress the known FastAPI/Starlette TestClient deprecation warning.
- Use the retained verification interpreter:
  `C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe`.

---

## File Structure

### Create

- `src/ace/domain/conclusion.py`
  - Sprint 4 enums and frozen question, evidence, conclusion, decision and
    accepted-record models.
- `src/ace/engine/conclusion.py`
  - The deterministic integrity and approval gate.
- `tests/test_evidence_to_conclusion.py`
  - Fictional builders plus all Sprint 4 domain, gate, integration, privacy
    and regression tests.

### Modify

- `src/ace/domain/__init__.py`
  - Export only the approved Sprint 4 domain vocabulary.
- `src/ace/engine/__init__.py`
  - Export only the Sprint 4 exception and gate function.

### Verify Unchanged

- `src/ace/domain/assessment.py`
- `src/ace/domain/trace.py`
- `src/ace/domain/models.py`
- `src/ace/engine/approval.py`
- `src/ace/engine/tracing.py`
- `src/ace/engine/evaluator.py`
- `src/ace/app.py`
- all existing tests

---

### Task 1: Audit-Question Records And Decisions

**Files:**

- Create: `src/ace/domain/conclusion.py`
- Create: `tests/test_evidence_to_conclusion.py`

**Interfaces:**

- Consumes:
  - `AuditorDecisionStatus` from `src.ace.domain.assessment`.
- Produces:
  - `AuditQuestionType`
  - `ConclusionType`
  - `ProposedAuditQuestion`
  - `AuditorQuestionDecision`

- [ ] **Step 1: Write failing question-record tests**

Create `tests/test_evidence_to_conclusion.py` with these imports and tests:

```python
from typing import Any

import pytest
from pydantic import ValidationError

from src.ace.domain.assessment import AuditorDecisionStatus
from src.ace.domain.conclusion import (
    AuditQuestionType,
    AuditorQuestionDecision,
    ConclusionType,
    ProposedAuditQuestion,
)


def validated_copy(model: Any, **changes: object) -> Any:
    values = model.model_dump()
    values.update(changes)
    return type(model).model_validate(values)


def make_question(
    question_type: AuditQuestionType,
    *,
    question_id: str | None = None,
    version: int = 1,
    control_id: str = "ACE-FICTIONAL-001",
) -> ProposedAuditQuestion:
    selected_id = question_id or f"AQ-{question_type.value}-001"
    if question_type is AuditQuestionType.MAIN:
        parent_id = None
        conclusion_type = None
        wording = (
            "Has the fictional mobilisation control been implemented "
            "and operated effectively?"
        )
    elif question_type is AuditQuestionType.IMPLEMENTATION:
        parent_id = "AQ-MAIN-001"
        conclusion_type = ConclusionType.IMPLEMENTATION
        wording = (
            "What evidence shows that the fictional control was put "
            "into practice?"
        )
    else:
        parent_id = "AQ-MAIN-001"
        conclusion_type = ConclusionType.EFFECTIVENESS
        wording = (
            "What evidence shows that the fictional implemented control "
            "achieved its intended result?"
        )
    return ProposedAuditQuestion(
        question_id=selected_id,
        question_version=version,
        question_type=question_type,
        wording=wording,
        purpose=f"Fictional purpose for {question_type.value}.",
        control_id=control_id,
        parent_question_id=parent_id,
        required_conclusion_type=conclusion_type,
    )


def make_question_decision(
    question: ProposedAuditQuestion,
    *,
    status: AuditorDecisionStatus = AuditorDecisionStatus.APPROVED,
) -> AuditorQuestionDecision:
    return AuditorQuestionDecision(
        decision_id=f"QDEC-{question.question_type.value}-001",
        question_id=question.question_id,
        question_version=question.question_version,
        question_type=question.question_type,
        decision_status=status,
        reviewer_id="FICTIONAL-AUDITOR-01",
        review_notes=f"Fictional review of {question.question_type.value}.",
        reviewed_at="2026-07-28T02:03:04.567890+00:00",
    )


def test_question_vocabulary_is_stable() -> None:
    assert [value.value for value in AuditQuestionType] == [
        "MAIN",
        "IMPLEMENTATION",
        "EFFECTIVENESS",
    ]
    assert [value.value for value in ConclusionType] == [
        "IMPLEMENTATION",
        "EFFECTIVENESS",
    ]


@pytest.mark.parametrize("version", [0, -1, "1"])
def test_question_version_is_a_positive_strict_integer(version: object) -> None:
    with pytest.raises(ValidationError):
        make_question(AuditQuestionType.MAIN, version=version)


def test_main_question_rejects_a_parent() -> None:
    question = make_question(AuditQuestionType.MAIN)
    with pytest.raises(
        ValidationError,
        match="main question must not have a parent",
    ):
        validated_copy(question, parent_question_id="AQ-OTHER")


def test_main_question_rejects_a_required_conclusion_type() -> None:
    question = make_question(AuditQuestionType.MAIN)
    with pytest.raises(
        ValidationError,
        match="main question must not require one conclusion type",
    ):
        validated_copy(
            question,
            required_conclusion_type=ConclusionType.IMPLEMENTATION,
        )


@pytest.mark.parametrize(
    ("question_type", "expected_conclusion"),
    [
        (AuditQuestionType.IMPLEMENTATION, ConclusionType.IMPLEMENTATION),
        (AuditQuestionType.EFFECTIVENESS, ConclusionType.EFFECTIVENESS),
    ],
)
def test_sub_question_requires_parent_and_matching_conclusion_type(
    question_type: AuditQuestionType,
    expected_conclusion: ConclusionType,
) -> None:
    question = make_question(question_type)
    assert question.parent_question_id == "AQ-MAIN-001"
    assert question.required_conclusion_type is expected_conclusion

    with pytest.raises(ValidationError, match="sub-question requires a parent"):
        validated_copy(question, parent_question_id=None)

    wrong_conclusion = (
        ConclusionType.EFFECTIVENESS
        if expected_conclusion is ConclusionType.IMPLEMENTATION
        else ConclusionType.IMPLEMENTATION
    )
    with pytest.raises(
        ValidationError,
        match="sub-question conclusion type does not match",
    ):
        validated_copy(question, required_conclusion_type=wrong_conclusion)


@pytest.mark.parametrize(
    "timestamp",
    [
        "not-a-timestamp",
        "2026-07-28T02:03:04.567890",
        "2026-07-28T12:03:04.567890+10:00",
        "2026-07-28 02:03:04.567890+00:00",
        " 2026-07-28T02:03:04.567890+00:00",
        "2026-07-28T02:03:04.567890+00:00 ",
    ],
)
def test_question_decision_rejects_noncanonical_utc(timestamp: str) -> None:
    decision = make_question_decision(
        make_question(AuditQuestionType.MAIN)
    )
    with pytest.raises(ValidationError):
        validated_copy(decision, reviewed_at=timestamp)


def test_question_records_are_frozen() -> None:
    question = make_question(AuditQuestionType.MAIN)
    decision = make_question_decision(question)
    with pytest.raises(ValidationError):
        question.wording = "Changed"
    with pytest.raises(ValidationError):
        decision.decision_status = AuditorDecisionStatus.REJECTED
```

- [ ] **Step 2: Run the question tests and confirm red**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py -q
```

Expected: collection fails with
`ModuleNotFoundError: No module named 'src.ace.domain.conclusion'`.

- [ ] **Step 3: Implement the question vocabulary and records**

Create `src/ace/domain/conclusion.py`. Use:

```python
"""Domain records for one fictional Evidence-to-Conclusion chain."""

from datetime import datetime, timedelta
from enum import Enum
import re
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)

from .assessment import AuditorDecisionStatus


NonEmptyText = Annotated[str, Field(min_length=1)]
PositiveVersion = Annotated[StrictInt, Field(gt=0)]
CONCLUSION_UTC_ISO_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:\+00:00|Z)"
)


def _validate_canonical_utc(value: str, label: str) -> str:
    if CONCLUSION_UTC_ISO_TIMESTAMP.fullmatch(value) is None:
        raise ValueError(f"{label} must use canonical UTC ISO 8601 format")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{label} must use ISO 8601 format") from error
    if parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must use a zero UTC offset")
    return value


class AuditQuestionType(str, Enum):
    MAIN = "MAIN"
    IMPLEMENTATION = "IMPLEMENTATION"
    EFFECTIVENESS = "EFFECTIVENESS"


class ConclusionType(str, Enum):
    IMPLEMENTATION = "IMPLEMENTATION"
    EFFECTIVENESS = "EFFECTIVENESS"


class ProposedAuditQuestion(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    question_id: NonEmptyText
    question_version: PositiveVersion
    question_type: AuditQuestionType
    wording: NonEmptyText
    purpose: NonEmptyText
    control_id: NonEmptyText
    parent_question_id: NonEmptyText | None = None
    required_conclusion_type: ConclusionType | None = None

    @model_validator(mode="after")
    def validate_question_shape(self) -> "ProposedAuditQuestion":
        if self.question_type is AuditQuestionType.MAIN:
            if self.parent_question_id is not None:
                raise ValueError("main question must not have a parent")
            if self.required_conclusion_type is not None:
                raise ValueError(
                    "main question must not require one conclusion type"
                )
            return self

        if self.parent_question_id is None:
            raise ValueError("sub-question requires a parent")
        expected = ConclusionType(self.question_type.value)
        if self.required_conclusion_type is not expected:
            raise ValueError("sub-question conclusion type does not match")
        return self


class AuditorQuestionDecision(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    decision_id: NonEmptyText
    question_id: NonEmptyText
    question_version: PositiveVersion
    question_type: AuditQuestionType
    decision_status: AuditorDecisionStatus
    reviewer_id: NonEmptyText
    review_notes: NonEmptyText
    reviewed_at: NonEmptyText

    @field_validator("reviewed_at", mode="before")
    @classmethod
    def reject_timestamp_whitespace(cls, value: object) -> object:
        if isinstance(value, str) and value != value.strip():
            raise ValueError(
                "review timestamp must not contain surrounding whitespace"
            )
        return value

    @field_validator("reviewed_at")
    @classmethod
    def validate_reviewed_at(cls, value: str) -> str:
        return _validate_canonical_utc(value, "review timestamp")
```

Do not import FastAPI, filesystems, databases, network clients or the MATE
evaluator.

- [ ] **Step 4: Run the focused tests and confirm green**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py -q
```

Expected: all Task 1 tests pass.

- [ ] **Step 5: Commit Task 1**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add -- src/ace/domain/conclusion.py tests/test_evidence_to_conclusion.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: add controlled audit question records"
```

---

### Task 2: Evidence Provenance And Matrix Records

**Files:**

- Modify: `src/ace/domain/conclusion.py`
- Modify: `tests/test_evidence_to_conclusion.py`

**Interfaces:**

- Consumes:
  - `NonEmptyText`
  - `_validate_canonical_utc()`
- Produces:
  - `EvidenceOrigin`
  - `EvidenceFreshness`
  - `EvidenceRelevance`
  - `EvidenceGapStatus`
  - `EvidenceGapDisposition`
  - `ConclusionEvidenceSufficiency`
  - `ConclusionContradictionStatus`
  - `EvidenceItem`
  - `EvidenceMatrixEntry`
  - `EvidenceGap`
  - `EvidenceMatrixReview`

- [ ] **Step 1: Write failing evidence-record tests**

Append imports and helpers:

```python
from src.ace.domain.conclusion import (
    ConclusionContradictionStatus,
    ConclusionEvidenceSufficiency,
    EvidenceFreshness,
    EvidenceGap,
    EvidenceGapDisposition,
    EvidenceGapStatus,
    EvidenceItem,
    EvidenceMatrixEntry,
    EvidenceMatrixReview,
    EvidenceOrigin,
    EvidenceRelevance,
)


def make_evidence(
    evidence_id: str,
    *,
    origin: EvidenceOrigin = EvidenceOrigin.RAW,
    freshness: EvidenceFreshness = EvidenceFreshness.CURRENT,
    source_evidence_ids: tuple[str, ...] = (),
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        title=f"Fictional evidence {evidence_id}",
        description=f"Fictional description for {evidence_id}.",
        origin=origin,
        source_title_or_originator="Fictional mobilisation register",
        source_version_or_date="Version 1.0",
        source_location=f"Entry {evidence_id}",
        collected_at="2026-07-28T03:04:05+00:00",
        valid_from="2026-07-01T00:00:00+00:00",
        valid_until="2026-08-01T00:00:00+00:00",
        freshness=freshness,
        source_evidence_ids=source_evidence_ids,
    )


def make_entry(
    entry_id: str,
    question_id: str,
    evidence_id: str,
    relevance: EvidenceRelevance = EvidenceRelevance.SUPPORTS,
) -> EvidenceMatrixEntry:
    return EvidenceMatrixEntry(
        entry_id=entry_id,
        question_id=question_id,
        evidence_id=evidence_id,
        relevance=relevance,
        rationale=f"Fictional relevance rationale for {evidence_id}.",
        reviewer_limitations=("Fictional pilot evidence only.",),
    )


def make_gap(
    gap_id: str,
    question_id: str,
    *,
    status: EvidenceGapStatus = EvidenceGapStatus.REQUESTED_NOT_PROVIDED,
    material: bool = True,
    disposition: EvidenceGapDisposition = EvidenceGapDisposition.OPEN,
) -> EvidenceGap:
    return EvidenceGap(
        gap_id=gap_id,
        question_id=question_id,
        status=status,
        description=f"Fictional evidence gap {gap_id}.",
        is_material=material,
        materiality_rationale=f"Fictional materiality rationale for {gap_id}.",
        disposition=disposition,
        disposition_rationale=(
            None
            if disposition is EvidenceGapDisposition.OPEN
            else f"Fictional disposition rationale for {gap_id}."
        ),
    )


def test_evidence_vocabulary_is_stable() -> None:
    assert [value.value for value in EvidenceOrigin] == [
        "RAW",
        "DERIVED",
        "AUDITOR_AUTHORED",
    ]
    assert [value.value for value in EvidenceFreshness] == [
        "CURRENT",
        "STALE",
        "SUPERSEDED",
        "UNCERTAIN",
    ]
    assert [value.value for value in EvidenceRelevance] == [
        "SUPPORTS",
        "WEAKENS",
        "CONTRADICTS",
    ]


def test_raw_evidence_rejects_source_evidence_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="raw evidence must not identify source evidence",
    ):
        make_evidence(
            "EVID-RAW-001",
            source_evidence_ids=("EVID-OTHER",),
        )


def test_derived_evidence_requires_source_evidence_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="derived evidence requires raw source evidence",
    ):
        make_evidence("EVID-DERIVED-001", origin=EvidenceOrigin.DERIVED)


def test_evidence_rejects_reversed_validity_period() -> None:
    evidence = make_evidence("EVID-RAW-001")
    with pytest.raises(
        ValidationError,
        match="validity end must not precede validity start",
    ):
        validated_copy(
            evidence,
            valid_from="2026-08-02T00:00:00+00:00",
            valid_until="2026-08-01T00:00:00+00:00",
        )


@pytest.mark.parametrize(
    "disposition",
    [
        EvidenceGapDisposition.RESOLVED,
        EvidenceGapDisposition.ACCEPTED_LIMITATION,
    ],
)
def test_non_open_gap_requires_disposition_rationale(
    disposition: EvidenceGapDisposition,
) -> None:
    gap = make_gap(
        "GAP-IMP-001",
        "AQ-IMPLEMENTATION-001",
        disposition=disposition,
    )
    with pytest.raises(
        ValidationError,
        match="gap disposition requires a rationale",
    ):
        validated_copy(gap, disposition_rationale=None)


def test_matrix_requires_an_entry_or_explicit_gap() -> None:
    with pytest.raises(
        ValidationError,
        match="matrix review requires evidence or an explicit gap",
    ):
        EvidenceMatrixReview(
            review_id="MATRIX-IMP-001",
            question_id="AQ-IMPLEMENTATION-001",
            entries=(),
            gaps=(),
            contradiction_status=(
                ConclusionContradictionStatus.NONE_IDENTIFIED
            ),
            contradiction_evidence_ids=(),
            contradiction_explanation=None,
            assumptions=(),
            limitations=("No fictional evidence was supplied.",),
            proposed_sufficiency=(
                ConclusionEvidenceSufficiency.INSUFFICIENT
            ),
        )


def test_explained_contradiction_requires_unique_evidence_and_explanation() -> None:
    entry = make_entry(
        "ENTRY-IMP-001",
        "AQ-IMPLEMENTATION-001",
        "EVID-RAW-001",
    )
    with pytest.raises(ValidationError):
        EvidenceMatrixReview(
            review_id="MATRIX-IMP-001",
            question_id="AQ-IMPLEMENTATION-001",
            entries=(entry,),
            gaps=(),
            contradiction_status=ConclusionContradictionStatus.EXPLAINED,
            contradiction_evidence_ids=("EVID-RAW-001",),
            contradiction_explanation=None,
            assumptions=(),
            limitations=(),
            proposed_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
        )


def test_evidence_records_are_frozen() -> None:
    evidence = make_evidence("EVID-RAW-001")
    with pytest.raises(ValidationError):
        evidence.freshness = EvidenceFreshness.STALE
```

- [ ] **Step 2: Run the focused tests and confirm red**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py -q
```

Expected: collection fails because the new evidence types are not defined.

- [ ] **Step 3: Implement the evidence vocabulary**

Add these exact enum values to `src/ace/domain/conclusion.py`:

```python
class EvidenceOrigin(str, Enum):
    RAW = "RAW"
    DERIVED = "DERIVED"
    AUDITOR_AUTHORED = "AUDITOR_AUTHORED"


class EvidenceFreshness(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"
    UNCERTAIN = "UNCERTAIN"


class EvidenceRelevance(str, Enum):
    SUPPORTS = "SUPPORTS"
    WEAKENS = "WEAKENS"
    CONTRADICTS = "CONTRADICTS"


class EvidenceGapStatus(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    REQUESTED_NOT_PROVIDED = "REQUESTED_NOT_PROVIDED"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    INADEQUATE = "INADEQUATE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceGapDisposition(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    ACCEPTED_LIMITATION = "ACCEPTED_LIMITATION"


class ConclusionEvidenceSufficiency(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    UNRESOLVED = "UNRESOLVED"


class ConclusionContradictionStatus(str, Enum):
    NONE_IDENTIFIED = "NONE_IDENTIFIED"
    EXPLAINED = "EXPLAINED"
    UNRESOLVED = "UNRESOLVED"
```

- [ ] **Step 4: Implement evidence and matrix records**

Add frozen models with these exact fields:

```python
class EvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    evidence_id: NonEmptyText
    title: NonEmptyText
    description: NonEmptyText
    origin: EvidenceOrigin
    source_title_or_originator: NonEmptyText
    source_version_or_date: NonEmptyText
    source_location: NonEmptyText
    collected_at: NonEmptyText
    valid_from: NonEmptyText | None = None
    valid_until: NonEmptyText | None = None
    freshness: EvidenceFreshness
    source_evidence_ids: tuple[NonEmptyText, ...] = ()


class EvidenceMatrixEntry(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    entry_id: NonEmptyText
    question_id: NonEmptyText
    evidence_id: NonEmptyText
    relevance: EvidenceRelevance
    rationale: NonEmptyText
    reviewer_limitations: tuple[NonEmptyText, ...] = ()


class EvidenceGap(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    gap_id: NonEmptyText
    question_id: NonEmptyText
    status: EvidenceGapStatus
    description: NonEmptyText
    is_material: StrictBool
    materiality_rationale: NonEmptyText
    disposition: EvidenceGapDisposition
    disposition_rationale: str | None = None


class EvidenceMatrixReview(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    review_id: NonEmptyText
    question_id: NonEmptyText
    entries: tuple[EvidenceMatrixEntry, ...] = ()
    gaps: tuple[EvidenceGap, ...] = ()
    contradiction_status: ConclusionContradictionStatus
    contradiction_evidence_ids: tuple[NonEmptyText, ...] = ()
    contradiction_explanation: str | None = None
    assumptions: tuple[NonEmptyText, ...] = ()
    limitations: tuple[NonEmptyText, ...] = ()
    proposed_sufficiency: ConclusionEvidenceSufficiency
```

Import `StrictBool`. Implement these validators:

1. `EvidenceItem`:
   - reject timestamp whitespace before parsing;
   - validate `collected_at`, `valid_from` and `valid_until` with
     `_validate_canonical_utc()`;
   - reject duplicate `source_evidence_ids`;
   - require no source IDs for `RAW`;
   - require at least one source ID for `DERIVED`;
   - allow zero or more source IDs for `AUDITOR_AUTHORED`;
   - when both validity bounds exist, parse them and reject
     `valid_until < valid_from`.
2. `EvidenceGap`:
   - require non-empty `disposition_rationale` for `RESOLVED` and
     `ACCEPTED_LIMITATION`.
3. `EvidenceMatrixReview`:
   - require at least one entry or gap;
   - reject duplicate entry IDs, evidence IDs within the same matrix and gap
     IDs;
   - `NONE_IDENTIFIED` requires no contradiction IDs;
   - `EXPLAINED` and `UNRESOLVED` require at least two unique contradiction
     evidence IDs;
   - `EXPLAINED` requires a non-empty explanation.

Use `datetime.fromisoformat()` for the validity comparison. Do not calculate
freshness from the current clock; freshness is an explicit reviewed
classification in this pilot.

- [ ] **Step 5: Run focused evidence tests**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py -q
```

Expected: all Task 1 and Task 2 tests pass.

- [ ] **Step 6: Commit Task 2**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add -- src/ace/domain/conclusion.py tests/test_evidence_to_conclusion.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: add evidence matrix records"
```

---

### Task 3: Conclusion Decisions And Protected Accepted Record

**Files:**

- Modify: `src/ace/domain/conclusion.py`
- Modify: `tests/test_evidence_to_conclusion.py`

**Interfaces:**

- Consumes:
  - `AcceptedPlanningTrace`
  - the Task 1 and Task 2 records
- Produces:
  - `ImplementationConclusion`
  - `EffectivenessConclusion`
  - `ProposedImplementationConclusion`
  - `ProposedEffectivenessConclusion`
  - `AuditorConclusionDecision`
  - `AcceptedEvidenceToConclusionRecord`

- [ ] **Step 1: Write failing conclusion-record tests**

Append:

```python
from src.ace.domain.conclusion import (
    AcceptedEvidenceToConclusionRecord,
    AuditorConclusionDecision,
    EffectivenessConclusion,
    ImplementationConclusion,
    ProposedEffectivenessConclusion,
    ProposedImplementationConclusion,
)


def make_implementation_proposal(
    *,
    outcome: ImplementationConclusion = (
        ImplementationConclusion.IMPLEMENTED
    ),
    relied_upon_evidence_ids: tuple[str, ...] = ("EVID-IMP-RAW-001",),
    considered_gap_ids: tuple[str, ...] = (),
) -> ProposedImplementationConclusion:
    return ProposedImplementationConclusion(
        proposal_id="CONC-IMP-001",
        proposal_version=1,
        question_id="AQ-IMPLEMENTATION-001",
        proposed_outcome=outcome,
        evidence_review_id="MATRIX-IMP-001",
        relied_upon_evidence_ids=relied_upon_evidence_ids,
        considered_gap_ids=considered_gap_ids,
        reasoning="Fictional implementation reasoning.",
        assumptions=("The fictional register is complete.",),
        limitations=("Fictional pilot evidence only.",),
    )


def make_effectiveness_proposal(
    *,
    outcome: EffectivenessConclusion = EffectivenessConclusion.EFFECTIVE,
    relied_upon_evidence_ids: tuple[str, ...] = ("EVID-EFF-RAW-001",),
    considered_gap_ids: tuple[str, ...] = (),
) -> ProposedEffectivenessConclusion:
    return ProposedEffectivenessConclusion(
        proposal_id="CONC-EFF-001",
        proposal_version=1,
        question_id="AQ-EFFECTIVENESS-001",
        proposed_outcome=outcome,
        evidence_review_id="MATRIX-EFF-001",
        relied_upon_evidence_ids=relied_upon_evidence_ids,
        considered_gap_ids=considered_gap_ids,
        reasoning="Fictional effectiveness reasoning.",
        assumptions=("The fictional outcome measure is relevant.",),
        limitations=("Fictional pilot evidence only.",),
    )


def make_conclusion_decision(
    proposal: (
        ProposedImplementationConclusion
        | ProposedEffectivenessConclusion
    ),
    *,
    status: AuditorDecisionStatus = AuditorDecisionStatus.APPROVED,
    final_sufficiency: ConclusionEvidenceSufficiency = (
        ConclusionEvidenceSufficiency.SUFFICIENT
    ),
) -> AuditorConclusionDecision:
    is_implementation = isinstance(
        proposal,
        ProposedImplementationConclusion,
    )
    return AuditorConclusionDecision(
        decision_id=(
            "CDEC-IMP-001" if is_implementation else "CDEC-EFF-001"
        ),
        proposal_id=proposal.proposal_id,
        proposal_version=proposal.proposal_version,
        conclusion_type=(
            ConclusionType.IMPLEMENTATION
            if is_implementation
            else ConclusionType.EFFECTIVENESS
        ),
        decision_status=status,
        approved_outcome=(
            proposal.proposed_outcome
            if status is AuditorDecisionStatus.APPROVED
            else None
        ),
        final_sufficiency=final_sufficiency,
        reviewer_id="FICTIONAL-AUDITOR-01",
        review_notes="Fictional conclusion review.",
        reviewed_at="2026-07-28T04:05:06+00:00",
    )


def test_conclusion_vocabularies_are_stable() -> None:
    assert [value.value for value in ImplementationConclusion] == [
        "IMPLEMENTED",
        "PARTIALLY_IMPLEMENTED",
        "NOT_IMPLEMENTED",
        "NOT_DETERMINED",
    ]
    assert [value.value for value in EffectivenessConclusion] == [
        "EFFECTIVE",
        "PARTIALLY_EFFECTIVE",
        "INEFFECTIVE",
        "NOT_DETERMINED",
    ]


def test_non_approved_decision_rejects_an_approved_outcome() -> None:
    proposal = make_implementation_proposal()
    decision = make_conclusion_decision(proposal)
    with pytest.raises(
        ValidationError,
        match="non-approved decision must not contain an approved outcome",
    ):
        validated_copy(
            decision,
            decision_status=AuditorDecisionStatus.CHANGES_REQUIRED,
        )


def test_not_determined_decision_rejects_sufficient_final_evidence() -> None:
    proposal = make_implementation_proposal(
        outcome=ImplementationConclusion.NOT_DETERMINED,
        relied_upon_evidence_ids=(),
        considered_gap_ids=("GAP-IMP-001",),
    )
    with pytest.raises(
        ValidationError,
        match="not determined requires insufficient or unresolved evidence",
    ):
        make_conclusion_decision(
            proposal,
            final_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
        )


def test_substantive_decision_requires_sufficient_evidence() -> None:
    proposal = make_effectiveness_proposal()
    with pytest.raises(
        ValidationError,
        match="substantive conclusion requires sufficient evidence",
    ):
        make_conclusion_decision(
            proposal,
            final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
        )
```

- [ ] **Step 2: Run the tests and confirm red**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py -q
```

Expected: collection fails because the conclusion types are not defined.

- [ ] **Step 3: Implement conclusion proposals and decisions**

Import `ValidationInfo` and `AcceptedPlanningTrace`. Add:

```python
class ImplementationConclusion(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    PARTIALLY_IMPLEMENTED = "PARTIALLY_IMPLEMENTED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_DETERMINED = "NOT_DETERMINED"


class EffectivenessConclusion(str, Enum):
    EFFECTIVE = "EFFECTIVE"
    PARTIALLY_EFFECTIVE = "PARTIALLY_EFFECTIVE"
    INEFFECTIVE = "INEFFECTIVE"
    NOT_DETERMINED = "NOT_DETERMINED"


class ProposedImplementationConclusion(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    proposal_id: NonEmptyText
    proposal_version: PositiveVersion
    question_id: NonEmptyText
    proposed_outcome: ImplementationConclusion
    evidence_review_id: NonEmptyText
    relied_upon_evidence_ids: tuple[NonEmptyText, ...] = ()
    considered_gap_ids: tuple[NonEmptyText, ...] = ()
    reasoning: NonEmptyText
    assumptions: tuple[NonEmptyText, ...] = ()
    limitations: tuple[NonEmptyText, ...] = ()


class ProposedEffectivenessConclusion(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    proposal_id: NonEmptyText
    proposal_version: PositiveVersion
    question_id: NonEmptyText
    proposed_outcome: EffectivenessConclusion
    evidence_review_id: NonEmptyText
    relied_upon_evidence_ids: tuple[NonEmptyText, ...] = ()
    considered_gap_ids: tuple[NonEmptyText, ...] = ()
    reasoning: NonEmptyText
    assumptions: tuple[NonEmptyText, ...] = ()
    limitations: tuple[NonEmptyText, ...] = ()


ApprovedConclusionOutcome = (
    ImplementationConclusion | EffectivenessConclusion
)


class AuditorConclusionDecision(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    decision_id: NonEmptyText
    proposal_id: NonEmptyText
    proposal_version: PositiveVersion
    conclusion_type: ConclusionType
    decision_status: AuditorDecisionStatus
    approved_outcome: ApprovedConclusionOutcome | None = None
    final_sufficiency: ConclusionEvidenceSufficiency
    reviewer_id: NonEmptyText
    review_notes: NonEmptyText
    reviewed_at: NonEmptyText
```

Implement:

- duplicate-ID validators for `relied_upon_evidence_ids` and
  `considered_gap_ids` on both proposal classes;
- the same strict timestamp validators used by
  `AuditorQuestionDecision`;
- a decision-state validator that:
  - requires an approved outcome for `APPROVED`;
  - forbids an approved outcome for other states;
  - requires an implementation enum for implementation decisions;
  - requires an effectiveness enum for effectiveness decisions;
  - requires `INSUFFICIENT` or `UNRESOLVED` when the approved outcome is
    `NOT_DETERMINED`;
  - requires `SUFFICIENT` for every other approved outcome.

- [ ] **Step 4: Implement protected accepted-record construction**

Add:

```python
_ACCEPTED_CONCLUSION_CONTEXT_KEY = "accepted_conclusion_factory"
_ACCEPTED_CONCLUSION_FACTORY_SENTINEL = object()


class AcceptedEvidenceToConclusionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    planning_trace: AcceptedPlanningTrace
    questions: tuple[ProposedAuditQuestion, ...] = Field(
        min_length=3,
        max_length=3,
    )
    question_decisions: tuple[AuditorQuestionDecision, ...] = Field(
        min_length=3,
        max_length=3,
    )
    evidence_items: tuple[EvidenceItem, ...] = ()
    evidence_reviews: tuple[EvidenceMatrixReview, ...] = Field(
        min_length=2,
        max_length=2,
    )
    implementation_proposal: ProposedImplementationConclusion
    effectiveness_proposal: ProposedEffectivenessConclusion
    conclusion_decisions: tuple[AuditorConclusionDecision, ...] = Field(
        min_length=2,
        max_length=2,
    )
    question_decision_ids: tuple[NonEmptyText, ...] = Field(
        min_length=3,
        max_length=3,
    )
    conclusion_decision_ids: tuple[NonEmptyText, ...] = Field(
        min_length=2,
        max_length=2,
    )
    implementation_outcome: ImplementationConclusion
    effectiveness_outcome: EffectivenessConclusion

    @model_validator(mode="before")
    @classmethod
    def require_approval_gate(
        cls,
        values: object,
        info: ValidationInfo,
    ) -> object:
        context = info.context
        if (
            context is None
            or context.get(_ACCEPTED_CONCLUSION_CONTEXT_KEY)
            is not _ACCEPTED_CONCLUSION_FACTORY_SENTINEL
        ):
            raise ValueError(
                "accepted evidence-to-conclusion record must be built "
                "by the approval gate"
            )
        return values

    @classmethod
    def _from_approved_gate(
        cls,
        **values: object,
    ) -> "AcceptedEvidenceToConclusionRecord":
        return cls.model_validate(
            values,
            context={
                _ACCEPTED_CONCLUSION_CONTEXT_KEY:
                    _ACCEPTED_CONCLUSION_FACTORY_SENTINEL
            },
        )
```

Do not duplicate gate validation in the accepted model. The private
construction context is an application workflow control, not a hostile-code
security boundary.

- [ ] **Step 5: Run the focused tests**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py -q
```

Expected: all Tasks 1-3 tests pass.

- [ ] **Step 6: Commit Task 3**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add -- src/ace/domain/conclusion.py tests/test_evidence_to_conclusion.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: add controlled conclusion records"
```

---

### Task 4: Complete Evidence-To-Conclusion Approval Gate

**Files:**

- Create: `src/ace/engine/conclusion.py`
- Modify: `tests/test_evidence_to_conclusion.py`

**Interfaces:**

- Consumes:
  - `AcceptedPlanningTrace`
  - all Sprint 4 domain records
- Produces:
  - `ConclusionApprovalBlockedError`
  - `build_accepted_evidence_to_conclusion(...)`

Exact public signature:

```python
def build_accepted_evidence_to_conclusion(
    *,
    planning_trace: AcceptedPlanningTrace,
    questions: Sequence[ProposedAuditQuestion],
    question_decisions: Sequence[AuditorQuestionDecision],
    evidence_items: Sequence[EvidenceItem],
    evidence_reviews: Sequence[EvidenceMatrixReview],
    implementation_proposal: ProposedImplementationConclusion,
    effectiveness_proposal: ProposedEffectivenessConclusion,
    conclusion_decisions: Sequence[AuditorConclusionDecision],
) -> AcceptedEvidenceToConclusionRecord:
```

- [ ] **Step 1: Add one complete fictional test bundle**

Append test imports for the existing Sprint 1-3 builders:

```python
from src.ace.domain.assessment import (
    AuditorDecision,
    ContradictionStatus,
    EvidenceAvailability,
    EvidenceReviewRecord,
    EvidenceSufficiency,
    MateDimension,
    ProposedAnswer,
    ProposedDimensionAssessment,
    SourceReference,
    SourceStatus,
)
from src.ace.domain.enums import HazardCategory
from src.ace.domain.trace import (
    AccountabilitySubjectType,
    AccountableRoleRecord,
    AcceptedPlanningTrace,
    AuditorRelationshipDecision,
    BindingObligationRecord,
    PlanningControlRecord,
    ProposedTraceRelationship,
    RiskRecord,
    TraceRelationshipType,
)
from src.ace.engine.approval import build_approved_assessment
from src.ace.engine.conclusion import (
    ConclusionApprovalBlockedError,
    build_accepted_evidence_to_conclusion,
)
from src.ace.engine.tracing import build_accepted_planning_trace
```

Add a local `make_accepted_trace()` helper. It must construct:

- control ID `ACE-FICTIONAL-001`;
- current fictional obligation, risk, control and job-role sources;
- one approved MATE proposal, review and decision for each `MateDimension`;
- the four exact Sprint 3 relationship types;
- one approved relationship decision for each proposal; and
- the accepted trace through `build_accepted_planning_trace()`.

Use these fixed identities so later assertions remain stable:

```text
OBL-FICTIONAL-001
RISK-FICTIONAL-001
ACE-FICTIONAL-001
ROLE-FICTIONAL-001
SRC-OBLIGATION
SRC-RISK
SRC-CONTROL
SRC-ROLE
```

Use `2026-07-28T01:02:03+00:00` for MATE and relationship decisions. Copy the
following local construction into the new test file; do not import test
helpers from another test module and do not modify the existing Sprint 3
test:

```python
def make_trace_source(source_id: str) -> SourceReference:
    return SourceReference(
        source_id=source_id,
        document_title=f"Fictional document for {source_id}",
        document_version="1.0",
        source_location=f"Section {source_id}",
        source_wording=f"Fictional source wording for {source_id}.",
        status=SourceStatus.CURRENT,
    )


def make_accepted_trace() -> AcceptedPlanningTrace:
    mate_proposals = []
    mate_reviews = []
    mate_decisions = []
    for dimension in MateDimension:
        source = make_trace_source(f"SRC-MATE-{dimension.value}")
        review = EvidenceReviewRecord(
            review_id=f"REV-MATE-{dimension.value}",
            source_references=(source,),
            supporting_source_ids=(source.source_id,),
            weakening_source_ids=(),
            contradictory_source_ids=(),
            evidence_availability=(
                EvidenceAvailability.REVIEWED_SUPPORTIVE,
            ),
            contradiction_status=ContradictionStatus.NONE_IDENTIFIED,
            contradiction_explanation=None,
            assumptions_checked=("The fictional source is current.",),
            limitations=("Control-design assessment only.",),
            proposed_sufficiency=(
                EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
            ),
        )
        proposal = ProposedDimensionAssessment(
            proposal_id=f"PROP-MATE-{dimension.value}",
            proposal_version=1,
            dimension=dimension,
            proposed_answer=ProposedAnswer.YES,
            rationale=f"Fictional MATE rationale for {dimension.label}.",
            evidence_review_id=review.review_id,
        )
        decision = AuditorDecision(
            decision_id=f"DEC-MATE-{dimension.value}",
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.proposal_version,
            dimension=dimension,
            decision_status=AuditorDecisionStatus.APPROVED,
            approved_answer=True,
            final_sufficiency=(
                EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
            ),
            reviewer_id="FICTIONAL-MATE-AUDITOR",
            review_notes=f"Fictional approval for {dimension.label}.",
            reviewed_at="2026-07-28T01:02:03+00:00",
        )
        mate_reviews.append(review)
        mate_proposals.append(proposal)
        mate_decisions.append(decision)

    mate = build_approved_assessment(
        control_id="ACE-FICTIONAL-001",
        title="Fictional mobilisation approval control",
        description="Fictional control-design assessment for Sprint 4.",
        hazard_category=HazardCategory.GOVERNANCE_OVERSIGHT,
        proposals=tuple(mate_proposals),
        evidence_reviews=tuple(mate_reviews),
        decisions=tuple(mate_decisions),
        reviewer_notes="Fictional Sprint 4 MATE input.",
    )
    obligation = BindingObligationRecord(
        obligation_id="OBL-FICTIONAL-001",
        title="Fictional mobilisation obligation",
        binding_instrument="Fictional Safety Management Policy",
        clause="Clause 4.1",
        obligation_text=(
            "A fictional mobilisation control must be approved before "
            "work starts."
        ),
        source_reference=make_trace_source("SRC-OBLIGATION"),
    )
    risk = RiskRecord(
        risk_id="RISK-FICTIONAL-001",
        title="Fictional uncontrolled mobilisation risk",
        risk_statement=(
            "Work may start without fictional governance approval."
        ),
        source_reference=make_trace_source("SRC-RISK"),
    )
    control = PlanningControlRecord(
        control_id="ACE-FICTIONAL-001",
        title="Fictional mobilisation approval control",
        design_statement=(
            "The fictional accountable role approves mobilisation "
            "before work starts."
        ),
        source_reference=make_trace_source("SRC-CONTROL"),
    )
    role = AccountableRoleRecord(
        accountability_id="ROLE-FICTIONAL-001",
        subject_type=AccountabilitySubjectType.JOB_ROLE,
        subject_title="Fictional Head of Safety",
        accountability_statement=(
            "The fictional role is accountable for the mobilisation control."
        ),
        source_reference=make_trace_source("SRC-ROLE"),
    )
    relationship_specs = (
        (
            TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK,
            obligation.obligation_id,
            risk.risk_id,
            (
                obligation.source_reference.source_id,
                risk.source_reference.source_id,
            ),
        ),
        (
            TraceRelationshipType.CONTROL_TREATS_RISK,
            control.control_id,
            risk.risk_id,
            (
                control.source_reference.source_id,
                risk.source_reference.source_id,
            ),
        ),
        (
            TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL,
            role.accountability_id,
            control.control_id,
            (
                role.source_reference.source_id,
                control.source_reference.source_id,
            ),
        ),
        (
            TraceRelationshipType.CONTROL_HAS_APPROVED_MATE_ASSESSMENT,
            control.control_id,
            f"MATE:{mate.control_id}",
            (control.source_reference.source_id,),
        ),
    )
    relationships = tuple(
        ProposedTraceRelationship(
            relationship_id=f"REL-{relationship_type.value}",
            relationship_version=1,
            relationship_type=relationship_type,
            source_record_id=source_id,
            target_record_id=target_id,
            supporting_source_ids=supporting_ids,
            rationale=f"Fictional rationale for {relationship_type.value}.",
        )
        for relationship_type, source_id, target_id, supporting_ids
        in relationship_specs
    )
    relationship_decisions = tuple(
        AuditorRelationshipDecision(
            decision_id=f"DEC-{relationship.relationship_type.value}",
            relationship_id=relationship.relationship_id,
            relationship_version=relationship.relationship_version,
            relationship_type=relationship.relationship_type,
            decision_status=AuditorDecisionStatus.APPROVED,
            reviewer_id="FICTIONAL-AUDITOR-01",
            review_notes=(
                "Fictional approval for "
                f"{relationship.relationship_type.value}."
            ),
            reviewed_at="2026-07-28T01:02:03+00:00",
        )
        for relationship in relationships
    )
    return build_accepted_planning_trace(
        obligation=obligation,
        risk=risk,
        control=control,
        accountable_role=role,
        relationships=relationships,
        decisions=relationship_decisions,
        mate_assessment=mate,
    )
```

Add this complete bundle:

```python
def make_complete_bundle() -> dict[str, object]:
    accepted_trace = make_accepted_trace()
    main_question = make_question(AuditQuestionType.MAIN)
    implementation_question = make_question(
        AuditQuestionType.IMPLEMENTATION
    )
    effectiveness_question = make_question(
        AuditQuestionType.EFFECTIVENESS
    )
    questions = (
        main_question,
        implementation_question,
        effectiveness_question,
    )
    question_decisions = tuple(
        make_question_decision(question) for question in questions
    )

    implementation_raw = make_evidence("EVID-IMP-RAW-001")
    implementation_derived = make_evidence(
        "EVID-IMP-DERIVED-001",
        origin=EvidenceOrigin.DERIVED,
        source_evidence_ids=(implementation_raw.evidence_id,),
    )
    effectiveness_raw = make_evidence("EVID-EFF-RAW-001")
    effectiveness_auditor_authored = make_evidence(
        "EVID-EFF-AUDITOR-001",
        origin=EvidenceOrigin.AUDITOR_AUTHORED,
        source_evidence_ids=(effectiveness_raw.evidence_id,),
    )
    evidence_items = (
        implementation_raw,
        implementation_derived,
        effectiveness_raw,
        effectiveness_auditor_authored,
    )

    implementation_matrix = EvidenceMatrixReview(
        review_id="MATRIX-IMP-001",
        question_id=implementation_question.question_id,
        entries=(
            make_entry(
                "ENTRY-IMP-RAW-001",
                implementation_question.question_id,
                implementation_raw.evidence_id,
            ),
            make_entry(
                "ENTRY-IMP-DERIVED-001",
                implementation_question.question_id,
                implementation_derived.evidence_id,
            ),
        ),
        gaps=(),
        contradiction_status=(
            ConclusionContradictionStatus.NONE_IDENTIFIED
        ),
        contradiction_evidence_ids=(),
        contradiction_explanation=None,
        assumptions=("The fictional implementation register is complete.",),
        limitations=("Fictional pilot evidence only.",),
        proposed_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
    )
    effectiveness_matrix = EvidenceMatrixReview(
        review_id="MATRIX-EFF-001",
        question_id=effectiveness_question.question_id,
        entries=(
            make_entry(
                "ENTRY-EFF-RAW-001",
                effectiveness_question.question_id,
                effectiveness_raw.evidence_id,
            ),
            make_entry(
                "ENTRY-EFF-AUDITOR-001",
                effectiveness_question.question_id,
                effectiveness_auditor_authored.evidence_id,
            ),
        ),
        gaps=(),
        contradiction_status=(
            ConclusionContradictionStatus.NONE_IDENTIFIED
        ),
        contradiction_evidence_ids=(),
        contradiction_explanation=None,
        assumptions=("The fictional outcome measure is relevant.",),
        limitations=("Fictional pilot evidence only.",),
        proposed_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
    )

    implementation_proposal = make_implementation_proposal()
    effectiveness_proposal = make_effectiveness_proposal()
    implementation_decision = make_conclusion_decision(
        implementation_proposal
    )
    effectiveness_decision = make_conclusion_decision(
        effectiveness_proposal
    )
    return {
        "planning_trace": accepted_trace,
        "questions": questions,
        "question_decisions": question_decisions,
        "evidence_items": evidence_items,
        "evidence_reviews": (
            implementation_matrix,
            effectiveness_matrix,
        ),
        "implementation_proposal": implementation_proposal,
        "effectiveness_proposal": effectiveness_proposal,
        "conclusion_decisions": (
            implementation_decision,
            effectiveness_decision,
        ),
    }
```

Add:

```python
def build_record(**changes: object) -> AcceptedEvidenceToConclusionRecord:
    bundle = make_complete_bundle()
    bundle.update(changes)
    return build_accepted_evidence_to_conclusion(**bundle)


def test_gate_builds_one_complete_accepted_record() -> None:
    record = build_record()

    assert record.planning_trace.control.control_id == "ACE-FICTIONAL-001"
    assert [question.question_type for question in record.questions] == [
        AuditQuestionType.MAIN,
        AuditQuestionType.IMPLEMENTATION,
        AuditQuestionType.EFFECTIVENESS,
    ]
    assert record.implementation_outcome is (
        ImplementationConclusion.IMPLEMENTED
    )
    assert record.effectiveness_outcome is EffectivenessConclusion.EFFECTIVE
    assert record.question_decision_ids == tuple(
        decision.decision_id for decision in record.question_decisions
    )
    assert record.conclusion_decision_ids == tuple(
        decision.decision_id for decision in record.conclusion_decisions
    )


def test_accepted_record_is_frozen_and_gate_only() -> None:
    record = build_record()
    values = record.model_dump()

    with pytest.raises(ValidationError):
        AcceptedEvidenceToConclusionRecord.model_validate(values)
    with pytest.raises(ValidationError):
        record.effectiveness_outcome = EffectivenessConclusion.INEFFECTIVE
```

- [ ] **Step 2: Run the happy-path tests and confirm red**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py::test_gate_builds_one_complete_accepted_record tests/test_evidence_to_conclusion.py::test_accepted_record_is_frozen_and_gate_only -q
```

Expected: collection fails because `src.ace.engine.conclusion` does not exist.

- [ ] **Step 3: Implement identity and approval helpers**

Create `src/ace/engine/conclusion.py` with:

```python
"""Approval gate for one fictional Evidence-to-Conclusion chain."""

from collections.abc import Sequence
from typing import TypeVar

from src.ace.domain.assessment import AuditorDecisionStatus
from src.ace.domain.conclusion import (
    AcceptedEvidenceToConclusionRecord,
    AuditQuestionType,
    AuditorConclusionDecision,
    AuditorQuestionDecision,
    ConclusionContradictionStatus,
    ConclusionEvidenceSufficiency,
    ConclusionType,
    EffectivenessConclusion,
    EvidenceFreshness,
    EvidenceGapDisposition,
    EvidenceItem,
    EvidenceMatrixReview,
    EvidenceOrigin,
    ImplementationConclusion,
    ProposedAuditQuestion,
    ProposedEffectivenessConclusion,
    ProposedImplementationConclusion,
)
from src.ace.domain.trace import AcceptedPlanningTrace


class ConclusionApprovalBlockedError(ValueError):
    """Raised when records do not form an approved conclusion chain."""


RecordT = TypeVar("RecordT")
QUESTION_ORDER = tuple(AuditQuestionType)
```

Implement private helpers with these exact responsibilities:

```python
def _one_for_question_type(
    records: Sequence[RecordT],
    question_type: AuditQuestionType,
    record_name: str,
) -> RecordT:
```

- return exactly one record whose `question_type` matches;
- otherwise raise:
  - `Conclusion blocked: <Title Case Type> <record_name> is missing.`
  - `Conclusion blocked: <Title Case Type> <record_name> appears more than once.`

```python
def _validate_unique_attribute(
    records: Sequence[object],
    attribute: str,
    label: str,
) -> None:
```

- reject duplicate string values with:
  `Conclusion blocked: <label> <value> appears more than once.`

```python
def _matching_question_decision(
    decisions: Sequence[AuditorQuestionDecision],
    question: ProposedAuditQuestion,
) -> AuditorQuestionDecision:
```

- match exact question ID and version;
- require matching question type;
- require `APPROVED`;
- give separate plain-English messages for missing, duplicate, rejected,
  changes-required and mismatched decisions.

```python
def _matching_conclusion_decision(
    decisions: Sequence[AuditorConclusionDecision],
    proposal_id: str,
    proposal_version: int,
    conclusion_type: ConclusionType,
) -> AuditorConclusionDecision:
```

- apply the same exact-version matching and state handling;
- require decision conclusion type to match.

- [ ] **Step 4: Implement the complete gate**

Implement `build_accepted_evidence_to_conclusion()` with these ordered checks:

1. Require exactly one main, implementation and effectiveness question.
2. Reject duplicate question IDs, question identity pairs and question
   decision IDs.
3. Require each sub-question's `parent_question_id` to equal the main
   question ID.
4. Require every question's `control_id` to equal
   `planning_trace.control.control_id`.
5. Match and approve all three question decisions.
6. Reject duplicate evidence IDs.
7. Resolve each `DERIVED` source ID and require the referenced item to be
   `RAW`.
8. Resolve every `AUDITOR_AUTHORED` source ID without changing its origin.
9. Require exactly one matrix review for the implementation question and one
   for the effectiveness question.
10. Reject duplicate review IDs, entry IDs and gap IDs across both matrices.
11. Require every entry and gap to identify its containing matrix question.
12. Resolve every entry and contradiction evidence ID.
13. Require the implementation proposal to identify the implementation
    question and matrix.
14. Require the effectiveness proposal to identify the effectiveness question
    and matrix.
15. Resolve every relied-upon evidence ID and require it to occur in that
    question's matrix entries.
16. Require `considered_gap_ids` to equal the complete set of gap IDs in the
    relevant matrix, including an empty set when there are no gaps.
17. Reject duplicate proposal identity pairs and conclusion decision IDs.
18. Match and approve the two exact conclusion proposal versions.
19. Require each approved outcome to equal its proposal.
20. For each substantive outcome:
    - require final sufficiency `SUFFICIENT`;
    - require at least one relied-upon evidence item;
    - require at least one relied-upon item with freshness `CURRENT`;
    - reject `UNRESOLVED` contradiction status;
    - reject any material gap whose disposition is `OPEN`.
21. For each `NOT_DETERMINED` outcome:
    - require final sufficiency `INSUFFICIENT` or `UNRESOLVED`;
    - require at least one non-empty proposal limitation;
    - require an explicit limiting condition: a gap, an unresolved
      contradiction or relied-upon evidence that is not current.
22. If implementation is `NOT_IMPLEMENTED` or `NOT_DETERMINED`, require
    effectiveness to be `NOT_DETERMINED`.
23. Construct the accepted record only through
    `AcceptedEvidenceToConclusionRecord._from_approved_gate()`.

Use the stable order:

```python
ordered_questions = (
    main_question,
    implementation_question,
    effectiveness_question,
)
ordered_question_decisions = tuple(
    _matching_question_decision(question_decisions, question)
    for question in ordered_questions
)
ordered_reviews = (
    implementation_review,
    effectiveness_review,
)
ordered_conclusion_decisions = (
    implementation_decision,
    effectiveness_decision,
)
```

Pass the approved outcomes from the matching decisions into the accepted
record. Do not infer or recalculate an outcome from evidence wording.

- [ ] **Step 5: Run the complete focused file**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py -q
```

Expected: all Task 1-4 tests pass.

- [ ] **Step 6: Commit Task 4**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add -- src/ace/engine/conclusion.py tests/test_evidence_to_conclusion.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: add evidence conclusion approval gate"
```

---

### Task 5: Gate Failure Coverage And Methodology Hardening

**Files:**

- Modify: `src/ace/engine/conclusion.py`
- Modify: `tests/test_evidence_to_conclusion.py`

**Interfaces:**

- Consumes:
  - the Task 4 gate and fictional bundle.
- Produces:
  - complete negative-path coverage for the approved design.

- [ ] **Step 1: Add question and identity failure tests**

Add tests that each call `build_accepted_evidence_to_conclusion()` and assert a
specific `ConclusionApprovalBlockedError` message for:

```python
def test_gate_blocks_a_missing_question_type() -> None:
    bundle = make_complete_bundle()
    bundle["questions"] = bundle["questions"][:-1]
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="Effectiveness question is missing",
    ):
        build_accepted_evidence_to_conclusion(**bundle)


def test_gate_blocks_a_wrong_sub_question_parent() -> None:
    bundle = make_complete_bundle()
    questions = list(bundle["questions"])
    questions[1] = validated_copy(
        questions[1],
        parent_question_id="AQ-WRONG-001",
    )
    bundle["questions"] = tuple(questions)
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="implementation question does not identify the main question",
    ):
        build_accepted_evidence_to_conclusion(**bundle)


def test_gate_blocks_a_different_control() -> None:
    bundle = make_complete_bundle()
    questions = list(bundle["questions"])
    questions[2] = validated_copy(
        questions[2],
        control_id="ACE-OTHER-001",
    )
    bundle["questions"] = tuple(questions)
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="concerns a different control",
    ):
        build_accepted_evidence_to_conclusion(**bundle)
```

Use this exact body for each remaining case:

```python
def assert_bundle_is_blocked(
    bundle: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ConclusionApprovalBlockedError, match=message):
        build_accepted_evidence_to_conclusion(**bundle)
```

Implement the remaining cases with these exact mutations and message
fragments:

| Case | Exact Bundle Mutation | Expected Message Fragment |
|---|---|---|
| Duplicate question ID | Replace the effectiveness question with a validated copy whose `question_id` is `AQ-IMPLEMENTATION-001` and `question_version` is `2` | `question identifier AQ-IMPLEMENTATION-001 appears more than once` |
| Duplicate question decision ID | Replace the effectiveness question decision with a validated copy whose `decision_id` equals the implementation question decision ID | `question decision identifier` |
| Missing question decision | Remove the effectiveness question decision | `Effectiveness question decision is missing` |
| Question decision version mismatch | Set the implementation question decision version to `2` | `Implementation question decision version does not match` |
| Question decision type mismatch | Set the implementation question decision type to `EFFECTIVENESS` | `Implementation question decision type does not match` |
| Rejected question | Set the implementation question decision status to `REJECTED` | `Implementation question has been rejected` |
| Changes-required question | Set the implementation question decision status to `CHANGES_REQUIRED` | `Implementation question requires changes` |

- [ ] **Step 2: Add provenance and matrix failure tests**

Use `assert_bundle_is_blocked()` for these exact cases:

| Case | Exact Bundle Mutation | Expected Message Fragment |
|---|---|---|
| Duplicate evidence ID | Change `EVID-EFF-RAW-001` to `EVID-IMP-RAW-001` | `evidence identifier EVID-IMP-RAW-001 appears more than once` |
| Missing derived source | Change `EVID-IMP-DERIVED-001.source_evidence_ids` to `("EVID-MISSING",)` | `derived evidence EVID-IMP-DERIVED-001 source EVID-MISSING is missing` |
| Derived source is not raw | Change the derived item to cite `EVID-EFF-AUDITOR-001` | `must resolve to raw evidence` |
| Missing auditor-authored source | Change `EVID-EFF-AUDITOR-001.source_evidence_ids` to `("EVID-MISSING",)` | `auditor-authored evidence EVID-EFF-AUDITOR-001 source EVID-MISSING is missing` |
| Missing implementation matrix | Remove `MATRIX-IMP-001` | `implementation evidence matrix is missing` |
| Duplicate review ID | Change the effectiveness review ID to `MATRIX-IMP-001` | `evidence review identifier MATRIX-IMP-001 appears more than once` |
| Duplicate entry ID across matrices | Change `ENTRY-EFF-RAW-001` to `ENTRY-IMP-RAW-001` | `matrix entry identifier ENTRY-IMP-RAW-001 appears more than once` |
| Duplicate gap ID across matrices | Add a `GAP-SHARED-001` gap to both matrices | `evidence gap identifier GAP-SHARED-001 appears more than once` |
| Entry on wrong question | Change `ENTRY-IMP-RAW-001.question_id` to `AQ-EFFECTIVENESS-001` | `implementation matrix contains an entry for a different question` |
| Gap on wrong question | Add `GAP-IMP-001` to the implementation matrix with question ID `AQ-EFFECTIVENESS-001` | `implementation matrix contains a gap for a different question` |
| Missing entry evidence | Change `ENTRY-IMP-RAW-001.evidence_id` to `EVID-MISSING` | `matrix evidence EVID-MISSING is missing` |
| Missing contradiction evidence | Make the implementation review `UNRESOLVED` with contradiction IDs `("EVID-IMP-RAW-001", "EVID-MISSING")` | `contradiction evidence EVID-MISSING is missing` |
| Missing relied-upon evidence | Change the implementation proposal's relied-upon IDs to `("EVID-MISSING",)` | `relied-upon evidence EVID-MISSING is missing` |
| Relied-upon evidence outside matrix | Change implementation relied-upon IDs to `("EVID-EFF-RAW-001",)` | `is not in the implementation evidence matrix` |
| Omitted matrix gap | Add `GAP-IMP-001` to the implementation matrix and leave `considered_gap_ids` empty | `implementation conclusion does not consider every evidence gap` |

Use this exact stale-evidence assertion:

```python
def test_substantive_conclusion_requires_current_evidence() -> None:
    bundle = make_complete_bundle()
    evidence_items = tuple(
        validated_copy(item, freshness=EvidenceFreshness.STALE)
        if item.evidence_id == "EVID-IMP-RAW-001"
        else item
        for item in bundle["evidence_items"]
    )
    bundle["evidence_items"] = evidence_items
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="implementation conclusion has no current relied-upon evidence",
    ):
        build_accepted_evidence_to_conclusion(**bundle)
```

- [ ] **Step 3: Add conclusion and decision failure tests**

Use `assert_bundle_is_blocked()` for these exact cases:

| Case | Exact Bundle Mutation | Expected Message Fragment |
|---|---|---|
| Implementation proposal uses effectiveness question | Change its `question_id` to `AQ-EFFECTIVENESS-001` | `implementation proposal refers to the wrong question` |
| Effectiveness proposal uses implementation matrix | Change its `evidence_review_id` to `MATRIX-IMP-001` | `effectiveness proposal refers to the wrong evidence matrix` |
| Duplicate proposal identity | Change the effectiveness proposal ID and version to `CONC-IMP-001` and `1` | `conclusion proposal CONC-IMP-001 version 1 appears more than once` |
| Duplicate conclusion decision ID | Change the effectiveness decision ID to `CDEC-IMP-001` | `conclusion decision identifier CDEC-IMP-001 appears more than once` |
| Missing conclusion decision | Remove the effectiveness decision | `Effectiveness conclusion decision is missing` |
| Conclusion decision version mismatch | Set the implementation decision version to `2` | `Implementation conclusion decision version does not match` |
| Conclusion decision type mismatch | Set the implementation decision type to `EFFECTIVENESS` | `Implementation conclusion decision type does not match` |
| Rejected conclusion | Replace the implementation decision with `make_conclusion_decision(proposal, status=REJECTED)` | `Implementation conclusion has been rejected` |
| Changes-required conclusion | Replace the implementation decision with `make_conclusion_decision(proposal, status=CHANGES_REQUIRED)` | `Implementation conclusion requires changes` |
| Approved outcome differs | Change implementation decision outcome to `PARTIALLY_IMPLEMENTED` | `Implementation approved outcome does not match the proposal` |
| Substantive outcome has insufficient final evidence | Change implementation decision final sufficiency to `INSUFFICIENT` | `substantive conclusion requires sufficient evidence` |
| Unresolved contradiction | Set the implementation review to `UNRESOLVED` with both implementation evidence IDs | `implementation evidence contains an unresolved contradiction` |
| Open material gap | Add material `GAP-IMP-001` with disposition `OPEN` and include it in the proposal's considered gaps | `implementation evidence contains an open material gap` |
| Not determined has no limitation text | Use a valid not-determined proposal but set `limitations=()` | `not determined conclusion requires an explicit limitation` |
| Not determined has no limiting condition | Use a not-determined proposal with current evidence, no gap and no contradiction | `not determined conclusion has no evidence limitation` |

Add these dependency tests:

```python
@pytest.mark.parametrize(
    "implementation_outcome",
    [
        ImplementationConclusion.NOT_IMPLEMENTED,
        ImplementationConclusion.NOT_DETERMINED,
    ],
)
def test_effectiveness_cannot_bypass_implementation(
    implementation_outcome: ImplementationConclusion,
) -> None:
    bundle = make_complete_bundle()
    considered_gap_ids: tuple[str, ...] = ()
    if (
        implementation_outcome
        is ImplementationConclusion.NOT_DETERMINED
    ):
        gap = make_gap("GAP-IMP-001", "AQ-IMPLEMENTATION-001")
        implementation_review = validated_copy(
            bundle["evidence_reviews"][0],
            entries=(),
            gaps=(gap,),
            proposed_sufficiency=(
                ConclusionEvidenceSufficiency.INSUFFICIENT
            ),
            limitations=("Requested fictional evidence was not provided.",),
        )
        bundle["evidence_reviews"] = (
            implementation_review,
            bundle["evidence_reviews"][1],
        )
        considered_gap_ids = (gap.gap_id,)
    implementation = make_implementation_proposal(
        outcome=implementation_outcome,
        relied_upon_evidence_ids=(
            ()
            if implementation_outcome
            is ImplementationConclusion.NOT_DETERMINED
            else ("EVID-IMP-RAW-001",)
        ),
        considered_gap_ids=considered_gap_ids,
    )
    if (
        implementation_outcome
        is ImplementationConclusion.NOT_DETERMINED
    ):
        implementation = validated_copy(
            implementation,
            limitations=(
                "Requested fictional implementation evidence was not "
                "provided.",
            ),
        )
    bundle["implementation_proposal"] = implementation
    bundle["conclusion_decisions"] = (
        make_conclusion_decision(
            implementation,
            final_sufficiency=(
                ConclusionEvidenceSufficiency.INSUFFICIENT
                if implementation_outcome
                is ImplementationConclusion.NOT_DETERMINED
                else ConclusionEvidenceSufficiency.SUFFICIENT
            ),
        ),
        bundle["conclusion_decisions"][1],
    )
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="effectiveness must be not determined",
    ):
        build_accepted_evidence_to_conclusion(**bundle)
```

- [ ] **Step 4: Add positive limitation tests**

Add:

```python
def test_not_determined_preserves_missing_evidence_without_calling_it_failure() -> None:
    bundle = make_complete_bundle()
    gap = make_gap("GAP-EFF-001", "AQ-EFFECTIVENESS-001")
    review = EvidenceMatrixReview(
        review_id="MATRIX-EFF-001",
        question_id="AQ-EFFECTIVENESS-001",
        entries=(),
        gaps=(gap,),
        contradiction_status=ConclusionContradictionStatus.NONE_IDENTIFIED,
        contradiction_evidence_ids=(),
        contradiction_explanation=None,
        assumptions=(),
        limitations=("Requested fictional outcome evidence was not provided.",),
        proposed_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
    )
    proposal = make_effectiveness_proposal(
        outcome=EffectivenessConclusion.NOT_DETERMINED,
        relied_upon_evidence_ids=(),
        considered_gap_ids=(gap.gap_id,),
    )
    proposal = validated_copy(
        proposal,
        limitations=("Requested fictional outcome evidence was not provided.",),
    )
    decision = make_conclusion_decision(
        proposal,
        final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
    )
    bundle["evidence_reviews"] = (
        bundle["evidence_reviews"][0],
        review,
    )
    bundle["effectiveness_proposal"] = proposal
    bundle["conclusion_decisions"] = (
        bundle["conclusion_decisions"][0],
        decision,
    )

    record = build_accepted_evidence_to_conclusion(**bundle)

    assert record.effectiveness_outcome is (
        EffectivenessConclusion.NOT_DETERMINED
    )
```

Add a second positive test showing that a material
`ACCEPTED_LIMITATION` gap with a non-empty disposition rationale may coexist
with a substantive outcome only when final sufficiency is `SUFFICIENT` and
current evidence is relied upon. The accepted record must retain the gap and
its rationale.

- [ ] **Step 5: Run the focused suite and fix only demonstrated failures**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py -q
```

Expected: every Sprint 4 test passes. When a test fails, make the smallest
change in `src/ace/engine/conclusion.py` that enforces the named rule. Do not
weaken a test or add a default approval.

- [ ] **Step 6: Commit Task 5**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add -- src/ace/engine/conclusion.py tests/test_evidence_to_conclusion.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "test: harden evidence conclusion approvals"
```

---

### Task 6: Public Exports And Regression Boundaries

**Files:**

- Modify: `src/ace/domain/__init__.py`
- Modify: `src/ace/engine/__init__.py`
- Modify: `tests/test_evidence_to_conclusion.py`

**Interfaces:**

- Consumes:
  - all completed Sprint 4 types and gate.
- Produces:
  - stable package imports for the approved Sprint 4 surface.

- [ ] **Step 1: Write failing export tests**

Append:

```python
def test_sprint_4_public_exports_are_available() -> None:
    from src.ace.domain import (
        AcceptedEvidenceToConclusionRecord,
        AuditQuestionType,
        AuditorConclusionDecision,
        AuditorQuestionDecision,
        ConclusionContradictionStatus,
        ConclusionEvidenceSufficiency,
        ConclusionType,
        EffectivenessConclusion,
        EvidenceFreshness,
        EvidenceGap,
        EvidenceGapDisposition,
        EvidenceGapStatus,
        EvidenceItem,
        EvidenceMatrixEntry,
        EvidenceMatrixReview,
        EvidenceOrigin,
        EvidenceRelevance,
        ImplementationConclusion,
        ProposedAuditQuestion,
        ProposedEffectivenessConclusion,
        ProposedImplementationConclusion,
    )
    from src.ace.engine import (
        ConclusionApprovalBlockedError,
        build_accepted_evidence_to_conclusion,
    )

    assert AuditQuestionType.MAIN.value == "MAIN"
    assert EvidenceOrigin.RAW.value == "RAW"
    assert ImplementationConclusion.IMPLEMENTED.value == "IMPLEMENTED"
    assert EffectivenessConclusion.EFFECTIVE.value == "EFFECTIVE"
    assert AcceptedEvidenceToConclusionRecord is not None
    assert AuditorConclusionDecision is not None
    assert AuditorQuestionDecision is not None
    assert ConclusionContradictionStatus is not None
    assert ConclusionEvidenceSufficiency is not None
    assert ConclusionType is not None
    assert EvidenceFreshness is not None
    assert EvidenceGap is not None
    assert EvidenceGapDisposition is not None
    assert EvidenceGapStatus is not None
    assert EvidenceItem is not None
    assert EvidenceMatrixEntry is not None
    assert EvidenceMatrixReview is not None
    assert EvidenceRelevance is not None
    assert ProposedAuditQuestion is not None
    assert ProposedEffectivenessConclusion is not None
    assert ProposedImplementationConclusion is not None
    assert ConclusionApprovalBlockedError is not None
    assert callable(build_accepted_evidence_to_conclusion)
```

- [ ] **Step 2: Run the export test and confirm red**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py::test_sprint_4_public_exports_are_available -q
```

Expected: import failure because the package exports have not been added.

- [ ] **Step 3: Add explicit exports**

In `src/ace/domain/__init__.py`, import every name listed in the export test
from `.conclusion` and append each exact string to `__all__`.

In `src/ace/engine/__init__.py`, add:

```python
from .conclusion import (
    ConclusionApprovalBlockedError,
    build_accepted_evidence_to_conclusion,
)
```

Append these exact strings to `__all__`:

```python
"ConclusionApprovalBlockedError",
"build_accepted_evidence_to_conclusion",
```

Do not remove, rename or reorder existing exports.

- [ ] **Step 4: Add regression and privacy assertions**

Append:

```python
from pathlib import Path

from fastapi.routing import APIRoute

from src.ace.app import app
from src.ace.domain.enums import ControlRating
from src.ace.domain.models import AssuranceDimensions, Control
from src.ace.engine.evaluator import evaluate_control


def test_existing_routes_remain_exactly_unchanged() -> None:
    routes = sorted(
        route.path
        for route in app.routes
        if isinstance(route, APIRoute)
    )
    assert routes == ["/", "/evaluations"]


@pytest.mark.parametrize(
    ("dimensions", "expected"),
    [
        ((True, True, True, True), ControlRating.ADEQUATE),
        ((True, True, False, True), ControlRating.PARTIALLY_ADEQUATE),
        ((True, True, True, False), ControlRating.PARTIALLY_ADEQUATE),
        ((True, True, False, False), ControlRating.INADEQUATE),
        ((True, False, True, True), ControlRating.INADEQUATE),
        ((False, True, True, True), ControlRating.INADEQUATE),
    ],
)
def test_sprint_4_does_not_change_mate_precedence(
    dimensions: tuple[bool, bool, bool, bool],
    expected: ControlRating,
) -> None:
    mandate, accountability, trigger, escalation = dimensions
    control = Control(
        control_id="ACE-FICTIONAL-REGRESSION",
        title="Fictional regression control",
        description="Fictional MATE regression check.",
        hazard_category=HazardCategory.GOVERNANCE_OVERSIGHT,
        dimensions=AssuranceDimensions(
            mandate=mandate,
            accountability=accountability,
            trigger=trigger,
            escalation=escalation,
        ),
    )
    assert evaluate_control(control).rating is expected


def test_sprint_4_source_has_no_prohibited_platform_capabilities() -> None:
    source = (
        Path("src/ace/domain/conclusion.py").read_text(encoding="utf-8")
        + Path("src/ace/engine/conclusion.py").read_text(encoding="utf-8")
    ).lower()
    for prohibited in (
        "requests",
        "http://",
        "https://",
        "telemetry",
        "analytics",
        "supabase",
        "postgres",
        "pgvector",
        "neo4j",
        "graphrag",
    ):
        assert prohibited not in source
```

The complete pre-existing 16-case truth table remains authoritative. This
focused regression test supplements it; it does not replace or duplicate the
full existing test.

- [ ] **Step 5: Run the Sprint 4 and full suites**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_evidence_to_conclusion.py -q
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: both commands pass. Record the exact full-suite pass count. The
known dependency warning remains visible.

- [ ] **Step 6: Commit Task 6**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add -- src/ace/domain/__init__.py src/ace/engine/__init__.py tests/test_evidence_to_conclusion.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: expose evidence conclusion workflow"
```

---

### Task 7: Independent Review And Final Verification

**Files:**

- Verify only: `src/ace/domain/conclusion.py`
- Verify only: `src/ace/engine/conclusion.py`
- Verify only: `src/ace/domain/__init__.py`
- Verify only: `src/ace/engine/__init__.py`
- Verify only: `tests/test_evidence_to_conclusion.py`
- Verify unchanged: every protected file listed under File Structure

**Interfaces:**

- Consumes: the complete Sprint 4 implementation.
- Produces: fresh completion evidence only; no new functionality.

- [ ] **Step 1: Run the complete test suite**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: the complete suite passes. Record the exact pass count instead of
predicting it. Keep the known FastAPI/Starlette warning visible.

- [ ] **Step 2: Compile the complete source tree**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m compileall -q src
```

Expected: exit code 0 and no compile errors.

- [ ] **Step 3: Scan the Sprint 4 implementation for prohibited capabilities**

Run:

```powershell
Select-String -Path 'src\ace\domain\conclusion.py','src\ace\engine\conclusion.py','tests\test_evidence_to_conclusion.py' -Pattern 'http://|https://|requests|telemetry|analytics|supabase|postgres|pgvector|neo4j|graphrag|Squadron'
```

Expected: no matches. Inspect any match before changing it. Do not remove
harmless text automatically.

- [ ] **Step 4: Confirm MATE rules were not copied into Sprint 4**

Run:

```powershell
Select-String -Path 'src\ace\domain\conclusion.py','src\ace\engine\conclusion.py' -Pattern 'ControlRating|PARTIALLY_ADEQUATE|failed_dimensions|failure_count'
```

Expected: no matches.

- [ ] **Step 5: Start the unchanged application locally**

Run:

```powershell
$aceServer = Start-Process -FilePath 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','src.ace.app:app','--host','127.0.0.1','--port','8000' -PassThru -WindowStyle Hidden
```

- [ ] **Step 6: Verify the health endpoint**

Run:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/' -Method Get
```

Expected:

```text
system           Assurance Compass Engine
status           ONLINE
audit_engagement Squadron Energy WHS Governance
```

- [ ] **Step 7: Verify the five unchanged fictional evaluations**

Run:

```powershell
$evaluations = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/evaluations' -Method Get
$evaluations.Count
$evaluations | Select-Object control_id,rating
```

Expected:

```text
5
ACE-BESS-001   ADEQUATE
ACE-HV-001     PARTIALLY_ADEQUATE
ACE-ARC-001    INADEQUATE
ACE-SIMOPS-001 PARTIALLY_ADEQUATE
ACE-SOCI-001   INADEQUATE
```

- [ ] **Step 8: Stop the server and confirm port 8000 is closed**

Run:

```powershell
Stop-Process -Id $aceServer.Id
Wait-Process -Id $aceServer.Id -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
```

Expected: no remaining listener.

- [ ] **Step 9: Verify exact Git scope**

Run:

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace status --short --branch
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff 11a38954b6762283d0923382e99560508e770fde -- src/ace/domain/conclusion.py src/ace/engine/conclusion.py src/ace/domain/__init__.py src/ace/engine/__init__.py tests/test_evidence_to_conclusion.py docs/superpowers/plans/2026-07-28-ace-sprint-4-evidence-to-conclusion.md
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff 11a38954b6762283d0923382e99560508e770fde --exit-code -- src/ace/domain/assessment.py src/ace/domain/trace.py src/ace/domain/models.py src/ace/engine/approval.py src/ace/engine/tracing.py src/ace/engine/evaluator.py src/ace/app.py
```

Expected:

- only the approved Sprint 4 domain, engine, exports, test and plan files
  differ;
- every protected implementation file remains unchanged;
- unrelated dirty and untracked files remain untouched.

- [ ] **Step 10: Request independent review**

Read and follow `superpowers:requesting-code-review`.

The reviewer must check:

- the accepted record is gate-only and immutable;
- question and conclusion decisions match exact proposal versions;
- raw, derived and auditor-authored evidence remain distinct;
- derived evidence resolves only to supplied raw evidence;
- missing evidence does not become a negative conclusion;
- substantive outcomes require sufficient current evidence;
- unresolved contradictions and open material gaps block substantive
  outcomes;
- accepted material limitations remain visible;
- `NOT_DETERMINED` retains an explicit limitation;
- effectiveness cannot bypass implementation;
- MATE remains design-only and unchanged;
- no platform, persistence, AI or external capability was added; and
- unrelated work was not touched.

Fix every valid Critical or Important finding through a new failing test,
minimal fix and passing test cycle.

- [ ] **Step 11: Rerun all verification after review changes**

Repeat Steps 1-9 after any review correction. Do not rely on results captured
before the final code change.

- [ ] **Step 12: Report without publishing**

Read and follow `superpowers:verification-before-completion`, then report:

- exact full-suite result;
- source compilation result;
- privacy and MATE-authority scan results;
- both localhost responses;
- server shutdown and closed port;
- independent review outcome;
- exact changed files and commits;
- protected-file confirmation;
- known warning; and
- confirmation that nothing was pushed, deployed, published or sent
  externally.

Do not merge, push, publish, deploy or clean unrelated work.

---

## Completion Checklist

- [ ] One accepted fictional Sprint 3 trace is the starting point.
- [ ] Exactly three audit questions are separately approved.
- [ ] Every question concerns the accepted planning control.
- [ ] Implementation and effectiveness use separate evidence matrices.
- [ ] Every evidence item retains origin, provenance and freshness.
- [ ] Raw evidence has no derived source.
- [ ] Derived evidence resolves directly to supplied raw evidence.
- [ ] Auditor-authored evidence remains explicitly classified.
- [ ] Every matrix entry and gap belongs to the correct question.
- [ ] Every gap remains visible and retains materiality and disposition.
- [ ] Missing evidence is never converted automatically into failure.
- [ ] Substantive conclusions require sufficient current evidence.
- [ ] Unresolved contradictions block substantive conclusions.
- [ ] Open material gaps block substantive conclusions.
- [ ] Accepted material limitations retain an explicit rationale.
- [ ] `NOT_DETERMINED` retains an explicit evidence limitation.
- [ ] Every conclusion decision matches an exact proposal version.
- [ ] Effectiveness does not bypass implementation.
- [ ] The accepted record is complete, gate-only and immutable.
- [ ] MATE remains unchanged and limited to control-design assessment.
- [ ] Existing FastAPI routes and responses remain unchanged.
- [ ] No finding, report, action, CONTRA or risk-reduction claim is added.
- [ ] No database, persistence, retrieval, graph, AI or external service is
  added.
- [ ] The full suite, compilation, privacy scans, endpoints, shutdown and diff
  checks pass.
- [ ] Unrelated work remains untouched.
- [ ] Nothing is pushed or published.
