"""Tests for authenticated, idempotent Engagement evidence capture."""

import base64
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.ace.app import app
from src.ace.workbench.engagement import EngagementDraft, EngagementService
from src.ace.workbench.storage import CaptureAttemptConflictError, WorkbenchStore


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQABpfZFQAAAAABJRU5ErkJggg=="
)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path / "sqe-local-data"))
    return TestClient(app)


def credentials() -> tuple[str, str]:
    return ("auditor", "fictional-password")


def payload(attempt_key: str = "capture-attempt-0001") -> dict[str, str]:
    return {
        "filename": "fictional-site-photo.png",
        "media_type": "image/png",
        "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        "capture_attempt_key": attempt_key,
    }


def test_v1_capture_returns_one_linked_pending_item_and_retries_safely(
    client: TestClient, tmp_path: Path
) -> None:
    first = client.post("/workbench/api/v1/evidence", auth=credentials(), json=payload())
    second = client.post("/workbench/api/v1/evidence", auth=credentials(), json=payload())

    assert first.status_code == second.status_code == 201
    assert first.json()["api_version"] == second.json()["api_version"] == "v1"
    evidence = first.json()["evidence"]
    assert second.json()["evidence"] == evidence
    assert evidence["engagement_id"] == "ENG-FIC-0001"
    assert evidence["status"] == "PENDING_REVIEW"
    assert evidence["media_type"] == "image/png"
    assert (tmp_path / "sqe-local-data" / evidence["media_path"]).read_bytes() == PNG_BYTES

    with WorkbenchStore(tmp_path / "sqe-local-data").connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM evidence WHERE is_capture = 1").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM audit_events WHERE event_type = 'CAPTURED'").fetchone()[0] == 1


def test_v1_capture_requires_authentication_and_creates_nothing(
    client: TestClient, tmp_path: Path
) -> None:
    response = client.post("/workbench/api/v1/evidence", json=payload())

    assert response.status_code == 401
    data_dir = tmp_path / "sqe-local-data"
    assert not (data_dir / "workbench.sqlite3").exists()
    assert not (data_dir / "media").exists()


def test_legacy_capture_uses_an_explicit_attempt_key_for_safe_retry(
    client: TestClient, tmp_path: Path
) -> None:
    legacy_payload = payload("legacy-capture-attempt-0001")
    first = client.post("/workbench/evidence", auth=credentials(), json=legacy_payload)
    second = client.post("/workbench/evidence", auth=credentials(), json=legacy_payload)

    assert first.status_code == second.status_code == 201
    assert second.json()["evidence_id"] == first.json()["evidence_id"]
    with WorkbenchStore(tmp_path / "sqe-local-data").connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM evidence WHERE is_capture = 1").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM audit_events WHERE event_type = 'CAPTURED'").fetchone()[0] == 1


@pytest.mark.parametrize(
    "changed_payload",
    [
        {"filename": "fictional-site-photo-2.png"},
        {
            "media_type": "image/gif",
            "data_base64": "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==",
        },
    ],
)
def test_v1_capture_rejects_changed_request_for_existing_attempt_key(
    client: TestClient, tmp_path: Path, changed_payload: dict[str, str]
) -> None:
    assert client.post("/workbench/api/v1/evidence", auth=credentials(), json=payload()).status_code == 201
    changed = payload()
    changed.update(changed_payload)

    response = client.post("/workbench/api/v1/evidence", auth=credentials(), json=changed)

    assert response.status_code == 409
    with WorkbenchStore(tmp_path / "sqe-local-data").connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM evidence WHERE is_capture = 1").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM audit_events WHERE event_type = 'CAPTURED'").fetchone()[0] == 1


def test_v1_capture_key_is_required_and_controlled(client: TestClient) -> None:
    missing = payload()
    del missing["capture_attempt_key"]
    assert client.post("/workbench/api/v1/evidence", auth=credentials(), json=missing).status_code == 422

    invalid = payload("invalid key")
    assert client.post("/workbench/api/v1/evidence", auth=credentials(), json=invalid).status_code == 422


