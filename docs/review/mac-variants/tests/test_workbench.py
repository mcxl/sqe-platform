import base64
import html
import os
from io import BytesIO
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.ace.app import app
from src.ace.workbench import storage
from src.ace.workbench.storage import WorkbenchStore


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQABpfZFQAAAAABJRU5ErkJggg=="
)
CORRUPT_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR42mNk+M/wHwAF/gL+9je9JwAAAABJRU5ErkJggg=="
)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path / "sqe-local-data"))
    return TestClient(app)


def credentials() -> tuple[str, str]:
    return ("auditor", "fictional-password")


def test_default_data_dir_uses_platform_user_data_path_without_creating_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ACE_DATA_DIR", raising=False)
    if os.name == "nt":
        local_app_data = tmp_path / "local-app-data"
        monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
        expected = local_app_data / "AuditCo" / "ACE" / "sqe-local-data"
    else:
        xdg_data = tmp_path / "xdg-data"
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data))
        expected = xdg_data / "auditco-ace" / "sqe-local-data"

    data_dir = storage.resolve_data_dir()

    assert data_dir == expected.resolve()
    assert not data_dir.exists()


def test_configured_data_dir_inside_linked_worktree_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree_root = tmp_path / "linked-worktree"
    source_workspace = worktree_root / "sqe"
    source_workspace.mkdir(parents=True)
    (worktree_root / ".git").write_text("gitdir: ../shared/.git/worktrees/sqe\n")
    monkeypatch.setattr(storage, "REPOSITORY_ROOT", source_workspace)
    monkeypatch.setenv("ACE_DATA_DIR", str(worktree_root / "sqe-local-data"))

    with pytest.raises(RuntimeError, match="ACE_DATA_DIR must be outside the source workspace"):
        storage.resolve_data_dir()


def test_direct_store_path_inside_git_worktree_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree_root = tmp_path / "worktree"
    source_workspace = worktree_root / "sqe"
    source_workspace.mkdir(parents=True)
    (worktree_root / ".git").mkdir()
    monkeypatch.setattr(storage, "REPOSITORY_ROOT", source_workspace)

    with pytest.raises(RuntimeError, match="Direct WorkbenchStore path must be outside the source workspace"):
        WorkbenchStore(worktree_root / "evidence")


def test_direct_store_path_outside_git_worktree_is_permitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree_root = tmp_path / "worktree"
    source_workspace = worktree_root / "sqe"
    source_workspace.mkdir(parents=True)
    (worktree_root / ".git").mkdir()
    monkeypatch.setattr(storage, "REPOSITORY_ROOT", source_workspace)
    external_data = tmp_path / "external-data"

    store = WorkbenchStore(external_data)

    assert store.data_dir == external_data.resolve()
    assert not external_data.exists()


def test_source_control_root_does_not_climb_into_unrelated_home_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_dir = tmp_path / "home"
    source_workspace = home_dir / "projects" / "sqe"
    source_workspace.mkdir(parents=True)
    (home_dir / ".git").mkdir()
    monkeypatch.setattr(storage, "REPOSITORY_ROOT", source_workspace)
    monkeypatch.setattr(storage.Path, "home", staticmethod(lambda: home_dir))
    external_data = home_dir / "sqe-local-data"
    monkeypatch.setenv("ACE_DATA_DIR", str(external_data))

    assert storage._source_control_root() == source_workspace.resolve()
    assert storage.resolve_data_dir() == external_data.resolve()


def test_default_data_dir_inside_source_workspace_names_the_default_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_workspace = tmp_path / "worktree" / "sqe"
    source_workspace.mkdir(parents=True)
    (source_workspace.parent / ".git").mkdir()
    monkeypatch.setattr(storage, "REPOSITORY_ROOT", source_workspace)
    monkeypatch.delenv("ACE_DATA_DIR", raising=False)
    monkeypatch.setattr(storage, "default_data_dir", lambda: source_workspace / "sqe-local-data")

    with pytest.raises(RuntimeError, match="default data directory must be outside the source workspace"):
        storage.resolve_data_dir()


