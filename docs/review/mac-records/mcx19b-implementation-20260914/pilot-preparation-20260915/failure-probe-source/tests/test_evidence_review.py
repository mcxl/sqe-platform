"""Evidence Review tests use fictional local workbench data only."""

from __future__ import annotations

import base64
import inspect
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from src.ace.app import app
from src.ace.workbench.evidence_review import EvidenceReviewService
from src.ace.workbench.routes import EvidenceReviewCompletionRequest
from src.ace.workbench.storage import WorkbenchStore


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQAB"
    "pfZFQAAAAABJRU5ErkJggg=="
)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path / "sqe-local-data"))
    return TestClient(app)


def credentials() -> tuple[str, str]:
    return ("auditor", "fictional-password")


def capture(client: TestClient, name: str) -> str:
    response = client.post(
        "/workbench/api/v1/evidence",
        auth=credentials(),
        json={
            "filename": f"fictional-{name}.png",
            "media_type": "image/png",
            "data_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
            "capture_attempt_key": f"capture-{name}-0001",
        },
    )
    assert response.status_code == 201
    return response.json()["evidence"]["evidence_id"]


def context(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
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
    }
    values.update(changes)
    return values


def save_context(client: TestClient, evidence_id: str, **changes: object) -> Response:
    return client.put(
        f"/workbench/api/v1/evidence/{evidence_id}/review/context",
        auth=credentials(),
        json=context(**changes),
    )


def question(client: TestClient, question_type: str, parent: str | None = None) -> str:
    response = client.post(
        "/workbench/api/v1/audit-questions",
        auth=credentials(),
        json={
            "engagement_id": "ENG-FIC-0001",
            "control_id": "CTL-FIC-0001",
            "question_type": question_type,
            "parent_question_id": parent,
            "question_text": f"Fictional {question_type} question?",
            "purpose": f"Fictional {question_type} purpose",
        },
    )
    assert response.status_code == 201
    return response.json()["question_version"]["question_id"]


def version(client: TestClient, question_id: str, number: int) -> None:
    response = client.post(
        f"/workbench/api/v1/audit-questions/{question_id}/versions",
        auth=credentials(),
        json={
            "question_id": question_id,
            "question_text": f"Fictional revised question {number}?",
            "purpose": f"Fictional revised purpose {number}",
        },
    )
    assert response.status_code == 201
    assert response.json()["question_version"]["version"] == number


def test_all_evidence_review_routes_require_authentication(client: TestClient) -> None:
    evidence_id = "EVD-FIC-0001"
    checks = (
        ("get", f"/workbench/evidence/{evidence_id}/review", None),
        ("get", f"/workbench/api/v1/evidence/{evidence_id}/review", None),
        ("get", f"/workbench/evidence/{evidence_id}/media", None),
        ("put", f"/workbench/api/v1/evidence/{evidence_id}/review/context", context()),
        ("post", "/workbench/api/v1/audit-questions", {}),
        ("post", "/workbench/api/v1/audit-questions/AQ-FIC/versions", {}),
        ("post", "/workbench/api/v1/audit-questions/AQ-FIC/decisions", {}),
        ("post", f"/workbench/api/v1/evidence/{evidence_id}/proposed-links", {}),
        ("post", f"/workbench/api/v1/evidence/{evidence_id}/review/complete", {}),
        ("post", f"/workbench/evidence/{evidence_id}/review", {"notes": "Fictional legacy review."}),
    )
    for method, path, payload in checks:
        response = getattr(client, method)(path, json=payload) if payload is not None else getattr(client, method)(path)
        assert response.status_code == 401


def test_page_has_accessible_complete_review_controls(client: TestClient) -> None:
    evidence_id = capture(client, "page")
    page = client.get(f"/workbench/evidence/{evidence_id}/review", auth=credentials())
    assert page.status_code == 200
    for label in (
        "Source Context And Gaps", "Provider", "Origin", "Gap Materiality", "Purpose",
        "MAIN Parent", "Decision", "Relevance", "Reviewed Unlinked",
    ):
        assert label in page.text
    assert "context-form" in page.text
    assert "question-form" in page.text
    assert "complete-form" in page.text
    assert "selectedQuestionId(form)" in page.text
    assert "${value(form,'question_id')}/versions" not in page.text
    assert page.text.count('throw new Error("Create an Audit Question version first.")') == 2


def test_complete_review_generates_and_retains_hidden_retry_key(client: TestClient) -> None:
    evidence_id = capture(client, "completion-key-page")
    page = client.get(f"/workbench/evidence/{evidence_id}/review", auth=credentials())

    assert page.status_code == 200
    assert "Completion Attempt Key" not in page.text
    assert 'name="completion_attempt_key"' not in page.text
    assert "let state, decisionAttemptKey, completionAttemptKey;" in page.text

    handler = page.text.split("document.querySelector('#complete-form').onsubmit", 1)[1]
    handler = handler.split("; load().catch", 1)[0]
    request_index = handler.index("await request(")
    clear_index = handler.index("completionAttemptKey=null;")
    error_handler = handler.split("catch(error)", 1)[1]

    assert "completionAttemptKey ??= `completion-${crypto.randomUUID()}`;" in handler
    assert "completion_attempt_key:completionAttemptKey" in handler
    assert request_index < clear_index
    assert "completionAttemptKey=null;" not in error_handler


