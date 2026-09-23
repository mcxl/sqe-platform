from pathlib import Path
from typing import Any

import pytest
from fastapi.routing import APIRoute
from pydantic import ValidationError

from src.ace.app import app
from src.ace.domain.assessment import (
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
from src.ace.domain.conclusion import (
    AcceptedEvidenceToConclusionRecord,
    AuditQuestionType,
    AuditorConclusionDecision,
    AuditorQuestionDecision,
    ConclusionContradictionStatus,
    ConclusionEvidenceSufficiency,
    ConclusionType,
    EvidenceFreshness,
    EvidenceGap,
    EvidenceGapDisposition,
    EvidenceGapStatus,
    EvidenceItem,
    EvidenceMatrixEntry,
    EvidenceMatrixReview,
    EvidenceOrigin,
    EvidenceRelevance,
    EffectivenessConclusion,
    ImplementationConclusion,
    ProposedAuditQuestion,
    ProposedEffectivenessConclusion,
    ProposedImplementationConclusion,
)
from src.ace.domain.enums import ControlRating, HazardCategory
from src.ace.domain.models import AssuranceDimensions, Control
from src.ace.domain.trace import (
    AccountabilitySubjectType,
    AccountableRoleRecord,
    AcceptedPlanningTrace,
    AuditorRelationshipDecision,
    BindingObligationRecord,
    PlanningControlRecord,
    ProposedTraceRelationship,
    RiskRecord,
    TraceRelationshipType,
)
from src.ace.engine.approval import build_approved_assessment
from src.ace.engine.conclusion import (
    ConclusionApprovalBlockedError,
    build_accepted_evidence_to_conclusion,
)
from src.ace.engine.evaluator import evaluate_control
from src.ace.engine.tracing import build_accepted_planning_trace


def validated_copy(model: Any, **changes: object) -> Any:
    values = model.model_dump()
    values.update(changes)
    return type(model).model_validate(values)


def unvalidated_copy(model: Any, **changes: object) -> Any:
    values = model.model_dump()
    values.update(changes)
    return type(model).model_construct(**values)


def make_question(
    question_type: AuditQuestionType,
    *,
    question_id: str | None = None,
    version: int = 1,
    control_id: str = "ACE-FICTIONAL-001",
) -> ProposedAuditQuestion:
    selected_id = question_id or f"AQ-{question_type.value}-001"
    if question_type is AuditQuestionType.MAIN:
        parent_id = None
        conclusion_type = None
        wording = (
            "Has the fictional mobilisation control been implemented "
            "and operated effectively?"
        )
    elif question_type is AuditQuestionType.IMPLEMENTATION:
        parent_id = "AQ-MAIN-001"
        conclusion_type = ConclusionType.IMPLEMENTATION
        wording = (
            "What evidence shows that the fictional control was put "
            "into practice?"
        )
    else:
        parent_id = "AQ-MAIN-001"
        conclusion_type = ConclusionType.EFFECTIVENESS
        wording = (
            "What evidence shows that the fictional implemented control "
            "achieved its intended result?"
        )
    return ProposedAuditQuestion(
        question_id=selected_id,
        question_version=version,
        question_type=question_type,
        wording=wording,
        purpose=f"Fictional purpose for {question_type.value}.",
        control_id=control_id,
        parent_question_id=parent_id,
        required_conclusion_type=conclusion_type,
    )


def make_question_decision(
    question: ProposedAuditQuestion,
    *,
    status: AuditorDecisionStatus = AuditorDecisionStatus.APPROVED,
) -> AuditorQuestionDecision:
    return AuditorQuestionDecision(
        decision_id=f"QDEC-{question.question_type.value}-001",
        question_id=question.question_id,
        question_version=question.question_version,
        question_type=question.question_type,
        decision_status=status,
        reviewer_id="FICTIONAL-AUDITOR-01",
        review_notes=f"Fictional review of {question.question_type.value}.",
        reviewed_at="2026-07-28T02:03:04.567890+00:00",
    )


def make_evidence(
    evidence_id: str,
    *,
    origin: EvidenceOrigin = EvidenceOrigin.RAW,
    freshness: EvidenceFreshness = EvidenceFreshness.CURRENT,
    source_evidence_ids: tuple[str, ...] = (),
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        title=f"Fictional evidence {evidence_id}",
        description=f"Fictional description for {evidence_id}.",
        origin=origin,
        source_title_or_originator="Fictional mobilisation register",
        source_version_or_date="Version 1.0",
        source_location=f"Entry {evidence_id}",
        collected_at="2026-07-28T03:04:05+00:00",
        valid_from="2026-07-01T00:00:00+00:00",
        valid_until="2026-08-01T00:00:00+00:00",
        freshness=freshness,
        source_evidence_ids=source_evidence_ids,
    )


def make_entry(
    entry_id: str,
    question_id: str,
    evidence_id: str,
    relevance: EvidenceRelevance = EvidenceRelevance.SUPPORTS,
) -> EvidenceMatrixEntry:
    return EvidenceMatrixEntry(
        entry_id=entry_id,
        question_id=question_id,
        evidence_id=evidence_id,
        relevance=relevance,
        rationale=f"Fictional relevance rationale for {evidence_id}.",
        reviewer_limitations=("Fictional pilot evidence only.",),
    )


def make_gap(
    gap_id: str,
    question_id: str,
    *,
    status: EvidenceGapStatus = EvidenceGapStatus.REQUESTED_NOT_PROVIDED,
    material: bool = True,
    disposition: EvidenceGapDisposition = EvidenceGapDisposition.OPEN,
) -> EvidenceGap:
    return EvidenceGap(
        gap_id=gap_id,
        question_id=question_id,
        status=status,
        description=f"Fictional evidence gap {gap_id}.",
        is_material=material,
        materiality_rationale=f"Fictional materiality rationale for {gap_id}.",
        disposition=disposition,
        disposition_rationale=(
            None
            if disposition is EvidenceGapDisposition.OPEN
            else f"Fictional disposition rationale for {gap_id}."
        ),
    )


def test_question_vocabulary_is_stable() -> None:
    assert [value.value for value in AuditQuestionType] == [
        "MAIN",
        "IMPLEMENTATION",
        "EFFECTIVENESS",
    ]
    assert [value.value for value in ConclusionType] == [
        "IMPLEMENTATION",
        "EFFECTIVENESS",
    ]


@pytest.mark.parametrize("version", [0, -1, "1"])
def test_question_version_is_a_positive_strict_integer(version: object) -> None:
    with pytest.raises(ValidationError):
        make_question(AuditQuestionType.MAIN, version=version)


def test_main_question_rejects_a_parent() -> None:
    question = make_question(AuditQuestionType.MAIN)
    with pytest.raises(
        ValidationError,
        match="main question must not have a parent",
    ):
        validated_copy(question, parent_question_id="AQ-OTHER")


def test_main_question_rejects_a_required_conclusion_type() -> None:
    question = make_question(AuditQuestionType.MAIN)
    with pytest.raises(
        ValidationError,
        match="main question must not require one conclusion type",
    ):
        validated_copy(
            question,
            required_conclusion_type=ConclusionType.IMPLEMENTATION,
        )


@pytest.mark.parametrize(
    ("question_type", "expected_conclusion"),
    [
        (AuditQuestionType.IMPLEMENTATION, ConclusionType.IMPLEMENTATION),
        (AuditQuestionType.EFFECTIVENESS, ConclusionType.EFFECTIVENESS),
    ],
)
def test_sub_question_requires_parent_and_matching_conclusion_type(
    question_type: AuditQuestionType,
    expected_conclusion: ConclusionType,
) -> None:
    question = make_question(question_type)
    assert question.parent_question_id == "AQ-MAIN-001"
    assert question.required_conclusion_type is expected_conclusion

    with pytest.raises(ValidationError, match="sub-question requires a parent"):
        validated_copy(question, parent_question_id=None)

    wrong_conclusion = (
        ConclusionType.EFFECTIVENESS
        if expected_conclusion is ConclusionType.IMPLEMENTATION
        else ConclusionType.IMPLEMENTATION
    )
    with pytest.raises(
        ValidationError,
        match="sub-question conclusion type does not match",
    ):
        validated_copy(question, required_conclusion_type=wrong_conclusion)


@pytest.mark.parametrize(
    "timestamp",
    [
        "not-a-timestamp",
        "2026-07-28T02:03:04.567890",
        "2026-07-28T12:03:04.567890+10:00",
        "2026-07-28 02:03:04.567890+00:00",
        " 2026-07-28T02:03:04.567890+00:00",
        "2026-07-28T02:03:04.567890+00:00 ",
    ],
)
def test_question_decision_rejects_noncanonical_utc(timestamp: str) -> None:
    decision = make_question_decision(
        make_question(AuditQuestionType.MAIN)
    )
    with pytest.raises(ValidationError):
        validated_copy(decision, reviewed_at=timestamp)


def test_question_records_are_frozen() -> None:
    question = make_question(AuditQuestionType.MAIN)
    decision = make_question_decision(question)
    with pytest.raises(ValidationError):
        question.wording = "Changed"
    with pytest.raises(ValidationError):
        decision.decision_status = AuditorDecisionStatus.REJECTED


def test_evidence_vocabulary_is_stable() -> None:
    assert [value.value for value in EvidenceOrigin] == [
        "RAW",
        "DERIVED",
        "AUDITOR_AUTHORED",
    ]
    assert [value.value for value in EvidenceFreshness] == [
        "CURRENT",
        "STALE",
        "SUPERSEDED",
        "UNCERTAIN",
    ]
    assert [value.value for value in EvidenceRelevance] == [
        "SUPPORTS",
        "WEAKENS",
        "CONTRADICTS",
    ]


def test_raw_evidence_rejects_source_evidence_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="raw evidence must not identify source evidence",
    ):
        make_evidence(
            "EVID-RAW-001",
            source_evidence_ids=("EVID-OTHER",),
        )


