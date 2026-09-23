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
import src.ace.engine.tracing as tracing_module
from src.ace.engine.tracing import (
    TraceApprovalBlockedError,
    build_accepted_planning_trace,
    forward_trace_references,
    reverse_trace_references,
)


def validated_copy(model: Any, **changes: object) -> Any:
    values = model.model_dump()
    values.update(changes)
    if isinstance(model, ApprovedMATEAssessment):
        return ApprovedMATEAssessment._from_approved_gate(**values)
    return type(model).model_validate(values)


def make_source(
    source_id: str,
    *,
    status: SourceStatus = SourceStatus.CURRENT,
) -> SourceReference:
    return SourceReference(
        source_id=source_id,
        document_title=f"Fictional document for {source_id}",
        document_version="1.0",
        source_location=f"Section {source_id}",
        source_wording=f"Fictional source wording for {source_id}.",
        status=status,
    )


def make_obligation() -> BindingObligationRecord:
    return BindingObligationRecord(
        obligation_id="OBL-FICTIONAL-001",
        title="Fictional mobilisation obligation",
        binding_instrument="Fictional Safety Management Policy",
        clause="Clause 4.1",
        obligation_text=(
            "A fictional mobilisation control must be approved before work starts."
        ),
        source_reference=make_source("SRC-OBLIGATION"),
    )


def make_risk() -> RiskRecord:
    return RiskRecord(
        risk_id="RISK-FICTIONAL-001",
        title="Fictional uncontrolled mobilisation risk",
        risk_statement=(
            "Work may start without required fictional governance approval."
        ),
        source_reference=make_source("SRC-RISK"),
    )


def make_control() -> PlanningControlRecord:
    return PlanningControlRecord(
        control_id="ACE-FICTIONAL-001",
        title="Fictional mobilisation approval control",
        design_statement=(
            "The fictional accountable role approves mobilisation before work starts."
        ),
        source_reference=make_source("SRC-CONTROL"),
    )


def make_role(
    *,
    subject_type: AccountabilitySubjectType = (
        AccountabilitySubjectType.JOB_ROLE
    ),
) -> AccountableRoleRecord:
    return AccountableRoleRecord(
        accountability_id="ROLE-FICTIONAL-001",
        subject_type=subject_type,
        subject_title=(
            "Fictional Head of Safety"
            if subject_type is AccountabilitySubjectType.JOB_ROLE
            else "Fictional Person A"
        ),
        accountability_statement=(
            "The fictional job role is accountable for the mobilisation control."
        ),
        source_reference=make_source("SRC-ROLE"),
    )


def make_relationship(
    relationship_type: TraceRelationshipType,
    *,
    source_record_id: str = "SOURCE-001",
    target_record_id: str = "TARGET-001",
    supporting_source_ids: tuple[str, ...] = ("SRC-OBLIGATION",),
    version: int = 1,
) -> ProposedTraceRelationship:
    return ProposedTraceRelationship(
        relationship_id=f"REL-{relationship_type.value}",
        relationship_version=version,
        relationship_type=relationship_type,
        source_record_id=source_record_id,
        target_record_id=target_record_id,
        supporting_source_ids=supporting_source_ids,
        rationale=f"Fictional rationale for {relationship_type.label}.",
    )


def make_relationship_decision(
    relationship: ProposedTraceRelationship,
    *,
    status: AuditorDecisionStatus = AuditorDecisionStatus.APPROVED,
    version: int | None = None,
) -> AuditorRelationshipDecision:
    return AuditorRelationshipDecision(
        decision_id=f"DEC-{relationship.relationship_type.value}",
        relationship_id=relationship.relationship_id,
        relationship_version=(
            relationship.relationship_version if version is None else version
        ),
        relationship_type=relationship.relationship_type,
        decision_status=status,
        reviewer_id="FICTIONAL-AUDITOR-01",
        review_notes=f"Fictional review of {relationship.relationship_type.label}.",
        reviewed_at="2026-07-28T01:02:03.456789+00:00",
    )


