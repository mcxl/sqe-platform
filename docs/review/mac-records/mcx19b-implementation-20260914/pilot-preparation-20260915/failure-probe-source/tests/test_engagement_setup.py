"""Integration tests for the controlled fictional Engagement setup path."""

import base64
import queue
import sqlite3
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.ace.app import app
from src.ace.workbench.engagement import (
    EngagementDraft,
    EngagementG0Error,
    EngagementService,
    EngagementValidationError,
)
from src.ace.workbench.storage import EngagementStoreRecord, WorkbenchStore


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


def fictional_draft(attempt_key: str = "attempt-engagement-0001") -> dict[str, object]:
    return {
        "creation_attempt_key": attempt_key,
        "title": "Fictional Engagement Setup Test",
        "reference": "ENG-SETUP-TEST-001",
        "authority": "Fictional pilot authority",
        "purpose": "Test the controlled Engagement setup path",
        "scope": "Fictional field capture activities",
        "exclusions": "Real-client information and evidence",
        "review_start_date": "2026-08-01",
        "review_end_date": "2026-08-31",
        "evidence_cut_off_date": "2026-08-15",
        "accountable_auditor": "Fictional Site Auditor",
        "data_classification": "FICTIONAL",
        "is_fictional": True,
    }


def test_engagement_setup_requires_auditor_authentication(client: TestClient) -> None:
    assert client.get("/workbench/engagements/new").status_code == 401
    assert client.post("/workbench/api/v1/engagements", json=fictional_draft()).status_code == 401


def test_page_collects_controlled_engagement_fields(client: TestClient) -> None:
    response = client.get("/workbench/engagements/new", auth=credentials())

    assert response.status_code == 200
    for field in (
        "title",
        "reference",
        "authority",
        "purpose",
        "scope",
        "exclusions",
        "review_start_date",
        "review_end_date",
        "evidence_cut_off_date",
        "accountable_auditor",
        "data_classification",
        "is_fictional",
    ):
        assert f'name="{field}"' in response.text
    assert "G0 permits fictional Engagements only" in response.text


def test_fictional_draft_retry_activation_and_current_state_are_controlled(
    client: TestClient, tmp_path: Path
) -> None:
    payload = fictional_draft()
    created = client.post("/workbench/api/v1/engagements", auth=credentials(), json=payload)

    assert created.status_code == 201
    body = created.json()
    assert body["api_version"] == "v1"
    draft = body["engagement"]
    assert draft["state"] == "DRAFT"
    assert draft["current"] is False

    retried = client.post("/workbench/api/v1/engagements", auth=credentials(), json=payload)
    assert retried.status_code == 201
    assert retried.json()["engagement"]["engagement_id"] == draft["engagement_id"]

    rejected = client.post(
        f"/workbench/api/v1/engagements/{draft['engagement_id']}/activate",
        auth=credentials(),
        json={"confirmed": False},
    )
    assert rejected.status_code == 422
    assert client.get(
        "/workbench/api/v1/engagements/current", auth=credentials()
    ).json()["engagement"]["engagement_id"] == "ENG-FIC-0001"

    activated = client.post(
        f"/workbench/api/v1/engagements/{draft['engagement_id']}/activate",
        auth=credentials(),
        json={"confirmed": True},
    )
    assert activated.status_code == 200
    ready = activated.json()["engagement"]
    assert ready["state"] == "READY_FOR_CAPTURE"
    assert ready["current"] is True

    current = client.get("/workbench/api/v1/engagements/current", auth=credentials())
    summary = client.get("/workbench/summary", auth=credentials())
    assert current.json()["engagement"] == ready
    assert summary.json()["current_engagement"] == ready
    assert summary.json()["engagement"] == ready["title"]
    page = client.get("/workbench", auth=credentials())
    assert ready["title"] in page.text
    assert ready["reference"] in page.text
    assert ready["state"] in page.text

    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        events = connection.execute(
            "SELECT event_type FROM engagement_audit_events WHERE engagement_id = ? ORDER BY event_type",
            (draft["engagement_id"],),
        ).fetchall()
    assert [event["event_type"] for event in events] == [
        "ENGAGEMENT_ACTIVATED",
        "ENGAGEMENT_CREATED",
    ]

    activation_retry = client.post(
        f"/workbench/api/v1/engagements/{draft['engagement_id']}/activate",
        auth=credentials(),
        json={"confirmed": True},
    )
    assert activation_retry.status_code == 200
    with store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM engagement_audit_events WHERE engagement_id = ?",
            (draft["engagement_id"],),
        ).fetchone()[0] == 2


