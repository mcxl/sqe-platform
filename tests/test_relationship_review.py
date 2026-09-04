import json
import sqlite3
from pathlib import Path

import pytest

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
from src.ace.domain.enums import HazardCategory
from src.ace.domain.trace import (
    AccountabilitySubjectType,
    AccountableRoleRecord,
    BindingObligationRecord,
    PlanningControlRecord,
    RiskRecord,
)
from src.ace.engine.approval import build_approved_assessment
from src.ace.workbench.action_result import ActionResultState
from src.ace.workbench.storage import WorkbenchStore


def service(tmp_path: Path, trace_input_provider=None):
    from src.ace.workbench.relationship_review import RelationshipReviewService

    return RelationshipReviewService(
        WorkbenchStore(tmp_path / "local-data"), trace_input_provider=trace_input_provider
    )


def auditor():
    from src.ace.workbench.relationship_review import RelationshipReviewActor, RelationshipReviewActorKind

    return RelationshipReviewActor(RelationshipReviewActorKind.ACCOUNTABLE_AUDITOR, "auditor")


def agent():
    from src.ace.workbench.relationship_review import RelationshipReviewActor, RelationshipReviewActorKind

    return RelationshipReviewActor(RelationshipReviewActorKind.AGENT, "agent")


def draft(version: int = 1) -> dict[str, object]:
    return {
        "relationship_version": version,
        "proposed_decision": "APPROVED",
        "draft_reason": "Fictional review draft note.",
    }


def preview(
    service_object,
    relationship_id: str = "REL-FIC-0001",
    reason: str = "The fictional relationship is approved.",
) -> dict[str, object]:
    return service_object.request_approval_preview(
        relationship_id,
        {"relationship_version": 1, "approval_reason": reason},
        agent(),
    )


def approve(service_object, key: str = "relationship-decision-0001") -> dict[str, object]:
    preview_state = preview(service_object)
    return service_object.record_decision(
        "REL-FIC-0001",
        {
            "relationship_version": preview_state["state"]["current_version"],
            "decision": "APPROVED",
            "reason": "The fictional relationship is approved.",
            "decision_key": key,
            "preview_token": preview_state["preview_token"],
        },
        auditor(),
    )


def changes_required(service_object, relationship_id: str = "REL-FIC-0001") -> dict[str, object]:
    return service_object.record_decision(
        relationship_id,
        {
            "relationship_version": 1,
            "decision": "CHANGES_REQUIRED",
            "reason": "Add a clearer fictional source link.",
            "decision_key": f"changes-required-{relationship_id}",
            "preview_token": None,
        },
        auditor(),
    )


def revision_request(version: int = 1, key: str = "relationship-revision-0001") -> dict[str, object]:
    return {
        "prior_relationship_version": version,
        "revision_key": key,
        "rationale": "Corrected fictional relationship rationale.",
        "supporting_source_ids": ["SRC-FIC-OBLIGATION"],
        "gaps": ["Fictional gap addressed."],
        "contradictions": ["No fictional contradiction remains."],
        "duplicate_warnings": ["No fictional duplicate remains."],
    }


def approved_mate_assessment():
    proposals = []
    reviews = []
    decisions = []
    for dimension in MateDimension:
        source = SourceReference(source_id=f"SRC-MATE-{dimension.value}", document_title="Fictional MATE source", document_version="1", source_location="Fictional register", source_wording="Fictional current MATE source.", status=SourceStatus.CURRENT)
        review = EvidenceReviewRecord(review_id=f"REV-MATE-{dimension.value}", source_references=(source,), supporting_source_ids=(source.source_id,), evidence_availability=(EvidenceAvailability.REVIEWED_SUPPORTIVE,), contradiction_status=ContradictionStatus.NONE_IDENTIFIED, proposed_sufficiency=EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT)
        proposal = ProposedDimensionAssessment(proposal_id=f"PROP-MATE-{dimension.value}", proposal_version=1, dimension=dimension, proposed_answer=ProposedAnswer.YES, rationale="Fictional MATE rationale.", evidence_review_id=review.review_id)
        decisions.append(AuditorDecision(decision_id=f"DEC-MATE-{dimension.value}", proposal_id=proposal.proposal_id, proposal_version=1, dimension=dimension, decision_status=AuditorDecisionStatus.APPROVED, approved_answer=True, final_sufficiency=EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT, reviewer_id="auditor", review_notes="Fictional MATE approval.", reviewed_at="2026-08-01T00:00:00Z"))
        proposals.append(proposal)
        reviews.append(review)
    return build_approved_assessment(control_id="CTL-FIC-0001", title="Fictional control", description="Fictional MATE assessment.", hazard_category=HazardCategory.GOVERNANCE_OVERSIGHT, proposals=tuple(proposals), evidence_reviews=tuple(reviews), decisions=tuple(decisions))


def trace_input_values():
    from src.ace.workbench.relationship_review import RelationshipTraceInputs

    def source(source_id: str) -> SourceReference:
        return SourceReference(
            source_id=source_id,
            document_title="Fictional planning source",
            document_version="1",
            source_location="Fictional register",
            source_wording="Fictional current source wording.",
            status=SourceStatus.CURRENT,
        )

    return RelationshipTraceInputs(
        obligation=BindingObligationRecord(
            obligation_id="OBL-FIC-0001",
            title="Fictional obligation",
            binding_instrument="Fictional instrument",
            clause="1",
            obligation_text="Fictional obligation text.",
            source_reference=source("SRC-FIC-OBLIGATION"),
        ),
        risk=RiskRecord(
            risk_id="RSK-FIC-0001",
            title="Fictional risk",
            risk_statement="Fictional risk statement.",
            source_reference=source("SRC-FIC-RISK"),
        ),
        control=PlanningControlRecord(
            control_id="CTL-FIC-0001",
            title="Fictional control",
            design_statement="Fictional control statement.",
            source_reference=source("SRC-FIC-CONTROL"),
        ),
        accountable_role=AccountableRoleRecord(
            accountability_id="ROLE-FIC-0001",
            subject_type=AccountabilitySubjectType.JOB_ROLE,
            subject_title="Fictional accountable role",
            accountability_statement="Fictional accountability statement.",
            source_reference=source("SRC-FIC-ROLE"),
        ),
        mate_assessment=approved_mate_assessment(),
    )


