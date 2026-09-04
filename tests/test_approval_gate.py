from typing import Any

import pytest
from pydantic import ValidationError

from src.ace.domain.assessment import (
    ApprovedMATEAssessment,
    AuditorDecision,
    AuditorDecisionStatus,
    ContradictionStatus,
    EvidenceAvailability,
    EvidenceReviewRecord,
    EvidenceSufficiency,
    MateDimension,
    ProposedAnswer,
    ProposedDimensionAssessment,
    SourceReference,
    SourceStatus,
)
from src.ace.domain.enums import ControlRating, HazardCategory
from src.ace.domain.models import AssuranceDimensions, EvaluationResult
from src.ace.engine import approval as approval_module
from src.ace.engine.approval import (
    ApprovalBlockedError,
    build_approved_assessment,
    evaluate_approved_assessment,
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


def test_contradictory_evidence_cannot_report_none_identified() -> None:
    review = make_review(MateDimension.TRIGGER)
    values = review.model_dump()
    values["supporting_source_ids"] = ()
    values["contradictory_source_ids"] = (
        review.source_references[0].source_id,
    )
    values["evidence_availability"] = (EvidenceAvailability.CONTRADICTORY,)
    values["contradiction_status"] = ContradictionStatus.NONE_IDENTIFIED

    with pytest.raises(
        ValidationError,
        match="contradictory evidence requires a contradiction status",
    ):
        EvidenceReviewRecord.model_validate(values)


def test_evidence_review_is_frozen() -> None:
    review = make_review(MateDimension.MANDATE)

    with pytest.raises(ValidationError):
        review.proposed_sufficiency = EvidenceSufficiency.INSUFFICIENT


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


def test_approved_assessment_rejects_direct_construction() -> None:
    values = build_assessment().model_dump()

    with pytest.raises(
        ValidationError,
        match="approved MATE assessment must be built by the approval gate",
    ):
        ApprovedMATEAssessment(**values)

    with pytest.raises(
        ValidationError,
        match="approved MATE assessment must be built by the approval gate",
    ):
        ApprovedMATEAssessment.model_validate(values)


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


def test_gate_blocks_a_duplicate_proposal_identity() -> None:
    proposals, reviews, decisions = make_bundle()
    accountability_proposal = validated_copy(
        proposals[1],
        proposal_id=proposals[0].proposal_id,
        proposal_version=proposals[0].proposal_version,
    )
    accountability_decision = validated_copy(
        decisions[1],
        proposal_id=proposals[0].proposal_id,
        proposal_version=proposals[0].proposal_version,
    )
    proposals = (proposals[0], accountability_proposal, *proposals[2:])
    decisions = (decisions[0], accountability_decision, *decisions[2:])

    with pytest.raises(
        ApprovalBlockedError,
        match="proposal PROP-MANDATE version 1 appears more than once",
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
        )


def test_gate_blocks_a_duplicate_decision_identifier() -> None:
    proposals, reviews, decisions = make_bundle()
    accountability_decision = validated_copy(
        decisions[1],
        decision_id=decisions[0].decision_id,
    )
    decisions = (decisions[0], accountability_decision, *decisions[2:])

    with pytest.raises(
        ApprovalBlockedError,
        match="auditor decision identifier DEC-MANDATE appears more than once",
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
            decisions=decisions,
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


def test_gate_blocks_evidence_review_reuse_across_dimensions() -> None:
    proposals, reviews, decisions = make_bundle()
    accountability = validated_copy(
        proposals[1],
        evidence_review_id=proposals[0].evidence_review_id,
    )
    proposals = (proposals[0], accountability, *proposals[2:])

    with pytest.raises(
        ApprovalBlockedError,
        match=(
            "Accountability reuses evidence review REV-MANDATE "
            "already assigned to Mandate"
        ),
    ):
        build_assessment(
            proposals=proposals,
            reviews=reviews,
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


@pytest.mark.parametrize("construction", ["copy", "construct"])
def test_evaluation_rejects_adversarial_dimension_construction(
    construction: str,
) -> None:
    assessment = build_assessment()
    invalid_dimensions = AssuranceDimensions(
        mandate=False,
        accountability=True,
        trigger=True,
        escalation=True,
    )
    if construction == "copy":
        adversarial = assessment.model_copy(
            update={"dimensions": invalid_dimensions}
        )
    else:
        values = {
            field: getattr(assessment, field)
            for field in ApprovedMATEAssessment.model_fields
        }
        values["dimensions"] = invalid_dimensions
        adversarial = ApprovedMATEAssessment.model_construct(**values)

    with pytest.raises(
        ApprovalBlockedError,
        match="approved assessment invariants are invalid",
    ):
        evaluate_approved_assessment(adversarial)


def test_evaluation_rejects_adversarial_non_approved_decision() -> None:
    assessment = build_assessment()
    altered_decision = assessment.decisions[0].model_copy(
        update={"decision_status": AuditorDecisionStatus.REJECTED}
    )
    adversarial = ApprovedMATEAssessment.model_construct(
        **{
            **{
                field: getattr(assessment, field)
                for field in ApprovedMATEAssessment.model_fields
            },
            "decisions": (altered_decision, *assessment.decisions[1:]),
        }
    )

    with pytest.raises(
        ApprovalBlockedError,
        match="approved assessment invariants are invalid",
    ):
        evaluate_approved_assessment(adversarial)


def test_approved_assessment_delegates_to_the_existing_evaluator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assessment = build_assessment()
    evaluator_result = EvaluationResult(
        control_id=assessment.control_id,
        rating=ControlRating.ADEQUATE,
        failed_dimensions=(),
        timestamp="2026-07-28T02:03:04.567890+00:00",
        reasoning="Fictional result returned by the existing evaluator.",
    )
    received_controls = []

    def evaluate_control(control: object) -> EvaluationResult:
        received_controls.append(control)
        return evaluator_result

    monkeypatch.setattr(approval_module, "evaluate_control", evaluate_control)

    result = evaluate_approved_assessment(assessment)

    assert result is evaluator_result
    assert len(received_controls) == 1
    assert received_controls[0].control_id == assessment.control_id
    assert received_controls[0].dimensions == assessment.dimensions
