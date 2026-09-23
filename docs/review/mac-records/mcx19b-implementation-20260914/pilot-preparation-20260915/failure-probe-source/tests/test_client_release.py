"""Phase 6A — Client release view tests.

Covers: release eligibility, visibility rules, engagement filtering,
version selection, withdrawal handling, private-field exclusion,
client auth boundary, API response shape, and HTML page content.
"""

from __future__ import annotations

import os
import sqlite3
from hashlib import sha256
from queue import Queue
from pathlib import Path
from threading import Event, Thread
from typing import Callable

import pytest
from fastapi.testclient import TestClient

from src.ace.app import app
from src.ace.domain.release import ReleasePackage
from src.ace.workbench.client_release_service import (
    ClientReleaseService,
    ClientReleaseStateError,
    ClientReleaseValidationError,
)
from src.ace.workbench.storage import WorkbenchStore


# ── Helpers ─────────────────────────────────────────────────────

CLIENT_USER = "fictional-client"
CLIENT_PASS = "fictional-client-password"
CLIENT_ENG = "ENG-FIC-0001"


def _create_draft_package(
    conn: sqlite3.Connection,
    release_id: str,
    engagement_id: str,
    *,
    add_created_event: bool = True,
) -> None:
    """Create a DRAFT release package, withdrawing any existing
    PUBLISHED package for the same engagement."""
    existing = conn.execute(
        "SELECT release_id FROM client_release_packages "
        "WHERE engagement_id = ? AND status = 'PUBLISHED'",
        (engagement_id,),
    ).fetchone()
    if existing is not None and existing["release_id"] != release_id:
        conn.execute(
            "UPDATE client_release_packages "
            "SET status = 'WITHDRAWN', "
            "    withdrawn_at = '2026-08-20T00:00:00Z', "
            "    withdrawn_by = 'Test' "
            "WHERE release_id = ?",
            (existing["release_id"],),
        )
        conn.execute(
            "INSERT OR IGNORE INTO engagement_audit_events "
            "(event_id, engagement_id, event_type, recorded_at, actor) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"EVT-{existing['release_id']}-WDN", engagement_id,
             "RELEASE_WITHDRAWN", "2026-08-20T00:00:00Z", "Test"),
        )
    release_version = conn.execute(
        "SELECT COALESCE(MAX(release_version), 0) + 1 AS next_version "
        "FROM client_release_packages WHERE engagement_id = ?",
        (engagement_id,),
    ).fetchone()["next_version"]
    conn.execute(
        "INSERT OR IGNORE INTO client_release_packages "
        "(release_id, engagement_id, release_version, status, created_at,"
        " created_by) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (release_id, engagement_id, release_version, "DRAFT",
         "2026-08-20T00:00:00Z", "Test"),
    )
    if add_created_event:
        conn.execute(
            "INSERT OR IGNORE INTO engagement_audit_events "
            "(event_id, engagement_id, event_type, recorded_at, actor) "
            "VALUES (?, ?, 'RELEASE_CREATED', '2026-08-20T00:00:00Z', "
            "'Test')",
            (f"EVT-{release_id}-CREATED", engagement_id),
        )


def _publish_draft_package(
    conn: sqlite3.Connection, release_id: str, engagement_id: str
) -> None:
    """Publish a DRAFT package: insert entries first, then call this.
    The RELEASE_PUBLISHED audit event is inserted automatically by the
    client_release_packages_auto_publish_event trigger."""
    conn.execute(
        "UPDATE client_release_packages "
        "SET status = 'PUBLISHED', "
        "    published_at = '2026-08-20T00:00:00Z', "
        "    published_by = 'Test' "
        "WHERE release_id = ?",
        (release_id,),
    )


def _set_client_env(
    monkeypatch: pytest.MonkeyPatch, data_dir: Path | None = None
) -> None:
    monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
    monkeypatch.setenv("ACE_CLIENT_USERNAME", CLIENT_USER)
    monkeypatch.setenv("ACE_CLIENT_PASSWORD", CLIENT_PASS)
    monkeypatch.setenv("ACE_CLIENT_ENGAGEMENT_ID", CLIENT_ENG)
    if data_dir is not None:
        monkeypatch.setenv("ACE_DATA_DIR", str(data_dir))


def _client_auth() -> tuple[str, str]:
    return (CLIENT_USER, CLIENT_PASS)


def _auditor_auth() -> tuple[str, str]:
    return ("auditor", "fictional-password")


def _insert_approved_action(
    conn: sqlite3.Connection,
    action_id: str,
    engagement_id: str,
    description: str,
    owner: str,
    target_date: str,
    delivery_status: str,
    approved_by: str,
    approved_at: str,
) -> None:
    """Insert an APPROVED action and its ACTION_APPROVED audit event
    so the insert-time validation trigger accepts the release entry."""
    conn.execute(
        "INSERT OR IGNORE INTO approved_actions "
        "(action_id, engagement_id, version, description, owner, "
        " target_date, approval_status, delivery_status, "
        " approved_by, approved_at, created_at) "
        "VALUES (?, ?, 1, ?, ?, ?, 'APPROVED', ?, ?, ?, ?)",
        (
            action_id, engagement_id, description, owner,
            target_date, delivery_status,
            approved_by, approved_at, approved_at,
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO engagement_audit_events "
        "(event_id, engagement_id, event_type, recorded_at, actor) "
        "VALUES (?, ?, 'ACTION_APPROVED', ?, ?)",
        (
            f"EVT-{action_id}-APPROVED",
            engagement_id,
            approved_at,
            approved_by,
        ),
    )


def _insert_candidate_action(
    conn: sqlite3.Connection,
    action_id: str,
    description: str = "Candidate action",
) -> None:
    """Insert an editable candidate action."""
    conn.execute(
        "INSERT INTO approved_actions "
        "(action_id, engagement_id, version, description, owner, "
        " target_date, approval_status, delivery_status, "
        " approved_by, approved_at, created_at) "
        "VALUES (?, 'ENG-FIC-0001', 1, ?, 'Candidate Owner', "
        "'2026-12-31', 'CANDIDATE', 'OPEN', NULL, NULL, "
        "'2026-08-20T00:00:00Z')",
        (action_id, description),
    )


def _insert_approved_action_without_event(
    conn: sqlite3.Connection,
    action_id: str,
    engagement_id: str,
    description: str,
    owner: str,
    target_date: str,
    delivery_status: str,
    approved_by: str | None,
    approved_at: str | None,
) -> None:
    """Insert an APPROVED action WITHOUT its ACTION_APPROVED audit
    event, using a plain INSERT and a fixed created_at.

    Lets a test forge a missing or mismatched audit event (or a
    NULL/blank/whitespace attribution) so the insert-time ACTION
    validation trigger can be exercised in isolation."""
    conn.execute(
        "INSERT INTO approved_actions "
        "(action_id, engagement_id, version, description, owner, "
        " target_date, approval_status, delivery_status, "
        " approved_by, approved_at, created_at) "
        "VALUES (?, ?, 1, ?, ?, ?, 'APPROVED', ?, ?, ?, ?)",
        (
            action_id, engagement_id, description, owner,
            target_date, delivery_status,
            approved_by, approved_at, "2026-08-20T00:00:00Z",
        ),
    )


def _insert_action_audit_event(
    conn: sqlite3.Connection,
    event_id: str,
    engagement_id: str,
    event_type: str,
    recorded_at: str,
    actor: str,
) -> None:
    """Insert an engagement audit event with explicit values using a
    plain INSERT, so a test can forge a single mismatched attribute
    (event_id, engagement_id, event_type, actor or recorded_at)."""
    conn.execute(
        "INSERT INTO engagement_audit_events "
        "(event_id, engagement_id, event_type, recorded_at, actor) "
        "VALUES (?, ?, ?, ?, ?)",
        (event_id, engagement_id, event_type, recorded_at, actor),
    )


def _insert_action_release_entry(
    conn: sqlite3.Connection,
    release_entry_id: str,
    release_id: str,
    action_id: str,
    *,
    display_title: str = "Action Entry",
    display_summary: str = "desc",
    action_owner: str = "Owner",
    action_target_date: str = "2026-12-31",
    action_delivery_status: str = "OPEN",
    evidence_ref: str = "EVD-FIC-0001",
    version: int = 1,
) -> None:
    """Insert an ACTION release entry using a plain INSERT (not INSERT
    OR IGNORE) so a validation failure raises rather than being
    silently skipped."""
    conn.execute(
        "INSERT INTO client_release_entries "
        "(release_entry_id, release_id, source_record_type, "
        " source_record_id, source_record_version, "
        " approved_evidence_reference_id, display_title, "
        " display_summary, action_owner, action_target_date, "
        " action_delivery_status) "
        "VALUES (?, ?, 'ACTION', ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            release_entry_id, release_id, action_id, version,
            evidence_ref, display_title, display_summary,
            action_owner, action_target_date, action_delivery_status,
        ),
    )


def _insert_legacy_conclusion_release_entry(
    conn: sqlite3.Connection,
    release_entry_id: str,
    release_id: str,
    conclusion_id: str,
    *,
    title: str = "Approved field capture conclusion",
    summary: str = (
        "The field capture control is suitably designed for "
        "fictional mobile evidence collection under the pilot scope."
    ),
    evidence_id: str = "EVD-FIC-0001",
    version: int = 1,
) -> None:
    """Insert a Phase 6A-style conclusion entry after a test disables
    its insert-time trigger.  This simulates a DRAFT entry copied by
    upgrade before the Phase 6B1 source checks existed."""
    conn.execute(
        "INSERT INTO client_release_entries "
        "(release_entry_id, release_id, source_record_type, "
        " source_record_id, source_record_version, "
        " approved_evidence_reference_id, display_title, "
        " display_summary) "
        "VALUES (?, ?, 'CONCLUSION', ?, ?, ?, ?, ?)",
        (
            release_entry_id, release_id, conclusion_id, version,
            evidence_id, title, summary,
        ),
    )


