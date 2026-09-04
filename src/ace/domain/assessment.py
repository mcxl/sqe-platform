"""Controlled evidence and auditor-decision records for MATE assessment."""

from datetime import datetime, timedelta
from enum import Enum
import re
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    ValidationInfo,
    field_validator,
    model_validator,
)

from .enums import HazardCategory
from .models import AssuranceDimensions


NonEmptyText = Annotated[str, Field(min_length=1)]
PositiveVersion = Annotated[StrictInt, Field(gt=0)]
ConfidenceScore = Annotated[float, Field(ge=0.0, le=1.0)]
UTC_ISO_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\+00:00|Z)"
)
_APPROVED_MATE_CONTEXT_KEY = "approved_mate_assessment_factory"
_APPROVED_MATE_FACTORY_SENTINEL = object()
_TRUSTED_MATE_PERSISTENCE_SENTINEL = object()


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

        has_contradictory_evidence = (
            bool(self.contradictory_source_ids)
            or EvidenceAvailability.CONTRADICTORY in self.evidence_availability
        )
        if (
            has_contradictory_evidence
            and self.contradiction_status is ContradictionStatus.NONE_IDENTIFIED
        ):
            raise ValueError(
                "contradictory evidence requires a contradiction status"
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

    @model_validator(mode="before")
    @classmethod
    def require_approval_gate(
        cls,
        values: object,
        info: ValidationInfo,
    ) -> object:
        context = info.context
        factory = None if context is None else context.get(_APPROVED_MATE_CONTEXT_KEY)
        trusted_context = (
            factory is _APPROVED_MATE_FACTORY_SENTINEL
            or factory is _TRUSTED_MATE_PERSISTENCE_SENTINEL
        )
        if not trusted_context:
            raise ValueError(
                "approved MATE assessment must be built by the approval gate"
            )
        return values

    @model_validator(mode="after")
    def validate_approval_invariants(self) -> "ApprovedMATEAssessment":
        """Keep decisions and evaluator dimensions bound at every validation boundary."""

        if len(self.decisions) != len(MateDimension):
            raise ValueError("approved MATE assessment must have four decisions")
        dimensions = [decision.dimension for decision in self.decisions]
        if set(dimensions) != set(MateDimension) or len(dimensions) != len(
            set(dimensions)
        ):
            raise ValueError("approved MATE assessment must cover each dimension once")
        decision_ids = [decision.decision_id for decision in self.decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("approved MATE assessment decision identifiers must be unique")
        for decision in self.decisions:
            if decision.decision_status is not AuditorDecisionStatus.APPROVED:
                raise ValueError("approved MATE assessment contains a non-approved decision")
            if (
                decision.final_sufficiency
                is not EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
            ):
                raise ValueError("approved MATE assessment contains insufficient evidence")
            if decision.approved_answer is None:
                raise ValueError("approved MATE assessment contains no approved answer")
            if decision.approved_answer is not getattr(
                self.dimensions, decision.dimension.field_name
            ):
                raise ValueError(
                    "approved MATE assessment dimensions do not match decisions"
                )
        return self

    @classmethod
    def _from_approved_gate(
        cls,
        **values: object,
    ) -> "ApprovedMATEAssessment":
        """Construct an assessment after the application approval gate passes."""

        return cls.model_validate(
            values,
            context={
                _APPROVED_MATE_CONTEXT_KEY: _APPROVED_MATE_FACTORY_SENTINEL
            },
        )

    @classmethod
    def _from_trusted_persistence(
        cls,
        **values: object,
    ) -> "ApprovedMATEAssessment":
        """Rehydrate an immutable snapshot through the same approval invariants."""

        return cls.model_validate(
            values,
            context={
                _APPROVED_MATE_CONTEXT_KEY: _TRUSTED_MATE_PERSISTENCE_SENTINEL
            },
        )
