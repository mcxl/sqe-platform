# ACE Sprint 2 Controlled Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fictional, domain-only approval boundary that traces each proposed MATE answer to reviewed evidence and an auditor decision before the existing deterministic evaluator is called.

**Architecture:** Frozen Pydantic records in `src/ace/domain/assessment.py` hold fictional sources, proposals, evidence reviews, auditor decisions and the resulting approved assessment. A focused service in `src/ace/engine/approval.py` checks that all four MATE dimensions are complete, current, sufficient and approved, converts only approved `YES` or `NO` answers to `AssuranceDimensions`, and delegates rating to the unchanged `evaluate_control()` function. No route, database, retrieval system, external service or rating rule is added.

**Tech Stack:** Python 3.11+, Pydantic 2, pytest 8, existing FastAPI application, existing local virtual environment.

## Global Constraints

- Work only in `C:\Users\AlanRichardson\Documents\agentic-os-workspace\sqe`.
- Keep all execution local and private.
- Use fictional source material only.
- Do not add telemetry, analytics, network clients or external API calls.
- Do not add persistence, PostgreSQL, Supabase, vector search, GraphRAG or a user interface.
- Do not change `src/ace/engine/evaluator.py`, `src/ace/app.py`, `tests/test_rating_engine.py` or `tests/test_app.py`.
- MATE means only Mandate, Accountability, Trigger and Escalation.
- The existing evaluator remains the only rating authority.
- `INADEQUATE` continues to take precedence when two or more dimensions fail.
- Existing evaluation results remain immutable.
- New auditor decision timestamps must use the same strict canonical UTC rule as existing evaluation timestamps.
- Do not suppress the existing FastAPI/Starlette TestClient deprecation warning.
- Do not install or update dependencies.
- Do not push, deploy, publish, open a tunnel or contact external services.
- Do not reset, clean, discard, overwrite, stage or commit unrelated work.
- Do not delete `C:\tmp\sqe-ace-sprint-1`.
- Use Australian English in documentation and messages.

---

## Task 1: Add The Controlled Vocabulary And Basic Frozen Records

**Files:**

- Create: `src/ace/domain/assessment.py`
- Modify: `src/ace/domain/__init__.py`
- Create: `tests/test_approval_gate.py`

- [ ] **Step 1: Add failing tests for the controlled vocabulary, source references and proposals**

Create `tests/test_approval_gate.py` with:

```python
from typing import Any

import pytest
from pydantic import ValidationError

from src.ace.domain.assessment import (
    AuditorDecisionStatus,
    ContradictionStatus,
    EvidenceAvailability,
    EvidenceSufficiency,
    MateDimension,
    ProposedAnswer,
    ProposedDimensionAssessment,
    SourceReference,
    SourceStatus,
)


def validated_copy(model: Any, **changes: object) -> Any:
    values = model.model_dump()
    values.update(changes)
    return type(model).model_validate(values)


def make_source(
    dimension: MateDimension,
    *,
    status: SourceStatus = SourceStatus.CURRENT,
) -> SourceReference:
    return SourceReference(
        source_id=f"SRC-{dimension.value}",
        document_title=f"Fictional {dimension.value.title()} Procedure",
        document_version="1.0",
        source_location=f"Section {dimension.value.title()}-1",
        source_wording=(
            f"Fictional wording relevant to the {dimension.value.title()} check."
        ),
        status=status,
    )


def make_proposal(
    dimension: MateDimension,
    *,
    answer: ProposedAnswer = ProposedAnswer.YES,
    version: int = 1,
    evidence_review_id: str | None = None,
) -> ProposedDimensionAssessment:
    return ProposedDimensionAssessment(
        proposal_id=f"PROP-{dimension.value}",
        proposal_version=version,
        dimension=dimension,
        proposed_answer=answer,
        rationale=f"Fictional rationale for {dimension.value.title()}.",
        evidence_review_id=evidence_review_id or f"REV-{dimension.value}",
    )


def test_controlled_vocabulary_values_are_stable() -> None:
    assert [dimension.value for dimension in MateDimension] == [
        "MANDATE",
        "ACCOUNTABILITY",
        "TRIGGER",
        "ESCALATION",
    ]
    assert [answer.value for answer in ProposedAnswer] == [
        "YES",
        "NO",
        "UNRESOLVED",
    ]
    assert [status.value for status in SourceStatus] == [
        "CURRENT",
        "SUPERSEDED",
        "UNCERTAIN",
    ]
    assert [status.value for status in EvidenceAvailability] == [
        "REVIEWED_SUPPORTIVE",
        "REVIEWED_INADEQUATE",
        "CONTRADICTORY",
        "NOT_REQUESTED",
        "REQUESTED_NOT_PROVIDED",
        "UNAVAILABLE",
        "NOT_APPLICABLE",
    ]


@pytest.mark.parametrize(
    "field_name",
    [
        "source_id",
        "document_title",
        "document_version",
        "source_location",
        "source_wording",
    ],
)
def test_source_reference_rejects_blank_required_text(field_name: str) -> None:
    values = make_source(MateDimension.MANDATE).model_dump()
    values[field_name] = "   "

    with pytest.raises(ValidationError):
        SourceReference.model_validate(values)


def test_source_reference_is_frozen() -> None:
    source = make_source(MateDimension.MANDATE)

    with pytest.raises(ValidationError):
        source.status = SourceStatus.SUPERSEDED


@pytest.mark.parametrize("version", [0, -1])
def test_proposal_version_must_be_positive(version: int) -> None:
    with pytest.raises(ValidationError):
        make_proposal(MateDimension.MANDATE, version=version)


@pytest.mark.parametrize(
    "field_name",
    ["proposal_id", "rationale", "evidence_review_id"],
)
def test_proposal_rejects_blank_required_text(field_name: str) -> None:
    values = make_proposal(MateDimension.MANDATE).model_dump()
    values[field_name] = "   "

    with pytest.raises(ValidationError):
        ProposedDimensionAssessment.model_validate(values)


def test_unresolved_is_a_valid_proposed_answer() -> None:
    proposal = make_proposal(
        MateDimension.TRIGGER,
        answer=ProposedAnswer.UNRESOLVED,
    )

    assert proposal.proposed_answer is ProposedAnswer.UNRESOLVED


def test_proposal_is_frozen() -> None:
    proposal = make_proposal(MateDimension.MANDATE)

    with pytest.raises(ValidationError):
        proposal.proposed_answer = ProposedAnswer.NO
```