def test_trace_vocabulary_values_are_stable() -> None:
    assert [value.value for value in AccountabilitySubjectType] == [
        "JOB_ROLE",
        "NAMED_PERSON",
    ]
    assert [value.value for value in TraceRelationshipType] == [
        "OBLIGATION_APPLIES_TO_RISK",
        "CONTROL_TREATS_RISK",
        "ROLE_ACCOUNTABLE_FOR_CONTROL",
        "CONTROL_HAS_APPROVED_MATE_ASSESSMENT",
    ]


@pytest.mark.parametrize(
    ("factory", "field_name"),
    [
        (make_obligation, "obligation_id"),
        (make_obligation, "binding_instrument"),
        (make_obligation, "clause"),
        (make_obligation, "obligation_text"),
        (make_risk, "risk_id"),
        (make_risk, "risk_statement"),
        (make_control, "control_id"),
        (make_control, "design_statement"),
        (make_role, "accountability_id"),
        (make_role, "subject_title"),
        (make_role, "accountability_statement"),
    ],
)
def test_planning_facts_reject_blank_required_text(
    factory: Any,
    field_name: str,
) -> None:
    values = factory().model_dump()
    values[field_name] = "   "

    with pytest.raises(ValidationError):
        type(factory()).model_validate(values)


@pytest.mark.parametrize(
    "record",
    [make_obligation(), make_risk(), make_control(), make_role()],
)
def test_planning_facts_are_frozen(record: Any) -> None:
    with pytest.raises(ValidationError):
        record.source_reference = make_source("SRC-CHANGED")


def test_named_person_is_recorded_explicitly_for_gate_review() -> None:
    role = make_role(subject_type=AccountabilitySubjectType.NAMED_PERSON)

    assert role.subject_type is AccountabilitySubjectType.NAMED_PERSON


@pytest.mark.parametrize("version", [0, -1, "1"])
def test_relationship_version_must_be_a_positive_strict_integer(
    version: object,
) -> None:
    with pytest.raises(ValidationError):
        make_relationship(
            TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK,
            version=version,
        )


def test_relationship_requires_supporting_sources() -> None:
    with pytest.raises(ValidationError):
        make_relationship(
            TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK,
            supporting_source_ids=(),
        )


def test_relationship_rejects_duplicate_supporting_source_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="supporting source identifiers must be unique",
    ):
        make_relationship(
            TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK,
            supporting_source_ids=("SRC-OBLIGATION", "SRC-OBLIGATION"),
        )


def test_relationship_proposal_is_frozen() -> None:
    relationship = make_relationship(
        TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK
    )

    with pytest.raises(ValidationError):
        relationship.target_record_id = "CHANGED"


@pytest.mark.parametrize(
    "timestamp",
    [
        "not-a-timestamp",
        "2026-07-28T01:02:03.456789",
        "2026-07-28T11:02:03.456789+10:00",
        "2026-07-28 01:02:03.456789+00:00",
        " 2026-07-28T01:02:03.456789+00:00",
        "2026-07-28T01:02:03.456789+00:00 ",
    ],
)
def test_relationship_decision_rejects_noncanonical_utc(
    timestamp: str,
) -> None:
    relationship = make_relationship(
        TraceRelationshipType.CONTROL_TREATS_RISK
    )
    values = make_relationship_decision(relationship).model_dump()
    values["reviewed_at"] = timestamp

    with pytest.raises(ValidationError):
        AuditorRelationshipDecision.model_validate(values)


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-07-28T01:02:03.456789+00:00",
        "2026-07-28T01:02:03.456789Z",
    ],
)
def test_relationship_decision_accepts_canonical_utc(timestamp: str) -> None:
    relationship = make_relationship(
        TraceRelationshipType.CONTROL_TREATS_RISK
    )
    values = make_relationship_decision(relationship).model_dump()
    values["reviewed_at"] = timestamp

    decision = AuditorRelationshipDecision.model_validate(values)

    assert decision.reviewed_at == timestamp