def test_derived_evidence_requires_source_evidence_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="derived evidence requires raw source evidence",
    ):
        make_evidence("EVID-DERIVED-001", origin=EvidenceOrigin.DERIVED)


def test_evidence_rejects_reversed_validity_period() -> None:
    evidence = make_evidence("EVID-RAW-001")
    with pytest.raises(
        ValidationError,
        match="validity end must not precede validity start",
    ):
        validated_copy(
            evidence,
            valid_from="2026-08-02T00:00:00+00:00",
            valid_until="2026-08-01T00:00:00+00:00",
        )


@pytest.mark.parametrize(
    "disposition",
    [
        EvidenceGapDisposition.RESOLVED,
        EvidenceGapDisposition.ACCEPTED_LIMITATION,
    ],
)
def test_non_open_gap_requires_disposition_rationale(
    disposition: EvidenceGapDisposition,
) -> None:
    gap = make_gap(
        "GAP-IMP-001",
        "AQ-IMPLEMENTATION-001",
        disposition=disposition,
    )
    with pytest.raises(
        ValidationError,
        match="gap disposition requires a rationale",
    ):
        validated_copy(gap, disposition_rationale=None)


def test_matrix_requires_an_entry_or_explicit_gap() -> None:
    with pytest.raises(
        ValidationError,
        match="matrix review requires evidence or an explicit gap",
    ):
        EvidenceMatrixReview(
            review_id="MATRIX-IMP-001",
            question_id="AQ-IMPLEMENTATION-001",
            entries=(),
            gaps=(),
            contradiction_status=(
                ConclusionContradictionStatus.NONE_IDENTIFIED
            ),
            contradiction_evidence_ids=(),
            contradiction_explanation=None,
            assumptions=(),
            limitations=("No fictional evidence was supplied.",),
            proposed_sufficiency=(
                ConclusionEvidenceSufficiency.INSUFFICIENT
            ),
        )


def test_explained_contradiction_requires_unique_evidence_and_explanation() -> None:
    entry = make_entry(
        "ENTRY-IMP-001",
        "AQ-IMPLEMENTATION-001",
        "EVID-RAW-001",
    )
    with pytest.raises(ValidationError):
        EvidenceMatrixReview(
            review_id="MATRIX-IMP-001",
            question_id="AQ-IMPLEMENTATION-001",
            entries=(entry,),
            gaps=(),
            contradiction_status=ConclusionContradictionStatus.EXPLAINED,
            contradiction_evidence_ids=("EVID-RAW-001",),
            contradiction_explanation=None,
            assumptions=(),
            limitations=(),
            proposed_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
        )


def test_evidence_records_are_frozen() -> None:
    evidence = make_evidence("EVID-RAW-001")
    with pytest.raises(ValidationError):
        evidence.freshness = EvidenceFreshness.STALE


from src.ace.domain.conclusion import (
    AcceptedEvidenceToConclusionRecord,
    AuditorConclusionDecision,
    EffectivenessConclusion,
    ImplementationConclusion,
    ProposedEffectivenessConclusion,
    ProposedImplementationConclusion,
)
from src.ace.domain.trace import AcceptedPlanningTrace


def make_implementation_proposal(
    *,
    outcome: ImplementationConclusion = (
        ImplementationConclusion.IMPLEMENTED
    ),
    relied_upon_evidence_ids: tuple[str, ...] = ("EVID-IMP-RAW-001",),
    considered_gap_ids: tuple[str, ...] = (),
) -> ProposedImplementationConclusion:
    return ProposedImplementationConclusion(
        proposal_id="CONC-IMP-001",
        proposal_version=1,
        question_id="AQ-IMPLEMENTATION-001",
        proposed_outcome=outcome,
        evidence_review_id="MATRIX-IMP-001",
        relied_upon_evidence_ids=relied_upon_evidence_ids,
        considered_gap_ids=considered_gap_ids,
        reasoning="Fictional implementation reasoning.",
        assumptions=("The fictional register is complete.",),
        limitations=("Fictional pilot evidence only.",),
    )


def make_effectiveness_proposal(
    *,
    outcome: EffectivenessConclusion = EffectivenessConclusion.EFFECTIVE,
    relied_upon_evidence_ids: tuple[str, ...] = ("EVID-EFF-RAW-001",),
    considered_gap_ids: tuple[str, ...] = (),
) -> ProposedEffectivenessConclusion:
    return ProposedEffectivenessConclusion(
        proposal_id="CONC-EFF-001",
        proposal_version=1,
        question_id="AQ-EFFECTIVENESS-001",
        proposed_outcome=outcome,
        evidence_review_id="MATRIX-EFF-001",
        relied_upon_evidence_ids=relied_upon_evidence_ids,
        considered_gap_ids=considered_gap_ids,
        reasoning="Fictional effectiveness reasoning.",
        assumptions=("The fictional outcome measure is relevant.",),
        limitations=("Fictional pilot evidence only.",),
    )


def make_conclusion_decision(
    proposal: (
        ProposedImplementationConclusion
        | ProposedEffectivenessConclusion
    ),
    *,
    status: AuditorDecisionStatus = AuditorDecisionStatus.APPROVED,
    final_sufficiency: ConclusionEvidenceSufficiency = (
        ConclusionEvidenceSufficiency.SUFFICIENT
    ),
) -> AuditorConclusionDecision:
    is_implementation = isinstance(
        proposal,
        ProposedImplementationConclusion,
    )
    return AuditorConclusionDecision(
        decision_id=(
            "CDEC-IMP-001" if is_implementation else "CDEC-EFF-001"
        ),
        proposal_id=proposal.proposal_id,
        proposal_version=proposal.proposal_version,
        conclusion_type=(
            ConclusionType.IMPLEMENTATION
            if is_implementation
            else ConclusionType.EFFECTIVENESS
        ),
        decision_status=status,
        approved_outcome=(
            proposal.proposed_outcome
            if status is AuditorDecisionStatus.APPROVED
            else None
        ),
        final_sufficiency=final_sufficiency,
        reviewer_id="FICTIONAL-AUDITOR-01",
        review_notes="Fictional conclusion review.",
        reviewed_at="2026-07-28T04:05:06+00:00",
    )