def approve_all_current_relationships(service_object) -> dict[str, object]:
    result: dict[str, object] = {}
    for number in range(1, 5):
        relationship_id = f"REL-FIC-000{number}"
        preview_state = preview(
            service_object, relationship_id, "Fictional relationship approval."
        )
        result = service_object.record_decision(
            relationship_id,
            {
                "relationship_version": 1,
                "decision": "APPROVED",
                "reason": "Fictional relationship approval.",
                "decision_key": f"relationship-default-trace-000{number}",
                "preview_token": preview_state["preview_token"],
            },
            auditor(),
        )
    return result


def test_queue_and_item_show_current_fictional_relationship_state(tmp_path: Path) -> None:
    review = service(tmp_path, trace_input_values)

    queue = review.get_queue(agent())
    item = review.get_item("REL-FIC-0001", agent())

    assert queue["result"]["code"] == "RELATIONSHIP_QUEUE_READY"
    assert queue["result"]["state"] == ActionResultState.NEEDS_REVIEW.value
    assert queue["queue"][0]["relationship_id"] == "REL-FIC-0001"
    assert item["result"]["code"] == "RELATIONSHIP_REVIEW_READY"
    assert item["state"]["current_version"] == 1
    assert item["state"]["source_support"] == ["SRC-FIC-OBLIGATION", "SRC-FIC-RISK"]
    assert item["state"]["gaps"]
    assert item["state"]["contradictions"]
    assert item["state"]["duplicate_warnings"]
    assert item["state"]["version_history"][0]["version"] == 1
    assert item["state"]["engagement_id"] == "ENG-FIC-0001"

    with WorkbenchStore(tmp_path / "local-data").connect() as connection:
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(relationship_review_items)"
            )
        }
    assert "engagement_id" in columns
    assert "is_fictional" not in columns


def test_relationship_identity_rows_reject_update_and_delete(tmp_path: Path) -> None:
    store = WorkbenchStore(tmp_path / "local-data")

    with store.connect() as connection:
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute(
                """UPDATE relationship_review_items SET title = 'Changed'
                   WHERE relationship_id = 'REL-FIC-0001'"""
            )
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute(
                """DELETE FROM relationship_review_items
                   WHERE relationship_id = 'REL-FIC-0001'"""
            )


def test_fictional_trace_input_snapshot_is_valid_and_immutable(tmp_path: Path) -> None:
    review = service(tmp_path)
    store = WorkbenchStore(tmp_path / "local-data")

    trace_inputs = trace_input_values()
    with store.connect() as connection:
        snapshot = connection.execute(
            """SELECT engagement_id, snapshot_json FROM relationship_trace_input_snapshots
               WHERE engagement_id = 'ENG-FIC-0001'"""
        ).fetchone()
        assert snapshot is not None
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute(
                """UPDATE relationship_trace_input_snapshots SET snapshot_json = '{}'
                   WHERE engagement_id = 'ENG-FIC-0001'"""
            )
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute(
                """DELETE FROM relationship_trace_input_snapshots
                   WHERE engagement_id = 'ENG-FIC-0001'"""
            )

    assert trace_inputs is not None
    assert trace_inputs.obligation.obligation_id == "OBL-FIC-0001"
    assert trace_inputs.control.control_id == "CTL-FIC-0001"
    assert len(trace_inputs.mate_assessment.decisions) == 4
    assert {decision.dimension for decision in trace_inputs.mate_assessment.decisions} == set(MateDimension)
    assert all(decision.decision_status is AuditorDecisionStatus.APPROVED for decision in trace_inputs.mate_assessment.decisions)
    assert trace_inputs.mate_assessment.dimensions.mandate is True
    assert trace_inputs.mate_assessment.dimensions.accountability is True
    assert trace_inputs.mate_assessment.dimensions.trigger is True
    assert trace_inputs.mate_assessment.dimensions.escalation is True


def test_default_service_creates_one_trace_from_fictional_snapshot(tmp_path: Path) -> None:
    review = service(tmp_path, trace_input_values)
    result = approve_all_current_relationships(review)

    with WorkbenchStore(tmp_path / "local-data").connect() as connection:
        trace_count = connection.execute(
            "SELECT COUNT(*) FROM accepted_planning_traces"
        ).fetchone()[0]

    assert result["result"]["code"] == "RELATIONSHIP_DECISION_RECORDED"
    assert result["trace_created"] is True
    assert trace_count == 1


@pytest.mark.parametrize("snapshot_json", [None, "{}"])
def test_missing_or_invalid_snapshot_rolls_back_completing_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot_json: str | None
) -> None:
    from src.ace.workbench.relationship_review import RelationshipReviewService
    from src.ace.workbench.relationship_review_storage import RelationshipReviewStorage

    store = WorkbenchStore(tmp_path / "local-data")
    with store.connect() as connection:
        if snapshot_json is None:
            connection.execute("DROP TRIGGER relationship_trace_input_snapshots_no_delete")
            connection.execute(
                "DELETE FROM relationship_trace_input_snapshots WHERE engagement_id = 'ENG-FIC-0001'"
            )
        else:
            connection.execute("DROP TRIGGER relationship_trace_input_snapshots_no_update")
            connection.execute(
                """UPDATE relationship_trace_input_snapshots SET snapshot_json = ?
                   WHERE engagement_id = 'ENG-FIC-0001'""",
                (snapshot_json,),
            )
        connection.commit()
    monkeypatch.setattr(RelationshipReviewStorage, "_seed", staticmethod(lambda connection: None))
    review = RelationshipReviewService(store)
    result = approve_all_current_relationships(review)

    with store.connect() as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "relationship_review_decisions",
                "relationship_review_events",
                "relationship_review_retries",
                "approved_relationships",
                "accepted_planning_traces",
            )
        }

    assert result["result"]["code"] == "RELATIONSHIP_MATE_REQUIRED"
    assert counts == {
        "relationship_review_decisions": 3,
        "relationship_review_events": 3,
        "relationship_review_retries": 3,
        "approved_relationships": 3,
        "accepted_planning_traces": 0,
    }