- [ ] **Step 2: Run the new test file and confirm it fails for the missing domain module**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_approval_gate.py -q
```

Expected: collection fails because `src.ace.domain.assessment` does not yet
exist.

- [ ] **Step 3: Create the controlled vocabulary and the first two records**

Create `src/ace/domain/assessment.py` with:

```python
"""Controlled evidence and auditor-decision records for MATE assessment."""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt


NonEmptyText = Annotated[str, Field(min_length=1)]
PositiveVersion = Annotated[StrictInt, Field(gt=0)]
ConfidenceScore = Annotated[float, Field(ge=0.0, le=1.0)]


class MateDimension(str, Enum):
    """The only four dimensions represented by MATE."""

    MANDATE = "MANDATE"
    ACCOUNTABILITY = "ACCOUNTABILITY"
    TRIGGER = "TRIGGER"
    ESCALATION = "ESCALATION"

    @property
    def field_name(self) -> str:
        return self.value.lower()

    @property
    def label(self) -> str:
        return self.value.title()


class ProposedAnswer(str, Enum):
    """A preparer's proposed answer before auditor approval."""

    YES = "YES"
    NO = "NO"
    UNRESOLVED = "UNRESOLVED"


class SourceStatus(str, Enum):
    """Whether a cited fictional source can support a current assessment."""

    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"
    UNCERTAIN = "UNCERTAIN"


class EvidenceAvailability(str, Enum):
    """How evidence availability was classified during review."""

    REVIEWED_SUPPORTIVE = "REVIEWED_SUPPORTIVE"
    REVIEWED_INADEQUATE = "REVIEWED_INADEQUATE"
    CONTRADICTORY = "CONTRADICTORY"
    NOT_REQUESTED = "NOT_REQUESTED"
    REQUESTED_NOT_PROVIDED = "REQUESTED_NOT_PROVIDED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceSufficiency(str, Enum):
    """Whether evidence is sufficient for control-design assessment."""

    SUFFICIENT_FOR_DESIGN_ASSESSMENT = "SUFFICIENT_FOR_DESIGN_ASSESSMENT"
    INSUFFICIENT = "INSUFFICIENT"
    UNRESOLVED = "UNRESOLVED"


class ContradictionStatus(str, Enum):
    """Status of contradictions identified in the reviewed evidence."""

    NONE_IDENTIFIED = "NONE_IDENTIFIED"
    EXPLAINED = "EXPLAINED"
    UNRESOLVED = "UNRESOLVED"


class AuditorDecisionStatus(str, Enum):
    """The accountable auditor's decision on one proposal version."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUIRED = "CHANGES_REQUIRED"


class SourceReference(BaseModel):
    """One precise fictional source passage reviewed for an assessment."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    source_id: NonEmptyText
    document_title: NonEmptyText
    document_version: NonEmptyText
    source_location: NonEmptyText
    source_wording: NonEmptyText
    status: SourceStatus


