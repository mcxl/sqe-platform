"""Approval gate for one fictional Evidence-to-Conclusion chain."""

from collections.abc import Sequence
from typing import TypeVar

from src.ace.domain.assessment import AuditorDecisionStatus
from src.ace.domain.conclusion import (
    AcceptedEvidenceToConclusionRecord,
    AuditQuestionType,
    AuditorConclusionDecision,
    AuditorQuestionDecision,
    ConclusionContradictionStatus,
    ConclusionEvidenceSufficiency,
    ConclusionType,
    EffectivenessConclusion,
    EvidenceFreshness,
    EvidenceGapDisposition,
    EvidenceItem,
    EvidenceMatrixReview,
    EvidenceOrigin,
    ImplementationConclusion,
    ProposedAuditQuestion,
    ProposedEffectivenessConclusion,
    ProposedImplementationConclusion,
)
from src.ace.domain.trace import AcceptedPlanningTrace


class ConclusionApprovalBlockedError(ValueError):
    """Raised when records do not form an approved conclusion chain."""


RecordT = TypeVar("RecordT")
QUESTION_ORDER = tuple(AuditQuestionType)


def _title(value: AuditQuestionType | ConclusionType) -> str:
    return value.value.replace("_", " ").capitalize()


def _one_for_question_type(
    records: Sequence[RecordT],
    question_type: AuditQuestionType,
    record_name: str,
) -> RecordT:
    matches = [
        record
        for record in records
        if getattr(record, "question_type", None) is question_type
    ]
    if not matches:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question_type)} {record_name} is missing."
        )
    if len(matches) > 1:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question_type)} {record_name} "
            "appears more than once."
        )
    return matches[0]


def _validate_unique_attribute(
    records: Sequence[object],
    attribute: str,
    label: str,
) -> None:
    values: set[str] = set()
    for record in records:
        value = getattr(record, attribute)
        if value in values:
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: {label} {value} appears more than once."
            )
        values.add(value)


def _matching_question_decision(
    decisions: Sequence[AuditorQuestionDecision],
    question: ProposedAuditQuestion,
) -> AuditorQuestionDecision:
    id_matches = [
        decision for decision in decisions if decision.question_id == question.question_id
    ]
    if not id_matches:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question.question_type)} question "
            "decision is missing."
        )
    matches = [
        decision
        for decision in id_matches
        if decision.question_version == question.question_version
    ]
    if not matches:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question.question_type)} question "
            "decision version does not match."
        )
    if len(matches) > 1:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question.question_type)} question "
            "decision appears more than once."
        )
    decision = matches[0]
    if decision.question_type is not question.question_type:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question.question_type)} question "
            "decision type does not match."
        )
    if decision.decision_status is AuditorDecisionStatus.REJECTED:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question.question_type)} question "
            "has been rejected."
        )
    if decision.decision_status is AuditorDecisionStatus.CHANGES_REQUIRED:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question.question_type)} question "
            "requires changes."
        )
    if decision.decision_status is not AuditorDecisionStatus.APPROVED:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question.question_type)} question "
            "has not been approved."
        )
    return decision


def _matching_conclusion_decision(
    decisions: Sequence[AuditorConclusionDecision],
    proposal_id: str,
    proposal_version: int,
    conclusion_type: ConclusionType,
) -> AuditorConclusionDecision:
    id_matches = [
        decision for decision in decisions if decision.proposal_id == proposal_id
    ]
    if not id_matches:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(conclusion_type)} conclusion "
            "decision is missing."
        )
    matches = [
        decision for decision in id_matches if decision.proposal_version == proposal_version
    ]
    if not matches:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(conclusion_type)} conclusion "
            "decision version does not match."
        )
    if len(matches) > 1:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(conclusion_type)} conclusion "
            "decision appears more than once."
        )
    decision = matches[0]
    if decision.conclusion_type is not conclusion_type:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(conclusion_type)} conclusion "
            "decision type does not match."
        )
    if decision.decision_status is AuditorDecisionStatus.REJECTED:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(conclusion_type)} conclusion "
            "has been rejected."
        )
    if decision.decision_status is AuditorDecisionStatus.CHANGES_REQUIRED:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(conclusion_type)} conclusion "
            "requires changes."
        )
    if decision.decision_status is not AuditorDecisionStatus.APPROVED:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(conclusion_type)} conclusion "
            "has not been approved."
        )
    return decision