def test_nonfictional_context_blocks_completing_approval(tmp_path: Path) -> None:
    review = service(tmp_path)
    store = WorkbenchStore(tmp_path / "local-data")
    for number in range(1, 4):
        relationship_id = f"REL-FIC-000{number}"
        preview_state = preview(review, relationship_id, "Fictional relationship approval.")
        review.record_decision(
            relationship_id,
            {
                "relationship_version": 1,
                "decision": "APPROVED",
                "reason": "Fictional relationship approval.",
                "decision_key": f"relationship-nonfictional-000{number}",
                "preview_token": preview_state["preview_token"],
            },
            auditor(),
        )
    preview_state = preview(review, "REL-FIC-0004", "Fictional relationship approval.")
    with store.connect() as connection:
        connection.execute(
            """UPDATE engagement_setups SET data_classification = 'REAL_CLIENT'
               WHERE engagement_id = 'ENG-FIC-0001'"""
        )
        connection.commit()
    result = review.record_decision(
        "REL-FIC-0004",
        {
            "relationship_version": 1,
            "decision": "APPROVED",
            "reason": "Fictional relationship approval.",
            "decision_key": "relationship-nonfictional-0004",
            "preview_token": preview_state["preview_token"],
        },
        auditor(),
    )

    with store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM relationship_review_decisions").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM accepted_planning_traces").fetchone()[0] == 0

    assert result["result"]["code"] == "G0_REAL_CLIENT_BLOCKED"


def test_real_client_current_engagement_blocks_queue_and_item_data(tmp_path: Path) -> None:
    review = service(tmp_path)
    store = WorkbenchStore(tmp_path / "local-data")
    with store.connect() as connection:
        connection.execute(
            """UPDATE engagement_setups
               SET data_classification = 'REAL_CLIENT', is_fictional = 0
               WHERE engagement_id = 'ENG-FIC-0001'"""
        )
        connection.commit()

    queue = review.get_queue(agent())
    item = review.get_item("REL-FIC-0001", agent())

    assert queue["result"]["state"] == ActionResultState.BLOCKED.value
    assert queue["result"]["code"] == "G0_REAL_CLIENT_BLOCKED"
    assert "queue" not in queue
    assert item["result"]["state"] == ActionResultState.BLOCKED.value
    assert item["result"]["code"] == "G0_REAL_CLIENT_BLOCKED"
    assert "state" not in item


def test_missing_current_ready_engagement_blocks_all_review_paths(tmp_path: Path) -> None:
    from src.ace.workbench.relationship_review import RelationshipReviewService

    provider_call_count = 0

    def trace_input_provider():
        nonlocal provider_call_count
        provider_call_count += 1
        return trace_input_values()

    review = RelationshipReviewService(
        WorkbenchStore(tmp_path / "local-data"),
        trace_input_provider=trace_input_provider,
    )
    store = WorkbenchStore(tmp_path / "local-data")
    with store.connect() as connection:
        connection.execute("DELETE FROM current_engagement")
        connection.commit()

    results = (
        review.get_queue(agent()),
        review.get_item("REL-FIC-0001", agent()),
        review.save_draft(
            "REL-FIC-0001",
            {"relationship_version": 1, "draft_reason": "Fictional note."},
            agent(),
        ),
        review.request_approval_preview(
            "REL-FIC-0001",
            {"relationship_version": 1, "approval_reason": "Fictional approval."},
            agent(),
        ),
        review.record_decision(
            "REL-FIC-0001",
            {
                "relationship_version": 1,
                "decision": "REJECTED",
                "reason": "Fictional rejection.",
                "decision_key": "relationship-no-engagement",
                "preview_token": None,
            },
            auditor(),
        ),
    )

    assert all(
        result == {
            "result": {
                "state": "BLOCKED",
                "code": "RELATIONSHIP_ENGAGEMENT_REQUIRED",
                "message": "A current READY_FOR_CAPTURE Engagement is required.",
                "permitted_actions": [],
            }
        }
        for result in results
    )
    assert provider_call_count == 0


def test_agents_can_save_drafts_and_request_zero_write_previews(tmp_path: Path) -> None:
    review = service(tmp_path)
    store = WorkbenchStore(tmp_path / "local-data")

    saved = review.save_draft("REL-FIC-0001", draft(), agent())
    with store.connect() as connection:
        tables = (
            "relationship_review_items",
            "relationship_review_versions",
            "relationship_review_drafts",
            "relationship_review_decisions",
            "relationship_review_events",
            "relationship_review_retries",
            "approved_relationships",
            "accepted_planning_traces",
        )
        before = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }
        preview_state = preview(review)
        after = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }

    assert saved["result"]["code"] == "RELATIONSHIP_DRAFT_SAVED"
    assert saved["result"]["state"] == ActionResultState.OK.value
    assert preview_state["result"]["state"] == ActionResultState.NEEDS_APPROVAL.value
    assert len(preview_state["preview_token"]) == 64
    assert before == after