class ProposedDimensionAssessment(BaseModel):
    """A proposed answer for one MATE dimension."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    proposal_id: NonEmptyText
    proposal_version: PositiveVersion
    dimension: MateDimension
    proposed_answer: ProposedAnswer
    rationale: NonEmptyText
    evidence_review_id: NonEmptyText
```

Do not add rating logic or import FastAPI.

- [ ] **Step 4: Export only the records that now exist**

Update `src/ace/domain/__init__.py` to:

```python
"""ACE domain vocabulary and records."""

from .assessment import (
    AuditorDecisionStatus,
    ContradictionStatus,
    EvidenceAvailability,
    EvidenceSufficiency,
    MateDimension,
    ProposedAnswer,
    ProposedDimensionAssessment,
    SourceReference,
    SourceStatus,
)
from .enums import ControlRating, HazardCategory
from .models import (
    LOW_CONFIDENCE_FLAG,
    AssuranceDimensions,
    Control,
    EvaluationResult,
)

__all__ = [
    "LOW_CONFIDENCE_FLAG",
    "AssuranceDimensions",
    "AuditorDecisionStatus",
    "ContradictionStatus",
    "Control",
    "ControlRating",
    "EvidenceAvailability",
    "EvidenceSufficiency",
    "EvaluationResult",
    "HazardCategory",
    "MateDimension",
    "ProposedAnswer",
    "ProposedDimensionAssessment",
    "SourceReference",
    "SourceStatus",
]
```

- [ ] **Step 5: Run the Task 1 tests**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_approval_gate.py -q
```

Expected: the Task 1 tests pass.

- [ ] **Step 6: Commit the controlled vocabulary and basic records**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add src/ace/domain/assessment.py src/ace/domain/__init__.py tests/test_approval_gate.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff --cached --check
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: add controlled MATE assessment records"
```

---

## Task 2: Add Evidence Review And Auditor Decision Validation

**Files:**

- Modify: `src/ace/domain/assessment.py`
- Modify: `src/ace/domain/__init__.py`
- Modify: `tests/test_approval_gate.py`

- [ ] **Step 1: Add failing tests for evidence review integrity**

Add `EvidenceReviewRecord` to the imports in `tests/test_approval_gate.py`.
Then add this helper before the tests:

```python
def make_review(
    dimension: MateDimension,
    *,
    source: SourceReference | None = None,
    contradiction_status: ContradictionStatus = ContradictionStatus.NONE_IDENTIFIED,
    proposed_sufficiency: EvidenceSufficiency = (
        EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
    ),
) -> EvidenceReviewRecord:
    selected_source = source or make_source(dimension)
    return EvidenceReviewRecord(
        review_id=f"REV-{dimension.value}",
        source_references=(selected_source,),
        supporting_source_ids=(selected_source.source_id,),
        weakening_source_ids=(),
        contradictory_source_ids=(),
        evidence_availability=(EvidenceAvailability.REVIEWED_SUPPORTIVE,),
        contradiction_status=contradiction_status,
        contradiction_explanation=None,
        assumptions_checked=("The fictional source is the approved version.",),
        limitations=("This is a control-design review only.",),
        proposed_sufficiency=proposed_sufficiency,
    )
```

Add these tests:

```python
def test_evidence_review_requires_at_least_one_source() -> None:
    values = make_review(MateDimension.MANDATE).model_dump()
    values["source_references"] = ()

    with pytest.raises(ValidationError):
        EvidenceReviewRecord.model_validate(values)


def test_evidence_review_rejects_duplicate_source_identifiers() -> None:
    source = make_source(MateDimension.MANDATE)
    values = make_review(MateDimension.MANDATE, source=source).model_dump()
    values["source_references"] = (source, source)

    with pytest.raises(
        ValidationError,
        match="source identifiers must be unique",
    ):
        EvidenceReviewRecord.model_validate(values)


def test_evidence_review_rejects_unknown_classified_source() -> None:
    values = make_review(MateDimension.MANDATE).model_dump()
    values["supporting_source_ids"] = ("SRC-NOT-SUPPLIED",)

    with pytest.raises(
        ValidationError,
        match="classified source identifiers must resolve",
    ):
        EvidenceReviewRecord.model_validate(values)


def test_source_cannot_have_conflicting_evidence_classifications() -> None:
    review = make_review(MateDimension.MANDATE)
    values = review.model_dump()
    values["weakening_source_ids"] = review.supporting_source_ids

    with pytest.raises(
        ValidationError,
        match="must not appear in more than one evidence classification",
    ):
        EvidenceReviewRecord.model_validate(values)


def test_explained_contradiction_requires_an_explanation() -> None:
    values = make_review(MateDimension.TRIGGER).model_dump()
    values["contradiction_status"] = ContradictionStatus.EXPLAINED
    values["contradiction_explanation"] = "   "

    with pytest.raises(
        ValidationError,
        match="explained contradiction requires an explanation",
    ):
        EvidenceReviewRecord.model_validate(values)


def test_evidence_review_is_frozen() -> None:
    review = make_review(MateDimension.MANDATE)

    with pytest.raises(ValidationError):
        review.proposed_sufficiency = EvidenceSufficiency.INSUFFICIENT
```

- [ ] **Step 2: Add failing tests for auditor decision integrity**

Add `AuditorDecision` to the imports in `tests/test_approval_gate.py`, then add
this helper:

```python
def make_decision(
    dimension: MateDimension,
    *,
    status: AuditorDecisionStatus = AuditorDecisionStatus.APPROVED,
    approved_answer: bool | None = True,
    final_sufficiency: EvidenceSufficiency = (
        EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
    ),
    proposal_id: str | None = None,
    proposal_version: int = 1,
) -> AuditorDecision:
    return AuditorDecision(
        decision_id=f"DEC-{dimension.value}",
        proposal_id=proposal_id or f"PROP-{dimension.value}",
        proposal_version=proposal_version,
        dimension=dimension,
        decision_status=status,
        approved_answer=approved_answer,
        final_sufficiency=final_sufficiency,
        reviewer_id="FICTIONAL-AUDITOR-01",
        review_notes=f"Fictional review notes for {dimension.value.title()}.",
        reviewed_at="2026-07-27T01:02:03.456789+00:00",
    )
```

Add:

```python
def test_approved_decision_requires_a_boolean_answer() -> None:
    with pytest.raises(
        ValidationError,
        match="approved decision requires a Boolean answer",
    ):
        make_decision(MateDimension.MANDATE, approved_answer=None)


@pytest.mark.parametrize(
    "status",
    [
        AuditorDecisionStatus.REJECTED,
        AuditorDecisionStatus.CHANGES_REQUIRED,
    ],
)
def test_nonapproved_decision_must_not_contain_an_approved_answer(
    status: AuditorDecisionStatus,
) -> None:
    with pytest.raises(
        ValidationError,
        match="non-approved decision must not contain an approved answer",
    ):
        make_decision(MateDimension.MANDATE, status=status, approved_answer=True)


@pytest.mark.parametrize(
    "sufficiency",
    [EvidenceSufficiency.INSUFFICIENT, EvidenceSufficiency.UNRESOLVED],
)
def test_approved_decision_requires_sufficient_design_evidence(
    sufficiency: EvidenceSufficiency,
) -> None:
    with pytest.raises(
        ValidationError,
        match="approved decision requires sufficient design evidence",
    ):
        make_decision(
            MateDimension.MANDATE,
            final_sufficiency=sufficiency,
        )


@pytest.mark.parametrize(
    "timestamp",
    [
        "not-a-timestamp",
        "2026-07-27T01:02:03.456789",
        "2026-07-27T11:02:03.456789+10:00",
        "2026-07-27 01:02:03.456789+00:00",
        " 2026-07-27T01:02:03.456789+00:00",
        "2026-07-27T01:02:03.456789+00:00 ",
    ],
)
def test_auditor_decision_rejects_noncanonical_utc_timestamps(
    timestamp: str,
) -> None:
    values = make_decision(MateDimension.MANDATE).model_dump()
    values["reviewed_at"] = timestamp

    with pytest.raises(ValidationError):
        AuditorDecision.model_validate(values)


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-07-27T01:02:03.456789+00:00",
        "2026-07-27T01:02:03.456789Z",
    ],
)
def test_auditor_decision_accepts_canonical_utc_timestamps(
    timestamp: str,
) -> None:
    values = make_decision(MateDimension.MANDATE).model_dump()
    values["reviewed_at"] = timestamp

    assert AuditorDecision.model_validate(values).reviewed_at == timestamp


@pytest.mark.parametrize("field_name", ["reviewer_id", "review_notes"])
def test_auditor_decision_rejects_blank_review_text(field_name: str) -> None:
    values = make_decision(MateDimension.MANDATE).model_dump()
    values[field_name] = "   "

    with pytest.raises(ValidationError):
        AuditorDecision.model_validate(values)


def test_auditor_decision_is_frozen() -> None:
    decision = make_decision(MateDimension.MANDATE)

    with pytest.raises(ValidationError):
        decision.approved_answer = False
```

- [ ] **Step 3: Run the evidence and decision tests and confirm they fail**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_approval_gate.py -q
```

Expected: collection or construction fails because the two records have not
been implemented.

- [ ] **Step 4: Implement evidence review and auditor decision records**

Add these imports near the top of `src/ace/domain/assessment.py`:

```python
from datetime import datetime, timedelta
import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    field_validator,
    model_validator,
)
```

Replace the earlier one-line Pydantic import. Then add after
`ProposedDimensionAssessment`:

```python
UTC_ISO_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\+00:00|Z)"
)


class EvidenceReviewRecord(BaseModel):
    """The evidence organised for one proposed MATE answer."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    review_id: NonEmptyText
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    supporting_source_ids: tuple[NonEmptyText, ...] = ()
    weakening_source_ids: tuple[NonEmptyText, ...] = ()
    contradictory_source_ids: tuple[NonEmptyText, ...] = ()
    evidence_availability: tuple[EvidenceAvailability, ...] = Field(min_length=1)
    contradiction_status: ContradictionStatus
    contradiction_explanation: str | None = None
    assumptions_checked: tuple[NonEmptyText, ...] = ()
    limitations: tuple[NonEmptyText, ...] = ()
    proposed_sufficiency: EvidenceSufficiency

    @model_validator(mode="after")
    def validate_source_classifications(self) -> "EvidenceReviewRecord":
        source_ids = tuple(source.source_id for source in self.source_references)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source identifiers must be unique within a review")

        classifications = (
            self.supporting_source_ids,
            self.weakening_source_ids,
            self.contradictory_source_ids,
        )
        classified_ids = tuple(
            source_id
            for classification in classifications
            for source_id in classification
        )
        if not set(classified_ids).issubset(set(source_ids)):
            raise ValueError(
                "classified source identifiers must resolve to supplied sources"
            )
        if len(classified_ids) != len(set(classified_ids)):
            raise ValueError(
                "a source must not appear in more than one evidence classification"
            )

        if (
            self.contradiction_status is ContradictionStatus.EXPLAINED
            and not (self.contradiction_explanation or "").strip()
        ):
            raise ValueError("an explained contradiction requires an explanation")

        return self