def test_conclusion_vocabularies_are_stable() -> None:
    assert [value.value for value in ImplementationConclusion] == [
        "IMPLEMENTED",
        "PARTIALLY_IMPLEMENTED",
        "NOT_IMPLEMENTED",
        "NOT_DETERMINED",
    ]
    assert [value.value for value in EffectivenessConclusion] == [
        "EFFECTIVE",
        "PARTIALLY_EFFECTIVE",
        "INEFFECTIVE",
        "NOT_DETERMINED",
    ]


def test_effectiveness_not_determined_round_trips_as_effectiveness() -> None:
    decision = make_conclusion_decision(
        make_effectiveness_proposal(
            outcome=EffectivenessConclusion.NOT_DETERMINED,
            relied_upon_evidence_ids=(),
            considered_gap_ids=("GAP-EFF-001",),
        ),
        final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
    )

    round_tripped = AuditorConclusionDecision.model_validate_json(
        decision.model_dump_json()
    )

    assert round_tripped.approved_outcome is EffectivenessConclusion.NOT_DETERMINED


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-07-28T04:05:06",
        "2026-07-28T14:05:06+10:00",
        " 2026-07-28T04:05:06+00:00",
    ],
)
def test_conclusion_decision_rejects_noncanonical_utc(timestamp: str) -> None:
    with pytest.raises(ValidationError):
        validated_copy(
            make_conclusion_decision(make_implementation_proposal()),
            reviewed_at=timestamp,
        )


def test_proposal_rejects_duplicate_relied_upon_evidence_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="relied-upon evidence IDs must be unique",
    ):
        make_implementation_proposal(
            relied_upon_evidence_ids=("EVID-IMP-RAW-001", "EVID-IMP-RAW-001")
        )


def test_proposal_rejects_duplicate_considered_gap_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="considered gap IDs must be unique",
    ):
        make_effectiveness_proposal(
            considered_gap_ids=("GAP-EFF-001", "GAP-EFF-001")
        )


def test_matrix_rejects_duplicate_evidence_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="matrix evidence IDs must be unique",
    ):
        EvidenceMatrixReview(
            review_id="MATRIX-IMP-001",
            question_id="AQ-IMPLEMENTATION-001",
            entries=(
                make_entry(
                    "ENTRY-IMP-001",
                    "AQ-IMPLEMENTATION-001",
                    "EVID-IMP-RAW-001",
                ),
                make_entry(
                    "ENTRY-IMP-002",
                    "AQ-IMPLEMENTATION-001",
                    "EVID-IMP-RAW-001",
                ),
            ),
            gaps=(),
            contradiction_status=ConclusionContradictionStatus.NONE_IDENTIFIED,
            contradiction_evidence_ids=(),
            contradiction_explanation=None,
            assumptions=(),
            limitations=(),
            proposed_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
        )


