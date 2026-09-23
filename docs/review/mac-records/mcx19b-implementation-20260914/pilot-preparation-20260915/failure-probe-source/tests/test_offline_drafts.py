"""Focused tests for ACE protected offline draft support."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.ace.app import app


def fictional_draft(attempt_key: str = "attempt-offline-0001") -> dict[str, object]:
    return {
        "creation_attempt_key": attempt_key,
        "title": "Fictional Offline Draft Test",
        "reference": "ENG-OFFLINE-001",
        "authority": "Fictional pilot authority",
        "purpose": "Test offline draft sync",
        "scope": "Fictional field capture activities",
        "exclusions": "Real-client information and evidence",
        "review_start_date": "2026-08-01",
        "review_end_date": "2026-08-31",
        "evidence_cut_off_date": "2026-08-15",
        "accountable_auditor": "Fictional Site Auditor",
        "data_classification": "FICTIONAL",
        "is_fictional": True,
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path / "sqe-local-data"))
    return TestClient(app)


def credentials() -> tuple[str, str]:
    return ("auditor", "fictional-password")


class TestSyncEndpoint:
    """Sync endpoint accepts offline drafts with idempotent key."""

    def test_sync_creates_new_draft_and_returns_synced_flag(self, client: TestClient) -> None:
        response = client.post(
            "/workbench/api/v1/engagements/sync",
            json=fictional_draft("attempt-sync-0001"),
            auth=credentials(),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["synced"] is True
        assert data["engagement"]["state"] == "DRAFT"
        assert data["engagement"]["title"] == "Fictional Offline Draft Test"

    def test_sync_is_idempotent_on_same_creation_attempt_key(self, client: TestClient) -> None:
        payload = fictional_draft("attempt-sync-0002")
        first = client.post(
            "/workbench/api/v1/engagements/sync", json=payload, auth=credentials()
        )
        assert first.status_code == 201
        first_id = first.json()["engagement"]["engagement_id"]

        second = client.post(
            "/workbench/api/v1/engagements/sync", json=payload, auth=credentials()
        )
        assert second.status_code == 201
        assert second.json()["synced"] is True
        assert second.json()["engagement"]["engagement_id"] == first_id

    def test_sync_rejects_real_client_data(self, client: TestClient) -> None:
        payload = fictional_draft("attempt-g0-sync")
        payload["data_classification"] = "REAL_CLIENT"
        payload["is_fictional"] = False
        response = client.post(
            "/workbench/api/v1/engagements/sync",
            json=payload,
            auth=credentials(),
        )
        assert response.status_code == 403

    def test_sync_requires_authentication(self, client: TestClient) -> None:
        response = client.post(
            "/workbench/api/v1/engagements/sync",
            json=fictional_draft("attempt-noauth"),
        )
        assert response.status_code == 401

    def test_sync_rejects_duplicate_reference_with_different_attempt_key(
        self, client: TestClient
    ) -> None:
        first = client.post(
            "/workbench/api/v1/engagements/sync",
            json=fictional_draft("attempt-ref-dup-1"),
            auth=credentials(),
        )
        assert first.status_code == 201
        second = fictional_draft("attempt-ref-dup-2")
        second["reference"] = "ENG-OFFLINE-001"
        response = client.post(
            "/workbench/api/v1/engagements/sync",
            json=second,
            auth=credentials(),
        )
        assert response.status_code == 409


class TestOfflineDraftPage:
    """Engagement setup page includes offline draft support."""

    def test_page_includes_offline_badge(self, client: TestClient) -> None:
        response = client.get("/workbench/engagements/new", auth=credentials())
        assert response.status_code == 200
        assert 'OFFLINE_DRAFT' in response.text
        assert 'offline-badge' in response.text

    def test_page_includes_indexeddb_storage(self, client: TestClient) -> None:
        response = client.get("/workbench/engagements/new", auth=credentials())
        assert response.status_code == 200
        assert 'IndexedDB' in response.text
        assert 'ace-offline-drafts' in response.text
        assert 'engagement_drafts' in response.text

    def test_page_includes_g0_client_validation(self, client: TestClient) -> None:
        response = client.get("/workbench/engagements/new", auth=credentials())
        assert response.status_code == 200
        assert 'REAL_CLIENT' in response.text
        assert 'G0 blocks' in response.text

    def test_page_includes_sync_on_reconnect(self, client: TestClient) -> None:
        response = client.get("/workbench/engagements/new", auth=credentials())
        assert response.status_code == 200
        assert 'online' in response.text
        assert 'Connection restored' in response.text
        assert 'Connection lost' in response.text

    def test_page_includes_duplicate_prevention_key(self, client: TestClient) -> None:
        response = client.get("/workbench/engagements/new", auth=credentials())
        assert response.status_code == 200
        assert 'creation_attempt_key' in response.text