class AuditorDecision(BaseModel):
    """The accountable auditor's immutable decision on one proposal version."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    decision_id: NonEmptyText
    proposal_id: NonEmptyText
    proposal_version: PositiveVersion
    dimension: MateDimension
    decision_status: AuditorDecisionStatus
    approved_answer: StrictBool | None = None
    final_sufficiency: EvidenceSufficiency
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
        if UTC_ISO_TIMESTAMP.fullmatch(reviewed_at) is None:
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

    @model_validator(mode="after")
    def validate_decision_state(self) -> "AuditorDecision":
        if self.decision_status is AuditorDecisionStatus.APPROVED:
            if self.approved_answer is None:
                raise ValueError("an approved decision requires a Boolean answer")
            if (
                self.final_sufficiency
                is not EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
            ):
                raise ValueError(
                    "an approved decision requires sufficient design evidence"
                )
        elif self.approved_answer is not None:
            raise ValueError(
                "a non-approved decision must not contain an approved answer"
            )

        return self
```

This duplicates the timestamp format check, not the rating rules. Do not move
or alter the existing `EvaluationResult` validator during this sprint.

- [ ] **Step 5: Export the two new records**

Add `AuditorDecision` and `EvidenceReviewRecord` to both the import block and
`__all__` in `src/ace/domain/__init__.py`. Keep the list in alphabetical order
apart from the existing `LOW_CONFIDENCE_FLAG` constant.

- [ ] **Step 6: Run the focused and complete tests**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_approval_gate.py -q
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: all tests pass. The one known dependency deprecation warning remains
visible.

- [ ] **Step 7: Commit the evidence and decision validation**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add src/ace/domain/assessment.py src/ace/domain/__init__.py tests/test_approval_gate.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff --cached --check
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: validate evidence reviews and auditor decisions"
```

---

## Task 3: Build The Approval Gate

**Files:**

- Modify: `src/ace/domain/assessment.py`
- Modify: `src/ace/domain/__init__.py`
- Create: `src/ace/engine/approval.py`
- Modify: `src/ace/engine/__init__.py`
- Modify: `tests/test_approval_gate.py`

- [ ] **Step 1: Add the shared fictional four-dimension fixture**

Add `HazardCategory` to the test imports:

```python
from src.ace.domain.enums import ControlRating, HazardCategory
```

Add `ApprovedMATEAssessment` to the assessment imports and add
`ApprovalBlockedError` and `build_approved_assessment`:

```python
from src.ace.engine.approval import (
    ApprovalBlockedError,
    build_approved_assessment,
)
```

Then add:

```python
MATE_ORDER = tuple(MateDimension)


def make_bundle(
    answers: dict[MateDimension, ProposedAnswer] | None = None,
) -> tuple[
    tuple[ProposedDimensionAssessment, ...],
    tuple[EvidenceReviewRecord, ...],
    tuple[AuditorDecision, ...],
]:
    selected_answers = answers or {}
    proposals = []
    reviews = []
    decisions = []

    for dimension in MATE_ORDER:
        answer = selected_answers.get(dimension, ProposedAnswer.YES)
        approved_answer = (
            True
            if answer is ProposedAnswer.YES
            else False
            if answer is ProposedAnswer.NO
            else None
        )
        reviews.append(make_review(dimension))
        proposals.append(make_proposal(dimension, answer=answer))
        if approved_answer is not None:
            decisions.append(
                make_decision(
                    dimension,
                    approved_answer=approved_answer,
                )
            )

    return tuple(proposals), tuple(reviews), tuple(decisions)


def build_assessment(
    *,
    proposals: tuple[ProposedDimensionAssessment, ...] | None = None,
    reviews: tuple[EvidenceReviewRecord, ...] | None = None,
    decisions: tuple[AuditorDecision, ...] | None = None,
) -> ApprovedMATEAssessment:
    default_proposals, default_reviews, default_decisions = make_bundle()
    return build_approved_assessment(
        control_id="ACE-FICTIONAL-001",
        title="Fictional mobilisation control",
        description="Fictional control-design assessment for testing only.",
        hazard_category=HazardCategory.GOVERNANCE_OVERSIGHT,
        proposals=proposals or default_proposals,
        evidence_reviews=reviews or default_reviews,
        decisions=decisions or default_decisions,
        confidence_score=0.95,
        reviewer_notes="Fictional Sprint 2 approval-boundary test.",
    )
```

- [ ] **Step 2: Add failing approval-gate tests**

Add:

```python
def test_gate_builds_four_approved_dimensions_in_stable_mate_order() -> None:
    proposals, reviews, decisions = make_bundle(
        {
            MateDimension.TRIGGER: ProposedAnswer.NO,
            MateDimension.ESCALATION: ProposedAnswer.NO,
        }
    )

    assessment = build_assessment(
        proposals=proposals,
        reviews=reviews,
        decisions=decisions,
    )

    assert assessment.dimensions.model_dump() == {
        "mandate": True,
        "accountability": True,
        "trigger": False,
        "escalation": False,
    }
    assert tuple(decision.dimension for decision in assessment.decisions) == MATE_ORDER


def test_approved_assessment_is_frozen() -> None:
    assessment = build_assessment()

    with pytest.raises(ValidationError):
        assessment.control_id = "CHANGED"


@pytest.mark.parametrize("collection_name", ["proposals", "decisions"])
def test_gate_blocks_a_missing_dimension(collection_name: str) -> None:
    proposals, reviews, decisions = make_bundle()
    values = {
        "proposals": proposals,
        "reviews": reviews,
        "decisions": decisions,
    }
    values[collection_name] = values[collection_name][:-1]

    with pytest.raises(
        ApprovalBlockedError,
        match="Escalation .* is missing",
    ):
        build_assessment(
            proposals=values["proposals"],
            reviews=values["reviews"],
            decisions=values["decisions"],
        )


@pytest.mark.parametrize("collection_name", ["proposals", "decisions"])
def test_gate_blocks_a_duplicate_dimension(collection_name: str) -> None:
    proposals, reviews, decisions = make_bundle()
    values = {
        "proposals": proposals,
        "reviews": reviews,
        "decisions": decisions,
    }
    values[collection_name] = values[collection_name] + (
        values[collection_name][0],
    )

    with pytest.raises(
        ApprovalBlockedError,
        match="Mandate .* appears more than once",
    ):
        build_assessment(
            proposals=values["proposals"],
            reviews=values["reviews"],
            decisions=values["decisions"],
        )


def test_gate_blocks_an_unresolved_proposal() -> None:
    proposals, reviews, decisions = make_bundle()
    proposals = (
        validated_copy(
            proposals[0],
            proposed_answer=ProposedAnswer.UNRESOLVED,
        ),
        *proposals[1:],
    )

    with pytest.raises(
        ApprovalBlockedError,
        match="Mandate remains unresolved",
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
        )


def test_missing_evidence_is_not_automatically_converted_to_no() -> None:
    proposals, reviews, decisions = make_bundle()
    proposals = (
        validated_copy(
            proposals[0],
            proposed_answer=ProposedAnswer.UNRESOLVED,
        ),
        *proposals[1:],
    )
    review = validated_copy(
        reviews[0],
        supporting_source_ids=(),
        evidence_availability=(
            EvidenceAvailability.REQUESTED_NOT_PROVIDED,
        ),
        proposed_sufficiency=EvidenceSufficiency.INSUFFICIENT,
    )
    reviews = (review, *reviews[1:])

    with pytest.raises(
        ApprovalBlockedError,
        match="Mandate remains unresolved",
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
        )


def test_auditor_final_sufficiency_can_override_the_proposed_review() -> None:
    proposals, reviews, decisions = make_bundle()
    review = validated_copy(
        reviews[0],
        proposed_sufficiency=EvidenceSufficiency.INSUFFICIENT,
    )
    reviews = (review, *reviews[1:])

    assessment = build_assessment(
        proposals=proposals,
        reviews=reviews,
        decisions=decisions,
    )

    assert assessment.dimensions.mandate is True


def test_gate_blocks_a_missing_evidence_review() -> None:
    proposals, reviews, decisions = make_bundle()

    with pytest.raises(
        ApprovalBlockedError,
        match="Mandate evidence review REV-MANDATE is missing",
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews[1:],
            decisions=decisions,
        )


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (AuditorDecisionStatus.REJECTED, "has been rejected"),
        (AuditorDecisionStatus.CHANGES_REQUIRED, "requires changes"),
    ],
)
def test_gate_blocks_nonapproved_auditor_decisions(
    status: AuditorDecisionStatus,
    message: str,
) -> None:
    proposals, reviews, decisions = make_bundle()
    replacement = make_decision(
        MateDimension.MANDATE,
        status=status,
        approved_answer=None,
        final_sufficiency=EvidenceSufficiency.INSUFFICIENT,
    )
    decisions = (replacement, *decisions[1:])

    with pytest.raises(ApprovalBlockedError, match=f"Mandate {message}"):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
        )


def test_gate_blocks_an_unresolved_contradiction() -> None:
    proposals, reviews, decisions = make_bundle()
    review = validated_copy(
        reviews[2],
        contradiction_status=ContradictionStatus.UNRESOLVED,
    )
    reviews = (*reviews[:2], review, *reviews[3:])

    with pytest.raises(
        ApprovalBlockedError,
        match="Trigger has an unresolved contradiction",
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
        )


@pytest.mark.parametrize(
    "source_status",
    [SourceStatus.SUPERSEDED, SourceStatus.UNCERTAIN],
)
def test_gate_blocks_a_dimension_without_a_current_source(
    source_status: SourceStatus,
) -> None:
    proposals, reviews, decisions = make_bundle()
    source = make_source(MateDimension.ACCOUNTABILITY, status=source_status)
    review = make_review(MateDimension.ACCOUNTABILITY, source=source)
    reviews = (reviews[0], review, *reviews[2:])

    with pytest.raises(
        ApprovalBlockedError,
        match="Accountability has no current reviewed source",
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
        )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"proposal_id": "PROP-WRONG"}, "proposal identifier"),
        ({"proposal_version": 2}, "proposal version"),
    ],
)
def test_gate_blocks_a_decision_that_does_not_match_its_proposal(
    change: dict[str, object],
    message: str,
) -> None:
    proposals, reviews, decisions = make_bundle()
    replacement = validated_copy(decisions[0], **change)
    decisions = (replacement, *decisions[1:])

    with pytest.raises(ApprovalBlockedError, match=message):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
        )


def test_gate_blocks_a_decision_with_the_wrong_dimension() -> None:
    proposals, reviews, decisions = make_bundle()
    replacement = validated_copy(
        decisions[0],
        dimension=MateDimension.TRIGGER,
    )
    decisions = (replacement, *decisions[1:])

    with pytest.raises(
        ApprovalBlockedError,
        match="Mandate auditor decision is missing",
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
        )


def test_gate_blocks_an_answer_that_differs_from_the_proposal() -> None:
    proposals, reviews, decisions = make_bundle()
    replacement = validated_copy(decisions[0], approved_answer=False)
    decisions = (replacement, *decisions[1:])

    with pytest.raises(
        ApprovalBlockedError,
        match="Mandate approved answer does not match the proposal",
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
        )
```

- [ ] **Step 3: Run the focused tests and confirm they fail**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_approval_gate.py -q
```

Expected: collection fails because the approved assessment and approval
service do not yet exist.

- [ ] **Step 4: Add the frozen approved assessment record**

Add this import in `src/ace/domain/assessment.py`:

```python
from .enums import HazardCategory
from .models import AssuranceDimensions
```

Then add:

```python
class ApprovedMATEAssessment(BaseModel):
    """The complete auditor-approved input to the existing evaluator."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    control_id: NonEmptyText
    title: NonEmptyText
    description: NonEmptyText
    hazard_category: HazardCategory
    confidence_score: ConfidenceScore = 1.0
    reviewer_notes: str | None = None
    decisions: tuple[AuditorDecision, ...] = Field(min_length=4, max_length=4)
    dimensions: AssuranceDimensions