@pytest.mark.parametrize("field_name", ["decision_id", "reviewer_id", "review_notes"])
def test_relationship_decision_rejects_blank_required_text(
    field_name: str,
) -> None:
    relationship = make_relationship(
        TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL
    )
    values = make_relationship_decision(relationship).model_dump()
    values[field_name] = "   "

    with pytest.raises(ValidationError):
        AuditorRelationshipDecision.model_validate(values)


def test_relationship_decision_is_frozen() -> None:
    relationship = make_relationship(
        TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL
    )
    decision = make_relationship_decision(relationship)

    with pytest.raises(ValidationError):
        decision.decision_status = AuditorDecisionStatus.REJECTED


def make_mate_assessment(
    answers: dict[MateDimension, ProposedAnswer] | None = None,
) -> ApprovedMATEAssessment:
    selected_answers = {} if answers is None else answers
    proposals = []
    reviews = []
    decisions = []

    for dimension in MateDimension:
        answer = selected_answers.get(dimension, ProposedAnswer.YES)
        approved_answer = answer is ProposedAnswer.YES
        source = make_source(f"SRC-MATE-{dimension.value}")
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
            proposed_answer=answer,
            rationale=f"Fictional MATE rationale for {dimension.label}.",
            evidence_review_id=review.review_id,
        )
        decision = AuditorDecision(
            decision_id=f"DEC-MATE-{dimension.value}",
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.proposal_version,
            dimension=dimension,
            decision_status=AuditorDecisionStatus.APPROVED,
            approved_answer=approved_answer,
            final_sufficiency=(
                EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
            ),
            reviewer_id="FICTIONAL-MATE-AUDITOR",
            review_notes=f"Fictional approval for {dimension.label}.",
            reviewed_at="2026-07-28T01:02:03.456789+00:00",
        )
        reviews.append(review)
        proposals.append(proposal)
        decisions.append(decision)

    return build_approved_assessment(
        control_id="ACE-FICTIONAL-001",
        title="Fictional mobilisation approval control",
        description="Fictional control-design assessment for Sprint 3.",
        hazard_category=HazardCategory.GOVERNANCE_OVERSIGHT,
        proposals=tuple(proposals),
        evidence_reviews=tuple(reviews),
        decisions=tuple(decisions),
        reviewer_notes="Fictional Sprint 3 MATE assessment.",
    )


def make_relationship_bundle(
    obligation: BindingObligationRecord,
    risk: RiskRecord,
    control: PlanningControlRecord,
    role: AccountableRoleRecord,
    mate_assessment: ApprovedMATEAssessment,
) -> tuple[
    tuple[ProposedTraceRelationship, ...],
    tuple[AuditorRelationshipDecision, ...],
]:
    relationships = (
        make_relationship(
            TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK,
            source_record_id=obligation.obligation_id,
            target_record_id=risk.risk_id,
            supporting_source_ids=(
                obligation.source_reference.source_id,
                risk.source_reference.source_id,
            ),
        ),
        make_relationship(
            TraceRelationshipType.CONTROL_TREATS_RISK,
            source_record_id=control.control_id,
            target_record_id=risk.risk_id,
            supporting_source_ids=(
                control.source_reference.source_id,
                risk.source_reference.source_id,
            ),
        ),
        make_relationship(
            TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL,
            source_record_id=role.accountability_id,
            target_record_id=control.control_id,
            supporting_source_ids=(
                role.source_reference.source_id,
                control.source_reference.source_id,
            ),
        ),
        make_relationship(
            TraceRelationshipType.CONTROL_HAS_APPROVED_MATE_ASSESSMENT,
            source_record_id=control.control_id,
            target_record_id=f"MATE:{mate_assessment.control_id}",
            supporting_source_ids=(control.source_reference.source_id,),
        ),
    )
    decisions = tuple(
        make_relationship_decision(relationship)
        for relationship in relationships
    )
    return relationships, decisions


