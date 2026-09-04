# ACE Sprint 3 Connected Assurance Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one fictional, domain-only Connected Assurance planning trace that connects a binding obligation, risk, planning control and accountable job role through auditor-approved relationships to the existing approved MATE assessment and immutable rating.

**Architecture:** Frozen Pydantic records in `src/ace/domain/trace.py` represent the four planning facts, relationship proposals, auditor decisions and accepted trace. A focused service in `src/ace/engine/tracing.py` validates provenance, exact endpoints and relationship approvals, delegates control-design rating to the unchanged Sprint 2 `evaluate_approved_assessment()` workflow, and provides deterministic forward and reverse trace views. No generic graph, persistence, route or external service is added.

**Tech Stack:** Python 3.11+, Pydantic 2, pytest 8, existing FastAPI application, existing local virtual environment.

## Global Constraints

- Work only in `C:\Users\AlanRichardson\Documents\agentic-os-workspace\sqe`.
- Keep execution local and private.
- Use fictional records and source wording only.
- MATE means only Mandate, Accountability, Trigger and Escalation.
- MATE is used only after the obligation, risk, planning control, accountable job role and their planning relationships have been identified and approved.
- MATE assesses the structural adequacy of the identified control's design; it does not map or approve the Connected Assurance relationships.
- The existing evaluator remains the only rating authority.
- Do not change the existing rating precedence.
- Do not add control implementation, operation or effectiveness claims.
- Do not add findings, actions, follow-up or risk-reduction claims.
- Do not add PostgreSQL, Supabase, persistence, full-text search, vector search, pgvector, Neo4j, GraphRAG or a generic graph.
- Do not add a webpage, FastAPI route, external API, AI service, telemetry or analytics.
- Do not expose real audit evidence or a real person's name.
- Keep all accepted records and results immutable.
- Keep decision timestamps in strict canonical UTC.
- Do not change the behaviour of `src/ace/domain/assessment.py`, `src/ace/engine/approval.py`, `src/ace/engine/evaluator.py`, `src/ace/app.py` or their existing tests.
- Do not suppress the existing FastAPI/Starlette TestClient deprecation warning.
- Do not install or update dependencies.
- Do not push, deploy, publish, open a tunnel or contact external services.
- Do not reset, clean, discard, overwrite, stage or commit unrelated work.
- Do not delete `C:\tmp\sqe-ace-sprint-1`.
- Use Australian English in documentation and messages.

---

## Task 1: Add Planning Fact Records

**Files:**

- Create: `src/ace/domain/trace.py`
- Modify: `src/ace/domain/__init__.py`
- Create: `tests/test_planning_trace.py`

**Interfaces:**

- Consumes: `SourceReference` and `SourceStatus` from `src.ace.domain.assessment`.
- Produces: `AccountabilitySubjectType`, `TraceRelationshipType`, `BindingObligationRecord`, `RiskRecord`, `PlanningControlRecord` and `AccountableRoleRecord`.

- [ ] **Step 1: Write failing tests for the controlled vocabulary and four planning facts**

Create `tests/test_planning_trace.py`:

```python
from typing import Any

import pytest
from pydantic import ValidationError

from src.ace.domain.assessment import SourceReference, SourceStatus
from src.ace.domain.trace import (
    AccountabilitySubjectType,
    AccountableRoleRecord,
    BindingObligationRecord,
    PlanningControlRecord,
    RiskRecord,
    TraceRelationshipType,
)


def validated_copy(model: Any, **changes: object) -> Any:
    values = model.model_dump()
    values.update(changes)
    return type(model).model_validate(values)


def make_source(
    source_id: str,
    *,
    status: SourceStatus = SourceStatus.CURRENT,
) -> SourceReference:
    return SourceReference(
        source_id=source_id,
        document_title=f"Fictional document for {source_id}",
        document_version="1.0",
        source_location=f"Section {source_id}",
        source_wording=f"Fictional source wording for {source_id}.",
        status=status,
    )


def make_obligation() -> BindingObligationRecord:
    return BindingObligationRecord(
        obligation_id="OBL-FICTIONAL-001",
        title="Fictional mobilisation obligation",
        binding_instrument="Fictional Safety Management Policy",
        clause="Clause 4.1",
        obligation_text=(
            "A fictional mobilisation control must be approved before work starts."
        ),
        source_reference=make_source("SRC-OBLIGATION"),
    )


def make_risk() -> RiskRecord:
    return RiskRecord(
        risk_id="RISK-FICTIONAL-001",
        title="Fictional uncontrolled mobilisation risk",
        risk_statement=(
            "Work may start without required fictional governance approval."
        ),
        source_reference=make_source("SRC-RISK"),
    )


def make_control() -> PlanningControlRecord:
    return PlanningControlRecord(
        control_id="ACE-FICTIONAL-001",
        title="Fictional mobilisation approval control",
        design_statement=(
            "The fictional accountable role approves mobilisation before work starts."
        ),
        source_reference=make_source("SRC-CONTROL"),
    )


def make_role(
    *,
    subject_type: AccountabilitySubjectType = (
        AccountabilitySubjectType.JOB_ROLE
    ),
) -> AccountableRoleRecord:
    return AccountableRoleRecord(
        accountability_id="ROLE-FICTIONAL-001",
        subject_type=subject_type,
        subject_title=(
            "Fictional Head of Safety"
            if subject_type is AccountabilitySubjectType.JOB_ROLE
            else "Fictional Person A"
        ),
        accountability_statement=(
            "The fictional job role is accountable for the mobilisation control."
        ),
        source_reference=make_source("SRC-ROLE"),
    )


def test_trace_vocabulary_values_are_stable() -> None:
    assert [value.value for value in AccountabilitySubjectType] == [
        "JOB_ROLE",
        "NAMED_PERSON",
    ]
    assert [value.value for value in TraceRelationshipType] == [
        "OBLIGATION_APPLIES_TO_RISK",
        "CONTROL_TREATS_RISK",
        "ROLE_ACCOUNTABLE_FOR_CONTROL",
        "CONTROL_HAS_APPROVED_MATE_ASSESSMENT",
    ]


@pytest.mark.parametrize(
    ("factory", "field_name"),
    [
        (make_obligation, "obligation_id"),
        (make_obligation, "binding_instrument"),
        (make_obligation, "clause"),
        (make_obligation, "obligation_text"),
        (make_risk, "risk_id"),
        (make_risk, "risk_statement"),
        (make_control, "control_id"),
        (make_control, "design_statement"),
        (make_role, "accountability_id"),
        (make_role, "subject_title"),
        (make_role, "accountability_statement"),
    ],
)
def test_planning_facts_reject_blank_required_text(
    factory: Any,
    field_name: str,
) -> None:
    values = factory().model_dump()
    values[field_name] = "   "

    with pytest.raises(ValidationError):
        type(factory()).model_validate(values)


@pytest.mark.parametrize(
    "record",
    [make_obligation(), make_risk(), make_control(), make_role()],
)
def test_planning_facts_are_frozen(record: Any) -> None:
    with pytest.raises(ValidationError):
        record.source_reference = make_source("SRC-CHANGED")


def test_named_person_is_recorded_explicitly_for_gate_review() -> None:
    role = make_role(subject_type=AccountabilitySubjectType.NAMED_PERSON)

    assert role.subject_type is AccountabilitySubjectType.NAMED_PERSON
```