def _build_phase6a_release_database(data_dir: Path) -> dict[str, object]:
    """Build a fictional database with the real pre-6B1 release schema."""
    store = WorkbenchStore(data_dir=data_dir)
    with store.connect() as conn:
        for trigger_name in (
            "client_release_packages_require_draft_insert",
            "client_release_packages_no_update",
            "client_release_packages_no_delete",
            "client_release_packages_validate_publish",
            "client_release_packages_auto_publish_event",
            "client_release_entries_no_update",
            "client_release_entries_no_delete",
            "client_release_entries_no_insert_after_publish",
            "client_release_entries_no_terminal_insert",
            "client_release_entries_validate_action_source",
            "client_release_entries_validate_conclusion_source",
            "client_release_entries_one_conclusion",
            "conclusions_no_update_after_approval",
            "conclusions_no_delete_after_approval",
            "engagement_audit_events_no_update",
            "engagement_audit_events_no_delete",
        ):
            conn.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
        conn.execute(
            "UPDATE conclusions SET title = ? "
            "WHERE conclusion_id = 'CON-FIC-0001' "
            "AND status = 'APPROVED'",
            ("Fictional approved field conclusion",),
        )
        conn.execute("DROP TABLE client_release_entries")
        conn.execute("DELETE FROM client_release_packages")
        conn.execute("DROP TABLE approved_actions")
        conn.execute("DROP TABLE engagement_audit_events")
        conn.execute(
            """
            CREATE TABLE client_release_entries (
                release_entry_id TEXT PRIMARY KEY,
                release_id TEXT NOT NULL
                    REFERENCES client_release_packages(release_id),
                source_record_type TEXT NOT NULL
                    CHECK (source_record_type IN ('CONCLUSION')),
                source_record_id TEXT NOT NULL,
                source_record_version INTEGER NOT NULL,
                approved_evidence_reference_id TEXT NOT NULL,
                display_title TEXT NOT NULL,
                display_summary TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE engagement_audit_events (
                event_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL
                    REFERENCES engagement_setups(engagement_id),
                event_type TEXT NOT NULL CHECK (
                    event_type IN ('ENGAGEMENT_CREATED', 'ENGAGEMENT_ACTIVATED',
                                   'CONCLUSION_APPROVED', 'RELEASE_CREATED',
                                   'RELEASE_PUBLISHED', 'RELEASE_WITHDRAWN')
                ),
                recorded_at TEXT NOT NULL,
                actor TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO client_release_packages "
            "(release_id, engagement_id, release_version, status, created_at, "
            " created_by, published_at, published_by) "
            "VALUES ('REL-FIC-PUBLISHED', 'ENG-FIC-0001', 2, 'PUBLISHED', "
            "'2026-08-19T09:30:00Z', 'Fictional Site Auditor', "
            "'2026-08-19T10:00:00Z', 'Fictional Site Auditor')"
        )
        conn.execute(
            "INSERT INTO client_release_packages "
            "(release_id, engagement_id, release_version, status, created_at, "
            " created_by, published_at, published_by, withdrawn_at, "
            " withdrawn_by, withdrawal_reason) "
            "VALUES ('REL-FIC-WITHDRAWN', 'ENG-FIC-0001', 1, "
            "'WITHDRAWN', '2026-08-19T08:00:00Z', "
            "'Fictional Site Auditor', '2026-08-19T08:30:00Z', "
            "'Fictional Site Auditor', '2026-08-19T09:00:00Z', "
            "'Fictional Site Auditor', 'Superseded by updated release')"
        )
        entry_values = (
            "CONCLUSION", "CON-FIC-0001", 1, "EVD-FIC-0001",
            "Approved field capture conclusion",
            "The field capture control is suitably designed for "
            "fictional mobile evidence collection under the pilot scope.",
        )
        conn.execute(
            "INSERT INTO client_release_entries VALUES "
            "('RLE-FIC-PUB-1', 'REL-FIC-PUBLISHED', "
            "?, ?, ?, ?, ?, ?)",
            entry_values,
        )
        conn.execute(
            "INSERT INTO client_release_entries VALUES "
            "('RLE-FIC-WDN-1', 'REL-FIC-WITHDRAWN', "
            "?, ?, ?, ?, ?, ?)",
            entry_values,
        )
        audit_rows = (
            (
                "EVT-CON-FIC-0001-APPROVED", "ENG-FIC-0001",
                "CONCLUSION_APPROVED", "2026-08-19T10:00:00Z",
                "Fictional Site Auditor",
            ),
            (
                "EVT-REL-FIC-PUB-CREATED", "ENG-FIC-0001",
                "RELEASE_CREATED", "2026-08-19T09:30:00Z",
                "Fictional Site Auditor",
            ),
            (
                "EVT-REL-FIC-PUB-PUBLISHED", "ENG-FIC-0001",
                "RELEASE_PUBLISHED", "2026-08-19T10:00:00Z",
                "Fictional Site Auditor",
            ),
            (
                "EVT-REL-FIC-WDN-CREATED", "ENG-FIC-0001",
                "RELEASE_CREATED", "2026-08-19T08:00:00Z",
                "Fictional Site Auditor",
            ),
            (
                "EVT-REL-FIC-WDN-PUBLISHED", "ENG-FIC-0001",
                "RELEASE_PUBLISHED", "2026-08-19T08:30:00Z",
                "Fictional Site Auditor",
            ),
            (
                "EVT-REL-FIC-WDN-WITHDRAWN", "ENG-FIC-0001",
                "RELEASE_WITHDRAWN", "2026-08-19T09:00:00Z",
                "Fictional Site Auditor",
            ),
        )
        conn.executemany(
            "INSERT INTO engagement_audit_events "
            "(event_id, engagement_id, event_type, recorded_at, actor) "
            "VALUES (?, ?, ?, ?, ?)",
            audit_rows,
        )
        legacy_package = tuple(conn.execute(
            "SELECT * FROM client_release_packages "
            "WHERE release_id = 'REL-FIC-PUBLISHED'"
        ).fetchone())
        legacy_entries = [
            tuple(row) for row in conn.execute(
                "SELECT * FROM client_release_entries "
                "WHERE release_id = 'REL-FIC-PUBLISHED' "
                "ORDER BY release_entry_id"
            ).fetchall()
        ]
        withdrawn_package = tuple(conn.execute(
            "SELECT * FROM client_release_packages "
            "WHERE release_id = 'REL-FIC-WITHDRAWN'"
        ).fetchone())
        withdrawn_entries = [
            tuple(row) for row in conn.execute(
                "SELECT * FROM client_release_entries "
                "WHERE release_id = 'REL-FIC-WITHDRAWN' "
                "ORDER BY release_entry_id"
            ).fetchall()
        ]
    return {
        "legacy_package": legacy_package,
        "legacy_entries": legacy_entries,
        "withdrawn_package": withdrawn_package,
        "withdrawn_entries": withdrawn_entries,
    }


# An old-style ACTION validation trigger that predates the Phase 6B1
# snapshot + audit-event checks: it only verifies the source action
# exists, is APPROVED, and matches the captured version.  Used to
# simulate a database created before the new rules so upgrade tests
# can assert the triggers are replaced.
_OLD_STYLE_ACTION_TRIGGER_SQL = """
CREATE TRIGGER client_release_entries_validate_action_source
BEFORE INSERT ON client_release_entries
WHEN NEW.source_record_type = 'ACTION'
BEGIN
    SELECT RAISE(ABORT,
        'Source action must be an APPROVED action for this engagement at the captured version')
    WHERE NOT EXISTS (
        SELECT 1 FROM approved_actions a
        WHERE a.action_id = NEW.source_record_id
          AND a.engagement_id = (
              SELECT engagement_id FROM client_release_packages
              WHERE release_id = NEW.release_id)
          AND a.approval_status = 'APPROVED'
          AND a.version = NEW.source_record_version
    );
END
"""


_FINAL_RELEASE_TRIGGER_INVENTORY = (
    ("approved_actions_no_delete_after_approval", "approved_actions"),
    ("approved_actions_no_update_after_approval", "approved_actions"),
    ("client_release_entries_no_delete", "client_release_entries"),
    ("client_release_entries_no_terminal_insert", "client_release_entries"),
    ("client_release_entries_no_update", "client_release_entries"),
    ("client_release_entries_one_action_source", "client_release_entries"),
    ("client_release_entries_one_conclusion", "client_release_entries"),
    ("client_release_entries_validate_action_source", "client_release_entries"),
    ("client_release_entries_validate_conclusion_source", "client_release_entries"),
    ("client_release_packages_auto_publish_event", "client_release_packages"),
    ("client_release_packages_no_delete", "client_release_packages"),
    ("client_release_packages_no_update", "client_release_packages"),
    ("client_release_packages_require_draft_insert", "client_release_packages"),
    ("client_release_packages_validate_publish", "client_release_packages"),
    ("conclusions_no_delete_after_approval", "conclusions"),
    ("conclusions_no_update_after_approval", "conclusions"),
    ("engagement_audit_events_no_delete", "engagement_audit_events"),
    ("engagement_audit_events_no_update", "engagement_audit_events"),
)


def _audit_event_snapshot(
    connection: sqlite3.Connection,
) -> list[tuple[object, ...]]:
    """Return every persisted audit-event column in deterministic order."""
    return [
        tuple(row)
        for row in connection.execute(
            """
            SELECT event_id, engagement_id, event_type, recorded_at, actor
            FROM engagement_audit_events
            ORDER BY event_id
            """
        ).fetchall()
    ]


def _client_release_read_snapshot(
    connection: sqlite3.Connection, engagement_id: str
) -> dict[str, list[tuple[object, ...]]]:
    """Return relevant full rows before or after one client release read."""
    return {
        "packages": [
            tuple(row)
            for row in connection.execute(
                "SELECT * FROM client_release_packages "
                "WHERE engagement_id = ? "
                "ORDER BY release_version, release_id",
                (engagement_id,),
            ).fetchall()
        ],
        "entries": [
            tuple(row)
            for row in connection.execute(
                """
                SELECT entry.* FROM client_release_entries AS entry
                JOIN client_release_packages AS package
                  ON package.release_id = entry.release_id
                WHERE package.engagement_id = ?
                ORDER BY entry.release_id, entry.release_entry_id
                """,
                (engagement_id,),
            ).fetchall()
        ],
        "conclusion_sources": [
            tuple(row)
            for row in connection.execute(
                "SELECT * FROM conclusions WHERE engagement_id = ? "
                "ORDER BY conclusion_id, version",
                (engagement_id,),
            ).fetchall()
        ],
        "action_sources": [
            tuple(row)
            for row in connection.execute(
                "SELECT * FROM approved_actions WHERE engagement_id = ? "
                "ORDER BY action_id, version",
                (engagement_id,),
            ).fetchall()
        ],
        "audit_events": [
            tuple(row)
            for row in connection.execute(
                "SELECT * FROM engagement_audit_events WHERE engagement_id = ? "
                "ORDER BY event_id",
                (engagement_id,),
            ).fetchall()
        ],
    }


def _assert_final_release_trigger_inventory(
    connection: sqlite3.Connection,
) -> list[tuple[object, ...]]:
    """Assert the final inventory and return its immutable audit snapshot.

    The query deliberately includes every trigger attached to release source,
    package, entry, and audit tables plus every ``client_release_`` trigger,
    so an unexpected trigger cannot be hidden by filtering to expected names.
    """
    rows = connection.execute(
        """
        SELECT name, tbl_name, sql FROM sqlite_master
        WHERE type = 'trigger'
          AND (
              tbl_name IN (
                  'approved_actions', 'client_release_entries',
                  'client_release_packages', 'conclusions',
                  'engagement_audit_events'
              )
              OR name LIKE 'client_release_%'
          )
        ORDER BY name
        """
    ).fetchall()
    assert [(row["name"], row["tbl_name"]) for row in rows] == list(
        _FINAL_RELEASE_TRIGGER_INVENTORY
    )
    assert all("_old" not in row["sql"] for row in rows)
    return _audit_event_snapshot(connection)


# ── Unit: release eligibility (direct store, no HTTP) ──────────

class TestReleaseEligibility:

    def test_candidate_conclusion_not_in_published_package(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-cand")
        store = WorkbenchStore()
        with store.connect() as conn:
            entry = conn.execute(
                "SELECT * FROM client_release_entries "
                "WHERE release_id = 'REL-FIC-PUBLISHED' "
                "AND source_record_id = 'CON-FIC-STALE'"
            ).fetchone()
            assert entry is None, "CANDIDATE must not appear in published package"

    def test_published_package_references_approved_conclusion(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-pub")
        store = WorkbenchStore()
        with store.connect() as conn:
            entry = conn.execute(
                "SELECT * FROM client_release_entries "
                "WHERE release_id = 'REL-FIC-PUBLISHED' "
                "AND source_record_id = 'CON-FIC-0001' "
                "AND source_record_version = 1"
            ).fetchone()
            assert entry is not None
            assert entry["display_title"] == "Approved field capture conclusion"
            assert entry["approved_evidence_reference_id"] == "EVD-FIC-0001"

    def test_release_package_is_immutable(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-imm")
        store = WorkbenchStore()
        with store.connect() as conn:
            with pytest.raises(Exception):
                conn.execute(
                    "UPDATE client_release_packages SET status = 'PUBLISHED' "
                    "WHERE release_id = 'REL-FIC-DRAFT'"
                )
                conn.commit()

    def test_published_to_withdrawn_transition_allowed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The trigger allows PUBLISHED → WITHDRAWN with only withdrawn fields changed."""
        _set_client_env(monkeypatch, tmp_path / "u-wdtrans")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                """
                UPDATE client_release_packages SET
                    status = 'WITHDRAWN',
                    withdrawn_at = '2026-08-20T00:00:00Z',
                    withdrawn_by = 'Fictional Admin',
                    withdrawal_reason = 'Content correction required'
                WHERE release_id = 'REL-FIC-PUBLISHED'
                """
            )
            conn.commit()
            row = conn.execute(
                "SELECT status, withdrawn_at FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            ).fetchone()
            assert row["status"] == "WITHDRAWN"
            assert row["withdrawn_at"] == "2026-08-20T00:00:00Z"

    def test_withdrawn_transition_blocks_content_changes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """PUBLISHED → WITHDRAWN must not change release content (e.g., release_version)."""
        _set_client_env(monkeypatch, tmp_path / "u-wdblock")
        store = WorkbenchStore()
        with store.connect() as conn:
            with pytest.raises(Exception):
                conn.execute(
                    """
                    UPDATE client_release_packages SET
                        status = 'WITHDRAWN',
                        release_version = 99,
                        withdrawn_at = '2026-08-20T00:00:00Z',
                        withdrawn_by = 'Fictional Admin'
                    WHERE release_id = 'REL-FIC-PUBLISHED'
                    """
                )
                conn.commit()

    def test_source_change_does_not_alter_published_content(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-src")
        store = WorkbenchStore()
        with store.connect() as conn:
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Approved conclusions cannot be updated",
            ):
                conn.execute(
                    "UPDATE conclusions SET summary = ? "
                    "WHERE conclusion_id = 'CON-FIC-0001' AND version = 1",
                    ("Modified summary",),
                )
            entry = conn.execute(
                "SELECT display_summary FROM client_release_entries "
                "WHERE release_id = 'REL-FIC-PUBLISHED' "
                "AND source_record_type = 'CONCLUSION'"
            ).fetchone()
            assert "field capture control is suitably designed" in entry["display_summary"]
            assert "Modified summary" not in entry["display_summary"]

    def test_withdrawn_package_is_not_current(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-wd")
        store = WorkbenchStore()
        with store.connect() as conn:
            pub = conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE engagement_id = 'ENG-FIC-0001' AND status = 'PUBLISHED' "
                "ORDER BY release_version DESC LIMIT 1"
            ).fetchone()
            assert pub is not None
            assert pub["status"] == "PUBLISHED"
            assert pub["release_id"] != "REL-FIC-WITHDRAWN"

    def test_only_one_current_package(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-one")
        store = WorkbenchStore()
        with store.connect() as conn:
            pubs = conn.execute(
                "SELECT COUNT(*) AS cnt FROM client_release_packages "
                "WHERE engagement_id = 'ENG-FIC-0001' AND status = 'PUBLISHED'"
            ).fetchone()
            assert pubs["cnt"] == 1

    def test_fresh_seed_versions_are_positive_integers_and_unique(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "seed-versions")
        with store.connect() as conn:
            rows = conn.execute(
                "SELECT engagement_id, release_id, release_version, "
                "typeof(release_version) AS kind FROM client_release_packages"
            ).fetchall()
        versions_by_engagement: dict[str, list[int]] = {}
        for row in rows:
            assert row["kind"] == "integer"
            assert row["release_version"] > 0
            versions_by_engagement.setdefault(row["engagement_id"], []).append(
                row["release_version"]
            )
        assert all(
            len(versions) == len(set(versions))
            for versions in versions_by_engagement.values()
        )
        assert {
            row["release_id"]: row["release_version"]
            for row in rows
            if row["engagement_id"] == "ENG-FIC-0001"
        } == {
            "REL-FIC-DRAFT": 3,
            "REL-FIC-PUBLISHED": 2,
            "REL-FIC-WITHDRAWN": 1,
        }

    def test_fresh_schema_requires_positive_integer_release_versions(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "release-version-check")
        with store.connect() as conn:
            table_sql = conn.execute(
                "SELECT sql FROM sqlite_master "
                "WHERE type = 'table' AND name = 'client_release_packages'"
            ).fetchone()["sql"]
        assert "typeof(release_version) = 'integer'" in table_sql
        assert "release_version > 0" in table_sql


class TestClientReleaseServiceBoundary:
    """Characterise the Stage 1 service facade over existing release history."""

    def test_build_next_draft_selects_the_next_version_and_audits(
        self, tmp_path: Path
    ) -> None:
        """Workflow ownership includes version selection and creation audit history."""
        store = WorkbenchStore(data_dir=tmp_path / "service-next-draft")
        service = ClientReleaseService()
        with store.connect() as connection:
            service.begin_release_write(connection)
            draft = service.build_next_draft(
                connection,
                release_id="REL-FIC-SERVICE-NEXT",
                engagement_id="ENG-FIC-0001",
                created_at="2026-08-21T00:00:00Z",
                created_by="Test",
            )
            event = connection.execute(
                "SELECT engagement_id, event_type, recorded_at, actor "
                "FROM engagement_audit_events WHERE event_id = ?",
                ("EVT-REL-FIC-SERVICE-NEXT-CREATED",),
            ).fetchone()

            assert connection.in_transaction
            assert draft.release_version == 4
            assert event is not None
            assert tuple(event) == (
                "ENG-FIC-0001",
                "RELEASE_CREATED",
                "2026-08-21T00:00:00Z",
                "Test",
            )
            connection.rollback()

    def test_build_next_draft_requires_the_caller_transaction(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(
            data_dir=tmp_path / "service-next-draft-no-transaction"
        )
        service = ClientReleaseService()
        with store.connect() as connection:
            with pytest.raises(
                ClientReleaseStateError, match="active caller transaction"
            ):
                service.build_next_draft(
                    connection,
                    release_id="REL-FIC-SERVICE-NEXT-NO-TX",
                    engagement_id="ENG-FIC-0001",
                    created_at="2026-08-21T00:00:00Z",
                    created_by="Test",
                )
            assert (
                service._storage.release_package(
                    connection, "REL-FIC-SERVICE-NEXT-NO-TX"
                )
                is None
            )

    def test_begin_release_write_requires_a_fresh_caller_transaction(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-begin-release-write")
        service = ClientReleaseService()
        with store.connect() as connection:
            service.begin_release_write(connection)
            assert connection.in_transaction
            with pytest.raises(ClientReleaseStateError, match="begin before"):
                service.begin_release_write(connection)
            connection.rollback()

    def test_build_next_draft_rejects_an_unknown_engagement(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-next-draft-missing-engagement")
        service = ClientReleaseService()
        with store.connect() as connection:
            service.begin_release_write(connection)
            with pytest.raises(ClientReleaseValidationError, match="engagement not found"):
                service.build_next_draft(
                    connection,
                    release_id="REL-FIC-SERVICE-MISSING-ENGAGEMENT",
                    engagement_id="ENG-FIC-MISSING",
                    created_at="2026-08-21T00:00:00Z",
                    created_by="Test",
                )
            assert connection.in_transaction
            connection.rollback()

    def test_build_next_draft_serialises_independent_callers(
        self, tmp_path: Path
    ) -> None:
        """Two immediate callers must serialise before version allocation reads."""
        store = WorkbenchStore(data_dir=tmp_path / "service-next-draft-concurrency")
        with store.connect():
            pass

        first_built = Event()
        release_first = Event()
        second_attempting = Event()
        second_finished = Event()
        outcomes: Queue[tuple[str, object]] = Queue()

        def open_connection() -> sqlite3.Connection:
            connection = sqlite3.connect(store.database_path, timeout=2)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA recursive_triggers = ON")
            connection.execute("PRAGMA busy_timeout = 2000")
            return connection

        def build_first() -> None:
            connection = open_connection()
            try:
                service = ClientReleaseService()
                service.begin_release_write(connection)
                draft = service.build_next_draft(
                    connection,
                    release_id="REL-FIC-CONCURRENT-FIRST",
                    engagement_id="ENG-FIC-0001",
                    created_at="2026-08-21T00:00:00Z",
                    created_by="First",
                )
                outcomes.put(("first", (draft.release_version, connection.in_transaction)))
                first_built.set()
                assert release_first.wait(timeout=2)
                connection.commit()
            except BaseException as error:
                outcomes.put(("first-error", error))
                first_built.set()
            finally:
                connection.close()

        def build_second() -> None:
            connection = open_connection()
            try:
                second_attempting.set()
                service = ClientReleaseService()
                service.begin_release_write(connection)
                draft = service.build_next_draft(
                    connection,
                    release_id="REL-FIC-CONCURRENT-SECOND",
                    engagement_id="ENG-FIC-0001",
                    created_at="2026-08-21T00:01:00Z",
                    created_by="Second",
                )
                outcomes.put(("second", (draft.release_version, connection.in_transaction)))
                connection.commit()
            except BaseException as error:
                outcomes.put(("second-error", error))
            finally:
                second_finished.set()
                connection.close()

        first = Thread(target=build_first)
        second = Thread(target=build_second)
        first.start()
        assert first_built.wait(timeout=2)
        second.start()
        assert second_attempting.wait(timeout=2)
        assert not second_finished.wait(timeout=0.1)
        release_first.set()
        first.join(timeout=3)
        second.join(timeout=3)

        assert not first.is_alive()
        assert not second.is_alive()
        results = dict(outcomes.queue)
        assert not {name: value for name, value in results.items() if name.endswith("-error")}
        assert results == {"first": (4, True), "second": (5, True)}
        with store.connect() as connection:
            events = connection.execute(
                "SELECT event_id, event_type FROM engagement_audit_events "
                "WHERE event_id IN (?, ?) ORDER BY event_id",
                (
                    "EVT-REL-FIC-CONCURRENT-FIRST-CREATED",
                    "EVT-REL-FIC-CONCURRENT-SECOND-CREATED",
                ),
            ).fetchall()
        assert [tuple(event) for event in events] == [
            ("EVT-REL-FIC-CONCURRENT-FIRST-CREATED", "RELEASE_CREATED"),
            ("EVT-REL-FIC-CONCURRENT-SECOND-CREATED", "RELEASE_CREATED"),
        ]

    def test_next_draft_lifecycle_keeps_exact_audit_and_history_deltas(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-next-draft-lifecycle")
        service = ClientReleaseService()
        release_id = "REL-FIC-NEXT-LIFECYCLE"
        with store.connect() as connection:
            service.begin_release_write(connection)
            def package_rows() -> dict[str, tuple[object, ...]]:
                return {
                    row["release_id"]: tuple(row)
                    for row in connection.execute(
                        "SELECT * FROM client_release_packages "
                        "WHERE engagement_id = ? ORDER BY release_version",
                        ("ENG-FIC-0001",),
                    ).fetchall()
                }

            def audit_rows() -> list[tuple[object, ...]]:
                return [
                    tuple(row)
                    for row in connection.execute(
                        "SELECT event_id, engagement_id, event_type, recorded_at, actor "
                        "FROM engagement_audit_events WHERE engagement_id = ? "
                        "ORDER BY event_id",
                        ("ENG-FIC-0001",),
                    ).fetchall()
                ]

            def assert_one_event_added(
                before: list[tuple[object, ...]], expected: tuple[object, ...]
            ) -> list[tuple[object, ...]]:
                after = audit_rows()
                assert len(after) == len(before) + 1
                assert set(after) - set(before) == {expected}
                assert set(before) - set(after) == set()
                return after

            before_packages = package_rows()
            before_events = audit_rows()
            before_history = service.get_release_history(connection, "ENG-FIC-0001")
            draft = service.build_next_draft(
                connection,
                release_id=release_id,
                engagement_id="ENG-FIC-0001",
                created_at="2026-08-21T00:00:00Z",
                created_by="Test",
            )
            assert connection.in_transaction
            assert draft.status == "DRAFT"
            created_event = (
                f"EVT-{release_id}-CREATED",
                "ENG-FIC-0001",
                "RELEASE_CREATED",
                "2026-08-21T00:00:00Z",
                "Test",
            )
            expected_draft = (
                release_id,
                "ENG-FIC-0001",
                4,
                "DRAFT",
                "2026-08-21T00:00:00Z",
                "Test",
                None,
                None,
                None,
                None,
                None,
            )
            assert package_rows() == {**before_packages, release_id: expected_draft}
            after_draft_events = assert_one_event_added(before_events, created_event)
            current = service.get_current_release(connection, "ENG-FIC-0001")
            history = service.get_release_history(connection, "ENG-FIC-0001")
            assert current is not None and current.package["release_id"] == "REL-FIC-PUBLISHED"
            assert [(row.release_id, row.status) for row in history] == [
                (release_id, "DRAFT"),
                *[(row.release_id, row.status) for row in before_history],
            ]

            source_entry = connection.execute(
                """
                SELECT * FROM client_release_entries
                WHERE release_id = 'REL-FIC-PUBLISHED'
                AND source_record_type = 'ACTION'
                ORDER BY release_entry_id LIMIT 1
                """
            ).fetchone()
            service.withdraw_release(
                connection,
                "REL-FIC-PUBLISHED",
                "2026-08-20T23:00:00Z",
                "Test",
                "Superseded by lifecycle test release",
            )
            assert service.get_current_release(connection, "ENG-FIC-0001") is None
            expected_prior_published = list(before_packages["REL-FIC-PUBLISHED"])
            expected_prior_published[3] = "WITHDRAWN"
            expected_prior_published[8:] = [
                "2026-08-20T23:00:00Z",
                "Test",
                "Superseded by lifecycle test release",
            ]
            after_prior_withdrawal_packages = {
                **before_packages,
                release_id: expected_draft,
                "REL-FIC-PUBLISHED": tuple(expected_prior_published),
            }
            assert package_rows() == after_prior_withdrawal_packages
            prior_withdrawal_event = (
                "EVT-REL-FIC-PUBLISHED-WDN",
                "ENG-FIC-0001",
                "RELEASE_WITHDRAWN",
                "2026-08-20T23:00:00Z",
                "Test",
            )
            after_prior_withdrawal_events = assert_one_event_added(
                after_draft_events, prior_withdrawal_event
            )
            _insert_action_release_entry(
                connection,
                "RLE-FIC-NEXT-LIFECYCLE",
                release_id,
                source_entry["source_record_id"],
                display_title=source_entry["display_title"],
                display_summary=source_entry["display_summary"],
                action_owner=source_entry["action_owner"],
                action_target_date=source_entry["action_target_date"],
                action_delivery_status=source_entry["action_delivery_status"],
                evidence_ref=source_entry["approved_evidence_reference_id"],
                version=source_entry["source_record_version"],
            )
            assert package_rows() == after_prior_withdrawal_packages
            assert audit_rows() == after_prior_withdrawal_events
            published = service.publish_release(
                connection, release_id, "2026-08-21T01:00:00Z", "Test"
            )
            current = service.get_current_release(connection, "ENG-FIC-0001")
            assert connection.in_transaction
            assert published.status == "PUBLISHED"
            assert current is not None and current.package["release_id"] == release_id
            expected_published = list(expected_draft)
            expected_published[3] = "PUBLISHED"
            expected_published[6:8] = ["2026-08-21T01:00:00Z", "Test"]
            assert package_rows() == {
                **after_prior_withdrawal_packages,
                release_id: tuple(expected_published),
            }
            published_event = (
                f"EVT-{release_id}-PUB",
                "ENG-FIC-0001",
                "RELEASE_PUBLISHED",
                "2026-08-21T01:00:00Z",
                "Test",
            )
            after_publication_events = assert_one_event_added(
                after_prior_withdrawal_events, published_event
            )
            assert [
                (row.release_id, row.status)
                for row in service.get_release_history(connection, "ENG-FIC-0001")
            ] == [
                (release_id, "PUBLISHED"),
                ("REL-FIC-DRAFT", "DRAFT"),
                ("REL-FIC-PUBLISHED", "WITHDRAWN"),
                ("REL-FIC-WITHDRAWN", "WITHDRAWN"),
            ]

            withdrawn = service.withdraw_release(
                connection,
                release_id,
                "2026-08-21T02:00:00Z",
                "Test",
                "Fictional correction",
            )
            assert connection.in_transaction
            assert withdrawn.status == "WITHDRAWN"
            assert service.get_current_release(connection, "ENG-FIC-0001") is None
            expected_withdrawn = list(expected_published)
            expected_withdrawn[3] = "WITHDRAWN"
            expected_withdrawn[8:] = [
                "2026-08-21T02:00:00Z", "Test", "Fictional correction"
            ]
            assert package_rows() == {
                **after_prior_withdrawal_packages,
                release_id: tuple(expected_withdrawn),
            }
            withdrawn_event = (
                f"EVT-{release_id}-WDN",
                "ENG-FIC-0001",
                "RELEASE_WITHDRAWN",
                "2026-08-21T02:00:00Z",
                "Test",
            )
            assert_one_event_added(after_publication_events, withdrawn_event)
            assert [
                (row.release_id, row.status)
                for row in service.get_release_history(connection, "ENG-FIC-0001")
            ] == [
                (release_id, "WITHDRAWN"),
                ("REL-FIC-DRAFT", "DRAFT"),
                ("REL-FIC-PUBLISHED", "WITHDRAWN"),
                ("REL-FIC-WITHDRAWN", "WITHDRAWN"),
            ]
            connection.rollback()

    def test_service_reads_engagement_on_the_supplied_connection(
        self, tmp_path: Path
    ) -> None:
        """Routes need engagement metadata without issuing release SQL themselves."""
        store = WorkbenchStore(data_dir=tmp_path / "service-engagement-reader")
        service = ClientReleaseService()
        with store.connect() as connection:
            engagement = service.get_engagement(connection, "ENG-FIC-0001")

        assert engagement == {
            "title": "Fictional Mobile Field Capture Engagement",
            "state": "READY_FOR_CAPTURE",
            "is_fictional": 1,
            "data_classification": "FICTIONAL",
        }

    def test_build_next_draft_reserves_null_id_legacy_history_versions(
        self, tmp_path: Path
    ) -> None:
        """A supported legacy row reserves its version even without a package ID."""
        data_dir = tmp_path / "service-next-draft-legacy-history"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as connection:
            connection.execute(
                """
                INSERT INTO client_release_packages
                (release_id, engagement_id, release_version, status, created_at, created_by)
                VALUES (NULL, 'ENG-FIC-0001', 3, 'DRAFT',
                        '2026-08-19T09:15:00Z', 'Fictional Site Auditor')
                """
            )

        service = ClientReleaseService()
        with WorkbenchStore(data_dir=data_dir).connect() as connection:
            service.begin_release_write(connection)
            draft = service.build_next_draft(
                connection,
                release_id="REL-FIC-LEGACY-NEXT",
                engagement_id="ENG-FIC-0001",
                created_at="2026-08-21T00:00:00Z",
                created_by="Test",
            )
            connection.rollback()

        assert draft.release_version == 5

    def test_current_release_and_history_use_the_active_connection(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-boundary")
        service = ClientReleaseService()
        with store.connect() as connection:
            current = service.get_current_release(connection, "ENG-FIC-0001")
            history = service.get_release_history(connection, "ENG-FIC-0001")

        assert current is not None
        assert current.package["release_id"] == "REL-FIC-PUBLISHED"
        assert current.package["status"] == "PUBLISHED"
        assert any(entry["source_record_type"] == "ACTION" for entry in current.entries)
        assert [package.release_version for package in history] == [3, 2, 1]
        assert [package.status for package in history] == [
            "DRAFT",
            "PUBLISHED",
            "WITHDRAWN",
        ]

    def test_history_preserves_supported_null_legacy_release_id(
        self, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "service-history-phase6a-null-id"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as connection:
            connection.execute(
                """
                INSERT INTO client_release_packages
                (release_id, engagement_id, release_version, status, created_at, created_by)
                VALUES (NULL, 'ENG-FIC-0001', 3, 'DRAFT',
                        '2026-08-19T09:15:00Z', 'Fictional Site Auditor')
                """
            )

        service = ClientReleaseService()
        with WorkbenchStore(data_dir=data_dir).connect() as connection:
            history = service.get_release_history(connection, "ENG-FIC-0001")

        assert [(package.release_id, package.release_version) for package in history] == [
            ("REL-FIC-PHASE6B1-UPGRADE", 4),
            (None, 3),
            ("REL-FIC-PUBLISHED", 2),
            ("REL-FIC-WITHDRAWN", 1),
        ]
        assert history[1].status == "DRAFT"
        assert history[0].created_by == "Fictional Site Auditor"

    def test_lifecycle_facade_preserves_trigger_enforced_transitions(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-lifecycle")
        service = ClientReleaseService()
        package = ReleasePackage(
            release_id="REL-FIC-SERVICE-BOUNDARY",
            engagement_id="ENG-FIC-0001",
            release_version=4,
            status="DRAFT",
            created_at="2026-08-21T00:00:00Z",
            created_by="Test",
        )
        with store.connect() as connection:
            connection.execute("BEGIN")
            service.withdraw_release(
                connection,
                "REL-FIC-PUBLISHED",
                "2026-08-20T23:00:00Z",
                "Test",
                "Superseded by fictional service-boundary release",
            )
            service.build_draft(connection, package)
            with pytest.raises(ClientReleaseValidationError):
                service.validate_release(connection, package.release_id)
            source_entry = connection.execute(
                """
                SELECT * FROM client_release_entries
                WHERE release_id = 'REL-FIC-PUBLISHED'
                AND source_record_type = 'ACTION'
                ORDER BY release_entry_id LIMIT 1
                """
            ).fetchone()
            _insert_action_release_entry(
                connection,
                "RLE-FIC-SERVICE-BOUNDARY",
                package.release_id,
                source_entry["source_record_id"],
                display_title=source_entry["display_title"],
                display_summary=source_entry["display_summary"],
                action_owner=source_entry["action_owner"],
                action_target_date=source_entry["action_target_date"],
                action_delivery_status=source_entry["action_delivery_status"],
                evidence_ref=source_entry["approved_evidence_reference_id"],
                version=source_entry["source_record_version"],
            )
            published = service.publish_release(
                connection,
                package.release_id,
                "2026-08-21T01:00:00Z",
                "Test",
            )
            withdrawn = service.withdraw_release(
                connection,
                package.release_id,
                "2026-08-21T02:00:00Z",
                "Test",
                "Fictional correction",
            )
            events = connection.execute(
                "SELECT event_type FROM engagement_audit_events WHERE event_id IN (?, ?, ?)",
                (
                    "EVT-REL-FIC-SERVICE-BOUNDARY-CREATED",
                    "EVT-REL-FIC-SERVICE-BOUNDARY-PUB",
                    "EVT-REL-FIC-SERVICE-BOUNDARY-WDN",
                ),
            ).fetchall()

        assert published.status == "PUBLISHED"
        assert withdrawn.status == "WITHDRAWN"
        assert {event["event_type"] for event in events} == {
            "RELEASE_CREATED",
            "RELEASE_PUBLISHED",
            "RELEASE_WITHDRAWN",
        }

    def test_publish_requires_active_transaction_without_mutation(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-publish-no-transaction")
        service = ClientReleaseService()
        with store.connect() as connection:
            with pytest.raises(ClientReleaseStateError, match="active caller transaction"):
                service.publish_release(
                    connection,
                    "REL-FIC-DRAFT",
                    "2026-08-21T01:00:00Z",
                    "Test",
                )
            package = service._storage.release_package(connection, "REL-FIC-DRAFT")

        assert package is not None
        assert package["status"] == "DRAFT"
        assert package["published_at"] is None

    def test_publish_succeeds_inside_active_transaction(self, tmp_path: Path) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-publish-transaction")
        service = ClientReleaseService()
        draft = ReleasePackage(
            release_id="REL-FIC-PUBLISH-TRANSACTION",
            engagement_id="ENG-FIC-0001",
            release_version=4,
            status="DRAFT",
            created_at="2026-08-21T00:00:00Z",
            created_by="Test",
        )
        with store.connect() as connection:
            connection.execute("BEGIN")
            service.withdraw_release(
                connection,
                "REL-FIC-PUBLISHED",
                "2026-08-20T23:00:00Z",
                "Test",
                "Superseded by fictional publication",
            )
            service.build_draft(connection, draft)
            source_entry = connection.execute(
                """
                SELECT * FROM client_release_entries
                WHERE release_id = 'REL-FIC-PUBLISHED'
                AND source_record_type = 'ACTION'
                ORDER BY release_entry_id LIMIT 1
                """
            ).fetchone()
            _insert_action_release_entry(
                connection,
                "RLE-FIC-PUBLISH-TRANSACTION",
                draft.release_id,
                source_entry["source_record_id"],
                display_title=source_entry["display_title"],
                display_summary=source_entry["display_summary"],
                action_owner=source_entry["action_owner"],
                action_target_date=source_entry["action_target_date"],
                action_delivery_status=source_entry["action_delivery_status"],
                evidence_ref=source_entry["approved_evidence_reference_id"],
                version=source_entry["source_record_version"],
            )
            package = service.publish_release(
                connection,
                draft.release_id,
                "2026-08-21T01:00:00Z",
                "Test",
            )

            assert connection.in_transaction
            assert package.status == "PUBLISHED"
            connection.rollback()

    def test_build_draft_uses_active_connection_for_uncommitted_state(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-uncommitted")
        service = ClientReleaseService()
        package = ReleasePackage(
            release_id="REL-FIC-UNCOMMITTED",
            engagement_id="ENG-FIC-0001",
            release_version=4,
            status="DRAFT",
            created_at="2026-08-21T00:00:00Z",
            created_by="Test",
        )
        with store.connect() as connection:
            connection.execute("BEGIN")
            persisted = service.build_draft(connection, package)
            history = service.get_release_history(connection, package.engagement_id)

            assert connection.in_transaction
            assert persisted == package
            assert package.release_id in {
                release.release_id for release in history
            }
            connection.rollback()

        with store.connect() as connection:
            assert service._storage.release_package(connection, package.release_id) is None

    def test_build_draft_rejects_terminal_metadata(self, tmp_path: Path) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-draft-metadata")
        service = ClientReleaseService()
        package = ReleasePackage(
            release_id="REL-FIC-TERMINAL-METADATA",
            engagement_id="ENG-FIC-0001",
            release_version=4,
            status="DRAFT",
            created_at="2026-08-21T00:00:00Z",
            created_by="Test",
            published_at="2026-08-21T01:00:00Z",
        )
        with store.connect() as connection:
            connection.execute("BEGIN")
            with pytest.raises(ClientReleaseStateError, match="terminal metadata"):
                service.build_draft(connection, package)
            assert service._storage.release_package(connection, package.release_id) is None
            connection.rollback()

    def test_build_draft_rolls_back_package_when_creation_event_fails(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-creation-atomic")
        service = ClientReleaseService()
        package = ReleasePackage(
            release_id="REL-FIC-CREATION-ATOMIC",
            engagement_id="ENG-FIC-0001",
            release_version=4,
            status="DRAFT",
            created_at="2026-08-21T00:00:00Z",
            created_by="Test",
        )
        with store.connect() as connection:
            connection.execute(
                """INSERT INTO engagement_audit_events
                   (event_id, engagement_id, event_type, recorded_at, actor)
                   VALUES (?, ?, 'RELEASE_CREATED', ?, ?)""",
                (
                    "EVT-REL-FIC-CREATION-ATOMIC-CREATED",
                    package.engagement_id,
                    package.created_at,
                    package.created_by,
                ),
            )
            connection.commit()
            connection.execute("BEGIN")
            with pytest.raises(sqlite3.IntegrityError):
                service.build_draft(connection, package)

            assert connection.in_transaction
            assert service._storage.release_package(connection, package.release_id) is None
            creation_events = connection.execute(
                """SELECT COUNT(*) AS count FROM engagement_audit_events
                   WHERE event_id = 'EVT-REL-FIC-CREATION-ATOMIC-CREATED'"""
            ).fetchone()["count"]
            assert creation_events == 1
            connection.execute(
                """INSERT INTO engagement_audit_events
                   (event_id, engagement_id, event_type, recorded_at, actor)
                   VALUES ('EVT-FIC-OUTER-CREATION', 'ENG-FIC-0001',
                           'RELEASE_CREATED', '2026-08-21T00:01:00Z', 'Test')"""
            )
            connection.rollback()

    def test_withdraw_rolls_back_status_when_withdrawal_event_fails(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-withdrawal-atomic")
        service = ClientReleaseService()
        with store.connect() as connection:
            connection.execute(
                """INSERT INTO engagement_audit_events
                   (event_id, engagement_id, event_type, recorded_at, actor)
                   VALUES ('EVT-REL-FIC-PUBLISHED-WDN', 'ENG-FIC-0001',
                           'RELEASE_WITHDRAWN', '2026-08-20T00:00:00Z', 'Test')"""
            )
            connection.commit()
            connection.execute("BEGIN")
            with pytest.raises(sqlite3.IntegrityError):
                service.withdraw_release(
                    connection,
                    "REL-FIC-PUBLISHED",
                    "2026-08-20T00:00:00Z",
                    "Test",
                    "Fictional correction",
                )

            package = service._storage.release_package(
                connection, "REL-FIC-PUBLISHED"
            )
            assert connection.in_transaction
            assert package is not None
            assert package["status"] == "PUBLISHED"
            assert package["withdrawn_at"] is None
            withdrawal_events = connection.execute(
                """SELECT COUNT(*) AS count FROM engagement_audit_events
                   WHERE event_id = 'EVT-REL-FIC-PUBLISHED-WDN'"""
            ).fetchone()["count"]
            assert withdrawal_events == 1
            connection.execute(
                """INSERT INTO engagement_audit_events
                   (event_id, engagement_id, event_type, recorded_at, actor)
                   VALUES ('EVT-FIC-OUTER-WITHDRAWAL', 'ENG-FIC-0001',
                           'RELEASE_WITHDRAWN', '2026-08-20T00:01:00Z', 'Test')"""
            )
            connection.rollback()

    @pytest.mark.parametrize(
        ("withdrawn_at", "withdrawn_by"),
        (
            ("2026-08-20 00:00:00Z", "Test"),
            ("2026-08-19T09:59:59Z", "Test"),
            ("2026-08-20T00:00:00Z", ""),
            ("2026-08-20T00:00:00Z", " Test"),
            ("2026-08-20T00:00:00Z", "Test "),
        ),
    )
    def test_withdraw_rejects_invalid_metadata_without_mutation(
        self, tmp_path: Path, withdrawn_at: str, withdrawn_by: str
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "service-withdrawal-validation")
        service = ClientReleaseService()
        with store.connect() as connection:
            connection.execute("BEGIN")
            with pytest.raises(ClientReleaseValidationError):
                service.withdraw_release(
                    connection,
                    "REL-FIC-PUBLISHED",
                    withdrawn_at,
                    withdrawn_by,
                )
            package = service._storage.release_package(
                connection, "REL-FIC-PUBLISHED"
            )
            assert package is not None
            assert package["status"] == "PUBLISHED"
            assert package["withdrawn_at"] is None
            connection.rollback()

    def test_current_route_delegates_to_the_service(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        from src.ace.workbench import client_routes

        store = WorkbenchStore(data_dir=tmp_path / "service-route")
        calls: list[tuple[sqlite3.Connection, str]] = []
        connect_calls = 0
        real_service = ClientReleaseService()
        original_connect = store.connect

        def tracked_connect() -> sqlite3.Connection:
            nonlocal connect_calls
            connect_calls += 1
            return original_connect()

        class TrackingService:
            def get_current_release(
                self, connection: sqlite3.Connection, engagement_id: str
            ) -> object:
                calls.append((connection, engagement_id))
                return real_service.get_current_release(connection, engagement_id)

            def get_engagement(
                self, connection: sqlite3.Connection, engagement_id: str
            ) -> dict[str, object] | None:
                calls.append((connection, engagement_id))
                return real_service.get_engagement(connection, engagement_id)

        monkeypatch.setattr(client_routes, "ClientReleaseService", TrackingService)
        monkeypatch.setattr(store, "connect", tracked_connect)
        data = client_routes._get_client_data(store, "ENG-FIC-0001")

        assert len(calls) == 2
        assert all(call[1] == "ENG-FIC-0001" for call in calls)
        assert calls[0][0] is calls[1][0]
        assert connect_calls == 1
        assert data.release_version == 2


# ── API tests ───────────────────────────────────────────────────

class TestClientApi:

    def test_valid_credentials_return_current_package(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "a-valid")
        client = TestClient(app)
        resp = client.get("/client/api/v1/release/current", auth=_client_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert data["engagement_name"] == "Fictional Mobile Field Capture Engagement"
        assert data["release_version"] == 2
        assert data["conclusion"] is not None
        assert data["conclusion"]["title"] == "Approved field capture conclusion"
        assert data["conclusion"]["evidence_reference_id"] == "EVD-FIC-0001"

    def test_current_api_and_html_match_characterised_baseline(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Keep the established current-release API payload and HTML bytes stable."""
        _set_client_env(monkeypatch, tmp_path / "a-characterised-bytes")
        client = TestClient(app)

        api = client.get("/client/api/v1/release/current", auth=_client_auth())
        page = client.get("/client", auth=_client_auth())

        assert api.status_code == 200
        assert api.headers["content-type"] == "application/json"
        assert api.json() == {
            "engagement_name": "Fictional Mobile Field Capture Engagement",
            "review_status": "READY_FOR_CAPTURE",
            "release_version": 2,
            "published_at": "2026-08-19T10:00:00Z",
            "conclusion": {
                "title": "Approved field capture conclusion",
                "summary": (
                    "The field capture control is suitably designed for "
                    "fictional mobile evidence collection under the pilot scope."
                ),
                "evidence_reference_id": "EVD-FIC-0001",
            },
            "actions": [
                {
                    "description": (
                        "Review and update the mobile field capture process to reduce "
                        "photo upload errors observed during the inspection."
                    ),
                    "owner": "Fictional Safety Manager",
                    "target_date": "2026-09-30",
                    "status": "OPEN",
                }
            ],
        }
        assert len(api.content) == 599
        assert sha256(api.content).hexdigest() == (
            "5e19bc98c09286a2eb8181650462cfb5ae6952eb342da080643d54a8ab6856af"
        )
        assert page.status_code == 200
        assert page.headers["content-type"] == "text/html; charset=utf-8"
        assert len(page.content) == 3156
        assert sha256(page.content).hexdigest() == (
            "017f19c4e4ebf5e98cb2c9493deec789a5bbf2107a39f6326c6d4fb8b0788e3d"
        )

    def test_client_get_endpoints_leave_release_rows_unchanged(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Both read routes preserve exact package, entry, source, and audit rows."""
        _set_client_env(monkeypatch, tmp_path / "a-read-snapshots")
        client = TestClient(app)
        store = WorkbenchStore()
        with store.connect() as conn:
            before = _client_release_read_snapshot(conn, CLIENT_ENG)

        api = client.get("/client/api/v1/release/current", auth=_client_auth())

        assert api.status_code == 200
        with store.connect() as conn:
            assert _client_release_read_snapshot(conn, CLIENT_ENG) == before

        page = client.get("/client", auth=_client_auth())

        assert page.status_code == 200
        with store.connect() as conn:
            assert _client_release_read_snapshot(conn, CLIENT_ENG) == before

    def test_missing_credentials_return_403(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "a-noauth")
        client = TestClient(app)
        resp = client.get("/client/api/v1/release/current")
        assert resp.status_code == 403

    def test_invalid_credentials_return_403(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "a-bad")
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=("wrong", "wrong")
        )
        assert resp.status_code == 403

    def test_auditor_credentials_do_not_grant_client_access(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "a-aud")
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_auditor_auth()
        )
        assert resp.status_code == 403

    def test_missing_configuration_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
        # Don't set client env vars
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=("any", "any")
        )
        assert resp.status_code == 503

    def test_empty_password_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty ACE_CLIENT_PASSWORD must be rejected, not treated as configured."""
        monkeypatch.setenv("ACE_AUDITOR_PASSWORD", "fictional-password")
        monkeypatch.setenv("ACE_CLIENT_USERNAME", CLIENT_USER)
        monkeypatch.setenv("ACE_CLIENT_PASSWORD", "")
        monkeypatch.setenv("ACE_CLIENT_ENGAGEMENT_ID", CLIENT_ENG)
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=(CLIENT_USER, "")
        )
        assert resp.status_code == 503

    def test_g0_guard_rejects_non_fictional_engagement(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A real-client or non-fictional engagement must be rejected
        before the release package is exposed, regardless of valid auth."""
        _set_client_env(monkeypatch, tmp_path / "a-nonfic")
        client = TestClient(app)
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO engagement_setups "
                "(engagement_id, creation_attempt_key, title, state, "
                " is_fictional, data_classification, created_at) "
                "VALUES ('ENG-G0-TEST', 'g0-test-key', 'Real Client', "
                "'READY_FOR_CAPTURE', 0, 'REAL_CLIENT', '2026-08-20T00:00:00Z')"
            )
            # A valid APPROVED conclusion with audit event is required
            # so the insert-time source validation trigger accepts the
            # CONCLUSION entry below.
            conn.execute(
                "INSERT OR IGNORE INTO conclusions "
                "(conclusion_id, mate_id, status, title, engagement_id, "
                " evidence_id, version, conclusion_type, summary, "
                " approved_by, approved_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "CON-G0-TEST",
                    "MATE-FIC-0001",
                    "APPROVED",
                    "G0 Test Conclusion",
                    "ENG-G0-TEST",
                    "EVD-G0-TEST",
                    1,
                    "CONCLUSION",
                    "Valid conclusion for the non-fictional guard test.",
                    "Test Auditor",
                    "2026-08-20T00:00:00Z",
                    "2026-08-20T00:00:00Z",
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "EVT-CON-G0-TEST-APPROVED",
                    "ENG-G0-TEST",
                    "CONCLUSION_APPROVED",
                    "2026-08-20T00:00:00Z",
                    "Test Auditor",
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, created_at, created_by) "
                "VALUES ('REL-G0-TEST', 'ENG-G0-TEST', 1, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'test')"
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-REL-G0-TEST-CREATED', 'ENG-G0-TEST', "
                "'RELEASE_CREATED', '2026-08-20T00:00:00Z', 'test')"
            )
            conn.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, source_record_id, "
                " source_record_version, approved_evidence_reference_id, "
                " display_title, display_summary) "
                "VALUES ('RLE-G0-TEST', 'REL-G0-TEST', 'CONCLUSION', 'CON-G0-TEST', "
                "1, 'EVD-G0-TEST', 'G0 Test Conclusion', "
                "'Valid conclusion for the non-fictional guard test.')"
            )
            conn.execute(
                "UPDATE client_release_packages "
                "SET status = 'PUBLISHED', "
                "    published_at = '2026-08-20T00:00:00Z', "
                "    published_by = 'test' "
                "WHERE release_id = 'REL-G0-TEST'"
            )
        monkeypatch.setenv("ACE_CLIENT_ENGAGEMENT_ID", "ENG-G0-TEST")
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 503
        # HTML page must also be blocked
        page = client.get("/client", auth=_client_auth())
        assert page.status_code == 503

    def test_post_fails(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "a-post")
        client = TestClient(app)
        resp = client.post(
            "/client/api/v1/release/current",
            json={"x": 1},
            auth=_client_auth(),
        )
        assert resp.status_code in (405, 404)

    def test_put_fails(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "a-put")
        client = TestClient(app)
        resp = client.put(
            "/client/api/v1/release/current",
            json={"x": 1},
            auth=_client_auth(),
        )
        assert resp.status_code in (405, 404)

    def test_delete_fails(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "a-del")
        client = TestClient(app)
        resp = client.delete(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code in (405, 404)


# ── HTML page tests ─────────────────────────────────────────────

class TestClientPage:

    def test_page_loads(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "p-load")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        assert resp.status_code == 200
        html = resp.text
        assert "Client Release View" in html
        assert "Fictional Mobile Field Capture Engagement" in html
        assert "Fictional pilot information only" in html

    def test_published_conclusion_appears(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "p-conc")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        assert "Approved field capture conclusion" in resp.text
        assert "field capture control is suitably designed" in resp.text
        assert "EVD-FIC-0001" in resp.text

    def test_release_version_appears(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "p-ver")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        assert "Release: v2" in resp.text

    def test_fictional_notice_appears(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "p-not")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        assert "Fictional pilot information only" in resp.text
        assert "not a client audit report" in resp.text

    def test_candidate_conclusion_not_visible(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "p-cand")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        # The stale draft conclusion must not appear
        assert "Fictional stale draft" not in resp.text

    def test_private_fields_not_in_page(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "p-priv")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        html = resp.text
        # No internal metadata in client view
        assert "approved_by" not in html
        assert "approved_at" not in html

    def test_no_edit_controls(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "p-edit")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        html = resp.text.lower()
        assert "<form" not in html
        assert "<input" not in html
        assert "<button" not in html

    def test_page_requires_auth(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "p-auth")
        client = TestClient(app)
        resp = client.get("/client")
        assert resp.status_code == 403

    def test_html_content_is_escaped(self) -> None:
        """Dynamic values rendered from database must be HTML-escaped."""
        from src.ace.domain.release import ClientConclusionEntry, ClientReleaseResponse
        from src.ace.workbench.client_routes import _render_page

        data = ClientReleaseResponse(
            engagement_name='<script>alert("eng")</script>',
            review_status="READY_FOR_CAPTURE",
            release_version=1,
            published_at='<img src=x onerror=alert(1)>',
            conclusion=ClientConclusionEntry(
                title='<b>bold conclusion</b>',
                summary='<a href="evil">click</a>',
                evidence_reference_id='<iframe src=x></iframe>',
            ),
        )
        html = _render_page(data)
        assert "&lt;script&gt;" in html
        assert "&lt;img" in html
        assert "&lt;b&gt;" in html
        assert "&lt;a" in html
        assert "&lt;iframe" in html
        # Raw tags must NOT appear as executable markup
        assert '<script>alert' not in html
        assert '<img src=x onerror' not in html
        assert '<b>bold' not in html
        assert '<iframe' not in html


# ── Audit events ────────────────────────────────────────────────


class TestReleaseAuditEvents:
    """Verify release lifecycle and conclusion approval events exist."""

    def test_engagement_audit_events_include_conclusion_approval(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "audit-conclusion")
        with store.connect() as conn:
            rows = conn.execute(
                """SELECT event_id, event_type, engagement_id, actor
                   FROM engagement_audit_events
                   WHERE event_type = 'CONCLUSION_APPROVED'
                   ORDER BY recorded_at"""
            ).fetchall()
        assert len(rows) >= 1, "CON-FIC-0001 approval event must exist"
        events = {r["event_id"]: dict(r) for r in rows}
        assert "EVT-CON-FIC-0001-APPROVED" in events
        evt = events["EVT-CON-FIC-0001-APPROVED"]
        assert evt["engagement_id"] == "ENG-FIC-0001"
        assert evt["actor"] == "Fictional Site Auditor"

    def test_release_created_events_exist(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "audit-created")
        with store.connect() as conn:
            rows = conn.execute(
                """SELECT event_id, engagement_id
                   FROM engagement_audit_events
                   WHERE event_type = 'RELEASE_CREATED'
                   ORDER BY recorded_at"""
            ).fetchall()
        event_ids = {r["event_id"] for r in rows}
        assert "EVT-REL-FIC-DRAFT-CREATED" in event_ids
        assert "EVT-REL-FIC-PUB-CREATED" in event_ids
        assert "EVT-REL-FIC-WDN-CREATED" in event_ids
        for r in rows:
            assert r["engagement_id"] == "ENG-FIC-0001"

    def test_release_published_events_exist(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "audit-published")
        with store.connect() as conn:
            rows = conn.execute(
                """SELECT event_id
                   FROM engagement_audit_events
                   WHERE event_type = 'RELEASE_PUBLISHED'
                   ORDER BY recorded_at"""
            ).fetchall()
        event_ids = {r["event_id"] for r in rows}
        assert "EVT-REL-FIC-PUBLISHED-PUB" in event_ids
        assert "EVT-REL-FIC-WITHDRAWN-PUB" in event_ids

    def test_release_withdrawn_event_exists(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "audit-withdrawn")
        with store.connect() as conn:
            row = conn.execute(
                """SELECT event_id, engagement_id, actor
                   FROM engagement_audit_events
                   WHERE event_type = 'RELEASE_WITHDRAWN'
                   AND event_id = 'EVT-REL-FIC-WDN-WITHDRAWN'"""
            ).fetchone()
        assert row is not None
        assert row["engagement_id"] == "ENG-FIC-0001"
        assert row["actor"] == "Fictional Site Auditor"

    def test_audit_events_are_immutable(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "audit-immutable")
        with store.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    "UPDATE engagement_audit_events SET actor = 'altered' "
                    "WHERE event_id = 'EVT-CON-FIC-0001-APPROVED'"
                )
                conn.commit()
                pytest.fail("expected immutable trigger to fire")
            except sqlite3.IntegrityError as e:
                conn.rollback()
                assert "immutable" in str(e) or "ABORT" in str(e)

    def test_check_constraint_migrated_for_existing_databases(
        self, tmp_path: Path
    ) -> None:
        """On a database created before Phase 6A, the CHECK constraint
        must be migrated so new event types (CONCLUSION_APPROVED,
        RELEASE_CREATED, etc.) are accepted."""
        data_dir = tmp_path / "migration-test"
        store = WorkbenchStore(data_dir)
        with store.connect() as conn:
            # Simulate a pre-6A schema: drop the current table and
            # recreate with only the original two event types.
            conn.execute("DROP TABLE IF EXISTS engagement_audit_events")
            conn.execute(
                """CREATE TABLE engagement_audit_events (
                       event_id TEXT PRIMARY KEY,
                       engagement_id TEXT NOT NULL,
                       event_type TEXT NOT NULL CHECK (
                           event_type IN ('ENGAGEMENT_CREATED', 'ENGAGEMENT_ACTIVATED')
                       ),
                       recorded_at TEXT NOT NULL,
                       actor TEXT NOT NULL
                   )"""
            )
            conn.execute(
                "INSERT INTO engagement_audit_events VALUES "
                "('EVT-OLD-1', 'ENG-FIC-0001', 'ENGAGEMENT_CREATED', "
                "'2026-01-01T00:00:00Z', 'old')"
            )
        # Re-open — migration should fire, table rebuilt, old row preserved
        store2 = WorkbenchStore(data_dir)
        with store2.connect() as conn:
            # Old row must survive migration
            old = conn.execute(
                "SELECT event_id FROM engagement_audit_events "
                "WHERE event_id = 'EVT-OLD-1'"
            ).fetchone()
            assert old is not None, "pre-existing row lost during migration"
            # New event type must be accepted after migration
            conn.execute(
                "INSERT INTO engagement_audit_events VALUES "
                "('EVT-MIG-TEST', 'ENG-FIC-0001', 'RELEASE_CREATED', "
                "'2026-08-20T00:00:00Z', 'test')"
            )
            row = conn.execute(
                "SELECT event_type FROM engagement_audit_events "
                "WHERE event_id = 'EVT-MIG-TEST'"
            ).fetchone()
            assert row is not None
            assert row["event_type"] == "RELEASE_CREATED"


# ── Phase 6B1: approved actions ──────────────────────────────────

class TestActionAPIResponse:

    def test_approved_action_appears_in_api(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """1. An approved released Action appears in the API."""
        _set_client_env(monkeypatch, tmp_path / "u-api-action")
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "actions" in data
        assert isinstance(data["actions"], list)
        assert len(data["actions"]) >= 1
        act = data["actions"][0]
        assert "description" in act
        assert "owner" in act
        assert "target_date" in act
        assert "status" in act
        assert act["owner"] == "Fictional Safety Manager"
        assert act["target_date"] == "2026-09-30"
        assert act["status"] == "OPEN"

    def test_published_action_survives_rejected_status_change(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A published Action remains visible after a rejected status change."""
        _set_client_env(monkeypatch, tmp_path / "u-candidate")
        # Verify the published Action is visible initially
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        before = [a for a in data["actions"]
                  if a["owner"] == "Fictional Safety Manager"]
        assert len(before) == 1
        # Approved source status cannot change.
        store = WorkbenchStore()
        with store.connect() as conn:
            with pytest.raises(sqlite3.IntegrityError,
                               match="Approved actions cannot be updated"):
                conn.execute(
                    "UPDATE approved_actions "
                    "SET approval_status = 'CANDIDATE' "
                    "WHERE action_id = 'ACT-FIC-0001'",
                )
        # Action must still appear in the published release
        resp2 = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        after = [a for a in data2["actions"]
                 if a["owner"] == "Fictional Safety Manager"]
        assert len(after) == 1
        assert after[0]["description"] == before[0]["description"]
        assert after[0]["target_date"] == before[0]["target_date"]
        assert after[0]["status"] == before[0]["status"]

    def test_other_engagement_action_hidden(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """4. An Action with no release entry remains hidden."""
        _set_client_env(monkeypatch, tmp_path / "u-other-eng")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO approved_actions "
                "(action_id, engagement_id, version, description, owner, "
                " target_date, approval_status, delivery_status, "
                " approved_by, approved_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "ACT-FIC-ENG2", "ENG-FIC-0002", 1,
                    "Other engagement action", "Owner", "2026-12-31",
                    "APPROVED", "OPEN",
                    "Auditor", "2026-08-20T00:00:00Z",
                    "2026-08-20T00:00:00Z",
                ),
            )
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        descriptions = [a["description"] for a in data["actions"]]
        assert "Other engagement action" not in descriptions

    def test_unreferenced_action_version_hidden(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """5. An Action with no release entry remains hidden."""
        _set_client_env(monkeypatch, tmp_path / "u-unref")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO approved_actions "
                "(action_id, engagement_id, version, description, owner, "
                " target_date, approval_status, delivery_status, "
                " approved_by, approved_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "ACT-FIC-UNREF", "ENG-FIC-0001", 2,
                    "Unreferenced action", "Owner", "2026-12-31",
                    "APPROVED", "OPEN",
                    "Auditor", "2026-08-20T00:00:00Z",
                    "2026-08-20T00:00:00Z",
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, ?, 'ACTION_APPROVED', ?, ?)",
                (
                    "EVT-ACT-FIC-UNREF-APPROVED", "ENG-FIC-0001",
                    "2026-08-20T00:00:00Z", "Auditor",
                ),
            )
            # version=2 is not referenced by any release entry
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        descriptions = [a["description"] for a in data["actions"]]
        assert "Unreferenced action" not in descriptions

    def test_private_fields_not_exposed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """11. Private approval fields do not appear in the API."""
        _set_client_env(monkeypatch, tmp_path / "u-priv")
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        for act in data["actions"]:
            assert "approved_by" not in act
            assert "action_id" not in act
            assert "approval_status" not in act
            assert "engagement_id" not in act


class TestActionHTMLPage:

    def test_action_appears_on_page(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """2. The Action appears on the HTML page."""
        _set_client_env(monkeypatch, tmp_path / "u-html")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        assert resp.status_code == 200
        html_text = resp.text
        assert "Agreed Actions" in html_text
        assert "Fictional Safety Manager" in html_text
        assert "2026-09-30" in html_text
        assert "OPEN" in html_text

    def test_approved_actions_section_heading(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The page uses 'Agreed Actions' as the section heading."""
        _set_client_env(monkeypatch, tmp_path / "u-heading")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        assert resp.status_code == 200
        assert "Agreed Actions" in resp.text
        assert "Approved Actions" not in resp.text

    def test_action_text_html_escaped(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """12. Dynamic Action text is HTML-escaped."""
        _set_client_env(monkeypatch, tmp_path / "u-xss")
        store = WorkbenchStore()
        script_injection = '<script>alert("xss")</script>'
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-FIC-XSS", "ENG-FIC-0001",
                script_injection, "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-FIC-XSS", "ENG-FIC-0001")
            conn.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary, action_owner, action_target_date, "
                " action_delivery_status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("RLE-FIC-XSS", "REL-FIC-XSS", "ACTION",
                 "ACT-FIC-XSS", 1, "EVD-FIC-0001",
                 "XSS Test", script_injection,
                 "Owner", "2026-12-31", "OPEN"),
            )
            _publish_draft_package(conn, "REL-FIC-XSS", "ENG-FIC-0001")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        assert resp.status_code == 200
        html_text = resp.text
        # Raw script tag must not appear — it must be escaped
        assert "<script>" not in html_text
        assert "&lt;script&gt;" in html_text


class TestActionReleaseRules:

    def test_missing_owner_blocks_publication(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """6. Missing owner blocks client publication of the Action."""
        _set_client_env(monkeypatch, tmp_path / "u-no-owner")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-FIC-NO-OWN", "ENG-FIC-0001",
                "No owner action", "", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-FIC-NO-OWN", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("RLE-FIC-NO-OWN", "REL-FIC-NO-OWN", "ACTION",
                     "ACT-FIC-NO-OWN", 1, "EVD-FIC-0001",
                     "No Owner", "No owner action",
                     "", "2026-12-31", "OPEN"),
                )

    def test_missing_target_date_blocks_publication(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """7. A non-matching target date is rejected at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-no-date")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-FIC-NO-DATE", "ENG-FIC-0001",
                "No date action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-FIC-NO-DATE", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("RLE-FIC-NO-DATE", "REL-FIC-NO-DATE", "ACTION",
                     "ACT-FIC-NO-DATE", 1, "EVD-FIC-0001",
                     "No Date", "No date action",
                     "Owner", "", "OPEN"),
                )

    def test_source_change_does_not_alter_published_text(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """8. Approved action content cannot change after approval."""
        _set_client_env(monkeypatch, tmp_path / "u-immutable")
        # Record snapshot values before attempted change
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        data_before = resp.json()
        owner_before = data_before["actions"][0]["owner"]
        desc_before = data_before["actions"][0]["description"]
        date_before = data_before["actions"][0]["target_date"]
        status_before = data_before["actions"][0]["status"]
        # Content mutation on an APPROVED action is blocked
        store = WorkbenchStore()
        with pytest.raises(sqlite3.IntegrityError,
                           match="Approved actions cannot be updated"):
            with store.connect() as conn:
                conn.execute(
                    "UPDATE approved_actions "
                    "SET description = ?, owner = ?, "
                    "target_date = ?, delivery_status = ? "
                    "WHERE action_id = 'ACT-FIC-0001'",
                    ("Changed after publication", "New Owner",
                     "2027-01-01", "COMPLETE"),
                )
        # Re-verify — published release still shows original values
        resp2 = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        data_after = resp2.json()
        assert data_after["actions"][0]["owner"] == owner_before
        assert data_after["actions"][0]["description"] == desc_before
        assert data_after["actions"][0]["target_date"] == date_before
        assert data_after["actions"][0]["status"] == status_before

    def test_withdrawn_package_does_not_expose_action(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """9. A withdrawn package does not expose its Action."""
        _set_client_env(monkeypatch, tmp_path / "u-withdrawn")
        store = WorkbenchStore()
        # Seed an action entry that belongs ONLY to the WITHDRAWN package
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-FIC-WDN", "ENG-FIC-0001",
                "Withdrawn-only action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-FIC-WDN-DRAFT", "ENG-FIC-0001")
            conn.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary, action_owner, action_target_date, "
                " action_delivery_status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "RLE-FIC-WDN-ACT", "REL-FIC-WDN-DRAFT", "ACTION",
                    "ACT-FIC-WDN", 1, "EVD-FIC-0001",
                    "Withdrawn action", "Withdrawn-only action",
                    "Owner", "2026-12-31", "OPEN",
                ),
            )
            _publish_draft_package(conn, "REL-FIC-WDN-DRAFT", "ENG-FIC-0001")
            # Withdraw the published package.
            conn.execute(
                "UPDATE client_release_packages "
                "SET status = 'WITHDRAWN', "
                "    withdrawn_at = '2026-08-20T01:00:00Z', "
                "    withdrawn_by = 'Test' "
                "WHERE release_id = 'REL-FIC-WDN-DRAFT'"
            )
            conn.execute(
                "INSERT OR IGNORE INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, ?, ?, ?, ?)",
                ("EVT-REL-FIC-WDN-WDN", "ENG-FIC-0001",
                 "RELEASE_WITHDRAWN", "2026-08-20T01:00:00Z", "Test"),
            )
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        descriptions = [a["description"] for a in data["actions"]]
        assert "Withdrawn-only action summary" not in descriptions

    def test_rejected_source_delete_keeps_action_visible(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A published Action remains visible after source deletion fails."""
        _set_client_env(monkeypatch, tmp_path / "u-deleted")
        # Verify visible before deletion
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        before = [a for a in resp.json()["actions"]
                  if a["owner"] == "Fictional Safety Manager"]
        assert len(before) == 1
        # Approved source deletion must fail.
        store = WorkbenchStore()
        with store.connect() as conn:
            with pytest.raises(sqlite3.IntegrityError,
                               match="Approved actions cannot be deleted"):
                conn.execute(
                    "DELETE FROM approved_actions "
                    "WHERE action_id = 'ACT-FIC-0001'",
                )
        # Action must still appear in the published release
        resp2 = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp2.status_code == 200
        after = [a for a in resp2.json()["actions"]
                 if a["owner"] == "Fictional Safety Manager"]
        assert len(after) == 1
        assert after[0]["description"] == before[0]["description"]
        assert after[0]["target_date"] == before[0]["target_date"]
        assert after[0]["status"] == before[0]["status"]

    def test_action_audit_before_release_published(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """ACTION_APPROVED audit event must precede RELEASE_PUBLISHED."""
        _set_client_env(monkeypatch, tmp_path / "u-audit-order")
        store = WorkbenchStore()
        with store.connect() as conn:
            events = conn.execute(
                "SELECT event_type, recorded_at FROM engagement_audit_events "
                "WHERE engagement_id = 'ENG-FIC-0001' "
                "ORDER BY recorded_at"
            ).fetchall()
        action_evt = None
        publish_evt = None
        for evt in events:
            if evt["event_type"] == "ACTION_APPROVED":
                action_evt = evt["recorded_at"]
            elif evt["event_type"] == "RELEASE_PUBLISHED":
                publish_evt = evt["recorded_at"]
        assert action_evt is not None, "ACTION_APPROVED event missing"
        assert publish_evt is not None, "RELEASE_PUBLISHED event missing"
        assert action_evt < publish_evt, (
            f"ACTION_APPROVED ({action_evt}) must precede "
            f"RELEASE_PUBLISHED ({publish_evt})"
        )

    def test_blank_delivery_status_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A non-matching delivery status is rejected at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-del-blank")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-FIC-DELBLANK", "ENG-FIC-0001",
                "Blank status action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            # Insert release entry with blank delivery status
            _create_draft_package(conn, "REL-FIC-DELBLANK", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("RLE-FIC-DELBLANK", "REL-FIC-DELBLANK", "ACTION",
                     "ACT-FIC-DELBLANK", 1, "EVD-FIC-0001",
                     "Blank Del", "Blank status action",
                     "Owner", "2026-12-31", ""),
                )

    def test_invalid_delivery_status_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A non-matching delivery status is rejected at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-del-bad")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-FIC-DELBAD", "ENG-FIC-0001",
                "Bad status action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            # Insert release entry with non-matching status
            _create_draft_package(conn, "REL-FIC-DELBAD", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("RLE-FIC-DELBAD", "REL-FIC-DELBAD", "ACTION",
                     "ACT-FIC-DELBAD", 1, "EVD-FIC-0001",
                     "Bad Del", "Bad status action",
                     "Owner", "2026-12-31", "INVALID"),
                )

    def test_open_and_complete_statuses_published(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """OPEN and COMPLETE delivery_statuses must be published."""
        _set_client_env(monkeypatch, tmp_path / "u-del-ok")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-FIC-DELOK", "ENG-FIC-0001")
            for i, status in enumerate(["OPEN", "COMPLETE"]):
                aid = f"ACT-FIC-DELOK-{i}"
                _insert_approved_action(
                    conn, aid, "ENG-FIC-0001",
                    f"Status {status}", "Owner", "2026-12-31", status,
                    "Auditor", "2026-08-20T00:00:00Z",
                )
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"RLE-FIC-DELOK-{i}", "REL-FIC-DELOK", "ACTION",
                        aid, 1, "EVD-FIC-0001",
                        f"OK Del {status}", f"Status {status}",
                        "Owner", "2026-12-31", status,
                    ),
                )
            _publish_draft_package(conn, "REL-FIC-DELOK", "ENG-FIC-0001")
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        statuses = [a["status"] for a in data["actions"]]
        assert "OPEN" in statuses
        assert "COMPLETE" in statuses


class TestActionIntegrity:

    def test_other_engagement_release_package_hidden(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An Action in another engagement's release package must not
        appear for a different engagement's client. The release
        package is the engagement boundary."""
        _set_client_env(monkeypatch, tmp_path / "u-integ-eng")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-FIC-ENG2X", "ENG-FIC-0002",
                "Cross-package action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-FIC-0002-PUB", "ENG-FIC-0002")
            conn.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary, action_owner, action_target_date, "
                " action_delivery_status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "RLE-FIC-ENG2X", "REL-FIC-0002-PUB", "ACTION",
                    "ACT-FIC-ENG2X", 1, "EVD-FIC-0001",
                    "Cross Eng", "Cross-package action",
                    "Owner", "2026-12-31", "OPEN",
                ),
            )
            _publish_draft_package(conn, "REL-FIC-0002-PUB", "ENG-FIC-0002")
        # Client is configured for ENG-FIC-0001 — must not see
        # actions from ENG-FIC-0002's release package.
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        descriptions = [a["description"] for a in data["actions"]]
        assert "Cross-package action" not in descriptions

    def test_rejected_version_update_preserves_snapshot(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A rejected source version update preserves the snapshot."""
        _set_client_env(monkeypatch, tmp_path / "u-integ-ver")
        store = WorkbenchStore()
        with store.connect() as conn:
            # Create an action at version 1 and publish its snapshot.
            _insert_approved_action(
                conn, "ACT-FIC-VER", "ENG-FIC-0001",
                "Version 1 snapshot description", "Owner V1",
                "2026-08-30", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-FIC-VER", "ENG-FIC-0001")
            conn.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary, action_owner, action_target_date, "
                " action_delivery_status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "RLE-FIC-VER", "REL-FIC-VER", "ACTION",
                    "ACT-FIC-VER", 1,
                    "EVD-FIC-0001",
                    "Version test", "Version 1 snapshot description",
                    "Owner V1", "2026-08-30", "OPEN",
                ),
            )
            _publish_draft_package(conn, "REL-FIC-VER", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Approved actions cannot be updated"):
                conn.execute(
                    "UPDATE approved_actions SET version = 2 "
                    "WHERE action_id = 'ACT-FIC-VER'"
                )
            # Changed content gets a new ID and approval event.
            _insert_approved_action(
                conn, "ACT-FIC-VER-CHANGED", "ENG-FIC-0001",
                "Version 2 description", "Owner V2", "2027-06-30",
                "COMPLETE", "Auditor Two", "2026-08-21T00:00:00Z",
            )
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        # Only the released version 1 snapshot must appear.
        found = [a for a in data["actions"]
                  if a["description"] == "Version 1 snapshot description"]
        assert len(found) == 1
        assert found[0]["owner"] == "Owner V1"
        assert found[0]["target_date"] == "2026-08-30"
        assert found[0]["status"] == "OPEN"
        assert not any(
            action["description"] == "Version 2 description"
            for action in data["actions"]
        )


class TestTargetDateValidation:

    def test_valid_date_accepted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Valid ISO calendar dates must be accepted."""
        _set_client_env(monkeypatch, tmp_path / "u-date-ok")
        store = WorkbenchStore()
        valid_dates = ["2026-12-31", "2026-01-01", "2028-02-29"]
        for i, good_date in enumerate(valid_dates):
            with store.connect() as conn:
                conn.execute(
                    "INSERT INTO approved_actions "
                    "(action_id, engagement_id, version, description, "
                    " owner, target_date, approval_status, "
                    " delivery_status, approved_by, approved_at, "
                    " created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"ACT-FIC-DATE-OK-{i}", "ENG-FIC-0001", 1,
                        "Good date", "Owner", good_date,
                        "APPROVED", "OPEN", "Auditor",
                        "2026-08-20T00:00:00Z",
                        "2026-08-20T00:00:00Z",
                    ),
                )

    def test_empty_target_date_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Empty target_date must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-date-empty")
        store = WorkbenchStore()
        with store.connect() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO approved_actions "
                    "(action_id, engagement_id, version, description, "
                    " owner, target_date, approval_status, "
                    " delivery_status, approved_by, approved_at, "
                    " created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        "ACT-FIC-DATE1", "ENG-FIC-0001", 1,
                        "Bad date", "Owner", "",
                        "APPROVED", "OPEN", "Auditor",
                        "2026-08-20T00:00:00Z",
                        "2026-08-20T00:00:00Z",
                    ),
                )

    def test_malformed_date_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Malformed dates must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-date-bad")
        store = WorkbenchStore()
        malformed = ["2026/12/31", "31-12-2026", "not-a-date",
                      "2026--01", "notadate"]
        for bad_date in malformed:
            with store.connect() as conn:
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute(
                        "INSERT INTO approved_actions "
                        "(action_id, engagement_id, version, "
                        " description, owner, target_date, "
                        " approval_status, delivery_status, "
                        " approved_by, approved_at, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            f"ACT-FIC-DATE-{bad_date[:8]}", "ENG-FIC-0001", 1,
                            "Bad date", "Owner", bad_date,
                            "APPROVED", "OPEN", "Auditor",
                            "2026-08-20T00:00:00Z",
                            "2026-08-20T00:00:00Z",
                        ),
                    )

    def test_impossible_calendar_date_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Impossible calendar dates must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-date-impossible")
        store = WorkbenchStore()
        impossible = ["2026-02-31", "2026-02-29", "2026-19-39",
                       "2026-11-31", "2026-02-30"]
        for i, bad_date in enumerate(impossible):
            with store.connect() as conn:
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute(
                        "INSERT INTO approved_actions "
                        "(action_id, engagement_id, version, "
                        " description, owner, target_date, "
                        " approval_status, delivery_status, "
                        " approved_by, approved_at, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            f"ACT-FIC-DATE-IMP-{i}", "ENG-FIC-0001", 1,
                            "Impossible date", "Owner", bad_date,
                            "APPROVED", "OPEN", "Auditor",
                            "2026-08-20T00:00:00Z",
                            "2026-08-20T00:00:00Z",
                        ),
                    )


class TestActionMigration:

    def test_approved_actions_migration_preserves_rows(
        self, tmp_path: Path
    ) -> None:
        """Adding snapshot columns must not drop existing data."""
        data_dir = tmp_path / "migrate-action"
        store1 = WorkbenchStore(data_dir=data_dir)
        # Seed an action
        with store1.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO approved_actions "
                "(action_id, engagement_id, version, description, "
                " owner, target_date, approval_status, "
                " delivery_status, approved_by, approved_at, "
                " created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "ACT-MIG-1", "ENG-FIC-0001", 1,
                    "Migration test", "Owner", "2026-12-31",
                    "APPROVED", "OPEN", "Auditor",
                    "2026-08-20T00:00:00Z",
                    "2026-08-20T00:00:00Z",
                ),
            )
        # Re-open — migration runs, row must survive
        store2 = WorkbenchStore(data_dir=data_dir)
        with store2.connect() as conn:
            row = conn.execute(
                "SELECT * FROM approved_actions WHERE action_id = 'ACT-MIG-1'"
            ).fetchone()
        assert row is not None
        assert row["description"] == "Migration test"


class TestActionWriteBoundary:

    def test_client_write_methods_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """10. Client write methods remain blocked on client routes."""
        _set_client_env(monkeypatch, tmp_path / "u-write")
        client = TestClient(app)
        auth = _client_auth()
        for method in ("post", "put", "patch"):
            resp = getattr(client, method)(
                "/client/api/v1/release/current", auth=auth, json={}
            )
            assert resp.status_code in (403, 405), (
                f"{method.upper()} returned {resp.status_code}"
            )
        resp = client.delete(
            "/client/api/v1/release/current", auth=auth
        )
        assert resp.status_code in (403, 405, 405)


class TestExistingBehaviourPreserved:

    def test_phase6a_conclusion_unchanged(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """13. Existing Phase 6A conclusion behaviour remains unchanged."""
        _set_client_env(monkeypatch, tmp_path / "u-conclusion")
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["conclusion"] is not None
        assert data["conclusion"]["title"] is not None
        assert data["conclusion"]["summary"] is not None
        assert data["conclusion"]["evidence_reference_id"] is not None

    def test_auth_unchanged(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """14. Existing authentication behaviour remains unchanged."""
        _set_client_env(monkeypatch, tmp_path / "u-auth")
        client = TestClient(app)
        # No auth — must be rejected
        resp = client.get("/client/api/v1/release/current")
        assert resp.status_code == 403
        # Wrong password — must be rejected
        resp = client.get(
            "/client/api/v1/release/current",
            auth=(CLIENT_USER, "wrong"),
        )
        assert resp.status_code == 403

    def test_fictional_notice_still_present(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The fictional pilot notice must still appear on the page."""
        _set_client_env(monkeypatch, tmp_path / "u-notice")
        client = TestClient(app)
        resp = client.get("/client", auth=_client_auth())
        assert resp.status_code == 200
        assert "Fictional pilot information only" in resp.text


class TestTriggerBlockedTransitions:

    def test_published_to_draft_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """PUBLISHED→DRAFT transition must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-blk-p2d")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-BLK-P2D", "ENG-FIC-0001")
            conn.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("RLE-BLK-P2D", "REL-BLK-P2D", "CONCLUSION",
                 "CON-FIC-0001", 1, "EVD-FIC-0001",
                 "Approved field capture conclusion",
                 "The field capture control is suitably designed for "
                 "fictional mobile evidence collection under the pilot scope."),
            )
            _publish_draft_package(conn, "REL-BLK-P2D", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Release packages are immutable"):
                conn.execute(
                    "UPDATE client_release_packages "
                    "SET status = 'DRAFT' "
                    "WHERE release_id = 'REL-BLK-P2D'"
                )

    def test_withdrawn_to_draft_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """WITHDRAWN→DRAFT transition must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-blk-w2d")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-BLK-W2D", "ENG-FIC-0001")
            conn.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("RLE-BLK-W2D", "REL-BLK-W2D", "CONCLUSION",
                 "CON-FIC-0001", 1, "EVD-FIC-0001",
                 "Approved field capture conclusion",
                 "The field capture control is suitably designed for "
                 "fictional mobile evidence collection under the pilot scope."),
            )
            _publish_draft_package(conn, "REL-BLK-W2D", "ENG-FIC-0001")
            conn.execute(
                "UPDATE client_release_packages "
                "SET status = 'WITHDRAWN', "
                "    withdrawn_at = '2026-08-21T00:00:00Z', "
                "    withdrawn_by = 'Test' "
                "WHERE release_id = 'REL-BLK-W2D'"
            )
            with pytest.raises(sqlite3.IntegrityError,
                               match="Release packages are immutable"):
                conn.execute(
                    "UPDATE client_release_packages "
                    "SET status = 'DRAFT' "
                    "WHERE release_id = 'REL-BLK-W2D'"
                )


class TestDraftPublicationRequirements:

    def test_missing_published_at_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """DRAFT→PUBLISHED must set published_at."""
        _set_client_env(monkeypatch, tmp_path / "u-miss-at")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-MISS-AT", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Release packages are immutable"):
                conn.execute(
                    "UPDATE client_release_packages "
                    "SET status = 'PUBLISHED', published_at = NULL, "
                    "    published_by = 'Test' "
                    "WHERE release_id = 'REL-MISS-AT'"
                )

    def test_missing_published_by_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """DRAFT→PUBLISHED must set published_by."""
        _set_client_env(monkeypatch, tmp_path / "u-miss-by")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-MISS-BY", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Release packages are immutable"):
                conn.execute(
                    "UPDATE client_release_packages "
                    "SET status = 'PUBLISHED', "
                    "    published_at = '2026-08-21T00:00:00Z', "
                    "    published_by = NULL "
                    "WHERE release_id = 'REL-MISS-BY'"
                )

    def test_changed_created_at_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """DRAFT→PUBLISHED must preserve created_at."""
        _set_client_env(monkeypatch, tmp_path / "u-chg-cat")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-CHG-CAT", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Release packages are immutable"):
                conn.execute(
                    "UPDATE client_release_packages "
                    "SET status = 'PUBLISHED', "
                    "    published_at = '2026-08-21T00:00:00Z', "
                    "    published_by = 'Test', "
                    "    created_at = '2026-01-01T00:00:00Z' "
                    "WHERE release_id = 'REL-CHG-CAT'"
                )


class TestActionSourceValidation:

    def test_missing_action_source_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """ACTION entry with non-existent source_action must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-src-miss")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-SRC-MISS", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("RLE-SRC-MISS", "REL-SRC-MISS", "ACTION",
                     "ACT-NONEXISTENT", 1, "EVD-FIC-0001",
                     "Missing Src", "Non-existent source action",
                     "Owner", "2026-12-31", "OPEN"),
                )

    def test_candidate_action_source_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """ACTION entry with CANDIDATE source_action must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-src-cand")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-SRC-CAND", "ENG-FIC-0001")
            conn.execute(
                "INSERT OR IGNORE INTO approved_actions "
                "(action_id, engagement_id, version, description, owner, "
                " target_date, approval_status, delivery_status, "
                " approved_by, approved_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("ACT-SRC-CAND", "ENG-FIC-0001", 1,
                 "Candidate action", "Owner", "2026-12-31",
                 "CANDIDATE", "OPEN", "Auditor",
                 "2026-08-21T00:00:00Z", "2026-08-21T00:00:00Z"),
            )
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("RLE-SRC-CAND", "REL-SRC-CAND", "ACTION",
                     "ACT-SRC-CAND", 1, "EVD-FIC-0001",
                     "Candidate Src", "Candidate source action",
                     "Owner", "2026-12-31", "OPEN"),
                )

    def test_cross_engagement_action_source_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """ACTION entry with cross-engagement source_action must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-src-cross")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-SRC-CROSS", "ENG-FIC-0001")
            # ACT-FIC-0001 belongs to ENG-FIC-0001, already seeded as APPROVED.
            # Create a package for ENG-FIC-0002 and try to reference ACT-FIC-0001.
            _create_draft_package(
                conn, "REL-SRC-CROSS-ENG2", "ENG-FIC-0002"
            )
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("RLE-SRC-CROSS", "REL-SRC-CROSS-ENG2", "ACTION",
                     "ACT-FIC-0001", 1, "EVD-FIC-0001",
                     "Cross Eng", "Cross-engagement action",
                     "Owner", "2026-12-31", "OPEN"),
                )

    def test_wrong_version_action_source_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """ACTION entry with wrong version must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-src-ver")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-SRC-VER", "ENG-FIC-0001")
            conn.execute(
                "INSERT OR IGNORE INTO approved_actions "
                "(action_id, engagement_id, version, description, owner, "
                " target_date, approval_status, delivery_status, "
                " approved_by, approved_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("ACT-SRC-VER", "ENG-FIC-0001", 2,
                 "Version 2 action", "Owner", "2026-12-31",
                 "APPROVED", "OPEN", "Auditor",
                 "2026-08-21T00:00:00Z", "2026-08-21T00:00:00Z"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, ?, 'ACTION_APPROVED', ?, ?)",
                ("EVT-ACT-SRC-VER-APPROVED", "ENG-FIC-0001",
                 "2026-08-21T00:00:00Z", "Auditor"),
            )
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("RLE-SRC-VER", "REL-SRC-VER", "ACTION",
                     "ACT-SRC-VER", 1, "EVD-FIC-0001",
                     "Wrong Ver", "Wrong version action",
                     "Owner", "2026-12-31", "OPEN"),
                )

    def test_conclusion_entries_unaffected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """CONCLUSION entries must pass their own validation
        while ACTION checks remain separate."""
        _set_client_env(monkeypatch, tmp_path / "u-src-conc")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-SRC-CONC", "ENG-FIC-0001")
            # Valid CONCLUSION entry with exact source snapshot match.
            conn.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("RLE-SRC-CONC", "REL-SRC-CONC", "CONCLUSION",
                 "CON-FIC-0001", 1, "EVD-FIC-0001",
                 "Approved field capture conclusion",
                 "The field capture control is suitably designed for "
                 "fictional mobile evidence collection under the pilot scope."),
            )
            _publish_draft_package(conn, "REL-SRC-CONC", "ENG-FIC-0001")
        # Must not crash client.
        client = TestClient(app)
        resp = client.get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert resp.status_code == 200