def test_review_state_exposes_existing_engagement_controls_and_hydrates_context(
    client: TestClient,
) -> None:
    evidence_id = capture(client, "state-controls")
    assert save_context(client, evidence_id).status_code == 200

    state = client.get(
        f"/workbench/api/v1/evidence/{evidence_id}/review", auth=credentials()
    ).json()
    assert state["available_controls"] == [
        {"control_id": "CTL-FIC-0001", "title": "Fictional capture control"}
    ]

    page = client.get(f"/workbench/evidence/{evidence_id}/review", auth=credentials())
    assert page.status_code == 200
    assert '<select name="control_id"' in page.text
    assert '<input name="control_id" value="CTL-FIC-0001"' not in page.text
    assert 'id="context-save" disabled' in page.text
    assert "hydrateSourceContext" in page.text
    for field in (
        "provider",
        "origin",
        "source_date",
        "source_version",
        "source_location",
        "description",
        "freshness",
        "limitations",
        "duplicate_evidence_id",
        "source_evidence_ids",
        "gap_status",
        "gap_explanation",
        "gap_materiality",
    ):
        assert field in page.text
    assert "JSON.stringify(body.detail)" in page.text


def test_review_page_disables_question_creation_when_current_engagement_has_no_controls(
    client: TestClient,
) -> None:
    created = client.post(
        "/workbench/api/v1/engagements",
        auth=credentials(),
        json={
            "creation_attempt_key": "no-controls-engagement-0001",
            "title": "Fictional No Controls Engagement",
            "reference": "ENG-NO-CONTROLS-001",
            "authority": "Fictional authority",
            "purpose": "Test the no-controls review state",
            "scope": "Fictional scope",
            "exclusions": "Real-client information",
            "review_start_date": "2026-08-01",
            "review_end_date": "2026-08-31",
            "evidence_cut_off_date": "2026-08-15",
            "accountable_auditor": "Fictional Site Auditor",
            "data_classification": "FICTIONAL",
            "is_fictional": True,
        },
    )
    assert created.status_code == 201
    engagement_id = created.json()["engagement"]["engagement_id"]
    assert client.post(
        f"/workbench/api/v1/engagements/{engagement_id}/activate",
        auth=credentials(),
        json={"confirmed": True},
    ).status_code == 200
    evidence_id = capture(client, "no-controls")

    state = client.get(
        f"/workbench/api/v1/evidence/{evidence_id}/review", auth=credentials()
    ).json()
    assert state["available_controls"] == []
    rejected_question = client.post(
        "/workbench/api/v1/audit-questions",
        auth=credentials(),
        json={
            "engagement_id": engagement_id,
            "control_id": "CTL-NO-CONTROLS-001",
            "question_type": "MAIN",
            "question_text": "Fictional question without a Control?",
            "purpose": "Test the controlled no-controls rejection",
        },
    )
    assert rejected_question.status_code == 422
    assert rejected_question.json()["detail"] == "Control does not belong to the Engagement"

    page = client.get(f"/workbench/evidence/{evidence_id}/review", auth=credentials())
    assert page.status_code == 200
    assert "No ACE Controls exist for this Engagement." in page.text
    assert 'id="question-submit" disabled' in page.text


def test_context_rules_versions_decisions_and_proposed_links(client: TestClient) -> None:
    raw_one = capture(client, "raw-one")
    raw_two = capture(client, "raw-two")
    derived = capture(client, "derived")
    assert save_context(client, raw_one).status_code == 200
    assert save_context(client, raw_two).status_code == 200
    saved = save_context(
        client,
        derived,
        provider="Fictional derived provider",
        origin="DERIVED",
        source_date="2026-08-13",
        source_version="2.0",
        source_location="Fictional derived register",
        description="Fictional derived description",
        freshness="STALE",
        limitations="Fictional derived limitation",
        duplicate_evidence_id=raw_two,
        source_evidence_ids=[raw_one, raw_two],
        gap_status="INADEQUATE",
        gap_explanation="Fictional derived gap",
        gap_materiality="MATERIAL",
    )
    assert saved.status_code == 200
    returned_context = client.get(
        f"/workbench/api/v1/evidence/{derived}/review", auth=credentials()
    ).json()["source_context"]
    assert returned_context["provider"] == "Fictional derived provider"
    assert returned_context["source_date"] == "2026-08-13"
    assert returned_context["source_version"] == "2.0"
    assert returned_context["source_location"] == "Fictional derived register"
    assert returned_context["description"] == "Fictional derived description"
    assert returned_context["freshness"] == "STALE"
    assert returned_context["limitations"] == "Fictional derived limitation"
    assert returned_context["duplicate_evidence_id"] == raw_two
    assert returned_context["source_evidence_ids"] == [raw_one, raw_two]
    assert returned_context["gap_status"] == "INADEQUATE"
    assert returned_context["gap_explanation"] == "Fictional derived gap"
    assert returned_context["gap_materiality"] == "MATERIAL"
    assert client.put(
        f"/workbench/api/v1/evidence/{raw_one}/review/context",
        auth=credentials(), json=context(evidence_id="EVD-FIC-0001"),
    ).status_code == 422
    self_reference = save_context(
        client, derived, origin="DERIVED", source_evidence_ids=[raw_one, derived]
    )
    assert self_reference.status_code == 422
    assert self_reference.json()["detail"] == "Source Evidence Item must differ from this item"
    assert save_context(client, derived, origin="RAW", source_evidence_ids=[raw_one]).status_code == 422
    assert save_context(client, derived, origin="DERIVED").status_code == 422
    assert save_context(client, derived, duplicate_evidence_id=derived).status_code == 422
    assert save_context(
        client, derived, gap_status="INADEQUATE", gap_explanation="Fictional gap", gap_materiality="MATERIAL"
    ).status_code == 200
    assert save_context(client, derived, gap_status="INADEQUATE").status_code == 422

    main = question(client, "MAIN")
    implementation = question(client, "IMPLEMENTATION", main)
    effectiveness = question(client, "EFFECTIVENESS", main)
    version(client, main, 2)
    version(client, implementation, 2)
    version(client, effectiveness, 2)
    state = client.get(f"/workbench/api/v1/evidence/{derived}/review", auth=credentials()).json()
    main_versions = [item for item in state["question_versions"] if item["question_id"] == main]
    assert [item["purpose"] for item in main_versions] == ["Fictional MAIN purpose", "Fictional revised purpose 2"]

    for question_id, question_version, status in (
        (main, 1, "APPROVED"), (implementation, 1, "REJECTED"), (effectiveness, 1, "CHANGES_REQUIRED"),
    ):
        response = client.post(
            f"/workbench/api/v1/audit-questions/{question_id}/decisions", auth=credentials(),
            json={
                "decision_attempt_key": f"decision-{status.lower()}-0001",
                "question_version": question_version,
                "status": status,
                "reason": f"Fictional {status} reason",
            },
        )
        assert response.status_code == 201
    duplicate_decision = client.post(
        f"/workbench/api/v1/audit-questions/{main}/decisions", auth=credentials(),
        json={
            "decision_attempt_key": "decision-second-0001",
            "question_version": 1,
            "status": "REJECTED",
            "reason": "Fictional second decision",
        },
    )
    assert duplicate_decision.status_code == 409

    for question_id, question_version, relevance in (
        (main, 1, "SUPPORTS"), (main, 2, "WEAKENS"), (effectiveness, 2, "CONTRADICTS"),
    ):
        response = client.post(
            f"/workbench/api/v1/evidence/{derived}/proposed-links", auth=credentials(),
            json={"question_id": question_id, "question_version": question_version, "relevance": relevance, "reason": f"Fictional {relevance} reason"},
        )
        assert response.status_code == 201
    duplicate_link = client.post(
        f"/workbench/api/v1/evidence/{derived}/proposed-links", auth=credentials(),
        json={"question_id": main, "question_version": 1, "relevance": "SUPPORTS", "reason": "Fictional second link"},
    )
    assert duplicate_link.status_code == 409
    review_state = client.get(
        f"/workbench/api/v1/evidence/{derived}/review", auth=credentials()
    ).json()
    assert {item["status"] for item in review_state["decisions"]} == {
        "APPROVED", "REJECTED", "CHANGES_REQUIRED"
    }
    assert {item["relevance"] for item in review_state["proposed_links"]} == {
        "SUPPORTS", "WEAKENS", "CONTRADICTS"
    }
    with WorkbenchStore().connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE audit_questions SET created_by = 'changed' WHERE question_id = ?", (main,)
            )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("DELETE FROM audit_questions WHERE question_id = ?", (main,))
        proposal_id = connection.execute("SELECT proposal_id FROM proposed_evidence_links LIMIT 1").fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("UPDATE proposed_evidence_links SET reason = 'Changed' WHERE proposal_id = ?", (proposal_id,))
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("DELETE FROM proposed_evidence_links WHERE proposal_id = ?", (proposal_id,))
        assert connection.execute("SELECT COUNT(*) FROM relationships").fetchone()[0] == 7


