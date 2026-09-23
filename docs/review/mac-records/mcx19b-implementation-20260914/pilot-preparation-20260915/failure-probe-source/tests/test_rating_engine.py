from datetime import datetime

from src.ace.domain.enums import ControlRating, HazardCategory

import pytest
from pydantic import ValidationError

from src.ace.engine.evaluator import evaluate_control

from src.ace.domain.models import (
    LOW_CONFIDENCE_FLAG,
    AssuranceDimensions,
    Control,
    EvaluationResult,
)


def test_control_rating_values_are_stable() -> None:
    assert [rating.value for rating in ControlRating] == [
        "ADEQUATE",
        "PARTIALLY_ADEQUATE",
        "INADEQUATE",
    ]


def test_hazard_category_values_are_stable() -> None:
    assert [category.value for category in HazardCategory] == [
        "BESS_THERMAL_RUNAWAY",
        "HV_ENERGIZATION",
        "ARC_FLASH",
        "SIMOPS",
        "SOCI_CYBER_PHYSICAL",
        "TPRM_CONTRACTOR_ONBOARDING",
        "GOVERNANCE_OVERSIGHT",
        "SAFETY_IN_DESIGN",
    ]


def make_control(
    *,
    confidence_score: float = 1.0,
    reviewer_notes: str | None = None,
) -> Control:
    return Control(
        control_id="ACE-TEST-001",
        title="Test control",
        description="Fictional test control.",
        hazard_category=HazardCategory.GOVERNANCE_OVERSIGHT,
        dimensions=AssuranceDimensions(
            mandate=True,
            accountability=True,
            trigger=True,
            escalation=True,
        ),
        confidence_score=confidence_score,
        reviewer_notes=reviewer_notes,
    )


@pytest.mark.parametrize("score", [0.0, 0.8, 1.0])
def test_confidence_boundaries_are_accepted(score: float) -> None:
    assert make_control(confidence_score=score).confidence_score == score


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_confidence_outside_range_is_rejected(score: float) -> None:
    with pytest.raises(ValidationError):
        make_control(confidence_score=score)


def test_low_confidence_adds_review_flag() -> None:
    control = make_control(confidence_score=0.79)

    assert control.reviewer_notes == LOW_CONFIDENCE_FLAG


def test_low_confidence_preserves_existing_notes() -> None:
    control = make_control(
        confidence_score=0.79,
        reviewer_notes="Check the fictional evidence source.",
    )

    assert control.reviewer_notes == (
        "Check the fictional evidence source.\n"
        f"{LOW_CONFIDENCE_FLAG}"
    )


def test_low_confidence_flag_is_not_duplicated() -> None:
    first = make_control(confidence_score=0.79)
    second = Control.model_validate(first.model_dump())

    assert second.reviewer_notes == LOW_CONFIDENCE_FLAG


def test_confidence_at_threshold_is_not_flagged() -> None:
    assert make_control(confidence_score=0.8).reviewer_notes is None


def test_assurance_dimensions_require_strict_booleans() -> None:
    with pytest.raises(ValidationError):
        AssuranceDimensions(
            mandate=1,
            accountability=True,
            trigger=True,
            escalation=True,
        )


@pytest.mark.parametrize("field_name", ["control_id", "title", "description"])
def test_control_identity_text_rejects_blank_values(field_name: str) -> None:
    values = {
        "control_id": "ACE-TEST-001",
        "title": "Test control",
        "description": "Fictional test control.",
        "hazard_category": HazardCategory.GOVERNANCE_OVERSIGHT,
        "dimensions": AssuranceDimensions(
            mandate=True,
            accountability=True,
            trigger=True,
            escalation=True,
        ),
    }
    values[field_name] = "   "

    with pytest.raises(ValidationError):
        Control(**values)


def test_evaluation_result_serialises_failed_dimensions_as_json_array() -> None:
    result = EvaluationResult(
        control_id="ACE-TEST-001",
        rating=ControlRating.PARTIALLY_ADEQUATE,
        failed_dimensions=("trigger",),
        timestamp="2026-07-26T00:00:00+00:00",
        reasoning="Fictional reasoning.",
    )

    assert result.model_dump(mode="json")["failed_dimensions"] == ["trigger"]


@pytest.mark.parametrize(
    "failed_dimensions",
    [
        ("unknown",),
        ("trigger", "trigger"),
        ("trigger", "mandate"),
    ],
    ids=["unknown-name", "duplicate", "non-canonical-order"],
)
def test_evaluation_result_rejects_invalid_failed_dimensions(
    failed_dimensions: tuple[str, ...],
) -> None:
    with pytest.raises(ValidationError):
        EvaluationResult(
            control_id="ACE-TEST-001",
            rating=ControlRating.INADEQUATE,
            failed_dimensions=failed_dimensions,
            timestamp="2026-07-27T01:02:03.456789+00:00",
            reasoning="Fictional reasoning.",
        )