class TestSnapshotDateValidation:

    def test_invalid_snapshot_date_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An ACTION release entry with a non-matching target_date
        is rejected at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-snap-date")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-FIC-SNAPDATE", "ENG-FIC-0001",
                "Bad snapshot date", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-FIC-SNAPDATE", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("RLE-FIC-SNAPDATE", "REL-FIC-SNAPDATE", "ACTION",
                     "ACT-FIC-SNAPDATE", 1, "EVD-FIC-0001",
                     "Bad Date", "Bad snapshot date",
                     "Owner", "2026-02-31", "OPEN"),
                )


class TestUpgradeSafety:

    def test_action_not_seeded_on_upgrade(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """On a database that already contains a published release,
        the action seed must not mutate the existing package."""
        _set_client_env(monkeypatch, tmp_path / "u-upgrade")
        store = WorkbenchStore()
        with store.connect() as conn:
            pkg = conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            ).fetchone()
            assert pkg is not None
            entries = conn.execute(
                "SELECT COUNT(*) as cnt FROM client_release_entries "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            ).fetchone()["cnt"]
            assert entries >= 1
            action_entry = conn.execute(
                "SELECT 1 FROM client_release_entries "
                "WHERE release_entry_id = 'RLE-FIC-ACT-1'"
            ).fetchone()
            assert action_entry is not None, (
                "Action entry must exist on fresh database"
            )
        # Re-open: upgrade must not add entries
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            entries2 = conn.execute(
                "SELECT COUNT(*) as cnt FROM client_release_entries "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            ).fetchone()["cnt"]
            assert entries2 == entries, (
                f"Upgrade must not add entries to published release "
                f"({entries} -> {entries2})"
            )


