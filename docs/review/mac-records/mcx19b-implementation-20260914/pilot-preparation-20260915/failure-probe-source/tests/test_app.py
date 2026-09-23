from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.ace.app import SAMPLE_CONTROLS, app
from src.ace.domain.enums import ControlRating, HazardCategory
from src.ace.domain.models import LOW_CONFIDENCE_FLAG
from src.ace.workbench import routes

client = TestClient(app)


@pytest.fixture
def workbench_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path / "sqe-local-data"))
    return TestClient(app)


def relationship_review_workbench_page(client: TestClient) -> str:
    response = client.get("/workbench", auth=("auditor", "fictional-password"))

    assert response.status_code == 200
    return response.text


def test_health_endpoint_returns_exact_engagement_status() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "system": "Assurance Compass Engine",
        "status": "ONLINE",
        "audit_engagement": "Squadron Energy WHS Governance",
    }


def test_only_the_approved_routes_are_exposed() -> None:
    route_methods = {}
    pending_routes = list(app.routes)
    while pending_routes:
        route = pending_routes.pop()
        nested_router = getattr(route, "original_router", None)
        nested_routes = getattr(route, "routes", None) or getattr(
            nested_router, "routes", None
        )
        if nested_routes is not None:
            pending_routes.extend(nested_routes)
            continue
        route_methods.setdefault(route.path, set()).update(route.methods)

    assert route_methods == {
        "/": {"GET"},
        "/evaluations": {"GET"},
        "/workbench": {"GET"},
        "/workbench/engagements/new": {"GET"},
        "/workbench/summary": {"GET"},
        "/workbench/engagement/summary": {"GET"},
        "/workbench/engagement/graph": {"GET"},
        "/workbench/engagement/graph/export": {"GET"},
        "/workbench/api/v1/engagements": {"POST"},
        "/workbench/api/v1/engagements/sync": {"POST"},
        "/workbench/api/v1/engagements/current": {"GET"},
        "/workbench/api/v1/engagements/{engagement_id}": {"GET"},
        "/workbench/api/v1/engagements/{engagement_id}/activate": {"POST"},
        "/workbench/api/v1/engagements/{engagement_id}/current": {"PUT"},
        "/workbench/api/v1/evidence": {"POST"},
        "/workbench/api/v1/evidence/{evidence_id}/review": {"GET"},
        "/workbench/api/v1/evidence/{evidence_id}/suggestions": {"GET"},
        "/workbench/api/v1/evidence/{evidence_id}/review/context": {"PUT"},
        "/workbench/api/v1/evidence/{evidence_id}/proposed-links": {"POST"},
        "/workbench/api/v1/evidence/{evidence_id}/review/complete": {"POST"},
        "/workbench/api/v1/audit-questions": {"POST"},
        "/workbench/api/v1/audit-questions/{question_id}/versions": {"POST"},
        "/workbench/api/v1/audit-questions/{question_id}/decisions": {"POST"},
        "/workbench/evidence": {"POST"},
        "/workbench/evidence/{evidence_id}/media": {"GET"},
        "/workbench/evidence/{evidence_id}/review": {"GET", "POST"},
        "/workbench/relationship-reviews/{relationship_id}": {"GET"},
        "/workbench/api/v1/relationship-reviews": {"GET"},
        "/workbench/api/v1/relationship-reviews/{relationship_id}": {"GET"},
        "/workbench/api/v1/relationship-reviews/{relationship_id}/draft": {"PUT"},
        "/workbench/api/v1/relationship-reviews/{relationship_id}/approval-preview": {"POST"},
        "/workbench/api/v1/relationship-reviews/{relationship_id}/decision": {"POST"},
        "/workbench/api/v1/relationship-reviews/{relationship_id}/revisions": {"POST"},
        "/workbench/api/v1/engagements/export": {"POST"},
        "/workbench/api/v1/engagements/export/{export_id}": {"GET"},
        "/client": {"GET"},
        "/client/api/v1/release/current": {"GET"},
    }


def test_sample_controls_are_immutable_and_cover_required_hazards() -> None:
    assert isinstance(SAMPLE_CONTROLS, tuple)
    assert {control.hazard_category for control in SAMPLE_CONTROLS} == {
        HazardCategory.BESS_THERMAL_RUNAWAY,
        HazardCategory.HV_ENERGIZATION,
        HazardCategory.ARC_FLASH,
        HazardCategory.SIMOPS,
        HazardCategory.SOCI_CYBER_PHYSICAL,
    }


