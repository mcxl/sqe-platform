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
from src.ace.domain.models import AssuranceDimensions, Control, EvaluationResult
from src.ace.engine.evaluator import evaluate_control


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


def _validate_unique_record_identifiers(
    proposals: Sequence[ProposedDimensionAssessment],
    decisions: Sequence[AuditorDecision],
) -> None:
    proposal_identities: set[tuple[str, int]] = set()
    for proposal in proposals:
        identity = (proposal.proposal_id, proposal.proposal_version)
        if identity in proposal_identities:
            raise ApprovalBlockedError(
                f"Evaluation blocked: proposal {proposal.proposal_id} version "
                f"{proposal.proposal_version} appears more than once."
            )
        proposal_identities.add(identity)

    decision_ids: set[str] = set()
    for decision in decisions:
        if decision.decision_id in decision_ids:
            raise ApprovalBlockedError(
                "Evaluation blocked: auditor decision identifier "
                f"{decision.decision_id} appears more than once."
            )
        decision_ids.add(decision.decision_id)


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

    for dimension in MATE_ORDER:
        _one_for_dimension(proposals, dimension, "proposal")
        _one_for_dimension(decisions, dimension, "auditor decision")

    _validate_unique_record_identifiers(proposals, decisions)
    reviews_by_id = _index_reviews(evidence_reviews)
    approved_answers: dict[str, bool] = {}
    ordered_decisions: list[AuditorDecision] = []
    review_assignments: dict[str, MateDimension] = {}

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

        previous_dimension = review_assignments.get(review.review_id)
        if previous_dimension is not None:
            raise ApprovalBlockedError(
                f"Evaluation blocked: {dimension.label} reuses evidence review "
                f"{review.review_id} already assigned to "
                f"{previous_dimension.label}."
            )
        review_assignments[review.review_id] = dimension

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