def build_trace(
    *,
    obligation: BindingObligationRecord | None = None,
    risk: RiskRecord | None = None,
    control: PlanningControlRecord | None = None,
    role: AccountableRoleRecord | None = None,
    mate_assessment: ApprovedMATEAssessment | None = None,
    relationships: tuple[ProposedTraceRelationship, ...] | None = None,
    decisions: tuple[AuditorRelationshipDecision, ...] | None = None,
) -> AcceptedPlanningTrace:
    selected_obligation = make_obligation() if obligation is None else obligation
    selected_risk = make_risk() if risk is None else risk
    selected_control = make_control() if control is None else control
    selected_role = make_role() if role is None else role
    selected_mate = (
        make_mate_assessment() if mate_assessment is None else mate_assessment
    )
    if relationships is None or decisions is None:
        default_relationships, default_decisions = make_relationship_bundle(
            selected_obligation,
            selected_risk,
            selected_control,
            selected_role,
            selected_mate,
        )
    else:
        default_relationships, default_decisions = (), ()
    return build_accepted_planning_trace(
        obligation=selected_obligation,
        risk=selected_risk,
        control=selected_control,
        accountable_role=selected_role,
        relationships=(
            default_relationships if relationships is None else relationships
        ),
        decisions=default_decisions if decisions is None else decisions,
        mate_assessment=selected_mate,
    )


def test_gate_builds_one_complete_accepted_trace() -> None:
    trace = build_trace()

    assert trace.obligation.obligation_id == "OBL-FICTIONAL-001"
    assert trace.risk.risk_id == "RISK-FICTIONAL-001"
    assert trace.control.control_id == "ACE-FICTIONAL-001"
    assert trace.accountable_role.subject_title == "Fictional Head of Safety"
    assert len(trace.relationships) == 4
    assert len(trace.decisions) == 4
    assert trace.decision_ids == tuple(
        decision.decision_id for decision in trace.decisions
    )
    assert trace.evaluation_result.rating is ControlRating.ADEQUATE


def test_forward_trace_order_is_deterministic() -> None:
    trace = build_trace()

    assert forward_trace_references(trace) == (
        "OBLIGATION:OBL-FICTIONAL-001",
        (
            "APPROVED_RELATIONSHIP:OBLIGATION_APPLIES_TO_RISK:"
            "REL-OBLIGATION_APPLIES_TO_RISK:v1:"
            "DECISION:DEC-OBLIGATION_APPLIES_TO_RISK"
        ),
        "RISK:RISK-FICTIONAL-001",
        (
            "APPROVED_RELATIONSHIP:CONTROL_TREATS_RISK:"
            "REL-CONTROL_TREATS_RISK:v1:"
            "DECISION:DEC-CONTROL_TREATS_RISK"
        ),
        "CONTROL:ACE-FICTIONAL-001",
        (
            "APPROVED_RELATIONSHIP:ROLE_ACCOUNTABLE_FOR_CONTROL:"
            "REL-ROLE_ACCOUNTABLE_FOR_CONTROL:v1:"
            "DECISION:DEC-ROLE_ACCOUNTABLE_FOR_CONTROL"
        ),
        "ROLE:ROLE-FICTIONAL-001",
        (
            "APPROVED_RELATIONSHIP:CONTROL_HAS_APPROVED_MATE_ASSESSMENT:"
            "REL-CONTROL_HAS_APPROVED_MATE_ASSESSMENT:v1:"
            "DECISION:DEC-CONTROL_HAS_APPROVED_MATE_ASSESSMENT"
        ),
        "MATE:ACE-FICTIONAL-001",
        "RATING:ADEQUATE",
    )


def test_reverse_trace_is_the_exact_design_follow_up_order() -> None:
    trace = build_trace()

    assert reverse_trace_references(trace) == (
        "RATING:ADEQUATE",
        "MATE:ACE-FICTIONAL-001",
        "ROLE:ROLE-FICTIONAL-001",
        "CONTROL:ACE-FICTIONAL-001",
        "RISK:RISK-FICTIONAL-001",
        "OBLIGATION:OBL-FICTIONAL-001",
    )


