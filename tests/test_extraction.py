"""Focused tests for the deterministic evidence extraction suggestions endpoint."""

import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.ace.app import app
from src.ace.workbench.extraction import EvidenceExtractionAdapter
from src.ace.workbench.storage import WorkbenchStore


def _credentials() -> tuple[str, str]:
    return ("auditor", "fictional-password")


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path / "sqe-local-data"))
    return TestClient(app)


class TestAdapter:
    def test_extract_returns_facts_and_warnings(self) -> None:
        adapter = EvidenceExtractionAdapter()
        text = "The inspection was completed on 12 August. No quorum was recorded."
        suggestions = adapter.extract(text)
        types = {s.type for s in suggestions}
        assert "FACT" in types
        assert "WARNING" in types

    def test_extract_empty_text_returns_empty(self) -> None:
        adapter = EvidenceExtractionAdapter()
        assert adapter.extract("") == []
        assert adapter.extract("   ") == []

    def test_extract_spans_match_source_exactly(self) -> None:
        adapter = EvidenceExtractionAdapter()
        text = "The inspection was completed on 12 August."
        suggestions = adapter.extract(text)
        for s in suggestions:
            assert text[s.start : s.end] == s.text

    def test_extract_is_deterministic(self) -> None:
        adapter = EvidenceExtractionAdapter()
        text = "The inspection was completed on 12 August 2026. No quorum was recorded."
        first = adapter.extract(text)
        second = adapter.extract(text)
        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert a.type == b.type
            assert a.text == b.text
            assert a.start == b.start
            assert a.end == b.end

    def test_extract_sorted_by_position(self) -> None:
        adapter = EvidenceExtractionAdapter()
        text = "Five non-conformances were identified. The assessment has been approved."
        suggestions = adapter.extract(text)
        positions = [s.start for s in suggestions]
        assert positions == sorted(positions)


class TestConfigurableRules:
    def test_custom_rules_replace_defaults(self) -> None:
        custom = re.compile(r"(?P<text>custom pattern)", re.IGNORECASE)
        adapter = EvidenceExtractionAdapter(rules=[(custom, "FACT")])
        suggestions = adapter.extract("The inspection was completed. custom pattern here.")
        assert len(suggestions) == 1
        assert suggestions[0].text == "custom pattern"
        assert suggestions[0].type == "FACT"

    def test_add_rule_extends_matches(self) -> None:
        adapter = EvidenceExtractionAdapter()
        before = adapter.extract("XYZ-999 special finding")
        has_xyz = any("XYZ-999" in s.text for s in before)
        assert not has_xyz, "XYZ-999 should not match any default rule"

        adapter.add_rule(re.compile(r"XYZ-\d{3}\s+special\s+finding", re.IGNORECASE), "WARNING")
        after = adapter.extract("XYZ-999 special finding")
        xyz_matches = [s for s in after if "XYZ-999" in s.text]
        assert len(xyz_matches) == 1
        assert xyz_matches[0].type == "WARNING"

    def test_default_rules_not_mutated_by_instance(self) -> None:
        from src.ace.workbench.extraction import DEFAULT_RULES

        original_len = len(DEFAULT_RULES)
        adapter = EvidenceExtractionAdapter()
        adapter.add_rule(re.compile(r"garbage"), "FACT")

        # DEFAULT_RULES should be unchanged
        assert len(DEFAULT_RULES) == original_len

        # A second adapter still gets the original defaults
        adapter2 = EvidenceExtractionAdapter()
        assert len(adapter2._rules) == original_len

    def test_add_rule_deterministic(self) -> None:
        adapter = EvidenceExtractionAdapter()
        adapter.add_rule(re.compile(r"extra check \d+", re.IGNORECASE), "FACT")
        first = adapter.extract("extra check 42 completed")
        second = adapter.extract("extra check 42 completed")
        assert first == second