- [ ] **Step 2: Run the focused tests and confirm the missing module failure**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_planning_trace.py -q
```

Expected: collection fails with
`ModuleNotFoundError: No module named 'src.ace.domain.trace'`.

- [ ] **Step 3: Implement the vocabulary and four frozen fact records**

Create `src/ace/domain/trace.py`:

```python
"""Domain records for one fictional Connected Assurance planning trace."""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from .assessment import SourceReference


NonEmptyText = Annotated[str, Field(min_length=1)]
PositiveVersion = Annotated[StrictInt, Field(gt=0)]


class AccountabilitySubjectType(str, Enum):
    """Whether accountability is assigned to a job role or a person."""

    JOB_ROLE = "JOB_ROLE"
    NAMED_PERSON = "NAMED_PERSON"


class TraceRelationshipType(str, Enum):
    """The four authorised relationships in the Sprint 3 planning trace."""

    OBLIGATION_APPLIES_TO_RISK = "OBLIGATION_APPLIES_TO_RISK"
    CONTROL_TREATS_RISK = "CONTROL_TREATS_RISK"
    ROLE_ACCOUNTABLE_FOR_CONTROL = "ROLE_ACCOUNTABLE_FOR_CONTROL"
    CONTROL_HAS_APPROVED_MATE_ASSESSMENT = (
        "CONTROL_HAS_APPROVED_MATE_ASSESSMENT"
    )

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").title()


class BindingObligationRecord(BaseModel):
    """One fictional binding requirement used in audit planning."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    obligation_id: NonEmptyText
    title: NonEmptyText
    binding_instrument: NonEmptyText
    clause: NonEmptyText
    obligation_text: NonEmptyText
    source_reference: SourceReference


class RiskRecord(BaseModel):
    """One fictional risk connected to the planning control."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    risk_id: NonEmptyText
    title: NonEmptyText
    risk_statement: NonEmptyText
    source_reference: SourceReference


class PlanningControlRecord(BaseModel):
    """One fictional control whose design lineage is being traced."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    control_id: NonEmptyText
    title: NonEmptyText
    design_statement: NonEmptyText
    source_reference: SourceReference


class AccountableRoleRecord(BaseModel):
    """The proposed accountability subject for the planning control."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    accountability_id: NonEmptyText
    subject_type: AccountabilitySubjectType
    subject_title: NonEmptyText
    accountability_statement: NonEmptyText
    source_reference: SourceReference
```

Do not validate whether sources are current here. A superseded or uncertain
source remains a valid factual record but is blocked by the trace gate.

- [ ] **Step 4: Export the implemented Sprint 3 fact types**

Add to `src/ace/domain/__init__.py`:

```python
from .trace import (
    AccountabilitySubjectType,
    AccountableRoleRecord,
    BindingObligationRecord,
    PlanningControlRecord,
    RiskRecord,
    TraceRelationshipType,
)
```

Add these names to `__all__` in alphabetical order:

```python
"AccountabilitySubjectType",
"AccountableRoleRecord",
"BindingObligationRecord",
"PlanningControlRecord",
"RiskRecord",
"TraceRelationshipType",
```

- [ ] **Step 5: Run focused and complete tests**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_planning_trace.py -q
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: all tests pass with the one known dependency warning in the complete
suite.

- [ ] **Step 6: Commit Task 1**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add src/ace/domain/trace.py src/ace/domain/__init__.py tests/test_planning_trace.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff --cached --check
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: add Connected Assurance planning facts"
```

---

## Task 2: Add Relationship Proposals And Auditor Decisions

**Files:**

- Modify: `src/ace/domain/trace.py`
- Modify: `src/ace/domain/__init__.py`
- Modify: `tests/test_planning_trace.py`

**Interfaces:**

- Consumes: `TraceRelationshipType` and Sprint 2
  `AuditorDecisionStatus`.
- Produces: `ProposedTraceRelationship` and
  `AuditorRelationshipDecision`.

- [ ] **Step 1: Add failing relationship proposal tests**

Add imports in `tests/test_planning_trace.py`:

```python
from src.ace.domain.trace import (
    AuditorRelationshipDecision,
    ProposedTraceRelationship,
)
```

Add this helper:

```python
def make_relationship(
    relationship_type: TraceRelationshipType,
    *,
    source_record_id: str = "SOURCE-001",
    target_record_id: str = "TARGET-001",
    supporting_source_ids: tuple[str, ...] = ("SRC-OBLIGATION",),
    version: int = 1,
) -> ProposedTraceRelationship:
    return ProposedTraceRelationship(
        relationship_id=f"REL-{relationship_type.value}",
        relationship_version=version,
        relationship_type=relationship_type,
        source_record_id=source_record_id,
        target_record_id=target_record_id,
        supporting_source_ids=supporting_source_ids,
        rationale=f"Fictional rationale for {relationship_type.label}.",
    )
```

Add:

```python
@pytest.mark.parametrize("version", [0, -1, "1"])
def test_relationship_version_must_be_a_positive_strict_integer(
    version: object,
) -> None:
    with pytest.raises(ValidationError):
        make_relationship(
            TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK,
            version=version,
        )


def test_relationship_requires_supporting_sources() -> None:
    with pytest.raises(ValidationError):
        make_relationship(
            TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK,
            supporting_source_ids=(),
        )


def test_relationship_rejects_duplicate_supporting_source_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="supporting source identifiers must be unique",
    ):
        make_relationship(
            TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK,
            supporting_source_ids=("SRC-OBLIGATION", "SRC-OBLIGATION"),
        )


def test_relationship_proposal_is_frozen() -> None:
    relationship = make_relationship(
        TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK
    )

    with pytest.raises(ValidationError):
        relationship.target_record_id = "CHANGED"
```