def _review_for_question(
    reviews: Sequence[EvidenceMatrixReview],
    question: ProposedAuditQuestion,
) -> EvidenceMatrixReview:
    matches = [review for review in reviews if review.question_id == question.question_id]
    if not matches:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {question.question_type.value.lower()} evidence "
            "matrix is missing."
        )
    if len(matches) > 1:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(question.question_type)} matrix review "
            "appears more than once."
        )
    return matches[0]


def _validate_proposal(
    *,
    proposal: ProposedImplementationConclusion | ProposedEffectivenessConclusion,
    decision: AuditorConclusionDecision,
    review: EvidenceMatrixReview,
    evidence_by_id: dict[str, EvidenceItem],
    question: ProposedAuditQuestion,
    conclusion_type: ConclusionType,
) -> None:
    if proposal.question_id != question.question_id:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {conclusion_type.value.lower()} proposal refers "
            "to the wrong question."
        )
    if proposal.evidence_review_id != review.review_id:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {conclusion_type.value.lower()} proposal refers "
            "to the wrong evidence matrix."
        )
    matrix_evidence_ids = {entry.evidence_id for entry in review.entries}
    relied_upon_items = []
    for evidence_id in proposal.relied_upon_evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: relied-upon evidence {evidence_id} is missing."
            )
        if evidence_id not in matrix_evidence_ids:
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: relied-upon evidence {evidence_id} is not in "
                f"the {conclusion_type.value.lower()} evidence matrix."
            )
        relied_upon_items.append(evidence)
    matrix_gap_ids = {gap.gap_id for gap in review.gaps}
    if set(proposal.considered_gap_ids) != matrix_gap_ids:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {conclusion_type.value.lower()} conclusion does "
            "not consider every evidence gap."
        )

    outcome = decision.approved_outcome
    if outcome != proposal.proposed_outcome:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(conclusion_type)} approved outcome "
            "does not match the proposal."
        )
    if outcome is None:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {_title(conclusion_type)} conclusion has no "
            "approved outcome."
        )
    not_determined = outcome.value == "NOT_DETERMINED"
    if not not_determined:
        if decision.final_sufficiency is not ConclusionEvidenceSufficiency.SUFFICIENT:
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: {conclusion_type.value.lower()} substantive "
                "conclusion requires sufficient evidence."
            )
        if not relied_upon_items:
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: {conclusion_type.value.lower()} substantive "
                "conclusion requires relied-upon evidence."
            )
        if not any(item.freshness is EvidenceFreshness.CURRENT for item in relied_upon_items):
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: {conclusion_type.value.lower()} conclusion "
                "has no current relied-upon evidence."
            )
        if review.contradiction_status is ConclusionContradictionStatus.UNRESOLVED:
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: {conclusion_type.value.lower()} evidence "
                "contains an unresolved contradiction."
            )
        if any(
            gap.is_material and gap.disposition is EvidenceGapDisposition.OPEN
            for gap in review.gaps
        ):
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: {conclusion_type.value.lower()} evidence "
                "contains an open material gap."
            )
        return

    if decision.final_sufficiency not in (
        ConclusionEvidenceSufficiency.INSUFFICIENT,
        ConclusionEvidenceSufficiency.UNRESOLVED,
    ):
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {conclusion_type.value.lower()} not determined "
            "requires insufficient or unresolved evidence."
        )
    if not proposal.limitations:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {conclusion_type.value.lower()} not determined "
            "conclusion requires an explicit limitation."
        )
    has_limiting_condition = (
        any(
            gap.disposition is EvidenceGapDisposition.OPEN
            for gap in review.gaps
        )
        or review.contradiction_status is ConclusionContradictionStatus.UNRESOLVED
        or any(item.freshness is not EvidenceFreshness.CURRENT for item in relied_upon_items)
    )
    if not has_limiting_condition:
        raise ConclusionApprovalBlockedError(
            f"Conclusion blocked: {conclusion_type.value.lower()} not determined "
            "conclusion has no evidence limitation."
        )