def test_workbench_rejects_requests_without_auditor_credentials(
    client: TestClient,
) -> None:
    response = client.get("/workbench")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"


def test_workbench_fails_closed_when_auditor_password_is_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ACE_AUDITOR_PASSWORD", raising=False)
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path / "sqe-local-data"))

    response = TestClient(app).get("/workbench", auth=("auditor", "any-value"))

    assert response.status_code == 503


def test_authenticated_workbench_shows_fictional_chain_and_live_counts(
    client: TestClient,
) -> None:
    response = client.get("/workbench/summary", auth=credentials())

    assert response.status_code == 200
    summary = response.json()
    assert summary["engagement"] == "Fictional Mobile Field Capture Engagement"
    assert summary["chain"] == [
        "Obligation",
        "Risk",
        "Control",
        "Owner",
        "Evidence",
        "MATE",
        "Conclusion",
    ]
    assert summary["counts"] == {
        "captured": 0,
        "pending_review": 0,
        "reviewed": 0,
        "open_conflicts": 0,
    }
    assert summary["recent_captures"] == []
    assert summary["pending_review"] == []


def test_capture_stores_original_outside_source_workspace_and_returns_pending_item(
    client: TestClient, tmp_path: Path
) -> None:
    response = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "fictional-site-photo.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        },
    )

    assert response.status_code == 201
    captured = response.json()
    assert captured["evidence_id"].startswith("EVD-")
    assert captured["status"] == "PENDING_REVIEW"
    assert captured["media_type"] == "image/png"
    assert not Path(captured["media_path"]).is_absolute()
    stored_file = tmp_path / "sqe-local-data" / captured["media_path"]
    assert stored_file.read_bytes() == PNG_BYTES
    assert Path.cwd() not in stored_file.parents

    summary = client.get("/workbench/summary", auth=credentials()).json()
    assert summary["counts"]["captured"] == 1
    assert summary["counts"]["pending_review"] == 1
    assert summary["recent_captures"][0]["evidence_id"] == captured["evidence_id"]


def test_summary_counts_open_conflict_linked_to_captured_evidence(
    client: TestClient, tmp_path: Path
) -> None:
    capture = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "fictional-conflict-photo.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        },
    ).json()
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute(
            "INSERT INTO relationships VALUES (?, ?, ?, ?, ?)",
            (
                "REL-TEST-0001",
                capture["evidence_id"],
                "MATE-FIC-0001",
                "CONTRA",
                "OPEN",
            ),
        )
        connection.commit()

    summary = client.get("/workbench/summary", auth=credentials()).json()

    assert summary["counts"]["open_conflicts"] == 1


def test_capture_rejects_non_image_payloads(client: TestClient) -> None:
    response = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "fictional-notes.txt",
            "media_type": "text/plain",
            "data_base64": base64.b64encode(b"fictional notes").decode("ascii"),
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("media_type", "content"),
    [
        ("image/jpeg", b"\xff\xd8\xff"),
        ("image/png", b"\x89PNG\r\n\x1a\n"),
        ("image/png", CORRUPT_PNG_BYTES),
        ("image/webp", b"RIFF\x00\x00\x00\x00WEBP"),
        ("image/gif", b"GIF89a"),
    ],
)
def test_capture_rejects_damaged_images_without_storing_media(
    client: TestClient, tmp_path: Path, media_type: str, content: bytes
) -> None:
    response = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "damaged-image",
            "media_type": media_type,
            "data_base64": base64.b64encode(content).decode("ascii"),
        },
    )

    assert response.status_code == 422
    assert not (tmp_path / "sqe-local-data" / "media").exists()