def test_incomplete_draft_can_be_completed_with_the_same_attempt_key(
    client: TestClient, tmp_path: Path
) -> None:
    incomplete = client.post(
        "/workbench/api/v1/engagements",
        auth=credentials(),
        json={"creation_attempt_key": "attempt-incomplete-0001", "reference": "ENG-INCOMPLETE-001"},
    )
    assert incomplete.status_code == 201
    engagement_id = incomplete.json()["engagement"]["engagement_id"]
    assert client.post(
        f"/workbench/api/v1/engagements/{engagement_id}/activate",
        auth=credentials(),
        json={"confirmed": True},
    ).status_code == 422
    assert client.get(
        f"/workbench/api/v1/engagements/{engagement_id}", auth=credentials()
    ).json()["engagement"]["state"] == "DRAFT"

    completed = fictional_draft("attempt-incomplete-0001")
    completed["reference"] = "ENG-INCOMPLETE-001"
    updated = client.post("/workbench/api/v1/engagements", auth=credentials(), json=completed)
    assert updated.status_code == 201
    assert updated.json()["engagement"]["engagement_id"] == engagement_id
    assert updated.json()["engagement"]["scope"] == completed["scope"]
    assert client.post(
        f"/workbench/api/v1/engagements/{engagement_id}/activate",
        auth=credentials(),
        json={"confirmed": True},
    ).status_code == 200
    with WorkbenchStore(tmp_path / "sqe-local-data").connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM engagement_audit_events WHERE engagement_id = ? AND event_type = ?",
            (engagement_id, "ENGAGEMENT_CREATED"),
        ).fetchone()[0] == 1


def test_duplicate_reference_draft_update_rolls_back(client: TestClient) -> None:
    first = fictional_draft("attempt-duplicate-update-001")
    first["reference"] = "ENG-DUPLICATE-UPDATE-001"
    first["title"] = "Earlier fictional draft"
    first_created = client.post("/workbench/api/v1/engagements", auth=credentials(), json=first)
    assert first_created.status_code == 201
    first_id = first_created.json()["engagement"]["engagement_id"]

    second = fictional_draft("attempt-duplicate-update-002")
    second["reference"] = "ENG-DUPLICATE-UPDATE-002"
    assert client.post("/workbench/api/v1/engagements", auth=credentials(), json=second).status_code == 201

    update = fictional_draft("attempt-duplicate-update-001")
    update["reference"] = "ENG-DUPLICATE-UPDATE-002"
    update["title"] = "Changed title must not persist"
    assert client.post("/workbench/api/v1/engagements", auth=credentials(), json=update).status_code == 409
    restored = client.get(f"/workbench/api/v1/engagements/{first_id}", auth=credentials())
    assert restored.json()["engagement"]["reference"] == first["reference"]
    assert restored.json()["engagement"]["title"] == first["title"]


@pytest.mark.parametrize("classification", ["PUBLIC", "AUDITCO_OWNED"])
def test_safe_non_client_classifications_activate_and_become_current(
    client: TestClient, classification: str
) -> None:
    payload = fictional_draft(f"attempt-{classification.lower()}-0001")
    payload["reference"] = f"ENG-{classification}-001"
    payload["data_classification"] = classification
    created = client.post("/workbench/api/v1/engagements", auth=credentials(), json=payload)
    engagement_id = created.json()["engagement"]["engagement_id"]

    activated = client.post(
        f"/workbench/api/v1/engagements/{engagement_id}/activate",
        auth=credentials(),
        json={"confirmed": True},
    )
    assert activated.status_code == 200
    assert activated.json()["engagement"]["state"] == "READY_FOR_CAPTURE"
    selected = client.put(
        f"/workbench/api/v1/engagements/{engagement_id}/current", auth=credentials()
    )
    assert selected.status_code == 200
    assert selected.json()["engagement"]["current"] is True