```

Export `ApprovedMATEAssessment` from `src/ace/domain/__init__.py`.

The public workflow must never ask a caller to supply `dimensions`. Only
`build_approved_assessment()` constructs this record. This is a workflow
boundary, not an authentication boundary.

- [ ] **Step 5: Implement the approval gate without any rating logic**

Create `src/ace/engine/approval.py` with:

```python
"""Auditor approval boundary for controlled MATE assessments."""

from collections.abc import Sequence
from typing import TypeVar

from src.ace.domain.assessment import (
    ApprovedMATEAssessment,
    AuditorDecision,
    AuditorDecisionStatus,
    ContradictionStatus,
    EvidenceReviewRecord,
    EvidenceSufficiency,
    MateDimension,
    ProposedAnswer,
    ProposedDimensionAssessment,
    SourceStatus,
)
from src.ace.domain.enums import HazardCategory
from src.ace.domain.models import AssuranceDimensions


class ApprovalBlockedError(ValueError):
    """Raised when a valid record set is not ready for evaluation."""


RecordT = TypeVar("RecordT")
MATE_ORDER = tuple(MateDimension)


def _one_for_dimension(
    records: Sequence[RecordT],
    dimension: MateDimension,
    record_name: str,
) -> RecordT:
    matches = [
        record
        for record in records
        if getattr(record, "dimension", None) is dimension
    ]
    if not matches:
        raise ApprovalBlockedError(
            f"Evaluation blocked: {dimension.label} {record_name} is missing."
        )
    if len(matches) > 1:
        raise ApprovalBlockedError(
            f"Evaluation blocked: {dimension.label} {record_name} "
            "appears more than once."
        )
    return matches[0]