def test_trace_retains_existing_inadequate_precedence() -> None:
    mate = make_mate_assessment(
        {
            MateDimension.TRIGGER: ProposedAnswer.NO,
            MateDimension.ESCALATION: ProposedAnswer.NO,
        }
    )

    trace = build_trace(mate_assessment=mate)

    assert trace.evaluation_result.rating is ControlRating.INADEQUATE
    assert forward_trace_references(trace)[-1] == "RATING:INADEQUATE"


def test_accepted_trace_is_frozen() -> None:
    trace = build_trace()

    with pytest.raises(ValidationError):
        trace.control = make_control()


def test_accepted_trace_rejects_direct_construction_and_model_validation() -> None:
    approved_trace = build_trace()
    values = approved_trace.model_dump()

    with pytest.raises(
        ValidationError,
        match="accepted planning trace must be built by the approval gate",
    ):
        AcceptedPlanningTrace(**values)

    with pytest.raises(
        ValidationError,
        match="accepted planning trace must be built by the approval gate",
    ):
        AcceptedPlanningTrace.model_validate(values)

    assert approved_trace.__class__ is AcceptedPlanningTrace
    with pytest.raises(ValidationError):
        approved_trace.control = make_control()


def test_gate_blocks_a_named_person() -> None:
    with pytest.raises(
        TraceApprovalBlockedError,
        match="accountability subject must be a job role",
    ):
        build_trace(
            role=make_role(
                subject_type=AccountabilitySubjectType.NAMED_PERSON
            )
        )


@pytest.mark.parametrize(
    "status",
    [SourceStatus.SUPERSEDED, SourceStatus.UNCERTAIN],
)
def test_gate_blocks_a_noncurrent_planning_source(
    status: SourceStatus,
) -> None:
    obligation = make_obligation()
    stale_source = validated_copy(obligation.source_reference, status=status)
    obligation = validated_copy(obligation, source_reference=stale_source)

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Binding Obligation source is not current",
    ):
        build_trace(obligation=obligation)


def test_gate_blocks_a_missing_relationship_type() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Control Has Approved Mate Assessment relationship is missing",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships[:-1],
            decisions=decisions[:-1],
        )


def test_gate_blocks_empty_relationships() -> None:
    with pytest.raises(
        TraceApprovalBlockedError,
        match="Obligation Applies To Risk relationship is missing",
    ):
        build_trace(relationships=())


def test_gate_blocks_empty_relationship_decisions() -> None:
    with pytest.raises(
        TraceApprovalBlockedError,
        match="Obligation Applies To Risk decision is missing",
    ):
        build_trace(decisions=())


def test_gate_blocks_a_duplicate_relationship_type() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Obligation Applies To Risk relationship appears more than once",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships + (relationships[0],),
            decisions=decisions + (decisions[0],),
        )


def test_gate_blocks_duplicate_planning_fact_identifiers() -> None:
    obligation = make_obligation()
    risk = validated_copy(make_risk(), risk_id=obligation.obligation_id)

    with pytest.raises(
        TraceApprovalBlockedError,
        match="planning identifiers must be unique",
    ):
        build_trace(obligation=obligation, risk=risk)