@pytest.mark.parametrize(
    ("proposal", "outcome", "message"),
    [
        (
            make_implementation_proposal(),
            EffectivenessConclusion.EFFECTIVE,
            "implementation decision requires an implementation outcome",
        ),
        (
            make_effectiveness_proposal(),
            ImplementationConclusion.IMPLEMENTED,
            "effectiveness decision requires an effectiveness outcome",
        ),
    ],
)
def test_conclusion_decision_rejects_an_outcome_of_the_wrong_type(
    proposal: ProposedImplementationConclusion | ProposedEffectivenessConclusion,
    outcome: ImplementationConclusion | EffectivenessConclusion,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        validated_copy(
            make_conclusion_decision(proposal),
            approved_outcome=outcome,
        )


def make_accepted_record() -> AcceptedEvidenceToConclusionRecord:
    main_question = make_question(AuditQuestionType.MAIN)
    implementation_question = make_question(AuditQuestionType.IMPLEMENTATION)
    effectiveness_question = make_question(AuditQuestionType.EFFECTIVENESS)
    questions = (
        main_question,
        implementation_question,
        effectiveness_question,
    )
    question_decisions = tuple(
        make_question_decision(question) for question in questions
    )
    implementation_proposal = make_implementation_proposal()
    effectiveness_proposal = make_effectiveness_proposal()
    conclusion_decisions = (
        make_conclusion_decision(implementation_proposal),
        make_conclusion_decision(effectiveness_proposal),
    )
    evidence_items = (
        make_evidence("EVID-IMP-RAW-001"),
        make_evidence("EVID-EFF-RAW-001"),
    )
    evidence_reviews = (
        EvidenceMatrixReview(
            review_id="MATRIX-IMP-001",
            question_id=implementation_question.question_id,
            entries=(
                make_entry(
                    "ENTRY-IMP-001",
                    implementation_question.question_id,
                    evidence_items[0].evidence_id,
                ),
            ),
            gaps=(),
            contradiction_status=ConclusionContradictionStatus.NONE_IDENTIFIED,
            contradiction_evidence_ids=(),
            contradiction_explanation=None,
            assumptions=(),
            limitations=(),
            proposed_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
        ),
        EvidenceMatrixReview(
            review_id="MATRIX-EFF-001",
            question_id=effectiveness_question.question_id,
            entries=(
                make_entry(
                    "ENTRY-EFF-001",
                    effectiveness_question.question_id,
                    evidence_items[1].evidence_id,
                ),
            ),
            gaps=(),
            contradiction_status=ConclusionContradictionStatus.NONE_IDENTIFIED,
            contradiction_evidence_ids=(),
            contradiction_explanation=None,
            assumptions=(),
            limitations=(),
            proposed_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
        ),
    )
    return AcceptedEvidenceToConclusionRecord._from_approved_gate(
        planning_trace=AcceptedPlanningTrace.model_construct(),
        questions=questions,
        question_decisions=question_decisions,
        evidence_items=evidence_items,
        evidence_reviews=evidence_reviews,
        implementation_proposal=implementation_proposal,
        effectiveness_proposal=effectiveness_proposal,
        conclusion_decisions=conclusion_decisions,
        question_decision_ids=tuple(
            decision.decision_id for decision in question_decisions
        ),
        conclusion_decision_ids=tuple(
            decision.decision_id for decision in conclusion_decisions
        ),
        implementation_outcome=implementation_proposal.proposed_outcome,
        effectiveness_outcome=effectiveness_proposal.proposed_outcome,
    )


def test_accepted_record_requires_gate_construction_and_is_frozen() -> None:
    record = make_accepted_record()
    values = dict(record)

    with pytest.raises(
        ValidationError,
        match="accepted evidence-to-conclusion record must be built by the approval gate",
    ):
        AcceptedEvidenceToConclusionRecord(**values)

    with pytest.raises(
        ValidationError,
        match="accepted evidence-to-conclusion record must be built by the approval gate",
    ):
        AcceptedEvidenceToConclusionRecord.model_validate(values)

    with pytest.raises(ValidationError):
        record.implementation_outcome = ImplementationConclusion.NOT_DETERMINED


def test_non_approved_decision_rejects_an_approved_outcome() -> None:
    proposal = make_implementation_proposal()
    decision = make_conclusion_decision(proposal)
    with pytest.raises(
        ValidationError,
        match="non-approved decision must not contain an approved outcome",
    ):
        validated_copy(
            decision,
            decision_status=AuditorDecisionStatus.CHANGES_REQUIRED,
        )


def test_not_determined_decision_rejects_sufficient_final_evidence() -> None:
    proposal = make_implementation_proposal(
        outcome=ImplementationConclusion.NOT_DETERMINED,
        relied_upon_evidence_ids=(),
        considered_gap_ids=("GAP-IMP-001",),
    )
    with pytest.raises(
        ValidationError,
        match="not determined requires insufficient or unresolved evidence",
    ):
        make_conclusion_decision(
            proposal,
            final_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
        )


def test_substantive_decision_requires_sufficient_evidence() -> None:
    proposal = make_effectiveness_proposal()
    with pytest.raises(
        ValidationError,
        match="substantive conclusion requires sufficient evidence",
    ):
        make_conclusion_decision(
            proposal,
            final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
        )


def make_trace_source(source_id: str) -> SourceReference:
    return SourceReference(
        source_id=source_id,
        document_title=f"Fictional document for {source_id}",
        document_version="1.0",
        source_location=f"Section {source_id}",
        source_wording=f"Fictional source wording for {source_id}.",
        status=SourceStatus.CURRENT,
    )


def make_accepted_trace() -> AcceptedPlanningTrace:
    mate_proposals = []
    mate_reviews = []
    mate_decisions = []
    for dimension in MateDimension:
        source = make_trace_source(f"SRC-MATE-{dimension.value}")
        review = EvidenceReviewRecord(
            review_id=f"REV-MATE-{dimension.value}",
            source_references=(source,),
            supporting_source_ids=(source.source_id,),
            weakening_source_ids=(),
            contradictory_source_ids=(),
            evidence_availability=(EvidenceAvailability.REVIEWED_SUPPORTIVE,),
            contradiction_status=ContradictionStatus.NONE_IDENTIFIED,
            contradiction_explanation=None,
            assumptions_checked=("The fictional source is current.",),
            limitations=("Control-design assessment only.",),
            proposed_sufficiency=(
                EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
            ),
        )
        proposal = ProposedDimensionAssessment(
            proposal_id=f"PROP-MATE-{dimension.value}",
            proposal_version=1,
            dimension=dimension,
            proposed_answer=ProposedAnswer.YES,
            rationale=f"Fictional MATE rationale for {dimension.label}.",
            evidence_review_id=review.review_id,
        )
        decision = AuditorDecision(
            decision_id=f"DEC-MATE-{dimension.value}",
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.proposal_version,
            dimension=dimension,
            decision_status=AuditorDecisionStatus.APPROVED,
            approved_answer=True,
            final_sufficiency=(
                EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
            ),
            reviewer_id="FICTIONAL-MATE-AUDITOR",
            review_notes=f"Fictional approval for {dimension.label}.",
            reviewed_at="2026-07-28T01:02:03+00:00",
        )
        mate_reviews.append(review)
        mate_proposals.append(proposal)
        mate_decisions.append(decision)

    mate = build_approved_assessment(
        control_id="ACE-FICTIONAL-001",
        title="Fictional mobilisation approval control",
        description="Fictional control-design assessment for Sprint 4.",
        hazard_category=HazardCategory.GOVERNANCE_OVERSIGHT,
        proposals=tuple(mate_proposals),
        evidence_reviews=tuple(mate_reviews),
        decisions=tuple(mate_decisions),
        reviewer_notes="Fictional Sprint 4 MATE input.",
    )
    obligation = BindingObligationRecord(
        obligation_id="OBL-FICTIONAL-001",
        title="Fictional mobilisation obligation",
        binding_instrument="Fictional Safety Management Policy",
        clause="Clause 4.1",
        obligation_text=(
            "A fictional mobilisation control must be approved before work starts."
        ),
        source_reference=make_trace_source("SRC-OBLIGATION"),
    )
    risk = RiskRecord(
        risk_id="RISK-FICTIONAL-001",
        title="Fictional uncontrolled mobilisation risk",
        risk_statement="Work may start without fictional governance approval.",
        source_reference=make_trace_source("SRC-RISK"),
    )
    control = PlanningControlRecord(
        control_id="ACE-FICTIONAL-001",
        title="Fictional mobilisation approval control",
        design_statement=(
            "The fictional accountable role approves mobilisation before work starts."
        ),
        source_reference=make_trace_source("SRC-CONTROL"),
    )
    role = AccountableRoleRecord(
        accountability_id="ROLE-FICTIONAL-001",
        subject_type=AccountabilitySubjectType.JOB_ROLE,
        subject_title="Fictional Head of Safety",
        accountability_statement=(
            "The fictional role is accountable for the mobilisation control."
        ),
        source_reference=make_trace_source("SRC-ROLE"),
    )
    relationship_specs = (
        (TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK, obligation.obligation_id, risk.risk_id, (obligation.source_reference.source_id, risk.source_reference.source_id)),
        (TraceRelationshipType.CONTROL_TREATS_RISK, control.control_id, risk.risk_id, (control.source_reference.source_id, risk.source_reference.source_id)),
        (TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL, role.accountability_id, control.control_id, (role.source_reference.source_id, control.source_reference.source_id)),
        (TraceRelationshipType.CONTROL_HAS_APPROVED_MATE_ASSESSMENT, control.control_id, f"MATE:{mate.control_id}", (control.source_reference.source_id,)),
    )
    relationships = tuple(
        ProposedTraceRelationship(
            relationship_id=f"REL-{relationship_type.value}",
            relationship_version=1,
            relationship_type=relationship_type,
            source_record_id=source_id,
            target_record_id=target_id,
            supporting_source_ids=supporting_ids,
            rationale=f"Fictional rationale for {relationship_type.value}.",
        )
        for relationship_type, source_id, target_id, supporting_ids in relationship_specs
    )
    relationship_decisions = tuple(
        AuditorRelationshipDecision(
            decision_id=f"DEC-{relationship.relationship_type.value}",
            relationship_id=relationship.relationship_id,
            relationship_version=relationship.relationship_version,
            relationship_type=relationship.relationship_type,
            decision_status=AuditorDecisionStatus.APPROVED,
            reviewer_id="FICTIONAL-AUDITOR-01",
            review_notes=f"Fictional approval for {relationship.relationship_type.value}.",
            reviewed_at="2026-07-28T01:02:03+00:00",
        )
        for relationship in relationships
    )
    return build_accepted_planning_trace(
        obligation=obligation,
        risk=risk,
        control=control,
        accountable_role=role,
        relationships=relationships,
        decisions=relationship_decisions,
        mate_assessment=mate,
    )


def make_complete_bundle() -> dict[str, object]:
    accepted_trace = make_accepted_trace()
    main_question = make_question(AuditQuestionType.MAIN)
    implementation_question = make_question(AuditQuestionType.IMPLEMENTATION)
    effectiveness_question = make_question(AuditQuestionType.EFFECTIVENESS)
    questions = (main_question, implementation_question, effectiveness_question)
    question_decisions = tuple(
        make_question_decision(question) for question in questions
    )
    implementation_raw = make_evidence("EVID-IMP-RAW-001")
    implementation_derived = make_evidence(
        "EVID-IMP-DERIVED-001",
        origin=EvidenceOrigin.DERIVED,
        source_evidence_ids=(implementation_raw.evidence_id,),
    )
    effectiveness_raw = make_evidence("EVID-EFF-RAW-001")
    effectiveness_auditor_authored = make_evidence(
        "EVID-EFF-AUDITOR-001",
        origin=EvidenceOrigin.AUDITOR_AUTHORED,
        source_evidence_ids=(effectiveness_raw.evidence_id,),
    )
    evidence_items = (
        implementation_raw,
        implementation_derived,
        effectiveness_raw,
        effectiveness_auditor_authored,
    )
    implementation_matrix = EvidenceMatrixReview(
        review_id="MATRIX-IMP-001",
        question_id=implementation_question.question_id,
        entries=(
            make_entry("ENTRY-IMP-RAW-001", implementation_question.question_id, implementation_raw.evidence_id),
            make_entry("ENTRY-IMP-DERIVED-001", implementation_question.question_id, implementation_derived.evidence_id),
        ),
        gaps=(),
        contradiction_status=ConclusionContradictionStatus.NONE_IDENTIFIED,
        contradiction_evidence_ids=(),
        contradiction_explanation=None,
        assumptions=("The fictional implementation register is complete.",),
        limitations=("Fictional pilot evidence only.",),
        proposed_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
    )
    effectiveness_matrix = EvidenceMatrixReview(
        review_id="MATRIX-EFF-001",
        question_id=effectiveness_question.question_id,
        entries=(
            make_entry("ENTRY-EFF-RAW-001", effectiveness_question.question_id, effectiveness_raw.evidence_id),
            make_entry("ENTRY-EFF-AUDITOR-001", effectiveness_question.question_id, effectiveness_auditor_authored.evidence_id),
        ),
        gaps=(),
        contradiction_status=ConclusionContradictionStatus.NONE_IDENTIFIED,
        contradiction_evidence_ids=(),
        contradiction_explanation=None,
        assumptions=("The fictional outcome measure is relevant.",),
        limitations=("Fictional pilot evidence only.",),
        proposed_sufficiency=ConclusionEvidenceSufficiency.SUFFICIENT,
    )
    implementation_proposal = make_implementation_proposal()
    effectiveness_proposal = make_effectiveness_proposal()
    implementation_decision = make_conclusion_decision(implementation_proposal)
    effectiveness_decision = make_conclusion_decision(effectiveness_proposal)
    return {
        "planning_trace": accepted_trace,
        "questions": questions,
        "question_decisions": question_decisions,
        "evidence_items": evidence_items,
        "evidence_reviews": (implementation_matrix, effectiveness_matrix),
        "implementation_proposal": implementation_proposal,
        "effectiveness_proposal": effectiveness_proposal,
        "conclusion_decisions": (implementation_decision, effectiveness_decision),
    }


def build_record(**changes: object) -> AcceptedEvidenceToConclusionRecord:
    bundle = make_complete_bundle()
    bundle.update(changes)
    return build_accepted_evidence_to_conclusion(**bundle)


def assert_bundle_is_blocked(
    bundle: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ConclusionApprovalBlockedError, match=message):
        build_accepted_evidence_to_conclusion(**bundle)


def test_gate_blocks_an_extra_question() -> None:
    bundle = make_complete_bundle()
    bundle["questions"] = (
        *bundle["questions"],
        make_question(AuditQuestionType.MAIN, question_id="AQ-MAIN-002"),
    )

    assert_bundle_is_blocked(bundle, "expected exactly 3 questions")


def test_gate_blocks_an_extra_question_decision() -> None:
    bundle = make_complete_bundle()
    decision = validated_copy(
        bundle["question_decisions"][0],
        decision_id="QDEC-MAIN-002",
    )
    bundle["question_decisions"] = (*bundle["question_decisions"], decision)

    assert_bundle_is_blocked(bundle, "expected exactly 3 question decisions")


def test_gate_blocks_an_extra_evidence_review() -> None:
    bundle = make_complete_bundle()
    review = validated_copy(
        bundle["evidence_reviews"][0],
        review_id="MATRIX-IMP-002",
    )
    bundle["evidence_reviews"] = (*bundle["evidence_reviews"], review)

    assert_bundle_is_blocked(bundle, "expected exactly 2 evidence reviews")


def test_gate_blocks_an_extra_conclusion_decision() -> None:
    bundle = make_complete_bundle()
    decision = validated_copy(
        bundle["conclusion_decisions"][0],
        decision_id="CDEC-IMP-002",
    )
    bundle["conclusion_decisions"] = (*bundle["conclusion_decisions"], decision)

    assert_bundle_is_blocked(bundle, "expected exactly 2 conclusion decisions")


def test_gate_blocks_a_missing_question_type() -> None:
    bundle = make_complete_bundle()
    bundle["questions"] = bundle["questions"][:-1]
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="Effectiveness question is missing",
    ):
        build_accepted_evidence_to_conclusion(**bundle)