- [ ] **Step 2: Add failing auditor relationship decision tests**

Add:

```python
from src.ace.domain.assessment import AuditorDecisionStatus
```

Add the helper:

```python
def make_relationship_decision(
    relationship: ProposedTraceRelationship,
    *,
    status: AuditorDecisionStatus = AuditorDecisionStatus.APPROVED,
    version: int | None = None,
) -> AuditorRelationshipDecision:
    return AuditorRelationshipDecision(
        decision_id=f"DEC-{relationship.relationship_type.value}",
        relationship_id=relationship.relationship_id,
        relationship_version=version or relationship.relationship_version,
        relationship_type=relationship.relationship_type,
        decision_status=status,
        reviewer_id="FICTIONAL-AUDITOR-01",
        review_notes=f"Fictional review of {relationship.relationship_type.label}.",
        reviewed_at="2026-07-28T01:02:03.456789+00:00",
    )
```

Add:

```python
@pytest.mark.parametrize(
    "timestamp",
    [
        "not-a-timestamp",
        "2026-07-28T01:02:03.456789",
        "2026-07-28T11:02:03.456789+10:00",
        "2026-07-28 01:02:03.456789+00:00",
        " 2026-07-28T01:02:03.456789+00:00",
        "2026-07-28T01:02:03.456789+00:00 ",
    ],
)
def test_relationship_decision_rejects_noncanonical_utc(
    timestamp: str,
) -> None:
    relationship = make_relationship(
        TraceRelationshipType.CONTROL_TREATS_RISK
    )
    values = make_relationship_decision(relationship).model_dump()
    values["reviewed_at"] = timestamp

    with pytest.raises(ValidationError):
        AuditorRelationshipDecision.model_validate(values)


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-07-28T01:02:03.456789+00:00",
        "2026-07-28T01:02:03.456789Z",
    ],
)
def test_relationship_decision_accepts_canonical_utc(timestamp: str) -> None:
    relationship = make_relationship(
        TraceRelationshipType.CONTROL_TREATS_RISK
    )
    values = make_relationship_decision(relationship).model_dump()
    values["reviewed_at"] = timestamp

    decision = AuditorRelationshipDecision.model_validate(values)

    assert decision.reviewed_at == timestamp


@pytest.mark.parametrize("field_name", ["decision_id", "reviewer_id", "review_notes"])
def test_relationship_decision_rejects_blank_required_text(
    field_name: str,
) -> None:
    relationship = make_relationship(
        TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL
    )
    values = make_relationship_decision(relationship).model_dump()
    values[field_name] = "   "

    with pytest.raises(ValidationError):
        AuditorRelationshipDecision.model_validate(values)


def test_relationship_decision_is_frozen() -> None:
    relationship = make_relationship(
        TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL
    )
    decision = make_relationship_decision(relationship)

    with pytest.raises(ValidationError):
        decision.decision_status = AuditorDecisionStatus.REJECTED
```

- [ ] **Step 3: Run focused tests and confirm the missing record failure**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_planning_trace.py -q
```

Expected: collection fails because `ProposedTraceRelationship` and
`AuditorRelationshipDecision` do not exist.

- [ ] **Step 4: Implement relationship proposals and decisions**

Extend the imports in `src/ace/domain/trace.py`:

```python
from datetime import datetime, timedelta
import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
)

from .assessment import AuditorDecisionStatus, SourceReference
```

Replace the earlier Pydantic and assessment imports, then add:

```python
TRACE_UTC_ISO_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\+00:00|Z)"
)


class ProposedTraceRelationship(BaseModel):
    """One proposed, versioned connection between trace records."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    relationship_id: NonEmptyText
    relationship_version: PositiveVersion
    relationship_type: TraceRelationshipType
    source_record_id: NonEmptyText
    target_record_id: NonEmptyText
    supporting_source_ids: tuple[NonEmptyText, ...] = Field(min_length=1)
    rationale: NonEmptyText

    @field_validator("supporting_source_ids")
    @classmethod
    def validate_supporting_source_ids(
        cls,
        source_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("supporting source identifiers must be unique")
        return source_ids


class AuditorRelationshipDecision(BaseModel):
    """The auditor's immutable decision on one relationship proposal version."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    decision_id: NonEmptyText
    relationship_id: NonEmptyText
    relationship_version: PositiveVersion
    relationship_type: TraceRelationshipType
    decision_status: AuditorDecisionStatus
    reviewer_id: NonEmptyText
    review_notes: NonEmptyText
    reviewed_at: NonEmptyText

    @field_validator("reviewed_at", mode="before")
    @classmethod
    def reject_timestamp_whitespace(cls, reviewed_at: object) -> object:
        if isinstance(reviewed_at, str) and reviewed_at != reviewed_at.strip():
            raise ValueError("review timestamp must not contain surrounding whitespace")
        return reviewed_at

    @field_validator("reviewed_at")
    @classmethod
    def validate_reviewed_at(cls, reviewed_at: str) -> str:
        if TRACE_UTC_ISO_TIMESTAMP.fullmatch(reviewed_at) is None:
            raise ValueError(
                "review timestamp must use canonical UTC ISO 8601 format"
            )

        try:
            parsed_timestamp = datetime.fromisoformat(reviewed_at)
        except ValueError as error:
            raise ValueError("review timestamp must use ISO 8601 format") from error

        utc_offset = parsed_timestamp.utcoffset()
        if utc_offset is None:
            raise ValueError("review timestamp must include a timezone")
        if utc_offset != timedelta(0):
            raise ValueError("review timestamp must use a zero UTC offset")

        return reviewed_at
```

Do not automatically approve a relationship inside either record.

- [ ] **Step 5: Export the relationship types**

Add these imports and `__all__` entries in `src/ace/domain/__init__.py`:

```python
AuditorRelationshipDecision,
ProposedTraceRelationship,
```

- [ ] **Step 6: Run focused and complete tests**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_planning_trace.py -q
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: all tests pass with the known warning visible in the complete suite.

- [ ] **Step 7: Commit Task 2**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add src/ace/domain/trace.py src/ace/domain/__init__.py tests/test_planning_trace.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff --cached --check
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: add trace relationship decisions"
```

---

## Task 3: Build The Trace Approval Gate

**Files:**

- Modify: `src/ace/domain/trace.py`
- Modify: `src/ace/domain/__init__.py`
- Create: `src/ace/engine/tracing.py`
- Modify: `src/ace/engine/__init__.py`
- Modify: `tests/test_planning_trace.py`

