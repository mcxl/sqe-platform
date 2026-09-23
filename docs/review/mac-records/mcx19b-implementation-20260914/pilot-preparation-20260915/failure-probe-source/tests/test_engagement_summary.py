"""Focused tests for the read-only Engagement Control Summary page."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.ace.app import app
from src.ace.workbench.storage import WorkbenchStore


def _credentials() -> tuple[str, str]:
    return ("auditor", "fictional-password")


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path / "sqe-local-data"))
    return TestClient(app)


def _fictional_draft(attempt_key: str = "attempt-summary-test-0001") -> dict[str, object]:
    return {
        "creation_attempt_key": attempt_key,
        "title": "Fictional Summary Test Engagement",
        "reference": "ENG-SUMMARY-TEST-001",
        "authority": "Fictional pilot authority",
        "purpose": "Test the Engagement Control Summary",
        "scope": "Fictional field capture activities",
        "exclusions": "Real-client information and evidence",
        "review_start_date": "2026-08-01",
        "review_end_date": "2026-08-31",
        "evidence_cut_off_date": "2026-08-15",
        "accountable_auditor": "Fictional Site Auditor",
        "data_classification": "FICTIONAL",
        "is_fictional": True,
    }


def _create_and_activate(client: TestClient, attempt_key: str) -> str:
    """Create a fictional draft, activate it, and return its engagement_id."""
    created = client.post(
        "/workbench/api/v1/engagements",
        auth=_credentials(),
        json=_fictional_draft(attempt_key),
    )
    assert created.status_code == 201
    engagement_id = created.json()["engagement"]["engagement_id"]

    activated = client.post(
        f"/workbench/api/v1/engagements/{engagement_id}/activate",
        auth=_credentials(),
        json={"confirmed": True},
    )
    assert activated.status_code == 200
    assert activated.json()["engagement"]["state"] == "READY_FOR_CAPTURE"
    return engagement_id


def test_summary_page_requires_auditor_authentication(client: TestClient) -> None:
    assert client.get("/workbench/engagement/summary").status_code == 401


def test_summary_page_is_read_only_html(client: TestClient) -> None:
    response = client.get("/workbench/engagement/summary", auth=_credentials())
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "text/html" in content_type


def test_seeded_engagement_is_shown(client: TestClient) -> None:
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    # Engagement details from the seed data
    assert "Fictional Mobile Field Capture Engagement" in text
    assert "ENG-FIC-0001" in text
    assert "READY_FOR_CAPTURE" in text
    assert "FICTIONAL" in text
    assert "Fictional Site Auditor" in text
    assert "2026-08-01" in text
    assert "2026-08-31" in text
    assert "Fictional pilot authority" in text
    assert "Fictional mobile field evidence capture" in text
    assert "Fictional field activities" in text
    assert "Real-client information and evidence" in text


def test_summary_shows_evidence_counts(client: TestClient) -> None:
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    # Evidence section exists
    assert "Evidence Captured" in text
    assert "Pending Review" in text
    assert "Evidence Reviewed" in text


def test_summary_shows_open_items_section(client: TestClient) -> None:
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert "Open Items" in text
    # Seeded placeholder evidence (EVD-FIC-0001) has is_capture=0,
    # so the CONTRA relationship won't surface as a conflict.
    # The section shows a no-open-items message.
    assert "No open conflicts or gaps" in text
    # Conflict capture-only note is always present
    assert "Relationship conflicts appear only for linked captured evidence" in text


def test_summary_shows_recent_activity(client: TestClient) -> None:
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert "Recent Activity" in text


def test_summary_shows_recommended_next_action(client: TestClient) -> None:
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert "Recommended Next Action" in text
    # Seeded engagement has evidence pending review
    assert "pending review" in text.lower()


def test_summary_has_no_write_actions(client: TestClient) -> None:
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    # No forms, no POST/PUT endpoints
    assert "<form" not in text
    assert 'method="post"' not in text.lower()
    assert "activate" not in text.lower()
    assert "delete" not in text.lower()
    assert "upload" not in text.lower()


def test_summary_renders_when_no_current_engagement(
    client: TestClient, tmp_path: Path
) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute("DELETE FROM current_engagement")

    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert "No Current Engagement" in text
    assert "Set up an Engagement" in text


def test_summary_after_creating_new_engagement(client: TestClient) -> None:
    engagement_id = _create_and_activate(client, "attempt-summary-new-0001")

    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert "Fictional Summary Test Engagement" in text
    assert "ENG-SUMMARY-TEST-001" in text
    assert "READY_FOR_CAPTURE" in text
    assert "Evidence Captured" in text
    assert "Recommended Next Action" in text


def test_summary_counts_are_accurate_with_captured_evidence(
    client: TestClient, tmp_path: Path
) -> None:
    engagement_id = _create_and_activate(client, "attempt-summary-counts-0001")
    store = WorkbenchStore(tmp_path / "sqe-local-data")

    # Verify initial state: no captures
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200

    # Directly insert evidence records to test counts
    with store.connect() as connection:
        connection.execute(
            """INSERT OR IGNORE INTO evidence (
                evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                is_capture, engagement_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "EVD-SUMMARY-0001",
                "OWN-FIC-0001",
                "test-capture-1.png",
                "image/png",
                None,
                "PENDING_REVIEW",
                "2026-08-15T10:00:00Z",
                1,
                engagement_id,
            ),
        )
        connection.execute(
            """INSERT OR IGNORE INTO evidence (
                evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                is_capture, engagement_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "EVD-SUMMARY-0002",
                "OWN-FIC-0001",
                "test-capture-2.png",
                "image/png",
                None,
                "REVIEWED",
                "2026-08-15T11:00:00Z",
                1,
                engagement_id,
            ),
        )

    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert "Evidence Captured" in text
    assert "Pending Review" in text
    assert "Evidence Reviewed" in text
    # Verify actual counts: 1 pending + 1 reviewed = 2 total captured
    assert "<td>Evidence Captured</td><td>2</td>" in text
    assert "<td>Pending Review</td><td>1</td>" in text
    assert "<td>Evidence Reviewed</td><td>1</td>" in text


def test_summary_recommendation_when_no_evidence(client: TestClient) -> None:
    engagement_id = _create_and_activate(client, "attempt-summary-no-evid-0001")

    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    # Should recommend capturing evidence
    assert "Capture evidence for the Engagement" in text


def test_summary_shows_pending_evidence_preview(
    client: TestClient, tmp_path: Path
) -> None:
    """Pending evidence items with captured data should appear in a preview list."""
    engagement_id = _create_and_activate(client, "attempt-summary-preview-0001")
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute(
            """INSERT OR IGNORE INTO evidence (
                evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                is_capture, engagement_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "EVD-PREVIEW-0001",
                "OWN-FIC-0001",
                "pending-capture.png",
                "image/png",
                None,
                "PENDING_REVIEW",
                "2026-08-15T10:00:00Z",
                1,
                engagement_id,
            ),
        )

    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert "Pending Evidence" in text
    assert "pending-capture.png" in text
    assert 'href="/workbench/evidence/EVD-PREVIEW-0001"' in text