def test_gate_blocks_a_wrong_sub_question_parent() -> None:
    bundle = make_complete_bundle()
    questions = list(bundle["questions"])
    questions[1] = validated_copy(
        questions[1],
        parent_question_id="AQ-WRONG-001",
    )
    bundle["questions"] = tuple(questions)
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="implementation question does not identify the main question",
    ):
        build_accepted_evidence_to_conclusion(**bundle)


def test_gate_blocks_a_different_control() -> None:
    bundle = make_complete_bundle()
    questions = list(bundle["questions"])
    questions[2] = validated_copy(
        questions[2],
        control_id="ACE-OTHER-001",
    )
    bundle["questions"] = tuple(questions)
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="concerns a different control",
    ):
        build_accepted_evidence_to_conclusion(**bundle)


def test_gate_blocks_a_duplicate_question_id() -> None:
    bundle = make_complete_bundle()
    questions = list(bundle["questions"])
    questions[2] = validated_copy(
        questions[2],
        question_id="AQ-IMPLEMENTATION-001",
        question_version=2,
    )
    bundle["questions"] = tuple(questions)

    assert_bundle_is_blocked(
        bundle,
        "question identifier AQ-IMPLEMENTATION-001 appears more than once",
    )


def test_gate_blocks_a_duplicate_question_decision_id() -> None:
    bundle = make_complete_bundle()
    decisions = list(bundle["question_decisions"])
    decisions[2] = validated_copy(
        decisions[2],
        decision_id=decisions[1].decision_id,
    )
    bundle["question_decisions"] = tuple(decisions)

    assert_bundle_is_blocked(bundle, "question decision identifier")


def test_gate_blocks_a_missing_question_decision() -> None:
    bundle = make_complete_bundle()
    bundle["question_decisions"] = bundle["question_decisions"][:-1]

    assert_bundle_is_blocked(bundle, "Effectiveness question decision is missing")


def test_gate_blocks_a_question_decision_version_mismatch() -> None:
    bundle = make_complete_bundle()
    decisions = list(bundle["question_decisions"])
    decisions[1] = validated_copy(decisions[1], question_version=2)
    bundle["question_decisions"] = tuple(decisions)

    assert_bundle_is_blocked(
        bundle,
        "Implementation question decision version does not match",
    )


def test_gate_blocks_a_question_decision_type_mismatch() -> None:
    bundle = make_complete_bundle()
    decisions = list(bundle["question_decisions"])
    decisions[1] = validated_copy(
        decisions[1],
        question_type=AuditQuestionType.EFFECTIVENESS,
    )
    bundle["question_decisions"] = tuple(decisions)

    assert_bundle_is_blocked(
        bundle,
        "Implementation question decision type does not match",
    )


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (AuditorDecisionStatus.REJECTED, "Implementation question has been rejected"),
        (
            AuditorDecisionStatus.CHANGES_REQUIRED,
            "Implementation question requires changes",
        ),
    ],
)
def test_gate_blocks_an_unapproved_question(
    status: AuditorDecisionStatus,
    message: str,
) -> None:
    bundle = make_complete_bundle()
    decisions = list(bundle["question_decisions"])
    decisions[1] = validated_copy(decisions[1], decision_status=status)
    bundle["question_decisions"] = tuple(decisions)

    assert_bundle_is_blocked(bundle, message)


def test_gate_blocks_a_duplicate_evidence_id() -> None:
    bundle = make_complete_bundle()
    items = list(bundle["evidence_items"])
    items[2] = validated_copy(items[2], evidence_id="EVID-IMP-RAW-001")
    bundle["evidence_items"] = tuple(items)

    assert_bundle_is_blocked(
        bundle,
        "evidence identifier EVID-IMP-RAW-001 appears more than once",
    )


@pytest.mark.parametrize(
    ("item_index", "source_ids", "message"),
    [
        (
            1,
            ("EVID-MISSING",),
            "derived evidence EVID-IMP-DERIVED-001 source EVID-MISSING is missing",
        ),
        (
            1,
            ("EVID-EFF-AUDITOR-001",),
            "must resolve to raw evidence",
        ),
        (
            3,
            ("EVID-MISSING",),
            "auditor-authored evidence EVID-EFF-AUDITOR-001 source EVID-MISSING is missing",
        ),
    ],
)
def test_gate_blocks_invalid_evidence_provenance(
    item_index: int,
    source_ids: tuple[str, ...],
    message: str,
) -> None:
    bundle = make_complete_bundle()
    items = list(bundle["evidence_items"])
    items[item_index] = validated_copy(
        items[item_index],
        source_evidence_ids=source_ids,
    )
    bundle["evidence_items"] = tuple(items)

    assert_bundle_is_blocked(bundle, message)


def test_gate_blocks_a_missing_implementation_matrix() -> None:
    bundle = make_complete_bundle()
    bundle["evidence_reviews"] = bundle["evidence_reviews"][1:]

    assert_bundle_is_blocked(bundle, "implementation evidence matrix is missing")