def _index_reviews(
    evidence_reviews: Sequence[EvidenceReviewRecord],
) -> dict[str, EvidenceReviewRecord]:
    indexed: dict[str, EvidenceReviewRecord] = {}
    for review in evidence_reviews:
        if review.review_id in indexed:
            raise ApprovalBlockedError(
                "Evaluation blocked: evidence review identifier "
                f"{review.review_id} appears more than once."
            )
        indexed[review.review_id] = review
    return indexed


def build_approved_assessment(
    *,
    control_id: str,
    title: str,
    description: str,
    hazard_category: HazardCategory,
    proposals: Sequence[ProposedDimensionAssessment],
    evidence_reviews: Sequence[EvidenceReviewRecord],
    decisions: Sequence[AuditorDecision],
    confidence_score: float = 1.0,
    reviewer_notes: str | None = None,
) -> ApprovedMATEAssessment:
    """Validate four approved MATE answers and build their frozen record."""

    reviews_by_id = _index_reviews(evidence_reviews)
    approved_answers: dict[str, bool] = {}
    ordered_decisions: list[AuditorDecision] = []

    for dimension in MATE_ORDER:
        proposal = _one_for_dimension(proposals, dimension, "proposal")
        decision = _one_for_dimension(decisions, dimension, "auditor decision")

        if proposal.proposed_answer is ProposedAnswer.UNRESOLVED:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} remains unresolved."
            )

        review = reviews_by_id.get(proposal.evidence_review_id)
        if review is None:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} evidence review "
                f"{proposal.evidence_review_id} is missing."
            )

        if not any(
            source.status is SourceStatus.CURRENT
            for source in review.source_references
        ):
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} has no current "
                "reviewed source."
            )

        if review.contradiction_status is ContradictionStatus.UNRESOLVED:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} has an unresolved "
                "contradiction."
            )

        if decision.proposal_id != proposal.proposal_id:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} decision proposal "
                "identifier does not match."
            )
        if decision.proposal_version != proposal.proposal_version:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} decision proposal "
                "version does not match."
            )
        if decision.dimension is not proposal.dimension:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} decision dimension "
                "does not match."
            )

        if decision.decision_status is AuditorDecisionStatus.REJECTED:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} has been rejected "
                "by the auditor."
            )
        if decision.decision_status is AuditorDecisionStatus.CHANGES_REQUIRED:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} requires changes "
                "before approval."
            )
        if decision.decision_status is not AuditorDecisionStatus.APPROVED:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} has not been approved "
                "by the auditor."
            )

        if (
            decision.final_sufficiency
            is not EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
        ):
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} evidence is not "
                "sufficient for design assessment."
            )
        if decision.approved_answer is None:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} has no approved "
                "Boolean answer."
            )

        expected_answer = proposal.proposed_answer is ProposedAnswer.YES
        if decision.approved_answer is not expected_answer:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} approved answer does "
                "not match the proposal."
            )

        approved_answers[dimension.field_name] = decision.approved_answer
        ordered_decisions.append(decision)

    dimensions = AssuranceDimensions(**approved_answers)
    return ApprovedMATEAssessment(
        control_id=control_id,
        title=title,
        description=description,
        hazard_category=hazard_category,
        confidence_score=confidence_score,
        reviewer_notes=reviewer_notes,
        decisions=tuple(ordered_decisions),
        dimensions=dimensions,
    )