**Interfaces:**

- Consumes: the four planning facts, four `ProposedTraceRelationship`
  records, four `AuditorRelationshipDecision` records and one existing
  `ApprovedMATEAssessment`.
- Produces:
  `build_accepted_planning_trace(...) -> AcceptedPlanningTrace`.
- Raises: `TraceApprovalBlockedError`.

- [ ] **Step 1: Add a real fictional approved MATE fixture**

Add these imports to `tests/test_planning_trace.py`:

```python
from src.ace.domain.assessment import (
    ApprovedMATEAssessment,
    AuditorDecision,
    ContradictionStatus,
    EvidenceAvailability,
    EvidenceReviewRecord,
    EvidenceSufficiency,
    MateDimension,
    ProposedAnswer,
    ProposedDimensionAssessment,
)
from src.ace.domain.enums import ControlRating, HazardCategory
from src.ace.domain.models import AssuranceDimensions
from src.ace.engine.approval import build_approved_assessment
```

Add:

```python
def make_mate_assessment(
    answers: dict[MateDimension, ProposedAnswer] | None = None,
) -> ApprovedMATEAssessment:
    selected_answers = answers or {}
    proposals = []
    reviews = []
    decisions = []

    for dimension in MateDimension:
        answer = selected_answers.get(dimension, ProposedAnswer.YES)
        approved_answer = answer is ProposedAnswer.YES
        source = make_source(f"SRC-MATE-{dimension.value}")
        review = EvidenceReviewRecord(
            review_id=f"REV-MATE-{dimension.value}",
            source_references=(source,),
            supporting_source_ids=(source.source_id,),
            weakening_source_ids=(),
            contradictory_source_ids=(),
            evidence_availability=(EvidenceAvailability.REVIEWED_SUPPORTIVE,),
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
            proposed_answer=answer,
            rationale=f"Fictional MATE rationale for {dimension.label}.",
            evidence_review_id=review.review_id,
        )
        decision = AuditorDecision(
            decision_id=f"DEC-MATE-{dimension.value}",
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.proposal_version,
            dimension=dimension,
            decision_status=AuditorDecisionStatus.APPROVED,
            approved_answer=approved_answer,
            final_sufficiency=(
                EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
            ),
            reviewer_id="FICTIONAL-MATE-AUDITOR",
            review_notes=f"Fictional approval for {dimension.label}.",
            reviewed_at="2026-07-28T01:02:03.456789+00:00",
        )
        reviews.append(review)
        proposals.append(proposal)
        decisions.append(decision)

    return build_approved_assessment(
        control_id="ACE-FICTIONAL-001",
        title="Fictional mobilisation approval control",
        description="Fictional control-design assessment for Sprint 3.",
        hazard_category=HazardCategory.GOVERNANCE_OVERSIGHT,
        proposals=tuple(proposals),
        evidence_reviews=tuple(reviews),
        decisions=tuple(decisions),
        reviewer_notes="Fictional Sprint 3 MATE assessment.",
    )
```

- [ ] **Step 2: Add complete relationship and decision bundle helpers**

Add:

```python
def make_relationship_bundle(
    obligation: BindingObligationRecord,
    risk: RiskRecord,
    control: PlanningControlRecord,
    role: AccountableRoleRecord,
    mate_assessment: ApprovedMATEAssessment,
) -> tuple[
    tuple[ProposedTraceRelationship, ...],
    tuple[AuditorRelationshipDecision, ...],
]:
    relationships = (
        make_relationship(
            TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK,
            source_record_id=obligation.obligation_id,
            target_record_id=risk.risk_id,
            supporting_source_ids=(
                obligation.source_reference.source_id,
                risk.source_reference.source_id,
            ),
        ),
        make_relationship(
            TraceRelationshipType.CONTROL_TREATS_RISK,
            source_record_id=control.control_id,
            target_record_id=risk.risk_id,
            supporting_source_ids=(
                control.source_reference.source_id,
                risk.source_reference.source_id,
            ),
        ),
        make_relationship(
            TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL,
            source_record_id=role.accountability_id,
            target_record_id=control.control_id,
            supporting_source_ids=(
                role.source_reference.source_id,
                control.source_reference.source_id,
            ),
        ),
        make_relationship(
            TraceRelationshipType.CONTROL_HAS_APPROVED_MATE_ASSESSMENT,
            source_record_id=control.control_id,
            target_record_id=f"MATE:{mate_assessment.control_id}",
            supporting_source_ids=(control.source_reference.source_id,),
        ),
    )
    decisions = tuple(
        make_relationship_decision(relationship)
        for relationship in relationships
    )
    return relationships, decisions
```

- [ ] **Step 3: Add failing success-path and immutability tests**

Add imports:

```python
from src.ace.domain.trace import AcceptedPlanningTrace
from src.ace.engine.tracing import (
    TraceApprovalBlockedError,
    build_accepted_planning_trace,
)
```

Add:

```python
def build_trace(
    *,
    obligation: BindingObligationRecord | None = None,
    risk: RiskRecord | None = None,
    control: PlanningControlRecord | None = None,
    role: AccountableRoleRecord | None = None,
    mate_assessment: ApprovedMATEAssessment | None = None,
    relationships: tuple[ProposedTraceRelationship, ...] | None = None,
    decisions: tuple[AuditorRelationshipDecision, ...] | None = None,
) -> AcceptedPlanningTrace:
    selected_obligation = obligation or make_obligation()
    selected_risk = risk or make_risk()
    selected_control = control or make_control()
    selected_role = role or make_role()
    selected_mate = mate_assessment or make_mate_assessment()
    default_relationships, default_decisions = make_relationship_bundle(
        selected_obligation,
        selected_risk,
        selected_control,
        selected_role,
        selected_mate,
    )
    return build_accepted_planning_trace(
        obligation=selected_obligation,
        risk=selected_risk,
        control=selected_control,
        accountable_role=selected_role,
        relationships=relationships or default_relationships,
        decisions=decisions or default_decisions,
        mate_assessment=selected_mate,
    )


def test_gate_builds_one_complete_accepted_trace() -> None:
    trace = build_trace()

    assert trace.obligation.obligation_id == "OBL-FICTIONAL-001"
    assert trace.risk.risk_id == "RISK-FICTIONAL-001"
    assert trace.control.control_id == "ACE-FICTIONAL-001"
    assert trace.accountable_role.subject_title == "Fictional Head of Safety"
    assert len(trace.relationships) == 4
    assert len(trace.decisions) == 4
    assert trace.decision_ids == tuple(
        decision.decision_id for decision in trace.decisions
    )
    assert trace.evaluation_result.rating is ControlRating.ADEQUATE


def test_accepted_trace_is_frozen() -> None:
    trace = build_trace()

    with pytest.raises(ValidationError):
        trace.control = make_control()
```