def test_referenced_raw_source_cannot_change_origin(client: TestClient) -> None:
    raw = capture(client, "origin-locked-raw")
    derived = capture(client, "origin-locked-derived")
    assert save_context(client, raw).status_code == 200
    assert save_context(
        client, derived, origin="DERIVED", source_evidence_ids=[raw]
    ).status_code == 200

    changed = save_context(client, raw, origin="AUDITOR_AUTHORED")

    assert changed.status_code == 422
    assert changed.json()["detail"] == (
        "Referenced RAW Evidence Item cannot change origin"
    )
    saved = client.get(
        f"/workbench/api/v1/evidence/{raw}/review", auth=credentials()
    ).json()["source_context"]
    assert saved["origin"] == "RAW"


def test_completion_rejects_stale_derived_provenance_atomically(client: TestClient) -> None:
    raw = capture(client, "stale-provenance-raw")
    derived = capture(client, "stale-provenance-derived")
    assert save_context(client, raw).status_code == 200
    assert save_context(
        client, derived, origin="DERIVED", source_evidence_ids=[raw]
    ).status_code == 200
    with WorkbenchStore().connect() as connection:
        connection.execute(
            "UPDATE evidence_review_contexts SET origin = 'AUDITOR_AUTHORED' WHERE evidence_id = ?",
            (raw,),
        )
        connection.commit()

    completed = client.post(
        f"/workbench/api/v1/evidence/{derived}/review/complete",
        auth=credentials(),
        json={"completion_attempt_key": "stale-provenance-0001"},
    )

    assert completed.status_code == 422
    assert completed.json()["detail"] == "Every derived source must have saved RAW context"
    with WorkbenchStore().connect() as connection:
        assert connection.execute(
            "SELECT status FROM evidence WHERE evidence_id = ?", (derived,)
        ).fetchone()[0] == "PENDING_REVIEW"
        assert connection.execute(
            "SELECT COUNT(*) FROM reviews WHERE evidence_id = ?", (derived,)
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM evidence_review_completions WHERE evidence_id = ?", (derived,)
        ).fetchone()[0] == 0
        assert connection.execute(
            """SELECT COUNT(*) FROM audit_events
               WHERE evidence_id = ? AND event_type = 'EVIDENCE_REVIEW_COMPLETED'""",
            (derived,),
        ).fetchone()[0] == 0


def test_audit_question_decision_exact_retry_returns_the_prior_decision(client: TestClient) -> None:
    main = question(client, "MAIN")
    payload = {
        "decision_attempt_key": "decision-retry-0001",
        "question_version": 1,
        "status": "APPROVED",
        "reason": "Fictional approved reason",
    }

    first = client.post(
        f"/workbench/api/v1/audit-questions/{main}/decisions", auth=credentials(), json=payload
    )
    retry = client.post(
        f"/workbench/api/v1/audit-questions/{main}/decisions", auth=credentials(), json=payload
    )

    assert first.status_code == 201
    assert retry.status_code == 201
    assert retry.json() == first.json()
    with WorkbenchStore().connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM audit_question_decisions WHERE question_id = ?", (main,)
        ).fetchone()[0] == 1