```

Important: `_one_for_dimension()` checks the decision's dimension before the
proposal-link checks. Therefore, for a decision carrying the wrong dimension,
the stable failure will be that the expected dimension's auditor decision is
missing. Keep the test specific to that outcome.

- [ ] **Step 6: Export only the implemented gate symbols**

Update `src/ace/engine/__init__.py` to:

```python
"""ACE evaluation engine."""

from .approval import ApprovalBlockedError, build_approved_assessment
from .evaluator import evaluate_control

__all__ = [
    "ApprovalBlockedError",
    "build_approved_assessment",
    "evaluate_control",
]
```

- [ ] **Step 7: Run the focused tests and fix only approval-boundary defects**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_approval_gate.py -q
```

Expected: all focused tests pass. Do not alter the existing evaluator to make
a new test pass.

- [ ] **Step 8: Run the complete suite**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: all Sprint 1 and Sprint 2 tests pass with the known deprecation
warning still visible.

- [ ] **Step 9: Commit the approval gate**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add src/ace/domain/assessment.py src/ace/domain/__init__.py src/ace/engine/approval.py src/ace/engine/__init__.py tests/test_approval_gate.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff --cached --check
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: require auditor approval for MATE inputs"
```

---

## Task 4: Delegate Approved Assessments To The Existing Evaluator

**Files:**

- Modify: `src/ace/engine/approval.py`
- Modify: `src/ace/engine/__init__.py`
- Modify: `tests/test_approval_gate.py`

- [ ] **Step 1: Add failing integration tests**

Add `evaluate_approved_assessment` to the approval imports in
`tests/test_approval_gate.py`, then add:

```python
@pytest.mark.parametrize(
    ("answers", "expected_rating"),
    [
        ({}, ControlRating.ADEQUATE),
        (
            {MateDimension.TRIGGER: ProposedAnswer.NO},
            ControlRating.PARTIALLY_ADEQUATE,
        ),
        (
            {MateDimension.MANDATE: ProposedAnswer.NO},
            ControlRating.INADEQUATE,
        ),
        (
            {
                MateDimension.TRIGGER: ProposedAnswer.NO,
                MateDimension.ESCALATION: ProposedAnswer.NO,
            },
            ControlRating.INADEQUATE,
        ),
    ],
)
def test_approved_assessment_uses_existing_rating_precedence(
    answers: dict[MateDimension, ProposedAnswer],
    expected_rating: ControlRating,
) -> None:
    proposals, reviews, decisions = make_bundle(answers)
    assessment = build_assessment(
        proposals=proposals,
        reviews=reviews,
        decisions=decisions,
    )

    result = evaluate_approved_assessment(assessment)

    assert result.rating is expected_rating
    assert result.control_id == assessment.control_id


def test_approved_assessment_returns_the_existing_immutable_result() -> None:
    result = evaluate_approved_assessment(build_assessment())

    assert result.__class__.__name__ == "EvaluationResult"
    with pytest.raises(ValidationError):
        result.reasoning = "Changed"


def test_evaluation_delegates_to_the_existing_evaluator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assessment = build_assessment()
    captured = {}

    def fake_evaluate(control: object) -> str:
        captured["control"] = control
        return "delegated"

    monkeypatch.setattr(
        "src.ace.engine.approval.evaluate_control",
        fake_evaluate,
    )

    assert evaluate_approved_assessment(assessment) == "delegated"
    control = captured["control"]
    assert control.control_id == assessment.control_id
    assert control.dimensions is assessment.dimensions
```

The test double returns a string only to prove delegation. The production
function remains annotated to return `EvaluationResult`.

- [ ] **Step 2: Run the integration tests and confirm they fail**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_approval_gate.py -q
```

Expected: import fails because `evaluate_approved_assessment` is not yet
implemented.

- [ ] **Step 3: Implement evaluator delegation**

Add imports to `src/ace/engine/approval.py`:

```python
from src.ace.domain.models import AssuranceDimensions, Control, EvaluationResult
from src.ace.engine.evaluator import evaluate_control
```

Replace the existing `AssuranceDimensions`-only import, then add:

```python
def evaluate_approved_assessment(
    assessment: ApprovedMATEAssessment,
) -> EvaluationResult:
    """Delegate one complete approved assessment to the existing evaluator."""

    control = Control(
        control_id=assessment.control_id,
        title=assessment.title,
        description=assessment.description,
        hazard_category=assessment.hazard_category,
        dimensions=assessment.dimensions,
        confidence_score=assessment.confidence_score,
        reviewer_notes=assessment.reviewer_notes,
    )
    return evaluate_control(control)
```

Do not import `ControlRating` or reproduce any failure-counting rule in this
module.

- [ ] **Step 4: Export the approved evaluation function**

Update `src/ace/engine/__init__.py` to:

```python
"""ACE evaluation engine."""

from .approval import (
    ApprovalBlockedError,
    build_approved_assessment,
    evaluate_approved_assessment,
)
from .evaluator import evaluate_control

__all__ = [
    "ApprovalBlockedError",
    "build_approved_assessment",
    "evaluate_approved_assessment",
    "evaluate_control",
]
```

