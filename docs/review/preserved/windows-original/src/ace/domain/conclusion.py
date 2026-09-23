"""Domain records for one fictional Evidence-to-Conclusion chain."""

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

from .assessment import AuditorDecisionStatus
from .trace import AcceptedPlanningTrace


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

    @field_validator("collected_at", "valid_from", "valid_until", mode="before")
    @classmethod
    def reject_timestamp_whitespace(cls, value: object) -> object:
        if isinstance(value, str) and value != value.strip():
            raise ValueError(
                "evidence timestamp must not contain surrounding whitespace"
            )
        return value

    @field_validator("collected_at", "valid_from", "valid_until")
    @classmethod
    def validate_evidence_timestamp(
        cls, value: str | None, info: ValidationInfo
    ) -> str | None:
        if value is None:
            return value
        labels = {
            "collected_at": "collection timestamp",
            "valid_from": "validity start",
            "valid_until": "validity end",
        }
        return _validate_canonical_utc(value, labels[info.field_name])

    @model_validator(mode="after")
    def validate_evidence_shape(self) -> "EvidenceItem":
        if len(set(self.source_evidence_ids)) != len(self.source_evidence_ids):
            raise ValueError("source evidence IDs must be unique")
        if self.origin is EvidenceOrigin.RAW and self.source_evidence_ids:
            raise ValueError("raw evidence must not identify source evidence")
        if self.origin is EvidenceOrigin.DERIVED and not self.source_evidence_ids:
            raise ValueError("derived evidence requires raw source evidence")
        if self.valid_from is not None and self.valid_until is not None:
            valid_from = datetime.fromisoformat(self.valid_from)
            valid_until = datetime.fromisoformat(self.valid_until)
            if valid_until < valid_from:
                raise ValueError("validity end must not precede validity start")
        return self


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

    @model_validator(mode="after")
    def validate_disposition(self) -> "EvidenceGap":
        if (
            self.disposition is not EvidenceGapDisposition.OPEN
            and not self.disposition_rationale
        ):
            raise ValueError("gap disposition requires a rationale")
        return self


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

    @model_validator(mode="after")
    def validate_review(self) -> "EvidenceMatrixReview":
        if not self.entries and not self.gaps:
            raise ValueError("matrix review requires evidence or an explicit gap")
        if len({entry.entry_id for entry in self.entries}) != len(self.entries):
            raise ValueError("matrix entry IDs must be unique")
        if len({entry.evidence_id for entry in self.entries}) != len(self.entries):
            raise ValueError("matrix evidence IDs must be unique")
        if len({gap.gap_id for gap in self.gaps}) != len(self.gaps):
            raise ValueError("matrix gap IDs must be unique")
        if self.contradiction_status is ConclusionContradictionStatus.NONE_IDENTIFIED:
            if self.contradiction_evidence_ids:
                raise ValueError(
                    "no identified contradiction must not identify evidence"
                )
            return self
        if len(set(self.contradiction_evidence_ids)) != len(
            self.contradiction_evidence_ids
        ):
            raise ValueError("contradiction evidence IDs must be unique")
        if len(self.contradiction_evidence_ids) < 2:
            raise ValueError(
                "contradiction status requires at least two unique evidence IDs"
            )
        if (
            self.contradiction_status is ConclusionContradictionStatus.EXPLAINED
            and not self.contradiction_explanation
        ):
            raise ValueError("explained contradiction requires an explanation")
        return self


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

    @model_validator(mode="after")
    def validate_references(self) -> "ProposedImplementationConclusion":
        if len(set(self.relied_upon_evidence_ids)) != len(
            self.relied_upon_evidence_ids
        ):
            raise ValueError("relied-upon evidence IDs must be unique")
        if len(set(self.considered_gap_ids)) != len(self.considered_gap_ids):
            raise ValueError("considered gap IDs must be unique")
        return self


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

    @model_validator(mode="after")
    def validate_references(self) -> "ProposedEffectivenessConclusion":
        if len(set(self.relied_upon_evidence_ids)) != len(
            self.relied_upon_evidence_ids
        ):
            raise ValueError("relied-upon evidence IDs must be unique")
        if len(set(self.considered_gap_ids)) != len(self.considered_gap_ids):
            raise ValueError("considered gap IDs must be unique")
        return self


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

    @field_validator("approved_outcome", mode="before")
    @classmethod
    def parse_approved_outcome_for_conclusion_type(
        cls,
        value: object,
        info: ValidationInfo,
    ) -> object:
        if isinstance(
            value,
            (ImplementationConclusion, EffectivenessConclusion),
        ):
            return value

        conclusion_type = info.data.get("conclusion_type")
        try:
            if conclusion_type is ConclusionType.IMPLEMENTATION:
                return ImplementationConclusion(value)
            if conclusion_type is ConclusionType.EFFECTIVENESS:
                return EffectivenessConclusion(value)
        except (TypeError, ValueError):
            return value
        return value

    @model_validator(mode="after")
    def validate_decision_state(self) -> "AuditorConclusionDecision":
        if self.decision_status is not AuditorDecisionStatus.APPROVED:
            if self.approved_outcome is not None:
                raise ValueError(
                    "non-approved decision must not contain an approved outcome"
                )
            return self

        if self.approved_outcome is None:
            raise ValueError("approved decision requires an approved outcome")

        if (
            self.conclusion_type is ConclusionType.IMPLEMENTATION
            and not isinstance(self.approved_outcome, ImplementationConclusion)
        ):
            raise ValueError(
                "implementation decision requires an implementation outcome"
            )
        if (
            self.conclusion_type is ConclusionType.EFFECTIVENESS
            and not isinstance(self.approved_outcome, EffectivenessConclusion)
        ):
            raise ValueError(
                "effectiveness decision requires an effectiveness outcome"
            )

        if self.approved_outcome.value == "NOT_DETERMINED":
            if self.final_sufficiency is ConclusionEvidenceSufficiency.SUFFICIENT:
                raise ValueError(
                    "not determined requires insufficient or unresolved evidence"
                )
            return self

        if self.final_sufficiency is not ConclusionEvidenceSufficiency.SUFFICIENT:
            raise ValueError(
                "substantive conclusion requires sufficient evidence"
            )
        return self


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