def build_accepted_evidence_to_conclusion(
    *,
    planning_trace: AcceptedPlanningTrace,
    questions: Sequence[ProposedAuditQuestion],
    question_decisions: Sequence[AuditorQuestionDecision],
    evidence_items: Sequence[EvidenceItem],
    evidence_reviews: Sequence[EvidenceMatrixReview],
    implementation_proposal: ProposedImplementationConclusion,
    effectiveness_proposal: ProposedEffectivenessConclusion,
    conclusion_decisions: Sequence[AuditorConclusionDecision],
) -> AcceptedEvidenceToConclusionRecord:
    """Validate and build one complete, approved conclusion chain."""

    expected_counts = (
        (questions, 3, "questions"),
        (question_decisions, 3, "question decisions"),
        (evidence_reviews, 2, "evidence reviews"),
        (conclusion_decisions, 2, "conclusion decisions"),
    )
    for records, expected_count, record_name in expected_counts:
        if len(records) > expected_count:
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: expected exactly {expected_count} "
                f"{record_name}, received {len(records)}."
            )

    main_question = _one_for_question_type(questions, AuditQuestionType.MAIN, "question")
    implementation_question = _one_for_question_type(questions, AuditQuestionType.IMPLEMENTATION, "question")
    effectiveness_question = _one_for_question_type(questions, AuditQuestionType.EFFECTIVENESS, "question")
    _validate_unique_attribute(questions, "question_id", "question identifier")
    identities = [(question.question_id, question.question_version) for question in questions]
    if len(identities) != len(set(identities)):
        raise ConclusionApprovalBlockedError(
            "Conclusion blocked: question identifier and version appear more than once."
        )
    _validate_unique_attribute(question_decisions, "decision_id", "question decision identifier")

    for question in (implementation_question, effectiveness_question):
        if question.parent_question_id != main_question.question_id:
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: {question.question_type.value.lower()} question "
                "does not identify the main question."
            )
    for question in (main_question, implementation_question, effectiveness_question):
        if question.control_id != planning_trace.control.control_id:
            raise ConclusionApprovalBlockedError(
                f"Conclusion blocked: {question.question_type.value.lower()} question "
                "concerns a different control."
            )

    ordered_questions = (main_question, implementation_question, effectiveness_question)
    ordered_question_decisions = tuple(
        _matching_question_decision(question_decisions, question)
        for question in ordered_questions
    )
    _validate_unique_attribute(evidence_items, "evidence_id", "evidence identifier")
    evidence_by_id = {item.evidence_id: item for item in evidence_items}
    for item in evidence_items:
        if item.origin is EvidenceOrigin.DERIVED:
            for source_id in item.source_evidence_ids:
                source = evidence_by_id.get(source_id)
                if source is None:
                    raise ConclusionApprovalBlockedError(
                        f"Conclusion blocked: derived evidence {item.evidence_id} "
                        f"source {source_id} is missing."
                    )
                if source.origin is not EvidenceOrigin.RAW:
                    raise ConclusionApprovalBlockedError(
                        f"Conclusion blocked: derived evidence {item.evidence_id} "
                        f"source {source_id} must resolve to raw evidence."
                    )
        if item.origin is EvidenceOrigin.AUDITOR_AUTHORED:
            for source_id in item.source_evidence_ids:
                if source_id not in evidence_by_id:
                    raise ConclusionApprovalBlockedError(
                        f"Conclusion blocked: auditor-authored evidence "
                        f"{item.evidence_id} source {source_id} is missing."
                    )

    implementation_review = _review_for_question(evidence_reviews, implementation_question)
    effectiveness_review = _review_for_question(evidence_reviews, effectiveness_question)
    ordered_reviews = (implementation_review, effectiveness_review)
    _validate_unique_attribute(evidence_reviews, "review_id", "evidence review identifier")
    entries = tuple(entry for review in ordered_reviews for entry in review.entries)
    gaps = tuple(gap for review in ordered_reviews for gap in review.gaps)
    _validate_unique_attribute(entries, "entry_id", "matrix entry identifier")
    _validate_unique_attribute(gaps, "gap_id", "evidence gap identifier")
    for review, question in zip(ordered_reviews, (implementation_question, effectiveness_question), strict=True):
        for entry in review.entries:
            if entry.question_id != review.question_id:
                raise ConclusionApprovalBlockedError(
                    f"Conclusion blocked: {question.question_type.value.lower()} "
                    "matrix contains an entry for a different question."
                )
            if entry.evidence_id not in evidence_by_id:
                raise ConclusionApprovalBlockedError(
                    f"Conclusion blocked: matrix evidence {entry.evidence_id} is "
                    "missing."
                )
        for gap in review.gaps:
            if gap.question_id != review.question_id:
                raise ConclusionApprovalBlockedError(
                    f"Conclusion blocked: {question.question_type.value.lower()} "
                    "matrix contains a gap for a different question."
                )
        for evidence_id in review.contradiction_evidence_ids:
            if evidence_id not in evidence_by_id:
                raise ConclusionApprovalBlockedError(
                    f"Conclusion blocked: contradiction evidence {evidence_id} is "
                    "missing."
                )

    proposals = (implementation_proposal, effectiveness_proposal)
    proposal_identities = [(proposal.proposal_id, proposal.proposal_version) for proposal in proposals]
    if len(proposal_identities) != len(set(proposal_identities)):
        proposal_id, proposal_version = next(
            identity
            for identity in proposal_identities
            if proposal_identities.count(identity) > 1
        )
        raise ConclusionApprovalBlockedError(
            "Conclusion blocked: conclusion proposal "
            f"{proposal_id} version {proposal_version} appears more than once."
        )
    _validate_unique_attribute(conclusion_decisions, "decision_id", "conclusion decision identifier")
    implementation_decision = _matching_conclusion_decision(
        conclusion_decisions,
        implementation_proposal.proposal_id,
        implementation_proposal.proposal_version,
        ConclusionType.IMPLEMENTATION,
    )
    effectiveness_decision = _matching_conclusion_decision(
        conclusion_decisions,
        effectiveness_proposal.proposal_id,
        effectiveness_proposal.proposal_version,
        ConclusionType.EFFECTIVENESS,
    )
    ordered_conclusion_decisions = (implementation_decision, effectiveness_decision)
    _validate_proposal(
        proposal=implementation_proposal,
        decision=implementation_decision,
        review=implementation_review,
        evidence_by_id=evidence_by_id,
        question=implementation_question,
        conclusion_type=ConclusionType.IMPLEMENTATION,
    )
    _validate_proposal(
        proposal=effectiveness_proposal,
        decision=effectiveness_decision,
        review=effectiveness_review,
        evidence_by_id=evidence_by_id,
        question=effectiveness_question,
        conclusion_type=ConclusionType.EFFECTIVENESS,
    )
    if (
        implementation_decision.approved_outcome
        in (ImplementationConclusion.NOT_IMPLEMENTED, ImplementationConclusion.NOT_DETERMINED)
        and effectiveness_decision.approved_outcome is not EffectivenessConclusion.NOT_DETERMINED
    ):
        raise ConclusionApprovalBlockedError(
            "Conclusion blocked: effectiveness must be not determined when "
            "implementation is not implemented or not determined."
        )

    return AcceptedEvidenceToConclusionRecord._from_approved_gate(
        planning_trace=planning_trace,
        questions=ordered_questions,
        question_decisions=ordered_question_decisions,
        evidence_items=tuple(evidence_items),
        evidence_reviews=ordered_reviews,
        implementation_proposal=implementation_proposal,
        effectiveness_proposal=effectiveness_proposal,
        conclusion_decisions=ordered_conclusion_decisions,
        question_decision_ids=tuple(decision.decision_id for decision in ordered_question_decisions),
        conclusion_decision_ids=tuple(decision.decision_id for decision in ordered_conclusion_decisions),
        implementation_outcome=implementation_decision.approved_outcome,
        effectiveness_outcome=effectiveness_decision.approved_outcome,
    )