def test_summary_shows_pending_preview_empty_state(client: TestClient) -> None:
    """When no evidence is pending review, the preview shows a clear message."""
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert "Pending Evidence" in text
    assert "No evidence pending review" in text


def test_summary_recommendation_has_navigation_link(
    client: TestClient, tmp_path: Path
) -> None:
    """When evidence is pending review, the recommendation includes a workbench link."""
    engagement_id = _create_and_activate(client, "attempt-summary-rec-link-0001")
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute(
            """INSERT OR IGNORE INTO evidence (
                evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                is_capture, engagement_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "EVD-RECLINK-0001",
                "OWN-FIC-0001",
                "pending-item.png",
                "image/png",
                None,
                "PENDING_REVIEW",
                "2026-08-15T10:00:00Z",
                1,
                engagement_id,
            ),
        )

    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    # The recommendation section should contain the workbench link
    assert "Recommended Next Action" in text
    assert "Open the Field Capture Workbench to review" in text
    assert 'href="/workbench"' in text


def test_summary_open_items_shows_conflict_capture_note(client: TestClient) -> None:
    """The Open Items section always explains the capture-only filtering."""
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert "Relationship conflicts appear only for linked captured evidence" in text
    assert 'href="/workbench/relationship-reviews"' in text


def test_summary_back_navigation_exists(client: TestClient) -> None:
    page = client.get("/workbench/engagement/summary", auth=_credentials())
    assert page.status_code == 200
    text = page.text

    assert 'href="/workbench"' in text
    assert "Back To Field Capture Workbench" in text