def test_capture_rolls_back_database_and_media_when_audit_event_fails(tmp_path: Path) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute(
            """
            CREATE TRIGGER test_fail_capture_event
            BEFORE INSERT ON audit_events
            WHEN NEW.event_type = 'CAPTURED'
            BEGIN
                SELECT RAISE(ABORT, 'test capture event failure');
            END;
            """
        )
        connection.commit()

    with pytest.raises(sqlite3.IntegrityError, match="test capture event failure"):
        EngagementService(store).capture(
            "fictional-site-photo.png", "image/png", PNG_BYTES, "auditor", "capture-audit-failure-0001"
        )

    assert list(store.media_dir.glob("*")) == []
    with store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM evidence WHERE is_capture = 1").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM audit_events WHERE event_type = 'CAPTURED'").fetchone()[0] == 0


def test_existing_database_gains_nullable_capture_columns_and_unique_key_index(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "sqe-local-data"
    data_dir.mkdir()
    connection = sqlite3.connect(data_dir / "workbench.sqlite3")
    connection.execute(
        """
        CREATE TABLE evidence (
            evidence_id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            media_type TEXT,
            media_path TEXT,
            status TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            is_capture INTEGER NOT NULL
        )
        """
    )
    connection.commit()
    connection.close()

    with WorkbenchStore(data_dir).connect() as migrated:
        columns = {row["name"] for row in migrated.execute("PRAGMA table_info(evidence)")}
        indexes = {row["name"] for row in migrated.execute("PRAGMA index_list(evidence)")}

    assert {"engagement_id", "capture_attempt_key", "request_sha256"} <= columns
    assert "evidence_capture_attempt_key_unique" in indexes


def test_summary_only_shows_the_current_engagement_captures(tmp_path: Path) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    service = EngagementService(store)
    service.capture("first.png", "image/png", PNG_BYTES, "auditor", "capture-current-one-0001")
    draft = EngagementDraft(
        creation_attempt_key="capture-summary-engagement-0001",
        title="Fictional Second Engagement",
        reference="ENG-CAPTURE-SUMMARY-001",
        authority="Fictional authority",
        purpose="Fictional purpose",
        scope="Fictional scope",
        exclusions="Real-client information",
        review_start_date="2026-08-01",
        review_end_date="2026-08-31",
        evidence_cut_off_date="2026-08-15",
        accountable_auditor="Fictional auditor",
        data_classification="FICTIONAL",
        is_fictional=True,
    )
    second = service.create_draft(draft, "auditor")
    service.activate(second.engagement_id, True, "auditor")

    summary = store.summary()

    assert summary["counts"]["captured"] == 0
    assert summary["recent_captures"] == []
    assert summary["pending_review"] == []


def test_capture_attempt_key_cannot_move_to_another_engagement(tmp_path: Path) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    service = EngagementService(store)
    attempt_key = "capture-other-engagement-0001"
    service.capture("first.png", "image/png", PNG_BYTES, "auditor", attempt_key)
    second = service.create_draft(
        EngagementDraft(
            creation_attempt_key="capture-key-engagement-0001",
            title="Fictional Second Engagement",
            reference="ENG-CAPTURE-KEY-001",
            authority="Fictional authority",
            purpose="Fictional purpose",
            scope="Fictional scope",
            exclusions="Real-client information",
            review_start_date="2026-08-01",
            review_end_date="2026-08-31",
            evidence_cut_off_date="2026-08-15",
            accountable_auditor="Fictional auditor",
            data_classification="FICTIONAL",
            is_fictional=True,
        ),
        "auditor",
    )
    service.activate(second.engagement_id, True, "auditor")

    with pytest.raises(CaptureAttemptConflictError):
        service.capture("first.png", "image/png", PNG_BYTES, "auditor", attempt_key)

    with store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM evidence WHERE is_capture = 1").fetchone()[0] == 1


def test_captured_audit_event_is_immutable(tmp_path: Path) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    EngagementService(store).capture(
        "immutable.png", "image/png", PNG_BYTES, "auditor", "capture-immutable-event-0001"
    )

    with store.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="Captured audit events are immutable"):
            connection.execute("UPDATE audit_events SET actor = 'other' WHERE event_type = 'CAPTURED'")