- [ ] **Step 5: Run focused tests**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest tests/test_approval_gate.py -q
```

Expected: all focused tests pass.

- [ ] **Step 6: Confirm there is no second rating implementation**

Run:

```powershell
Select-String -LiteralPath 'src\ace\engine\approval.py' -Pattern 'ControlRating|PARTIALLY_ADEQUATE|failure_count'
```

Expected: no matches.

- [ ] **Step 7: Run the complete suite**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: all tests pass and the known dependency warning remains visible.

- [ ] **Step 8: Commit evaluator integration**

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace add src/ace/engine/approval.py src/ace/engine/__init__.py tests/test_approval_gate.py
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff --cached --check
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace commit -m "feat: evaluate approved MATE assessments"
```

---

## Task 5: Complete Regression, Privacy And Runtime Verification

**Files:**

- Verify only: `src/ace/domain/assessment.py`
- Verify only: `src/ace/engine/approval.py`
- Verify only: `src/ace/domain/__init__.py`
- Verify only: `src/ace/engine/__init__.py`
- Verify only: `tests/test_approval_gate.py`
- Verify unchanged: `src/ace/engine/evaluator.py`
- Verify unchanged: `src/ace/app.py`
- Verify unchanged: `tests/test_rating_engine.py`
- Verify unchanged: `tests/test_app.py`

- [ ] **Step 1: Run the complete test suite from the approved local environment**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m pytest -q
```

Expected: the complete suite passes. Record the exact pass count and the one
known FastAPI/Starlette TestClient deprecation warning. Do not predict the
final pass count in advance.

- [ ] **Step 2: Compile the complete source tree**

Run:

```powershell
& 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -m compileall -q src
```

Expected: exit code 0 and no compile errors.

- [ ] **Step 3: Inspect the Sprint 2 code for prohibited capabilities or real evidence**

Run:

```powershell
Select-String -Path 'src\ace\domain\assessment.py','src\ace\engine\approval.py','tests\test_approval_gate.py' -Pattern 'http://|https://|requests|telemetry|analytics|supabase|postgres|pgvector|neo4j|graphrag|Squadron'
```

Expected: no matches. If a harmless match appears in a test description,
inspect it rather than automatically deleting it. No real source wording,
client evidence or external integration may remain.

- [ ] **Step 4: Verify both existing localhost endpoints**

Start the server locally and keep its process identifier:

```powershell
$aceServer = Start-Process -FilePath 'C:\tmp\sqe-ace-sprint-1\sqe\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','src.ace.app:app','--host','127.0.0.1','--port','8000' -PassThru -WindowStyle Hidden
```

Verify the health endpoint:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/' -Method Get
```

Expected fields:

```text
system           Assurance Compass Engine
status           ONLINE
audit_engagement Squadron Energy WHS Governance
```

Verify the evaluation endpoint:

```powershell
$evaluations = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/evaluations' -Method Get
$evaluations.Count
$evaluations | Select-Object control_id,rating
```

Expected: five fictional results with the existing IDs and ratings:

```text
ACE-BESS-001   ADEQUATE
ACE-HV-001     PARTIALLY_ADEQUATE
ACE-ARC-001    INADEQUATE
ACE-SIMOPS-001 PARTIALLY_ADEQUATE
ACE-SOCI-001   INADEQUATE
```

- [ ] **Step 5: Stop the server and prove port 8000 is closed**

Run:

```powershell
Stop-Process -Id $aceServer.Id
Wait-Process -Id $aceServer.Id -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
```

Expected: the final command returns no listener. If endpoint verification
fails, stop the recorded process before investigating.

- [ ] **Step 6: Inspect the exact branch diff and unchanged protected files**

Run:

```powershell
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace status --short --branch
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff 750f47ecd905f92827fd2018d16944013f829560 -- src/ace/domain/assessment.py src/ace/domain/__init__.py src/ace/engine/approval.py src/ace/engine/__init__.py tests/test_approval_gate.py docs/superpowers/specs/2026-07-27-ace-sprint-2-controlled-evidence-design.md docs/superpowers/plans/2026-07-27-ace-sprint-2-controlled-evidence.md
git -c safe.directory=C:/Users/AlanRichardson/Documents/agentic-os-workspace diff 750f47ecd905f92827fd2018d16944013f829560 --exit-code -- src/ace/engine/evaluator.py src/ace/app.py tests/test_rating_engine.py tests/test_app.py
```

Expected:

- the first diff contains only the approved Sprint 2 design, plan, domain
  records, approval service, exports and tests;
- the second diff exits 0, proving the protected Sprint 1 files are unchanged;
- unrelated dirty or untracked files remain untouched.

- [ ] **Step 7: Apply the verification-before-completion skill**

Read and follow `superpowers:verification-before-completion`. Base the final
claim only on fresh command output gathered in this task.

- [ ] **Step 8: Report the result without publishing it**

Report:

- the exact complete-test result;
- compile success;
- the two verified localhost responses;
- confirmation that the server stopped and port 8000 closed;
- confirmation that the evaluator and application behaviour remained
  unchanged;
- confirmation that only fictional, in-memory records were added;
- the known warning;
- the commits created; and
- that nothing was pushed, deployed, published or sent externally.

Do not push the branch. Do not open a tunnel. Do not contact external services.

---

## Completion Checklist

- [ ] Every MATE dimension has exactly one proposal and one matching auditor
      decision.
- [ ] Every proposal resolves to an evidence review containing at least one
      current fictional source.
- [ ] Evidence source identifiers resolve and do not carry conflicting
      classifications.
- [ ] `UNRESOLVED`, rejected, changes-required, insufficient and contradictory
      cases are blocked in plain English.
- [ ] Missing evidence is never automatically converted to `NO`.
- [ ] Approved `YES` and `NO` values alone become strict Booleans.
- [ ] Approved records and evaluation results are immutable.
- [ ] Strict canonical UTC timestamps are enforced.
- [ ] Control design is not described as proof of implementation or
      effectiveness.
- [ ] `evaluate_control()` remains the sole rating authority.
- [ ] Existing FastAPI routes and response bodies remain unchanged.
- [ ] No persistence, retrieval, AI, graph, telemetry or external service has
      been added.
- [ ] All test, compile, endpoint, shutdown, privacy and diff checks pass.
- [ ] Unrelated work remains untouched.
- [ ] Nothing is pushed or published.