- [ ] **Step 4: Add failing gate safety tests**

Add:

```python
def test_gate_blocks_a_named_person() -> None:
    with pytest.raises(
        TraceApprovalBlockedError,
        match="accountability subject must be a job role",
    ):
        build_trace(
            role=make_role(
                subject_type=AccountabilitySubjectType.NAMED_PERSON
            )
        )


@pytest.mark.parametrize(
    "status",
    [SourceStatus.SUPERSEDED, SourceStatus.UNCERTAIN],
)
def test_gate_blocks_a_noncurrent_planning_source(
    status: SourceStatus,
) -> None:
    obligation = make_obligation()
    stale_source = validated_copy(obligation.source_reference, status=status)
    obligation = validated_copy(obligation, source_reference=stale_source)

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Binding Obligation source is not current",
    ):
        build_trace(obligation=obligation)


def test_gate_blocks_a_missing_relationship_type() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Control Has Approved Mate Assessment relationship is missing",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships[:-1],
            decisions=decisions[:-1],
        )


def test_gate_blocks_a_duplicate_relationship_type() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Obligation Applies To Risk relationship appears more than once",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships + (relationships[0],),
            decisions=decisions + (decisions[0],),
        )


def test_gate_blocks_the_wrong_relationship_endpoint() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    wrong = validated_copy(
        relationships[1],
        target_record_id=obligation.obligation_id,
    )
    relationships = (relationships[0], wrong, *relationships[2:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Control Treats Risk endpoints do not match",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_a_source_from_an_unrelated_endpoint() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    wrong = validated_copy(
        relationships[0],
        supporting_source_ids=(role.source_reference.source_id,),
    )
    relationships = (wrong, *relationships[1:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Obligation Applies To Risk uses a source outside its endpoints",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (AuditorDecisionStatus.REJECTED, "has been rejected"),
        (AuditorDecisionStatus.CHANGES_REQUIRED, "requires changes"),
    ],
)
def test_gate_blocks_a_nonapproved_relationship(
    status: AuditorDecisionStatus,
    message: str,
) -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    rejected = validated_copy(decisions[0], decision_status=status)
    decisions = (rejected, *decisions[1:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match=f"Obligation Applies To Risk {message}",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_a_decision_for_the_wrong_version() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    wrong = validated_copy(decisions[0], relationship_version=2)
    decisions = (wrong, *decisions[1:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match="decision relationship version does not match",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_a_control_that_differs_from_mate() -> None:
    control = validated_copy(make_control(), control_id="ACE-DIFFERENT-001")

    with pytest.raises(
        TraceApprovalBlockedError,
        match="does not match the approved MATE assessment",
    ):
        build_trace(control=control)


def test_gate_blocks_a_mate_assessment_with_an_unapproved_decision() -> None:
    mate = make_mate_assessment()
    rejected = validated_copy(
        mate.decisions[0],
        decision_status=AuditorDecisionStatus.REJECTED,
        approved_answer=None,
    )
    mate = validated_copy(
        mate,
        decisions=(rejected, *mate.decisions[1:]),
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="approved MATE assessment is not fully approved",
    ):
        build_trace(mate_assessment=mate)


def test_gate_blocks_mate_dimensions_that_disagree_with_decisions() -> None:
    mate = make_mate_assessment()
    mate = validated_copy(
        mate,
        dimensions=AssuranceDimensions(
            mandate=False,
            accountability=True,
            trigger=True,
            escalation=True,
        ),
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="approved MATE assessment is internally inconsistent",
    ):
        build_trace(mate_assessment=mate)
```