def test_permitted_actions_follow_relationship_actor_kind(tmp_path: Path) -> None:
    review = service(tmp_path)

    agent_queue = review.get_queue(agent())
    agent_item = review.get_item("REL-FIC-0001", agent())
    agent_draft = review.save_draft("REL-FIC-0001", draft(), agent())
    agent_preview = preview(review)
    auditor_queue = review.get_queue(auditor())
    auditor_item = review.get_item("REL-FIC-0001", auditor())
    auditor_draft = review.save_draft("REL-FIC-0001", draft(), auditor())
    auditor_preview = review.request_approval_preview(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "approval_reason": "The fictional relationship is approved.",
        },
        auditor(),
    )

    for response in (agent_queue, agent_item, agent_draft, agent_preview):
        assert "submit_decision" not in response["result"]["permitted_actions"]
    for response in (auditor_queue, auditor_item, auditor_draft, auditor_preview):
        assert "submit_decision" in response["result"]["permitted_actions"]


def test_saved_review_draft_does_not_change_immutable_proposal(tmp_path: Path) -> None:
    review = service(tmp_path)
    store = WorkbenchStore(tmp_path / "local-data")
    before = review.get_item("REL-FIC-0001", agent())["state"]

    saved = review.save_draft(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "proposed_decision": "CHANGES_REQUIRED",
            "draft_reason": "Ask for a clearer fictional source link.",
        },
        agent(),
    )
    after = review.get_item("REL-FIC-0001", agent())["state"]
    with store.connect() as connection:
        snapshot = connection.execute(
            """SELECT snapshot_json FROM relationship_review_versions
               WHERE relationship_id = 'REL-FIC-0001' AND relationship_version = 1"""
        ).fetchone()[0]

    assert saved["result"]["state"] == ActionResultState.OK.value
    assert after["rationale"] == before["rationale"]
    assert after["source_support"] == before["source_support"]
    assert "Ask for a clearer fictional source link." not in snapshot


def test_final_decisions_require_accountable_auditor_and_current_preview(tmp_path: Path) -> None:
    review = service(tmp_path)
    preview_state = preview(review)
    request = {
        "relationship_version": 1,
        "decision": "APPROVED",
        "reason": "The fictional relationship is approved.",
        "decision_key": "relationship-decision-0001",
        "preview_token": preview_state["preview_token"],
    }

    blocked = review.record_decision("REL-FIC-0001", request, agent())
    stale = review.record_decision(
        "REL-FIC-0001",
        {**request, "reason": "A different fictional approval reason."},
        auditor(),
    )
    direct = review.record_decision(
        "REL-FIC-0001",
        {**request, "decision": "REJECTED", "decision_key": "relationship-decision-0002", "preview_token": None},
        auditor(),
    )

    assert blocked["result"]["code"] == "ACCOUNTABLE_AUDITOR_REQUIRED"
    assert stale["result"]["code"] == "RELATIONSHIP_PREVIEW_STALE"
    assert direct["result"]["code"] == "RELATIONSHIP_DECISION_RECORDED"


def test_changed_approval_reason_makes_preview_stale(tmp_path: Path) -> None:
    review = service(tmp_path)
    preview_state = review.request_approval_preview(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "approval_reason": "The fictional relationship is supported.",
        },
        agent(),
    )

    result = review.record_decision(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "decision": "APPROVED",
            "reason": "The fictional relationship has different support.",
            "decision_key": "relationship-decision-reason-change",
            "preview_token": preview_state["preview_token"],
        },
        auditor(),
    )

    assert result["result"]["state"] == ActionResultState.BLOCKED.value
    assert result["result"]["code"] == "RELATIONSHIP_PREVIEW_STALE"


def test_active_engagement_change_makes_approval_preview_stale(tmp_path: Path) -> None:
    review = service(tmp_path)
    preview_state = preview(review)
    store = WorkbenchStore(tmp_path / "local-data")
    with store.connect() as connection:
        connection.execute(
            """INSERT OR IGNORE INTO engagement_setups (
                   engagement_id, creation_attempt_key, title, reference,
                   data_classification, is_fictional, state, created_at, activated_at
               ) VALUES (?, ?, ?, ?, 'FICTIONAL', 1, 'READY_FOR_CAPTURE', ?, ?)""",
            (
                "ENG-FIC-0002",
                "fictional-engagement-0002",
                "Second Fictional Engagement",
                "FIC-0002",
                "2026-08-14T00:00:00Z",
                "2026-08-14T00:00:00Z",
            ),
        )
        connection.execute(
            "UPDATE current_engagement SET engagement_id = 'ENG-FIC-0002' WHERE current_slot = 1"
        )
        connection.commit()

    result = review.record_decision(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "decision": "APPROVED",
            "reason": "The fictional relationship is approved.",
            "decision_key": "relationship-active-change",
            "preview_token": preview_state["preview_token"],
        },
        auditor(),
    )

    assert result["result"]["state"] == ActionResultState.BLOCKED.value
    assert result["result"]["code"] == "RELATIONSHIP_PREVIEW_STALE"


def test_g0_blocks_nonfictional_relationship_before_any_final_write(tmp_path: Path) -> None:
    from src.ace.workbench.relationship_review import RelationshipReviewService

    provider_call_count = 0

    def trace_input_provider():
        nonlocal provider_call_count
        provider_call_count += 1
        return trace_input_values()

    review = RelationshipReviewService(
        WorkbenchStore(tmp_path / "local-data"),
        trace_input_provider=trace_input_provider,
    )
    store = WorkbenchStore(tmp_path / "local-data")
    with store.connect() as connection:
        connection.execute(
            """UPDATE engagement_setups SET is_fictional = 0,
                      data_classification = 'REAL_CLIENT'
               WHERE engagement_id = 'ENG-FIC-0001'"""
        )
        connection.commit()

    result = review.record_decision(
        "REL-FIC-0001",
        {"relationship_version": 1, "decision": "REJECTED", "reason": "Fictional test boundary.", "decision_key": "relationship-decision-0005", "preview_token": None},
        auditor(),
    )
    with store.connect() as connection:
        decision_count = connection.execute("SELECT COUNT(*) FROM relationship_review_decisions").fetchone()[0]

    assert result["result"]["state"] == ActionResultState.BLOCKED.value
    assert result["result"]["code"] == "G0_REAL_CLIENT_BLOCKED"
    assert decision_count == 0
    assert provider_call_count == 0