def test_capture_rejects_decompression_bomb_warning_without_storing_media(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    image_buffer = BytesIO()
    Image.new("RGB", (2, 1)).save(image_buffer, format="PNG")
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1)

    response = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "warning-image.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(image_buffer.getvalue()).decode("ascii"),
        },
    )

    assert response.status_code == 422
    summary = client.get("/workbench/summary", auth=credentials()).json()
    assert summary["counts"] == {
        "captured": 0,
        "pending_review": 0,
        "reviewed": 0,
        "open_conflicts": 0,
    }
    assert summary["recent_captures"] == []
    assert summary["pending_review"] == []
    with WorkbenchStore(tmp_path / "sqe-local-data").connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM evidence WHERE is_capture = 1"
        ).fetchone()[0] == 0
    assert list((tmp_path / "sqe-local-data" / "media").glob("*")) == []


def test_capture_rejects_mismatched_image_data_without_storing_media(
    client: TestClient, tmp_path: Path
) -> None:
    response = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "mismatched-image.jpg",
            "media_type": "image/jpeg",
            "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        },
    )

    assert response.status_code == 422
    assert not (tmp_path / "sqe-local-data" / "media").exists()


def test_capture_rejects_oversized_image_data_without_storing_media(
    client: TestClient, tmp_path: Path
) -> None:
    oversized_content = PNG_BYTES + b"\x00" * (10 * 1024 * 1024)

    response = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "oversized-image.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(oversized_content).decode("ascii"),
        },
    )

    assert response.status_code == 422
    assert not (tmp_path / "sqe-local-data" / "media").exists()


def test_media_retrieval_requires_authentication_and_returns_original(
    client: TestClient,
) -> None:
    capture = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "fictional-site-photo.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        },
    ).json()
    media_url = f"/workbench/evidence/{capture['evidence_id']}/media"

    assert client.get(media_url).status_code == 401

    response = client.get(media_url, auth=credentials())

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == PNG_BYTES