def test_gate_blocks_a_duplicate_review_id() -> None:
    bundle = make_complete_bundle()
    reviews = list(bundle["evidence_reviews"])
    reviews[1] = validated_copy(reviews[1], review_id="MATRIX-IMP-001")
    bundle["evidence_reviews"] = tuple(reviews)

    assert_bundle_is_blocked(
        bundle,
        "evidence review identifier MATRIX-IMP-001 appears more than once",
    )


def test_gate_blocks_duplicate_entry_ids_across_matrices() -> None:
    bundle = make_complete_bundle()
    reviews = list(bundle["evidence_reviews"])
    entries = list(reviews[1].entries)
    entries[0] = validated_copy(entries[0], entry_id="ENTRY-IMP-RAW-001")
    reviews[1] = validated_copy(reviews[1], entries=tuple(entries))
    bundle["evidence_reviews"] = tuple(reviews)

    assert_bundle_is_blocked(
        bundle,
        "matrix entry identifier ENTRY-IMP-RAW-001 appears more than once",
    )


def test_gate_blocks_duplicate_gap_ids_across_matrices() -> None:
    bundle = make_complete_bundle()
    reviews = list(bundle["evidence_reviews"])
    reviews[0] = validated_copy(
        reviews[0],
        gaps=(make_gap("GAP-SHARED-001", "AQ-IMPLEMENTATION-001"),),
    )
    reviews[1] = validated_copy(
        reviews[1],
        gaps=(make_gap("GAP-SHARED-001", "AQ-EFFECTIVENESS-001"),),
    )
    bundle["evidence_reviews"] = tuple(reviews)

    assert_bundle_is_blocked(
        bundle,
        "evidence gap identifier GAP-SHARED-001 appears more than once",
    )


def test_gate_blocks_an_entry_on_the_wrong_question() -> None:
    bundle = make_complete_bundle()
    reviews = list(bundle["evidence_reviews"])
    entries = list(reviews[0].entries)
    entries[0] = validated_copy(
        entries[0],
        question_id="AQ-EFFECTIVENESS-001",
    )
    reviews[0] = validated_copy(reviews[0], entries=tuple(entries))
    bundle["evidence_reviews"] = tuple(reviews)

    assert_bundle_is_blocked(
        bundle,
        "implementation matrix contains an entry for a different question",
    )


def test_gate_blocks_a_gap_on_the_wrong_question() -> None:
    bundle = make_complete_bundle()
    reviews = list(bundle["evidence_reviews"])
    reviews[0] = validated_copy(
        reviews[0],
        gaps=(make_gap("GAP-IMP-001", "AQ-EFFECTIVENESS-001"),),
    )
    bundle["evidence_reviews"] = tuple(reviews)

    assert_bundle_is_blocked(
        bundle,
        "implementation matrix contains a gap for a different question",
    )


def test_gate_blocks_missing_matrix_evidence() -> None:
    bundle = make_complete_bundle()
    reviews = list(bundle["evidence_reviews"])
    entries = list(reviews[0].entries)
    entries[0] = validated_copy(entries[0], evidence_id="EVID-MISSING")
    reviews[0] = validated_copy(reviews[0], entries=tuple(entries))
    bundle["evidence_reviews"] = tuple(reviews)

    assert_bundle_is_blocked(bundle, "matrix evidence EVID-MISSING is missing")


def test_gate_blocks_missing_contradiction_evidence() -> None:
    bundle = make_complete_bundle()
    reviews = list(bundle["evidence_reviews"])
    reviews[0] = validated_copy(
        reviews[0],
        contradiction_status=ConclusionContradictionStatus.UNRESOLVED,
        contradiction_evidence_ids=("EVID-IMP-RAW-001", "EVID-MISSING"),
        contradiction_explanation="Fictional unresolved contradiction.",
    )
    bundle["evidence_reviews"] = tuple(reviews)

    assert_bundle_is_blocked(
        bundle,
        "contradiction evidence EVID-MISSING is missing",
    )


@pytest.mark.parametrize(
    ("evidence_ids", "message"),
    [
        ("EVID-MISSING", "relied-upon evidence EVID-MISSING is missing"),
        (
            "EVID-EFF-RAW-001",
            "is not in the implementation evidence matrix",
        ),
    ],
)
def test_gate_blocks_invalid_relied_upon_evidence(
    evidence_ids: str,
    message: str,
) -> None:
    bundle = make_complete_bundle()
    bundle["implementation_proposal"] = validated_copy(
        bundle["implementation_proposal"],
        relied_upon_evidence_ids=(evidence_ids,),
    )

    assert_bundle_is_blocked(bundle, message)


def test_gate_blocks_an_omitted_matrix_gap() -> None:
    bundle = make_complete_bundle()
    reviews = list(bundle["evidence_reviews"])
    reviews[0] = validated_copy(
        reviews[0],
        gaps=(make_gap("GAP-IMP-001", "AQ-IMPLEMENTATION-001"),),
    )
    bundle["evidence_reviews"] = tuple(reviews)

    assert_bundle_is_blocked(
        bundle,
        "implementation conclusion does not consider every evidence gap",
    )


def test_substantive_conclusion_requires_current_evidence() -> None:
    bundle = make_complete_bundle()
    evidence_items = tuple(
        validated_copy(item, freshness=EvidenceFreshness.STALE)
        if item.evidence_id == "EVID-IMP-RAW-001"
        else item
        for item in bundle["evidence_items"]
    )
    bundle["evidence_items"] = evidence_items
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="implementation conclusion has no current relied-upon evidence",
    ):
        build_accepted_evidence_to_conclusion(**bundle)


def test_gate_blocks_an_implementation_proposal_on_the_wrong_question() -> None:
    bundle = make_complete_bundle()
    bundle["implementation_proposal"] = validated_copy(
        bundle["implementation_proposal"],
        question_id="AQ-EFFECTIVENESS-001",
    )

    assert_bundle_is_blocked(
        bundle,
        "implementation proposal refers to the wrong question",
    )


def test_gate_blocks_an_effectiveness_proposal_on_the_wrong_matrix() -> None:
    bundle = make_complete_bundle()
    bundle["effectiveness_proposal"] = validated_copy(
        bundle["effectiveness_proposal"],
        evidence_review_id="MATRIX-IMP-001",
    )

    assert_bundle_is_blocked(
        bundle,
        "effectiveness proposal refers to the wrong evidence matrix",
    )


def test_gate_blocks_a_duplicate_proposal_identity() -> None:
    bundle = make_complete_bundle()
    bundle["effectiveness_proposal"] = validated_copy(
        bundle["effectiveness_proposal"],
        proposal_id="CONC-IMP-001",
        proposal_version=1,
    )

    assert_bundle_is_blocked(
        bundle,
        "conclusion proposal CONC-IMP-001 version 1 appears more than once",
    )


def test_gate_blocks_a_duplicate_conclusion_decision_id() -> None:
    bundle = make_complete_bundle()
    decisions = list(bundle["conclusion_decisions"])
    decisions[1] = validated_copy(decisions[1], decision_id="CDEC-IMP-001")
    bundle["conclusion_decisions"] = tuple(decisions)

    assert_bundle_is_blocked(
        bundle,
        "conclusion decision identifier CDEC-IMP-001 appears more than once",
    )


def test_gate_blocks_a_missing_conclusion_decision() -> None:
    bundle = make_complete_bundle()
    bundle["conclusion_decisions"] = bundle["conclusion_decisions"][:-1]

    assert_bundle_is_blocked(
        bundle,
        "Effectiveness conclusion decision is missing",
    )


def test_gate_blocks_a_conclusion_decision_version_mismatch() -> None:
    bundle = make_complete_bundle()
    decisions = list(bundle["conclusion_decisions"])
    decisions[0] = validated_copy(decisions[0], proposal_version=2)
    bundle["conclusion_decisions"] = tuple(decisions)

    assert_bundle_is_blocked(
        bundle,
        "Implementation conclusion decision version does not match",
    )