def test_real_client_engagement_blocks_draft_and_preview_without_writes(
    tmp_path: Path,
) -> None:
    review = service(tmp_path)
    store = WorkbenchStore(tmp_path / "local-data")
    with store.connect() as connection:
        relationship_tables = (
            "relationship_review_items",
            "relationship_review_versions",
            "relationship_review_drafts",
            "relationship_review_decisions",
            "relationship_review_events",
            "relationship_review_retries",
            "approved_relationships",
            "accepted_planning_traces",
        )
        before = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in relationship_tables
        }
        connection.execute(
            """UPDATE engagement_setups SET is_fictional = 0,
                      data_classification = 'REAL_CLIENT'
               WHERE engagement_id = 'ENG-FIC-0001'"""
        )
        connection.commit()

    draft_result = review.save_draft("REL-FIC-0001", draft(), agent())
    preview_result = review.request_approval_preview(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "approval_reason": "Fictional approval reason.",
        },
        agent(),
    )
    with store.connect() as connection:
        after = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in relationship_tables
        }

    for result in (draft_result, preview_result):
        assert result["result"]["state"] == ActionResultState.BLOCKED.value
        assert result["result"]["code"] == "G0_REAL_CLIENT_BLOCKED"
        assert "state" not in result
    assert after == before


def test_final_transaction_retry_conflict_changes_required_and_immutability(tmp_path: Path) -> None:
    review = service(tmp_path)
    first = approve(review)
    retry = approve(review)
    conflict = review.record_decision(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "decision": "APPROVED",
            "reason": "A different fictional reason.",
            "decision_key": "relationship-decision-0001",
            "preview_token": preview(review)["preview_token"],
        },
        auditor(),
    )
    changes = review.record_decision(
        "REL-FIC-0002",
        {
            "relationship_version": 1,
            "decision": "CHANGES_REQUIRED",
            "reason": "Add a fictional source.",
            "decision_key": "relationship-decision-0002",
            "preview_token": None,
        },
        auditor(),
    )
    store = WorkbenchStore(tmp_path / "local-data")
    with store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM approved_relationships").fetchone()[0] == 1
        proposal_snapshot = json.loads(connection.execute(
            """SELECT snapshot_json FROM relationship_review_versions
               WHERE relationship_id = 'REL-FIC-0001' AND relationship_version = 1"""
        ).fetchone()[0])
        approved_snapshot = json.loads(connection.execute(
            """SELECT snapshot_json FROM approved_relationships
               WHERE relationship_id = 'REL-FIC-0001' AND relationship_version = 1"""
        ).fetchone()[0])
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute("DELETE FROM relationship_review_decisions")
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute("UPDATE relationship_review_versions SET snapshot_json = '{}' ")

    assert first["result"]["code"] == "RELATIONSHIP_DECISION_RECORDED"
    assert retry == first
    assert conflict["result"]["code"] == "RELATIONSHIP_DECISION_KEY_CONFLICT"
    assert approved_snapshot == {
        "identity": {
            "engagement_id": "ENG-FIC-0001",
            "relationship_id": "REL-FIC-0001",
            "relationship_type": "OBLIGATION_APPLIES_TO_RISK",
            "source_record_id": "OBL-FIC-0001",
            "target_record_id": "RSK-FIC-0001",
            "title": "Fictional obligation applies to risk",
        },
        "relationship_version": 1,
        "proposal": proposal_snapshot,
    }
    assert changes["state"]["current_version"] == 1
    assert len(changes["state"]["version_history"]) == 1
    assert "revision_request" not in changes["state"]["version_history"][0]


def test_second_decision_key_for_decided_version_returns_controlled_result(
    tmp_path: Path,
) -> None:
    review = service(tmp_path)
    base_request = {
        "relationship_version": 1,
        "decision": "REJECTED",
        "reason": "The fictional relationship is not supported.",
        "preview_token": None,
    }
    first = review.record_decision(
        "REL-FIC-0001",
        {**base_request, "decision_key": "relationship-first-decision"},
        auditor(),
    )

    second = review.record_decision(
        "REL-FIC-0001",
        {**base_request, "decision_key": "relationship-second-decision"},
        auditor(),
    )

    assert first["result"]["code"] == "RELATIONSHIP_DECISION_RECORDED"
    assert second["result"]["state"] == ActionResultState.BLOCKED.value
    assert second["result"]["code"] == "RELATIONSHIP_DECISION_ALREADY_RECORDED"


def test_decision_key_reuse_for_another_relationship_conflicts(tmp_path: Path) -> None:
    review = service(tmp_path)
    first = review.record_decision(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "decision": "REJECTED",
            "reason": "Fictional rejection.",
            "decision_key": "relationship-cross-target",
            "preview_token": None,
        },
        auditor(),
    )

    second = review.record_decision(
        "REL-FIC-0002",
        {
            "relationship_version": 1,
            "decision": "REJECTED",
            "reason": "Fictional rejection.",
            "decision_key": "relationship-cross-target",
            "preview_token": None,
        },
        auditor(),
    )

    assert first["result"]["code"] == "RELATIONSHIP_DECISION_RECORDED"
    assert second["result"]["state"] == ActionResultState.BLOCKED.value
    assert second["result"]["code"] == "RELATIONSHIP_DECISION_KEY_CONFLICT"


def test_retry_rows_are_target_bound_and_immutable(tmp_path: Path) -> None:
    review = service(tmp_path)
    review.record_decision(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "decision": "REJECTED",
            "reason": "Fictional rejection.",
            "decision_key": "relationship-immutable-retry",
            "preview_token": None,
        },
        auditor(),
    )

    with WorkbenchStore(tmp_path / "local-data").connect() as connection:
        retry = connection.execute(
            """SELECT relationship_id, relationship_version
               FROM relationship_review_retries
               WHERE decision_key = 'relationship-immutable-retry'"""
        ).fetchone()
        assert dict(retry) == {
            "relationship_id": "REL-FIC-0001",
            "relationship_version": 1,
        }
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute(
                """UPDATE relationship_review_retries SET request_sha256 = 'changed'
                   WHERE decision_key = 'relationship-immutable-retry'"""
            )
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute(
                """DELETE FROM relationship_review_retries
                   WHERE decision_key = 'relationship-immutable-retry'"""
            )


