"""Auditor approval boundary for controlled MATE assessments."""

from collections.abc import Callable, Sequence
from hashlib import sha256
import hmac
import json
import secrets
from typing import TypeVar
import weakref

from src.ace.domain.assessment import (
    ApprovedMATEAssessment,
    _APPROVED_MATE_CONSTRUCTION_CONTEXT,
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


def _complete_approval_gate(
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
    assessment = ApprovedMATEAssessment.model_validate(
        {
            "control_id": control_id,
            "title": title,
            "description": description,
            "hazard_category": hazard_category,
            "confidence_score": confidence_score,
            "reviewer_notes": reviewer_notes,
            "decisions": tuple(ordered_decisions),
            "dimensions": dimensions,
        },
        context={
            "approved_mate_construction": _APPROVED_MATE_CONSTRUCTION_CONTEXT
        },
    )
    return assessment


def _approval_boundary() -> tuple[
    Callable[..., ApprovedMATEAssessment],
    Callable[[ApprovedMATEAssessment], EvaluationResult],
    Callable[..., ApprovedMATEAssessment],
]:
    """Keep MATE origin records inaccessible outside this approval boundary.

    This binds an issued object to its canonical content in this Python process. It
    does not make a hostile in-process importer a security boundary.
    """

    origins: dict[
        int, tuple[weakref.ReferenceType[ApprovedMATEAssessment], str, bytes]
    ] = {}
    origin_key = secrets.token_bytes(32)
    g0_digest = "bdc022399d6e4a7d1558776b5bafdd406dda0e7a537dbd7ef3aa46d2ae4dad3c"
    g0_created_at = "2026-08-01T00:00:00Z"
    g0_created_by = "seed"

    def content_digest(assessment: ApprovedMATEAssessment) -> str:
        return sha256(
            json.dumps(
                assessment.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

    def origin_authentication(
        assessment: ApprovedMATEAssessment, digest: str
    ) -> bytes:
        return hmac.digest(
            origin_key,
            f"{id(assessment)}:{digest}".encode(),
            "sha256",
        )

    def register(assessment: ApprovedMATEAssessment) -> ApprovedMATEAssessment:
        identifier = id(assessment)

        def remove_origin(
            reference: weakref.ReferenceType[ApprovedMATEAssessment],
        ) -> None:
            current_origin = origins.get(identifier)
            if (
                isinstance(current_origin, tuple)
                and len(current_origin) == 3
                and current_origin[0] is reference
            ):
                del origins[identifier]

        reference = weakref.ref(assessment, remove_origin)
        digest = content_digest(assessment)
        origins[identifier] = (
            reference,
            digest,
            origin_authentication(assessment, digest),
        )
        return assessment

    def build(**values: object) -> ApprovedMATEAssessment:
        assessment = _complete_approval_gate(**values)
        return register(assessment)

    def rehydrate(
        values: dict[str, object], created_at: str, created_by: str
    ) -> ApprovedMATEAssessment:
        digest = sha256(
            json.dumps(
                values, sort_keys=True, separators=(",", ":"), default=str
            ).encode()
        ).hexdigest()
        if (
            created_at != g0_created_at
            or created_by != g0_created_by
            or digest != g0_digest
        ):
            raise ValueError("persisted MATE snapshot is not the verified G0 record")
        assessment = ApprovedMATEAssessment.model_validate(
            values,
            context={
                "approved_mate_construction": _APPROVED_MATE_CONSTRUCTION_CONTEXT
            },
        )
        return register(assessment)

    def evaluate(assessment: ApprovedMATEAssessment) -> EvaluationResult:
        try:
            origin = origins.get(id(assessment))
            if (
                not isinstance(origin, tuple)
                or len(origin) != 3
                or origin[0]() is not assessment
                or not isinstance(origin[1], str)
                or not isinstance(origin[2], bytes)
                or origin[1] != (digest := content_digest(assessment))
                or not hmac.compare_digest(
                    origin[2], origin_authentication(assessment, digest)
                )
            ):
                raise ValueError("approved MATE assessment has no trusted origin")
            assessment = ApprovedMATEAssessment.model_validate(
                assessment.model_dump(),
                context={
                    "approved_mate_construction": _APPROVED_MATE_CONSTRUCTION_CONTEXT
                },
            )
        except (TypeError, ValueError) as error:
            raise ApprovalBlockedError(
                "Evaluation blocked: approved assessment invariants are invalid."
            ) from error
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

    return build, evaluate, rehydrate


build_approved_assessment, evaluate_approved_assessment, rehydrate_verified_g0_mate = (
    _approval_boundary()
)