class TestSeedUpgradeSafety:
    """Regression: seed must not mutate non-DRAFT packages during upgrade."""

    # ── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _count_entries(conn: sqlite3.Connection, release_id: str) -> int:
        return conn.execute(
            "SELECT COUNT(*) as cnt FROM client_release_entries "
            "WHERE release_id = ?",
            (release_id,),
        ).fetchone()["cnt"]

    @staticmethod
    def _count_audit_events(conn: sqlite3.Connection) -> int:
        return conn.execute(
            "SELECT COUNT(*) as cnt FROM engagement_audit_events"
        ).fetchone()["cnt"]

    # ── tests ────────────────────────────────────────────────────

    def test_withdrawn_package_not_mutated_on_reopen(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A WITHDRAWN package must not receive the seeded action
        when the database is re-opened for a Phase 6B1 upgrade."""
        d = tmp_path / "u-wdn"
        _set_client_env(monkeypatch, d)
        store = WorkbenchStore()
        with store.connect() as conn:
            # Manually withdraw the published package
            conn.execute(
                "UPDATE client_release_packages "
                "SET status = 'WITHDRAWN', "
                "    withdrawn_at = '2026-08-20T00:00:00Z', "
                "    withdrawn_by = 'Auditor' "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            )
            entry_count = self._count_entries(conn, "REL-FIC-PUBLISHED")
        # Re-open — upgrade path must leave WITHDRAWN package untouched
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            pkg = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            ).fetchone()
            assert pkg["status"] == "WITHDRAWN"
            assert (
                self._count_entries(conn, "REL-FIC-PUBLISHED")
                == entry_count
            )

    def test_published_package_not_mutated_on_reopen(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A PUBLISHED package must not receive extra entries
        when the database is re-opened."""
        d = tmp_path / "u-pub"
        _set_client_env(monkeypatch, d)
        store = WorkbenchStore()
        with store.connect() as conn:
            entry_count = self._count_entries(conn, "REL-FIC-PUBLISHED")
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            assert (
                self._count_entries(conn, "REL-FIC-PUBLISHED")
                == entry_count
            )

    def test_draft_package_receives_seeded_action(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """When the package is DRAFT, _seed_fictional_chain adds
        the action entry during initialisation."""
        _set_client_env(monkeypatch, tmp_path / "u-draft")
        store = WorkbenchStore()
        with store.connect() as conn:
            action_entry = conn.execute(
                "SELECT 1 FROM client_release_entries "
                "WHERE release_entry_id = 'RLE-FIC-ACT-1'"
            ).fetchone()
            assert action_entry is not None

    def test_audit_history_unchanged_on_reopen(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Existing release entries and audit events must remain
        unchanged when the database is re-opened for upgrade."""
        d = tmp_path / "u-audit"
        _set_client_env(monkeypatch, d)
        store = WorkbenchStore()
        with store.connect() as conn:
            entry_count = self._count_entries(conn, "REL-FIC-PUBLISHED")
            audit_count = self._count_audit_events(conn)
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            assert (
                self._count_entries(conn, "REL-FIC-PUBLISHED")
                == entry_count
            )
            assert (
                self._count_audit_events(conn) == audit_count
            )


class TestPhase6ATo6B1FictionalUpgrade:
    """A true Phase 6A release upgrades without changing history."""

    _UPGRADE_ID = "REL-FIC-PHASE6B1-UPGRADE"

    @staticmethod
    def _legacy_entries(
        conn: sqlite3.Connection, release_id: str
    ) -> list[tuple[object, ...]]:
        return [
            tuple(row) for row in conn.execute(
                "SELECT release_entry_id, release_id, source_record_type, "
                "source_record_id, source_record_version, "
                "approved_evidence_reference_id, display_title, "
                "display_summary FROM client_release_entries "
                "WHERE release_id = ? ORDER BY release_entry_id",
                (release_id,),
            ).fetchall()
        ]

    @staticmethod
    def _all_rows(
        conn: sqlite3.Connection, table: str, order_by: str
    ) -> list[tuple[object, ...]]:
        return [
            tuple(row) for row in conn.execute(
                f"SELECT * FROM {table} ORDER BY {order_by}"
            ).fetchall()
        ]

    def test_true_phase6a_database_gets_new_current_action_release(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "phase6a-upgrade"
        baseline = _build_phase6a_release_database(data_dir)

        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            old_package = conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            ).fetchone()
            old_entries = self._legacy_entries(conn, "REL-FIC-PUBLISHED")
            historical_withdrawn = tuple(conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-WITHDRAWN'"
            ).fetchone())
            historical_entries = self._legacy_entries(
                conn, "REL-FIC-WITHDRAWN"
            )
            current = conn.execute(
                "SELECT release_id, release_version, status, published_at "
                "FROM client_release_packages "
                "WHERE engagement_id = 'ENG-FIC-0001' "
                "AND status = 'PUBLISHED'"
            ).fetchone()
            new_entries = conn.execute(
                "SELECT source_record_type, source_record_id, "
                "source_record_version, approved_evidence_reference_id, "
                "display_title, display_summary, action_owner, "
                "action_target_date, action_delivery_status "
                "FROM client_release_entries WHERE release_id = ? "
                "ORDER BY source_record_type",
                (self._UPGRADE_ID,),
            ).fetchall()
            action = conn.execute(
                "SELECT description, owner, target_date, approval_status, "
                "delivery_status, approved_by, approved_at "
                "FROM approved_actions WHERE action_id = 'ACT-FIC-0001'"
            ).fetchone()
            source_conclusion = conn.execute(
                "SELECT title, summary, evidence_id, version, status, "
                "approved_by, approved_at FROM conclusions "
                "WHERE conclusion_id = 'CON-FIC-0001'"
            ).fetchone()
            legacy_publish_event = conn.execute(
                "SELECT event_id, engagement_id, event_type, recorded_at, actor "
                "FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-PUB-PUBLISHED'"
            ).fetchone()
            ordered_events = [
                tuple(row) for row in conn.execute(
                    "SELECT event_id, recorded_at FROM engagement_audit_events "
                    "WHERE event_id IN ("
                    "'EVT-ACT-FIC-0001-APPROVED', "
                    "'EVT-CON-FIC-0001-APPROVED', "
                    "'EVT-REL-FIC-PHASE6B1-UPGRADE-CREATED', "
                    "'EVT-REL-FIC-PUBLISHED-PHASE6B1-WITHDRAWN', "
                    "'EVT-REL-FIC-PHASE6B1-UPGRADE-PUB') "
                    "ORDER BY recorded_at"
                ).fetchall()
            ]

        original = baseline["legacy_package"]
        assert old_package["status"] == "WITHDRAWN"
        assert tuple(old_package)[:3] == original[:3]
        assert tuple(old_package)[4:8] == original[4:8]
        assert old_package["withdrawn_at"] == "2026-08-19T10:45:00Z"
        assert old_entries == baseline["legacy_entries"]
        assert old_entries[0][6] == "Approved field capture conclusion"
        assert historical_withdrawn == baseline["withdrawn_package"]
        assert historical_entries == baseline["withdrawn_entries"]

        assert tuple(current) == (
            self._UPGRADE_ID, 3, "PUBLISHED", "2026-08-19T11:00:00Z"
        )
        assert tuple(new_entries[0]) == (
            "ACTION", "ACT-FIC-0001", 1, "EVD-FIC-0001",
            "Improve field capture workflow",
            "Review and update the mobile field capture process "
            "to reduce photo upload errors observed during the inspection.",
            "Fictional Safety Manager", "2026-09-30", "OPEN",
        )
        assert tuple(new_entries[1]) == (
            "CONCLUSION", "CON-FIC-0001", 1, "EVD-FIC-0001",
            "Approved field capture conclusion",
            "The field capture control is suitably designed for "
            "fictional mobile evidence collection under the pilot scope.",
            "", "", "",
        )
        assert tuple(source_conclusion) == (
            "Fictional approved field conclusion",
            "The field capture control is suitably designed for "
            "fictional mobile evidence collection under the pilot scope.",
            "EVD-FIC-0001", 1, "APPROVED", "Fictional Site Auditor",
            "2026-08-19T10:00:00Z",
        )
        assert tuple(legacy_publish_event) == (
            "EVT-REL-FIC-PUB-PUBLISHED", "ENG-FIC-0001",
            "RELEASE_PUBLISHED", "2026-08-19T10:00:00Z",
            "Fictional Site Auditor",
        )
        assert tuple(action) == (
            "Review and update the mobile field capture process "
            "to reduce photo upload errors observed during the inspection.",
            "Fictional Safety Manager", "2026-09-30", "APPROVED", "OPEN",
            "Fictional Site Auditor", "2026-08-19T09:30:00Z",
        )
        assert ordered_events == [
            ("EVT-ACT-FIC-0001-APPROVED", "2026-08-19T09:30:00Z"),
            ("EVT-CON-FIC-0001-APPROVED", "2026-08-19T10:00:00Z"),
            (
                "EVT-REL-FIC-PHASE6B1-UPGRADE-CREATED",
                "2026-08-19T10:30:00Z",
            ),
            (
                "EVT-REL-FIC-PUBLISHED-PHASE6B1-WITHDRAWN",
                "2026-08-19T10:45:00Z",
            ),
            ("EVT-REL-FIC-PHASE6B1-UPGRADE-PUB", "2026-08-19T11:00:00Z"),
        ]

        _set_client_env(monkeypatch, data_dir)
        response = TestClient(app).get(
            "/client/api/v1/release/current", auth=_client_auth()
        )
        assert response.status_code == 200
        assert any(
            item["description"].startswith("Review and update")
            for item in response.json()["actions"]
        )

    def test_exact_phase6a_upgrade_keeps_versions_unique_after_reopen(
        self, tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "phase6a-unique-versions"
        _build_phase6a_release_database(data_dir)

        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            first_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT release_id, release_version "
                    "FROM client_release_packages "
                    "WHERE engagement_id = 'ENG-FIC-0001' "
                    "ORDER BY release_version"
                ).fetchall()
            ]
            first_draft_event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-DRAFT-CREATED'"
            ).fetchone()["count"]

        reopened = WorkbenchStore(data_dir=data_dir)
        with reopened.connect() as conn:
            reopened_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT release_id, release_version "
                    "FROM client_release_packages "
                    "WHERE engagement_id = 'ENG-FIC-0001' "
                    "ORDER BY release_version"
                ).fetchall()
            ]
            reopened_draft_event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-DRAFT-CREATED'"
            ).fetchone()["count"]

        assert first_packages == [
            ("REL-FIC-WITHDRAWN", 1),
            ("REL-FIC-PUBLISHED", 2),
            (self._UPGRADE_ID, 3),
        ]
        assert len({version for _, version in first_packages}) == len(
            first_packages
        )
        assert reopened_packages == first_packages
        assert len({version for _, version in reopened_packages}) == len(
            reopened_packages
        )
        assert first_draft_event_count == 0
        assert reopened_draft_event_count == 0

    def test_exact_base_draft_version_is_preserved_before_upgrade(
        self, tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "phase6a-existing-draft"
        baseline = _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-FIC-DRAFT', 'ENG-FIC-0001', 1, 'DRAFT', "
                "'2026-08-19T09:00:00Z', 'Fictional Site Auditor')"
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-REL-FIC-DRAFT-CREATED', 'ENG-FIC-0001', "
                "'RELEASE_CREATED', '2026-08-19T09:00:00Z', "
                "'Fictional Site Auditor')"
            )

        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            draft = conn.execute(
                "SELECT release_version, status FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-DRAFT'"
            ).fetchone()
            upgrade = conn.execute(
                "SELECT release_version, status FROM client_release_packages "
                "WHERE release_id = ?",
                (self._UPGRADE_ID,),
            ).fetchone()
            published = tuple(conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            ).fetchone())
            withdrawn = tuple(conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-WITHDRAWN'"
            ).fetchone())

        assert tuple(draft) == (1, "DRAFT")
        assert tuple(upgrade) == (3, "PUBLISHED")
        assert published[:3] == baseline["legacy_package"][:3]
        assert published[4:8] == baseline["legacy_package"][4:8]
        assert withdrawn == baseline["withdrawn_package"]

    def test_existing_version_three_draft_uses_next_upgrade_version(
        self, tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "phase6a-version-three-draft"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-FIC-DRAFT', 'ENG-FIC-0001', 3, 'DRAFT', "
                "'2026-08-19T09:00:00Z', 'Fictional Site Auditor')"
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-REL-FIC-DRAFT-CREATED', 'ENG-FIC-0001', "
                "'RELEASE_CREATED', '2026-08-19T09:00:00Z', "
                "'Fictional Site Auditor')"
            )

        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            draft = conn.execute(
                "SELECT release_version, status FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-DRAFT'"
            ).fetchone()
            upgrade = conn.execute(
                "SELECT release_version, status FROM client_release_packages "
                "WHERE release_id = ?",
                (self._UPGRADE_ID,),
            ).fetchone()

        assert tuple(draft) == (3, "DRAFT")
        assert tuple(upgrade) == (4, "PUBLISHED")

    def test_unrelated_version_three_skips_optional_draft_seed(
        self, tmp_path: Path,
    ) -> None:
        """Migration does not add the fixed draft beside version three."""
        data_dir = tmp_path / "phase6a-unrelated-version-three"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-UNRELATED-V3', 'ENG-FIC-0001', 3, 'DRAFT', "
                "'2026-08-19T09:15:00Z', 'Fictional Site Auditor')"
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-REL-UNRELATED-V3-CREATED', 'ENG-FIC-0001', "
                "'RELEASE_CREATED', '2026-08-19T09:15:00Z', "
                "'Fictional Site Auditor')"
            )
            conn.execute("PRAGMA ignore_check_constraints = ON")
            conn.execute(
                "INSERT INTO client_release_entries VALUES "
                "('RLE-FIC-PUB-ACTION', 'REL-FIC-PUBLISHED', 'ACTION', "
                "'ACT-LEGACY', 1, 'EVD-FIC-0001', 'Legacy action', "
                "'Legacy action')"
            )
            conn.execute("PRAGMA ignore_check_constraints = OFF")

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            first_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT release_id, release_version FROM "
                    "client_release_packages WHERE engagement_id = "
                    "'ENG-FIC-0001' ORDER BY release_version"
                ).fetchall()
            ]
            draft_count = conn.execute(
                "SELECT COUNT(*) AS count FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-DRAFT'"
            ).fetchone()["count"]
            draft_event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-DRAFT-CREATED'"
            ).fetchone()["count"]
            unrelated_event = tuple(conn.execute(
                "SELECT engagement_id, event_type, recorded_at, actor "
                "FROM engagement_audit_events WHERE event_id = "
                "'EVT-REL-UNRELATED-V3-CREATED'"
            ).fetchone())

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            reopened_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT release_id, release_version FROM "
                    "client_release_packages WHERE engagement_id = "
                    "'ENG-FIC-0001' ORDER BY release_version"
                ).fetchall()
            ]
            reopened_draft_event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-DRAFT-CREATED'"
            ).fetchone()["count"]

        assert first_packages == [
            ("REL-FIC-WITHDRAWN", 1),
            ("REL-FIC-PUBLISHED", 2),
            ("REL-UNRELATED-V3", 3),
        ]
        assert len({version for _, version in first_packages}) == len(
            first_packages
        )
        assert draft_count == 0
        assert draft_event_count == 0
        assert unrelated_event == (
            "ENG-FIC-0001",
            "RELEASE_CREATED",
            "2026-08-19T09:15:00Z",
            "Fictional Site Auditor",
        )
        assert reopened_packages == first_packages
        assert reopened_draft_event_count == 0

    def test_null_legacy_id_at_version_three_skips_optional_draft_seed(
        self, tmp_path: Path,
    ) -> None:
        """A legacy NULL ID still reserves its release version during upgrade."""
        data_dir = tmp_path / "phase6a-null-version-three"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "(NULL, 'ENG-FIC-0001', 3, 'DRAFT', "
                "'2026-08-19T09:15:00Z', 'Fictional Site Auditor')"
            )

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            first_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT release_id, release_version FROM "
                    "client_release_packages WHERE engagement_id = "
                    "'ENG-FIC-0001' ORDER BY release_version"
                ).fetchall()
            ]
            draft_event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-DRAFT-CREATED'"
            ).fetchone()["count"]
            upgrade_event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-PHASE6B1-UPGRADE-CREATED'"
            ).fetchone()["count"]

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            reopened_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT release_id, release_version FROM "
                    "client_release_packages WHERE engagement_id = "
                    "'ENG-FIC-0001' ORDER BY release_version"
                ).fetchall()
            ]
            reopened_draft_event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-DRAFT-CREATED'"
            ).fetchone()["count"]
            reopened_upgrade_event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-PHASE6B1-UPGRADE-CREATED'"
            ).fetchone()["count"]

        assert first_packages == [
            ("REL-FIC-WITHDRAWN", 1),
            ("REL-FIC-PUBLISHED", 2),
            (None, 3),
            (self._UPGRADE_ID, 4),
        ]
        assert len({version for _, version in first_packages}) == len(
            first_packages
        )
        assert draft_event_count == 0
        assert upgrade_event_count == 1
        assert reopened_packages == first_packages
        assert reopened_draft_event_count == draft_event_count
        assert reopened_upgrade_event_count == upgrade_event_count

    def test_skipped_draft_seed_does_not_create_orphan_event(
        self, tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "phase6a-skipped-draft-seed"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-FIC-PHASE6B1-UPGRADE', 'ENG-FIC-0001', 3, 'DRAFT', "
                "'2026-08-19T10:30:00Z', 'Fictional Site Auditor')"
            )

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            package_count = conn.execute(
                "SELECT COUNT(*) AS count FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-DRAFT'"
            ).fetchone()["count"]
            event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-DRAFT-CREATED'"
            ).fetchone()["count"]

        assert package_count == 0
        assert event_count == 0

    def test_existing_draft_seed_creates_event_from_package_row(
        self, tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "phase6a-existing-draft-seed"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-FIC-DRAFT', 'ENG-FIC-0001', 3, 'DRAFT', "
                "'2026-08-20T01:02:03Z', 'Fictional Draft Owner')"
            )

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            event = conn.execute(
                "SELECT engagement_id, event_type, recorded_at, actor "
                "FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-FIC-DRAFT-CREATED'"
            ).fetchone()

        assert tuple(event) == (
            "ENG-FIC-0001",
            "RELEASE_CREATED",
            "2026-08-20T01:02:03Z",
            "Fictional Draft Owner",
        )

    def test_reopen_is_idempotent_for_published_and_withdrawn_upgrade(
        self, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "phase6a-idempotent"
        baseline = _build_phase6a_release_database(data_dir)
        first = WorkbenchStore(data_dir=data_dir)
        with first.connect() as conn:
            first_packages = self._all_rows(
                conn, "client_release_packages", "release_id"
            )
            first_entries = self._all_rows(
                conn, "client_release_entries", "release_entry_id"
            )
            first_events = self._all_rows(
                conn, "engagement_audit_events", "event_id"
            )
        reopened = WorkbenchStore(data_dir=data_dir)
        with reopened.connect() as conn:
            assert self._all_rows(
                conn, "client_release_packages", "release_id"
            ) == first_packages
            assert self._all_rows(
                conn, "client_release_entries", "release_entry_id"
            ) == first_entries
            assert self._all_rows(
                conn, "engagement_audit_events", "event_id"
            ) == first_events
            assert tuple(conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-WITHDRAWN'"
            ).fetchone()) == baseline["withdrawn_package"]
            assert self._legacy_entries(
                conn, "REL-FIC-WITHDRAWN"
            ) == baseline["withdrawn_entries"]
            conn.execute(
                "UPDATE client_release_packages SET status = 'WITHDRAWN', "
                "withdrawn_at = '2026-08-19T12:00:00Z', "
                "withdrawn_by = 'Fictional Site Auditor', "
                "withdrawal_reason = 'Fictional terminal test' "
                "WHERE release_id = ?",
                (self._UPGRADE_ID,),
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-REL-FIC-PHASE6B1-UPGRADE-WITHDRAWN', "
                "'ENG-FIC-0001', 'RELEASE_WITHDRAWN', "
                "'2026-08-19T12:00:00Z', 'Fictional Site Auditor')"
            )
            terminal_packages = self._all_rows(
                conn, "client_release_packages", "release_id"
            )
            terminal_entries = self._all_rows(
                conn, "client_release_entries", "release_entry_id"
            )
            terminal_events = self._all_rows(
                conn, "engagement_audit_events", "event_id"
            )
        terminal_reopen = WorkbenchStore(data_dir=data_dir)
        with terminal_reopen.connect() as conn:
            assert self._all_rows(
                conn, "client_release_packages", "release_id"
            ) == terminal_packages
            assert self._all_rows(
                conn, "client_release_entries", "release_entry_id"
            ) == terminal_entries
            assert self._all_rows(
                conn, "engagement_audit_events", "event_id"
            ) == terminal_events

    def test_unrelated_newer_current_package_is_not_superseded(
        self, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "phase6a-unrelated-current"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
            conn.execute(
                "UPDATE client_release_packages SET status = 'WITHDRAWN', "
                "withdrawn_at = '2026-08-19T10:15:00Z', "
                "withdrawn_by = 'Fictional Phase 6A Auditor', "
                "withdrawal_reason = 'Fictional prior supersession' "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by, published_at, published_by) "
                "VALUES ('REL-FIC-UNRELATED-CURRENT', 'ENG-FIC-0001', 9, "
                "'PUBLISHED', '2026-08-20T00:00:00Z', "
                "'Fictional Other Auditor', '2026-08-20T01:00:00Z', "
                "'Fictional Other Auditor')"
            )
            expected_current = tuple(conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-UNRELATED-CURRENT'"
            ).fetchone())
        upgraded = WorkbenchStore(data_dir=data_dir)
        with upgraded.connect() as conn:
            current = tuple(conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE status = 'PUBLISHED' AND engagement_id = 'ENG-FIC-0001'"
            ).fetchone())
            upgrade_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM client_release_packages "
                "WHERE release_id = ?",
                (self._UPGRADE_ID,),
            ).fetchone()["cnt"]
        assert current == expected_current
        assert upgrade_count == 0


@pytest.mark.parametrize(
    "fault",
    (
        "wrong_package",
        "wrong_entry_id",
        "wrong_package_metadata",
        "wrong_source_metadata",
        "wrong_mate_id",
        "wrong_conclusion_type",
        "wrong_created_at",
        "wrong_creation_event",
        "wrong_publication_event",
    ),
)
def test_phase6a_lineage_requires_every_exact_fixed_base_value(
    tmp_path: Path, fault: str
) -> None:
    data_dir = tmp_path / f"phase6a-exact-lineage-{fault}"
    _build_phase6a_release_database(data_dir)
    mutations = {
        "wrong_package": (
            "UPDATE client_release_entries SET release_id = "
            "'REL-FIC-WITHDRAWN' WHERE release_entry_id = 'RLE-FIC-PUB-1'"
        ),
        "wrong_entry_id": (
            "UPDATE client_release_entries SET release_entry_id = "
            "'RLE-FIC-WRONG' WHERE release_entry_id = 'RLE-FIC-PUB-1'"
        ),
        "wrong_package_metadata": (
            "UPDATE client_release_packages SET created_by = 'Wrong Creator' "
            "WHERE release_id = 'REL-FIC-PUBLISHED'"
        ),
        "wrong_source_metadata": (
            "UPDATE conclusions SET title = 'Wrong approved title' "
            "WHERE conclusion_id = 'CON-FIC-0001'"
        ),
        "wrong_mate_id": (
            "UPDATE conclusions SET mate_id = 'MATE-FIC-0002' "
            "WHERE conclusion_id = 'CON-FIC-0001'"
        ),
        "wrong_conclusion_type": (
            "UPDATE conclusions SET conclusion_type = 'OTHER' "
            "WHERE conclusion_id = 'CON-FIC-0001'"
        ),
        "wrong_created_at": (
            "UPDATE conclusions SET created_at = '2026-08-13T00:00:00Z' "
            "WHERE conclusion_id = 'CON-FIC-0001'"
        ),
        "wrong_creation_event": (
            "UPDATE engagement_audit_events SET actor = 'Wrong Creator' "
            "WHERE event_id = 'EVT-REL-FIC-PUB-CREATED'"
        ),
        "wrong_publication_event": (
            "UPDATE engagement_audit_events SET event_id = "
            "'EVT-REL-FIC-WRONG-PUBLISHED' "
            "WHERE event_id = 'EVT-REL-FIC-PUB-PUBLISHED'"
        ),
    }
    with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
        conn.execute(mutations[fault])
    store = WorkbenchStore(data_dir=data_dir)
    if fault == "wrong_package":
        with store.connect() as conn:
            upgrade_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-PHASE6B1-UPGRADE'"
            ).fetchone()["cnt"]
        assert upgrade_count == 0
    else:
        with pytest.raises(
            sqlite3.IntegrityError,
            match="Source conclusion must be an APPROVED conclusion",
        ):
            store.connect()


class TestConclusionSourceValidation:
    """CONCLUSION entries must reference an APPROVED conclusion
    for the release's engagement at the captured version."""

    @staticmethod
    def _insert_draft_entry(
        conn: sqlite3.Connection,
        release_id: str,
        conclusion_id: str,
        version: int = 1,
        display_title: str = "Approved field capture conclusion",
        display_summary: str = (
            "The field capture control is suitably designed for "
            "fictional mobile evidence collection under the pilot scope."
        ),
        evidence_ref: str = "EVD-FIC-0001",
    ) -> None:
        conn.execute(
            "INSERT OR IGNORE INTO client_release_entries "
            "(release_entry_id, release_id, source_record_type, "
            " source_record_id, source_record_version, "
            " approved_evidence_reference_id, display_title, "
            " display_summary) "
            "VALUES (?, ?, 'CONCLUSION', ?, ?, ?, ?, ?)",
            (
                f"RLE-TEST-{conclusion_id}", release_id,
                conclusion_id, version,
                evidence_ref, display_title, display_summary,
            ),
        )

    # ── rejection tests ──────────────────────────────────────────

    def test_nonexistent_conclusion_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A CONCLUSION entry referencing a nonexistent conclusion
        must be rejected at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-c-nx")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-TEST-NX", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError):
                self._insert_draft_entry(
                    conn, "REL-TEST-NX", "CON-DOES-NOT-EXIST"
                )

    def test_unapproved_conclusion_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A CONCLUSION entry referencing a conclusion that is not
        APPROVED must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-c-ua")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO conclusions "
                "(conclusion_id, mate_id, status, title, "
                " engagement_id, evidence_id, version, "
                " conclusion_type, summary, created_at) "
                "VALUES (?, ?, 'CANDIDATE', ?, ?, ?, 1, "
                " 'CONCLUSION', ?, '2026-01-01')",
                ("CON-TEST-UN", "MATE-FIC-0001",
                 "Unapproved", "ENG-FIC-0001", "EVD-FIC-0001",
                 "Unapproved summary"),
            )
            _create_draft_package(conn, "REL-TEST-UA", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError):
                self._insert_draft_entry(
                    conn, "REL-TEST-UA", "CON-TEST-UN"
                )

    def test_cross_engagement_conclusion_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A CONCLUSION entry for a conclusion on a different
        engagement must be rejected."""
        d = tmp_path / "u-c-xe"
        _set_client_env(monkeypatch, d)
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO engagement_setups "
                "(engagement_id, creation_attempt_key) "
                "VALUES ('ENG-X-0002', 'key-x2')"
            )
            conn.execute(
                "INSERT OR IGNORE INTO conclusions "
                "(conclusion_id, mate_id, status, title, "
                " engagement_id, evidence_id, version, "
                " conclusion_type, summary, created_at) "
                "VALUES (?, ?, 'APPROVED', ?, ?, ?, 1, "
                " 'CONCLUSION', ?, '2026-01-01')",
                ("CON-TEST-XE", "MATE-FIC-0001",
                 "Cross Eng", "ENG-X-0002", "EVD-FIC-0001",
                 "Cross engagement summary"),
            )
            _create_draft_package(conn, "REL-TEST-XE", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError):
                self._insert_draft_entry(
                    conn, "REL-TEST-XE", "CON-TEST-XE"
                )

    def test_wrong_version_conclusion_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A CONCLUSION entry with a version that does not match the
        conclusion's version must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-c-wv")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-TEST-WV", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError):
                self._insert_draft_entry(
                    conn, "REL-TEST-WV", "CON-FIC-0001", version=999
                )

    # ── acceptance tests ─────────────────────────────────────────

    def test_valid_conclusion_accepted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A CONCLUSION entry referencing a valid APPROVED conclusion
        must be accepted at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-c-ok")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-TEST-OK", "ENG-FIC-0001")
            # This must not raise
            self._insert_draft_entry(
                conn, "REL-TEST-OK", "CON-FIC-0001"
            )
            _publish_draft_package(conn, "REL-TEST-OK", "ENG-FIC-0001")

    # ── non-regression tests ─────────────────────────────────────

    def test_action_validation_still_works(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """ACTION source validation must not be broken by adding
        the CONCLUSION trigger."""
        _set_client_env(monkeypatch, tmp_path / "u-c-act")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-TEST-ACT", "ENG-FIC-0001")
            # Non-matching action snapshot must still be rejected
            _insert_approved_action(
                conn, "ACT-TEST-VAL", "ENG-FIC-0001",
                "Desc A", "Owner A", "2026-12-31", "OPEN",
                "Auditor", "2026-01-01",
            )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT OR IGNORE INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    " source_record_id, source_record_version, "
                    " approved_evidence_reference_id, display_title, "
                    " display_summary, action_owner, action_target_date, "
                    " action_delivery_status) "
                    "VALUES (?, ?, 'ACTION', ?, ?,'EVD-FIC-0001',"
                    " 'T', 'Wrong desc', 'Owner A', '2026-12-31', 'OPEN')",
                    ("RLE-TEST-AVAL", "REL-TEST-ACT",
                     "ACT-TEST-VAL", 1),
                )

    def test_published_packages_unchanged(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Published and withdrawn packages must not be affected
        by adding the CONCLUSION validation trigger."""
        _set_client_env(monkeypatch, tmp_path / "u-c-pub")
        store = WorkbenchStore()
        with store.connect() as conn:
            pub_entries = conn.execute(
                "SELECT COUNT(*) as cnt FROM client_release_entries "
                "WHERE release_id = 'REL-FIC-PUBLISHED'"
            ).fetchone()["cnt"]
            wdn_entries = conn.execute(
                "SELECT COUNT(*) as cnt FROM client_release_entries "
                "WHERE release_id = 'REL-FIC-WITHDRAWN'"
            ).fetchone()["cnt"]
        # Re-open — upgrade must not change published/withdrawn data
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            assert (
                conn.execute(
                    "SELECT COUNT(*) as cnt FROM client_release_entries "
                    "WHERE release_id = 'REL-FIC-PUBLISHED'"
                ).fetchone()["cnt"]
                == pub_entries
            )
            assert (
                conn.execute(
                    "SELECT COUNT(*) as cnt FROM client_release_entries "
                    "WHERE release_id = 'REL-FIC-WITHDRAWN'"
                ).fetchone()["cnt"]
                == wdn_entries
            )

    # ── Phase 6B2: snapshot / attribution / audit-event validation ──
    #
    # The seeded EVT-CON-FIC-0001-APPROVED audit event is immutable
    # (engagement_audit_events has no-update/no-delete triggers) and
    # carries actor="Fictional Site Auditor", so the controlled
    # snapshot tests below build a *fresh* conclusion id whose matching
    # audit event can be inserted, omitted, or forged at will.  Only
    # test_published_snapshot_preserved_after_source_change reuses the
    # seeded CON-FIC-0001 deliberately.

    _SNAP_TITLE = "Approved field capture conclusion"
    _SNAP_SUMMARY = (
        "The field capture control is suitably designed for "
        "fictional mobile evidence collection under the pilot scope."
    )
    _SNAP_EVIDENCE = "EVD-FIC-0001"
    _SNAP_APPROVED_BY = "Auditor"
    _SNAP_APPROVED_AT = "2026-08-20T00:00:00Z"
    _SNAP_CONCLUSION_ID = "CON-VAL-0001"
    _SNAP_ENGAGEMENT_ID = "ENG-FIC-0001"

    @staticmethod
    def _insert_conclusion_row(
        conn: sqlite3.Connection,
        conclusion_id: str,
        engagement_id: str,
        title: str,
        summary: str,
        evidence_id: str,
        approved_by: str | None,
        approved_at: str | None,
    ) -> None:
        """Insert a single APPROVED conclusion row with a plain INSERT.

        Uses a fresh conclusion id (never the seeded CON-FIC-0001), so
        there is no primary-key conflict and any fixture error surfaces
        immediately.  No audit event is inserted here.
        """
        conn.execute(
            "INSERT INTO conclusions "
            "(conclusion_id, mate_id, status, title, engagement_id, "
            " evidence_id, version, conclusion_type, summary, "
            " approved_by, approved_at, created_at) "
            "VALUES (?, ?, 'APPROVED', ?, ?, ?, 1, 'CONCLUSION', "
            " ?, ?, ?, ?)",
            # created_at is NOT NULL, so it gets a fixed timestamp
            # independent of approved_at (which may be NULL/blank in the
            # attribution-rejection tests).
            (conclusion_id, "MATE-FIC-0001", title, engagement_id,
             evidence_id, summary, approved_by, approved_at,
             "2026-08-20T00:00:00Z"),
        )

    @staticmethod
    def _insert_approved_conclusion(
        conn: sqlite3.Connection,
        conclusion_id: str,
        engagement_id: str,
        title: str,
        summary: str,
        evidence_id: str,
        approved_by: str,
        approved_at: str,
    ) -> None:
        """Insert an APPROVED conclusion and its matching
        EVT-<conclusion_id>-APPROVED audit event so the insert-time
        validation trigger accepts a matching release entry.
        """
        TestConclusionSourceValidation._insert_conclusion_row(
            conn, conclusion_id, engagement_id, title, summary,
            evidence_id, approved_by, approved_at,
        )
        conn.execute(
            "INSERT INTO engagement_audit_events "
            "(event_id, engagement_id, event_type, recorded_at, actor) "
            "VALUES (?, ?, 'CONCLUSION_APPROVED', ?, ?)",
            (f"EVT-{conclusion_id}-APPROVED", engagement_id,
             approved_at, approved_by),
        )

    @staticmethod
    def _insert_audit_event(
        conn: sqlite3.Connection,
        event_id: str,
        engagement_id: str,
        event_type: str,
        recorded_at: str,
        actor: str,
    ) -> None:
        """Insert one engagement audit event with explicit values using
        a plain INSERT, so a test can forge a single mismatched
        attribute (event_id, engagement_id, event_type, actor, or
        recorded_at) in isolation.
        """
        conn.execute(
            "INSERT INTO engagement_audit_events "
            "(event_id, engagement_id, event_type, recorded_at, actor) "
            "VALUES (?, ?, ?, ?, ?)",
            (event_id, engagement_id, event_type, recorded_at, actor),
        )

    @staticmethod
    def _insert_conclusion_entry(
        conn: sqlite3.Connection,
        release_id: str,
        conclusion_id: str,
        display_title: str = "Approved field capture conclusion",
        display_summary: str = (
            "The field capture control is suitably designed for "
            "fictional mobile evidence collection under the pilot scope."
        ),
        evidence_ref: str = "EVD-FIC-0001",
        version: int = 1,
        release_entry_id: str | None = None,
    ) -> None:
        """Insert a CONCLUSION release entry with a plain INSERT (not
        INSERT OR IGNORE) so a validation failure raises IntegrityError
        rather than being silently skipped.
        """
        conn.execute(
            "INSERT INTO client_release_entries "
            "(release_entry_id, release_id, source_record_type, "
            " source_record_id, source_record_version, "
            " approved_evidence_reference_id, display_title, "
            " display_summary) "
            "VALUES (?, ?, 'CONCLUSION', ?, ?, ?, ?, ?)",
            (release_entry_id or f"RLE-VAL-{conclusion_id}",
             release_id, conclusion_id,
             version, evidence_ref, display_title, display_summary),
        )

    @staticmethod
    def _create_legacy_snapshot_package(
        conn: sqlite3.Connection,
        release_id: str,
        *,
        status: str,
        add_publish_event: bool = True,
        event_actor: str = "Legacy Publisher",
        event_time: str | None = None,
        event_id: str | None = None,
        published_at: str = "2026-08-20T00:00:00Z",
    ) -> None:
        """Create a legacy package whose conclusion snapshot differs
        from the current source. Current validation is reinstalled when
        the test reopens the database."""
        conn.execute(
            "DROP TRIGGER client_release_entries_validate_conclusion_source"
        )
        conn.execute(
            "DROP TRIGGER client_release_packages_validate_publish"
        )
        if status != "DRAFT":
            conn.execute(
                "DROP TRIGGER client_release_packages_auto_publish_event"
            )
        _create_draft_package(conn, release_id, "ENG-FIC-0001")
        conn.execute(
            "INSERT INTO client_release_entries "
            "(release_entry_id, release_id, source_record_type, "
            " source_record_id, source_record_version, "
            " approved_evidence_reference_id, display_title, "
            " display_summary) "
            "VALUES (?, ?, 'CONCLUSION', 'CON-FIC-0001', 1, "
            "'EVD-LEGACY-SNAPSHOT', 'Legacy released title', "
            "'Legacy released summary')",
            (f"RLE-{release_id}-LEGACY", release_id),
        )
        if status != "DRAFT":
            conn.execute(
                "UPDATE client_release_packages SET status = 'PUBLISHED', "
                "published_at = ?, published_by = 'Legacy Publisher' "
                "WHERE release_id = ?",
                (published_at, release_id),
            )
            if not add_publish_event:
                return
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, 'ENG-FIC-0001', 'RELEASE_PUBLISHED', ?, ?)",
                (
                    event_id or f"EVT-{release_id}-PUB",
                    event_time or published_at,
                    event_actor,
                ),
            )

    # ── snapshot mismatch rejections ─────────────────────────────

    def test_mismatched_title_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A release entry whose display_title differs from the
        conclusion title must be rejected at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-c-mt")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-MT", "ENG-FIC-0001")
            self._insert_approved_conclusion(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-MT", self._SNAP_CONCLUSION_ID,
                    display_title="Wrong Title",
                )

    def test_mismatched_summary_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A release entry whose display_summary differs from the
        conclusion summary must be rejected at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-c-ms")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-MS", "ENG-FIC-0001")
            self._insert_approved_conclusion(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-MS", self._SNAP_CONCLUSION_ID,
                    display_summary="Wrong summary",
                )

    def test_mismatched_evidence_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A release entry whose approved_evidence_reference_id differs
        from the conclusion evidence_id must be rejected at insert
        time."""
        _set_client_env(monkeypatch, tmp_path / "u-c-mev")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-MEV", "ENG-FIC-0001")
            self._insert_approved_conclusion(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-MEV", self._SNAP_CONCLUSION_ID,
                    evidence_ref="EVD-WRONG",
                )

    def test_arbitrary_mismatched_snapshot_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An arbitrary snapshot without source or release lineage is rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-c-arbitrary")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-ARBITRARY", "ENG-FIC-0001")
            self._insert_approved_conclusion(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-ARBITRARY", self._SNAP_CONCLUSION_ID,
                    display_title="Arbitrary title",
                    display_summary="Arbitrary summary",
                    evidence_ref="EVD-ARBITRARY",
                )

    def test_post_publication_injected_snapshot_cannot_create_lineage(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "u-c-post-publish-injection"
        _set_client_env(monkeypatch, data_dir)
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(
                conn, "REL-INJECTED-PRIOR", "ENG-FIC-0001"
            )
            self._insert_conclusion_entry(
                conn, "REL-INJECTED-PRIOR", "CON-FIC-0001",
                release_entry_id="RLE-INJECTED-VALID",
            )
            _publish_draft_package(
                conn, "REL-INJECTED-PRIOR", "ENG-FIC-0001"
            )
            conn.execute(
                "DROP TRIGGER client_release_entries_no_terminal_insert"
            )
            conn.execute(
                "DROP TRIGGER client_release_entries_one_conclusion"
            )
            conn.execute(
                "DROP TRIGGER client_release_entries_validate_conclusion_source"
            )
            conn.execute(
                "INSERT INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                "source_record_id, source_record_version, "
                "approved_evidence_reference_id, display_title, "
                "display_summary) VALUES ('RLE-INJECTED-ARBITRARY', "
                "'REL-INJECTED-PRIOR', 'CONCLUSION', 'CON-FIC-0001', 1, "
                "'EVD-INJECTED', 'Injected title', 'Injected summary')"
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            _create_draft_package(
                conn, "REL-INJECTED-CARRY", "ENG-FIC-0001"
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-INJECTED-CARRY", "CON-FIC-0001",
                    display_title="Injected title",
                    display_summary="Injected summary",
                    evidence_ref="EVD-INJECTED",
                    release_entry_id="RLE-INJECTED-CARRY",
                )

    def test_carry_forward_from_draft_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A matching snapshot in a DRAFT package gives no lineage."""
        data_dir = tmp_path / "u-c-lineage-draft"
        _set_client_env(monkeypatch, data_dir)
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_legacy_snapshot_package(
                conn, "REL-LEGACY-DRAFT", status="DRAFT"
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            _create_draft_package(conn, "REL-CARRY-DRAFT", "ENG-FIC-0001")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-CARRY-DRAFT", "CON-FIC-0001",
                    display_title="Legacy released title",
                    display_summary="Legacy released summary",
                    evidence_ref="EVD-LEGACY-SNAPSHOT",
                    release_entry_id="RLE-CARRY-DRAFT",
                )

    def test_carry_forward_without_publish_event_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A published package without its publication event gives no lineage."""
        data_dir = tmp_path / "u-c-lineage-missing-event"
        _set_client_env(monkeypatch, data_dir)
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_legacy_snapshot_package(
                conn, "REL-LEGACY-NO-EVENT", status="PUBLISHED",
                add_publish_event=False,
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            _create_draft_package(conn, "REL-CARRY-NO-EVENT", "ENG-FIC-0001")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-CARRY-NO-EVENT", "CON-FIC-0001",
                    display_title="Legacy released title",
                    display_summary="Legacy released summary",
                    evidence_ref="EVD-LEGACY-SNAPSHOT",
                    release_entry_id="RLE-CARRY-NO-EVENT",
                )

    @pytest.mark.parametrize(
        ("event_actor", "event_time"),
        (
            ("Wrong Publisher", "2026-08-20T00:00:00Z"),
            ("Legacy Publisher", "2026-08-20T00:00:01Z"),
        ),
    )
    def test_carry_forward_with_mismatched_publish_event_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        event_actor: str, event_time: str,
    ) -> None:
        """Publication actor and time must match the prior package."""
        suffix = event_actor.replace(" ", "-") + event_time[-3:-1]
        data_dir = tmp_path / f"u-c-lineage-mismatch-{suffix}"
        _set_client_env(monkeypatch, data_dir)
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_legacy_snapshot_package(
                conn, "REL-LEGACY-BAD-EVENT", status="PUBLISHED",
                event_actor=event_actor, event_time=event_time,
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            _create_draft_package(conn, "REL-CARRY-BAD-EVENT", "ENG-FIC-0001")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-CARRY-BAD-EVENT", "CON-FIC-0001",
                    display_title="Legacy released title",
                    display_summary="Legacy released summary",
                    evidence_ref="EVD-LEGACY-SNAPSHOT",
                    release_entry_id="RLE-CARRY-BAD-EVENT",
                )

    def test_different_package_event_with_same_metadata_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An event for another package cannot prove this lineage."""
        data_dir = tmp_path / "u-c-lineage-other-package-event"
        _set_client_env(monkeypatch, data_dir)
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_legacy_snapshot_package(
                conn, "REL-LEGACY-OTHER-EVENT", status="PUBLISHED",
                event_id="EVT-REL-DIFFERENT-PACKAGE-PUB",
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            _create_draft_package(conn, "REL-CARRY-OTHER-EVENT", "ENG-FIC-0001")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-CARRY-OTHER-EVENT", "CON-FIC-0001",
                    display_title="Legacy released title",
                    display_summary="Legacy released summary",
                    evidence_ref="EVD-LEGACY-SNAPSHOT",
                    release_entry_id="RLE-CARRY-OTHER-EVENT",
                )

    def test_wrong_lineage_publish_event_id_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A wrong event ID cannot prove a prior package publication."""
        data_dir = tmp_path / "u-c-lineage-wrong-event-id"
        _set_client_env(monkeypatch, data_dir)
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_legacy_snapshot_package(
                conn, "REL-LEGACY-WRONG-ID", status="PUBLISHED",
                event_id="EVT-WRONG-LINEAGE-ID",
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            _create_draft_package(conn, "REL-CARRY-WRONG-ID", "ENG-FIC-0001")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-CARRY-WRONG-ID", "CON-FIC-0001",
                    display_title="Legacy released title",
                    display_summary="Legacy released summary",
                    evidence_ref="EVD-LEGACY-SNAPSHOT",
                    release_entry_id="RLE-CARRY-WRONG-ID",
                )

    def test_arbitrary_prior_with_valid_current_event_id_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A current event ID cannot validate an arbitrary old snapshot."""
        data_dir = tmp_path / "u-c-lineage-current-event"
        _set_client_env(monkeypatch, data_dir)
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_legacy_snapshot_package(
                conn, "REL-LEGACY-CURRENT-ID", status="PUBLISHED"
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            _create_draft_package(conn, "REL-CARRY-CURRENT-ID", "ENG-FIC-0001")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-CARRY-CURRENT-ID", "CON-FIC-0001",
                    display_title="Legacy released title",
                    display_summary="Legacy released summary",
                    evidence_ref="EVD-LEGACY-SNAPSHOT",
                    release_entry_id="RLE-CARRY-CURRENT-ID",
                )
            package_status = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-CARRY-CURRENT-ID'"
            ).fetchone()["status"]
        assert package_status == "DRAFT"

    def test_nonexact_future_lineage_is_rejected_before_publication(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A later prior publication cannot support an earlier release."""
        data_dir = tmp_path / "u-c-lineage-future"
        _set_client_env(monkeypatch, data_dir)
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_legacy_snapshot_package(
                conn, "REL-LEGACY-FUTURE", status="PUBLISHED",
                published_at="2026-08-21T00:00:00Z",
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            conn.execute(
                "UPDATE client_release_packages SET status = 'WITHDRAWN', "
                "withdrawn_at = '2026-08-22T00:00:00Z', "
                "withdrawn_by = 'Legacy Publisher', "
                "withdrawal_reason = 'Fictional chronology test' "
                "WHERE release_id = 'REL-LEGACY-FUTURE'"
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-REL-LEGACY-FUTURE-WDN', 'ENG-FIC-0001', "
                "'RELEASE_WITHDRAWN', '2026-08-22T00:00:00Z', "
                "'Legacy Publisher')"
            )
            _create_draft_package(conn, "REL-CARRY-EARLY", "ENG-FIC-0001")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-CARRY-EARLY", "CON-FIC-0001",
                    display_title="Legacy released title",
                    display_summary="Legacy released summary",
                    evidence_ref="EVD-LEGACY-SNAPSHOT",
                    release_entry_id="RLE-CARRY-EARLY",
                )
            package_status = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-CARRY-EARLY'"
            ).fetchone()["status"]
            publish_event_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-CARRY-EARLY-PUB'"
            ).fetchone()["cnt"]
        assert package_status == "DRAFT"
        assert publish_event_count == 0

    # ── approval attribution rejections ─────────────────────────

    def test_null_approval_attribution_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A conclusion with NULL approved_by/approved_at must be
        rejected: the TRIM(COALESCE(..., '')) <> '' guard fails before
        the audit-event check is reached."""
        _set_client_env(monkeypatch, tmp_path / "u-c-na")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-NA", "ENG-FIC-0001")
            self._insert_conclusion_row(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                None, None,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-NA", self._SNAP_CONCLUSION_ID,
                )

    def test_blank_approval_attribution_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A conclusion with empty-string approved_by/approved_at must
        be rejected by the nonblank attribution guard."""
        _set_client_env(monkeypatch, tmp_path / "u-c-bl")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-BL", "ENG-FIC-0001")
            self._insert_conclusion_row(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                "", "",
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-BL", self._SNAP_CONCLUSION_ID,
                )

    @pytest.mark.parametrize("whitespace", ("\t", "\n", "\v", "\f", "\r"))
    def test_whitespace_approval_attribution_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, whitespace: str,
    ) -> None:
        """A conclusion with whitespace-only approved_by/approved_at
        must be rejected: TRIM collapses them to the empty string."""
        _set_client_env(monkeypatch, tmp_path / "u-c-ws")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-WS", "ENG-FIC-0001")
            self._insert_conclusion_row(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                whitespace, whitespace,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-WS", self._SNAP_CONCLUSION_ID,
                )

    # ── audit-event rejections ───────────────────────────────────

    def test_missing_approval_event_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A conclusion with valid attribution but no matching
        EVT-<conclusion_id>-APPROVED audit event must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-c-mae")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-MAE", "ENG-FIC-0001")
            self._insert_conclusion_row(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            # No EVT-CON-VAL-0001-APPROVED audit event is inserted.
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-MAE", self._SNAP_CONCLUSION_ID,
                )

    def test_wrong_event_id_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An audit event with the wrong event_id must be rejected: the
        trigger requires EVT-<conclusion_id>-APPROVED exactly."""
        _set_client_env(monkeypatch, tmp_path / "u-c-weid")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-WEID", "ENG-FIC-0001")
            self._insert_conclusion_row(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            self._insert_audit_event(
                conn, "EVT-WRONG-ID", self._SNAP_ENGAGEMENT_ID,
                "CONCLUSION_APPROVED", self._SNAP_APPROVED_AT,
                self._SNAP_APPROVED_BY,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-WEID", self._SNAP_CONCLUSION_ID,
                )

    def test_wrong_event_engagement_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An audit event whose engagement_id differs from the
        conclusion's engagement must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-c-weng")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-WENG", "ENG-FIC-0001")
            self._insert_conclusion_row(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            # ENG-FIC-0002 is seeded, so the FK is satisfied, but it is
            # not the conclusion's engagement.
            self._insert_audit_event(
                conn, f"EVT-{self._SNAP_CONCLUSION_ID}-APPROVED",
                "ENG-FIC-0002", "CONCLUSION_APPROVED",
                self._SNAP_APPROVED_AT, self._SNAP_APPROVED_BY,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-WENG", self._SNAP_CONCLUSION_ID,
                )

    def test_wrong_event_type_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An audit event with the wrong event_type must be rejected:
        the trigger requires CONCLUSION_APPROVED exactly."""
        _set_client_env(monkeypatch, tmp_path / "u-c-wet")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-WET", "ENG-FIC-0001")
            self._insert_conclusion_row(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            self._insert_audit_event(
                conn, f"EVT-{self._SNAP_CONCLUSION_ID}-APPROVED",
                self._SNAP_ENGAGEMENT_ID, "RELEASE_PUBLISHED",
                self._SNAP_APPROVED_AT, self._SNAP_APPROVED_BY,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-WET", self._SNAP_CONCLUSION_ID,
                )

    def test_wrong_event_actor_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An audit event whose actor differs from the conclusion's
        approved_by must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-c-wea")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-WEA", "ENG-FIC-0001")
            self._insert_conclusion_row(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            self._insert_audit_event(
                conn, f"EVT-{self._SNAP_CONCLUSION_ID}-APPROVED",
                self._SNAP_ENGAGEMENT_ID, "CONCLUSION_APPROVED",
                self._SNAP_APPROVED_AT, "Wrong Person",
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-WEA", self._SNAP_CONCLUSION_ID,
                )

    def test_wrong_event_recorded_at_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An audit event whose recorded_at differs from the
        conclusion's approved_at must be rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-c-wer")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-WER", "ENG-FIC-0001")
            self._insert_conclusion_row(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            self._insert_audit_event(
                conn, f"EVT-{self._SNAP_CONCLUSION_ID}-APPROVED",
                self._SNAP_ENGAGEMENT_ID, "CONCLUSION_APPROVED",
                "2020-01-01T00:00:00Z", self._SNAP_APPROVED_BY,
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source conclusion must be an APPROVED conclusion",
            ):
                self._insert_conclusion_entry(
                    conn, "REL-VAL-WER", self._SNAP_CONCLUSION_ID,
                )

    # ── acceptance tests ─────────────────────────────────────────

    def test_exact_snapshot_accepted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A release entry whose snapshot exactly matches an APPROVED
        conclusion with a matching audit event must be accepted."""
        _set_client_env(monkeypatch, tmp_path / "u-c-snap-ok")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-OK", "ENG-FIC-0001")
            self._insert_approved_conclusion(
                conn, self._SNAP_CONCLUSION_ID, self._SNAP_ENGAGEMENT_ID,
                self._SNAP_TITLE, self._SNAP_SUMMARY, self._SNAP_EVIDENCE,
                self._SNAP_APPROVED_BY, self._SNAP_APPROVED_AT,
            )
            # Must not raise.
            self._insert_conclusion_entry(
                conn, "REL-VAL-OK", self._SNAP_CONCLUSION_ID,
            )
            row = conn.execute(
                "SELECT display_title, display_summary, "
                " approved_evidence_reference_id "
                "FROM client_release_entries "
                "WHERE release_entry_id = ?",
                (f"RLE-VAL-{self._SNAP_CONCLUSION_ID}",),
            ).fetchone()
            assert row is not None
            assert row["display_title"] == self._SNAP_TITLE
            assert row["display_summary"] == self._SNAP_SUMMARY
            assert (
                row["approved_evidence_reference_id"]
                == self._SNAP_EVIDENCE
            )

    def test_published_snapshot_preserved_after_source_change(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Once a release entry is published, mutating the source
        conclusion's title, summary and evidence must not change the
        captured snapshot.

        This deliberately reuses the seeded CON-FIC-0001 (whose matching
        EVT-CON-FIC-0001-APPROVED audit event is immutable) rather than
        the fresh controlled id, because it exercises the publish-then-
        mutate path against real seeded data.
        """
        _set_client_env(monkeypatch, tmp_path / "u-c-snap")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-VAL-SNAP", "ENG-FIC-0001")
            # Snapshot exactly matches the seeded CON-FIC-0001.
            self._insert_conclusion_entry(
                conn, "REL-VAL-SNAP", "CON-FIC-0001",
            )
            _publish_draft_package(
                conn, "REL-VAL-SNAP", "ENG-FIC-0001",
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Approved conclusions cannot be updated",
            ):
                conn.execute(
                    "UPDATE conclusions "
                    "SET title = 'Changed conclusion title', "
                    "    summary = 'Changed summary text', "
                    "    evidence_id = 'EVD-CHANGED-0001' "
                    "WHERE conclusion_id = 'CON-FIC-0001'",
                )
            row = conn.execute(
                "SELECT display_title, display_summary, "
                " approved_evidence_reference_id "
                "FROM client_release_entries "
                "WHERE release_entry_id = ?",
                ("RLE-VAL-CON-FIC-0001",),
            ).fetchone()
            assert row is not None
            assert row["display_title"] == self._SNAP_TITLE
            assert row["display_summary"] == self._SNAP_SUMMARY
            assert (
                row["approved_evidence_reference_id"]
                == self._SNAP_EVIDENCE
            )


# ── Release creation identity and conclusion cardinality ───────


class TestReleaseCreationAndConclusionCardinality:
    """Publication needs exact creation identity and one conclusion."""

    @staticmethod
    def _insert_valid_conclusion(
        conn: sqlite3.Connection, release_id: str, entry_id: str
    ) -> None:
        _insert_legacy_conclusion_release_entry(
            conn, entry_id, release_id, "CON-FIC-0001"
        )

    @staticmethod
    def _assert_failed_publication(
        conn: sqlite3.Connection, release_id: str
    ) -> None:
        status = conn.execute(
            "SELECT status FROM client_release_packages WHERE release_id = ?",
            (release_id,),
        ).fetchone()["status"]
        publish_events = conn.execute(
            "SELECT COUNT(*) AS cnt FROM engagement_audit_events "
            "WHERE event_id = ?",
            (f"EVT-{release_id}-PUB",),
        ).fetchone()["cnt"]
        assert status == "DRAFT"
        assert publish_events == 0

    def test_missing_creation_event_blocks_publication(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-release-created-missing")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(
                conn, "REL-CREATED-MISSING", "ENG-FIC-0001",
                add_created_event=False,
            )
            self._insert_valid_conclusion(
                conn, "REL-CREATED-MISSING", "RLE-CREATED-MISSING"
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="matching RELEASE_CREATED audit event",
            ):
                _publish_draft_package(
                    conn, "REL-CREATED-MISSING", "ENG-FIC-0001"
                )
            self._assert_failed_publication(conn, "REL-CREATED-MISSING")

    def test_wrong_creation_event_id_blocks_publication(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-release-created-wrong-id")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(
                conn, "REL-CREATED-WRONG-ID", "ENG-FIC-0001",
                add_created_event=False,
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-WRONG-CREATED', 'ENG-FIC-0001', "
                "'RELEASE_CREATED', '2026-08-20T00:00:00Z', 'Test')"
            )
            self._insert_valid_conclusion(
                conn, "REL-CREATED-WRONG-ID", "RLE-CREATED-WRONG-ID"
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="matching RELEASE_CREATED audit event",
            ):
                _publish_draft_package(
                    conn, "REL-CREATED-WRONG-ID", "ENG-FIC-0001"
                )
            self._assert_failed_publication(conn, "REL-CREATED-WRONG-ID")

    def test_other_package_creation_event_blocks_publication(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-release-created-other")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(
                conn, "REL-CREATED-OTHER", "ENG-FIC-0001",
                add_created_event=False,
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-REL-DIFFERENT-CREATED', 'ENG-FIC-0001', "
                "'RELEASE_CREATED', '2026-08-20T00:00:00Z', 'Test')"
            )
            self._insert_valid_conclusion(
                conn, "REL-CREATED-OTHER", "RLE-CREATED-OTHER"
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="matching RELEASE_CREATED audit event",
            ):
                _publish_draft_package(
                    conn, "REL-CREATED-OTHER", "ENG-FIC-0001"
                )
            self._assert_failed_publication(conn, "REL-CREATED-OTHER")

    def test_deterministic_creation_event_allows_publication(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-release-created-current")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(
                conn, "REL-CREATED-CURRENT", "ENG-FIC-0001"
            )
            self._insert_valid_conclusion(
                conn, "REL-CREATED-CURRENT", "RLE-CREATED-CURRENT"
            )
            _publish_draft_package(
                conn, "REL-CREATED-CURRENT", "ENG-FIC-0001"
            )
            status = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-CREATED-CURRENT'"
            ).fetchone()["status"]
        assert status == "PUBLISHED"

    @pytest.mark.parametrize(
        ("release_id", "legacy_event_id"),
        (
            ("REL-FIC-PUBLISHED", "EVT-REL-FIC-PUB-CREATED"),
        ),
    )
    def test_exact_phase6a_creation_event_mappings_allow_publication(
        self, tmp_path: Path, release_id: str, legacy_event_id: str
    ) -> None:
        data_dir = tmp_path / f"u-release-created-{release_id.lower()}"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
            conn.execute(
                "UPDATE conclusions SET title = "
                "'Approved field capture conclusion' "
                "WHERE conclusion_id = 'CON-FIC-0001'"
            )
            if release_id != "REL-FIC-PUBLISHED":
                conn.execute(
                    "UPDATE client_release_packages SET status = 'WITHDRAWN', "
                    "withdrawn_at = '2026-08-19T10:15:00Z', "
                    "withdrawn_by = 'Fictional Site Auditor', "
                    "withdrawal_reason = 'Fictional test setup' "
                    "WHERE release_id = 'REL-FIC-PUBLISHED'"
                )
            conn.execute(
                "UPDATE client_release_packages SET status = 'DRAFT', "
                "published_at = NULL, published_by = NULL, "
                "withdrawn_at = NULL, withdrawn_by = NULL, "
                "withdrawal_reason = NULL WHERE release_id = ?",
                (release_id,),
            )
        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            creation_event = conn.execute(
                "SELECT event_type FROM engagement_audit_events "
                "WHERE event_id = ?",
                (legacy_event_id,),
            ).fetchone()
            status = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = ?",
                (release_id,),
            ).fetchone()["status"]
        assert creation_event["event_type"] == "RELEASE_CREATED"
        assert status == "PUBLISHED"

    def test_second_conclusion_insert_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-one-conclusion-insert")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(
                conn, "REL-ONE-CONCLUSION", "ENG-FIC-0001"
            )
            self._insert_valid_conclusion(
                conn, "REL-ONE-CONCLUSION", "RLE-ONE-CONCLUSION-1"
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="already contains a conclusion",
            ):
                self._insert_valid_conclusion(
                    conn, "REL-ONE-CONCLUSION", "RLE-ONE-CONCLUSION-2"
                )
            count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM client_release_entries "
                "WHERE release_id = 'REL-ONE-CONCLUSION' "
                "AND source_record_type = 'CONCLUSION'"
            ).fetchone()["cnt"]
        assert count == 1

    def test_legacy_draft_with_two_conclusions_cannot_publish(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "u-one-conclusion-legacy"
        _set_client_env(monkeypatch, data_dir)
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(
                conn, "REL-TWO-CONCLUSIONS", "ENG-FIC-0001"
            )
            self._insert_valid_conclusion(
                conn, "REL-TWO-CONCLUSIONS", "RLE-TWO-CONCLUSIONS-1"
            )
            conn.execute(
                "DROP TRIGGER client_release_entries_one_conclusion"
            )
            self._insert_valid_conclusion(
                conn, "REL-TWO-CONCLUSIONS", "RLE-TWO-CONCLUSIONS-2"
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            with pytest.raises(
                sqlite3.IntegrityError,
                match="cannot contain more than one conclusion",
            ):
                _publish_draft_package(
                    conn, "REL-TWO-CONCLUSIONS", "ENG-FIC-0001"
                )
            self._assert_failed_publication(conn, "REL-TWO-CONCLUSIONS")

    def test_one_conclusion_and_multiple_actions_can_publish(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-one-conclusion-actions")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(
                conn, "REL-CONCLUSION-ACTIONS", "ENG-FIC-0001"
            )
            self._insert_valid_conclusion(
                conn, "REL-CONCLUSION-ACTIONS", "RLE-CONCLUSION-ACTIONS"
            )
            for suffix in ("A", "B"):
                _insert_approved_action(
                    conn, f"ACT-MULTI-{suffix}", "ENG-FIC-0001",
                    f"Fictional action {suffix}", "Fictional Owner",
                    "2026-12-31", "OPEN", "Fictional Approver",
                    "2026-08-20T00:00:00Z",
                )
                _insert_action_release_entry(
                    conn, f"RLE-MULTI-{suffix}",
                    "REL-CONCLUSION-ACTIONS", f"ACT-MULTI-{suffix}",
                    display_summary=f"Fictional action {suffix}",
                    action_owner="Fictional Owner",
                )
            _publish_draft_package(
                conn, "REL-CONCLUSION-ACTIONS", "ENG-FIC-0001"
            )
            counts = {
                row["source_record_type"]: row["cnt"]
                for row in conn.execute(
                    "SELECT source_record_type, COUNT(*) AS cnt "
                    "FROM client_release_entries "
                    "WHERE release_id = 'REL-CONCLUSION-ACTIONS' "
                    "GROUP BY source_record_type"
                )
            }
        assert counts == {"ACTION": 2, "CONCLUSION": 1}

    def test_reopen_recreates_one_conclusion_trigger(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-one-conclusion-reopen")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_entries_one_conclusion"
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM sqlite_master "
                "WHERE type = 'trigger' "
                "AND name = 'client_release_entries_one_conclusion'"
            ).fetchone()["cnt"]
        assert count == 1


# ── Phase 6B1: approved conclusion immutability ─────────────────


class TestApprovedConclusionImmutability:
    """Approved conclusions are fixed source records."""

    _TRIGGER_NAMES = {
        "conclusions_no_update_after_approval",
        "conclusions_no_delete_after_approval",
    }

    def test_approved_conclusion_update_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-ci-update")
        store = WorkbenchStore()
        with store.connect() as conn:
            before = tuple(conn.execute(
                "SELECT * FROM conclusions "
                "WHERE conclusion_id = 'CON-FIC-0001'"
            ).fetchone())
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Approved conclusions cannot be updated",
            ):
                conn.execute(
                    "UPDATE conclusions SET title = 'Changed title' "
                    "WHERE conclusion_id = 'CON-FIC-0001'"
                )
            after = tuple(conn.execute(
                "SELECT * FROM conclusions "
                "WHERE conclusion_id = 'CON-FIC-0001'"
            ).fetchone())
        assert after == before

    def test_approved_conclusion_delete_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-ci-delete")
        store = WorkbenchStore()
        with store.connect() as conn:
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Approved conclusions cannot be deleted",
            ):
                conn.execute(
                    "DELETE FROM conclusions "
                    "WHERE conclusion_id = 'CON-FIC-0001'"
                )
            status = conn.execute(
                "SELECT status FROM conclusions "
                "WHERE conclusion_id = 'CON-FIC-0001'"
            ).fetchone()["status"]
        assert status == "APPROVED"

    def test_candidate_conclusion_update_allowed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-ci-candidate")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "UPDATE conclusions SET title = 'Revised fictional draft', "
                "summary = 'Revised fictional candidate summary' "
                "WHERE conclusion_id = 'CON-FIC-STALE'"
            )
            row = conn.execute(
                "SELECT status, title, summary FROM conclusions "
                "WHERE conclusion_id = 'CON-FIC-STALE'"
            ).fetchone()
        assert tuple(row) == (
            "CANDIDATE", "Revised fictional draft",
            "Revised fictional candidate summary",
        )

    def test_fresh_database_has_both_lock_triggers(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-ci-fresh")
        store = WorkbenchStore()
        with store.connect() as conn:
            names = {
                row["name"] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                    "AND name LIKE 'conclusions_no_%_after_approval'"
                )
            }
        assert names == self._TRIGGER_NAMES

    def test_reopen_recreates_both_lock_triggers(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-ci-reopen")
        store = WorkbenchStore()
        with store.connect() as conn:
            for trigger_name in self._TRIGGER_NAMES:
                conn.execute(f"DROP TRIGGER {trigger_name}")
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            names = {
                row["name"] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                    "AND name LIKE 'conclusions_no_%_after_approval'"
                )
            }
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Approved conclusions cannot be updated",
            ):
                conn.execute(
                    "UPDATE conclusions SET title = 'Changed title' "
                    "WHERE conclusion_id = 'CON-FIC-0001'"
                )
        assert names == self._TRIGGER_NAMES

    def test_repeated_initialisation_is_idempotent(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "u-ci-idempotent")
        first = WorkbenchStore()
        with first.connect() as conn:
            before_conclusions = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM conclusions ORDER BY conclusion_id"
                ).fetchall()
            ]
            before_events = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM engagement_audit_events ORDER BY event_id"
                ).fetchall()
            ]
        WorkbenchStore()
        third = WorkbenchStore()
        with third.connect() as conn:
            after_conclusions = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM conclusions ORDER BY conclusion_id"
                ).fetchall()
            ]
            after_events = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM engagement_audit_events ORDER BY event_id"
                ).fetchall()
            ]
            trigger_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM sqlite_master "
                "WHERE type = 'trigger' "
                "AND name LIKE 'conclusions_no_%_after_approval'"
            ).fetchone()["cnt"]
        assert after_conclusions == before_conclusions
        assert after_events == before_events
        assert trigger_count == 2


# ── Phase 6B1: ACTION validation trigger negative tests ─────────


class TestActionValidationTrigger:
    """Explicit negative tests for the
    client_release_entries_validate_action_source BEFORE INSERT
    trigger.

    Every rejection here must fire at INSERT time (not at publish
    time) so a malformed ACTION entry can never reach a DRAFT
    package.  Test-specific records use plain INSERT so a validation
    failure raises rather than being silently skipped by INSERT OR
    IGNORE."""

    # ── snapshot nonblank field rejections ───────────────────────

    def test_blank_owner_rejected_at_insert(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """1. A blank owner is rejected at insert time, not at publish."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-blank-owner")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-VT-BLANK-OWN", "ENG-FIC-0001",
                "Blank owner action", "", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-VT-BLANK-OWN", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-BLANK-OWN", "REL-VT-BLANK-OWN",
                    "ACT-VT-BLANK-OWN",
                    display_summary="Blank owner action",
                    action_owner="",
                )

    @pytest.mark.parametrize("whitespace", ("\t", "\n", "\v", "\f", "\r"))
    def test_whitespace_owner_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, whitespace: str,
    ) -> None:
        """2. A whitespace-only owner is rejected at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-ws-owner")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-VT-WS-OWN", "ENG-FIC-0001",
                "Whitespace owner action", whitespace, "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-VT-WS-OWN", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-WS-OWN", "REL-VT-WS-OWN",
                    "ACT-VT-WS-OWN",
                    display_summary="Whitespace owner action",
                    action_owner=whitespace,
                )

    @pytest.mark.parametrize(
        ("display_title", "description", "evidence_ref"),
        (
            ("\t", "ASCII display action", "EVD-FIC-0001"),
            ("Action title", "\t", "EVD-FIC-0001"),
            ("Action title", "ASCII display action", "\t"),
        ),
    )
    def test_ascii_whitespace_display_fields_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        display_title: str, description: str, evidence_ref: str,
    ) -> None:
        """Required ACTION display fields reject ASCII whitespace."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-ascii-display")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-VT-ASCII-DISPLAY", "ENG-FIC-0001", description,
                "Owner", "2026-12-31", "OPEN", "Auditor",
                "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-VT-ASCII-DISPLAY", "ENG-FIC-0001")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source action must be an APPROVED action",
            ):
                _insert_action_release_entry(
                    conn, "RLE-VT-ASCII-DISPLAY", "REL-VT-ASCII-DISPLAY",
                    "ACT-VT-ASCII-DISPLAY", display_title=display_title,
                    display_summary=description, evidence_ref=evidence_ref,
                )

    # ── approval attribution rejections ─────────────────────────

    def test_null_action_approval_attribution_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """3. NULL approved_by/approved_at is rejected at insert time."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-null-attr")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-VT-NULL-ATTR", "ENG-FIC-0001",
                "Null attribution action", "Owner", "2026-12-31", "OPEN",
                None, None,
            )
            _create_draft_package(conn, "REL-VT-NULL-ATTR", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-NULL-ATTR", "REL-VT-NULL-ATTR",
                    "ACT-VT-NULL-ATTR",
                    display_summary="Null attribution action",
                )

    def test_blank_action_approval_attribution_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """4. Blank approved_by/approved_at is rejected at insert time.

        A matching blank audit event is supplied so the only failing
        condition is the nonblank attribution check."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-blank-attr")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-VT-BLANK-ATTR", "ENG-FIC-0001",
                "Blank attribution action", "Owner", "2026-12-31", "OPEN",
                "", "",
            )
            _insert_action_audit_event(
                conn, "EVT-ACT-VT-BLANK-ATTR-APPROVED", "ENG-FIC-0001",
                "ACTION_APPROVED", "", "",
            )
            _create_draft_package(conn, "REL-VT-BLANK-ATTR", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-BLANK-ATTR", "REL-VT-BLANK-ATTR",
                    "ACT-VT-BLANK-ATTR",
                    display_summary="Blank attribution action",
                )

    @pytest.mark.parametrize("whitespace", ("\t", "\n", "\v", "\f", "\r"))
    def test_whitespace_action_approval_attribution_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, whitespace: str,
    ) -> None:
        """5. Whitespace-only approved_by/approved_at is rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-ws-attr")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-VT-WS-ATTR", "ENG-FIC-0001",
                "Whitespace attribution action", "Owner",
                "2026-12-31", "OPEN", whitespace, whitespace,
            )
            _insert_action_audit_event(
                conn, "EVT-ACT-VT-WS-ATTR-APPROVED", "ENG-FIC-0001",
                "ACTION_APPROVED", whitespace, whitespace,
            )
            _create_draft_package(conn, "REL-VT-WS-ATTR", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-WS-ATTR", "REL-VT-WS-ATTR",
                    "ACT-VT-WS-ATTR",
                    display_summary="Whitespace attribution action",
                )

    # ── audit event matching rejections ─────────────────────────

    def test_missing_action_approval_event_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """6. A valid action with no EVT-<id>-APPROVED event is rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-miss-evt")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-VT-MISS-EVT", "ENG-FIC-0001",
                "Missing event action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-VT-MISS-EVT", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-MISS-EVT", "REL-VT-MISS-EVT",
                    "ACT-VT-MISS-EVT",
                    display_summary="Missing event action",
                )

    def test_wrong_action_event_id_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """7. An audit event with the wrong event_id is rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-wrong-eid")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-VT-WRONG-EID", "ENG-FIC-0001",
                "Wrong event id action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _insert_action_audit_event(
                conn, "EVT-ACT-VT-WRONG-EID-BOGUS", "ENG-FIC-0001",
                "ACTION_APPROVED", "2026-08-20T00:00:00Z", "Auditor",
            )
            _create_draft_package(conn, "REL-VT-WRONG-EID", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-WRONG-EID", "REL-VT-WRONG-EID",
                    "ACT-VT-WRONG-EID",
                    display_summary="Wrong event id action",
                )

    def test_wrong_action_event_engagement_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """8. An audit event with the wrong engagement is rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-wrong-eng")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-VT-WRONG-ENG", "ENG-FIC-0001",
                "Wrong engagement event action", "Owner",
                "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _insert_action_audit_event(
                conn, "EVT-ACT-VT-WRONG-ENG-APPROVED", "ENG-FIC-0002",
                "ACTION_APPROVED", "2026-08-20T00:00:00Z", "Auditor",
            )
            _create_draft_package(conn, "REL-VT-WRONG-ENG", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-WRONG-ENG", "REL-VT-WRONG-ENG",
                    "ACT-VT-WRONG-ENG",
                    display_summary="Wrong engagement event action",
                )

    def test_wrong_action_event_type_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """9. An audit event with the wrong event_type is rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-wrong-etype")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-VT-WRONG-ETYPE", "ENG-FIC-0001",
                "Wrong event type action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _insert_action_audit_event(
                conn, "EVT-ACT-VT-WRONG-ETYPE-APPROVED", "ENG-FIC-0001",
                "CONCLUSION_APPROVED", "2026-08-20T00:00:00Z", "Auditor",
            )
            _create_draft_package(conn, "REL-VT-WRONG-ETYPE", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-WRONG-ETYPE", "REL-VT-WRONG-ETYPE",
                    "ACT-VT-WRONG-ETYPE",
                    display_summary="Wrong event type action",
                )

    def test_wrong_action_event_actor_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """10. An audit event whose actor != approved_by is rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-wrong-actor")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-VT-WRONG-ACTOR", "ENG-FIC-0001",
                "Wrong actor event action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _insert_action_audit_event(
                conn, "EVT-ACT-VT-WRONG-ACTOR-APPROVED", "ENG-FIC-0001",
                "ACTION_APPROVED", "2026-08-20T00:00:00Z",
                "Wrong Actor",
            )
            _create_draft_package(conn, "REL-VT-WRONG-ACTOR", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-WRONG-ACTOR", "REL-VT-WRONG-ACTOR",
                    "ACT-VT-WRONG-ACTOR",
                    display_summary="Wrong actor event action",
                )

    def test_wrong_action_event_recorded_at_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """11. An audit event whose recorded_at != approved_at is rejected."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-wrong-rat")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-VT-WRONG-RAT", "ENG-FIC-0001",
                "Wrong recorded_at event action", "Owner",
                "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _insert_action_audit_event(
                conn, "EVT-ACT-VT-WRONG-RAT-APPROVED", "ENG-FIC-0001",
                "ACTION_APPROVED", "2026-08-21T00:00:00Z", "Auditor",
            )
            _create_draft_package(conn, "REL-VT-WRONG-RAT", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-WRONG-RAT", "REL-VT-WRONG-RAT",
                    "ACT-VT-WRONG-RAT",
                    display_summary="Wrong recorded_at event action",
                )

    # ── acceptance / side-effect tests ──────────────────────────

    def test_exact_action_snapshot_accepted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """12. An exact snapshot match with a matching audit event is
        accepted at insert time and survives publication."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-exact")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-VT-EXACT", "ENG-FIC-0001",
                "Exact snapshot action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-VT-EXACT", "ENG-FIC-0001")
            # Must not raise — snapshot and audit event both match.
            _insert_action_release_entry(
                conn, "RLE-VT-EXACT", "REL-VT-EXACT", "ACT-VT-EXACT",
                display_summary="Exact snapshot action",
            )
            _publish_draft_package(conn, "REL-VT-EXACT", "ENG-FIC-0001")
            row = conn.execute(
                "SELECT source_record_id, action_owner, action_target_date, "
                "action_delivery_status FROM client_release_entries "
                "WHERE release_entry_id = 'RLE-VT-EXACT'"
            ).fetchone()
            assert row is not None
            assert row["source_record_id"] == "ACT-VT-EXACT"

    def test_rejected_entry_leaves_package_draft(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """13. After a rejected insert the package stays DRAFT with no
        new entries."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-rej-draft")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-VT-REJ-DRAFT", "ENG-FIC-0001",
                "Rejection draft action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-VT-REJ-DRAFT", "ENG-FIC-0001")
            conn.commit()
            entries_before = conn.execute(
                "SELECT COUNT(*) AS cnt FROM client_release_entries "
                "WHERE release_id = 'REL-VT-REJ-DRAFT'"
            ).fetchone()["cnt"]
            # Snapshot mismatch (display_summary) -> rejected at insert.
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-REJ-DRAFT", "REL-VT-REJ-DRAFT",
                    "ACT-VT-REJ-DRAFT",
                    display_summary="WRONG summary does not match",
                )
            conn.rollback()
            pkg = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-VT-REJ-DRAFT'"
            ).fetchone()
            assert pkg["status"] == "DRAFT"
            entries_after = conn.execute(
                "SELECT COUNT(*) AS cnt FROM client_release_entries "
                "WHERE release_id = 'REL-VT-REJ-DRAFT'"
            ).fetchone()["cnt"]
            assert entries_after == entries_before

    def test_rejection_creates_no_publish_event(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """14. After a rejected insert no RELEASE_PUBLISHED audit event
        exists for the package."""
        _set_client_env(monkeypatch, tmp_path / "u-vt-rej-noevent")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-VT-REJ-PUB", "ENG-FIC-0001",
                "Rejection publish action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-VT-REJ-PUB", "ENG-FIC-0001")
            conn.commit()
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-VT-REJ-PUB", "REL-VT-REJ-PUB",
                    "ACT-VT-REJ-PUB",
                    display_summary="WRONG summary does not match",
                )
            conn.rollback()
            publish_events = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events "
                "WHERE event_type = 'RELEASE_PUBLISHED' "
                "AND event_id = 'EVT-REL-VT-REJ-PUB-PUB'"
            ).fetchone()["cnt"]
            assert publish_events == 0


# ── Phase 6B1: trigger lifecycle (fresh + upgrade) ──────────────


class TestReleasePackageInsertBoundary:
    """Every release package starts as DRAFT."""

    _TRIGGER_NAME = "client_release_packages_require_draft_insert"

    def test_direct_published_insert_is_rejected_without_side_effects(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "direct-published")
        with store.connect() as conn:
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages must start as DRAFT",
            ):
                conn.execute(
                    "INSERT INTO client_release_packages "
                    "(release_id, engagement_id, release_version, status, "
                    " created_at, created_by, published_at, published_by) "
                    "VALUES ('REL-DIRECT-PUBLISHED', 'ENG-FIC-0002', 1, "
                    "'PUBLISHED', 'bad-time', 'Fictional Creator', "
                    "'bad-time', '')"
                )
            package_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM client_release_packages "
                "WHERE release_id = 'REL-DIRECT-PUBLISHED'"
            ).fetchone()["cnt"]
            event_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events "
                "WHERE event_id LIKE 'EVT-REL-DIRECT-PUBLISHED-%'"
            ).fetchone()["cnt"]
        assert package_count == 0
        assert event_count == 0

    def test_direct_withdrawn_insert_is_rejected_without_side_effects(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "direct-withdrawn")
        with store.connect() as conn:
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages must start as DRAFT",
            ):
                conn.execute(
                    "INSERT INTO client_release_packages "
                    "(release_id, engagement_id, release_version, status, "
                    " created_at, created_by, published_at, published_by, "
                    " withdrawn_at, withdrawn_by, withdrawal_reason) "
                    "VALUES ('REL-DIRECT-WITHDRAWN', 'ENG-FIC-0002', 1, "
                    "'WITHDRAWN', '2026-08-20T00:00:00Z', "
                    "'Fictional Creator', '2026-08-20T01:00:00Z', "
                    "'Fictional Publisher', '2026-08-20T02:00:00Z', "
                    "'Fictional Withdrawer', 'Fictional reason')"
                )
            package_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM client_release_packages "
                "WHERE release_id = 'REL-DIRECT-WITHDRAWN'"
            ).fetchone()["cnt"]
            event_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events "
                "WHERE event_id LIKE 'EVT-REL-DIRECT-WITHDRAWN-%'"
            ).fetchone()["cnt"]
        assert package_count == 0
        assert event_count == 0

    def test_direct_draft_insert_is_accepted(self, tmp_path: Path) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "direct-draft")
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                " created_at, created_by) "
                "VALUES ('REL-DIRECT-DRAFT', 'ENG-FIC-0002', 1, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Fictional Creator')"
            )
            row = conn.execute(
                "SELECT status, published_at, withdrawn_at "
                "FROM client_release_packages "
                "WHERE release_id = 'REL-DIRECT-DRAFT'"
            ).fetchone()
        assert tuple(row) == ("DRAFT", None, None)

    def test_fresh_database_has_draft_insert_trigger(
        self, tmp_path: Path
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "insert-fresh")
        with store.connect() as conn:
            row = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'trigger' "
                "AND name = ?",
                (self._TRIGGER_NAME,),
            ).fetchone()
        assert row is not None
        assert "BEFORE INSERT ON client_release_packages" in row["sql"]
        assert "NEW.status != 'DRAFT'" in row["sql"]

    def test_reopen_installs_trigger_and_preserves_existing_history(
        self, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "insert-reopen"
        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            conn.execute(f"DROP TRIGGER {self._TRIGGER_NAME}")
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                " created_at, created_by, published_at, published_by, "
                " withdrawn_at, withdrawn_by, withdrawal_reason) "
                "VALUES ('REL-HISTORICAL-WITHDRAWN', 'ENG-FIC-0002', 1, "
                "'WITHDRAWN', '2026-08-19T00:00:00Z', "
                "'Fictional Creator', '2026-08-19T01:00:00Z', "
                "'Fictional Publisher', '2026-08-19T02:00:00Z', "
                "'Fictional Withdrawer', 'Fictional history')"
            )
            before = tuple(conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE release_id = 'REL-HISTORICAL-WITHDRAWN'"
            ).fetchone())
        reopened = WorkbenchStore(data_dir=data_dir)
        with reopened.connect() as conn:
            trigger = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                "AND name = ?",
                (self._TRIGGER_NAME,),
            ).fetchone()
            after = tuple(conn.execute(
                "SELECT * FROM client_release_packages "
                "WHERE release_id = 'REL-HISTORICAL-WITHDRAWN'"
            ).fetchone())
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages must start as DRAFT",
            ):
                conn.execute(
                    "INSERT INTO client_release_packages "
                    "(release_id, engagement_id, release_version, status, "
                    " created_at, created_by) "
                    "VALUES ('REL-REOPEN-PUBLISHED', 'ENG-FIC-0002', 2, "
                    "'PUBLISHED', '2026-08-20T00:00:00Z', "
                    "'Fictional Creator')"
                )
        assert trigger is not None
        assert after == before

    def test_repeated_initialisation_is_idempotent(
        self, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "insert-idempotent"
        first = WorkbenchStore(data_dir=data_dir)
        with first.connect() as conn:
            before_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM client_release_packages ORDER BY release_id"
                ).fetchall()
            ]
            before_events = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events"
            ).fetchone()["cnt"]
        WorkbenchStore(data_dir=data_dir)
        third = WorkbenchStore(data_dir=data_dir)
        with third.connect() as conn:
            after_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM client_release_packages ORDER BY release_id"
                ).fetchall()
            ]
            after_events = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events"
            ).fetchone()["cnt"]
            trigger_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM sqlite_master "
                "WHERE type = 'trigger' AND name = ?",
                (self._TRIGGER_NAME,),
            ).fetchone()["cnt"]
        assert after_packages == before_packages
        assert after_events == before_events
        assert trigger_count == 1


class TestReleaseTriggerInventory:
    """Stage 3: retained SQLite release boundaries are intentional."""

    def test_fresh_and_reopened_database_keep_only_final_release_boundaries(
        self, tmp_path: Path,
    ) -> None:
        """Fail if a migration loses a retained boundary or leaves stale SQL.

        Stage 2 moved creation and withdrawal audit coordination into the
        service. Publication remains trigger-owned and all remaining release
        triggers protect direct SQL, legacy upgrades, or immutable history.
        """
        data_dir = tmp_path / "release-trigger-inventory"
        first = WorkbenchStore(data_dir=data_dir)
        with first.connect() as conn:
            before_audit_events = _assert_final_release_trigger_inventory(conn)

        reopened = WorkbenchStore(data_dir=data_dir)
        with reopened.connect() as conn:
            after_audit_events = _assert_final_release_trigger_inventory(conn)

        assert after_audit_events == before_audit_events

    def test_phase6a_fixture_upgrade_and_reopen_keep_final_boundaries(
        self, tmp_path: Path,
    ) -> None:
        """The Phase 6A fixture upgrades to, then reopens with, the inventory."""
        data_dir = tmp_path / "release-trigger-phase6a-upgrade"
        _build_phase6a_release_database(data_dir)
        with sqlite3.connect(data_dir / "workbench.sqlite3") as conn:
            legacy_audit_events = _audit_event_snapshot(conn)

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            upgraded_audit_events = _assert_final_release_trigger_inventory(conn)

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            reopened_audit_events = _assert_final_release_trigger_inventory(conn)

        expected_migration_events = [
            (
                "EVT-ACT-FIC-0001-APPROVED",
                "ENG-FIC-0001",
                "ACTION_APPROVED",
                "2026-08-19T09:30:00Z",
                "Fictional Site Auditor",
            ),
            (
                "EVT-REL-FIC-PHASE6B1-UPGRADE-CREATED",
                "ENG-FIC-0001",
                "RELEASE_CREATED",
                "2026-08-19T10:30:00Z",
                "Fictional Site Auditor",
            ),
            (
                "EVT-REL-FIC-PHASE6B1-UPGRADE-PUB",
                "ENG-FIC-0001",
                "RELEASE_PUBLISHED",
                "2026-08-19T11:00:00Z",
                "Fictional Site Auditor",
            ),
            (
                "EVT-REL-FIC-PUBLISHED-PHASE6B1-WITHDRAWN",
                "ENG-FIC-0001",
                "RELEASE_WITHDRAWN",
                "2026-08-19T10:45:00Z",
                "Fictional Site Auditor",
            ),
        ]
        assert all(event in upgraded_audit_events for event in legacy_audit_events)
        assert [
            event for event in upgraded_audit_events if event not in legacy_audit_events
        ] == expected_migration_events
        assert reopened_audit_events == upgraded_audit_events

    def test_predecessor_trigger_upgrade_and_reopen_keep_final_boundaries(
        self, tmp_path: Path,
    ) -> None:
        """A Phase 6B1 predecessor trigger is replaced without audit drift."""
        data_dir = tmp_path / "release-trigger-predecessor-upgrade"
        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_entries_validate_action_source"
            )
            conn.execute("DROP TRIGGER client_release_packages_validate_publish")
            conn.execute(_OLD_STYLE_ACTION_TRIGGER_SQL)
            predecessor_audit_events = _audit_event_snapshot(conn)

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            upgraded_audit_events = _assert_final_release_trigger_inventory(conn)

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            reopened_audit_events = _assert_final_release_trigger_inventory(conn)

        assert upgraded_audit_events == predecessor_audit_events
        assert reopened_audit_events == upgraded_audit_events


class TestReleaseDirectSqlImmutability:
    """Retained SQLite triggers reject direct writes and preserve rows."""

    @staticmethod
    def _assert_rejected_write_preserves_snapshot(
        connection: sqlite3.Connection,
        snapshot: Callable[[], object],
        statement: str,
        error_message: str,
        marker_event_id: str,
    ) -> None:
        before = snapshot()
        connection.execute("BEGIN")
        with pytest.raises(sqlite3.IntegrityError, match=error_message):
            connection.execute(statement)
        assert connection.in_transaction
        assert snapshot() == before
        connection.execute(
            """
            INSERT INTO engagement_audit_events
            (event_id, engagement_id, event_type, recorded_at, actor)
            VALUES (?, 'ENG-FIC-0001', 'RELEASE_CREATED',
                    '2026-08-21T00:00:00Z', 'Test')
            """,
            (marker_event_id,),
        )
        assert connection.execute(
            "SELECT 1 FROM engagement_audit_events WHERE event_id = ?",
            (marker_event_id,),
        ).fetchone() is not None
        connection.rollback()
        assert snapshot() == before

    def test_published_package_delete_rejected_and_row_unchanged(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "direct-package-delete")
        with store.connect() as conn:
            self._assert_rejected_write_preserves_snapshot(
                conn,
                lambda: tuple(conn.execute(
                    "SELECT release_id, engagement_id, release_version, status, "
                    "created_at, created_by, published_at, published_by, "
                    "withdrawn_at, withdrawn_by, withdrawal_reason "
                    "FROM client_release_packages "
                    "WHERE release_id = 'REL-FIC-PUBLISHED'"
                ).fetchone()),
                "DELETE FROM client_release_packages "
                "WHERE release_id = 'REL-FIC-PUBLISHED'",
                "Release packages are immutable",
                "EVT-TEST-DIRECT-PACKAGE-DELETE",
            )

    def test_release_entry_update_rejected_and_row_unchanged(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "direct-entry-update")
        with store.connect() as conn:
            self._assert_rejected_write_preserves_snapshot(
                conn,
                lambda: tuple(conn.execute(
                    "SELECT release_entry_id, release_id, source_record_type, "
                    "source_record_id, source_record_version, "
                    "approved_evidence_reference_id, display_title, "
                    "display_summary, action_owner, action_target_date, "
                    "action_delivery_status FROM client_release_entries "
                    "WHERE release_entry_id = 'RLE-FIC-ACT-1'"
                ).fetchone()),
                "UPDATE client_release_entries SET display_summary = 'Changed' "
                "WHERE release_entry_id = 'RLE-FIC-ACT-1'",
                "Release entries are immutable",
                "EVT-TEST-DIRECT-ENTRY-UPDATE",
            )

    def test_release_entry_delete_rejected_and_row_unchanged(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "direct-entry-delete")
        with store.connect() as conn:
            self._assert_rejected_write_preserves_snapshot(
                conn,
                lambda: tuple(conn.execute(
                    "SELECT release_entry_id, release_id, source_record_type, "
                    "source_record_id, source_record_version, "
                    "approved_evidence_reference_id, display_title, "
                    "display_summary, action_owner, action_target_date, "
                    "action_delivery_status FROM client_release_entries "
                    "WHERE release_entry_id = 'RLE-FIC-ACT-1'"
                ).fetchone()),
                "DELETE FROM client_release_entries "
                "WHERE release_entry_id = 'RLE-FIC-ACT-1'",
                "Release entries are immutable",
                "EVT-TEST-DIRECT-ENTRY-DELETE",
            )

    def test_engagement_audit_event_delete_rejected_and_row_unchanged(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "direct-audit-delete")
        with store.connect() as conn:
            self._assert_rejected_write_preserves_snapshot(
                conn,
                lambda: _audit_event_snapshot(conn),
                "DELETE FROM engagement_audit_events "
                "WHERE event_id = 'EVT-CON-FIC-0001-APPROVED'",
                "Engagement audit events are immutable",
                "EVT-TEST-DIRECT-AUDIT-DELETE",
            )


class TestTriggerLifecycle:
    """Verify the release-validation triggers exist on a fresh
    database, contain no stale _old table references, are replaced on
    upgrade, and that upgrade preserves existing data while enforcing
    the new rules."""

    def test_validation_triggers_exist_on_fresh_db(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """15. All release validation triggers exist on a fresh database."""
        _set_client_env(monkeypatch, tmp_path / "u-life-fresh")
        store = WorkbenchStore()
        with store.connect() as conn:
            names = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                    "AND name IN ("
                    "'client_release_entries_validate_action_source', "
                    "'client_release_entries_validate_conclusion_source', "
                    "'client_release_entries_one_conclusion', "
                    "'client_release_packages_validate_publish')"
                )
            }
        assert "client_release_entries_validate_action_source" in names
        assert "client_release_entries_validate_conclusion_source" in names
        assert "client_release_entries_one_conclusion" in names
        assert "client_release_packages_validate_publish" in names

    def test_triggers_have_no_old_table_references(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """16. No release validation trigger references a renamed _old table."""
        _set_client_env(monkeypatch, tmp_path / "u-life-no-old")
        store = WorkbenchStore()
        with store.connect() as conn:
            rows = conn.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' "
                "AND name IN ("
                "'client_release_entries_validate_action_source', "
                "'client_release_entries_validate_conclusion_source', "
                "'client_release_entries_one_conclusion', "
                "'client_release_packages_validate_publish')"
            ).fetchall()
        assert len(rows) == 4
        for row in rows:
            assert "_old" not in row["sql"], (
                f"trigger {row['name']} still references a renamed _old table"
            )

    def test_upgrade_replaces_old_triggers(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """17. Old-style triggers are replaced with the new definitions
        when the database is re-opened for upgrade."""
        _set_client_env(monkeypatch, tmp_path / "u-life-replace")
        store = WorkbenchStore()
        with store.connect() as conn:
            # Simulate a pre-6B1 build: swap in an old-style ACTION
            # trigger that lacks snapshot + audit-event checks.
            conn.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_entries_validate_action_source"
            )
            conn.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_packages_validate_publish"
            )
            conn.execute(_OLD_STYLE_ACTION_TRIGGER_SQL)
            conn.commit()
            old_sql = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'trigger' "
                "AND name = 'client_release_entries_validate_action_source'"
            ).fetchone()["sql"]
            assert "ACTION_APPROVED" not in old_sql
            assert "TRIM" not in old_sql
        # Re-open — _initialise must drop and recreate the new trigger.
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            new_sql = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'trigger' "
                "AND name = 'client_release_entries_validate_action_source'"
            ).fetchone()["sql"]
            publish_sql = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'trigger' "
                "AND name = 'client_release_packages_validate_publish'"
            ).fetchone()["sql"]
        assert "ACTION_APPROVED" in new_sql
        assert "TRIM" in new_sql
        assert "julianday" in publish_sql
        assert "_old" not in publish_sql

    def test_reopen_replaces_terminal_entry_trigger_and_blocks_null_id_entry(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """Reopen replaces the old equality lookup with a NULL-safe lookup."""
        _set_client_env(monkeypatch, tmp_path / "u-terminal-trigger")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_entries_no_terminal_insert"
            )
            conn.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_packages_require_draft_insert"
            )
            conn.execute(
                """
                CREATE TRIGGER client_release_entries_no_terminal_insert
                BEFORE INSERT ON client_release_entries
                BEGIN
                    SELECT RAISE(ABORT,
                        'Cannot add entries to a published or withdrawn release')
                    WHERE (SELECT status FROM client_release_packages
                           WHERE release_id = NEW.release_id)
                          IN ('PUBLISHED', 'WITHDRAWN');
                END
                """
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by, published_at, published_by) VALUES "
                "(NULL, 'ENG-FIC-0002', 1, 'PUBLISHED', "
                "'2026-08-20T00:00:00Z', 'Creator', "
                "'2026-08-20T01:00:00Z', 'Publisher')"
            )

        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            trigger_sql = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'trigger' "
                "AND name = 'client_release_entries_no_terminal_insert'"
            ).fetchone()["sql"]
            assert "release_id IS NEW.release_id" in trigger_sql
            # Isolate the terminal guard.  Other entry source checks have
            # separate coverage and can reject this forged legacy row first.
            conn.execute(
                "DROP TRIGGER client_release_entries_validate_action_source"
            )
            conn.execute(
                "DROP TRIGGER client_release_entries_validate_conclusion_source"
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Cannot add entries to a published or withdrawn release",
            ):
                conn.execute(
                    "INSERT INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    "source_record_id, source_record_version, "
                    "approved_evidence_reference_id, display_title, "
                    "display_summary) VALUES "
                    "('RLE-LEGACY-NULL-TERMINAL', NULL, 'CONCLUSION', "
                    "'CON-FIC-0001', 1, 'EVD-FIC-0001', "
                    "'Legacy title', 'Legacy summary')"
                )

    def test_reopen_replaces_auto_publish_trigger_with_null_safe_identity(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """Reopen replaces the old auto-event trigger before a NULL-ID publish."""
        _set_client_env(monkeypatch, tmp_path / "u-auto-publish-trigger")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_auto_publish_event"
            )
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute(
                """
                CREATE TRIGGER client_release_packages_auto_publish_event
                AFTER UPDATE ON client_release_packages
                WHEN NEW.status = 'PUBLISHED' AND OLD.status = 'DRAFT'
                BEGIN
                    INSERT INTO engagement_audit_events
                    (event_id, engagement_id, event_type, recorded_at, actor)
                    VALUES ('EVT-' || NEW.release_id || '-PUB',
                            NEW.engagement_id,
                            'RELEASE_PUBLISHED',
                            NEW.published_at,
                            NEW.published_by);
                END
                """
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "(NULL, 'ENG-FIC-0002', 1, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )

        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            trigger_sql = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'trigger' "
                "AND name = 'client_release_packages_auto_publish_event'"
            ).fetchone()["sql"]
            assert "NEW.release_id IS OLD.release_id" in trigger_sql
            # The publication validator correctly rejects an empty package.
            # Remove it only to isolate the auto-event identity guard.
            conn.execute(
                "DROP TRIGGER client_release_packages_validate_publish"
            )
            conn.execute(
                "UPDATE client_release_packages "
                "SET status = 'PUBLISHED', "
                "published_at = '2026-08-20T01:00:00Z', "
                "published_by = 'Publisher' "
                "WHERE release_id IS NULL"
            )
            event = conn.execute(
                "SELECT event_id, event_type, actor FROM "
                "engagement_audit_events WHERE engagement_id = 'ENG-FIC-0002' "
                "AND event_type = 'RELEASE_PUBLISHED'"
            ).fetchone()
        assert tuple(event) == (None, "RELEASE_PUBLISHED", "Publisher")

    def test_new_rules_apply_after_upgrade(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """18. After upgrade, a release entry without a matching audit
        event is rejected by the new trigger."""
        _set_client_env(monkeypatch, tmp_path / "u-life-rules")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_entries_validate_action_source"
            )
            conn.execute(_OLD_STYLE_ACTION_TRIGGER_SQL)
            conn.commit()
        # Re-open to apply the upgrade.
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            _insert_approved_action_without_event(
                conn, "ACT-LIFE-RULES", "ENG-FIC-0001",
                "Upgrade rules action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-LIFE-RULES", "ENG-FIC-0001")
            # No ACTION_APPROVED audit event -> new trigger must reject.
            with pytest.raises(sqlite3.IntegrityError,
                               match="Source action must be an APPROVED action"):
                _insert_action_release_entry(
                    conn, "RLE-LIFE-RULES", "REL-LIFE-RULES",
                    "ACT-LIFE-RULES",
                    display_summary="Upgrade rules action",
                )

    def test_published_and_withdrawn_history_unchanged_after_upgrade(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """19. Upgrade does not alter PUBLISHED or WITHDRAWN history."""
        _set_client_env(monkeypatch, tmp_path / "u-life-entries")
        store = WorkbenchStore()
        with store.connect() as conn:
            before_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM client_release_packages "
                    "WHERE status IN ('PUBLISHED', 'WITHDRAWN') "
                    "ORDER BY release_id"
                ).fetchall()
            ]
            before_entries = [
                tuple(row) for row in conn.execute(
                    "SELECT e.* FROM client_release_entries e "
                    "JOIN client_release_packages p ON p.release_id = e.release_id "
                    "WHERE p.status IN ('PUBLISHED', 'WITHDRAWN') "
                    "ORDER BY e.release_entry_id"
                ).fetchall()
            ]
        assert before_packages
        assert before_entries
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            after_packages = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM client_release_packages "
                    "WHERE status IN ('PUBLISHED', 'WITHDRAWN') "
                    "ORDER BY release_id"
                ).fetchall()
            ]
            after_entries = [
                tuple(row) for row in conn.execute(
                    "SELECT e.* FROM client_release_entries e "
                    "JOIN client_release_packages p ON p.release_id = e.release_id "
                    "WHERE p.status IN ('PUBLISHED', 'WITHDRAWN') "
                    "ORDER BY e.release_entry_id"
                ).fetchall()
            ]
        assert after_packages == before_packages
        assert after_entries == before_entries

    def test_audit_event_counts_unchanged_after_upgrade(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """20. Audit event counts are unchanged by upgrade."""
        _set_client_env(monkeypatch, tmp_path / "u-life-audit")
        store = WorkbenchStore()
        with store.connect() as conn:
            before = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events"
            ).fetchone()["cnt"]
        assert before > 0
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            after = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events"
            ).fetchone()["cnt"]
        assert after == before

    def test_repeated_initialisation_idempotent(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """21. Opening the same database twice must not raise."""
        _set_client_env(monkeypatch, tmp_path / "u-life-idempotent")
        store1 = WorkbenchStore()
        with store1.connect() as conn:
            before_events = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events"
            ).fetchone()["cnt"]
            before_triggers = [
                row["name"] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                    "ORDER BY name"
                ).fetchall()
            ]
        # Second open of the same database must succeed.
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            after_events = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events"
            ).fetchone()["cnt"]
            after_triggers = [
                row["name"] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                    "ORDER BY name"
                ).fetchall()
            ]
        assert after_events == before_events
        assert after_triggers == before_triggers


# ── Publication metadata validation ───────────────────────────

class TestPublicationMetadata:
    """Whitespace-only and malformed published_at / published_by
    must be rejected at the DRAFT→PUBLISHED transition."""

    # ── helpers ────────────────────────────────────────────────

    @staticmethod
    def _create_draft(conn: sqlite3.Connection, release_id: str) -> None:
        _create_draft_package(conn, release_id, "ENG-FIC-0001")

    @staticmethod
    def _publish(
        conn: sqlite3.Connection, release_id: str,
        published_at: str, published_by: str,
    ) -> None:
        conn.execute(
            "UPDATE client_release_packages "
            "SET status = 'PUBLISHED', published_at = ?, published_by = ? "
            "WHERE release_id = ?",
            (published_at, published_by, release_id),
        )

    # ── whitespace_by ───────────────────────────────────────────

    @pytest.mark.parametrize("whitespace", ("\t", "\n", "\v", "\f", "\r"))
    def test_whitespace_published_by_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, whitespace: str,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "ws-by")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-WS-BY")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                self._publish(
                    conn, "REL-WS-BY",
                    "2026-08-20T00:00:00Z", whitespace,
                )

    def test_whitespace_published_at_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "ws-at")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-WS-AT")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                self._publish(
                    conn, "REL-WS-AT",
                    "   ", "Auditor",
                )

    # ── leading / trailing ─────────────────────────────────────

    def test_leading_whitespace_published_by_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "lead")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-LEAD")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                self._publish(
                    conn, "REL-LEAD",
                    "2026-08-20T00:00:00Z", "  Auditor",
                )

    def test_trailing_whitespace_published_by_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "trail")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-TRAIL")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                self._publish(
                    conn, "REL-TRAIL",
                    "2026-08-20T00:00:00Z", "Auditor  ",
                )

    # ── malformed timestamps ───────────────────────────────────

    def test_date_only_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "dateonly")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-DATE")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                self._publish(
                    conn, "REL-DATE",
                    "2026-08-20", "Auditor",
                )

    def test_invalid_calendar_date_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "invcal")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-INVCAL")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                self._publish(
                    conn, "REL-INVCAL",
                    "2026-02-30T00:00:00Z", "Auditor",
                )

    def test_invalid_time_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "invtime")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-INVTIME")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                self._publish(
                    conn, "REL-INVTIME",
                    "2026-08-20T25:00:00Z", "Auditor",
                )

    def test_missing_z_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "noz")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-NOZ")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                self._publish(
                    conn, "REL-NOZ",
                    "2026-08-20T00:00:00", "Auditor",
                )

    def test_offset_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "offset")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-OFF")
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                self._publish(
                    conn, "REL-OFF",
                    "2026-08-20T00:00:00+10:00", "Auditor",
                )

    # ── valid canonical ────────────────────────────────────────

    def test_valid_canonical_timestamp_accepted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "canon")
        store = WorkbenchStore()
        with store.connect() as conn:
            # Use a separate engagement — the seed already has a
            # PUBLISHED package for ENG-FIC-0001 and the unique index
            # one_current_release_per_engagement allows only one.
            conn.execute(
                "INSERT OR IGNORE INTO engagement_setups "
                "(engagement_id, creation_attempt_key, title, state, "
                " is_fictional, data_classification, created_at) "
                "VALUES ('ENG-CANON', 'canon-key', 'Canon Test', "
                "'READY_FOR_CAPTURE', 1, 'FICTIONAL', '2026-08-20T00:00:00Z')"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                " created_at, created_by) "
                "VALUES ('REL-CANON', 'ENG-CANON', 1, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'test')"
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-REL-CANON-CREATED', 'ENG-CANON', "
                "'RELEASE_CREATED', '2026-08-20T00:00:00Z', 'test')"
            )
            _insert_approved_action(
                conn, "ACT-CANON", "ENG-CANON",
                "Canonical publication action", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-CANON", "REL-CANON", "ACT-CANON",
                display_summary="Canonical publication action",
            )
            self._publish(
                conn, "REL-CANON",
                "2026-08-20T00:00:00Z", "Auditor",
            )
            pkg = conn.execute(
                "SELECT status, published_at, published_by "
                "FROM client_release_packages "
                "WHERE release_id = 'REL-CANON'"
            ).fetchone()
            assert pkg is not None
            assert pkg["status"] == "PUBLISHED"
            assert pkg["published_at"] == "2026-08-20T00:00:00Z"
            assert pkg["published_by"] == "Auditor"

    # ── side effects ──────────────────────────────────────────

    def test_rejected_publish_leaves_draft(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "side-draft")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-SIDE-D")
            with pytest.raises(sqlite3.IntegrityError):
                self._publish(
                    conn, "REL-SIDE-D",
                    "bad", "Auditor",
                )
            status = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-SIDE-D'"
            ).fetchone()["status"]
            assert status == "DRAFT"

    def test_rejected_publish_creates_no_event(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "side-noevt")
        store = WorkbenchStore()
        with store.connect() as conn:
            self._create_draft(conn, "REL-SIDE-E")
            with pytest.raises(sqlite3.IntegrityError):
                self._publish(
                    conn, "REL-SIDE-E",
                    "bad", "Auditor",
                )
            cnt = conn.execute(
                "SELECT COUNT(*) as cnt FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-SIDE-E-PUB'"
            ).fetchone()["cnt"]
            assert cnt == 0

    # ── upgrade ────────────────────────────────────────────────

    def test_upgrade_uses_corrected_trigger(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """After a fresh-to-upgrade cycle the corrected trigger
        must still reject whitespace-only published_by."""
        data_dir = tmp_path / "upg-pub"
        data_dir.mkdir()
        _set_client_env(monkeypatch, data_dir)
        # First initialisation (fresh).
        WorkbenchStore()
        # Second initialisation (upgrade).
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            _create_draft_package(conn, "REL-UPG-PUB", "ENG-FIC-0001")
            # Whitespace-only published_by → must still be rejected
            # after the upgrade cycle.
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release packages are immutable",
            ):
                conn.execute(
                    "UPDATE client_release_packages "
                    "SET status = 'PUBLISHED', published_at = ?, "
                    " published_by = ? WHERE release_id = ?",
                    ("2026-08-20T00:00:00Z", "   ", "REL-UPG-PUB"),
                )


# ── Publication-time integrity ───────────────────────────────

class TestReleasePublicationIntegrity:
    """DRAFT packages must pass current source and time checks when
    they change to PUBLISHED, including entries retained from Phase 6A."""

    _TITLE = "Approved field capture conclusion"
    _SUMMARY = (
        "The field capture control is suitably designed for "
        "fictional mobile evidence collection under the pilot scope."
    )
    _EVIDENCE = "EVD-FIC-0001"

    @staticmethod
    def _publish_at(
        conn: sqlite3.Connection, release_id: str, published_at: str,
    ) -> None:
        conn.execute(
            "UPDATE client_release_packages "
            "SET status = 'PUBLISHED', published_at = ?, published_by = 'Auditor' "
            "WHERE release_id = ?",
            (published_at, release_id),
        )

    @staticmethod
    def _assert_publish_rejected(
        conn: sqlite3.Connection, release_id: str, message: str,
        published_at: str = "2026-08-20T00:00:00Z",
    ) -> None:
        with pytest.raises(sqlite3.IntegrityError, match=message):
            TestReleasePublicationIntegrity._publish_at(
                conn, release_id, published_at,
            )
        package = conn.execute(
            "SELECT status FROM client_release_packages WHERE release_id = ?",
            (release_id,),
        ).fetchone()
        assert package is not None
        assert package["status"] == "DRAFT"
        publish_events = conn.execute(
            "SELECT COUNT(*) AS cnt FROM engagement_audit_events "
            "WHERE event_id = ? AND event_type = 'RELEASE_PUBLISHED'",
            (f"EVT-{release_id}-PUB",),
        ).fetchone()["cnt"]
        assert publish_events == 0

    @staticmethod
    def _legacy_store(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, release_id: str,
        conclusion_id: str, *, title: str = _TITLE, summary: str = _SUMMARY,
        evidence_id: str = _EVIDENCE, version: int = 1,
    ) -> WorkbenchStore:
        """Create one legacy DRAFT entry before reopening for upgrade."""
        data_dir = tmp_path / release_id.lower()
        data_dir.mkdir()
        _set_client_env(monkeypatch, data_dir)
        store1 = WorkbenchStore()
        with store1.connect() as conn:
            _create_draft_package(conn, release_id, "ENG-FIC-0001")
            conn.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_entries_validate_conclusion_source"
            )
            _insert_legacy_conclusion_release_entry(
                conn, f"RLE-{release_id}", release_id, conclusion_id,
                title=title, summary=summary, evidence_id=evidence_id,
                version=version,
            )
            conn.commit()
        return WorkbenchStore()

    def test_legacy_missing_source_entry_rejected_after_upgrade(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        store = self._legacy_store(
            monkeypatch, tmp_path, "REL-LEGACY-MISSING", "CON-DOES-NOT-EXIST",
        )
        with store.connect() as conn:
            self._assert_publish_rejected(
                conn, "REL-LEGACY-MISSING",
                "Release package contains an invalid source entry",
            )

    def test_legacy_candidate_source_entry_rejected_after_upgrade(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        store = self._legacy_store(
            monkeypatch, tmp_path, "REL-LEGACY-CANDIDATE", "CON-FIC-STALE",
            title="Fictional stale draft conclusion",
            summary="An earlier draft that was never approved.",
        )
        with store.connect() as conn:
            self._assert_publish_rejected(
                conn, "REL-LEGACY-CANDIDATE",
                "Release package contains an invalid source entry",
            )

    def test_legacy_wrong_version_entry_rejected_after_upgrade(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        store = self._legacy_store(
            monkeypatch, tmp_path, "REL-LEGACY-VERSION", "CON-FIC-0001",
            version=2,
        )
        with store.connect() as conn:
            self._assert_publish_rejected(
                conn, "REL-LEGACY-VERSION",
                "Release package contains an invalid source entry",
            )

    def test_legacy_cross_engagement_entry_rejected_after_upgrade(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "legacy-cross-engagement"
        data_dir.mkdir()
        _set_client_env(monkeypatch, data_dir)
        store1 = WorkbenchStore()
        with store1.connect() as conn:
            _create_draft_package(conn, "REL-LEGACY-CROSS", "ENG-FIC-0001")
            TestConclusionSourceValidation._insert_approved_conclusion(
                conn, "CON-LEGACY-CROSS", "ENG-FIC-0002",
                "Other engagement conclusion", "Other engagement summary",
                "EVD-FIC-0002", "Auditor", "2026-08-20T00:00:00Z",
            )
            conn.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_entries_validate_conclusion_source"
            )
            _insert_legacy_conclusion_release_entry(
                conn, "RLE-LEGACY-CROSS", "REL-LEGACY-CROSS",
                "CON-LEGACY-CROSS", title="Other engagement conclusion",
                summary="Other engagement summary", evidence_id="EVD-FIC-0002",
            )
            conn.commit()
        store2 = WorkbenchStore()
        with store2.connect() as conn:
            self._assert_publish_rejected(
                conn, "REL-LEGACY-CROSS",
                "Release package contains an invalid source entry",
            )

    def test_valid_legacy_draft_entry_is_accepted_after_upgrade(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        store = self._legacy_store(
            monkeypatch, tmp_path, "REL-LEGACY-VALID", "CON-FIC-0001",
        )
        with store.connect() as conn:
            trigger = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'trigger' "
                "AND name = 'client_release_packages_validate_publish'"
            ).fetchone()
            assert trigger is not None
            assert "_old" not in trigger["sql"]
            self._publish_at(conn, "REL-LEGACY-VALID", "2026-08-20T00:00:00Z")
            package = conn.execute(
                "SELECT status, published_at FROM client_release_packages "
                "WHERE release_id = 'REL-LEGACY-VALID'"
            ).fetchone()
            assert package is not None
            assert package["status"] == "PUBLISHED"
            assert package["published_at"] == "2026-08-20T00:00:00Z"

    @pytest.mark.parametrize(
        ("title", "summary", "evidence_id"),
        (
            ("\t", _SUMMARY, _EVIDENCE),
            (_TITLE, "\t", _EVIDENCE),
            (_TITLE, _SUMMARY, "\t"),
        ),
    )
    def test_ascii_whitespace_legacy_display_field_cannot_publish(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        title: str, summary: str, evidence_id: str,
    ) -> None:
        """Publish-time validation rejects ASCII-whitespace display data."""
        store = self._legacy_store(
            monkeypatch, tmp_path, "REL-LEGACY-ASCII-DISPLAY", "CON-FIC-0001",
            title=title, summary=summary, evidence_id=evidence_id,
        )
        with store.connect() as conn:
            self._assert_publish_rejected(
                conn, "REL-LEGACY-ASCII-DISPLAY",
                "Release package contains an invalid source entry",
            )

    def test_empty_package_publication_is_rejected_without_event(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "empty-package")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-EMPTY-PUBLISH", "ENG-FIC-0001")
            self._assert_publish_rejected(
                conn, "REL-EMPTY-PUBLISH",
                "Release package must contain at least one valid entry",
            )

    def test_publication_before_package_creation_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "before-created")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-BEFORE-CREATED", "ENG-FIC-0001")
            _insert_legacy_conclusion_release_entry(
                conn, "RLE-BEFORE-CREATED", "REL-BEFORE-CREATED", "CON-FIC-0001",
            )
            self._assert_publish_rejected(
                conn, "REL-BEFORE-CREATED",
                "Publication time must not be before package creation",
                "2026-08-19T10:00:00Z",
            )

    def test_malformed_package_creation_time_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "malformed-created")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, created_at, created_by) "
                "VALUES ('REL-MALFORMED-CREATED', 'ENG-FIC-0001', 4, 'DRAFT', "
                "'not-a-time', 'test')"
            )
            _insert_legacy_conclusion_release_entry(
                conn, "RLE-MALFORMED-CREATED", "REL-MALFORMED-CREATED",
                "CON-FIC-0001",
            )
            self._assert_publish_rejected(
                conn, "REL-MALFORMED-CREATED",
                "Publication time must not be before package creation",
            )

    def test_numeric_package_creation_time_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "numeric-created")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, created_at, created_by) "
                "VALUES ('REL-NUMERIC-CREATED', 'ENG-FIC-0001', 4, 'DRAFT', "
                "'1', 'test')"
            )
            _insert_legacy_conclusion_release_entry(
                conn, "RLE-NUMERIC-CREATED", "REL-NUMERIC-CREATED",
                "CON-FIC-0001",
            )
            self._assert_publish_rejected(
                conn, "REL-NUMERIC-CREATED",
                "Publication time must not be before package creation",
            )

    def test_impossible_package_creation_date_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "impossible-created")
        store = WorkbenchStore()
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, created_at, created_by) "
                "VALUES ('REL-IMPOSSIBLE-CREATED', 'ENG-FIC-0001', 4, 'DRAFT', "
                "'2026-02-30T00:00:00Z', 'test')"
            )
            _insert_legacy_conclusion_release_entry(
                conn, "RLE-IMPOSSIBLE-CREATED", "REL-IMPOSSIBLE-CREATED",
                "CON-FIC-0001",
            )
            self._assert_publish_rejected(
                conn, "REL-IMPOSSIBLE-CREATED",
                "Publication time must not be before package creation",
            )

    def test_publication_before_action_approval_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "before-action-approval")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-BEFORE-ACTION", "ENG-FIC-0001")
            _insert_approved_action(
                conn, "ACT-BEFORE-PUBLISH", "ENG-FIC-0001",
                "Later action approval", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-08-20T01:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-BEFORE-ACTION", "REL-BEFORE-ACTION",
                "ACT-BEFORE-PUBLISH", display_summary="Later action approval",
            )
            self._assert_publish_rejected(
                conn, "REL-BEFORE-ACTION",
                "Publication time must not be before source approval",
            )

    def test_malformed_action_approval_time_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "malformed-action-approval")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-MALFORMED-ACTION", "ENG-FIC-0001")
            _insert_approved_action(
                conn, "ACT-MALFORMED-APPROVAL", "ENG-FIC-0001",
                "Malformed action approval", "Owner", "2026-12-31", "OPEN",
                "Auditor", "not-a-time",
            )
            _insert_action_release_entry(
                conn, "RLE-MALFORMED-ACTION", "REL-MALFORMED-ACTION",
                "ACT-MALFORMED-APPROVAL",
                display_summary="Malformed action approval",
            )
            self._assert_publish_rejected(
                conn, "REL-MALFORMED-ACTION",
                "Publication time must not be before source approval",
            )

    def test_numeric_action_approval_time_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "numeric-action-approval")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-NUMERIC-ACTION", "ENG-FIC-0001")
            _insert_approved_action(
                conn, "ACT-NUMERIC-APPROVAL", "ENG-FIC-0001",
                "Numeric action approval", "Owner", "2026-12-31", "OPEN",
                "Auditor", "1",
            )
            _insert_action_release_entry(
                conn, "RLE-NUMERIC-ACTION", "REL-NUMERIC-ACTION",
                "ACT-NUMERIC-APPROVAL", display_summary="Numeric action approval",
            )
            self._assert_publish_rejected(
                conn, "REL-NUMERIC-ACTION",
                "Publication time must not be before source approval",
            )

    def test_impossible_action_approval_date_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "impossible-action-approval")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-IMPOSSIBLE-ACTION", "ENG-FIC-0001")
            _insert_approved_action(
                conn, "ACT-IMPOSSIBLE-APPROVAL", "ENG-FIC-0001",
                "Impossible action approval", "Owner", "2026-12-31", "OPEN",
                "Auditor", "2026-02-30T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-IMPOSSIBLE-ACTION", "REL-IMPOSSIBLE-ACTION",
                "ACT-IMPOSSIBLE-APPROVAL",
                display_summary="Impossible action approval",
            )
            self._assert_publish_rejected(
                conn, "REL-IMPOSSIBLE-ACTION",
                "Publication time must not be before source approval",
            )

    def test_publication_before_conclusion_approval_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "before-conclusion-approval")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-BEFORE-CONCLUSION", "ENG-FIC-0001")
            TestConclusionSourceValidation._insert_approved_conclusion(
                conn, "CON-BEFORE-PUBLISH", "ENG-FIC-0001",
                "Later conclusion approval", "Later conclusion summary",
                "EVD-FIC-0001", "Auditor", "2026-08-20T01:00:00Z",
            )
            TestConclusionSourceValidation._insert_conclusion_entry(
                conn, "REL-BEFORE-CONCLUSION", "CON-BEFORE-PUBLISH",
                display_title="Later conclusion approval",
                display_summary="Later conclusion summary",
            )
            self._assert_publish_rejected(
                conn, "REL-BEFORE-CONCLUSION",
                "Publication time must not be before source approval",
            )

    def test_malformed_conclusion_approval_time_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "malformed-conclusion-approval")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-MALFORMED-CONCLUSION", "ENG-FIC-0001")
            TestConclusionSourceValidation._insert_approved_conclusion(
                conn, "CON-MALFORMED-APPROVAL", "ENG-FIC-0001",
                "Malformed conclusion approval", "Malformed conclusion summary",
                "EVD-FIC-0001", "Auditor", "not-a-time",
            )
            TestConclusionSourceValidation._insert_conclusion_entry(
                conn, "REL-MALFORMED-CONCLUSION", "CON-MALFORMED-APPROVAL",
                display_title="Malformed conclusion approval",
                display_summary="Malformed conclusion summary",
            )
            self._assert_publish_rejected(
                conn, "REL-MALFORMED-CONCLUSION",
                "Publication time must not be before source approval",
            )

    def test_numeric_conclusion_approval_time_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "numeric-conclusion-approval")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-NUMERIC-CONCLUSION", "ENG-FIC-0001")
            TestConclusionSourceValidation._insert_approved_conclusion(
                conn, "CON-NUMERIC-APPROVAL", "ENG-FIC-0001",
                "Numeric conclusion approval", "Numeric conclusion summary",
                "EVD-FIC-0001", "Auditor", "1",
            )
            TestConclusionSourceValidation._insert_conclusion_entry(
                conn, "REL-NUMERIC-CONCLUSION", "CON-NUMERIC-APPROVAL",
                display_title="Numeric conclusion approval",
                display_summary="Numeric conclusion summary",
            )
            self._assert_publish_rejected(
                conn, "REL-NUMERIC-CONCLUSION",
                "Publication time must not be before source approval",
            )

    def test_impossible_conclusion_approval_date_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "impossible-conclusion-approval")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-IMPOSSIBLE-CONCLUSION", "ENG-FIC-0001")
            TestConclusionSourceValidation._insert_approved_conclusion(
                conn, "CON-IMPOSSIBLE-APPROVAL", "ENG-FIC-0001",
                "Impossible conclusion approval", "Impossible conclusion summary",
                "EVD-FIC-0001", "Auditor", "2026-02-30T00:00:00Z",
            )
            TestConclusionSourceValidation._insert_conclusion_entry(
                conn, "REL-IMPOSSIBLE-CONCLUSION", "CON-IMPOSSIBLE-APPROVAL",
                display_title="Impossible conclusion approval",
                display_summary="Impossible conclusion summary",
            )
            self._assert_publish_rejected(
                conn, "REL-IMPOSSIBLE-CONCLUSION",
                "Publication time must not be before source approval",
            )

    def test_24_hour_publication_time_with_valid_entry_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "24-hour-publication")
        store = WorkbenchStore()
        with store.connect() as conn:
            _create_draft_package(conn, "REL-24-HOUR", "ENG-FIC-0001")
            _insert_legacy_conclusion_release_entry(
                conn, "RLE-24-HOUR", "REL-24-HOUR", "CON-FIC-0001",
            )
            self._assert_publish_rejected(
                conn, "REL-24-HOUR", "Release packages are immutable",
                "2026-08-20T24:00:00Z",
            )

    def test_publication_time_equality_boundaries_are_accepted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        _set_client_env(monkeypatch, tmp_path / "equality-boundaries")
        store = WorkbenchStore()
        boundary = "2026-08-20T00:00:00Z"
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO engagement_setups "
                "(engagement_id, creation_attempt_key, title, state, is_fictional, "
                " data_classification, created_at) "
                "VALUES ('ENG-EQUALITY', 'equality-key', 'Equality Test', "
                "'READY_FOR_CAPTURE', 1, 'FICTIONAL', ?)",
                (boundary,),
            )
            conn.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES ('EVT-REL-EQUALITY-CREATED', 'ENG-EQUALITY', "
                "'RELEASE_CREATED', ?, 'test')",
                (boundary,),
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, created_at, created_by) "
                "VALUES ('REL-EQUALITY', 'ENG-EQUALITY', 1, 'DRAFT', ?, 'test')",
                (boundary,),
            )
            _insert_approved_action(
                conn, "ACT-EQUALITY", "ENG-EQUALITY",
                "Equality action", "Owner", "2026-12-31", "OPEN",
                "Auditor", boundary,
            )
            _insert_action_release_entry(
                conn, "RLE-EQUALITY-A", "REL-EQUALITY", "ACT-EQUALITY",
                display_summary="Equality action",
            )
            TestConclusionSourceValidation._insert_approved_conclusion(
                conn, "CON-EQUALITY", "ENG-EQUALITY",
                "Equality conclusion", "Equality conclusion summary",
                "EVD-FIC-0001", "Auditor", boundary,
            )
            TestConclusionSourceValidation._insert_conclusion_entry(
                conn, "REL-EQUALITY", "CON-EQUALITY",
                display_title="Equality conclusion",
                display_summary="Equality conclusion summary",
            )
            self._publish_at(conn, "REL-EQUALITY", boundary)
            package = conn.execute(
                "SELECT status, published_at FROM client_release_packages "
                "WHERE release_id = 'REL-EQUALITY'"
            ).fetchone()
            assert package is not None
            assert package["status"] == "PUBLISHED"
            assert package["published_at"] == boundary


class TestClientReleaseEntryIdIntegrity:
    """Release entries always have stable identifiers."""

    @staticmethod
    def _make_release_entry_ids_nullable(conn: sqlite3.Connection) -> None:
        for trigger_name in (
            "client_release_entries_no_update",
            "client_release_entries_no_delete",
            "client_release_entries_no_terminal_insert",
            "client_release_entries_validate_action_source",
            "client_release_entries_validate_conclusion_source",
            "client_release_entries_one_conclusion",
            "client_release_entries_one_action_source",
            "client_release_packages_validate_publish",
        ):
            conn.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
        conn.execute(
            "ALTER TABLE client_release_entries "
            "RENAME TO client_release_entries_old"
        )
        conn.execute(
            """
            CREATE TABLE client_release_entries (
                release_entry_id TEXT PRIMARY KEY,
                release_id TEXT NOT NULL
                    REFERENCES client_release_packages(release_id),
                source_record_type TEXT NOT NULL
                    CHECK (source_record_type IN ('CONCLUSION', 'ACTION')),
                source_record_id TEXT NOT NULL,
                source_record_version INTEGER NOT NULL,
                approved_evidence_reference_id TEXT NOT NULL,
                display_title TEXT NOT NULL,
                display_summary TEXT NOT NULL,
                action_owner TEXT NOT NULL DEFAULT '',
                action_target_date TEXT NOT NULL DEFAULT '',
                action_delivery_status TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            INSERT INTO client_release_entries
            SELECT * FROM client_release_entries_old
            """
        )
        conn.execute("DROP TABLE client_release_entries_old")

    def test_fresh_schema_requires_non_null_release_entry_ids(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "entry-id-fresh")
        with store.connect() as conn:
            release_entry_id = next(
                column for column in conn.execute(
                    "PRAGMA table_info(client_release_entries)"
                ).fetchall()
                if column["name"] == "release_entry_id"
            )
        assert release_entry_id["type"] == "TEXT"
        assert release_entry_id["notnull"] == 1
        assert release_entry_id["pk"] == 1

    def test_direct_null_entry_id_is_rejected_without_audit_event(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "entry-id-null-insert")
        with store.connect() as conn:
            _create_draft_package(conn, "REL-NULL-ENTRY", "ENG-FIC-0001")
            TestConclusionSourceValidation._insert_approved_conclusion(
                conn, "CON-NULL-ENTRY", "ENG-FIC-0001",
                "Null entry title", "Null entry summary", "EVD-FIC-0001",
                "Auditor", "2026-08-20T00:00:00Z",
            )
            before_events = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events"
            ).fetchone()["count"]
            with pytest.raises(
                sqlite3.IntegrityError,
                match="NOT NULL constraint failed: client_release_entries.release_entry_id",
            ):
                conn.execute(
                    "INSERT INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    "source_record_id, source_record_version, "
                    "approved_evidence_reference_id, display_title, "
                    "display_summary) VALUES "
                    "(NULL, 'REL-NULL-ENTRY', 'CONCLUSION', "
                    "'CON-NULL-ENTRY', 1, 'EVD-FIC-0001', "
                    "'Null entry title', 'Null entry summary')"
                )
            null_entry_count = conn.execute(
                "SELECT COUNT(*) AS count FROM client_release_entries "
                "WHERE release_entry_id IS NULL"
            ).fetchone()["count"]
            package_status = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-NULL-ENTRY'"
            ).fetchone()["status"]
            after_events = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events"
            ).fetchone()["count"]
        assert null_entry_count == 0
        assert package_status == "DRAFT"
        assert after_events == before_events

    def test_legacy_non_null_entry_ids_upgrade_once_and_reopen_idempotently(
        self, tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "entry-id-upgrade"
        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            self._make_release_entry_ids_nullable(conn)
            before_entries = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM client_release_entries ORDER BY rowid"
                ).fetchall()
            ]
            before_events = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM engagement_audit_events ORDER BY event_id"
                ).fetchall()
            ]
            legacy_entry_id = next(
                column for column in conn.execute(
                    "PRAGMA table_info(client_release_entries)"
                ).fetchall()
                if column["name"] == "release_entry_id"
            )
        assert legacy_entry_id["notnull"] == 0

        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            upgraded_entry_id = next(
                column for column in conn.execute(
                    "PRAGMA table_info(client_release_entries)"
                ).fetchall()
                if column["name"] == "release_entry_id"
            )
            first_entries = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM client_release_entries ORDER BY rowid"
                ).fetchall()
            ]
            first_events = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM engagement_audit_events ORDER BY event_id"
                ).fetchall()
            ]
        with WorkbenchStore(data_dir=data_dir).connect() as conn:
            second_entries = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM client_release_entries ORDER BY rowid"
                ).fetchall()
            ]
            second_events = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM engagement_audit_events ORDER BY event_id"
                ).fetchall()
            ]
        assert upgraded_entry_id["notnull"] == 1
        assert first_entries == before_entries
        assert first_events == before_events
        assert second_entries == first_entries
        assert second_events == first_events

    @pytest.mark.parametrize("null_entry_count", (1, 2), ids=("one", "multiple"))
    def test_legacy_null_entry_ids_fail_closed_without_row_changes(
        self, tmp_path: Path, null_entry_count: int,
    ) -> None:
        data_dir = tmp_path / f"entry-id-null-{null_entry_count}"
        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            self._make_release_entry_ids_nullable(conn)
            legacy_release_id = conn.execute(
                "SELECT release_id FROM client_release_entries "
                "ORDER BY rowid LIMIT 1"
            ).fetchone()["release_id"]
            for number in range(null_entry_count):
                conn.execute(
                    "INSERT INTO client_release_entries "
                    "(release_entry_id, release_id, source_record_type, "
                    "source_record_id, source_record_version, "
                    "approved_evidence_reference_id, display_title, "
                    "display_summary) VALUES "
                    "(NULL, ?, 'CONCLUSION', ?, 1, "
                    "'EVD-FIC-0001', ?, 'Legacy null entry')",
                    (
                        legacy_release_id,
                        f"CON-LEGACY-NULL-{number}",
                        f"Legacy null {number}",
                    ),
                )
            before_entries = [
                tuple(row) for row in conn.execute(
                    "SELECT * FROM client_release_entries ORDER BY rowid"
                ).fetchall()
            ]

        for _ in range(2):
            with pytest.raises(
                sqlite3.IntegrityError,
                match=(
                    "Existing client release entries contain "
                    f"{null_entry_count} NULL release entry ID\\(s\\)"
                ),
            ):
                WorkbenchStore(data_dir=data_dir).connect()
            with sqlite3.connect(store.database_path) as legacy_connection:
                after_entries = legacy_connection.execute(
                    "SELECT * FROM client_release_entries ORDER BY rowid"
                ).fetchall()
                release_entry_id = next(
                    column for column in legacy_connection.execute(
                        "PRAGMA table_info(client_release_entries)"
                    ).fetchall()
                    if column[1] == "release_entry_id"
                )
            assert after_entries == before_entries
            assert release_entry_id[3] == 0


class TestReleasePackageCreationIntegrity:
    """New packages require an attributable, increasing draft record."""

    _INVALID_CREATORS = (
        "",
        "   ",
        "\t",
        "\n",
        "\r",
        "\f",
        "\v",
        "\tCreator",
        "Creator\n",
    )

    @staticmethod
    def _created_event(
        conn: sqlite3.Connection, release_id: str, engagement_id: str,
        created_by: str, created_at: str = "2026-08-20T00:00:00Z",
    ) -> None:
        conn.execute(
            "INSERT INTO engagement_audit_events "
            "(event_id, engagement_id, event_type, recorded_at, actor) "
            "VALUES (?, ?, 'RELEASE_CREATED', ?, ?)",
            (f"EVT-{release_id}-CREATED", engagement_id, created_at, created_by),
        )

    @pytest.mark.parametrize("created_by", _INVALID_CREATORS)
    def test_blank_or_untrimmed_creator_is_rejected_at_insert(
        self, tmp_path: Path, created_by: str,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "creator-insert")
        with store.connect() as conn:
            with pytest.raises(
                sqlite3.IntegrityError, match="creator must be trimmed",
            ):
                conn.execute(
                    "INSERT INTO client_release_packages "
                    "(release_id, engagement_id, release_version, status, "
                    "created_at, created_by) VALUES "
                    "('REL-BAD-CREATOR', 'ENG-FIC-0002', 1, 'DRAFT', "
                    "'2026-08-20T00:00:00Z', ?)",
                    (created_by,),
                )

    def test_trimmed_creator_can_insert_before_creation_event(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "creator-event")
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-BEFORE-CREATION-EVENT', 'ENG-FIC-0002', 1, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )
            row = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-BEFORE-CREATION-EVENT'"
            ).fetchone()
        assert row["status"] == "DRAFT"

    def test_new_release_package_with_null_id_is_rejected(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "null-id-insert")
        with store.connect() as conn:
            with pytest.raises(
                sqlite3.IntegrityError, match="Release package ID is required",
            ):
                conn.execute(
                    "INSERT INTO client_release_packages "
                    "(release_id, engagement_id, release_version, status, "
                    "created_at, created_by) VALUES "
                    "(NULL, 'ENG-FIC-0002', 1, 'DRAFT', "
                    "'2026-08-20T00:00:00Z', 'Creator')"
                )
            null_packages = conn.execute(
                "SELECT COUNT(*) AS count FROM client_release_packages "
                "WHERE release_id IS NULL"
            ).fetchone()["count"]
        assert null_packages == 0

    def test_legacy_null_id_empty_draft_cannot_publish_or_emit_event_after_reopen(
        self, tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "legacy-null-id"
        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            conn.execute("DROP TRIGGER client_release_packages_require_draft_insert")
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "(NULL, 'ENG-FIC-0002', 1, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )

        reopened = WorkbenchStore(data_dir=data_dir)
        with reopened.connect() as conn:
            before_events = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_type = 'RELEASE_PUBLISHED'"
            ).fetchone()["count"]
            with pytest.raises(
                sqlite3.IntegrityError,
                match="must contain at least one valid entry",
            ):
                conn.execute(
                    "UPDATE client_release_packages "
                    "SET status = 'PUBLISHED', "
                    "published_at = '2026-08-20T00:00:00Z', "
                    "published_by = 'Creator' "
                    "WHERE release_id IS NULL"
                )
            legacy_package = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id IS NULL"
            ).fetchone()
            after_events = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_type = 'RELEASE_PUBLISHED'"
            ).fetchone()["count"]
        assert legacy_package["status"] == "DRAFT"
        assert after_events == before_events

    @pytest.mark.parametrize("created_by", _INVALID_CREATORS)
    def test_legacy_whitespace_creator_cannot_publish(
        self, tmp_path: Path, created_by: str,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "creator-publish")
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-BLANK-CREATOR', 'ENG-FIC-0002', 1, 'DRAFT', "
                "'2026-08-20T00:00:00Z', ?)",
                (created_by,),
            )
            self._created_event(
                conn, "REL-LEGACY-BLANK-CREATOR", "ENG-FIC-0002", created_by,
            )
            _insert_approved_action(
                conn, "ACT-LEGACY-BLANK-CREATOR", "ENG-FIC-0002",
                "Legacy action", "Owner", "2026-12-31", "OPEN", "Auditor",
                "2026-08-20T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-LEGACY-BLANK-CREATOR", "REL-LEGACY-BLANK-CREATOR",
                "ACT-LEGACY-BLANK-CREATOR", display_summary="Legacy action",
            )
            with pytest.raises(
                sqlite3.IntegrityError, match="creator must be trimmed",
            ):
                _publish_draft_package(
                    conn, "REL-LEGACY-BLANK-CREATOR", "ENG-FIC-0002",
                )

    @pytest.mark.parametrize("release_version", (0, -1, 1.5))
    def test_existing_invalid_release_versions_fail_closed_during_migration(
        self, tmp_path: Path, release_version: int | float,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "legacy-version-migration")
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute("PRAGMA ignore_check_constraints = ON")
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-INVALID-VERSION', 'ENG-FIC-0002', ?, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')",
                (release_version,),
            )
            conn.execute("PRAGMA ignore_check_constraints = OFF")
        with pytest.raises(
            sqlite3.IntegrityError,
            match="non-positive or non-integer version",
        ):
            with WorkbenchStore(
                data_dir=tmp_path / "legacy-version-migration"
            ).connect():
                pass

    @pytest.mark.parametrize(
        ("draft_version", "terminal_version", "message"),
        (
            (1.5, 1, "positive integer"),
            (0, 1, "positive integer"),
            (1, 1, "greater than terminal versions"),
            (1, 2, "greater than terminal versions"),
        ),
    )
    def test_legacy_invalid_release_version_cannot_publish(
        self,
        tmp_path: Path,
        draft_version: int | float,
        terminal_version: int,
        message: str,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "legacy-version-publish")
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-TERMINAL', 'ENG-FIC-0002', ?, 'WITHDRAWN', "
                "'2026-08-19T00:00:00Z', 'Creator')",
                (terminal_version,),
            )
            conn.execute("PRAGMA ignore_check_constraints = ON")
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-DRAFT', 'ENG-FIC-0002', ?, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')",
                (draft_version,),
            )
            conn.execute("PRAGMA ignore_check_constraints = OFF")
            self._created_event(
                conn, "REL-LEGACY-DRAFT", "ENG-FIC-0002", "Creator",
            )
            _insert_approved_action(
                conn, "ACT-LEGACY-VERSION", "ENG-FIC-0002", "Legacy action",
                "Owner", "2026-12-31", "OPEN", "Auditor",
                "2026-08-20T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-LEGACY-VERSION", "REL-LEGACY-DRAFT",
                "ACT-LEGACY-VERSION", display_summary="Legacy action",
            )
            with pytest.raises(sqlite3.IntegrityError, match=message):
                _publish_draft_package(conn, "REL-LEGACY-DRAFT", "ENG-FIC-0002")

    def test_legacy_greater_integer_release_version_can_publish(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "legacy-greater-version")
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-TERMINAL-GREATER', 'ENG-FIC-0002', 2, "
                "'WITHDRAWN', '2026-08-19T00:00:00Z', 'Creator')"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-DRAFT-GREATER', 'ENG-FIC-0002', 3, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )
            self._created_event(
                conn, "REL-LEGACY-DRAFT-GREATER", "ENG-FIC-0002", "Creator",
            )
            _insert_approved_action(
                conn, "ACT-LEGACY-GREATER", "ENG-FIC-0002", "Legacy action",
                "Owner", "2026-12-31", "OPEN", "Auditor",
                "2026-08-20T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-LEGACY-GREATER", "REL-LEGACY-DRAFT-GREATER",
                "ACT-LEGACY-GREATER", display_summary="Legacy action",
            )
            _publish_draft_package(
                conn, "REL-LEGACY-DRAFT-GREATER", "ENG-FIC-0002",
            )
            status = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-LEGACY-DRAFT-GREATER'"
            ).fetchone()["status"]
        assert status == "PUBLISHED"

    def test_duplicate_legacy_draft_versions_cannot_publish(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "legacy-duplicate-drafts")
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-DUPLICATE-ONE', 'ENG-FIC-0002', 2, 'DRAFT', "
                "'2026-08-19T00:00:00Z', 'Creator')"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-DUPLICATE-TWO', 'ENG-FIC-0002', 2, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )
            self._created_event(
                conn, "REL-LEGACY-DUPLICATE-TWO", "ENG-FIC-0002", "Creator",
            )
            _insert_approved_action(
                conn, "ACT-LEGACY-DUPLICATE", "ENG-FIC-0002", "Legacy action",
                "Owner", "2026-12-31", "OPEN", "Auditor",
                "2026-08-20T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-LEGACY-DUPLICATE", "REL-LEGACY-DUPLICATE-TWO",
                "ACT-LEGACY-DUPLICATE", display_summary="Legacy action",
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="version already exists for the engagement",
            ):
                _publish_draft_package(
                    conn, "REL-LEGACY-DUPLICATE-TWO", "ENG-FIC-0002",
                )
            package = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-LEGACY-DUPLICATE-TWO'"
            ).fetchone()
            event_count = conn.execute(
                "SELECT COUNT(*) AS count FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-LEGACY-DUPLICATE-TWO-PUB'"
            ).fetchone()["count"]
        assert package["status"] == "DRAFT"
        assert event_count == 0

    def test_valid_legacy_version_can_publish_with_later_draft(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "legacy-later-draft")
        with store.connect() as conn:
            conn.execute(
                "DROP TRIGGER client_release_packages_require_draft_insert"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-WITHDRAWN-ONE', 'ENG-FIC-0002', 1, 'WITHDRAWN', "
                "'2026-08-18T00:00:00Z', 'Creator')"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-PUBLISH-TWO', 'ENG-FIC-0002', 2, 'DRAFT', "
                "'2026-08-19T00:00:00Z', 'Creator')"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-LATER-THREE', 'ENG-FIC-0002', 3, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )
            self._created_event(
                conn, "REL-LEGACY-PUBLISH-TWO", "ENG-FIC-0002", "Creator",
                "2026-08-19T00:00:00Z",
            )
            _insert_approved_action(
                conn, "ACT-LEGACY-PUBLISH-TWO", "ENG-FIC-0002", "Legacy action",
                "Owner", "2026-12-31", "OPEN", "Auditor",
                "2026-08-19T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-LEGACY-PUBLISH-TWO", "REL-LEGACY-PUBLISH-TWO",
                "ACT-LEGACY-PUBLISH-TWO", display_summary="Legacy action",
            )
            _publish_draft_package(
                conn, "REL-LEGACY-PUBLISH-TWO", "ENG-FIC-0002",
            )
            packages = conn.execute(
                "SELECT release_id, status FROM client_release_packages "
                "WHERE release_id IN ('REL-LEGACY-PUBLISH-TWO', "
                "'REL-LEGACY-LATER-THREE') ORDER BY release_id"
            ).fetchall()
        assert [tuple(package) for package in packages] == [
            ("REL-LEGACY-LATER-THREE", "DRAFT"),
            ("REL-LEGACY-PUBLISH-TWO", "PUBLISHED"),
        ]

    def test_legacy_creator_must_match_creation_event_at_publish(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "creator-publish-event")
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-LEGACY-WRONG-CREATOR', 'ENG-FIC-0002', 1, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )
            self._created_event(
                conn, "REL-LEGACY-WRONG-CREATOR", "ENG-FIC-0002", "Other",
            )
            _insert_approved_action(
                conn, "ACT-LEGACY-WRONG-CREATOR", "ENG-FIC-0002",
                "Legacy action", "Owner", "2026-12-31", "OPEN", "Auditor",
                "2026-08-20T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-LEGACY-WRONG-CREATOR", "REL-LEGACY-WRONG-CREATOR",
                "ACT-LEGACY-WRONG-CREATOR", display_summary="Legacy action",
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="matching RELEASE_CREATED audit event",
            ):
                _publish_draft_package(
                    conn, "REL-LEGACY-WRONG-CREATOR", "ENG-FIC-0002",
                )

    def test_valid_increasing_integer_release_versions_are_accepted(
        self, tmp_path: Path,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "versions")
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-V1', 'ENG-FIC-0002', 1, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-V2', 'ENG-FIC-0002', 2, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )
            versions = conn.execute(
                "SELECT release_version FROM client_release_packages "
                "WHERE engagement_id = 'ENG-FIC-0002' ORDER BY release_version"
            ).fetchall()
        assert [row["release_version"] for row in versions] == [1, 2]

    @pytest.mark.parametrize(
        ("release_id", "release_version", "message"),
        (
            ("REL-V0", 0, "must be positive"),
            ("REL-VNEG", -1, "must be positive"),
            ("REL-VFRACTION", 1.5, "must be an integer"),
            ("REL-VREPEAT", 2, "greater than existing versions"),
            ("REL-VDECREASE", 1, "greater than existing versions"),
        ),
    )
    def test_zero_negative_fractional_repeated_and_decreasing_versions_reject(
        self,
        tmp_path: Path,
        release_id: str,
        release_version: int | float,
        message: str,
    ) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "invalid-versions")
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                "created_at, created_by) VALUES "
                "('REL-V2', 'ENG-FIC-0002', 2, 'DRAFT', "
                "'2026-08-20T00:00:00Z', 'Creator')"
            )
            with pytest.raises(sqlite3.IntegrityError, match=message):
                conn.execute(
                    "INSERT INTO client_release_packages "
                    "(release_id, engagement_id, release_version, status, "
                    "created_at, created_by) VALUES (?, 'ENG-FIC-0002', ?, "
                    "'DRAFT', '2026-08-20T00:00:00Z', 'Creator')",
                    (release_id, release_version),
                )


class TestActionSourceCardinality:
    """An ACTION source/version can appear once in each package."""

    def test_duplicate_action_is_rejected_at_insert(self, tmp_path: Path) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "action-insert")
        with store.connect() as conn:
            _create_draft_package(conn, "REL-DUP-ACTION", "ENG-FIC-0001")
            _insert_approved_action(
                conn, "ACT-DUP", "ENG-FIC-0001", "Duplicate action", "Owner",
                "2026-12-31", "OPEN", "Auditor", "2026-08-20T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-DUP-ACTION-1", "REL-DUP-ACTION", "ACT-DUP",
                display_summary="Duplicate action",
            )
            with pytest.raises(
                sqlite3.IntegrityError, match="already contains this action source version",
            ):
                _insert_action_release_entry(
                    conn, "RLE-DUP-ACTION-2", "REL-DUP-ACTION", "ACT-DUP",
                    display_summary="Duplicate action",
                )

    def test_legacy_duplicate_action_cannot_publish(self, tmp_path: Path) -> None:
        store = WorkbenchStore(data_dir=tmp_path / "action-publish")
        with store.connect() as conn:
            _create_draft_package(conn, "REL-LEGACY-DUP-ACTION", "ENG-FIC-0001")
            _insert_approved_action(
                conn, "ACT-LEGACY-DUP", "ENG-FIC-0001", "Legacy duplicate", "Owner",
                "2026-12-31", "OPEN", "Auditor", "2026-08-20T00:00:00Z",
            )
            _insert_action_release_entry(
                conn, "RLE-LEGACY-DUP-1", "REL-LEGACY-DUP-ACTION", "ACT-LEGACY-DUP",
                display_summary="Legacy duplicate",
            )
            conn.execute("DROP TRIGGER client_release_entries_one_action_source")
            _insert_action_release_entry(
                conn, "RLE-LEGACY-DUP-2", "REL-LEGACY-DUP-ACTION", "ACT-LEGACY-DUP",
                display_summary="Legacy duplicate",
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="cannot contain duplicate action source versions",
            ):
                _publish_draft_package(
                    conn, "REL-LEGACY-DUP-ACTION", "ENG-FIC-0001",
                )


class TestApprovedActionCheckMigration:
    """Existing complete tables gain the canonical target-date CHECK."""

    def test_missing_target_date_check_is_rebuilt_without_data_loss(
        self, tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "action-check-upgrade"
        store = WorkbenchStore(data_dir=data_dir)
        with store.connect() as conn:
            conn.execute("DROP TRIGGER client_release_entries_validate_action_source")
            conn.execute("DROP TRIGGER client_release_packages_validate_publish")
            conn.execute("DROP TRIGGER approved_actions_no_update_after_approval")
            conn.execute("DROP TRIGGER approved_actions_no_delete_after_approval")
            conn.execute("ALTER TABLE approved_actions RENAME TO approved_actions_old")
            conn.execute(
                """
                CREATE TABLE approved_actions (
                    action_id TEXT PRIMARY KEY, engagement_id TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1, description TEXT NOT NULL,
                    owner TEXT NOT NULL, target_date TEXT NOT NULL,
                    approval_status TEXT NOT NULL, delivery_status TEXT NOT NULL,
                    approved_by TEXT, approved_at TEXT, created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("INSERT INTO approved_actions SELECT * FROM approved_actions_old")
            conn.execute("DROP TABLE approved_actions_old")
            before = tuple(conn.execute(
                "SELECT * FROM approved_actions WHERE action_id = 'ACT-FIC-0001'"
            ).fetchone())
        upgraded = WorkbenchStore(data_dir=data_dir)
        with upgraded.connect() as conn:
            after = tuple(conn.execute(
                "SELECT * FROM approved_actions WHERE action_id = 'ACT-FIC-0001'"
            ).fetchone())
            table_sql = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' "
                "AND name = 'approved_actions'"
            ).fetchone()["sql"]
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO approved_actions "
                    "(action_id, engagement_id, version, description, owner, target_date, "
                    "approval_status, delivery_status, created_at) VALUES "
                    "('ACT-BAD-UPGRADE-DATE', 'ENG-FIC-0001', 1, 'Bad', 'Owner', "
                    "'2026-02-30', 'CANDIDATE', 'OPEN', '2026-08-20T00:00:00Z')"
                )
            conn.execute("PRAGMA ignore_check_constraints = ON")
            _insert_approved_action(
                conn, "ACT-LEGACY-BAD-DATE", "ENG-FIC-0001", "Legacy bad date",
                "Owner", "2026-02-30", "OPEN", "Auditor", "2026-08-20T00:00:00Z",
            )
            conn.execute("PRAGMA ignore_check_constraints = OFF")
            _create_draft_package(conn, "REL-LEGACY-BAD-DATE", "ENG-FIC-0001")
            conn.execute("DROP TRIGGER client_release_entries_validate_action_source")
            _insert_action_release_entry(
                conn, "RLE-LEGACY-BAD-DATE", "REL-LEGACY-BAD-DATE",
                "ACT-LEGACY-BAD-DATE", display_summary="Legacy bad date",
                action_target_date="2026-02-30",
            )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="contains an invalid source entry",
            ):
                _publish_draft_package(
                    conn, "REL-LEGACY-BAD-DATE", "ENG-FIC-0001",
                )
        assert after == before
        assert "CHECK (target_date IS strftime('%Y-%m-%d', target_date))" in table_sql


