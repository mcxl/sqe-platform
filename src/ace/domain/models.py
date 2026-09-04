from datetime import datetime, timedelta
import re
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)

from .enums import ControlRating, HazardCategory

LOW_CONFIDENCE_FLAG = "Review required: confidence score is below 0.8."
NonEmptyText = Annotated[str, Field(min_length=1)]
ConfidenceScore = Annotated[float, Field(ge=0.0, le=1.0)]
FAILED_DIMENSION_ORDER = ("mandate", "accountability", "trigger", "escalation")
UTC_ISO_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\+00:00|Z)"
)


class AssuranceDimensions(BaseModel):
    """Four structural checks used to assess a control."""

    model_config = ConfigDict(frozen=True)

    mandate: StrictBool
    accountability: StrictBool
    trigger: StrictBool
    escalation: StrictBool


class Control(BaseModel):
    """A WHS governance control submitted to the evaluator."""

    model_config = ConfigDict(str_strip_whitespace=True)

    control_id: NonEmptyText
    title: NonEmptyText
    description: NonEmptyText
    hazard_category: HazardCategory
    dimensions: AssuranceDimensions
    confidence_score: ConfidenceScore = 1.0
    reviewer_notes: str | None = None

    @model_validator(mode="after")
    def add_low_confidence_flag(self) -> "Control":
        if self.confidence_score >= 0.8:
            return self

        notes = self.reviewer_notes or ""
        if LOW_CONFIDENCE_FLAG in notes:
            return self

        self.reviewer_notes = (
            f"{notes}\n{LOW_CONFIDENCE_FLAG}" if notes else LOW_CONFIDENCE_FLAG
        )
        return self


class EvaluationResult(BaseModel):
    """Immutable audit record produced by evaluating one control."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    control_id: NonEmptyText
    rating: ControlRating
    failed_dimensions: tuple[str, ...]
    timestamp: NonEmptyText
    reasoning: NonEmptyText

    @field_validator("failed_dimensions")
    @classmethod
    def validate_failed_dimensions(
        cls, failed_dimensions: tuple[str, ...]
    ) -> tuple[str, ...]:
        unknown_dimensions = set(failed_dimensions) - set(FAILED_DIMENSION_ORDER)
        if unknown_dimensions:
            raise ValueError("failed dimensions must use recognised names")

        if len(failed_dimensions) != len(set(failed_dimensions)):
            raise ValueError("failed dimensions must not contain duplicates")

        canonical_dimensions = tuple(
            dimension
            for dimension in FAILED_DIMENSION_ORDER
            if dimension in failed_dimensions
        )
        if failed_dimensions != canonical_dimensions:
            raise ValueError("failed dimensions must use canonical order")

        return failed_dimensions

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, timestamp: str) -> str:
        if UTC_ISO_TIMESTAMP.fullmatch(timestamp) is None:
            raise ValueError("timestamp must use canonical UTC ISO 8601 format")

        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
        except ValueError as error:
            raise ValueError("timestamp must use ISO 8601 format") from error

        utc_offset = parsed_timestamp.utcoffset()
        if utc_offset is None:
            raise ValueError("timestamp must include a timezone")
        if utc_offset != timedelta(0):
            raise ValueError("timestamp must use a zero UTC offset")

        return timestamp

    @field_validator("timestamp", mode="before")
    @classmethod
    def reject_timestamp_whitespace(cls, timestamp: object) -> object:
        if isinstance(timestamp, str) and timestamp != timestamp.strip():
            raise ValueError("timestamp must not contain surrounding whitespace")
        return timestamp