- [ ] **Step 5: Run focused tests and confirm the missing gate failure**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_planning_trace.py -q
```

Expected: collection fails because `AcceptedPlanningTrace` or
`src.ace.engine.tracing` does not exist.

- [ ] **Step 6: Add the frozen accepted trace record**

Add imports in `src/ace/domain/trace.py`:

```python
from .assessment import (
    ApprovedMATEAssessment,
    AuditorDecisionStatus,
    SourceReference,
)
from .models import EvaluationResult
```

Replace the earlier assessment import, then add:

```python
class AcceptedPlanningTrace(BaseModel):
    """One complete auditor-approved Connected Assurance planning trace."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    obligation: BindingObligationRecord
    risk: RiskRecord
    control: PlanningControlRecord
    accountable_role: AccountableRoleRecord
    relationships: tuple[ProposedTraceRelationship, ...] = Field(
        min_length=4,
        max_length=4,
    )
    decisions: tuple[AuditorRelationshipDecision, ...] = Field(
        min_length=4,
        max_length=4,
    )
    decision_ids: tuple[NonEmptyText, ...] = Field(min_length=4, max_length=4)
    mate_assessment: ApprovedMATEAssessment
    evaluation_result: EvaluationResult
```

Export `AcceptedPlanningTrace` from `src/ace/domain/__init__.py`.

- [ ] **Step 7: Implement the trace approval gate**

Create `src/ace/engine/tracing.py`:

```python
"""Approval gate for one fictional Connected Assurance planning trace."""

from collections.abc import Sequence
from typing import TypeVar

from src.ace.domain.assessment import (
    ApprovedMATEAssessment,
    AuditorDecisionStatus,
    MateDimension,
    SourceReference,
    SourceStatus,
)
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
from src.ace.engine.approval import evaluate_approved_assessment


class TraceApprovalBlockedError(ValueError):
    """Raised when planning records do not form an approved trace."""


RecordT = TypeVar("RecordT")
RELATIONSHIP_ORDER = tuple(TraceRelationshipType)


def _one_for_type(
    records: Sequence[RecordT],
    relationship_type: TraceRelationshipType,
    record_name: str,
) -> RecordT:
    matches = [
        record
        for record in records
        if getattr(record, "relationship_type", None) is relationship_type
    ]
    if not matches:
        raise TraceApprovalBlockedError(
            f"Trace blocked: {relationship_type.label} {record_name} is missing."
        )
    if len(matches) > 1:
        raise TraceApprovalBlockedError(
            f"Trace blocked: {relationship_type.label} {record_name} "
            "appears more than once."
        )
    return matches[0]


def _validate_unique_identifiers(
    *,
    fact_ids: tuple[str, ...],
    sources: tuple[SourceReference, ...],
    relationships: Sequence[ProposedTraceRelationship],
    decisions: Sequence[AuditorRelationshipDecision],
) -> None:
    if len(fact_ids) != len(set(fact_ids)):
        raise TraceApprovalBlockedError(
            "Trace blocked: planning identifiers must be unique."
        )

    source_ids = tuple(source.source_id for source in sources)
    if len(source_ids) != len(set(source_ids)):
        raise TraceApprovalBlockedError(
            "Trace blocked: planning source identifiers must be unique."
        )

    relationship_identities: set[tuple[str, int]] = set()
    for relationship in relationships:
        identity = (
            relationship.relationship_id,
            relationship.relationship_version,
        )
        if identity in relationship_identities:
            raise TraceApprovalBlockedError(
                f"Trace blocked: relationship {relationship.relationship_id} "
                f"version {relationship.relationship_version} appears more "
                "than once."
            )
        relationship_identities.add(identity)

    decision_ids: set[str] = set()
    for decision in decisions:
        if decision.decision_id in decision_ids:
            raise TraceApprovalBlockedError(
                f"Trace blocked: decision {decision.decision_id} appears more "
                "than once."
            )
        decision_ids.add(decision.decision_id)


def _validate_mate_assessment(
    mate_assessment: ApprovedMATEAssessment,
) -> None:
    for dimension in MateDimension:
        matches = [
            decision
            for decision in mate_assessment.decisions
            if decision.dimension is dimension
        ]
        if len(matches) != 1:
            raise TraceApprovalBlockedError(
                "Trace blocked: approved MATE assessment is not fully approved."
            )

        decision = matches[0]
        if decision.decision_status is not AuditorDecisionStatus.APPROVED:
            raise TraceApprovalBlockedError(
                "Trace blocked: approved MATE assessment is not fully approved."
            )
        if decision.approved_answer is not getattr(
            mate_assessment.dimensions,
            dimension.field_name,
        ):
            raise TraceApprovalBlockedError(
                "Trace blocked: approved MATE assessment is internally "
                "inconsistent."
            )


def build_accepted_planning_trace(
    *,
    obligation: BindingObligationRecord,
    risk: RiskRecord,
    control: PlanningControlRecord,
    accountable_role: AccountableRoleRecord,
    relationships: Sequence[ProposedTraceRelationship],
    decisions: Sequence[AuditorRelationshipDecision],
    mate_assessment: ApprovedMATEAssessment,
) -> AcceptedPlanningTrace:
    """Validate and build one complete, approved planning trace."""

    for relationship_type in RELATIONSHIP_ORDER:
        _one_for_type(relationships, relationship_type, "relationship")
        _one_for_type(decisions, relationship_type, "decision")

    fact_sources = (
        ("Binding Obligation", obligation.source_reference),
        ("Risk", risk.source_reference),
        ("Planning Control", control.source_reference),
        ("Accountable Role", accountable_role.source_reference),
    )
    for label, source in fact_sources:
        if source.status is not SourceStatus.CURRENT:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {label} source is not current."
            )

    if accountable_role.subject_type is not AccountabilitySubjectType.JOB_ROLE:
        raise TraceApprovalBlockedError(
            "Trace blocked: accountability subject must be a job role."
        )

    if control.control_id != mate_assessment.control_id:
        raise TraceApprovalBlockedError(
            f"Trace blocked: planning control {control.control_id} does not "
            "match the approved MATE assessment."
        )

    _validate_mate_assessment(mate_assessment)

    sources = tuple(source for _, source in fact_sources)
    _validate_unique_identifiers(
        fact_ids=(
            obligation.obligation_id,
            risk.risk_id,
            control.control_id,
            accountable_role.accountability_id,
        ),
        sources=sources,
        relationships=relationships,
        decisions=decisions,
    )

    mate_endpoint = f"MATE:{mate_assessment.control_id}"
    expected_endpoints = {
        TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK: (
            obligation.obligation_id,
            risk.risk_id,
        ),
        TraceRelationshipType.CONTROL_TREATS_RISK: (
            control.control_id,
            risk.risk_id,
        ),
        TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL: (
            accountable_role.accountability_id,
            control.control_id,
        ),
        TraceRelationshipType.CONTROL_HAS_APPROVED_MATE_ASSESSMENT: (
            control.control_id,
            mate_endpoint,
        ),
    }
    allowed_sources = {
        TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK: {
            obligation.source_reference.source_id,
            risk.source_reference.source_id,
        },
        TraceRelationshipType.CONTROL_TREATS_RISK: {
            control.source_reference.source_id,
            risk.source_reference.source_id,
        },
        TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL: {
            accountable_role.source_reference.source_id,
            control.source_reference.source_id,
        },
        TraceRelationshipType.CONTROL_HAS_APPROVED_MATE_ASSESSMENT: {
            control.source_reference.source_id,
        },
    }

    ordered_relationships = []
    ordered_decisions = []
    for relationship_type in RELATIONSHIP_ORDER:
        relationship = _one_for_type(
            relationships,
            relationship_type,
            "relationship",
        )
        decision = _one_for_type(decisions, relationship_type, "decision")
        expected_source, expected_target = expected_endpoints[relationship_type]

        if (
            relationship.source_record_id != expected_source
            or relationship.target_record_id != expected_target
        ):
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} endpoints do not "
                "match the required records."
            )

        if not set(relationship.supporting_source_ids).issubset(
            allowed_sources[relationship_type]
        ):
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} uses a source "
                "outside its endpoints."
            )

        if decision.relationship_id != relationship.relationship_id:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} decision "
                "relationship identifier does not match."
            )
        if decision.relationship_version != relationship.relationship_version:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} decision "
                "relationship version does not match."
            )
        if decision.relationship_type is not relationship.relationship_type:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} decision type "
                "does not match."
            )

        if decision.decision_status is AuditorDecisionStatus.REJECTED:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} has been rejected."
            )
        if decision.decision_status is AuditorDecisionStatus.CHANGES_REQUIRED:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} requires changes."
            )
        if decision.decision_status is not AuditorDecisionStatus.APPROVED:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} has not been "
                "approved."
            )

        ordered_relationships.append(relationship)
        ordered_decisions.append(decision)

    evaluation_result = evaluate_approved_assessment(mate_assessment)
    if evaluation_result.control_id != control.control_id:
        raise TraceApprovalBlockedError(
            "Trace blocked: evaluation result refers to a different control."
        )

    return AcceptedPlanningTrace(
        obligation=obligation,
        risk=risk,
        control=control,
        accountable_role=accountable_role,
        relationships=tuple(ordered_relationships),
        decisions=tuple(ordered_decisions),
        decision_ids=tuple(
            decision.decision_id for decision in ordered_decisions
        ),
        mate_assessment=mate_assessment,
        evaluation_result=evaluation_result,
    )
```

Do not import `ControlRating` or reproduce rating precedence in this module.

- [ ] **Step 8: Export the implemented trace gate**

Add to `src/ace/engine/__init__.py`:

```python
from .tracing import (
    TraceApprovalBlockedError,
    build_accepted_planning_trace,
)
```

Add to `__all__`:

```python
"TraceApprovalBlockedError",
"build_accepted_planning_trace",
```

- [ ] **Step 9: Run focused and complete tests**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_planning_trace.py -q
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: all tests pass with the known warning visible.

- [ ] **Step 10: Commit Task 3**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add src/ace/domain/trace.py src/ace/domain/__init__.py src/ace/engine/tracing.py src/ace/engine/__init__.py tests/test_planning_trace.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff --cached --check
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: approve one Connected Assurance trace"
```

---

## Task 4: Add Deterministic Forward And Reverse Trace Views

**Files:**

- Modify: `src/ace/engine/tracing.py`
- Modify: `src/ace/engine/__init__.py`
- Modify: `tests/test_planning_trace.py`

**Interfaces:**

- Consumes: `AcceptedPlanningTrace`.
- Produces:
  `forward_trace_references(trace) -> tuple[str, ...]` and
  `reverse_trace_references(trace) -> tuple[str, ...]`.

- [ ] **Step 1: Add failing forward and reverse trace tests**

Add imports:

```python
from src.ace.engine.tracing import (
    forward_trace_references,
    reverse_trace_references,
)
```

Add:

```python
def test_forward_trace_order_is_deterministic() -> None:
    trace = build_trace()

    assert forward_trace_references(trace) == (
        "OBLIGATION:OBL-FICTIONAL-001",
        "RISK:RISK-FICTIONAL-001",
        "CONTROL:ACE-FICTIONAL-001",
        "ROLE:ROLE-FICTIONAL-001",
        "MATE:ACE-FICTIONAL-001",
        "RATING:ADEQUATE",
    )


def test_reverse_trace_is_the_exact_reverse_view() -> None:
    trace = build_trace()

    assert reverse_trace_references(trace) == (
        "RATING:ADEQUATE",
        "MATE:ACE-FICTIONAL-001",
        "ROLE:ROLE-FICTIONAL-001",
        "CONTROL:ACE-FICTIONAL-001",
        "RISK:RISK-FICTIONAL-001",
        "OBLIGATION:OBL-FICTIONAL-001",
    )


def test_trace_retains_existing_inadequate_precedence() -> None:
    mate = make_mate_assessment(
        {
            MateDimension.TRIGGER: ProposedAnswer.NO,
            MateDimension.ESCALATION: ProposedAnswer.NO,
        }
    )

    trace = build_trace(mate_assessment=mate)

    assert trace.evaluation_result.rating is ControlRating.INADEQUATE
    assert forward_trace_references(trace)[-1] == "RATING:INADEQUATE"
```

- [ ] **Step 2: Run the three tests and confirm missing function failures**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_planning_trace.py::test_forward_trace_order_is_deterministic tests/test_planning_trace.py::test_reverse_trace_is_the_exact_reverse_view tests/test_planning_trace.py::test_trace_retains_existing_inadequate_precedence -q
```

Expected: collection fails because the view functions do not exist.

- [ ] **Step 3: Implement deterministic trace views**

Add to `src/ace/engine/tracing.py`:

```python
def forward_trace_references(
    trace: AcceptedPlanningTrace,
) -> tuple[str, ...]:
    """Return the stable planning trace from obligation to rating."""

    return (
        f"OBLIGATION:{trace.obligation.obligation_id}",
        f"RISK:{trace.risk.risk_id}",
        f"CONTROL:{trace.control.control_id}",
        f"ROLE:{trace.accountable_role.accountability_id}",
        f"MATE:{trace.mate_assessment.control_id}",
        f"RATING:{trace.evaluation_result.rating.value}",
    )


def reverse_trace_references(
    trace: AcceptedPlanningTrace,
) -> tuple[str, ...]:
    """Return the same stable trace from rating to obligation."""

    return tuple(reversed(forward_trace_references(trace)))
```

These functions expose a controlled view, not generic graph traversal.

- [ ] **Step 4: Export both trace view functions**

Add to the tracing import and `__all__` in `src/ace/engine/__init__.py`:

```python
forward_trace_references,
reverse_trace_references,
```

- [ ] **Step 5: Confirm there is no second rating implementation**

Run:

```powershell
Select-String -LiteralPath 'src\ace\engine\tracing.py' -Pattern 'ControlRating|PARTIALLY_ADEQUATE|failure_count'
```

Expected: no matches.

- [ ] **Step 6: Run focused and complete tests**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_planning_trace.py -q
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: all tests pass with the one known warning visible.

- [ ] **Step 7: Commit Task 4**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add src/ace/engine/tracing.py src/ace/engine/__init__.py tests/test_planning_trace.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff --cached --check
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: add deterministic assurance trace views"
```

---

## Task 5: Complete Regression, Privacy And Runtime Verification

**Files:**

- Verify only: `src/ace/domain/trace.py`
- Verify only: `src/ace/engine/tracing.py`
- Verify only: `src/ace/domain/__init__.py`
- Verify only: `src/ace/engine/__init__.py`
- Verify only: `tests/test_planning_trace.py`
- Verify unchanged: `src/ace/domain/assessment.py`
- Verify unchanged: `src/ace/engine/approval.py`
- Verify unchanged: `src/ace/engine/evaluator.py`
- Verify unchanged: `src/ace/app.py`
- Verify unchanged: `tests/test_approval_gate.py`
- Verify unchanged: `tests/test_rating_engine.py`
- Verify unchanged: `tests/test_app.py`

**Interfaces:**

- Consumes: the complete Sprint 3 implementation.
- Produces: fresh completion evidence only; no new functionality.

- [ ] **Step 1: Run the complete test suite**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: the complete suite passes. Record the exact pass count rather than
predicting it. The one known FastAPI/Starlette warning remains visible.

- [ ] **Step 2: Compile all source**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m compileall -q src
```

Expected: exit code 0 and no compile errors.

- [ ] **Step 3: Scan only the Sprint 3 files for prohibited capabilities**

Run:

```powershell
Select-String -Path 'src\ace\domain\trace.py','src\ace\engine\tracing.py','tests\test_planning_trace.py' -Pattern 'http://|https://|requests|telemetry|analytics|supabase|postgres|pgvector|neo4j|graphrag|Squadron'
```

Expected: no matches. Inspect any match before changing it. Do not remove
harmless text automatically.

- [ ] **Step 4: Confirm the trace service contains no rating rules**

Run:

```powershell
Select-String -LiteralPath 'src\ace\engine\tracing.py' -Pattern 'ControlRating|PARTIALLY_ADEQUATE|failure_count'
```

Expected: no matches.

- [ ] **Step 5: Start the existing application locally**

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

- [ ] **Step 7: Verify the five unchanged evaluation results**

Run:

```powershell
$evaluations = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/evaluations' -Method Get
$evaluations.Count
$evaluations | Select-Object control_id,rating
```

Expected:

```text
ACE-BESS-001   ADEQUATE
ACE-HV-001     PARTIALLY_ADEQUATE
ACE-ARC-001    INADEQUATE
ACE-SIMOPS-001 PARTIALLY_ADEQUATE
ACE-SOCI-001   INADEQUATE
```

- [ ] **Step 8: Stop the server and prove port 8000 is closed**

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
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff 2cab623 -- src/ace/domain/trace.py src/ace/domain/__init__.py src/ace/engine/tracing.py src/ace/engine/__init__.py tests/test_planning_trace.py docs/superpowers/plans/2026-07-28-ace-sprint-3-connected-assurance-trace.md
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff 2cab623 --exit-code -- src/ace/domain/assessment.py src/ace/engine/approval.py src/ace/engine/evaluator.py src/ace/app.py tests/test_approval_gate.py tests/test_rating_engine.py tests/test_app.py
```

Expected:

- only the approved Sprint 3 domain, engine, exports, tests and plan differ;
- the protected Sprint 1 and Sprint 2 files are unchanged;
- unrelated dirty and untracked files remain untouched.

- [ ] **Step 10: Apply independent review and completion verification**

Read and follow:

- `superpowers:requesting-code-review`; and
- `superpowers:verification-before-completion`.

Fix every valid Critical or Important finding through a new red-green test
cycle. Rerun all verification after any change.

- [ ] **Step 11: Report without publishing**

Report:

- the exact test result;
- compilation result;
- privacy and rating-authority scan results;
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

## Final-Review Hardening Corrections

This section is a governing correction to the implementation steps above. It
overrides the shortened Task 4 view and its mechanical reverse implementation
where they conflict with the approved design.

### Controlled Accepted-Trace Construction

`AcceptedPlanningTrace` may be constructed only by
`build_accepted_planning_trace()`. Ordinary direct construction and
`model_validate()` calls must fail without the private Pydantic validation
context supplied by the trace gate's private construction method. The domain
model must not duplicate the gate's relationship, decision, source or MATE
validation. This is an application workflow control, not an authentication or
hostile-code security boundary.

### MATE Decision Identity

`_validate_mate_assessment()` must reject a reused MATE `decision_id` in
addition to requiring exactly one approved, answer-consistent decision for
each of Mandate, Accountability, Trigger and Escalation.

### Exact Forward Output

Every approved relationship reference uses this stable token:

```text
APPROVED_RELATIONSHIP:<relationship_type.value>:<relationship_id>:v<relationship_version>:DECISION:<decision_id>
```

`forward_trace_references()` returns exactly:

```text
OBLIGATION:<obligation_id>
APPROVED_RELATIONSHIP:OBLIGATION_APPLIES_TO_RISK:<relationship_id>:v<relationship_version>:DECISION:<decision_id>
RISK:<risk_id>
APPROVED_RELATIONSHIP:CONTROL_TREATS_RISK:<relationship_id>:v<relationship_version>:DECISION:<decision_id>
CONTROL:<control_id>
APPROVED_RELATIONSHIP:ROLE_ACCOUNTABLE_FOR_CONTROL:<relationship_id>:v<relationship_version>:DECISION:<decision_id>
ROLE:<accountability_id>
APPROVED_RELATIONSHIP:CONTROL_HAS_APPROVED_MATE_ASSESSMENT:<relationship_id>:v<relationship_version>:DECISION:<decision_id>
MATE:<control_id>
RATING:<rating.value>
```

### Exact Reverse Output

The reverse follow-up remains the design's facts-and-results-only view. It is
implemented explicitly and is not a reversal of the expanded forward tuple:

```text
RATING:<rating.value>
MATE:<control_id>
ROLE:<accountability_id>
CONTROL:<control_id>
RISK:<risk_id>
OBLIGATION:<obligation_id>
```

### Final-Review Regression Coverage

Focused tests must cover duplicate planning fact and source identifiers,
duplicate relationship identities and decision identifiers, relationship
decision identifier and type mismatches, the derived MATE endpoint, blocked
empty relationship and decision collections, blocked direct accepted-record
construction, duplicate MATE decision identifiers, and evaluator-result
retention. A literal 16-case Boolean matrix must pass through the trace gate
and retain the existing Sprint 1 ratings: no failures is `ADEQUATE`; exactly
one failed Trigger or Escalation is `PARTIALLY_ADEQUATE`; every other
combination is `INADEQUATE`. Rating precedence remains solely in the existing
evaluator.

---

## Completion Checklist

- [ ] One binding obligation, risk, planning control and accountable job role
      form the accepted trace.
- [ ] Each planning fact has one precise current fictional source.
- [ ] Exactly four authorised relationship types appear.
- [ ] Every relationship has a unique versioned proposal and matching auditor
      decision.
- [ ] Every accepted decision is approved.
- [ ] Named-person accountability is blocked.
- [ ] Incorrect endpoints and unrelated sources are blocked.
- [ ] The planning control matches the approved MATE assessment.
- [ ] MATE is used after relationship approval and only for control-design
      assessment.
- [ ] The existing evaluator remains the sole rating authority.
- [ ] Forward and reverse trace views are deterministic.
- [ ] The trace makes no implementation, effectiveness, risk-reduction,
      finding or action claim.
- [ ] Accepted records and results are immutable.
- [ ] Existing FastAPI routes and response bodies remain unchanged.
- [ ] No database, generic graph, vector system, external service, AI or
      telemetry is added.
- [ ] All tests, compilation, privacy, endpoint, shutdown and diff checks pass.
- [ ] Unrelated work remains untouched.
- [ ] Nothing is pushed or published.
