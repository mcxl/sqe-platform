from fastapi.testclient import TestClient

from src.ace.app import SAMPLE_CONTROLS, app
from src.ace.domain.enums import ControlRating, HazardCategory
from src.ace.domain.models import LOW_CONFIDENCE_FLAG

client = TestClient(app)


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
        route_methods[route.path] = route.methods

    assert route_methods == {
        "/": {"GET"},
        "/evaluations": {"GET"},
        "/workbench": {"GET"},
        "/workbench/engagements/new": {"GET"},
        "/workbench/summary": {"GET"},
        "/workbench/api/v1/engagements": {"POST"},
        "/workbench/api/v1/engagements/current": {"GET"},
        "/workbench/api/v1/engagements/{engagement_id}": {"GET"},
        "/workbench/api/v1/engagements/{engagement_id}/activate": {"POST"},
        "/workbench/api/v1/engagements/{engagement_id}/current": {"PUT"},
        "/workbench/api/v1/evidence": {"POST"},
        "/workbench/evidence": {"POST"},
        "/workbench/evidence/{evidence_id}/media": {"GET"},
        "/workbench/evidence/{evidence_id}/review": {"POST"},
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