def test_capture_uses_a_public_fictional_current_engagement(client: TestClient) -> None:
    payload = fictional_draft("attempt-public-capture-0001")
    payload["reference"] = "ENG-PUBLIC-CAPTURE-001"
    payload["data_classification"] = "PUBLIC"
    created = client.post("/workbench/api/v1/engagements", auth=credentials(), json=payload)
    engagement_id = created.json()["engagement"]["engagement_id"]
    assert client.post(
        f"/workbench/api/v1/engagements/{engagement_id}/activate",
        auth=credentials(),
        json={"confirmed": True},
    ).status_code == 200

    response = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "fictional-public-image.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        },
    )
    assert response.status_code == 201


def test_g0_rejects_real_client_setup_without_persisting_or_returning_values(
    client: TestClient, tmp_path: Path
) -> None:
    payload = fictional_draft("attempt-real-client-0001")
    payload.update(
        {
            "title": "CLIENT SECRET TITLE",
            "reference": "CLIENT-SECRET-REF",
            "data_classification": "REAL_CLIENT",
            "is_fictional": False,
        }
    )

    response = client.post("/workbench/api/v1/engagements", auth=credentials(), json=payload)
    assert response.status_code == 403
    assert "CLIENT SECRET" not in response.text

    with WorkbenchStore(tmp_path / "sqe-local-data").connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM engagement_setups WHERE reference = ?", ("CLIENT-SECRET-REF",)
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM engagement_audit_events WHERE engagement_id != 'ENG-FIC-0001'"
        ).fetchone()[0] == 0


def test_safe_retry_rejects_an_unsafe_ready_record_with_the_same_attempt_key(
    client: TestClient, tmp_path: Path
) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute(
            """
            INSERT INTO engagement_setups VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ENG-ABCDEF654321",
                "unsafe-ready-retry-0001",
                "CLIENT RETRY SECRET TITLE",
                "CLIENT-RETRY-SECRET-REF",
                "Authority",
                "Purpose",
                "Scope",
                "Exclusions",
                "2026-08-01",
                "2026-08-31",
                "2026-08-15",
                "Auditor",
                "REAL_CLIENT",
                0,
                "READY_FOR_CAPTURE",
                "2026-08-01T00:00:00Z",
                "2026-08-01T00:00:00Z",
            ),
        )
        connection.commit()

    response = client.post(
        "/workbench/api/v1/engagements",
        auth=credentials(),
        json=fictional_draft("unsafe-ready-retry-0001"),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "G0 blocks this Engagement"}
    assert "CLIENT RETRY SECRET" not in response.text
    assert "CLIENT-RETRY-SECRET" not in response.text


def test_g0_blocks_unsafe_direct_database_record_before_read_or_activation(
    client: TestClient, tmp_path: Path
) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute(
            """
            INSERT INTO engagement_setups VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ENG-ABCDEF123456",
                "direct-old-path-0001",
                "CLIENT DIRECT SECRET TITLE",
                "CLIENT-DIRECT-SECRET-REF",
                "Authority",
                "Purpose",
                "Scope",
                "Exclusions",
                "2026-08-01",
                "2026-08-31",
                "2026-08-15",
                "Auditor",
                "REAL_CLIENT",
                0,
                "READY_FOR_CAPTURE",
                "2026-08-01T00:00:00Z",
                "2026-08-01T00:00:00Z",
            ),
        )
        connection.execute(
            """
            INSERT INTO current_engagement (current_slot, engagement_id) VALUES (1, ?)
            ON CONFLICT(current_slot) DO UPDATE SET engagement_id = excluded.engagement_id
            """,
            ("ENG-ABCDEF123456",),
        )
        connection.commit()

    read_response = client.get(
        "/workbench/api/v1/engagements/ENG-ABCDEF123456", auth=credentials()
    )
    assert read_response.status_code == 403
    assert "CLIENT DIRECT SECRET" not in read_response.text
    assert "CLIENT-DIRECT-SECRET" not in read_response.text
    assert client.put(
        "/workbench/api/v1/engagements/ENG-ABCDEF123456/current", auth=credentials()
    ).status_code == 403

    for path in ("/workbench", "/workbench/summary", "/workbench/api/v1/engagements/current"):
        current_response = client.get(path, auth=credentials())
        assert current_response.status_code == 403
        assert current_response.json() == {"detail": "G0 blocks this Engagement"}
        assert "CLIENT DIRECT SECRET" not in current_response.text
        assert "CLIENT-DIRECT-SECRET" not in current_response.text

    response = client.post(
        "/workbench/api/v1/engagements/ENG-ABCDEF123456/activate",
        auth=credentials(),
        json={"confirmed": True},
    )
    assert response.status_code == 403
    rejected_capture = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "fictional-rejected-image.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        },
    )
    assert rejected_capture.status_code == 403
    assert rejected_capture.json() == {"detail": "G0 blocks this Engagement"}
    with store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM engagement_audit_events WHERE engagement_id = 'ENG-ABCDEF123456'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM evidence WHERE is_capture = 1"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM audit_events WHERE event_type = 'CAPTURED'"
        ).fetchone()[0] == 0
    assert list((tmp_path / "sqe-local-data" / "media").glob("*")) == []