def test_gate_blocks_duplicate_planning_source_identifiers() -> None:
    obligation = make_obligation()
    original_risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, original_risk, control, role, mate
    )
    duplicate_source = validated_copy(
        original_risk.source_reference,
        source_id=obligation.source_reference.source_id,
    )
    risk = validated_copy(original_risk, source_reference=duplicate_source)

    with pytest.raises(
        TraceApprovalBlockedError,
        match="planning source identifiers must be unique",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_duplicate_relationship_identities() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    duplicate = validated_copy(
        relationships[1],
        relationship_id=relationships[0].relationship_id,
        relationship_version=relationships[0].relationship_version,
    )
    relationships = (relationships[0], duplicate, *relationships[2:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match=(
            "relationship REL-OBLIGATION_APPLIES_TO_RISK "
            "version 1 appears more than once"
        ),
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_duplicate_relationship_decision_identifiers() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    duplicate = validated_copy(
        decisions[1],
        decision_id=decisions[0].decision_id,
    )
    decisions = (decisions[0], duplicate, *decisions[2:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match=(
            "decision DEC-OBLIGATION_APPLIES_TO_RISK "
            "appears more than once"
        ),
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_the_wrong_relationship_endpoint() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    wrong = validated_copy(
        relationships[1],
        target_record_id=obligation.obligation_id,
    )
    relationships = (relationships[0], wrong, *relationships[2:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Control Treats Risk endpoints do not match",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_the_wrong_derived_mate_endpoint() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    wrong = validated_copy(
        relationships[3],
        target_record_id="MATE:ACE-DIFFERENT-001",
    )
    relationships = (*relationships[:3], wrong)

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Control Has Approved Mate Assessment endpoints do not match",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_a_source_from_an_unrelated_endpoint() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    wrong = validated_copy(
        relationships[0],
        supporting_source_ids=(role.source_reference.source_id,),
    )
    relationships = (wrong, *relationships[1:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Obligation Applies To Risk uses a source outside its endpoints",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (AuditorDecisionStatus.REJECTED, "has been rejected"),
        (AuditorDecisionStatus.CHANGES_REQUIRED, "requires changes"),
    ],
)
def test_gate_blocks_a_nonapproved_relationship(
    status: AuditorDecisionStatus,
    message: str,
) -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    rejected = validated_copy(decisions[0], decision_status=status)
    decisions = (rejected, *decisions[1:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match=f"Obligation Applies To Risk {message}",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_a_decision_for_the_wrong_version() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    wrong = validated_copy(decisions[0], relationship_version=2)
    decisions = (wrong, *decisions[1:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match="decision relationship version does not match",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_a_decision_for_the_wrong_relationship_identifier() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    wrong = validated_copy(decisions[0], relationship_id="REL-DIFFERENT-001")
    decisions = (wrong, *decisions[1:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match="decision relationship identifier does not match",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


def test_gate_blocks_a_decision_with_the_wrong_relationship_type() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    wrong = validated_copy(
        decisions[0],
        relationship_type=TraceRelationshipType.CONTROL_TREATS_RISK,
    )
    decisions = (wrong, *decisions[1:])

    with pytest.raises(
        TraceApprovalBlockedError,
        match="decision type does not match",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=decisions,
        )


@pytest.mark.parametrize("version", [0, -1, "1"])
def test_relationship_decision_version_must_be_a_positive_strict_integer(
    version: object,
) -> None:
    relationship = make_relationship(
        TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK
    )

    with pytest.raises(ValidationError):
        make_relationship_decision(relationship, version=version)


def test_gate_blocks_a_control_that_differs_from_mate() -> None:
    control = validated_copy(make_control(), control_id="ACE-DIFFERENT-001")

    with pytest.raises(
        TraceApprovalBlockedError,
        match="does not match the approved MATE assessment",
    ):
        build_trace(control=control)


def test_gate_blocks_a_mate_assessment_with_an_unapproved_decision() -> None:
    mate = make_mate_assessment()
    rejected = validated_copy(
        mate.decisions[0],
        decision_status=AuditorDecisionStatus.REJECTED,
        approved_answer=None,
    )
    mate = validated_copy(
        mate,
        decisions=(rejected, *mate.decisions[1:]),
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="approved MATE assessment is not fully approved",
    ):
        build_trace(mate_assessment=mate)


def test_gate_checks_relationship_approval_before_mate_assessment() -> None:
    obligation = make_obligation()
    risk = make_risk()
    control = make_control()
    role = make_role()
    mate = make_mate_assessment()
    relationships, decisions = make_relationship_bundle(
        obligation, risk, control, role, mate
    )
    rejected = validated_copy(
        decisions[0],
        decision_status=AuditorDecisionStatus.REJECTED,
    )
    duplicate_mate_decision = validated_copy(
        mate.decisions[1],
        decision_id=mate.decisions[0].decision_id,
    )
    mate = validated_copy(
        mate,
        decisions=(
            mate.decisions[0],
            duplicate_mate_decision,
            *mate.decisions[2:],
        ),
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="Obligation Applies To Risk has been rejected",
    ):
        build_trace(
            obligation=obligation,
            risk=risk,
            control=control,
            role=role,
            mate_assessment=mate,
            relationships=relationships,
            decisions=(rejected, *decisions[1:]),
        )


def test_gate_blocks_mate_dimensions_that_disagree_with_decisions() -> None:
    mate = make_mate_assessment()
    mate = validated_copy(
        mate,
        dimensions=AssuranceDimensions(
            mandate=False,
            accountability=True,
            trigger=True,
            escalation=True,
        ),
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="approved MATE assessment is internally inconsistent",
    ):
        build_trace(mate_assessment=mate)


def test_gate_blocks_duplicate_mate_decision_identifiers() -> None:
    mate = make_mate_assessment()
    duplicate = validated_copy(
        mate.decisions[1],
        decision_id=mate.decisions[0].decision_id,
    )
    mate = validated_copy(
        mate,
        decisions=(mate.decisions[0], duplicate, *mate.decisions[2:]),
    )

    with pytest.raises(
        TraceApprovalBlockedError,
        match="MATE decision DEC-MATE-MANDATE appears more than once",
    ):
        build_trace(mate_assessment=mate)


@pytest.mark.parametrize(
    (
        "mandate",
        "accountability",
        "trigger",
        "escalation",
        "expected_rating",
    ),
    [
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
    ],
    ids=[
        "NNNN-inadequate",
        "NNNY-inadequate",
        "NNYN-inadequate",
        "NNYY-inadequate",
        "NYNN-inadequate",
        "NYNY-inadequate",
        "NYYN-inadequate",
        "NYYY-inadequate",
        "YNNN-inadequate",
        "YNNY-inadequate",
        "YNYN-inadequate",
        "YNYY-inadequate",
        "YYNN-inadequate",
        "YYNY-partially-adequate",
        "YYYN-partially-adequate",
        "YYYY-adequate",
    ],
)
def test_all_mate_boolean_combinations_use_existing_rating_precedence(
    mandate: bool,
    accountability: bool,
    trigger: bool,
    escalation: bool,
    expected_rating: ControlRating,
) -> None:
    answers = {
        MateDimension.MANDATE: (
            ProposedAnswer.YES if mandate else ProposedAnswer.NO
        ),
        MateDimension.ACCOUNTABILITY: (
            ProposedAnswer.YES if accountability else ProposedAnswer.NO
        ),
        MateDimension.TRIGGER: (
            ProposedAnswer.YES if trigger else ProposedAnswer.NO
        ),
        MateDimension.ESCALATION: (
            ProposedAnswer.YES if escalation else ProposedAnswer.NO
        ),
    }

    trace = build_trace(mate_assessment=make_mate_assessment(answers))

    assert trace.evaluation_result.rating is expected_rating


def test_gate_retains_the_existing_evaluator_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mate = make_mate_assessment()
    evaluator_result = EvaluationResult(
        control_id=mate.control_id,
        rating=ControlRating.PARTIALLY_ADEQUATE,
        failed_dimensions=("trigger",),
        timestamp="2026-07-28T02:03:04.567890+00:00",
        reasoning="Fictional result returned by the existing evaluator.",
    )
    monkeypatch.setattr(
        tracing_module,
        "evaluate_approved_assessment",
        lambda assessment: evaluator_result,
    )

    trace = build_trace(mate_assessment=mate)

    assert trace.evaluation_result is evaluator_result
