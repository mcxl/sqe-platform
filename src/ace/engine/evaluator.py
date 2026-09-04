"""ACE evaluation with deterministic decisions and actual UTC assessment times."""

from datetime import datetime, timezone

from src.ace.domain.enums import ControlRating
from src.ace.domain.models import Control, EvaluationResult

DIMENSIONS = (
    ("mandate", "Mandate"),
    ("accountability", "Accountability"),
    ("trigger", "Trigger"),
    ("escalation", "Escalation"),
)


def _join_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "None"


def _reasoning(
    rating: ControlRating,
    passed_labels: tuple[str, ...],
    failed_labels: tuple[str, ...],
) -> str:
    if rating is ControlRating.ADEQUATE:
        rationale = "all four assurance dimensions passed"
    elif len(failed_labels) >= 2:
        rationale = "two or more assurance dimensions failed"
    elif "Mandate" in failed_labels or "Accountability" in failed_labels:
        rationale = "a foundational Mandate or Accountability dimension failed"
    else:
        rationale = "exactly one non-foundational dimension failed"

    display_rating = rating.value.replace("_", " ").title()
    return (
        f"Rating: {display_rating}. "
        f"Passed dimensions: {_join_labels(passed_labels)}. "
        f"Failed dimensions: {_join_labels(failed_labels)}. "
        f"Rationale: {rationale}."
    )


def evaluate_control(control: Control) -> EvaluationResult:
    """Evaluate one control deterministically and record its actual UTC assessment time."""

    dimensions = control.dimensions
    failed_dimensions = tuple(
        field_name
        for field_name, _ in DIMENSIONS
        if not getattr(dimensions, field_name)
    )
    failed_labels = tuple(
        label for field_name, label in DIMENSIONS if not getattr(dimensions, field_name)
    )
    passed_labels = tuple(
        label for field_name, label in DIMENSIONS if getattr(dimensions, field_name)
    )

    failure_count = len(failed_dimensions)
    if failure_count == 0:
        rating = ControlRating.ADEQUATE
    elif (
        failure_count >= 2
        or not dimensions.mandate
        or not dimensions.accountability
    ):
        rating = ControlRating.INADEQUATE
    else:
        rating = ControlRating.PARTIALLY_ADEQUATE

    return EvaluationResult(
        control_id=control.control_id,
        rating=rating,
        failed_dimensions=failed_dimensions,
        timestamp=datetime.now(timezone.utc).isoformat(),
        reasoning=_reasoning(rating, passed_labels, failed_labels),
    )