class TestSuggestionsEndpoint:
    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        assert (
            client.get("/workbench/api/v1/evidence/EVD-FIC-0001/suggestions").status_code
            == 401
        )

    def test_authenticated_returns_suggestions(self, client: TestClient) -> None:
        response = client.get(
            "/workbench/api/v1/evidence/EVD-FIC-0001/suggestions", auth=_credentials()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["api_version"] == "v1"
        assert data["evidence_id"] == "EVD-FIC-0001"
        assert isinstance(data["suggestions"], list)

    def test_suggestions_include_facts_and_warnings(self, client: TestClient) -> None:
        response = client.get(
            "/workbench/api/v1/evidence/EVD-FIC-0001/suggestions", auth=_credentials()
        )
        assert response.status_code == 200
        suggestions = response.json()["suggestions"]
        types = {s["type"] for s in suggestions}
        assert "FACT" in types
        assert "WARNING" in types

    def test_suggestions_have_exact_source_spans(self, client: TestClient) -> None:
        response = client.get(
            "/workbench/api/v1/evidence/EVD-FIC-0001/suggestions", auth=_credentials()
        )
        assert response.status_code == 200
        data = response.json()
        # Retrieve the seeded source text so we can verify exact slices
        data_dir = os.environ.get("ACE_DATA_DIR", "")
        store = WorkbenchStore(data_dir=Path(data_dir) if data_dir else None)
        with store.connect() as conn:
            records = conn.execute(
                "SELECT source_text FROM evidence WHERE evidence_id = ?",
                ("EVD-FIC-0001",),
            ).fetchall()
        assert records, "seeded EVD-FIC-0001 must have source_text"
        source_text = records[0]["source_text"]
        assert source_text, "source_text must not be empty"
        for s in data["suggestions"]:
            assert isinstance(s["source_start"], int)
            assert isinstance(s["source_end"], int)
            assert s["source_start"] >= 0
            assert s["source_end"] > s["source_start"]
            assert (
                source_text[s["source_start"] : s["source_end"]] == s["text"]
            ), f"slice [{s['source_start']}:{s['source_end']}] should equal '{s['text']}'"

    def test_suggestions_are_deterministic(self, client: TestClient) -> None:
        first = client.get(
            "/workbench/api/v1/evidence/EVD-FIC-0001/suggestions", auth=_credentials()
        )
        second = client.get(
            "/workbench/api/v1/evidence/EVD-FIC-0001/suggestions", auth=_credentials()
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == second.json()

    def test_empty_source_text_returns_empty_list(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        evidence_id = "EVD-EMPTY-0001"
        store = WorkbenchStore(tmp_path / "sqe-local-data")
        with store.connect() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO evidence (
                    evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                    is_capture, engagement_id, source_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    evidence_id,
                    "OWN-FIC-0001",
                    "empty.png",
                    "image/png",
                    None,
                    "PENDING_REVIEW",
                    "2026-08-15T10:00:00Z",
                    1,
                    "ENG-FIC-0001",
                    "",
                ),
            )

        response = client.get(
            f"/workbench/api/v1/evidence/{evidence_id}/suggestions", auth=_credentials()
        )
        assert response.status_code == 200
        assert response.json()["suggestions"] == []

    def test_nonexistent_evidence_returns_empty_list(
        self, client: TestClient
    ) -> None:
        response = client.get(
            "/workbench/api/v1/evidence/EVD-NONEXISTENT/suggestions",
            auth=_credentials(),
        )
        assert response.status_code == 200
        assert response.json()["suggestions"] == []

    def test_no_source_text_returns_empty_list(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        evidence_id = "EVD-NOSOURCE-0001"
        store = WorkbenchStore(tmp_path / "sqe-local-data")
        with store.connect() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO evidence (
                    evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                    is_capture, engagement_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    evidence_id,
                    "OWN-FIC-0001",
                    "nosource.png",
                    "image/png",
                    None,
                    "PENDING_REVIEW",
                    "2026-08-15T10:00:00Z",
                    1,
                    "ENG-FIC-0001",
                ),
            )

        response = client.get(
            f"/workbench/api/v1/evidence/{evidence_id}/suggestions", auth=_credentials()
        )
        assert response.status_code == 200
        assert response.json()["suggestions"] == []

    def test_endpoint_is_read_only_no_write_path(self, client: TestClient) -> None:
        get_response = client.get(
            "/workbench/api/v1/evidence/EVD-FIC-0001/suggestions", auth=_credentials()
        )
        assert get_response.status_code == 200

        post_response = client.post(
            "/workbench/api/v1/evidence/EVD-FIC-0001/suggestions",
            auth=_credentials(),
            json={},
        )
        assert post_response.status_code == 405

        put_response = client.put(
            "/workbench/api/v1/evidence/EVD-FIC-0001/suggestions",
            auth=_credentials(),
            json={},
        )
        assert put_response.status_code == 405

    def test_evidence_review_page_has_suggestions_section(
        self, client: TestClient
    ) -> None:
        page = client.get(
            "/workbench/evidence/EVD-FIC-0001/review", auth=_credentials()
        )
        assert page.status_code == 200
        text = page.text
        assert "Review Suggestions" in text
        assert "suggestions-list" in text