def test_service_rejects_blank_final_reason_before_writing(tmp_path: Path) -> None:
    review = service(tmp_path)

    with pytest.raises(ValueError, match="reason"):
        review.record_decision(
            "REL-FIC-0001",
            {
                "relationship_version": 1,
                "decision": "REJECTED",
                "reason": "   ",
                "decision_key": "relationship-blank-reason",
                "preview_token": None,
            },
            auditor(),
        )

    with WorkbenchStore(tmp_path / "local-data").connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM relationship_review_decisions"
        ).fetchone()[0] == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"relationship_version": True},
        {"relationship_version": 0},
        {"reason": "x" * 4001},
        {"decision_key": "bad key"},
        {"preview_token": "not-a-token"},
    ],
)
def test_service_rejects_malformed_final_decision_fields(
    tmp_path: Path, changes: dict[str, object]
) -> None:
    review = service(tmp_path)
    request = {
        "relationship_version": 1,
        "decision": "REJECTED",
        "reason": "Fictional rejection.",
        "decision_key": "relationship-valid-request",
        "preview_token": None,
        **changes,
    }

    with pytest.raises(ValueError):
        review.record_decision("REL-FIC-0001", request, auditor())


def test_stale_version_and_failed_final_insert_leave_no_partial_records(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    review = service(tmp_path)
    stale = review.record_decision(
        "REL-FIC-0001",
        {"relationship_version": 99, "decision": "REJECTED", "reason": "Fictional.", "decision_key": "relationship-decision-0003", "preview_token": None},
        auditor(),
    )
    original = review._storage._insert_event
    monkeypatch.setattr(review._storage, "_insert_event", lambda *args: (_ for _ in ()).throw(sqlite3.IntegrityError("forced final failure")))
    with pytest.raises(sqlite3.IntegrityError, match="forced final failure"):
        review.record_decision(
            "REL-FIC-0001",
            {"relationship_version": 1, "decision": "REJECTED", "reason": "Fictional.", "decision_key": "relationship-decision-0004", "preview_token": None},
            auditor(),
        )
    monkeypatch.setattr(review._storage, "_insert_event", original)
    with WorkbenchStore(tmp_path / "local-data").connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM relationship_review_decisions").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM relationship_review_retries").fetchone()[0] == 0

    assert stale["result"]["state"] == ActionResultState.BLOCKED.value
    assert stale["result"]["code"] == "RELATIONSHIP_VERSION_STALE"


def test_late_retry_failure_rolls_back_every_final_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ace.workbench.relationship_review import RelationshipReviewService

    store = WorkbenchStore(tmp_path / "local-data")
    review = RelationshipReviewService(
        store,
        trace_input_provider=lambda: trace_input_values(),
    )
    reason = "Fictional relationship approval."
    for number in range(1, 4):
        relationship_id = f"REL-FIC-000{number}"
        preview_state = preview(review, relationship_id, reason)
        review.record_decision(
            relationship_id,
            {
                "relationship_version": 1,
                "decision": "APPROVED",
                "reason": reason,
                "decision_key": f"relationship-rollback-00{number}",
                "preview_token": preview_state["preview_token"],
            },
            auditor(),
        )

    tables = (
        "relationship_review_decisions",
        "relationship_review_events",
        "approved_relationships",
        "relationship_review_retries",
        "accepted_planning_traces",
    )
    with store.connect() as connection:
        baseline = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }

    trace_insert_attempts: list[str] = []
    original_connect = store.connect

    def instrumented_connect() -> sqlite3.Connection:
        connection = original_connect()
        connection.create_function(
            "mark_trace_insert",
            0,
            lambda: trace_insert_attempts.append("attempted"),
        )
        return connection

    monkeypatch.setattr(store, "connect", instrumented_connect)
    with store.connect() as connection:
        connection.execute(
            """CREATE TRIGGER mark_trace_insert_attempt
               BEFORE INSERT ON accepted_planning_traces
               BEGIN SELECT mark_trace_insert(); END"""
        )
        connection.execute(
            """CREATE TRIGGER force_retry_failure
               BEFORE INSERT ON relationship_review_retries
               BEGIN SELECT RAISE(ABORT, 'forced late retry failure'); END"""
        )
        connection.commit()

    preview_state = preview(review, "REL-FIC-0004", reason)
    with pytest.raises(sqlite3.DatabaseError, match="forced late retry failure"):
        review.record_decision(
            "REL-FIC-0004",
            {
                "relationship_version": 1,
                "decision": "APPROVED",
                "reason": reason,
                "decision_key": "relationship-late-failure",
                "preview_token": preview_state["preview_token"],
            },
            auditor(),
        )

    with store.connect() as connection:
        after = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }
        fourth_decisions = connection.execute(
            """SELECT COUNT(*) FROM relationship_review_decisions
               WHERE relationship_id = 'REL-FIC-0004'
                 AND relationship_version = 1"""
        ).fetchone()[0]
        fourth_approvals = connection.execute(
            """SELECT COUNT(*) FROM approved_relationships
               WHERE relationship_id = 'REL-FIC-0004'
                 AND relationship_version = 1"""
        ).fetchone()[0]

    assert trace_insert_attempts == ["attempted"]
    assert after == baseline
    assert fourth_decisions == 0
    assert fourth_approvals == 0
    assert after["accepted_planning_traces"] == 0