def test_gate_blocks_a_conclusion_decision_type_mismatch() -> None:
    bundle = make_complete_bundle()
    decisions = list(bundle["conclusion_decisions"])
    decisions[0] = unvalidated_copy(
        decisions[0],
        conclusion_type=ConclusionType.EFFECTIVENESS,
        approved_outcome=EffectivenessConclusion.EFFECTIVE,
    )
    bundle["conclusion_decisions"] = tuple(decisions)

    assert_bundle_is_blocked(
        bundle,
        "Implementation conclusion decision type does not match",
    )


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (
            AuditorDecisionStatus.REJECTED,
            "Implementation conclusion has been rejected",
        ),
        (
            AuditorDecisionStatus.CHANGES_REQUIRED,
            "Implementation conclusion requires changes",
        ),
    ],
)
def test_gate_blocks_an_unapproved_conclusion(
    status: AuditorDecisionStatus,
    message: str,
) -> None:
    bundle = make_complete_bundle()
    proposal = bundle["implementation_proposal"]
    bundle["conclusion_decisions"] = (
        make_conclusion_decision(proposal, status=status),
        bundle["conclusion_decisions"][1],
    )

    assert_bundle_is_blocked(bundle, message)


def test_gate_blocks_a_different_approved_outcome() -> None:
    bundle = make_complete_bundle()
    decisions = list(bundle["conclusion_decisions"])
    decisions[0] = validated_copy(
        decisions[0],
        approved_outcome=ImplementationConclusion.PARTIALLY_IMPLEMENTED,
    )
    bundle["conclusion_decisions"] = tuple(decisions)

    assert_bundle_is_blocked(
        bundle,
        "Implementation approved outcome does not match the proposal",
    )


def test_gate_blocks_insufficient_final_evidence_for_a_substantive_outcome() -> None:
    bundle = make_complete_bundle()
    decisions = list(bundle["conclusion_decisions"])
    decisions[0] = unvalidated_copy(
        decisions[0],
        final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
    )
    bundle["conclusion_decisions"] = tuple(decisions)

    assert_bundle_is_blocked(
        bundle,
        "substantive conclusion requires sufficient evidence",
    )


def test_gate_blocks_an_unresolved_contradiction() -> None:
    bundle = make_complete_bundle()
    reviews = list(bundle["evidence_reviews"])
    reviews[0] = validated_copy(
        reviews[0],
        contradiction_status=ConclusionContradictionStatus.UNRESOLVED,
        contradiction_evidence_ids=(
            "EVID-IMP-RAW-001",
            "EVID-IMP-DERIVED-001",
        ),
        contradiction_explanation="Fictional unresolved contradiction.",
    )
    bundle["evidence_reviews"] = tuple(reviews)

    assert_bundle_is_blocked(
        bundle,
        "implementation evidence contains an unresolved contradiction",
    )


def test_gate_blocks_an_open_material_gap() -> None:
    bundle = make_complete_bundle()
    gap = make_gap("GAP-IMP-001", "AQ-IMPLEMENTATION-001")
    reviews = list(bundle["evidence_reviews"])
    reviews[0] = validated_copy(reviews[0], gaps=(gap,))
    bundle["evidence_reviews"] = tuple(reviews)
    bundle["implementation_proposal"] = validated_copy(
        bundle["implementation_proposal"],
        considered_gap_ids=(gap.gap_id,),
    )

    assert_bundle_is_blocked(
        bundle,
        "implementation evidence contains an open material gap",
    )


def test_gate_blocks_a_not_determined_conclusion_without_a_limitation() -> None:
    bundle = make_complete_bundle()
    gap = make_gap("GAP-IMP-001", "AQ-IMPLEMENTATION-001")
    reviews = list(bundle["evidence_reviews"])
    reviews[0] = validated_copy(reviews[0], gaps=(gap,))
    proposal = validated_copy(
        make_implementation_proposal(
            outcome=ImplementationConclusion.NOT_DETERMINED,
            relied_upon_evidence_ids=(),
            considered_gap_ids=(gap.gap_id,),
        ),
        limitations=(),
    )
    bundle["evidence_reviews"] = tuple(reviews)
    bundle["implementation_proposal"] = proposal
    bundle["conclusion_decisions"] = (
        make_conclusion_decision(
            proposal,
            final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
        ),
        bundle["conclusion_decisions"][1],
    )

    assert_bundle_is_blocked(
        bundle,
        "not determined conclusion requires an explicit limitation",
    )


def test_gate_blocks_a_not_determined_conclusion_without_a_limiting_condition() -> None:
    bundle = make_complete_bundle()
    proposal = make_implementation_proposal(
        outcome=ImplementationConclusion.NOT_DETERMINED,
        relied_upon_evidence_ids=("EVID-IMP-RAW-001",),
    )
    bundle["implementation_proposal"] = proposal
    bundle["conclusion_decisions"] = (
        make_conclusion_decision(
            proposal,
            final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
        ),
        bundle["conclusion_decisions"][1],
    )

    assert_bundle_is_blocked(
        bundle,
        "not determined conclusion has no evidence limitation",
    )


def test_resolved_gap_does_not_limit_a_not_determined_conclusion() -> None:
    bundle = make_complete_bundle()
    gap = make_gap(
        "GAP-IMP-001",
        "AQ-IMPLEMENTATION-001",
        disposition=EvidenceGapDisposition.RESOLVED,
    )
    reviews = list(bundle["evidence_reviews"])
    reviews[0] = validated_copy(reviews[0], gaps=(gap,))
    proposal = make_implementation_proposal(
        outcome=ImplementationConclusion.NOT_DETERMINED,
        relied_upon_evidence_ids=("EVID-IMP-RAW-001",),
        considered_gap_ids=(gap.gap_id,),
    )
    bundle["evidence_reviews"] = tuple(reviews)
    bundle["implementation_proposal"] = proposal
    effectiveness_proposal = make_effectiveness_proposal(
        outcome=EffectivenessConclusion.NOT_DETERMINED,
    )
    bundle["evidence_items"] = tuple(
        validated_copy(item, freshness=EvidenceFreshness.STALE)
        if item.evidence_id == "EVID-EFF-RAW-001"
        else item
        for item in bundle["evidence_items"]
    )
    bundle["effectiveness_proposal"] = effectiveness_proposal
    bundle["conclusion_decisions"] = (
        make_conclusion_decision(
            proposal,
            final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
        ),
        make_conclusion_decision(
            effectiveness_proposal,
            final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
        ),
    )

    assert_bundle_is_blocked(
        bundle,
        "not determined conclusion has no evidence limitation",
    )


@pytest.mark.parametrize(
    "implementation_outcome",
    [
        ImplementationConclusion.NOT_IMPLEMENTED,
        ImplementationConclusion.NOT_DETERMINED,
    ],
)
def test_effectiveness_cannot_bypass_implementation(
    implementation_outcome: ImplementationConclusion,
) -> None:
    bundle = make_complete_bundle()
    considered_gap_ids: tuple[str, ...] = ()
    if (
        implementation_outcome
        is ImplementationConclusion.NOT_DETERMINED
    ):
        gap = make_gap("GAP-IMP-001", "AQ-IMPLEMENTATION-001")
        implementation_review = validated_copy(
            bundle["evidence_reviews"][0],
            entries=(),
            gaps=(gap,),
            proposed_sufficiency=(
                ConclusionEvidenceSufficiency.INSUFFICIENT
            ),
            limitations=("Requested fictional evidence was not provided.",),
        )
        bundle["evidence_reviews"] = (
            implementation_review,
            bundle["evidence_reviews"][1],
        )
        considered_gap_ids = (gap.gap_id,)
    implementation = make_implementation_proposal(
        outcome=implementation_outcome,
        relied_upon_evidence_ids=(
            ()
            if implementation_outcome
            is ImplementationConclusion.NOT_DETERMINED
            else ("EVID-IMP-RAW-001",)
        ),
        considered_gap_ids=considered_gap_ids,
    )
    if (
        implementation_outcome
        is ImplementationConclusion.NOT_DETERMINED
    ):
        implementation = validated_copy(
            implementation,
            limitations=(
                "Requested fictional implementation evidence was not "
                "provided.",
            ),
        )
    bundle["implementation_proposal"] = implementation
    bundle["conclusion_decisions"] = (
        make_conclusion_decision(
            implementation,
            final_sufficiency=(
                ConclusionEvidenceSufficiency.INSUFFICIENT
                if implementation_outcome
                is ImplementationConclusion.NOT_DETERMINED
                else ConclusionEvidenceSufficiency.SUFFICIENT
            ),
        ),
        bundle["conclusion_decisions"][1],
    )
    with pytest.raises(
        ConclusionApprovalBlockedError,
        match="effectiveness must be not determined",
    ):
        build_accepted_evidence_to_conclusion(**bundle)