def test_audit_question_decision_rejects_conflicting_attempt_key_reuse(client: TestClient) -> None:
    main = question(client, "MAIN")
    first = client.post(
        f"/workbench/api/v1/audit-questions/{main}/decisions",
        auth=credentials(),
        json={
            "decision_attempt_key": "decision-conflict-0001",
            "question_version": 1,
            "status": "APPROVED",
            "reason": "Fictional approved reason",
        },
    )
    assert first.status_code == 201

    changed = client.post(
        f"/workbench/api/v1/audit-questions/{main}/decisions",
        auth=credentials(),
        json={
            "decision_attempt_key": "decision-conflict-0001",
            "question_version": 1,
            "status": "REJECTED",
            "reason": "Fictional rejected reason",
        },
    )
    assert changed.status_code == 409

    version(client, main, 2)
    different_version = client.post(
        f"/workbench/api/v1/audit-questions/{main}/decisions",
        auth=credentials(),
        json={
            "decision_attempt_key": "decision-conflict-0001",
            "question_version": 2,
            "status": "APPROVED",
            "reason": "Fictional approved reason",
        },
    )
    assert different_version.status_code == 409

    other_question = question(client, "MAIN")
    different_question = client.post(
        f"/workbench/api/v1/audit-questions/{other_question}/decisions",
        auth=credentials(),
        json={
            "decision_attempt_key": "decision-conflict-0001",
            "question_version": 1,
            "status": "APPROVED",
            "reason": "Fictional approved reason",
        },
    )
    assert different_question.status_code == 409