def test_sample_set_exercises_low_confidence_flag() -> None:
    flagged_controls = [
        control
        for control in SAMPLE_CONTROLS
        if control.confidence_score < 0.8
    ]

    assert len(flagged_controls) == 1
    assert flagged_controls[0].reviewer_notes == LOW_CONFIDENCE_FLAG


def test_evaluations_endpoint_returns_five_live_results() -> None:
    response = client.get("/evaluations")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 5
    assert [result["control_id"] for result in results] == [
        "ACE-BESS-001",
        "ACE-HV-001",
        "ACE-ARC-001",
        "ACE-SIMOPS-001",
        "ACE-SOCI-001",
    ]
    assert [result["rating"] for result in results] == [
        ControlRating.ADEQUATE.value,
        ControlRating.PARTIALLY_ADEQUATE.value,
        ControlRating.INADEQUATE.value,
        ControlRating.PARTIALLY_ADEQUATE.value,
        ControlRating.INADEQUATE.value,
    ]
    assert all("timestamp" in result for result in results)
    assert all("reasoning" in result for result in results)


def test_workbench_relationship_review_queue_displays_item_fields(
    workbench_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class QueueService:
        def get_queue(self, auditor: object) -> dict[str, object]:
            assert getattr(auditor, "kind").value == "ACCOUNTABLE_AUDITOR"
            assert getattr(auditor, "actor_id") == "auditor"
            return {
                "result": {"message": "Fictional queue is ready."},
                "engagement_id": "fictional-engagement-001",
                "queue": [
                    {
                        "relationship_id": "fictional-relationship-001",
                        "engagement_id": "fictional-engagement-001",
                        "title": "Fictional < Relationship",
                        "relationship_type": "SUPPORTS & TESTS",
                        "current_version": 7,
                        "material_risk_priority": "HIGH & URGENT",
                        "waiting_since": "2026-08-15T10:00:00+10:00",
                    }
                ],
            }

    monkeypatch.setattr(routes, "relationship_review_service", lambda: QueueService())
    page = relationship_review_workbench_page(workbench_client)

    assert "<h2>Relationship Reviews</h2>" in page
    assert 'id="relationship-reviews"' in page
    assert "Fictional &lt; Relationship" in page
    assert "SUPPORTS &amp; TESTS" in page
    assert "fictional-engagement-001" in page
    assert "Version 7" in page
    assert "HIGH &amp; URGENT" in page
    assert "Waiting since 2026-08-15T10:00:00+10:00" in page
    assert "<strong>Fictional < Relationship</strong>" not in page


def test_workbench_relationship_review_queue_uses_encoded_navigation_links(
    workbench_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class QueueService:
        def get_queue(self, auditor: object) -> dict[str, object]:
            return {
                "result": {"message": "Fictional queue is ready."},
                "engagement_id": "fictional-engagement-002",
                "queue": [
                    {
                        "relationship_id": "fictional/review?item#1",
                        "engagement_id": "fictional-engagement-002",
                        "title": "Fictional relationship",
                        "relationship_type": "SUPPORTS",
                        "current_version": 1,
                        "material_risk_priority": "MEDIUM",
                        "waiting_since": "2026-08-15T11:00:00+10:00",
                    }
                ],
            }

    monkeypatch.setattr(routes, "relationship_review_service", lambda: QueueService())
    page = relationship_review_workbench_page(workbench_client)

    assert 'href="/workbench/relationship-reviews/fictional%2Freview%3Fitem%231"' in page


def test_workbench_relationship_review_queue_has_empty_state(
    workbench_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class QueueService:
        def get_queue(self, auditor: object) -> dict[str, object]:
            return {
                "result": {"message": "Fictional queue is ready."},
                "engagement_id": "fictional-engagement-003",
                "queue": [],
            }

    monkeypatch.setattr(routes, "relationship_review_service", lambda: QueueService())
    page = relationship_review_workbench_page(workbench_client)

    assert "No Relationship Reviews need review." in page


def test_workbench_relationship_review_queue_has_controlled_failure_state(
    workbench_client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    class QueueService:
        def get_queue(self, auditor: object) -> dict[str, object]:
            raise RuntimeError("Fictional queue storage failure")

    monkeypatch.setattr(routes, "relationship_review_service", lambda: QueueService())
    caplog.set_level("ERROR", logger=routes.__name__)
    page = relationship_review_workbench_page(workbench_client)

    assert "Relationship Review queue is not available" in caplog.text
    assert "Relationship Reviews are not available." in page
    assert "Fictional queue storage failure" not in page