def test_not_determined_preserves_missing_evidence_without_calling_it_failure() -> None:
    bundle = make_complete_bundle()
    gap = make_gap("GAP-EFF-001", "AQ-EFFECTIVENESS-001")
    review = EvidenceMatrixReview(
        review_id="MATRIX-EFF-001",
        question_id="AQ-EFFECTIVENESS-001",
        entries=(),
        gaps=(gap,),
        contradiction_status=ConclusionContradictionStatus.NONE_IDENTIFIED,
        contradiction_evidence_ids=(),
        contradiction_explanation=None,
        assumptions=(),
        limitations=("Requested fictional outcome evidence was not provided.",),
        proposed_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
    )
    proposal = make_effectiveness_proposal(
        outcome=EffectivenessConclusion.NOT_DETERMINED,
        relied_upon_evidence_ids=(),
        considered_gap_ids=(gap.gap_id,),
    )
    proposal = validated_copy(
        proposal,
        limitations=("Requested fictional outcome evidence was not provided.",),
    )
    decision = make_conclusion_decision(
        proposal,
        final_sufficiency=ConclusionEvidenceSufficiency.INSUFFICIENT,
    )
    bundle["evidence_reviews"] = (
        bundle["evidence_reviews"][0],
        review,
    )
    bundle["effectiveness_proposal"] = proposal
    bundle["conclusion_decisions"] = (
        bundle["conclusion_decisions"][0],
        decision,
    )

    record = build_accepted_evidence_to_conclusion(**bundle)

    assert record.effectiveness_outcome is (
        EffectivenessConclusion.NOT_DETERMINED
    )


def test_substantive_conclusion_retains_an_accepted_limitation_gap() -> None:
    bundle = make_complete_bundle()
    gap = make_gap(
        "GAP-IMP-001",
        "AQ-IMPLEMENTATION-001",
        disposition=EvidenceGapDisposition.ACCEPTED_LIMITATION,
    )
    reviews = list(bundle["evidence_reviews"])
    reviews[0] = validated_copy(reviews[0], gaps=(gap,))
    bundle["evidence_reviews"] = tuple(reviews)
    bundle["implementation_proposal"] = validated_copy(
        bundle["implementation_proposal"],
        considered_gap_ids=(gap.gap_id,),
    )

    record = build_accepted_evidence_to_conclusion(**bundle)

    retained_gap = record.evidence_reviews[0].gaps[0]
    assert retained_gap.gap_id == gap.gap_id
    assert retained_gap.disposition is EvidenceGapDisposition.ACCEPTED_LIMITATION
    assert retained_gap.disposition_rationale == gap.disposition_rationale


def test_gate_builds_one_complete_accepted_record() -> None:
    record = build_record()

    assert record.planning_trace.control.control_id == "ACE-FICTIONAL-001"
    assert [question.question_type for question in record.questions] == [
        AuditQuestionType.MAIN,
        AuditQuestionType.IMPLEMENTATION,
        AuditQuestionType.EFFECTIVENESS,
    ]
    assert record.implementation_outcome is ImplementationConclusion.IMPLEMENTED
    assert record.effectiveness_outcome is EffectivenessConclusion.EFFECTIVE
    assert record.question_decision_ids == tuple(
        decision.decision_id for decision in record.question_decisions
    )
    assert record.conclusion_decision_ids == tuple(
        decision.decision_id for decision in record.conclusion_decisions
    )


def test_accepted_record_is_frozen_and_gate_only() -> None:
    record = build_record()
    values = record.model_dump()

    with pytest.raises(ValidationError):
        AcceptedEvidenceToConclusionRecord.model_validate(values)
    with pytest.raises(ValidationError):
        record.effectiveness_outcome = EffectivenessConclusion.INEFFECTIVE


def test_sprint_4_public_exports_are_available() -> None:
    from src.ace.domain import (
        AcceptedEvidenceToConclusionRecord,
        AuditQuestionType,
        AuditorConclusionDecision,
        AuditorQuestionDecision,
        ConclusionContradictionStatus,
        ConclusionEvidenceSufficiency,
        ConclusionType,
        EffectivenessConclusion,
        EvidenceFreshness,
        EvidenceGap,
        EvidenceGapDisposition,
        EvidenceGapStatus,
        EvidenceItem,
        EvidenceMatrixEntry,
        EvidenceMatrixReview,
        EvidenceOrigin,
        EvidenceRelevance,
        ImplementationConclusion,
        ProposedAuditQuestion,
        ProposedEffectivenessConclusion,
        ProposedImplementationConclusion,
    )
    from src.ace.engine import (
        ConclusionApprovalBlockedError,
        build_accepted_evidence_to_conclusion,
    )

    assert AuditQuestionType.MAIN.value == "MAIN"
    assert EvidenceOrigin.RAW.value == "RAW"
    assert ImplementationConclusion.IMPLEMENTED.value == "IMPLEMENTED"
    assert EffectivenessConclusion.EFFECTIVE.value == "EFFECTIVE"
    assert AcceptedEvidenceToConclusionRecord is not None
    assert AuditorConclusionDecision is not None
    assert AuditorQuestionDecision is not None
    assert ConclusionContradictionStatus is not None
    assert ConclusionEvidenceSufficiency is not None
    assert ConclusionType is not None
    assert EvidenceFreshness is not None
    assert EvidenceGap is not None
    assert EvidenceGapDisposition is not None
    assert EvidenceGapStatus is not None
    assert EvidenceItem is not None
    assert EvidenceMatrixEntry is not None
    assert EvidenceMatrixReview is not None
    assert EvidenceRelevance is not None
    assert ProposedAuditQuestion is not None
    assert ProposedEffectivenessConclusion is not None
    assert ProposedImplementationConclusion is not None
    assert ConclusionApprovalBlockedError is not None
    assert callable(build_accepted_evidence_to_conclusion)


def test_existing_routes_remain_exactly_unchanged() -> None:
    routes = sorted(
        route.path
        for route in app.routes
        if isinstance(route, APIRoute)
    )
    assert routes == ["/", "/evaluations"]


@pytest.mark.parametrize(
    ("dimensions", "expected"),
    [
        ((True, True, True, True), ControlRating.ADEQUATE),
        ((True, True, False, True), ControlRating.PARTIALLY_ADEQUATE),
        ((True, True, True, False), ControlRating.PARTIALLY_ADEQUATE),
        ((True, True, False, False), ControlRating.INADEQUATE),
        ((True, False, True, True), ControlRating.INADEQUATE),
        ((False, True, True, True), ControlRating.INADEQUATE),
    ],
)
def test_sprint_4_does_not_change_mate_precedence(
    dimensions: tuple[bool, bool, bool, bool],
    expected: ControlRating,
) -> None:
    mandate, accountability, trigger, escalation = dimensions
    control = Control(
        control_id="ACE-FICTIONAL-REGRESSION",
        title="Fictional regression control",
        description="Fictional MATE regression check.",
        hazard_category=HazardCategory.GOVERNANCE_OVERSIGHT,
        dimensions=AssuranceDimensions(
            mandate=mandate,
            accountability=accountability,
            trigger=trigger,
            escalation=escalation,
        ),
    )
    assert evaluate_control(control).rating is expected


def test_sprint_4_source_has_no_prohibited_platform_capabilities() -> None:
    source = (
        Path("src/ace/domain/conclusion.py").read_text(encoding="utf-8")
        + Path("src/ace/engine/conclusion.py").read_text(encoding="utf-8")
    ).lower()
    for prohibited in (
        "requests",
        "http://",
        "https://",
        "telemetry",
        "analytics",
        "supabase",
        "postgres",
        "pgvector",
        "neo4j",
        "graphrag",
    ):
        assert prohibited not in source