def test_legacy_audit_question_decision_schema_adds_attempt_columns(tmp_path: Path) -> None:
    data_dir = tmp_path / "sqe-local-data"
    data_dir.mkdir()
    database_path = data_dir / "workbench.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """CREATE TABLE audit_question_decisions (
                decision_id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                question_version INTEGER NOT NULL,
                status TEXT NOT NULL,
                reason TEXT NOT NULL,
                decided_at TEXT NOT NULL,
                decided_by TEXT NOT NULL,
                UNIQUE (question_id, question_version)
            )"""
        )

    with WorkbenchStore(data_dir).connect() as connection:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(audit_question_decisions)")}
        indexes = {row["name"] for row in connection.execute("PRAGMA index_list(audit_question_decisions)")}

    assert {"decision_attempt_key", "request_sha256"} <= columns
    assert "decision_attempt_key_unique" in indexes


def test_completion_requires_context_is_global_retry_safe_and_freezes_data(client: TestClient) -> None:
    first = capture(client, "complete-first")
    second = capture(client, "complete-second")
    assert client.post(
        f"/workbench/api/v1/evidence/{first}/review/complete", auth=credentials(),
        json={"completion_attempt_key": "complete-first-0001"},
    ).status_code == 422
    assert save_context(client, first).status_code == 200
    main = question(client, "MAIN")
    assert client.post(
        f"/workbench/api/v1/evidence/{first}/proposed-links",
        auth=credentials(),
        json={
            "question_id": main,
            "question_version": 1,
            "relevance": "SUPPORTS",
            "reason": "Fictional completion link",
        },
    ).status_code == 201
    with WorkbenchStore().connect() as connection:
        relationship_count = connection.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
    complete = client.post(
        f"/workbench/api/v1/evidence/{first}/review/complete", auth=credentials(),
        json={"completion_attempt_key": "complete-global-0001", "notes": "Fictional completion."},
    )
    assert complete.status_code == 200
    assert client.post(
        f"/workbench/api/v1/evidence/{first}/review/complete", auth=credentials(),
        json={"completion_attempt_key": "complete-global-0001", "notes": "Fictional completion."},
    ).json() == complete.json()
    with WorkbenchStore().connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM relationships").fetchone()[0] == relationship_count
        assert connection.execute(
            "SELECT COUNT(*) FROM audit_events WHERE evidence_id = ? AND event_type = 'EVIDENCE_REVIEW_COMPLETED'",
            (first,),
        ).fetchone()[0] == 1
    assert client.post(
        f"/workbench/api/v1/evidence/{second}/review/complete", auth=credentials(),
        json={"completion_attempt_key": "complete-global-0001", "notes": "Fictional completion."},
    ).status_code == 409
    assert client.post(
        f"/workbench/api/v1/evidence/{first}/review/complete", auth=credentials(),
        json={"completion_attempt_key": "complete-global-0001", "notes": "Changed fictional completion."},
    ).status_code == 409
    assert save_context(client, first).status_code == 409
    assert client.post(
        f"/workbench/api/v1/evidence/{first}/proposed-links", auth=credentials(),
        json={"question_id": "AQ-NOT-FOUND", "question_version": 1, "relevance": "SUPPORTS", "reason": "Frozen"},
    ).status_code == 409
    legacy_completion = client.post(
        f"/workbench/evidence/{second}/review", auth=credentials(), json={"notes": "Legacy fictional review."}
    )
    assert legacy_completion.status_code == 422
    assert legacy_completion.json()["detail"] == "Save source context before review completion"
    assert save_context(client, second).status_code == 200
    assert client.post(
        f"/workbench/evidence/{second}/review", auth=credentials(), json={"notes": "Legacy fictional review."}
    ).status_code == 200
    summary = client.get("/workbench/summary", auth=credentials()).json()
    assert second in {item["evidence_id"] for item in summary["reviewed_unlinked"]}
    with WorkbenchStore().connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE audit_events SET actor = 'changed' WHERE evidence_id = ? AND event_type = 'EVIDENCE_REVIEW_COMPLETED'",
                (first,),
            )


@pytest.mark.parametrize(
    ("statement", "value_statement", "expected_value"),
    [
        pytest.param(
            "UPDATE evidence_review_contexts SET provider = 'changed' WHERE evidence_id = ?",
            "SELECT provider FROM evidence_review_contexts WHERE evidence_id = ?",
            "Fictional field team",
            id="context-update",
        ),
        pytest.param(
            "DELETE FROM evidence_review_contexts WHERE evidence_id = ?",
            "SELECT COUNT(*) FROM evidence_review_contexts WHERE evidence_id = ?",
            1,
            id="context-delete",
        ),
        pytest.param(
            "UPDATE reviews SET notes = 'changed' WHERE evidence_id = ?",
            "SELECT notes FROM reviews WHERE evidence_id = ?",
            "Fictional immutable review.",
            id="review-update",
        ),
        pytest.param(
            "DELETE FROM reviews WHERE evidence_id = ?",
            "SELECT COUNT(*) FROM reviews WHERE evidence_id = ?",
            1,
            id="review-delete",
        ),
        pytest.param(
            """INSERT OR REPLACE INTO reviews (
                review_id, evidence_id, reviewer, reviewed_at, notes
            ) VALUES ('REV-IMMUTABLE-REPLACE', ?, 'changed', '2026-08-14T00:00:00Z', 'changed')""",
            "SELECT notes FROM reviews WHERE evidence_id = ?",
            "Fictional immutable review.",
            id="review-insert-or-replace",
        ),
        pytest.param(
            "UPDATE evidence_review_completions SET request_sha256 = 'changed' WHERE evidence_id = ?",
            "SELECT request_sha256 FROM evidence_review_completions WHERE evidence_id = ?",
            None,
            id="completion-update",
        ),
        pytest.param(
            "DELETE FROM evidence_review_completions WHERE evidence_id = ?",
            "SELECT COUNT(*) FROM evidence_review_completions WHERE evidence_id = ?",
            1,
            id="completion-delete",
        ),
        pytest.param(
            "UPDATE evidence SET status = 'PENDING_REVIEW' WHERE evidence_id = ?",
            "SELECT status FROM evidence WHERE evidence_id = ?",
            "REVIEWED",
            id="reviewed-status-change",
        ),
        pytest.param(
            "UPDATE evidence SET filename = 'changed.png' WHERE evidence_id = ?",
            "SELECT filename FROM evidence WHERE evidence_id = ?",
            None,
            id="evidence-update",
        ),
        pytest.param(
            "DELETE FROM evidence WHERE evidence_id = ?",
            "SELECT COUNT(*) FROM evidence WHERE evidence_id = ?",
            1,
            id="evidence-delete",
        ),
        pytest.param(
            """INSERT OR REPLACE INTO evidence (
                evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                is_capture, engagement_id, capture_attempt_key, request_sha256
            ) SELECT evidence_id, owner_id, 'changed.png', media_type, media_path, status, captured_at,
                is_capture, engagement_id, capture_attempt_key, request_sha256
            FROM evidence WHERE evidence_id = ?""",
            "SELECT filename FROM evidence WHERE evidence_id = ?",
            None,
            id="evidence-insert-or-replace",
        ),
    ],
)
def test_completed_evidence_review_rejects_direct_sqlite_mutation(
    client: TestClient, statement: str, value_statement: str, expected_value: object
) -> None:
    evidence_id = capture(client, "immutable-direct-write")
    assert save_context(client, evidence_id).status_code == 200
    completed = client.post(
        f"/workbench/api/v1/evidence/{evidence_id}/review/complete",
        auth=credentials(),
        json={
            "completion_attempt_key": "immutable-direct-write-0001",
            "notes": "Fictional immutable review.",
        },
    )
    assert completed.status_code == 200

    with WorkbenchStore().connect() as connection:
        expected = expected_value
        if expected is None:
            expected = connection.execute(value_statement, (evidence_id,)).fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(statement, (evidence_id,))
        assert connection.execute(value_statement, (evidence_id,)).fetchone()[0] == expected


@pytest.mark.parametrize("notes", [pytest.param(None), pytest.param("__OMITTED__")])
def test_completion_normalises_null_or_omitted_notes_to_controlled_default(
    client: TestClient, notes: str | None
) -> None:
    evidence_id = capture(client, f"default-notes-{notes is None}")
    assert save_context(client, evidence_id).status_code == 200
    payload: dict[str, object] = {"completion_attempt_key": f"default-notes-{notes is None}-0001"}
    if notes != "__OMITTED__":
        payload["notes"] = notes

    response = client.post(
        f"/workbench/api/v1/evidence/{evidence_id}/review/complete",
        auth=credentials(),
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["completion"]["notes"] == "Evidence review completed."
    assert (
        EvidenceReviewCompletionRequest(**payload).model_dump()["notes"]
        == "Evidence review completed."
    )


def test_completion_rejects_empty_non_null_notes() -> None:
    with pytest.raises(ValueError):
        EvidenceReviewCompletionRequest(
            completion_attempt_key="empty-notes-0001", notes=""
        )


def test_legacy_completion_uses_the_store_review_path() -> None:
    class LegacyReviewStore:
        def review(self, evidence_id: str, reviewer: str, notes: str) -> dict[str, str]:
            return {"evidence_id": evidence_id, "reviewer": reviewer, "notes": notes}

    result = EvidenceReviewService(LegacyReviewStore()).complete_legacy(  # type: ignore[arg-type]
        "EVD-FIC-0001", "Fictional legacy review.", "auditor"
    )

    assert result == {
        "evidence_id": "EVD-FIC-0001",
        "reviewer": "auditor",
        "notes": "Fictional legacy review.",
    }


def test_store_review_uses_shared_completion_key_derivation(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence_id = capture(client, "shared-legacy-key")
    assert save_context(client, evidence_id).status_code == 200

    def shared_completion_hash(value: str, notes: str) -> str:
        assert (value, notes) == (evidence_id, "Fictional legacy review.")
        return "shared-completion-key"

    monkeypatch.setattr(
        WorkbenchStore,
        "_completion_sha256",
        staticmethod(shared_completion_hash),
    )
    store = WorkbenchStore()
    completed = store.review(evidence_id, "auditor", "Fictional legacy review.")

    assert completed is not None
    with store.connect() as connection:
        attempt_key = connection.execute(
            "SELECT completion_attempt_key FROM evidence_review_completions WHERE evidence_id = ?",
            (evidence_id,),
        ).fetchone()[0]
    assert attempt_key == "legacy-shared-completion-key"


def test_connect_migrates_legacy_reviewed_evidence_and_retries_with_trimmed_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "sqe-local-data"
    evidence_id = "EVD-ABCDEF123456"
    store = WorkbenchStore(data_dir)
    with store.connect():
        pass

    database_path = data_dir / "workbench.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO evidence (
                evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                is_capture, engagement_id, capture_attempt_key, request_sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                "OWN-FIC-0001",
                "Fictional legacy evidence",
                None,
                None,
                "REVIEWED",
                "2026-08-13T00:00:00Z",
                1,
                "ENG-FIC-0001",
                None,
                None,
            ),
        )
        connection.execute(
            """INSERT INTO reviews (
                review_id, evidence_id, reviewer, reviewed_at, notes
            ) VALUES (?, ?, ?, ?, ?)""",
            (
                "REV-LEGACY-0001",
                evidence_id,
                "legacy-auditor",
                "2026-08-13T01:00:00Z",
                "  Fictional legacy review.  ",
            ),
        )

    with store.connect() as connection:
        completion = connection.execute(
            """SELECT completion_attempt_key, request_sha256, review_id, completed_at
            FROM evidence_review_completions WHERE evidence_id = ?""",
            (evidence_id,),
        ).fetchone()

    assert completion is not None
    assert tuple(completion) == (
        "legacy-" + WorkbenchStore._completion_sha256(
            evidence_id, "Fictional legacy review."
        ),
        WorkbenchStore._completion_sha256(evidence_id, "Fictional legacy review."),
        "REV-LEGACY-0001",
        "2026-08-13T01:00:00Z",
    )

    with store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM evidence_review_completions WHERE evidence_id = ?",
            (evidence_id,),
        ).fetchone()[0] == 1

    state = store.evidence_review_state(evidence_id)
    assert state is not None
    assert state["completion_state"] == "REVIEWED"
    assert state["completion"] == {
        "completed_at": "2026-08-13T01:00:00Z",
        "reviewer": "legacy-auditor",
        "reviewed_at": "2026-08-13T01:00:00Z",
        "notes": "  Fictional legacy review.  ",
    }

    monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
    monkeypatch.setenv("ACE_DATA_DIR", str(data_dir))
    retry = TestClient(app).post(
        f"/workbench/evidence/{evidence_id}/review",
        auth=credentials(),
        json={"notes": "  Fictional legacy review.  "},
    )

    assert retry.status_code == 200
    assert retry.json() == {
        "evidence_id": evidence_id,
        "status": "REVIEWED",
        "reviewer": "legacy-auditor",
        "reviewed_at": "2026-08-13T01:00:00Z",
        "notes": "  Fictional legacy review.  ",
        "completed_at": "2026-08-13T01:00:00Z",
    }


def test_connect_repairs_legacy_reviewed_placeholder_before_completion_migration(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "sqe-local-data"
    store = WorkbenchStore(data_dir)
    with store.connect():
        pass

    database_path = data_dir / "workbench.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE evidence SET status = ?, engagement_id = NULL WHERE evidence_id = ?",
            ("REVIEWED", "EVD-FIC-0001"),
        )
        connection.execute(
            """INSERT INTO reviews (
                review_id, evidence_id, reviewer, reviewed_at, notes
            ) VALUES (?, ?, ?, ?, ?)""",
            (
                "REV-LEGACY-FIC-0001",
                "EVD-FIC-0001",
                "legacy-auditor",
                "2026-08-13T01:00:00Z",
                "Fictional legacy placeholder review.",
            ),
        )

    with store.connect() as connection:
        assert connection.execute(
            "SELECT engagement_id FROM evidence WHERE evidence_id = ?",
            ("EVD-FIC-0001",),
        ).fetchone()[0] == "ENG-FIC-0001"
        assert connection.execute(
            "SELECT COUNT(*) FROM evidence_review_completions WHERE evidence_id = ?",
            ("EVD-FIC-0001",),
        ).fetchone()[0] == 1

    with store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM evidence_review_completions WHERE evidence_id = ?",
            ("EVD-FIC-0001",),
        ).fetchone()[0] == 1


def test_connection_initialisation_does_not_drop_evidence_review_triggers() -> None:
    assert "DROP TRIGGER" not in inspect.getsource(WorkbenchStore._initialise)


def test_seeded_placeholder_belongs_to_current_engagement_for_controlled_review(
    tmp_path: Path,
) -> None:
    state = WorkbenchStore(tmp_path / "sqe-local-data").evidence_review_state("EVD-FIC-0001")

    assert state is not None
    assert state["evidence"]["engagement_id"] == "ENG-FIC-0001"
    assert state["engagement"]["engagement_id"] == "ENG-FIC-0001"


def test_connect_does_not_invent_legacy_completion_without_review(tmp_path: Path) -> None:
    data_dir = tmp_path / "sqe-local-data"
    evidence_id = "EVD-ABCDEF654321"
    store = WorkbenchStore(data_dir)
    with store.connect():
        pass

    database_path = data_dir / "workbench.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO evidence (
                evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                is_capture, engagement_id, capture_attempt_key, request_sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                "OWN-FIC-0001",
                "Fictional incomplete legacy evidence",
                None,
                None,
                "REVIEWED",
                "2026-08-13T00:00:00Z",
                1,
                "ENG-FIC-0001",
                None,
                None,
            ),
        )

    with store.connect() as connection:
        assert connection.execute(
            "SELECT status FROM evidence WHERE evidence_id = ?", (evidence_id,)
        ).fetchone()[0] == "REVIEWED"
        assert connection.execute(
            "SELECT COUNT(*) FROM evidence_review_completions WHERE evidence_id = ?",
            (evidence_id,),
        ).fetchone()[0] == 0


def test_read_only_review_queries_use_deferred_transactions(
    client: TestClient, tmp_path: Path
) -> None:
    class TracedWorkbenchStore(WorkbenchStore):
        def __init__(self, data_dir: Path) -> None:
            super().__init__(data_dir)
            self.transaction_trace: list[str] = []

        def connect(self) -> sqlite3.Connection:
            connection = super().connect()
            connection.set_trace_callback(self.transaction_trace.append)
            return connection

    evidence_id = capture(client, "deferred-reads")
    store = TracedWorkbenchStore(tmp_path / "sqe-local-data")
    for read in (lambda: store.evidence_review_state(evidence_id), lambda: store.media(evidence_id)):
        store.transaction_trace.clear()
        assert read() is not None
        transactions = {statement.strip().upper() for statement in store.transaction_trace}
        assert "BEGIN" in transactions
        assert "BEGIN IMMEDIATE" not in transactions


def test_not_found_review_writes_roll_back_without_commit(tmp_path: Path) -> None:
    class TracedWorkbenchStore(WorkbenchStore):
        def __init__(self, data_dir: Path) -> None:
            super().__init__(data_dir)
            self.transaction_trace: list[str] = []

        def connect(self) -> sqlite3.Connection:
            connection = super().connect()
            connection.set_trace_callback(self.transaction_trace.append)
            return connection

    store = TracedWorkbenchStore(tmp_path / "sqe-local-data")
    missing_evidence_id = "EVD-FIC-9999"
    writes = (
        lambda: store.save_evidence_review_context(missing_evidence_id, context(), "auditor"),
        lambda: store.create_proposed_link(
            missing_evidence_id,
            {
                "question_id": "AQ-FIC-0001",
                "question_version": 1,
                "relevance": "SUPPORTS",
                "reason": "Fictional missing-evidence link.",
            },
            "auditor",
        ),
        lambda: store.complete_evidence_review(
            missing_evidence_id,
            {
                "completion_attempt_key": "missing-completion-0001",
                "notes": "Fictional missing-evidence completion.",
            },
            "auditor",
        ),
    )

    for write in writes:
        store.transaction_trace.clear()
        assert write() is None
        transactions = {statement.strip().upper() for statement in store.transaction_trace}
        assert "ROLLBACK" in transactions
        assert "COMMIT" not in transactions


def test_upgrade_from_pre_purpose_question_versions_preserves_created_fields(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "sqe-local-data"
    data_dir.mkdir()
    database_path = data_dir / "workbench.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE audit_question_versions (
                question_id TEXT NOT NULL REFERENCES audit_questions(question_id),
                version INTEGER NOT NULL CHECK (version > 0),
                question_text TEXT NOT NULL CHECK (length(trim(question_text)) > 0),
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                PRIMARY KEY (question_id, version)
            )
            """
        )

    store = WorkbenchStore(data_dir)
    with store.connect():
        pass
    created = store.create_audit_question(
        {
            "engagement_id": "ENG-FIC-0001",
            "control_id": "CTL-FIC-0001",
            "question_type": "MAIN",
            "parent_question_id": None,
            "question_text": "Fictional migrated initial question?",
            "purpose": "Fictional migrated initial purpose",
        },
        "initial-auditor",
    )
    version = store.create_audit_question_version(
        created["question_id"],
        {
            "question_text": "Fictional migrated revised question?",
            "purpose": "Fictional migrated revised purpose",
        },
        "version-auditor",
    )

    with store.connect() as connection:
        rows = connection.execute(
            """
            SELECT version, question_text, purpose, created_at, created_by
            FROM audit_question_versions WHERE question_id = ? ORDER BY version
            """,
            (created["question_id"],),
        ).fetchall()

    assert [tuple(row) for row in rows] == [
        (
            1,
            "Fictional migrated initial question?",
            "Fictional migrated initial purpose",
            created["created_at"],
            "initial-auditor",
        ),
        (
            2,
            "Fictional migrated revised question?",
            "Fictional migrated revised purpose",
            version["created_at"],
            "version-auditor",
        ),
    ]