def test_g0_blocks_an_unclassified_ready_record_before_direct_read_or_activation(
    client: TestClient, tmp_path: Path
) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute(
            """
            INSERT INTO engagement_setups VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ENG-ABCDEF345678",
                "direct-unclassified-ready-0001",
                "UNCLASSIFIED SECRET TITLE",
                "UNCLASSIFIED-SECRET-REF",
                "Authority",
                "Purpose",
                "Scope",
                "Exclusions",
                "2026-08-01",
                "2026-08-31",
                "2026-08-15",
                "Auditor",
                None,
                None,
                "READY_FOR_CAPTURE",
                "2026-08-01T00:00:00Z",
                "2026-08-01T00:00:00Z",
            ),
        )
        connection.commit()

    response = client.get(
        "/workbench/api/v1/engagements/ENG-ABCDEF345678", auth=credentials()
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "G0 blocks this Engagement"}
    assert "UNCLASSIFIED SECRET" not in response.text
    assert "UNCLASSIFIED-SECRET" not in response.text

    activation = client.post(
        "/workbench/api/v1/engagements/ENG-ABCDEF345678/activate",
        auth=credentials(),
        json={"confirmed": True},
    )

    assert activation.status_code == 403
    assert activation.json() == {"detail": "G0 blocks this Engagement"}
    assert "UNCLASSIFIED SECRET" not in activation.text
    assert "UNCLASSIFIED-SECRET" not in activation.text
    with store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM engagement_audit_events WHERE engagement_id = 'ENG-ABCDEF345678'"
        ).fetchone()[0] == 0
        current = connection.execute(
            "SELECT engagement_id FROM current_engagement WHERE current_slot = 1"
        ).fetchone()["engagement_id"]
    assert current == "ENG-FIC-0001"


def test_select_current_validates_the_locked_record_and_preserves_the_current_selection(
    tmp_path: Path,
) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    service = EngagementService(store)
    draft = EngagementDraft(**fictional_draft("attempt-locked-selection-0001"))
    engagement_id = service.create_draft(draft, "auditor").engagement_id
    service.activate(engagement_id, True, "auditor")
    with store.connect() as connection:
        connection.execute(
            "UPDATE current_engagement SET engagement_id = ? WHERE current_slot = 1",
            ("ENG-FIC-0001",),
        )
        connection.commit()

    unsafe_change_has_lock = threading.Event()
    allow_unsafe_change = threading.Event()
    validation_started = threading.Event()
    change_result: queue.Queue[BaseException | None] = queue.Queue()
    selection_result: queue.Queue[BaseException | None] = queue.Queue()
    validate = service._validate_current_capture

    def change_to_unsafe_record() -> None:
        try:
            with store.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    UPDATE engagement_setups
                    SET data_classification = ?, is_fictional = ?
                    WHERE engagement_id = ?
                    """,
                    ("REAL_CLIENT", 0, engagement_id),
                )
                unsafe_change_has_lock.set()
                assert allow_unsafe_change.wait(timeout=3)
                connection.commit()
        except BaseException as error:
            change_result.put(error)
        else:
            change_result.put(None)

    def record_validation(record: EngagementStoreRecord) -> None:
        validation_started.set()
        validate(record)

    service._validate_current_capture = record_validation  # type: ignore[method-assign]

    def select_current() -> None:
        try:
            service.select_current(engagement_id)
        except BaseException as error:
            selection_result.put(error)
        else:
            selection_result.put(None)

    change_thread = threading.Thread(target=change_to_unsafe_record)
    change_thread.start()
    assert unsafe_change_has_lock.wait(timeout=3)
    selection_thread = threading.Thread(target=select_current)
    selection_thread.start()
    assert not validation_started.wait(timeout=0.2)
    allow_unsafe_change.set()

    change_thread.join(timeout=3)
    assert not change_thread.is_alive()
    assert change_result.get_nowait() is None
    selection_thread.join(timeout=3)
    assert not selection_thread.is_alive()
    assert validation_started.is_set()
    assert isinstance(selection_result.get_nowait(), EngagementG0Error)
    with store.connect() as connection:
        current = connection.execute(
            "SELECT engagement_id FROM current_engagement WHERE current_slot = 1"
        ).fetchone()["engagement_id"]
    assert current == "ENG-FIC-0001"