class TestApprovedActionLock:
    """Approved actions are fixed; candidate actions remain editable."""

    _TRIGGER_NAMES = {
        "approved_actions_no_update_after_approval",
        "approved_actions_no_delete_after_approval",
    }

    def test_content_mutation_blocked_on_approved(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Updating description on an APPROVED action raises
        IntegrityError."""
        _set_client_env(monkeypatch, tmp_path / "u-ac1")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-IMM-01", "ENG-FIC-0001",
                "Original desc", "Owner", "2026-12-31", "OPEN",
                "Approver", "2026-08-20T10:00:00Z",
            )
        with pytest.raises(sqlite3.IntegrityError,
                           match="Approved actions cannot be updated"):
            with store.connect() as conn:
                conn.execute(
                    "UPDATE approved_actions "
                    "SET description = 'Changed' "
                    "WHERE action_id = 'ACT-IMM-01'",
                )

    def test_owner_mutation_blocked_on_approved(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Changing owner on an APPROVED action is blocked."""
        _set_client_env(monkeypatch, tmp_path / "u-ac2")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-IMM-02", "ENG-FIC-0001",
                "Desc", "Original Owner", "2026-12-31", "OPEN",
                "Approver", "2026-08-20T10:00:00Z",
            )
        with pytest.raises(sqlite3.IntegrityError,
                           match="Approved actions cannot be updated"):
            with store.connect() as conn:
                conn.execute(
                    "UPDATE approved_actions "
                    "SET owner = 'Hijacker' "
                    "WHERE action_id = 'ACT-IMM-02'",
                )

    def test_status_change_blocked_on_approved(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An APPROVED action cannot return to CANDIDATE."""
        _set_client_env(monkeypatch, tmp_path / "u-ac3")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-IMM-03", "ENG-FIC-0001",
                "Desc", "Owner", "2026-12-31", "OPEN",
                "Approver", "2026-08-20T10:00:00Z",
            )
        with store.connect() as conn:
            with pytest.raises(sqlite3.IntegrityError,
                               match="Approved actions cannot be updated"):
                conn.execute(
                    "UPDATE approved_actions "
                    "SET approval_status = 'CANDIDATE' "
                    "WHERE action_id = 'ACT-IMM-03'",
                )
            row = conn.execute(
                "SELECT approval_status FROM approved_actions "
                "WHERE action_id = 'ACT-IMM-03'"
            ).fetchone()
            assert row is not None
            assert row["approval_status"] == "APPROVED"

    def test_approval_metadata_change_blocked_on_approved(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Approval attribution cannot change after approval."""
        _set_client_env(monkeypatch, tmp_path / "u-ac4")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-IMM-04", "ENG-FIC-0001",
                "Desc", "Owner", "2026-12-31", "OPEN",
                "Approver", "2026-08-20T10:00:00Z",
            )
        with store.connect() as conn:
            with pytest.raises(sqlite3.IntegrityError,
                               match="Approved actions cannot be updated"):
                conn.execute(
                    "UPDATE approved_actions "
                    "SET approved_by = 'New Approver', "
                    "approved_at = '2026-08-21T10:00:00Z' "
                    "WHERE action_id = 'ACT-IMM-04'",
                )
            row = conn.execute(
                "SELECT approved_by, approved_at "
                "FROM approved_actions WHERE action_id = 'ACT-IMM-04'"
            ).fetchone()
            assert row is not None
            assert row["approved_by"] == "Approver"
            assert row["approved_at"] == "2026-08-20T10:00:00Z"

    def test_content_mutation_allowed_on_candidate(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Content mutation on a CANDIDATE action is not blocked
        (the trigger only fires when OLD.approval_status='APPROVED')."""
        _set_client_env(monkeypatch, tmp_path / "u-ac5")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_candidate_action(conn, "ACT-IMM-05", "Draft desc")
        # Mutation should succeed — trigger only guards APPROVED rows
        with store.connect() as conn:
            conn.execute(
                "UPDATE approved_actions "
                "SET description = 'Updated', owner = 'New Owner' "
                "WHERE action_id = 'ACT-IMM-05'",
            )
            row = conn.execute(
                "SELECT description, owner FROM approved_actions "
                "WHERE action_id = 'ACT-IMM-05'"
            ).fetchone()
            assert row is not None
            assert row["description"] == "Updated"
            assert row["owner"] == "New Owner"

    def test_delivery_status_mutation_blocked_on_approved(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Changing delivery_status on an APPROVED action is blocked."""
        _set_client_env(monkeypatch, tmp_path / "u-ac6")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-IMM-06", "ENG-FIC-0001",
                "Desc", "Owner", "2026-12-31", "OPEN",
                "Approver", "2026-08-20T10:00:00Z",
            )
        with pytest.raises(sqlite3.IntegrityError,
                           match="Approved actions cannot be updated"):
            with store.connect() as conn:
                conn.execute(
                    "UPDATE approved_actions "
                    "SET delivery_status = 'COMPLETE' "
                    "WHERE action_id = 'ACT-IMM-06'",
                )

    def test_engagement_id_mutation_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Changing engagement_id on an APPROVED action is blocked."""
        _set_client_env(monkeypatch, tmp_path / "u-ac7")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-IMM-07", "ENG-FIC-0001",
                "Desc", "Owner", "2026-12-31", "OPEN",
                "Approver", "2026-08-20T10:00:00Z",
            )
        with pytest.raises(sqlite3.IntegrityError,
                           match="Approved actions cannot be updated"):
            with store.connect() as conn:
                conn.execute(
                    "UPDATE approved_actions "
                    "SET engagement_id = 'ENG-OTHER' "
                    "WHERE action_id = 'ACT-IMM-07'",
                )

    def test_approved_delete_blocked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An APPROVED action cannot be deleted."""
        _set_client_env(monkeypatch, tmp_path / "u-ac8")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-IMM-08", "ENG-FIC-0001",
                "Approved action", "Owner", "2026-12-31", "OPEN",
                "Approver", "2026-08-20T10:00:00Z",
            )
            with pytest.raises(sqlite3.IntegrityError,
                               match="Approved actions cannot be deleted"):
                conn.execute(
                    "DELETE FROM approved_actions "
                    "WHERE action_id = 'ACT-IMM-08'"
                )
            count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM approved_actions "
                "WHERE action_id = 'ACT-IMM-08'"
            ).fetchone()["cnt"]
        assert count == 1

    def test_candidate_delete_allowed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A CANDIDATE action can be deleted."""
        _set_client_env(monkeypatch, tmp_path / "u-ac9")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_candidate_action(conn, "ACT-IMM-09")
            conn.execute(
                "DELETE FROM approved_actions "
                "WHERE action_id = 'ACT-IMM-09'"
            )
            count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM approved_actions "
                "WHERE action_id = 'ACT-IMM-09'"
            ).fetchone()["cnt"]
        assert count == 0

    def test_new_action_with_fresh_approval_can_be_released(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Changed content uses a new action ID and approval event."""
        _set_client_env(monkeypatch, tmp_path / "u-ac10")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-IMM-OLD", "ENG-FIC-0001",
                "Original approved content", "Original Owner",
                "2026-12-31", "OPEN", "First Approver",
                "2026-08-20T00:00:00Z",
            )
            _insert_approved_action(
                conn, "ACT-IMM-NEW", "ENG-FIC-0001",
                "Changed approved content", "New Owner",
                "2027-01-31", "COMPLETE", "New Approver",
                "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-IMM-NEW", "ENG-FIC-0001")
            _insert_action_release_entry(
                conn, "RLE-IMM-NEW", "REL-IMM-NEW", "ACT-IMM-NEW",
                display_title="Changed action",
                display_summary="Changed approved content",
                action_owner="New Owner",
                action_target_date="2027-01-31",
                action_delivery_status="COMPLETE",
            )
            _publish_draft_package(conn, "REL-IMM-NEW", "ENG-FIC-0001")
            package = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-IMM-NEW'"
            ).fetchone()
            entry = conn.execute(
                "SELECT source_record_id, display_summary "
                "FROM client_release_entries "
                "WHERE release_entry_id = 'RLE-IMM-NEW'"
            ).fetchone()
            event = conn.execute(
                "SELECT actor FROM engagement_audit_events "
                "WHERE event_id = 'EVT-ACT-IMM-NEW-APPROVED'"
            ).fetchone()
        assert package["status"] == "PUBLISHED"
        assert tuple(entry) == ("ACT-IMM-NEW", "Changed approved content")
        assert event["actor"] == "New Approver"

    def test_fresh_database_has_both_lock_triggers(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A fresh database has both approved-action lock triggers."""
        _set_client_env(monkeypatch, tmp_path / "u-ac11")
        store = WorkbenchStore()
        with store.connect() as conn:
            names = {
                row["name"] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                    "AND name LIKE 'approved_actions_no_%_after_approval'"
                )
            }
        assert names == self._TRIGGER_NAMES

    def test_reopen_replaces_partial_trigger_with_both_locks(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Reopen replaces the partial trigger with both full locks."""
        _set_client_env(monkeypatch, tmp_path / "u-ac12")
        store = WorkbenchStore()
        with store.connect() as conn:
            for trigger_name in self._TRIGGER_NAMES:
                conn.execute(f"DROP TRIGGER {trigger_name}")
            conn.execute(
                """
                CREATE TRIGGER approved_actions_no_content_mutation
                BEFORE UPDATE ON approved_actions
                WHEN OLD.approval_status = 'APPROVED'
                BEGIN
                    SELECT RAISE(ABORT, 'Partial content lock')
                    WHERE OLD.description != NEW.description;
                END
                """
            )
        reopened = WorkbenchStore()
        with reopened.connect() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                "AND name LIKE 'approved_actions_no_%'"
            ).fetchall()
        assert {row["name"] for row in rows} == self._TRIGGER_NAMES

    def test_repeated_initialisation_is_idempotent(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Repeated initialization keeps two locks and audit history."""
        _set_client_env(monkeypatch, tmp_path / "u-ac13")
        first = WorkbenchStore()
        with first.connect() as conn:
            before_events = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events"
            ).fetchone()["cnt"]
        WorkbenchStore()
        third = WorkbenchStore()
        with third.connect() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                "AND name LIKE 'approved_actions_no_%_after_approval'"
            ).fetchall()
            after_events = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events"
            ).fetchone()["cnt"]
        assert {row["name"] for row in rows} == self._TRIGGER_NAMES
        assert len(rows) == 2
        assert after_events == before_events

    def test_greptile_attack_cannot_publish_changed_content(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Old approval metadata cannot publish changed action content."""
        _set_client_env(monkeypatch, tmp_path / "u-ac14")
        store = WorkbenchStore()
        with store.connect() as conn:
            _insert_approved_action(
                conn, "ACT-IMM-ATTACK", "ENG-FIC-0001",
                "Approved safe content", "Owner", "2026-12-31", "OPEN",
                "Approver", "2026-08-20T00:00:00Z",
            )
            _create_draft_package(conn, "REL-IMM-ATTACK", "ENG-FIC-0001")
            with pytest.raises(sqlite3.IntegrityError,
                               match="Approved actions cannot be updated"):
                conn.execute(
                    "UPDATE approved_actions "
                    "SET approval_status = 'CANDIDATE' "
                    "WHERE action_id = 'ACT-IMM-ATTACK'"
                )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Source action must be an APPROVED action",
            ):
                _insert_action_release_entry(
                    conn, "RLE-IMM-ATTACK", "REL-IMM-ATTACK",
                    "ACT-IMM-ATTACK",
                    display_summary="Changed attack content",
                )
            with pytest.raises(
                sqlite3.IntegrityError,
                match="Release package must contain at least one valid entry",
            ):
                _publish_draft_package(
                    conn, "REL-IMM-ATTACK", "ENG-FIC-0001"
                )
            package = conn.execute(
                "SELECT status FROM client_release_packages "
                "WHERE release_id = 'REL-IMM-ATTACK'"
            ).fetchone()
            publish_events = conn.execute(
                "SELECT COUNT(*) AS cnt FROM engagement_audit_events "
                "WHERE event_id = 'EVT-REL-IMM-ATTACK-PUB'"
            ).fetchone()["cnt"]
        assert package["status"] == "DRAFT"
        assert publish_events == 0
