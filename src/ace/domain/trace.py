"""Domain records for one fictional Connected Assurance planning trace."""

from datetime import datetime, timedelta
from enum import Enum
import re
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    ValidationInfo,
    field_validator,
    model_validator,
)

from .assessment import (
    ApprovedMATEAssessment,
    AuditorDecisionStatus,
    SourceReference,
)
from .models import EvaluationResult


NonEmptyText = Annotated[str, Field(min_length=1)]
PositiveVersion = Annotated[StrictInt, Field(gt=0)]
TRACE_UTC_ISO_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\+00:00|Z)"
)
_ACCEPTED_TRACE_CONTEXT_KEY = "accepted_trace_factory"
_ACCEPTED_TRACE_FACTORY_SENTINEL = object()


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
            or context.get(_ACCEPTED_TRACE_CONTEXT_KEY)
            is not _ACCEPTED_TRACE_FACTORY_SENTINEL
        ):
            raise ValueError(
                "accepted planning trace must be built by the approval gate"
            )
        return values

    @classmethod
    def _from_approved_gate(cls, **values: object) -> "AcceptedPlanningTrace":
        """Construct a trace after the application approval gate has passed."""

        return cls.model_validate(
            values,
            context={
                _ACCEPTED_TRACE_CONTEXT_KEY: _ACCEPTED_TRACE_FACTORY_SENTINEL
            },
        )