def test_all_current_relationship_approvals_use_provider_and_existing_trace_engine(tmp_path: Path) -> None:
    from src.ace.workbench.relationship_review import RelationshipReviewService

    inputs = trace_input_values()
    provider_call_count = 0

    def trace_input_provider():
        nonlocal provider_call_count
        provider_call_count += 1
        return inputs

    review = RelationshipReviewService(
        WorkbenchStore(tmp_path / "local-data"),
        trace_input_provider=trace_input_provider,
    )
    for number in range(1, 5):
        relationship_id = f"REL-FIC-000{number}"
        preview_state = preview(
            review, relationship_id, "Fictional relationship approval."
        )
        result = review.record_decision(
            relationship_id,
            {"relationship_version": 1, "decision": "APPROVED", "reason": "Fictional relationship approval.", "decision_key": f"relationship-decision-00{number}0", "preview_token": preview_state["preview_token"]},
            auditor(),
        )
        assert provider_call_count == (1 if number == 4 else 0)

    with WorkbenchStore(tmp_path / "local-data").connect() as connection:
        trace_count = connection.execute("SELECT COUNT(*) FROM accepted_planning_traces").fetchone()[0]
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute("DELETE FROM accepted_planning_traces")

    assert result["result"]["code"] == "RELATIONSHIP_DECISION_RECORDED"
    assert result["trace_created"] is True
    assert trace_count == 1
    assert provider_call_count == 1


@pytest.mark.parametrize("decision", ["REJECTED", "CHANGES_REQUIRED"])
def test_provider_does_not_run_for_non_approved_final_decisions(
    tmp_path: Path, decision: str
) -> None:
    from src.ace.workbench.relationship_review import RelationshipReviewService

    provider_call_count = 0

    def trace_input_provider():
        nonlocal provider_call_count
        provider_call_count += 1
        return trace_input_values()

    review = RelationshipReviewService(
        WorkbenchStore(tmp_path / "local-data"),
        trace_input_provider=trace_input_provider,
    )
    result = review.record_decision(
        "REL-FIC-0001",
        {
            "relationship_version": 1,
            "decision": decision,
            "reason": "Fictional final decision.",
            "decision_key": f"relationship-{decision.lower()}-provider-order",
            "preview_token": None,
        },
        auditor(),
    )

    assert result["result"]["code"] == "RELATIONSHIP_DECISION_RECORDED"
    assert provider_call_count == 0


def test_trace_creation_uses_only_provider_domain_facts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ace.engine.tracing import build_accepted_planning_trace as domain_builder
    from src.ace.workbench import relationship_review_storage
    from src.ace.workbench.relationship_review import RelationshipReviewService

    inputs = trace_input_values()
    called = False

    def checked_builder(**values):
        nonlocal called
        called = True
        assert values["obligation"] is inputs.obligation
        assert values["risk"] is inputs.risk
        assert values["control"] is inputs.control
        assert values["accountable_role"] is inputs.accountable_role
        assert values["mate_assessment"] is inputs.mate_assessment
        return domain_builder(**values)

    monkeypatch.setattr(
        relationship_review_storage,
        "build_accepted_planning_trace",
        checked_builder,
    )
    review = RelationshipReviewService(
        WorkbenchStore(tmp_path / "local-data"),
        trace_input_provider=lambda: inputs,
    )
    for number in range(1, 5):
        relationship_id = f"REL-FIC-000{number}"
        preview_state = review.request_approval_preview(
            relationship_id,
            {
                "relationship_version": 1,
                "approval_reason": "Fictional relationship approval.",
            },
            agent(),
        )
        review.record_decision(
            relationship_id,
            {
                "relationship_version": 1,
                "decision": "APPROVED",
                "reason": "Fictional relationship approval.",
                "decision_key": f"relationship-provider-00{number}",
                "preview_token": preview_state["preview_token"],
            },
            auditor(),
        )

    assert called is True


def test_final_approved_relationship_rolls_back_until_trace_inputs_are_available(tmp_path: Path) -> None:
    from src.ace.workbench.relationship_review import RelationshipReviewService

    provided_inputs = {"value": None}
    review = RelationshipReviewService(
        WorkbenchStore(tmp_path / "local-data"),
        trace_input_provider=lambda: provided_inputs["value"],
    )
    request: dict[str, object] = {}
    for number in range(1, 5):
        relationship_id = f"REL-FIC-000{number}"
        preview_state = preview(
            review, relationship_id, "Fictional relationship approval."
        )
        request = {
            "relationship_version": 1,
            "decision": "APPROVED",
            "reason": "Fictional relationship approval.",
            "decision_key": f"relationship-decision-01{number}0",
            "preview_token": preview_state["preview_token"],
        }
        result = review.record_decision(
            relationship_id,
            request,
            auditor(),
        )

    with WorkbenchStore(tmp_path / "local-data").connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM relationship_review_decisions").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM relationship_review_events").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM relationship_review_retries").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM approved_relationships").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM accepted_planning_traces").fetchone()[0] == 0

    assert result["result"]["state"] == ActionResultState.NEEDS_EVIDENCE.value
    assert result["result"]["code"] == "RELATIONSHIP_MATE_REQUIRED"
    provided_inputs["value"] = trace_input_values()
    recovered = review.record_decision("REL-FIC-0004", request, auditor())

    with WorkbenchStore(tmp_path / "local-data").connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM relationship_review_decisions").fetchone()[0] == 4
        assert connection.execute("SELECT COUNT(*) FROM relationship_review_events").fetchone()[0] == 4
        assert connection.execute("SELECT COUNT(*) FROM relationship_review_retries").fetchone()[0] == 4
        assert connection.execute("SELECT COUNT(*) FROM approved_relationships").fetchone()[0] == 4
        assert connection.execute("SELECT COUNT(*) FROM accepted_planning_traces").fetchone()[0] == 1

    assert recovered["result"]["code"] == "RELATIONSHIP_DECISION_RECORDED"
    assert recovered["trace_created"] is True