@pytest.mark.parametrize(
    "timestamp",
    [
        "not-a-timestamp",
        "2026-07-27T01:02:03.456789",
        "2026-07-27T11:02:03.456789+10:00",
        "2026-07-27X01:02:03.456789+00:00",
        "2026-07-27 01:02:03.456789+00:00",
        " 2026-07-27T01:02:03.456789+00:00",
        "2026-07-27T01:02:03.456789+00:00 ",
    ],
    ids=[
        "malformed",
        "timezone-naive",
        "non-utc-offset",
        "non-canonical-x-separator",
        "non-canonical-space-separator",
        "leading-whitespace",
        "trailing-whitespace",
    ],
)
def test_evaluation_result_rejects_invalid_timestamps(timestamp: str) -> None:
    with pytest.raises(ValidationError):
        EvaluationResult(
            control_id="ACE-TEST-001",
            rating=ControlRating.PARTIALLY_ADEQUATE,
            failed_dimensions=("trigger",),
            timestamp=timestamp,
            reasoning="Fictional reasoning.",
        )


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-07-27T01:02:03.456789+00:00",
        "2026-07-27T01:02:03.456789Z",
    ],
    ids=["explicit-zero-offset", "zulu-suffix"],
)
def test_evaluation_result_accepts_canonical_immutable_record(timestamp: str) -> None:
    result = EvaluationResult(
        control_id="ACE-TEST-001",
        rating=ControlRating.INADEQUATE,
        failed_dimensions=["mandate", "trigger", "escalation"],
        timestamp=timestamp,
        reasoning="Fictional reasoning.",
    )

    assert result.failed_dimensions == ("mandate", "trigger", "escalation")
    assert isinstance(result.failed_dimensions, tuple)
    assert result.timestamp == timestamp
    assert isinstance(result.timestamp, str)


RATING_CASES = [
    (False, False, False, False, ControlRating.INADEQUATE),
    (False, False, False, True, ControlRating.INADEQUATE),
    (False, False, True, False, ControlRating.INADEQUATE),
    (False, False, True, True, ControlRating.INADEQUATE),
    (False, True, False, False, ControlRating.INADEQUATE),
    (False, True, False, True, ControlRating.INADEQUATE),
    (False, True, True, False, ControlRating.INADEQUATE),
    (False, True, True, True, ControlRating.INADEQUATE),
    (True, False, False, False, ControlRating.INADEQUATE),
    (True, False, False, True, ControlRating.INADEQUATE),
    (True, False, True, False, ControlRating.INADEQUATE),
    (True, False, True, True, ControlRating.INADEQUATE),
    (True, True, False, False, ControlRating.INADEQUATE),
    (True, True, False, True, ControlRating.PARTIALLY_ADEQUATE),
    (True, True, True, False, ControlRating.PARTIALLY_ADEQUATE),
    (True, True, True, True, ControlRating.ADEQUATE),
]


@pytest.mark.parametrize(
    ("mandate", "accountability", "trigger", "escalation", "expected_rating"),
    RATING_CASES,
)
def test_all_dimension_permutations(
    mandate: bool,
    accountability: bool,
    trigger: bool,
    escalation: bool,
    expected_rating: ControlRating,
) -> None:
    control = make_control()
    control.dimensions = AssuranceDimensions(
        mandate=mandate,
        accountability=accountability,
        trigger=trigger,
        escalation=escalation,
    )

    result = evaluate_control(control)

    assert result.rating is expected_rating


def test_failed_dimensions_follow_stable_order() -> None:
    control = make_control()
    control.dimensions = AssuranceDimensions(
        mandate=False,
        accountability=True,
        trigger=False,
        escalation=False,
    )

    result = evaluate_control(control)

    assert result.failed_dimensions == ("mandate", "trigger", "escalation")


def test_reasoning_names_passed_and_failed_dimensions() -> None:
    control = make_control()
    control.dimensions = AssuranceDimensions(
        mandate=True,
        accountability=True,
        trigger=False,
        escalation=True,
    )

    result = evaluate_control(control)

    assert "Passed dimensions: Mandate, Accountability, Escalation." in result.reasoning
    assert "Failed dimensions: Trigger." in result.reasoning
    assert "exactly one non-foundational dimension failed" in result.reasoning


def test_adequate_reasoning_explains_total_pass() -> None:
    result = evaluate_control(make_control())

    assert "Failed dimensions: None." in result.reasoning
    assert "all four assurance dimensions passed" in result.reasoning


def test_inadequate_reasoning_explains_precedence() -> None:
    control = make_control()
    control.dimensions = AssuranceDimensions(
        mandate=True,
        accountability=True,
        trigger=False,
        escalation=False,
    )

    result = evaluate_control(control)

    assert result.rating is ControlRating.INADEQUATE
    assert "two or more assurance dimensions failed" in result.reasoning


def test_timestamp_is_timezone_aware_utc() -> None:
    result = evaluate_control(make_control())

    timestamp = datetime.fromisoformat(result.timestamp)
    assert timestamp.utcoffset() is not None
    assert timestamp.utcoffset().total_seconds() == 0


def test_evaluation_result_fields_are_frozen() -> None:
    result = evaluate_control(make_control())

    with pytest.raises(ValidationError):
        result.rating = ControlRating.INADEQUATE


def test_failed_dimensions_collection_is_immutable() -> None:
    control = make_control()
    control.dimensions = AssuranceDimensions(
        mandate=True,
        accountability=True,
        trigger=False,
        escalation=True,
    )
    result = evaluate_control(control)

    with pytest.raises(TypeError):
        result.failed_dimensions[0] = "escalation"
