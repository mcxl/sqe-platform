"""Approval gate for one fictional Connected Assurance planning trace."""

from collections.abc import Sequence
from typing import TypeVar

from src.ace.domain.assessment import (
    ApprovedMATEAssessment,
    AuditorDecisionStatus,
    MateDimension,
    SourceReference,
    SourceStatus,
)
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
from src.ace.engine.approval import evaluate_approved_assessment


class TraceApprovalBlockedError(ValueError):
    """Raised when planning records do not form an approved trace."""


RecordT = TypeVar("RecordT")
RELATIONSHIP_ORDER = tuple(TraceRelationshipType)


def _one_for_type(
    records: Sequence[RecordT],
    relationship_type: TraceRelationshipType,
    record_name: str,
) -> RecordT:
    matches = [
        record
        for record in records
        if getattr(record, "relationship_type", None) is relationship_type
    ]
    if not matches:
        raise TraceApprovalBlockedError(
            f"Trace blocked: {relationship_type.label} {record_name} is missing."
        )
    if len(matches) > 1:
        raise TraceApprovalBlockedError(
            f"Trace blocked: {relationship_type.label} {record_name} "
            "appears more than once."
        )
    return matches[0]


def _validate_unique_identifiers(
    *,
    fact_ids: tuple[str, ...],
    sources: tuple[SourceReference, ...],
    relationships: Sequence[ProposedTraceRelationship],
    decisions: Sequence[AuditorRelationshipDecision],
) -> None:
    if len(fact_ids) != len(set(fact_ids)):
        raise TraceApprovalBlockedError(
            "Trace blocked: planning identifiers must be unique."
        )

    source_ids = tuple(source.source_id for source in sources)
    if len(source_ids) != len(set(source_ids)):
        raise TraceApprovalBlockedError(
            "Trace blocked: planning source identifiers must be unique."
        )

    relationship_identities: set[tuple[str, int]] = set()
    for relationship in relationships:
        identity = (
            relationship.relationship_id,
            relationship.relationship_version,
        )
        if identity in relationship_identities:
            raise TraceApprovalBlockedError(
                f"Trace blocked: relationship {relationship.relationship_id} "
                f"version {relationship.relationship_version} appears more "
                "than once."
            )
        relationship_identities.add(identity)

    decision_ids: set[str] = set()
    for decision in decisions:
        if decision.decision_id in decision_ids:
            raise TraceApprovalBlockedError(
                f"Trace blocked: decision {decision.decision_id} appears more "
                "than once."
            )
        decision_ids.add(decision.decision_id)


def _validate_mate_assessment(
    mate_assessment: ApprovedMATEAssessment,
) -> None:
    mate_decision_ids: set[str] = set()
    for decision in mate_assessment.decisions:
        if decision.decision_id in mate_decision_ids:
            raise TraceApprovalBlockedError(
                f"Trace blocked: MATE decision {decision.decision_id} "
                "appears more than once."
            )
        mate_decision_ids.add(decision.decision_id)

    for dimension in MateDimension:
        matches = [
            decision
            for decision in mate_assessment.decisions
            if decision.dimension is dimension
        ]
        if len(matches) != 1:
            raise TraceApprovalBlockedError(
                "Trace blocked: approved MATE assessment is not fully approved."
            )

        decision = matches[0]
        if decision.decision_status is not AuditorDecisionStatus.APPROVED:
            raise TraceApprovalBlockedError(
                "Trace blocked: approved MATE assessment is not fully approved."
            )
        if decision.approved_answer is not getattr(
            mate_assessment.dimensions,
            dimension.field_name,
        ):
            raise TraceApprovalBlockedError(
                "Trace blocked: approved MATE assessment is internally "
                "inconsistent."
            )


def _decision_for_relationship(
    decisions: Sequence[AuditorRelationshipDecision],
    relationship: ProposedTraceRelationship,
) -> AuditorRelationshipDecision:
    identity_matches = [
        decision
        for decision in decisions
        if decision.relationship_id == relationship.relationship_id
        and decision.relationship_version == relationship.relationship_version
    ]
    if len(identity_matches) == 1:
        return identity_matches[0]
    if len(identity_matches) > 1:
        raise TraceApprovalBlockedError(
            f"Trace blocked: relationship {relationship.relationship_id} "
            f"version {relationship.relationship_version} has more than one "
            "decision."
        )
    return _one_for_type(
        decisions,
        relationship.relationship_type,
        "decision",
    )