def test_review_marks_evidence_reviewed_and_records_auditor_and_notes(
    client: TestClient,
) -> None:
    capture = client.post(
        "/workbench/evidence",
        auth=credentials(),
        json={
            "filename": "fictional-site-photo.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        },
    ).json()

    response = client.post(
        f"/workbench/evidence/{capture['evidence_id']}/review",
        auth=credentials(),
        json={"notes": "Fictional image reviewed on the laptop."},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Save source context before review completion"

    context_response = client.put(
        f"/workbench/api/v1/evidence/{capture['evidence_id']}/review/context",
        auth=credentials(),
        json={
            "provider": "Fictional field team",
            "origin": "RAW",
            "source_date": "2026-08-12",
            "source_version": "1.0",
            "source_location": "Fictional local store",
            "description": "Fictional source context",
            "freshness": "CURRENT",
            "limitations": "Fictional limitation",
            "duplicate_evidence_id": None,
            "source_evidence_ids": [],
            "gap_status": "NOT_REQUESTED",
            "gap_explanation": None,
            "gap_materiality": None,
        },
    )

    assert context_response.status_code == 200

    response = client.post(
        f"/workbench/evidence/{capture['evidence_id']}/review",
        auth=credentials(),
        json={"notes": "Fictional image reviewed on the laptop."},
    )

    assert response.status_code == 200
    reviewed = response.json()
    assert reviewed["status"] == "REVIEWED"
    assert reviewed["reviewer"] == "auditor"
    assert reviewed["reviewed_at"].endswith("Z")
    assert reviewed["notes"] == "Fictional image reviewed on the laptop."

    summary = client.get("/workbench/summary", auth=credentials()).json()
    assert summary["counts"]["reviewed"] == 1
    assert all(
        item["evidence_id"] != capture["evidence_id"]
        for item in summary["pending_review"]
    )
    assert [item["evidence_id"] for item in summary["reviewed_unlinked"]] == [
        capture["evidence_id"]
    ]

    page = client.get("/workbench", auth=credentials())
    assert page.status_code == 200
    assert "Reviewed Unlinked" in page.text
    assert 'id="reviewed-unlinked"' in page.text
    assert "data.reviewed_unlinked.map(evidenceItem)" in page.text
    assert "encodeURIComponent(item.evidence_id)}/review" in page.text


def test_responsive_workbench_page_has_capture_and_review_controls(
    client: TestClient,
) -> None:
    response = client.get("/workbench", auth=credentials())

    assert response.status_code == 200
    assert '<meta name="viewport"' in response.text
    assert "Capture Evidence" in response.text
    assert 'capture="environment"' in response.text
    assert "Pending Review" in response.text
    assert "Fictional Mobile Field Capture Engagement" in response.text


def test_mobile_capture_page_has_safe_touch_and_upload_feedback_contracts(
    client: TestClient,
) -> None:
    response = client.get("/workbench", auth=credentials())

    assert response.status_code == 200
    page = response.text
    assert 'viewport-fit=cover' in page
    assert '<meta name="theme-color" content="#005a9c">' in page
    assert 'min-height: 100vh; min-height: 100dvh;' in page
    assert 'env(safe-area-inset-top)' in page
    assert 'env(safe-area-inset-right)' in page
    assert 'env(safe-area-inset-bottom)' in page
    assert 'env(safe-area-inset-left)' in page
    assert 'max(calc(1rem + 56px + .75rem), calc(env(safe-area-inset-bottom) + 56px + .75rem))' in page
    assert '.capture-area { position: fixed;' in page
    assert 'left: max(1rem, env(safe-area-inset-left));' in page
    assert 'right: max(1rem, env(safe-area-inset-right));' in page
    assert 'bottom: max(.75rem, env(safe-area-inset-bottom));' in page
    assert 'max-width: 980px; margin: 0 auto;' in page
    assert 'position: sticky' not in page
    assert 'overscroll-behavior-y: none' in page
    assert 'touch-action: manipulation' in page
    assert '-webkit-tap-highlight-color: transparent' in page
    assert 'user-select: none; -webkit-user-select: none' in page
    assert 'button, input, select, textarea { font-size: 16px; }' in page
    assert 'min-height: 44px' in page
    assert 'accept="image/*" capture="environment"' in page
    assert 'aria-live="polite"' in page
    assert 'let captureInProgress = false;' in page
    assert 'if (!file || captureInProgress)' in page
    assert "notice.textContent = 'Preparing capture';" in page
    assert "notice.textContent = 'Uploading';" in page
    assert "captureInput.disabled = isProcessing;" in page
    assert "captureControl.setAttribute('aria-busy', String(isProcessing));" in page
    assert "Capture failed. The image file could not be read." in page
    assert "Capture failed. The upload request could not be completed." in page
    assert "Capture failed. The server did not accept the image." in page
    assert "notice.textContent = `Captured ${captured.evidence_id}.`;" in page
    assert 'captureInProgress = false;' in page
    assert "setCaptureProcessing(false);" in page
    assert "event.target.value = '';" in page
    assert 'loadWorkbench({ preserveNotice: true });' in page


def test_relationship_review_page_and_json_share_current_state(client: TestClient) -> None:
    item_url = "/workbench/api/v1/relationship-reviews/REL-FIC-0001"

    queue = client.get("/workbench/api/v1/relationship-reviews", auth=credentials())
    item = client.get(item_url, auth=credentials())
    page = client.get("/workbench/relationship-reviews/REL-FIC-0001", auth=credentials())

    assert queue.status_code == 200
    assert queue.json()["result"]["code"] == "RELATIONSHIP_QUEUE_READY"
    assert item.status_code == 200
    assert item.json()["result"]["code"] == "RELATIONSHIP_REVIEW_READY"
    assert item.json()["state"]["current_version"] == 1
    assert page.status_code == 200
    payload = page.text.split(
        '<pre id="relationship-review-state">', 1
    )[1].split("</pre>", 1)[0]
    assert json.loads(html.unescape(payload)) == item.json()


def test_relationship_review_page_renders_workflow_fields_as_html(
    client: TestClient,
) -> None:
    response = client.get(
        "/workbench/relationship-reviews/REL-FIC-0001",
        auth=credentials(),
    )

    assert response.status_code == 200
    assert "<h2>Linked Records</h2>" in response.text
    assert "<dt>Source Record</dt><dd>OBL-FIC-0001</dd>" in response.text
    assert "<dt>Target Record</dt><dd>RSK-FIC-0001</dd>" in response.text
    assert "<h2>Source Support</h2>" in response.text
    assert "<h2>Warnings</h2>" in response.text
    assert "<h2>Version History</h2>" in response.text
    assert "<h2>Earlier Decisions</h2>" in response.text
    assert "Fictional relationship proposal awaiting review." in response.text


def test_authenticated_relationship_routes_create_one_accepted_trace(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.ace.workbench import routes
    from src.ace.workbench.relationship_review import RelationshipReviewService
    from tests.test_relationship_review import trace_input_values

    monkeypatch.setattr(
        routes,
        "relationship_review_service",
        lambda: RelationshipReviewService(WorkbenchStore(), trace_input_provider=trace_input_values),
    )
    result: dict[str, object] = {}
    for number in range(1, 5):
        relationship_id = f"REL-FIC-000{number}"
        preview = client.post(
            f"/workbench/api/v1/relationship-reviews/{relationship_id}/approval-preview",
            auth=credentials(),
            json={
                "relationship_version": 1,
                "approval_reason": "Fictional relationship approval.",
            },
        )
        assert preview.status_code == 200
        result = client.post(
            f"/workbench/api/v1/relationship-reviews/{relationship_id}/decision",
            auth=credentials(),
            json={
                "relationship_version": 1,
                "decision": "APPROVED",
                "reason": "Fictional relationship approval.",
                "decision_key": f"relationship-http-trace-000{number}",
                "preview_token": preview.json()["preview_token"],
            },
        ).json()

    with WorkbenchStore().connect() as connection:
        trace_count = connection.execute(
            "SELECT COUNT(*) FROM accepted_planning_traces"
        ).fetchone()[0]

    assert result["result"]["code"] == "RELATIONSHIP_DECISION_RECORDED"
    assert result["trace_created"] is True
    assert trace_count == 1


def test_relationship_review_routes_are_strict_and_authenticated(client: TestClient) -> None:
    url = "/workbench/api/v1/relationship-reviews/REL-FIC-0001/draft"
    revision_url = "/workbench/api/v1/relationship-reviews/REL-FIC-0001/revisions"

    assert client.put(url, json={}).status_code == 401
    assert client.post(revision_url, json={}).status_code == 401
    response = client.put(
        url,
        auth=credentials(),
        json={
            "relationship_version": 1,
            "proposed_decision": "APPROVED",
            "draft_reason": "Fictional review note.",
            "extra": "blocked",
        },
    )

    assert response.status_code == 422

    oversized = client.put(
        url,
        auth=credentials(),
        json={
            "relationship_version": 1,
            "proposed_decision": "APPROVED",
            "draft_reason": "x" * 4001,
        },
    )

    assert oversized.status_code == 422

    saved = client.put(
        url,
        auth=credentials(),
        json={
            "relationship_version": 1,
            "proposed_decision": "APPROVED",
            "draft_reason": "Fictional review note.",
        },
    )
    preview_response = client.post(
        "/workbench/api/v1/relationship-reviews/REL-FIC-0001/approval-preview",
        auth=credentials(),
        json={
            "relationship_version": 1,
            "approval_reason": "Fictional approval reason.",
        },
    )
    missing_preview_body = client.post(
        "/workbench/api/v1/relationship-reviews/REL-FIC-0001/approval-preview",
        auth=credentials(),
    )

    assert saved.status_code == 200
    assert saved.json()["result"]["code"] == "RELATIONSHIP_DRAFT_SAVED"
    assert preview_response.status_code == 200
    assert preview_response.json()["result"]["code"] == "RELATIONSHIP_APPROVAL_PREVIEW_READY"
    assert missing_preview_body.status_code == 422
    assert client.post(
        revision_url,
        auth=credentials(),
        json={
            "prior_relationship_version": 1,
            "revision_key": "relationship-revision-0001",
            "rationale": "Fictional correction.",
            "supporting_source_ids": ["SRC-FIC-001"],
            "gaps": [],
            "contradictions": [],
            "duplicate_warnings": [],
            "extra": "blocked",
        },
    ).status_code == 422