def test_workbench_mark_reviewed_opens_controlled_review_page(client: TestClient) -> None:
    page = client.get("/workbench", auth=credentials())
    assert page.status_code == 200
    assert "window.location.assign(`/workbench/evidence/${evidenceId}/review`)" in page.text
    assert "fetch(`/workbench/evidence/${evidenceId}/review`, {method: 'POST'" not in page.text
    assert "Mark Reviewed" not in page.text
    assert "Review Evidence" in page.text


def test_g0_media_and_atomic_completion(client: TestClient, tmp_path: Path) -> None:
    evidence_id = capture(client, "atomic")
    assert save_context(client, evidence_id).status_code == 200
    store = WorkbenchStore(tmp_path / "sqe-local-data")
    with store.connect() as connection:
        connection.execute("""CREATE TRIGGER fail_completion_event BEFORE INSERT ON audit_events
            WHEN NEW.event_type = 'EVIDENCE_REVIEW_COMPLETED'
            BEGIN SELECT RAISE(ABORT, 'fictional completion failure'); END;""")
        connection.commit()
    with pytest.raises(sqlite3.IntegrityError, match="fictional completion failure"):
        EvidenceReviewService(store).complete(
            evidence_id, {"completion_attempt_key": "complete-atomic-0001", "notes": "Fictional atomic review."}, "auditor"
        )
    with store.connect() as connection:
        assert connection.execute("SELECT status FROM evidence WHERE evidence_id = ?", (evidence_id,)).fetchone()[0] == "PENDING_REVIEW"
        assert connection.execute("SELECT COUNT(*) FROM audit_events WHERE event_type = 'EVIDENCE_REVIEW_COMPLETED'").fetchone()[0] == 0
    main = question(client, "MAIN")
    with store.connect() as connection:
        connection.execute("UPDATE engagement_setups SET data_classification = 'REAL_CLIENT', is_fictional = 0 WHERE engagement_id = 'ENG-FIC-0001'")
        connection.commit()
    for method, path, payload in (
        ("get", f"/workbench/api/v1/evidence/{evidence_id}/review", None),
        ("get", f"/workbench/evidence/{evidence_id}/review", None),
        ("get", f"/workbench/evidence/{evidence_id}/media", None),
        ("put", f"/workbench/api/v1/evidence/{evidence_id}/review/context", context()),
        ("post", f"/workbench/api/v1/evidence/{evidence_id}/review/complete", {"completion_attempt_key": "complete-g0-0001"}),
        ("post", f"/workbench/evidence/{evidence_id}/review", {"notes": "Blocked fictional legacy review."}),
    ):
        response = getattr(client, method)(path, auth=credentials(), json=payload) if payload is not None else getattr(client, method)(path, auth=credentials())
        assert response.status_code == 403
        assert "fictional-atomic" not in response.text
    for path, payload in (
        ("/workbench/api/v1/audit-questions", {
            "engagement_id": "ENG-FIC-0001", "control_id": "CTL-FIC-0001", "question_type": "MAIN",
            "question_text": "Blocked fictional question?", "purpose": "Blocked fictional purpose",
        }),
        (f"/workbench/api/v1/audit-questions/{main}/versions", {
            "question_text": "Blocked fictional version?", "purpose": "Blocked fictional purpose",
        }),
        (f"/workbench/api/v1/audit-questions/{main}/decisions", {
            "decision_attempt_key": "decision-g0-0001",
            "question_version": 1, "status": "APPROVED", "reason": "Blocked fictional reason",
        }),
        (f"/workbench/api/v1/evidence/{evidence_id}/proposed-links", {
            "question_id": main, "question_version": 1, "relevance": "SUPPORTS", "reason": "Blocked fictional reason",
        }),
    ):
        assert client.post(path, auth=credentials(), json=payload).status_code == 403