def build_accepted_planning_trace(
    *,
    obligation: BindingObligationRecord,
    risk: RiskRecord,
    control: PlanningControlRecord,
    accountable_role: AccountableRoleRecord,
    relationships: Sequence[ProposedTraceRelationship],
    decisions: Sequence[AuditorRelationshipDecision],
    mate_assessment: ApprovedMATEAssessment,
) -> AcceptedPlanningTrace:
    """Validate and build one complete, approved planning trace."""

    for relationship_type in RELATIONSHIP_ORDER:
        _one_for_type(relationships, relationship_type, "relationship")
    if len(decisions) != len(RELATIONSHIP_ORDER):
        for relationship_type in RELATIONSHIP_ORDER:
            _one_for_type(decisions, relationship_type, "decision")

    fact_sources = (
        ("Binding Obligation", obligation.source_reference),
        ("Risk", risk.source_reference),
        ("Planning Control", control.source_reference),
        ("Accountable Role", accountable_role.source_reference),
    )
    for label, source in fact_sources:
        if source.status is not SourceStatus.CURRENT:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {label} source is not current."
            )

    if accountable_role.subject_type is not AccountabilitySubjectType.JOB_ROLE:
        raise TraceApprovalBlockedError(
            "Trace blocked: accountability subject must be a job role."
        )

    if control.control_id != mate_assessment.control_id:
        raise TraceApprovalBlockedError(
            f"Trace blocked: planning control {control.control_id} does not "
            "match the approved MATE assessment."
        )

    sources = tuple(source for _, source in fact_sources)
    _validate_unique_identifiers(
        fact_ids=(
            obligation.obligation_id,
            risk.risk_id,
            control.control_id,
            accountable_role.accountability_id,
        ),
        sources=sources,
        relationships=relationships,
        decisions=decisions,
    )

    mate_endpoint = f"MATE:{mate_assessment.control_id}"
    expected_endpoints = {
        TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK: (
            obligation.obligation_id,
            risk.risk_id,
        ),
        TraceRelationshipType.CONTROL_TREATS_RISK: (
            control.control_id,
            risk.risk_id,
        ),
        TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL: (
            accountable_role.accountability_id,
            control.control_id,
        ),
        TraceRelationshipType.CONTROL_HAS_APPROVED_MATE_ASSESSMENT: (
            control.control_id,
            mate_endpoint,
        ),
    }
    allowed_sources = {
        TraceRelationshipType.OBLIGATION_APPLIES_TO_RISK: {
            obligation.source_reference.source_id,
            risk.source_reference.source_id,
        },
        TraceRelationshipType.CONTROL_TREATS_RISK: {
            control.source_reference.source_id,
            risk.source_reference.source_id,
        },
        TraceRelationshipType.ROLE_ACCOUNTABLE_FOR_CONTROL: {
            accountable_role.source_reference.source_id,
            control.source_reference.source_id,
        },
        TraceRelationshipType.CONTROL_HAS_APPROVED_MATE_ASSESSMENT: {
            control.source_reference.source_id,
        },
    }

    ordered_relationships = []
    ordered_decisions = []
    for relationship_type in RELATIONSHIP_ORDER:
        relationship = _one_for_type(
            relationships,
            relationship_type,
            "relationship",
        )
        decision = _decision_for_relationship(decisions, relationship)
        expected_source, expected_target = expected_endpoints[relationship_type]

        if (
            relationship.source_record_id != expected_source
            or relationship.target_record_id != expected_target
        ):
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} endpoints do not "
                "match the required records."
            )

        if not set(relationship.supporting_source_ids).issubset(
            allowed_sources[relationship_type]
        ):
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} uses a source "
                "outside its endpoints."
            )

        if decision.relationship_id != relationship.relationship_id:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} decision "
                "relationship identifier does not match."
            )
        if decision.relationship_version != relationship.relationship_version:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} decision "
                "relationship version does not match."
            )
        if decision.relationship_type is not relationship.relationship_type:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} decision type "
                "does not match."
            )

        if decision.decision_status is AuditorDecisionStatus.REJECTED:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} has been rejected."
            )
        if decision.decision_status is AuditorDecisionStatus.CHANGES_REQUIRED:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} requires changes."
            )
        if decision.decision_status is not AuditorDecisionStatus.APPROVED:
            raise TraceApprovalBlockedError(
                f"Trace blocked: {relationship_type.label} has not been "
                "approved."
            )

        ordered_relationships.append(relationship)
        ordered_decisions.append(decision)

    _validate_mate_assessment(mate_assessment)

    evaluation_result = evaluate_approved_assessment(mate_assessment)
    if evaluation_result.control_id != control.control_id:
        raise TraceApprovalBlockedError(
            "Trace blocked: evaluation result refers to a different control."
        )

    return AcceptedPlanningTrace._from_approved_gate(
        obligation=obligation,
        risk=risk,
        control=control,
        accountable_role=accountable_role,
        relationships=tuple(ordered_relationships),
        decisions=tuple(ordered_decisions),
        decision_ids=tuple(
            decision.decision_id for decision in ordered_decisions
        ),
        mate_assessment=mate_assessment,
        evaluation_result=evaluation_result,
    )


def forward_trace_references(
    trace: AcceptedPlanningTrace,
) -> tuple[str, ...]:
    """Return the stable planning trace from obligation to rating."""

    approved_relationships = tuple(
        (
            "APPROVED_RELATIONSHIP:"
            f"{relationship.relationship_type.value}:"
            f"{relationship.relationship_id}:"
            f"v{relationship.relationship_version}:"
            f"DECISION:{decision.decision_id}"
        )
        for relationship, decision in zip(
            trace.relationships,
            trace.decisions,
            strict=True,
        )
    )

    return (
        f"OBLIGATION:{trace.obligation.obligation_id}",
        approved_relationships[0],
        f"RISK:{trace.risk.risk_id}",
        approved_relationships[1],
        f"CONTROL:{trace.control.control_id}",
        approved_relationships[2],
        f"ROLE:{trace.accountable_role.accountability_id}",
        approved_relationships[3],
        f"MATE:{trace.mate_assessment.control_id}",
        f"RATING:{trace.evaluation_result.rating.value}",
    )


def reverse_trace_references(
    trace: AcceptedPlanningTrace,
) -> tuple[str, ...]:
    """Return the stable facts-only follow-up from rating to obligation."""

    return (
        f"RATING:{trace.evaluation_result.rating.value}",
        f"MATE:{trace.mate_assessment.control_id}",
        f"ROLE:{trace.accountable_role.accountability_id}",
        f"CONTROL:{trace.control.control_id}",
        f"RISK:{trace.risk.risk_id}",
        f"OBLIGATION:{trace.obligation.obligation_id}",
    )