def test_revision_requires_auditor_and_current_changes_required_decision(tmp_path: Path) -> None:
    review = service(tmp_path)
    request = revision_request()

    blocked = review.create_revision("REL-FIC-0001", request, agent())
    missing = review.create_revision("REL-FIC-0001", request, auditor())
    changes_required(review)
    created = review.create_revision("REL-FIC-0001", request, auditor())

    assert blocked["result"]["code"] == "ACCOUNTABLE_AUDITOR_REQUIRED"
    assert missing["result"]["code"] == "RELATIONSHIP_REVISION_NOT_ALLOWED"
    assert created["result"]["code"] == "RELATIONSHIP_REVISION_CREATED"
    assert created["state"]["current_version"] == 2
    corrected = created["state"]["version_history"][-1]
    assert corrected["rationale"] == request["rationale"]
    assert corrected["supporting_source_ids"] == request["supporting_source_ids"]
    assert corrected["revision_request"] == "Add a clearer fictional source link."


@pytest.mark.parametrize(
    "sources",
    [
        ["SRC-FIC-UNKNOWN"],
        ["SRC-FIC-OBLIGATION", "SRC-FIC-OBLIGATION"],
    ],
)
def test_revision_blocks_unknown_or_duplicate_supporting_sources(
    tmp_path: Path, sources: list[str]
) -> None:
    review = service(tmp_path)
    changes_required(review)

    blocked = review.create_revision(
        "REL-FIC-0001",
        {**revision_request(), "supporting_source_ids": sources},
        auditor(),
    )

    assert blocked["result"]["state"] == ActionResultState.BLOCKED.value
    assert blocked["result"]["code"] == "RELATIONSHIP_REVISION_SOURCE_BOUNDARY_INVALID"
    assert review.get_item("REL-FIC-0001", agent())["state"]["current_version"] == 1


def test_allowed_revision_can_be_approved_into_one_accepted_trace(tmp_path: Path) -> None:
    from src.ace.workbench.relationship_review import RelationshipReviewService

    store = WorkbenchStore(tmp_path / "local-data")
    review = RelationshipReviewService(store, trace_input_provider=trace_input_values)
    changes_required(review)
    revised = review.create_revision("REL-FIC-0001", revision_request(), auditor())
    revision_preview = review.request_approval_preview(
        "REL-FIC-0001",
        {
            "relationship_version": 2,
            "approval_reason": "Corrected fictional relationship approval.",
        },
        agent(),
    )
    review.record_decision(
        "REL-FIC-0001",
        {
            "relationship_version": 2,
            "decision": "APPROVED",
            "reason": "Corrected fictional relationship approval.",
            "decision_key": "relationship-revision-approved-0001",
            "preview_token": revision_preview["preview_token"],
        },
        auditor(),
    )
    for number in range(2, 5):
        relationship_id = f"REL-FIC-000{number}"
        preview_state = preview(review, relationship_id, "Fictional relationship approval.")
        result = review.record_decision(
            relationship_id,
            {
                "relationship_version": 1,
                "decision": "APPROVED",
                "reason": "Fictional relationship approval.",
                "decision_key": f"relationship-trace-approval-000{number}",
                "preview_token": preview_state["preview_token"],
            },
            auditor(),
        )

    with store.connect() as connection:
        trace_count = connection.execute(
            "SELECT COUNT(*) FROM accepted_planning_traces"
        ).fetchone()[0]

    assert revised["result"]["code"] == "RELATIONSHIP_REVISION_CREATED"
    assert result["trace_created"] is True
    assert trace_count == 1


@pytest.mark.parametrize("decision", ["APPROVED", "REJECTED"])
def test_revision_rejects_other_final_decisions(tmp_path: Path, decision: str) -> None:
    review = service(tmp_path)
    request = {
        "relationship_version": 1,
        "decision": decision,
        "reason": "Fictional final decision.",
        "decision_key": f"relationship-{decision.lower()}-0001",
        "preview_token": None,
    }
    if decision == "APPROVED":
        request["preview_token"] = preview(review, reason=request["reason"])["preview_token"]
    review.record_decision("REL-FIC-0001", request, auditor())

    blocked = review.create_revision("REL-FIC-0001", revision_request(), auditor())

    assert blocked["result"]["code"] == "RELATIONSHIP_REVISION_NOT_ALLOWED"


def test_revision_is_immutable_idempotent_and_rejects_stale_or_conflicting_keys(tmp_path: Path) -> None:
    review = service(tmp_path)
    store = WorkbenchStore(tmp_path / "local-data")
    changes_required(review)
    request = revision_request()
    created = review.create_revision("REL-FIC-0001", request, auditor())
    retry = review.create_revision("REL-FIC-0001", request, auditor())
    conflict = review.create_revision(
        "REL-FIC-0001", {**request, "rationale": "Different fictional correction."}, auditor()
    )
    stale = review.create_revision("REL-FIC-0001", revision_request(1, "relationship-revision-0002"), auditor())

    with store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM relationship_review_versions WHERE relationship_id = 'REL-FIC-0001'"
        ).fetchone()[0] == 2
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            connection.execute(
                "UPDATE relationship_review_versions SET snapshot_json = '{}' WHERE relationship_id = 'REL-FIC-0001'"
            )

    assert retry == created
    assert conflict["result"]["code"] == "RELATIONSHIP_REVISION_KEY_CONFLICT"
    assert stale["result"]["code"] == "RELATIONSHIP_REVISION_STALE"


def test_revision_is_blocked_by_g0(tmp_path: Path) -> None:
    review = service(tmp_path)
    store = WorkbenchStore(tmp_path / "local-data")
    changes_required(review)
    with store.connect() as connection:
        connection.execute(
            "UPDATE engagement_setups SET data_classification = 'REAL_CLIENT' WHERE engagement_id = 'ENG-FIC-0001'"
        )
        connection.commit()

    blocked = review.create_revision("REL-FIC-0001", revision_request(), auditor())

    assert blocked["result"]["code"] == "G0_REAL_CLIENT_BLOCKED"