def test_g0_blocks_an_unsafe_draft_directly_placed_in_current(
    client: TestClient, tmp_path: Path
) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute(
            """
            INSERT INTO engagement_setups VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ENG-ABCDEF789012",
                "direct-current-draft-0001",
                "CLIENT DRAFT SECRET TITLE",
                "CLIENT-DRAFT-SECRET-REF",
                "Authority",
                "Purpose",
                "Scope",
                "Exclusions",
                "2026-08-01",
                "2026-08-31",
                "2026-08-15",
                "Auditor",
                "REAL_CLIENT",
                0,
                "DRAFT",
                "2026-08-01T00:00:00Z",
                None,
            ),
        )
        connection.execute(
            """
            INSERT INTO current_engagement (current_slot, engagement_id) VALUES (1, ?)
            ON CONFLICT(current_slot) DO UPDATE SET engagement_id = excluded.engagement_id
            """,
            ("ENG-ABCDEF789012",),
        )
        connection.commit()

    for path in ("/workbench", "/workbench/summary", "/workbench/api/v1/engagements/current"):
        response = client.get(path, auth=credentials())
        assert response.status_code == 403
        assert response.json() == {"detail": "G0 blocks this Engagement"}
        assert "CLIENT DRAFT SECRET" not in response.text
        assert "CLIENT-DRAFT-SECRET" not in response.text


def test_activation_rolls_back_when_audit_event_persistence_fails(
    client: TestClient, tmp_path: Path
) -> None:
    created = client.post(
        "/workbench/api/v1/engagements", auth=credentials(), json=fictional_draft()
    )
    engagement_id = created.json()["engagement"]["engagement_id"]
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        prior_current = connection.execute(
            "SELECT engagement_id FROM current_engagement WHERE current_slot = 1"
        ).fetchone()["engagement_id"]
        connection.execute(
            """
            CREATE TRIGGER test_fail_activation_event
            BEFORE INSERT ON engagement_audit_events
            WHEN NEW.event_type = 'ENGAGEMENT_ACTIVATED'
            BEGIN
                SELECT RAISE(ABORT, 'test activation event failure');
            END;
            """
        )
        connection.commit()

    with pytest.raises(sqlite3.IntegrityError, match="test activation event failure"):
        EngagementService(store).activate(engagement_id, True, "auditor")

    with store.connect() as connection:
        engagement = connection.execute(
            "SELECT state, activated_at FROM engagement_setups WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchone()
        activation_events = connection.execute(
            """
            SELECT COUNT(*) FROM engagement_audit_events
            WHERE engagement_id = ? AND event_type = 'ENGAGEMENT_ACTIVATED'
            """,
            (engagement_id,),
        ).fetchone()[0]
        current = connection.execute(
            "SELECT engagement_id FROM current_engagement WHERE current_slot = 1"
        ).fetchone()["engagement_id"]
    assert engagement["state"] == "DRAFT"
    assert engagement["activated_at"] is None
    assert activation_events == 0
    assert current == prior_current


def test_activation_validates_the_concurrent_draft_save_after_acquiring_the_write_lock(
    tmp_path: Path,
) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    service = EngagementService(store)
    draft = EngagementDraft(**fictional_draft("attempt-locked-activation-0001"))
    engagement_id = service.create_draft(draft, "auditor").engagement_id
    saved_draft_has_lock = threading.Event()
    allow_draft_save = threading.Event()
    validation_started = threading.Event()
    activation_started = threading.Event()
    save_result: queue.Queue[BaseException | None] = queue.Queue()
    activation_result: queue.Queue[BaseException | None] = queue.Queue()
    validate = service._validate_activation
    check_reference = store._check_reference_is_available

    def pause_draft_save(
        connection: sqlite3.Connection, reference: object, current_engagement_id: str | None
    ) -> None:
        saved_draft_has_lock.set()
        assert allow_draft_save.wait(timeout=3)
        check_reference(connection, reference, current_engagement_id)

    def record_validation(record: EngagementStoreRecord) -> None:
        validation_started.set()
        validate(record)

    store._check_reference_is_available = pause_draft_save  # type: ignore[method-assign]
    service._validate_activation = record_validation  # type: ignore[method-assign]

    def save_incomplete_draft() -> None:
        try:
            service.create_draft(
                EngagementDraft(
                    creation_attempt_key=draft.creation_attempt_key,
                    reference=draft.reference,
                ),
                "auditor",
            )
        except BaseException as error:
            save_result.put(error)
        else:
            save_result.put(None)

    def activate() -> None:
        activation_started.set()
        try:
            service.activate(engagement_id, True, "auditor")
        except BaseException as error:
            activation_result.put(error)
        else:
            activation_result.put(None)

    save_thread = threading.Thread(target=save_incomplete_draft)
    save_thread.start()
    assert saved_draft_has_lock.wait(timeout=3)
    thread = threading.Thread(target=activate)
    thread.start()
    assert activation_started.wait(timeout=1)
    assert not validation_started.wait(timeout=0.2)
    allow_draft_save.set()

    save_thread.join(timeout=3)
    assert not save_thread.is_alive()
    assert save_result.get_nowait() is None
    thread.join(timeout=3)
    assert not thread.is_alive()
    assert validation_started.is_set()
    assert isinstance(activation_result.get_nowait(), EngagementValidationError)
    with store.connect() as connection:
        row = connection.execute(
            "SELECT state, activated_at FROM engagement_setups WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchone()
        activation_events = connection.execute(
            """
            SELECT COUNT(*) FROM engagement_audit_events
            WHERE engagement_id = ? AND event_type = 'ENGAGEMENT_ACTIVATED'
            """,
            (engagement_id,),
        ).fetchone()[0]
    assert row["state"] == "DRAFT"
    assert row["activated_at"] is None
    assert activation_events == 0


def test_capture_fails_safely_without_a_ready_current_engagement(
    client: TestClient, tmp_path: Path
) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute("DELETE FROM current_engagement WHERE current_slot = 1")
        connection.commit()

    response = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "fictional-image.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        },
    )
    assert response.status_code == 409
    with store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM evidence WHERE is_capture = 1"
        ).fetchone()[0] == 0


def test_capture_removes_media_and_rolls_back_when_evidence_persistence_fails(
    tmp_path: Path,
) -> None:
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    service = EngagementService(store)
    engagement_id = service.create_draft(
        EngagementDraft(**fictional_draft("attempt-capture-cleanup-0001")), "auditor"
    ).engagement_id
    service.activate(engagement_id, True, "auditor")
    with store.connect() as connection:
        connection.execute(
            """
            CREATE TRIGGER test_fail_capture_evidence
            BEFORE INSERT ON evidence
            WHEN NEW.is_capture = 1
            BEGIN
                SELECT RAISE(ABORT, 'test capture evidence failure');
            END;
            """
        )
        connection.commit()

    with pytest.raises(sqlite3.IntegrityError, match="test capture evidence failure"):
        service.capture("fictional-image.png", "image/png", PNG_BYTES, "auditor")

    assert list(store.media_dir.glob("*")) == []
    with store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM evidence WHERE is_capture = 1"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM audit_events WHERE event_type = 'CAPTURED'"
        ).fetchone()[0] == 0


def test_successful_draft_save_clears_confirmation_before_showing_the_saved_summary(
    client: TestClient,
) -> None:
    page = client.get("/workbench/engagements/new", auth=credentials()).text

    reset = "if (data.engagement.state === 'DRAFT') { confirm.checked = false; }"
    assert reset in page
    reset_pos = page.index(reset)
    assert reset_pos < page.index("showRecord(data.engagement);", reset_pos)