def test_full_record_review_flow_capture_to_completion(client: TestClient) -> None:
    """Complete record review: capture → context → questions → versions → decisions → links → completion."""
    evidence_id = capture(client, "full-flow")

    assert save_context(
        client, evidence_id,
        provider="Full Flow Provider",
        origin="RAW",
        source_date="2026-08-14",
        source_version="1.0",
        source_location="Full Flow Store",
        description="Full flow fictional evidence",
        freshness="CURRENT",
        limitations="Fictional limitation",
        gap_status="NOT_REQUESTED",
    ).status_code == 200

    main = question(client, "MAIN")
    impl = question(client, "IMPLEMENTATION", main)
    eff = question(client, "EFFECTIVENESS", main)

    version(client, main, 2)
    version(client, impl, 2)
    version(client, eff, 2)

    for question_id, question_version, status in (
        (main, 2, "APPROVED"),
        (impl, 2, "REJECTED"),
        (eff, 2, "CHANGES_REQUIRED"),
    ):
        assert client.post(
            f"/workbench/api/v1/audit-questions/{question_id}/decisions",
            auth=credentials(),
            json={
                "decision_attempt_key": f"decision-full-flow-{status.lower()}-0001",
                "question_version": question_version,
                "status": status,
                "reason": f"Full flow {status} reason",
            },
        ).status_code == 201

    for question_id, question_version, relevance in (
        (main, 2, "SUPPORTS"),
        (impl, 2, "WEAKENS"),
        (eff, 2, "CONTRADICTS"),
    ):
        assert client.post(
            f"/workbench/api/v1/evidence/{evidence_id}/proposed-links",
            auth=credentials(),
            json={
                "question_id": question_id,
                "question_version": question_version,
                "relevance": relevance,
                "reason": f"Full flow {relevance} reason",
            },
        ).status_code == 201

    completed = client.post(
        f"/workbench/api/v1/evidence/{evidence_id}/review/complete",
        auth=credentials(),
        json={
            "completion_attempt_key": "complete-full-flow-0001",
            "notes": "Full record review completed.",
        },
    )
    assert completed.status_code == 200
    assert completed.json()["completion"]["notes"] == "Full record review completed."

    state = client.get(
        f"/workbench/api/v1/evidence/{evidence_id}/review", auth=credentials()
    ).json()
    assert state["evidence"]["status"] == "REVIEWED"
    assert state["completion_state"] == "REVIEWED"
    assert state["completion"]["notes"] == "Full record review completed."
    assert len(state["decisions"]) == 3
    assert {d["status"] for d in state["decisions"]} == {"APPROVED", "REJECTED", "CHANGES_REQUIRED"}
    assert len(state["proposed_links"]) == 3
    assert {l["relevance"] for l in state["proposed_links"]} == {"SUPPORTS", "WEAKENS", "CONTRADICTS"}
    assert len(state["question_versions"]) == 6

    summary = client.get("/workbench/summary", auth=credentials()).json()
    assert summary["counts"]["reviewed"] > 0
