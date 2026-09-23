"""SQLite storage for fictional local workbench evidence."""

from __future__ import annotations

import os
import json
import re
import sqlite3
import uuid
from hashlib import sha256
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Callable

from src.ace.workbench.extraction import EvidenceExtractionAdapter

if TYPE_CHECKING:
    from src.ace.workbench.engagement import EngagementDraft


EVIDENCE_ID_PATTERN = re.compile(r"^EVD-(?:FIC-\d{4}|[A-F0-9]{12})$")
ENGAGEMENT_ID_PATTERN = re.compile(r"^ENG-(?:FIC-\d{4}|[A-F0-9]{12})$")
CAPTURE_ATTEMPT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{7,127}$")
COMPLETION_ATTEMPT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{7,127}$")
DECISION_ATTEMPT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{7,127}$")
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _source_control_root() -> Path:
    source_workspace = REPOSITORY_ROOT.resolve()
    home_dir = Path.home().resolve()
    candidate = source_workspace
    while candidate != home_dir and candidate.parent != candidate:
        marker = candidate / ".git"
        if marker.is_file() or marker.is_dir():
            return candidate
        candidate = candidate.parent
    return source_workspace


def default_data_dir() -> Path:
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA") or str(
            Path.home() / "AppData" / "Local"
        )
        return Path(local_app_data) / "AuditCo" / "ACE" / "sqe-local-data"
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "auditco-ace" / "sqe-local-data"
    return Path.home() / ".local" / "share" / "auditco-ace" / "sqe-local-data"


DEFAULT_DATA_DIR = default_data_dir()


def _validate_data_dir(data_dir: Path, source: str) -> Path:
    resolved_dir = data_dir.expanduser().resolve()
    try:
        resolved_dir.relative_to(_source_control_root())
    except ValueError:
        return resolved_dir
    raise RuntimeError(f"{source} must be outside the source workspace")


def resolve_data_dir() -> Path:
    """Return the external local data directory without creating it."""
    configured_dir = os.environ.get("ACE_DATA_DIR")
    if configured_dir:
        return _validate_data_dir(Path(configured_dir), "ACE_DATA_DIR")
    return _validate_data_dir(default_data_dir(), "default data directory")


class EngagementNotFoundError(LookupError):
    """The controlled Engagement does not exist."""


class DuplicateEngagementReferenceError(ValueError):
    """The Engagement reference is already controlled by another draft."""


class NoReadyCurrentEngagementError(RuntimeError):
    """Capture is blocked until a ready current Engagement exists."""


class CaptureAttemptConflictError(RuntimeError):
    """A capture attempt key was reused with a different request."""


class EvidenceReviewG0Error(RuntimeError):
    """Evidence Review is blocked outside the current fictional boundary."""


@dataclass(frozen=True)
class EngagementStoreRecord:
    """Persistence representation of a controlled Engagement."""

    engagement_id: str
    creation_attempt_key: str
    title: str | None
    reference: str | None
    authority: str | None
    purpose: str | None
    scope: str | None
    exclusions: str | None
    review_start_date: str | None
    review_end_date: str | None
    evidence_cut_off_date: str | None
    accountable_auditor: str | None
    data_classification: str | None
    is_fictional: bool | None
    state: str
    created_at: str
    activated_at: str | None
    current: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class WorkbenchStore:
    """Keep fictional workbench metadata and media outside the source workspace."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = (
            resolve_data_dir()
            if data_dir is None
            else _validate_data_dir(data_dir, "Direct WorkbenchStore path")
        )
        self.media_dir = self.data_dir / "media"
        self.database_path = self.data_dir / "workbench.sqlite3"
        self._suggestions_cache: dict[str, list[dict[str, object]]] = {}

    def connect(self) -> sqlite3.Connection:
        self.media_dir.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA recursive_triggers = ON")
        try:
            self._initialise(connection)
        except Exception:
            connection.rollback()
            connection.close()
            raise
        return connection

    def _initialise(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS engagements (
                engagement_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                eoi_reference TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS obligations (
                obligation_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id),
                title TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS risks (
                risk_id TEXT PRIMARY KEY,
                obligation_id TEXT NOT NULL REFERENCES obligations(obligation_id),
                title TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS controls (
                control_id TEXT PRIMARY KEY,
                risk_id TEXT NOT NULL REFERENCES risks(risk_id),
                title TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS owners (
                owner_id TEXT PRIMARY KEY,
                control_id TEXT NOT NULL REFERENCES controls(control_id),
                name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL REFERENCES owners(owner_id),
                filename TEXT NOT NULL,
                media_type TEXT,
                media_path TEXT,
                status TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                is_capture INTEGER NOT NULL CHECK (is_capture IN (0, 1)),
                engagement_id TEXT REFERENCES engagement_setups(engagement_id),
                capture_attempt_key TEXT,
                request_sha256 TEXT,
                source_text TEXT DEFAULT NULL
            );
            CREATE TABLE IF NOT EXISTS mates (
                mate_id TEXT PRIMARY KEY,
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                title TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conclusions (
                conclusion_id TEXT PRIMARY KEY,
                mate_id TEXT NOT NULL REFERENCES mates(mate_id),
                status TEXT NOT NULL,
                title TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS relationships (
                relationship_id TEXT PRIMARY KEY,
                source_record_id TEXT NOT NULL,
                target_record_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reviews (
                review_id TEXT PRIMARY KEY,
                evidence_id TEXT NOT NULL UNIQUE REFERENCES evidence(evidence_id),
                reviewer TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                notes TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                event_type TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                actor TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence_review_contexts (
                evidence_id TEXT PRIMARY KEY REFERENCES evidence(evidence_id),
                provider TEXT,
                origin TEXT NOT NULL CHECK (origin IN ('RAW', 'DERIVED', 'AUDITOR_AUTHORED')),
                source_date TEXT,
                source_version TEXT,
                source_location TEXT,
                description TEXT,
                freshness TEXT NOT NULL CHECK (freshness IN ('CURRENT', 'STALE', 'SUPERSEDED', 'UNCERTAIN')),
                limitations TEXT,
                duplicate_evidence_id TEXT REFERENCES evidence(evidence_id),
                source_evidence_ids TEXT NOT NULL DEFAULT '[]',
                gap_status TEXT NOT NULL CHECK (gap_status IN ('NOT_REQUESTED', 'REQUESTED_NOT_PROVIDED', 'UNAVAILABLE', 'STALE', 'INADEQUATE', 'NOT_APPLICABLE')),
                gap_explanation TEXT,
                gap_materiality TEXT CHECK (
                    gap_materiality IN ('MATERIAL', 'NOT_MATERIAL', 'UNDETERMINED')
                    OR gap_materiality IS NULL
                ),
                updated_at TEXT NOT NULL,
                updated_by TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_questions (
                question_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL REFERENCES engagement_setups(engagement_id),
                control_id TEXT NOT NULL REFERENCES controls(control_id),
                question_type TEXT NOT NULL CHECK (question_type IN ('MAIN', 'IMPLEMENTATION', 'EFFECTIVENESS')),
                parent_question_id TEXT REFERENCES audit_questions(question_id),
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_question_versions (
                question_id TEXT NOT NULL REFERENCES audit_questions(question_id),
                version INTEGER NOT NULL CHECK (version > 0),
                question_text TEXT NOT NULL CHECK (length(trim(question_text)) > 0),
                purpose TEXT NOT NULL CHECK (length(trim(purpose)) > 0),
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                PRIMARY KEY (question_id, version)
            );
            CREATE TABLE IF NOT EXISTS audit_question_decisions (
                decision_id TEXT PRIMARY KEY,
                decision_attempt_key TEXT NOT NULL UNIQUE,
                request_sha256 TEXT NOT NULL,
                question_id TEXT NOT NULL,
                question_version INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('APPROVED', 'REJECTED', 'CHANGES_REQUIRED')),
                reason TEXT NOT NULL CHECK (length(trim(reason)) > 0),
                decided_at TEXT NOT NULL,
                decided_by TEXT NOT NULL,
                FOREIGN KEY (question_id, question_version)
                    REFERENCES audit_question_versions(question_id, version),
                UNIQUE (question_id, question_version)
            );
            CREATE TABLE IF NOT EXISTS proposed_evidence_links (
                proposal_id TEXT PRIMARY KEY,
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                question_id TEXT NOT NULL,
                question_version INTEGER NOT NULL,
                relevance TEXT NOT NULL CHECK (relevance IN ('SUPPORTS', 'WEAKENS', 'CONTRADICTS')),
                reason TEXT NOT NULL CHECK (length(trim(reason)) > 0),
                proposed_at TEXT NOT NULL,
                proposed_by TEXT NOT NULL,
                FOREIGN KEY (question_id, question_version)
                    REFERENCES audit_question_versions(question_id, version),
                UNIQUE (evidence_id, question_id, question_version)
            );
            CREATE TABLE IF NOT EXISTS evidence_review_completions (
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                completion_attempt_key TEXT NOT NULL,
                request_sha256 TEXT NOT NULL,
                review_id TEXT NOT NULL REFERENCES reviews(review_id),
                completed_at TEXT NOT NULL,
                PRIMARY KEY (evidence_id, completion_attempt_key),
                UNIQUE (completion_attempt_key)
            );
            CREATE TABLE IF NOT EXISTS engagement_setups (
                engagement_id TEXT PRIMARY KEY,
                creation_attempt_key TEXT NOT NULL UNIQUE,
                title TEXT,
                reference TEXT UNIQUE,
                authority TEXT,
                purpose TEXT,
                scope TEXT,
                exclusions TEXT,
                review_start_date TEXT,
                review_end_date TEXT,
                evidence_cut_off_date TEXT,
                accountable_auditor TEXT,
                data_classification TEXT CHECK (
                    data_classification IN ('FICTIONAL', 'PUBLIC', 'AUDITCO_OWNED', 'REAL_CLIENT')
                ),
                is_fictional INTEGER CHECK (is_fictional IN (0, 1)),
                state TEXT NOT NULL CHECK (state IN ('DRAFT', 'READY_FOR_CAPTURE')),
                created_at TEXT NOT NULL,
                activated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS current_engagement (
                current_slot INTEGER PRIMARY KEY CHECK (current_slot = 1),
                engagement_id TEXT NOT NULL REFERENCES engagement_setups(engagement_id)
            );
            CREATE TABLE IF NOT EXISTS engagement_audit_events (
                event_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL REFERENCES engagement_setups(engagement_id),
                event_type TEXT NOT NULL CHECK (
                    event_type IN ('ENGAGEMENT_CREATED', 'ENGAGEMENT_ACTIVATED',
                                   'CONCLUSION_APPROVED',
                                   'RELEASE_CREATED', 'RELEASE_PUBLISHED', 'RELEASE_WITHDRAWN')
                ),
                recorded_at TEXT NOT NULL,
                actor TEXT NOT NULL
            );
            CREATE TRIGGER IF NOT EXISTS engagement_audit_events_no_update
            BEFORE UPDATE ON engagement_audit_events
            BEGIN
                SELECT RAISE(ABORT, 'Engagement audit events are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS engagement_audit_events_no_delete
            BEFORE DELETE ON engagement_audit_events
            BEGIN
                SELECT RAISE(ABORT, 'Engagement audit events are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS captured_audit_events_no_update
            BEFORE UPDATE ON audit_events
            WHEN OLD.event_type = 'CAPTURED'
            BEGIN
                SELECT RAISE(ABORT, 'Captured audit events are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS captured_audit_events_no_delete
            BEFORE DELETE ON audit_events
            WHEN OLD.event_type = 'CAPTURED'
            BEGIN
                SELECT RAISE(ABORT, 'Captured audit events are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS evidence_review_completed_events_no_update
            BEFORE UPDATE ON audit_events
            WHEN OLD.event_type = 'EVIDENCE_REVIEW_COMPLETED'
            BEGIN
                SELECT RAISE(ABORT, 'Evidence Review completion events are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS evidence_review_completed_events_no_delete
            BEFORE DELETE ON audit_events
            WHEN OLD.event_type = 'EVIDENCE_REVIEW_COMPLETED'
            BEGIN
                SELECT RAISE(ABORT, 'Evidence Review completion events are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS completed_evidence_review_contexts_no_update
            BEFORE UPDATE ON evidence_review_contexts
            WHEN EXISTS (
                SELECT 1 FROM evidence_review_completions
                WHERE evidence_id = OLD.evidence_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'Completed Evidence Review contexts are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS completed_evidence_review_contexts_no_delete
            BEFORE DELETE ON evidence_review_contexts
            WHEN EXISTS (
                SELECT 1 FROM evidence_review_completions
                WHERE evidence_id = OLD.evidence_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'Completed Evidence Review contexts are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS completed_evidence_reviews_no_update
            BEFORE UPDATE ON reviews
            WHEN EXISTS (
                SELECT 1 FROM evidence_review_completions
                WHERE review_id = OLD.review_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'Completed Evidence Reviews are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS completed_evidence_reviews_no_delete
            BEFORE DELETE ON reviews
            WHEN EXISTS (
                SELECT 1 FROM evidence_review_completions
                WHERE review_id = OLD.review_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'Completed Evidence Reviews are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS evidence_review_completions_no_update
            BEFORE UPDATE ON evidence_review_completions
            BEGIN
                SELECT RAISE(ABORT, 'Evidence Review completions are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS evidence_review_completions_no_delete
            BEFORE DELETE ON evidence_review_completions
            BEGIN
                SELECT RAISE(ABORT, 'Evidence Review completions are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS completed_evidence_review_status_no_change
            BEFORE UPDATE OF status ON evidence
            WHEN EXISTS (
                SELECT 1 FROM evidence_review_completions
                WHERE evidence_id = OLD.evidence_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'Completed Evidence is immutable after review');
            END;
            CREATE TRIGGER IF NOT EXISTS completed_evidence_no_update
            BEFORE UPDATE ON evidence
            WHEN EXISTS (
                SELECT 1 FROM evidence_review_completions
                WHERE evidence_id = OLD.evidence_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'Completed Evidence is immutable after review');
            END;
            CREATE TRIGGER IF NOT EXISTS completed_evidence_no_delete
            BEFORE DELETE ON evidence
            WHEN EXISTS (
                SELECT 1 FROM evidence_review_completions
                WHERE evidence_id = OLD.evidence_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'Completed Evidence is immutable after review');
            END;
            CREATE TRIGGER IF NOT EXISTS audit_question_versions_no_update
            BEFORE UPDATE ON audit_question_versions
            BEGIN SELECT RAISE(ABORT, 'Audit Question versions are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS audit_questions_no_update
            BEFORE UPDATE ON audit_questions
            BEGIN SELECT RAISE(ABORT, 'Audit Questions are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS audit_questions_no_delete
            BEFORE DELETE ON audit_questions
            BEGIN SELECT RAISE(ABORT, 'Audit Questions are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS audit_question_versions_no_delete
            BEFORE DELETE ON audit_question_versions
            BEGIN SELECT RAISE(ABORT, 'Audit Question versions are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS audit_question_decisions_no_update
            BEFORE UPDATE ON audit_question_decisions
            BEGIN SELECT RAISE(ABORT, 'Audit Question decisions are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS audit_question_decisions_no_delete
            BEFORE DELETE ON audit_question_decisions
            BEGIN SELECT RAISE(ABORT, 'Audit Question decisions are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS proposed_evidence_links_no_update
            BEFORE UPDATE ON proposed_evidence_links
            BEGIN SELECT RAISE(ABORT, 'Proposed Evidence Links are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS proposed_evidence_links_no_delete
            BEFORE DELETE ON proposed_evidence_links
            BEGIN SELECT RAISE(ABORT, 'Proposed Evidence Links are immutable'); END;
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL REFERENCES engagement_setups(engagement_id),
                content_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                node_count INTEGER NOT NULL,
                edge_count INTEGER NOT NULL,
                warning_count INTEGER NOT NULL,
                snapshot_data TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS change_records (
                change_id TEXT PRIMARY KEY,
                export_id TEXT NOT NULL,
                record_id TEXT NOT NULL,
                snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id),
                evidence_id TEXT,
                idempotency_key TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                change_type TEXT NOT NULL CHECK (change_type IN ('added', 'removed', 'modified')),
                record_type TEXT NOT NULL,
                label TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT ''
            );
            CREATE TRIGGER IF NOT EXISTS snapshots_no_update
            BEFORE UPDATE ON snapshots
            BEGIN SELECT RAISE(ABORT, 'Snapshots are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS snapshots_no_delete
            BEFORE DELETE ON snapshots
            BEGIN SELECT RAISE(ABORT, 'Snapshots are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS change_records_no_update
            BEFORE UPDATE ON change_records
            BEGIN SELECT RAISE(ABORT, 'Change records are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS change_records_no_delete
            BEFORE DELETE ON change_records
            BEGIN SELECT RAISE(ABORT, 'Change records are append-only'); END;
            """
        )
        self._add_evidence_columns(connection)
        self._add_evidence_review_columns(connection)
        self._add_snapshot_columns(connection)
        self._add_phase6a_columns_and_tables(connection)
        self._add_phase6b1_tables(connection)
        self._validate_client_release_package_versions(connection)
        self._seed_fictional_chain(connection)
        self._seed_fictional_action(connection)
        self._migrate_legacy_evidence_review_completions(connection)
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS evidence_capture_attempt_key_unique
            ON evidence(capture_attempt_key)
            WHERE capture_attempt_key IS NOT NULL
            """
        )
        self._seed_fictional_chain(connection)
        self._create_client_release_package_insert_trigger(connection)
        self._create_client_release_entry_terminal_insert_trigger(connection)

        from src.ace.workbench.relationship_review_storage import RelationshipReviewStorage

        RelationshipReviewStorage.initialise(connection)
        connection.commit()

    @staticmethod
    def _create_client_release_entry_terminal_insert_trigger(
        connection: sqlite3.Connection,
    ) -> None:
        # ── Phase 6B1: block entry inserts after publication ─────
        # Must run after both seed calls so fictional entries are
        # inserted while the package is still DRAFT.  The trigger
        # then guards against real-world mutation post-publish.
        # Replace the predecessor trigger on every open.  SQLite does not
        # update an existing trigger with CREATE TRIGGER IF NOT EXISTS.
        # The replacement uses IS so a legacy NULL package ID is matched.
        connection.execute(
            "DROP TRIGGER IF EXISTS "
            "client_release_entries_no_insert_after_publish"
        )
        connection.execute(
            "DROP TRIGGER IF EXISTS "
            "client_release_entries_no_terminal_insert"
        )
        connection.execute(
            """
            CREATE TRIGGER client_release_entries_no_terminal_insert
            BEFORE INSERT ON client_release_entries
            BEGIN
                SELECT RAISE(ABORT,
                    'Cannot add entries to a published or withdrawn release')
                WHERE (SELECT status FROM client_release_packages
                       WHERE release_id IS NEW.release_id)
                      IN ('PUBLISHED', 'WITHDRAWN');
            END
            """
        )

    @staticmethod
    def _add_evidence_columns(connection: sqlite3.Connection) -> None:
        existing_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(evidence)")
        }
        for column, definition in (
            ("engagement_id", "TEXT REFERENCES engagement_setups(engagement_id)"),
            ("capture_attempt_key", "TEXT"),
            ("request_sha256", "TEXT"),
            ("source_text", "TEXT DEFAULT NULL"),
        ):
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE evidence ADD COLUMN {column} {definition}")

    @staticmethod
    def _add_snapshot_columns(connection: sqlite3.Connection) -> None:
        existing = {
            row["name"] for row in connection.execute("PRAGMA table_info(snapshots)")
        }
        if "snapshot_data" not in existing:
            connection.execute(
                "ALTER TABLE snapshots ADD COLUMN snapshot_data TEXT NOT NULL DEFAULT '{}'"
            )

    @staticmethod
    def _add_evidence_review_columns(connection: sqlite3.Connection) -> None:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(audit_question_versions)")
        }
        if "purpose" not in columns:
            connection.execute(
                "ALTER TABLE audit_question_versions ADD COLUMN purpose TEXT NOT NULL DEFAULT 'Legacy purpose'"
            )
        decision_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(audit_question_decisions)")
        }
        for column, definition in (
            ("decision_attempt_key", "TEXT"),
            ("request_sha256", "TEXT"),
        ):
            if column not in decision_columns:
                connection.execute(
                    f"ALTER TABLE audit_question_decisions ADD COLUMN {column} {definition}"
                )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS completion_attempt_key_unique "
            "ON evidence_review_completions(completion_attempt_key)"
        )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS decision_attempt_key_unique "
            "ON audit_question_decisions(decision_attempt_key) "
            "WHERE decision_attempt_key IS NOT NULL"
        )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS audit_question_decision_exact_version_unique "
            "ON audit_question_decisions(question_id, question_version)"
        )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS proposed_link_exact_version_unique "
            "ON proposed_evidence_links(evidence_id, question_id, question_version)"
        )

    def _migrate_legacy_evidence_review_completions(
        self, connection: sqlite3.Connection
    ) -> None:
        legacy_reviews = connection.execute(
            """
            SELECT e.evidence_id, r.review_id, r.reviewed_at, r.notes
            FROM evidence AS e
            JOIN reviews AS r ON r.evidence_id = e.evidence_id
            LEFT JOIN evidence_review_completions AS c ON c.evidence_id = e.evidence_id
            WHERE e.status = 'REVIEWED' AND c.evidence_id IS NULL
            ORDER BY e.evidence_id
            """
        ).fetchall()
        for review in legacy_reviews:
            notes = self._required_text(review["notes"], "Review notes")
            request_sha256 = self._completion_sha256(review["evidence_id"], notes)
            connection.execute(
                """
                INSERT INTO evidence_review_completions (
                    evidence_id, completion_attempt_key, request_sha256, review_id, completed_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    review["evidence_id"],
                    f"legacy-{request_sha256}",
                    request_sha256,
                    review["review_id"],
                    review["reviewed_at"],
                ),
            )

    @staticmethod
    def _add_phase6a_columns_and_tables(connection: sqlite3.Connection) -> None:
        """Phase 6A: extend conclusions + create client release tables."""

        # ── Extend conclusions table ────────────────────────────
        col_names = {
            row["name"] for row in connection.execute("PRAGMA table_info(conclusions)")
        }
        for column, definition in (
            ("engagement_id", "TEXT"),
            ("evidence_id", "TEXT"),
            ("version", "INTEGER NOT NULL DEFAULT 1"),
            ("conclusion_type", "TEXT NOT NULL DEFAULT 'CONCLUSION'"),
            ("summary", "TEXT NOT NULL DEFAULT ''"),
            ("approved_by", "TEXT"),
            ("approved_at", "TEXT"),
            ("created_at", "TEXT NOT NULL DEFAULT ''"),
        ):
            if column not in col_names:
                connection.execute(
                    f"ALTER TABLE conclusions ADD COLUMN {column} {definition}"
                )
        # Migrate existing records to version 1
        connection.execute(
            "UPDATE conclusions SET version = 1 WHERE version IS NULL OR version = 0"
        )

        # ── Migrate engagement_audit_events CHECK constraint ────
        # CREATE TABLE IF NOT EXISTS does not update an existing
        # table's CHECK, so upgraded installations retain only the
        # original two event types and silently discard new ones.
        existing_check = connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'engagement_audit_events'"
        ).fetchone()
        if existing_check is not None and "RELEASE_CREATED" not in existing_check["sql"]:
            connection.execute("ALTER TABLE engagement_audit_events "
                               "RENAME TO engagement_audit_events_old")
            connection.execute(
                """CREATE TABLE engagement_audit_events (
                       event_id TEXT PRIMARY KEY,
                       engagement_id TEXT NOT NULL
                           REFERENCES engagement_setups(engagement_id),
                       event_type TEXT NOT NULL CHECK (
                           event_type IN ('ENGAGEMENT_CREATED', 'ENGAGEMENT_ACTIVATED',
                                          'CONCLUSION_APPROVED',
                                          'RELEASE_CREATED', 'RELEASE_PUBLISHED',
                                          'RELEASE_WITHDRAWN')
                       ),
                       recorded_at TEXT NOT NULL,
                       actor TEXT NOT NULL
                   )"""
            )
            connection.execute(
                "INSERT INTO engagement_audit_events "
                "SELECT * FROM engagement_audit_events_old"
            )
            connection.execute("DROP TABLE engagement_audit_events_old")
            # Recreate immutability triggers on the new table
            connection.executescript(
                """
                CREATE TRIGGER IF NOT EXISTS engagement_audit_events_no_update
                BEFORE UPDATE ON engagement_audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'Engagement audit events are immutable');
                END;
                CREATE TRIGGER IF NOT EXISTS engagement_audit_events_no_delete
                BEFORE DELETE ON engagement_audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'Engagement audit events are immutable');
                END;
                """
            )

        # ── Client release packages ─────────────────────────────
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS client_release_packages (
                release_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL
                    REFERENCES engagement_setups(engagement_id),
                release_version INTEGER NOT NULL CHECK (
                    typeof(release_version) = 'integer'
                    AND release_version > 0
                ),
                status TEXT NOT NULL
                    CHECK (status IN ('DRAFT', 'PUBLISHED', 'WITHDRAWN')),
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                published_at TEXT,
                published_by TEXT,
                withdrawn_at TEXT,
                withdrawn_by TEXT,
                withdrawal_reason TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                one_current_release_per_engagement
            ON client_release_packages(engagement_id)
            WHERE status = 'PUBLISHED'
            """
        )

        # ── Client release entries ──────────────────────────────
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS client_release_entries (
                release_entry_id TEXT NOT NULL PRIMARY KEY,
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

        # ── Immutability triggers (PUBLISHED→WITHDRAWN and
        #    DRAFT→PUBLISHED allowed) ──────────────────────────
        connection.execute(
            """
            CREATE TRIGGER IF NOT EXISTS client_release_packages_no_update
            BEFORE UPDATE ON client_release_packages
            WHEN NOT (
                (OLD.status = 'PUBLISHED'
                 AND NEW.status = 'WITHDRAWN'
                 AND OLD.release_id IS NEW.release_id
                 AND OLD.engagement_id = NEW.engagement_id
                 AND OLD.release_version = NEW.release_version
                 AND OLD.created_at = NEW.created_at
                 AND OLD.created_by = NEW.created_by
                 AND COALESCE(OLD.published_at, '') = COALESCE(NEW.published_at, '')
                 AND COALESCE(OLD.published_by, '') = COALESCE(NEW.published_by, ''))
                OR
                (OLD.status = 'DRAFT'
                 AND NEW.status = 'PUBLISHED'
                 AND OLD.release_id IS NEW.release_id
                 AND OLD.engagement_id = NEW.engagement_id
                 AND OLD.release_version = NEW.release_version
                 AND OLD.created_at = NEW.created_at
                 AND OLD.created_by = NEW.created_by
                 AND TRIM(COALESCE(NEW.published_at, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                 AND TRIM(COALESCE(NEW.published_by, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                 AND NEW.published_by = TRIM(NEW.published_by, char(9) || char(10) || char(11) || char(12) || char(13) || ' ')
                 AND NEW.published_at IS strftime('%Y-%m-%dT%H:%M:%SZ', NEW.published_at)
                 AND NEW.published_at IS
                     strftime('%Y-%m-%dT%H:%M:%SZ', julianday(NEW.published_at))
                 AND COALESCE(OLD.withdrawn_at, '') = COALESCE(NEW.withdrawn_at, '')
                 AND COALESCE(OLD.withdrawn_by, '') = COALESCE(NEW.withdrawn_by, '')
                 AND COALESCE(OLD.withdrawal_reason, '') = COALESCE(NEW.withdrawal_reason, ''))
            )
            BEGIN
                SELECT RAISE(ABORT, 'Release packages are immutable');
            END
            """
        )
        connection.execute(
            """
            CREATE TRIGGER IF NOT EXISTS client_release_packages_no_delete
            BEFORE DELETE ON client_release_packages
            BEGIN
                SELECT RAISE(ABORT, 'Release packages are immutable');
            END
            """
        )
        connection.execute(
            """
            CREATE TRIGGER IF NOT EXISTS client_release_entries_no_update
            BEFORE UPDATE ON client_release_entries
            BEGIN
                SELECT RAISE(ABORT, 'Release entries are immutable');
            END
            """
        )
        connection.execute(
            """
            CREATE TRIGGER IF NOT EXISTS client_release_entries_no_delete
            BEFORE DELETE ON client_release_entries
            BEGIN
                SELECT RAISE(ABORT, 'Release entries are immutable');
            END
            """
        )
    @staticmethod
    def _validate_client_release_package_versions(
        connection: sqlite3.Connection,
    ) -> None:
        """Fail closed if existing release package versions are invalid."""
        invalid_version = connection.execute(
            "SELECT release_id FROM client_release_packages "
            "WHERE typeof(release_version) != 'integer' "
            "OR release_version <= 0 LIMIT 1"
        ).fetchone()
        if invalid_version is not None:
            raise sqlite3.IntegrityError(
                "Existing release package has a non-positive or non-integer version: "
                f"{invalid_version['release_id']}"
            )

    @staticmethod
    def _create_client_release_package_insert_trigger(
        connection: sqlite3.Connection,
    ) -> None:
        """Install the insert boundary after fixed history is present."""
        WorkbenchStore._validate_client_release_package_versions(connection)
        connection.execute(
            "DROP TRIGGER IF EXISTS client_release_packages_require_draft_insert"
        )
        connection.execute(
            """
            CREATE TRIGGER client_release_packages_require_draft_insert
            BEFORE INSERT ON client_release_packages
            WHEN NEW.release_id IS NULL OR NOT EXISTS (
                SELECT 1 FROM client_release_packages existing
                WHERE existing.release_id IS NEW.release_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'Release package ID is required')
                WHERE NEW.release_id IS NULL;
                SELECT RAISE(ABORT, 'Release packages must start as DRAFT')
                WHERE NEW.status != 'DRAFT';
                SELECT RAISE(ABORT, 'Release package creator must be trimmed')
                WHERE TRIM(
                    COALESCE(NEW.created_by, ''),
                    char(9) || char(10) || char(11) || char(12) || char(13) || ' '
                ) = ''
                   OR NEW.created_by != TRIM(
                       NEW.created_by,
                       char(9) || char(10) || char(11) || char(12) || char(13) || ' '
                   );
                SELECT RAISE(ABORT, 'Release version must be an integer')
                WHERE typeof(NEW.release_version) != 'integer';
                SELECT RAISE(ABORT, 'Release version must be positive')
                WHERE NEW.release_version <= 0;
                SELECT RAISE(
                    ABORT,
                    'Release version must be greater than existing versions for the engagement'
                )
                WHERE EXISTS (
                    SELECT 1 FROM client_release_packages existing
                    WHERE existing.engagement_id = NEW.engagement_id
                      AND existing.release_version >= NEW.release_version
                );
            END
            """
        )

    # ── Phase 6B1: approved actions ──────────────────────────────

    @staticmethod
    def _add_phase6b1_tables(connection: sqlite3.Connection) -> None:
        """Phase 6B1: approved_actions table + extended CHECK constraints."""

        entry_columns = connection.execute(
            "PRAGMA table_info(client_release_entries)"
        ).fetchall()
        entry_column_names = {column["name"] for column in entry_columns}
        entry_id_column = next(
            column for column in entry_columns
            if column["name"] == "release_entry_id"
        )
        requires_entry_id_upgrade = not entry_id_column["notnull"]
        if requires_entry_id_upgrade:
            null_entry_id_count = connection.execute(
                "SELECT COUNT(*) AS count FROM client_release_entries "
                "WHERE release_entry_id IS NULL"
            ).fetchone()["count"]
            if null_entry_id_count:
                raise sqlite3.IntegrityError(
                    "Existing client release entries contain "
                    f"{null_entry_id_count} NULL release entry ID(s)"
                )

        # An approved conclusion is a fixed source record. Historical
        # release snapshots can then provide immutable lineage when an
        # older released snapshot differs from legacy live source text.
        connection.execute(
            "DROP TRIGGER IF EXISTS conclusions_no_update_after_approval"
        )
        connection.execute(
            """
            CREATE TRIGGER conclusions_no_update_after_approval
            BEFORE UPDATE ON conclusions
            WHEN OLD.status = 'APPROVED'
            BEGIN
                SELECT RAISE(ABORT, 'Approved conclusions cannot be updated');
            END
            """
        )
        connection.execute(
            "DROP TRIGGER IF EXISTS conclusions_no_delete_after_approval"
        )
        connection.execute(
            """
            CREATE TRIGGER conclusions_no_delete_after_approval
            BEFORE DELETE ON conclusions
            WHEN OLD.status = 'APPROVED'
            BEGIN
                SELECT RAISE(ABORT, 'Approved conclusions cannot be deleted');
            END
            """
        )

        # ── Approved actions ────────────────────────────────────
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS approved_actions (
                action_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL
                    REFERENCES engagement_setups(engagement_id),
                version INTEGER NOT NULL DEFAULT 1,
                description TEXT NOT NULL,
                owner TEXT NOT NULL,
                target_date TEXT NOT NULL
                    CHECK (target_date IS strftime('%Y-%m-%d', target_date)),
                approval_status TEXT NOT NULL
                    CHECK (approval_status IN ('CANDIDATE', 'APPROVED')),
                delivery_status TEXT NOT NULL
                    CHECK (delivery_status IN ('OPEN', 'COMPLETE')),
                approved_by TEXT,
                approved_at TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        # Migrate table created before Phase 6B1 (no version/status cols).
        # Never drop an existing table — add columns or fail closed.
        existing_cols = connection.execute(
            "PRAGMA table_info(approved_actions)"
        ).fetchall()
        col_names = {r["name"] for r in existing_cols}
        required = {"version", "approval_status", "delivery_status",
                     "description", "owner", "target_date"}
        if existing_cols:
            missing = required - col_names
            if "approval_status" in missing:
                raise sqlite3.OperationalError(
                    "approved_actions table exists with an incompatible schema "
                    "from a pre-6B1 build. Drop the database file and re-run."
                )
            for col in sorted(missing):
                if col == "version":
                    connection.execute(
                        "ALTER TABLE approved_actions ADD COLUMN version "
                        "INTEGER NOT NULL DEFAULT 1"
                    )
                # Other columns will be added as needed

        table_sql = connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'approved_actions'"
        ).fetchone()
        canonical_check = "check(target_dateisstrftime('%y-%m-%d',target_date))"
        if (
            table_sql is not None
            and canonical_check not in "".join(table_sql["sql"].lower().split())
        ):
            # SQLite cannot add a table CHECK. Remove every dependent
            # trigger before rename. This method recreates them below.
            for trigger_name in (
                "client_release_entries_validate_action_source",
                "client_release_packages_validate_publish",
                "approved_actions_no_content_mutation",
                "approved_actions_no_update_after_approval",
                "approved_actions_no_delete_after_approval",
            ):
                connection.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
            connection.execute(
                "ALTER TABLE approved_actions RENAME TO approved_actions_old"
            )
            connection.execute(
                """
                CREATE TABLE approved_actions (
                    action_id TEXT PRIMARY KEY,
                    engagement_id TEXT NOT NULL
                        REFERENCES engagement_setups(engagement_id),
                    version INTEGER NOT NULL DEFAULT 1,
                    description TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    target_date TEXT NOT NULL
                        CHECK (target_date IS strftime('%Y-%m-%d', target_date)),
                    approval_status TEXT NOT NULL
                        CHECK (approval_status IN ('CANDIDATE', 'APPROVED')),
                    delivery_status TEXT NOT NULL
                        CHECK (delivery_status IN ('OPEN', 'COMPLETE')),
                    approved_by TEXT,
                    approved_at TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO approved_actions (
                    action_id, engagement_id, version, description, owner,
                    target_date, approval_status, delivery_status, approved_by,
                    approved_at, created_at
                )
                SELECT action_id, engagement_id, version, description, owner,
                       target_date, approval_status, delivery_status, approved_by,
                       approved_at, created_at
                FROM approved_actions_old
                """
            )
            connection.execute("DROP TABLE approved_actions_old")

        # An approved action is a fixed source record. A changed action
        # must use a new action_id and a new ACTION_APPROVED event.
        connection.execute(
            "DROP TRIGGER IF EXISTS approved_actions_no_content_mutation"
        )
        connection.execute(
            "DROP TRIGGER IF EXISTS approved_actions_no_update_after_approval"
        )
        connection.execute(
            """
            CREATE TRIGGER approved_actions_no_update_after_approval
            BEFORE UPDATE ON approved_actions
            WHEN OLD.approval_status = 'APPROVED'
            BEGIN
                SELECT RAISE(ABORT, 'Approved actions cannot be updated');
            END
            """
        )
        connection.execute(
            "DROP TRIGGER IF EXISTS approved_actions_no_delete_after_approval"
        )
        connection.execute(
            """
            CREATE TRIGGER approved_actions_no_delete_after_approval
            BEFORE DELETE ON approved_actions
            WHEN OLD.approval_status = 'APPROVED'
            BEGIN
                SELECT RAISE(ABORT, 'Approved actions cannot be deleted');
            END
            """
        )

        # ── Extend client_release_entries CHECK for ACTION ──────
        existing_check = connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'client_release_entries'"
        ).fetchone()
        if (
            existing_check is not None
            and (
                "'ACTION'" not in existing_check["sql"]
                or requires_entry_id_upgrade
            )
        ):
            connection.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_packages_validate_publish"
            )
            connection.execute(
                "ALTER TABLE client_release_entries "
                "RENAME TO client_release_entries_old"
            )
            connection.execute(
                """
                CREATE TABLE client_release_entries (
                    release_entry_id TEXT NOT NULL PRIMARY KEY,
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
            entry_copy_columns = [
                "release_entry_id",
                "release_id",
                "source_record_type",
                "source_record_id",
                "source_record_version",
                "approved_evidence_reference_id",
                "display_title",
                "display_summary",
            ]
            entry_copy_columns.extend(
                column for column in (
                    "action_owner",
                    "action_target_date",
                    "action_delivery_status",
                )
                if column in entry_column_names
            )
            copied_columns = ", ".join(entry_copy_columns)
            connection.execute(
                "INSERT INTO client_release_entries "
                f"({copied_columns}) SELECT {copied_columns} "
                "FROM client_release_entries_old"
            )
            connection.execute("DROP TABLE client_release_entries_old")
            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS client_release_entries_no_update
                BEFORE UPDATE ON client_release_entries
                BEGIN
                    SELECT RAISE(ABORT, 'Release entries are immutable');
                END
                """
            )
            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS client_release_entries_no_delete
                BEFORE DELETE ON client_release_entries
                BEGIN
                    SELECT RAISE(ABORT, 'Release entries are immutable');
                END
                """
            )
        # ── Upgrade release_packages trigger to allow DRAFT→PUBLISHED ──
        connection.execute(
            "DROP TRIGGER IF EXISTS client_release_packages_no_update"
        )
        connection.execute(
            """
            CREATE TRIGGER client_release_packages_no_update
            BEFORE UPDATE ON client_release_packages
            WHEN NOT (
                (OLD.status = 'PUBLISHED'
                 AND NEW.status = 'WITHDRAWN'
                 AND OLD.release_id IS NEW.release_id
                 AND OLD.engagement_id = NEW.engagement_id
                 AND OLD.release_version = NEW.release_version
                 AND OLD.created_at = NEW.created_at
                 AND OLD.created_by = NEW.created_by
                 AND COALESCE(OLD.published_at, '') = COALESCE(NEW.published_at, '')
                 AND COALESCE(OLD.published_by, '') = COALESCE(NEW.published_by, ''))
                OR
                (OLD.status = 'DRAFT'
                 AND NEW.status = 'PUBLISHED'
                 AND OLD.release_id IS NEW.release_id
                 AND OLD.engagement_id = NEW.engagement_id
                 AND OLD.release_version = NEW.release_version
                 AND OLD.created_at = NEW.created_at
                 AND OLD.created_by = NEW.created_by
                 AND TRIM(COALESCE(NEW.published_at, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                 AND TRIM(COALESCE(NEW.published_by, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                 AND NEW.published_by = TRIM(NEW.published_by, char(9) || char(10) || char(11) || char(12) || char(13) || ' ')
                 AND NEW.published_at IS strftime('%Y-%m-%dT%H:%M:%SZ', NEW.published_at)
                 AND NEW.published_at IS
                     strftime('%Y-%m-%dT%H:%M:%SZ', julianday(NEW.published_at))
                 AND COALESCE(OLD.withdrawn_at, '') = COALESCE(NEW.withdrawn_at, '')
                 AND COALESCE(OLD.withdrawn_by, '') = COALESCE(NEW.withdrawn_by, '')
                 AND COALESCE(OLD.withdrawal_reason, '') = COALESCE(NEW.withdrawal_reason, ''))
            )
            BEGIN
                SELECT RAISE(ABORT, 'Release packages are immutable');
            END
            """
        )
        # ── Add action snapshot columns to client_release_entries ──
        existing_cols = connection.execute(
            "PRAGMA table_info(client_release_entries)"
        ).fetchall()
        col_names = {r["name"] for r in existing_cols}
        if "action_owner" not in col_names:
            connection.execute(
                "ALTER TABLE client_release_entries "
                "ADD COLUMN action_owner TEXT NOT NULL DEFAULT ''"
            )
        if "action_target_date" not in col_names:
            connection.execute(
                "ALTER TABLE client_release_entries "
                "ADD COLUMN action_target_date TEXT NOT NULL DEFAULT ''"
            )
        if "action_delivery_status" not in col_names:
            connection.execute(
                "ALTER TABLE client_release_entries "
                "ADD COLUMN action_delivery_status TEXT NOT NULL DEFAULT ''"
            )

        # ── Extend engagement_audit_events CHECK for ACTION_APPROVED
        existing_check = connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'engagement_audit_events'"
        ).fetchone()
        if existing_check is not None and "'ACTION_APPROVED'" not in existing_check["sql"]:
            # Drop all triggers that reference engagement_audit_events
            # before the table rename — SQLite rewrites trigger bodies
            # to track renames, so any existing trigger would be left
            # pointing at the soon-to-be-dropped _old table.
            connection.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_packages_auto_publish_event"
            )
            connection.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_entries_validate_action_source"
            )
            connection.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_entries_validate_conclusion_source"
            )
            connection.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_packages_validate_publish"
            )
            connection.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_packages_require_draft_insert"
            )
            connection.execute(
                "ALTER TABLE engagement_audit_events "
                "RENAME TO engagement_audit_events_old"
            )
            connection.execute(
                """CREATE TABLE engagement_audit_events (
                       event_id TEXT PRIMARY KEY,
                       engagement_id TEXT NOT NULL
                           REFERENCES engagement_setups(engagement_id),
                       event_type TEXT NOT NULL CHECK (
                           event_type IN ('ENGAGEMENT_CREATED', 'ENGAGEMENT_ACTIVATED',
                                          'CONCLUSION_APPROVED',
                                          'RELEASE_CREATED', 'RELEASE_PUBLISHED',
                                          'RELEASE_WITHDRAWN',
                                          'ACTION_APPROVED')
                       ),
                       recorded_at TEXT NOT NULL,
                       actor TEXT NOT NULL
                   )"""
            )
            connection.execute(
                "INSERT INTO engagement_audit_events "
                "SELECT * FROM engagement_audit_events_old"
            )
            connection.execute("DROP TABLE engagement_audit_events_old")
            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS engagement_audit_events_no_update
                BEFORE UPDATE ON engagement_audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'Engagement audit events are immutable');
                END
                """
            )
            connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS engagement_audit_events_no_delete
                BEFORE DELETE ON engagement_audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'Engagement audit events are immutable');
                END
                """
            )

        # ── Recreate release validation triggers after rename ────
        WorkbenchStore._create_phase6b1_release_validation_triggers(
            connection
        )

        # ── Auto-insert RELEASE_PUBLISHED audit event ────────────
        # Must be created AFTER the engagement_audit_events CHECK
        # extension block above, because SQLite rewrites trigger
        # bodies when tables are renamed (ALTER TABLE … RENAME TO
        # rewrites table references inside all existing triggers,
        # leaving the trigger pointing at the now-dropped _old table).
        # Recreate this after the audit-event table migration.  Creating it
        # earlier would leave SQLite's renamed-table reference in its body.
        connection.execute(
            "DROP TRIGGER IF EXISTS "
            "client_release_packages_auto_publish_event"
        )
        connection.execute(
            """
            CREATE TRIGGER client_release_packages_auto_publish_event
            AFTER UPDATE ON client_release_packages
            WHEN NEW.status = 'PUBLISHED'
             AND OLD.status = 'DRAFT'
             AND NEW.release_id IS OLD.release_id
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

    @staticmethod
    def _create_phase6b1_release_validation_triggers(
        connection: sqlite3.Connection,
    ) -> None:
        """Drop and recreate ACTION and CONCLUSION source-validation
        triggers.  Must be called AFTER any engagement_audit_events
        table rename, because SQLite rewrites trigger bodies to track
        renames and a freshly-created trigger before a rename would be
        left pointing at the soon-to-be-dropped _old table."""
        # ── ACTION ──────────────────────────────────────────────
        connection.execute(
            "DROP TRIGGER IF EXISTS "
            "client_release_entries_validate_action_source"
        )
        connection.execute(
            """
            CREATE TRIGGER
                client_release_entries_validate_action_source
            BEFORE INSERT ON client_release_entries
            WHEN NEW.source_record_type = 'ACTION'
            BEGIN
                SELECT RAISE(ABORT,
                    'Source action must be an APPROVED action for this engagement at the captured version with matching snapshot values, nonblank fields, and a matching ACTION_APPROVED audit event')
                WHERE NOT EXISTS (
                    SELECT 1 FROM approved_actions a
                    WHERE a.action_id = NEW.source_record_id
                      AND a.engagement_id = (
                          SELECT engagement_id
                          FROM client_release_packages
                          WHERE release_id IS NEW.release_id)
                      AND a.approval_status = 'APPROVED'
                      AND a.version = NEW.source_record_version
                      AND a.description = NEW.display_summary
                      AND a.owner = NEW.action_owner
                      AND a.target_date = NEW.action_target_date
                      AND a.delivery_status = NEW.action_delivery_status
                      AND TRIM(NEW.display_summary, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(NEW.action_owner, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(NEW.action_target_date, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                       AND TRIM(a.description, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                       AND TRIM(a.owner, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                       AND TRIM(a.target_date, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                       AND a.target_date IS
                           strftime('%Y-%m-%d', a.target_date)
                       AND a.delivery_status IN ('OPEN', 'COMPLETE')
                      AND TRIM(NEW.display_title, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(NEW.approved_evidence_reference_id, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(COALESCE(a.approved_by, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(COALESCE(a.approved_at, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND EXISTS (
                          SELECT 1 FROM engagement_audit_events evt
                          WHERE evt.event_id =
                              'EVT-' || a.action_id || '-APPROVED'
                            AND evt.engagement_id = a.engagement_id
                            AND evt.event_type = 'ACTION_APPROVED'
                            AND evt.actor = a.approved_by
                            AND evt.recorded_at = a.approved_at
                      )
                );
            END
            """
        )
        # ── Publish-time validation ──────────────────────────────
        # Existing DRAFT entries can predate the insert-time checks.
        # Recheck every entry before publication so a Phase 6A entry
        # cannot bypass the Phase 6B1 source-integrity rules.
        connection.execute(
            "DROP TRIGGER IF EXISTS "
            "client_release_packages_validate_publish"
        )
        connection.execute(
            """
            CREATE TRIGGER client_release_packages_validate_publish
            BEFORE UPDATE ON client_release_packages
            WHEN OLD.status = 'DRAFT'
             AND NEW.status = 'PUBLISHED'
             AND NEW.release_id IS OLD.release_id
             AND NEW.engagement_id = OLD.engagement_id
             AND NEW.release_version = OLD.release_version
             AND NEW.created_at = OLD.created_at
             AND NEW.created_by = OLD.created_by
             AND TRIM(COALESCE(NEW.published_at, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
             AND TRIM(COALESCE(NEW.published_by, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
             AND NEW.published_by = TRIM(NEW.published_by, char(9) || char(10) || char(11) || char(12) || char(13) || ' ')
             AND NEW.published_at IS strftime('%Y-%m-%dT%H:%M:%SZ', NEW.published_at)
             AND NEW.published_at IS
                 strftime('%Y-%m-%dT%H:%M:%SZ', julianday(NEW.published_at))
             AND COALESCE(NEW.withdrawn_at, '') = COALESCE(OLD.withdrawn_at, '')
             AND COALESCE(NEW.withdrawn_by, '') = COALESCE(OLD.withdrawn_by, '')
             AND COALESCE(NEW.withdrawal_reason, '') = COALESCE(OLD.withdrawal_reason, '')
            BEGIN
                SELECT RAISE(ABORT, 'Release package must contain at least one valid entry')
                WHERE NOT EXISTS (
                    SELECT 1 FROM client_release_entries e
                    WHERE e.release_id IS NEW.release_id
                );
                SELECT RAISE(ABORT, 'Release package creator must be trimmed')
                WHERE TRIM(
                    COALESCE(NEW.created_by, ''),
                    char(9) || char(10) || char(11) || char(12) || char(13) || ' '
                ) = ''
                   OR NEW.created_by != TRIM(
                       NEW.created_by,
                       char(9) || char(10) || char(11) || char(12) || char(13) || ' '
                   );
                SELECT RAISE(ABORT, 'Release version must be a positive integer')
                WHERE typeof(NEW.release_version) != 'integer'
                   OR NEW.release_version <= 0;
                SELECT RAISE(
                    ABORT,
                    'Release version must be greater than terminal versions for the engagement'
                )
                WHERE EXISTS (
                    SELECT 1 FROM client_release_packages existing
                    WHERE existing.engagement_id = NEW.engagement_id
                      AND existing.release_id IS NOT NEW.release_id
                      AND existing.status IN ('PUBLISHED', 'WITHDRAWN')
                      AND existing.release_version >= NEW.release_version
                );
                SELECT RAISE(
                    ABORT,
                    'Release version already exists for the engagement'
                )
                WHERE EXISTS (
                    SELECT 1 FROM client_release_packages existing
                    WHERE existing.engagement_id = NEW.engagement_id
                      AND existing.release_id IS NOT NEW.release_id
                      AND existing.release_version = NEW.release_version
                );
                SELECT RAISE(ABORT, 'Release package cannot contain more than one conclusion')
                WHERE (
                    SELECT COUNT(*) FROM client_release_entries e
                    WHERE e.release_id IS NEW.release_id
                      AND e.source_record_type = 'CONCLUSION'
                ) > 1;
                SELECT RAISE(ABORT, 'Release package cannot contain duplicate action source versions')
                WHERE EXISTS (
                    SELECT 1 FROM client_release_entries e
                    WHERE e.release_id IS NEW.release_id
                      AND e.source_record_type = 'ACTION'
                    GROUP BY e.source_record_id, e.source_record_version
                    HAVING COUNT(*) > 1
                );
                SELECT RAISE(ABORT, 'Release package contains an invalid source entry')
                WHERE EXISTS (
                    SELECT 1 FROM client_release_entries e
                    WHERE e.release_id IS NEW.release_id
                      AND NOT (
                          (
                              e.source_record_type = 'ACTION'
                              AND EXISTS (
                                  SELECT 1 FROM approved_actions a
                                  WHERE a.action_id = e.source_record_id
                                    AND a.engagement_id = NEW.engagement_id
                                    AND a.approval_status = 'APPROVED'
                                    AND a.version = e.source_record_version
                                    AND a.description = e.display_summary
                                    AND a.owner = e.action_owner
                                    AND a.target_date = e.action_target_date
                                    AND a.delivery_status = e.action_delivery_status
                                    AND TRIM(e.display_summary, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(e.action_owner, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(e.action_target_date, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                     AND TRIM(a.description, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                     AND TRIM(a.owner, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                     AND TRIM(a.target_date, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                     AND a.target_date IS
                                         strftime('%Y-%m-%d', a.target_date)
                                     AND a.delivery_status IN ('OPEN', 'COMPLETE')
                                    AND TRIM(e.display_title, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(e.approved_evidence_reference_id, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(COALESCE(a.approved_by, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(COALESCE(a.approved_at, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND EXISTS (
                                        SELECT 1 FROM engagement_audit_events evt
                                        WHERE evt.event_id =
                                            'EVT-' || a.action_id || '-APPROVED'
                                          AND evt.engagement_id = a.engagement_id
                                          AND evt.event_type = 'ACTION_APPROVED'
                                          AND evt.actor = a.approved_by
                                          AND evt.recorded_at = a.approved_at
                                    )
                              )
                          )
                          OR
                          (
                              e.source_record_type = 'CONCLUSION'
                              AND EXISTS (
                                  SELECT 1 FROM conclusions c
                                  WHERE c.conclusion_id = e.source_record_id
                                    AND c.engagement_id = NEW.engagement_id
                                    AND c.status = 'APPROVED'
                                    AND c.version = e.source_record_version
                                    AND TRIM(c.title, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(c.summary, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(c.evidence_id, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(e.display_title, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(e.display_summary, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(e.approved_evidence_reference_id, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(COALESCE(c.approved_by, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND TRIM(COALESCE(c.approved_at, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                                    AND EXISTS (
                                        SELECT 1 FROM engagement_audit_events evt
                                        WHERE evt.event_id =
                                            'EVT-' || c.conclusion_id || '-APPROVED'
                                          AND evt.engagement_id = c.engagement_id
                                          AND evt.event_type = 'CONCLUSION_APPROVED'
                                          AND evt.actor = c.approved_by
                                          AND evt.recorded_at = c.approved_at
                                    )
                                    AND (
                                        (
                                            c.title = e.display_title
                                            AND c.summary = e.display_summary
                                            AND c.evidence_id =
                                                e.approved_evidence_reference_id
                                        )
                                        OR (
                                            c.conclusion_id = 'CON-FIC-0001'
                                            AND c.mate_id = 'MATE-FIC-0001'
                                            AND c.engagement_id = 'ENG-FIC-0001'
                                            AND c.version = 1
                                            AND c.conclusion_type = 'CONCLUSION'
                                            AND c.evidence_id = 'EVD-FIC-0001'
                                            AND c.title = 'Fictional approved field conclusion'
                                            AND c.summary = 'The field capture control is suitably designed for fictional mobile evidence collection under the pilot scope.'
                                            AND c.approved_by = 'Fictional Site Auditor'
                                            AND c.approved_at = '2026-08-19T10:00:00Z'
                                            AND c.created_at = '2026-08-12T00:00:00Z'
                                            AND e.source_record_id = 'CON-FIC-0001'
                                            AND e.source_record_version = 1
                                            AND e.approved_evidence_reference_id = 'EVD-FIC-0001'
                                            AND e.display_title = 'Approved field capture conclusion'
                                            AND e.display_summary = 'The field capture control is suitably designed for fictional mobile evidence collection under the pilot scope.'
                                            AND EXISTS (
                                                SELECT 1
                                                FROM client_release_entries prior_e
                                                JOIN client_release_packages prior_p
                                                  ON prior_p.release_id = prior_e.release_id
                                                WHERE prior_p.release_id = 'REL-FIC-PUBLISHED'
                                                  AND prior_p.engagement_id = 'ENG-FIC-0001'
                                                  AND prior_p.release_version = 2
                                                  AND prior_p.status = 'WITHDRAWN'
                                                  AND prior_p.created_at = '2026-08-19T09:30:00Z'
                                                  AND prior_p.created_by = 'Fictional Site Auditor'
                                                  AND prior_p.published_at = '2026-08-19T10:00:00Z'
                                                  AND prior_p.published_by = 'Fictional Site Auditor'
                                                  AND prior_e.release_entry_id = 'RLE-FIC-PUB-1'
                                                  AND prior_e.source_record_type = 'CONCLUSION'
                                                  AND prior_e.source_record_id = 'CON-FIC-0001'
                                                  AND prior_e.source_record_version = 1
                                                  AND prior_e.approved_evidence_reference_id = 'EVD-FIC-0001'
                                                  AND prior_e.display_title = 'Approved field capture conclusion'
                                                  AND prior_e.display_summary = 'The field capture control is suitably designed for fictional mobile evidence collection under the pilot scope.'
                                                  AND julianday(prior_p.published_at) >=
                                                      julianday(prior_p.created_at)
                                                  AND julianday(prior_p.published_at) >=
                                                      julianday(c.approved_at)
                                                  AND julianday(prior_p.published_at) <=
                                                      julianday(NEW.published_at)
                                                  AND EXISTS (
                                                      SELECT 1
                                                      FROM engagement_audit_events created_evt
                                                      WHERE created_evt.event_id = 'EVT-REL-FIC-PUB-CREATED'
                                                        AND created_evt.engagement_id = 'ENG-FIC-0001'
                                                        AND created_evt.event_type = 'RELEASE_CREATED'
                                                        AND created_evt.actor = 'Fictional Site Auditor'
                                                        AND created_evt.recorded_at = '2026-08-19T09:30:00Z'
                                                  )
                                                  AND EXISTS (
                                                      SELECT 1
                                                      FROM engagement_audit_events release_evt
                                                      WHERE release_evt.event_id = 'EVT-REL-FIC-PUB-PUBLISHED'
                                                        AND release_evt.engagement_id = 'ENG-FIC-0001'
                                                        AND release_evt.event_type = 'RELEASE_PUBLISHED'
                                                        AND release_evt.actor = 'Fictional Site Auditor'
                                                        AND release_evt.recorded_at = '2026-08-19T10:00:00Z'
                                                  )
                                            )
                                        )
                                    )
                              )
                          )
                      )
                );
                SELECT RAISE(ABORT, 'Publication time must not be before package creation')
                WHERE NEW.created_at IS NOT
                          strftime('%Y-%m-%dT%H:%M:%SZ', NEW.created_at)
                   OR NEW.created_at IS NOT
                          strftime('%Y-%m-%dT%H:%M:%SZ', julianday(NEW.created_at))
                   OR julianday(NEW.published_at) < julianday(NEW.created_at);
                SELECT RAISE(ABORT, 'Publication time must not be before source approval')
                WHERE EXISTS (
                    SELECT 1 FROM client_release_entries e
                    JOIN approved_actions a
                      ON e.source_record_type = 'ACTION'
                     AND a.action_id = e.source_record_id
                    WHERE e.release_id IS NEW.release_id
                      AND (
                          a.approved_at IS NOT
                              strftime('%Y-%m-%dT%H:%M:%SZ', a.approved_at)
                          OR a.approved_at IS NOT
                              strftime('%Y-%m-%dT%H:%M:%SZ', julianday(a.approved_at))
                          OR julianday(NEW.published_at) < julianday(a.approved_at)
                      )
                    UNION ALL
                    SELECT 1 FROM client_release_entries e
                    JOIN conclusions c
                      ON e.source_record_type = 'CONCLUSION'
                     AND c.conclusion_id = e.source_record_id
                    WHERE e.release_id IS NEW.release_id
                      AND (
                          c.approved_at IS NOT
                              strftime('%Y-%m-%dT%H:%M:%SZ', c.approved_at)
                          OR c.approved_at IS NOT
                              strftime('%Y-%m-%dT%H:%M:%SZ', julianday(c.approved_at))
                          OR julianday(NEW.published_at) < julianday(c.approved_at)
                      )
                );
                SELECT RAISE(ABORT, 'Release package requires a matching RELEASE_CREATED audit event')
                WHERE NOT EXISTS (
                    SELECT 1 FROM engagement_audit_events created_evt
                    WHERE (
                        created_evt.event_id =
                            'EVT-' || NEW.release_id || '-CREATED'
                        OR (
                            NEW.release_id = 'REL-FIC-PUBLISHED'
                            AND created_evt.event_id =
                                'EVT-REL-FIC-PUB-CREATED'
                        )
                        OR (
                            NEW.release_id = 'REL-FIC-WITHDRAWN'
                            AND created_evt.event_id =
                                'EVT-REL-FIC-WDN-CREATED'
                        )
                    )
                      AND created_evt.engagement_id = NEW.engagement_id
                      AND created_evt.event_type = 'RELEASE_CREATED'
                      AND created_evt.actor = NEW.created_by
                      AND created_evt.recorded_at = NEW.created_at
                );
            END
            """
        )
        # ── CONCLUSION ──────────────────────────────────────────
        connection.execute(
            "DROP TRIGGER IF EXISTS "
            "client_release_entries_validate_conclusion_source"
        )
        connection.execute(
            """
            CREATE TRIGGER
                client_release_entries_validate_conclusion_source
            BEFORE INSERT ON client_release_entries
            WHEN NEW.source_record_type = 'CONCLUSION'
            BEGIN
                SELECT RAISE(ABORT,
                    'Source conclusion must be an APPROVED conclusion for this engagement at the captured version with matching snapshot values, nonblank fields, and a matching CONCLUSION_APPROVED audit event')
                WHERE NOT EXISTS (
                    SELECT 1 FROM conclusions c
                    WHERE c.conclusion_id = NEW.source_record_id
                      AND c.engagement_id = (
                          SELECT engagement_id
                          FROM client_release_packages
                          WHERE release_id IS NEW.release_id)
                      AND c.status = 'APPROVED'
                      AND c.version = NEW.source_record_version
                      AND TRIM(c.title, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(c.summary, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(c.evidence_id, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(NEW.display_title, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(NEW.display_summary, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(NEW.approved_evidence_reference_id, char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(COALESCE(c.approved_by, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND TRIM(COALESCE(c.approved_at, ''), char(9) || char(10) || char(11) || char(12) || char(13) || ' ') <> ''
                      AND EXISTS (
                          SELECT 1 FROM engagement_audit_events evt
                          WHERE evt.event_id =
                              'EVT-' || c.conclusion_id || '-APPROVED'
                            AND evt.engagement_id = c.engagement_id
                            AND evt.event_type = 'CONCLUSION_APPROVED'
                            AND evt.actor = c.approved_by
                            AND evt.recorded_at = c.approved_at
                      )
                      AND (
                          (
                              c.title = NEW.display_title
                              AND c.summary = NEW.display_summary
                              AND c.evidence_id =
                                  NEW.approved_evidence_reference_id
                          )
                          OR (
                               c.conclusion_id = 'CON-FIC-0001'
                               AND c.mate_id = 'MATE-FIC-0001'
                               AND c.engagement_id = 'ENG-FIC-0001'
                               AND c.version = 1
                               AND c.conclusion_type = 'CONCLUSION'
                               AND c.evidence_id = 'EVD-FIC-0001'
                               AND c.title = 'Fictional approved field conclusion'
                               AND c.summary = 'The field capture control is suitably designed for fictional mobile evidence collection under the pilot scope.'
                               AND c.approved_by = 'Fictional Site Auditor'
                               AND c.approved_at = '2026-08-19T10:00:00Z'
                               AND c.created_at = '2026-08-12T00:00:00Z'
                              AND NEW.source_record_id = 'CON-FIC-0001'
                              AND NEW.source_record_version = 1
                              AND NEW.approved_evidence_reference_id = 'EVD-FIC-0001'
                              AND NEW.display_title = 'Approved field capture conclusion'
                              AND NEW.display_summary = 'The field capture control is suitably designed for fictional mobile evidence collection under the pilot scope.'
                              AND EXISTS (
                                  SELECT 1
                                  FROM client_release_entries prior_e
                                  JOIN client_release_packages prior_p
                                    ON prior_p.release_id = prior_e.release_id
                                  WHERE prior_p.release_id = 'REL-FIC-PUBLISHED'
                                    AND prior_p.engagement_id = 'ENG-FIC-0001'
                                    AND prior_p.release_version = 2
                                    AND prior_p.status = 'PUBLISHED'
                                    AND prior_p.created_at = '2026-08-19T09:30:00Z'
                                    AND prior_p.created_by = 'Fictional Site Auditor'
                                    AND prior_p.published_at = '2026-08-19T10:00:00Z'
                                    AND prior_p.published_by = 'Fictional Site Auditor'
                                    AND prior_e.release_entry_id = 'RLE-FIC-PUB-1'
                                    AND prior_e.source_record_type = 'CONCLUSION'
                                    AND prior_e.source_record_id = 'CON-FIC-0001'
                                    AND prior_e.source_record_version = 1
                                    AND prior_e.approved_evidence_reference_id = 'EVD-FIC-0001'
                                    AND prior_e.display_title = 'Approved field capture conclusion'
                                    AND prior_e.display_summary = 'The field capture control is suitably designed for fictional mobile evidence collection under the pilot scope.'
                                    AND julianday(prior_p.published_at) >=
                                        julianday(prior_p.created_at)
                                    AND julianday(prior_p.published_at) >=
                                        julianday(c.approved_at)
                                    AND EXISTS (
                                        SELECT 1
                                        FROM engagement_audit_events created_evt
                                        WHERE created_evt.event_id = 'EVT-REL-FIC-PUB-CREATED'
                                          AND created_evt.engagement_id = 'ENG-FIC-0001'
                                          AND created_evt.event_type = 'RELEASE_CREATED'
                                          AND created_evt.actor = 'Fictional Site Auditor'
                                          AND created_evt.recorded_at = '2026-08-19T09:30:00Z'
                                    )
                                    AND EXISTS (
                                        SELECT 1
                                        FROM engagement_audit_events release_evt
                                        WHERE release_evt.event_id = 'EVT-REL-FIC-PUB-PUBLISHED'
                                          AND release_evt.engagement_id = 'ENG-FIC-0001'
                                          AND release_evt.event_type = 'RELEASE_PUBLISHED'
                                          AND release_evt.actor = 'Fictional Site Auditor'
                                          AND release_evt.recorded_at = '2026-08-19T10:00:00Z'
                                    )
                              )
                          )
                      )
                );
            END
            """
        )
        connection.execute(
            "DROP TRIGGER IF EXISTS client_release_entries_one_conclusion"
        )
        connection.execute(
            """
            CREATE TRIGGER client_release_entries_one_conclusion
            BEFORE INSERT ON client_release_entries
            WHEN NEW.source_record_type = 'CONCLUSION'
             AND EXISTS (
                 SELECT 1 FROM client_release_entries existing
                 WHERE existing.release_id IS NEW.release_id
                   AND existing.source_record_type = 'CONCLUSION'
                   AND existing.release_entry_id != NEW.release_entry_id
             )
            BEGIN
                SELECT RAISE(ABORT, 'Release package already contains a conclusion');
            END
            """
        )
        connection.execute(
            "DROP TRIGGER IF EXISTS client_release_entries_one_action_source"
        )
        connection.execute(
            """
            CREATE TRIGGER client_release_entries_one_action_source
            BEFORE INSERT ON client_release_entries
            WHEN NEW.source_record_type = 'ACTION'
             AND EXISTS (
                 SELECT 1 FROM client_release_entries existing
                 WHERE existing.release_id IS NEW.release_id
                   AND existing.source_record_type = 'ACTION'
                   AND existing.source_record_id = NEW.source_record_id
                   AND existing.source_record_version = NEW.source_record_version
                   AND existing.release_entry_id != NEW.release_entry_id
             )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Release package already contains this action source version'
                );
            END
            """
        )

    @staticmethod
    def _seed_fictional_action(connection: sqlite3.Connection) -> None:
        """Phase 6B1: action release entry is seeded inside
        _seed_fictional_chain before publication; this method exists
        as an extension point for future seed data."""

    @staticmethod
    def _seed_fictional_chain(connection: sqlite3.Connection) -> None:
        connection.execute(
            "INSERT OR IGNORE INTO engagements VALUES (?, ?, ?)",
            ("ENG-FIC-0001", "Fictional Mobile Field Capture Engagement", "EOI-FIC-0001"),
        )
        seeded = connection.execute(
            """
            INSERT OR IGNORE INTO engagement_setups (
                engagement_id, creation_attempt_key, title, reference, authority, purpose,
                scope, exclusions, review_start_date, review_end_date, evidence_cut_off_date,
                accountable_auditor, data_classification, is_fictional, state, created_at,
                activated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ENG-FIC-0001",
                "seeded-fictional-chain",
                "Fictional Mobile Field Capture Engagement",
                "ENG-FIC-0001",
                "Fictional pilot authority",
                "Fictional mobile field evidence capture",
                "Fictional field activities",
                "Real-client information and evidence",
                "2026-08-01",
                "2026-08-31",
                "2026-08-31",
                "Fictional Site Auditor",
                "FICTIONAL",
                1,
                "READY_FOR_CAPTURE",
                "2026-08-12T00:00:00Z",
                "2026-08-12T00:00:00Z",
            ),
        )
        if seeded.rowcount:
            connection.execute(
                "INSERT OR IGNORE INTO current_engagement VALUES (?, ?)", (1, "ENG-FIC-0001")
            )
        connection.execute(
            "INSERT OR IGNORE INTO obligations VALUES (?, ?, ?)",
            ("OBL-FIC-0001", "ENG-FIC-0001", "Fictional field evidence obligation"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO risks VALUES (?, ?, ?)",
            ("RSK-FIC-0001", "OBL-FIC-0001", "Fictional evidence trace risk"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO controls VALUES (?, ?, ?)",
            ("CTL-FIC-0001", "RSK-FIC-0001", "Fictional capture control"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO owners VALUES (?, ?, ?)",
            ("OWN-FIC-0001", "CTL-FIC-0001", "Fictional Site Auditor"),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO evidence (
                evidence_id, owner_id, filename, media_type, media_path, status, captured_at,
                is_capture, engagement_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EVD-FIC-0001",
                "OWN-FIC-0001",
                "Fictional evidence placeholder",
                None,
                None,
                "PENDING_REVIEW",
                "2026-08-12T00:00:00Z",
                0,
                "ENG-FIC-0001",
            ),
        )
        connection.execute(
            """UPDATE evidence SET engagement_id = ?
            WHERE evidence_id = ? AND engagement_id IS NULL""",
            ("ENG-FIC-0001", "EVD-FIC-0001"),
        )
        connection.execute(
            """UPDATE evidence SET source_text = ?
            WHERE evidence_id = ? AND source_text IS NULL""",
            (
                "The inspection was completed on 12 August 2026 by "
                "Fictional Site Auditor. No quorum was recorded in the minutes. "
                "The responsible officer assigned to follow-up is Fictional Safety Manager. "
                "Five non-conformances were identified during the walkthrough. "
                "Reference REF-WHS-0042 requires further review. "
                "The assessment has been approved.",
                "EVD-FIC-0001",
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO mates VALUES (?, ?, ?)",
            ("MATE-FIC-0001", "EVD-FIC-0001", "Fictional MATE assessment"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO conclusions "
            "(conclusion_id, mate_id, status, title, engagement_id, evidence_id, "
            " version, conclusion_type, summary, approved_by, approved_at, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "CON-FIC-0001",
                "MATE-FIC-0001",
                "APPROVED",
                "Approved field capture conclusion",
                "ENG-FIC-0001",
                "EVD-FIC-0001",
                1,
                "CONCLUSION",
                "The field capture control is suitably designed for "
                "fictional mobile evidence collection under the pilot scope.",
                "Fictional Site Auditor",
                "2026-08-19T10:00:00Z",
                "2026-08-12T00:00:00Z",
            ),
        )
        # Migrate a legacy conclusion row that was created by an earlier phase
        # (INSERT OR IGNORE skips it, leaving it with the old 4-column schema).
        connection.execute(
            """
            UPDATE conclusions SET
                status = 'APPROVED',
                title = ?,
                engagement_id = ?,
                evidence_id = ?,
                version = 1,
                conclusion_type = 'CONCLUSION',
                summary = ?,
                approved_by = ?,
                approved_at = ?,
                created_at = ?
            WHERE conclusion_id = 'CON-FIC-0001' AND status = 'CANDIDATE'
            """,
            (
                "Approved field capture conclusion",
                "ENG-FIC-0001",
                "EVD-FIC-0001",
                "The field capture control is suitably designed for "
                "fictional mobile evidence collection under the pilot scope.",
                "Fictional Site Auditor",
                "2026-08-19T10:00:00Z",
                "2026-08-12T00:00:00Z",
            ),
        )
        # Record the fictional approval as an audit event
        connection.execute(
            "INSERT OR IGNORE INTO engagement_audit_events "
            "(event_id, engagement_id, event_type, recorded_at, actor) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "EVT-CON-FIC-0001-APPROVED",
                "ENG-FIC-0001",
                "CONCLUSION_APPROVED",
                "2026-08-19T10:00:00Z",
                "Fictional Site Auditor",
            ),
        )
        # Stale draft of a different conclusion (not in any package)
        connection.execute(
            "INSERT OR IGNORE INTO conclusions "
            "(conclusion_id, mate_id, status, title, engagement_id, evidence_id, "
            " version, conclusion_type, summary, approved_by, approved_at, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "CON-FIC-STALE",
                "MATE-FIC-0001",
                "CANDIDATE",
                "Fictional stale draft conclusion",
                "ENG-FIC-0001",
                "EVD-FIC-0001",
                1,
                "CONCLUSION",
                "An earlier draft that was never approved.",
                None,
                None,
                "2026-08-18T00:00:00Z",
            ),
        )
        # ── Cross-engagement test record ────────────────────────
        connection.execute(
            "INSERT OR IGNORE INTO engagements VALUES (?, ?, ?)",
            ("ENG-FIC-0002", "Fictional Second Engagement", "EOI-FIC-0002"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO engagement_setups ("
            " engagement_id, creation_attempt_key, title, reference, authority,"
            " purpose, scope, exclusions, review_start_date, review_end_date,"
            " evidence_cut_off_date, accountable_auditor, data_classification,"
            " is_fictional, state, created_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ENG-FIC-0002", "seeded-fictional-chain-2",
                "Fictional Second Engagement", "ENG-FIC-0002",
                "Fictional pilot authority", "Fictional secondary engagement",
                "Fictional scope", "Real-client information",
                "2026-08-01", "2026-08-31", "2026-08-31",
                "Fictional Site Auditor", "FICTIONAL", 1,
                "READY_FOR_CAPTURE", "2026-08-19T00:00:00Z",
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "EVD-FIC-0002", "OWN-FIC-0001", "fictional-evidence-2.txt",
                "text/plain", None, "PENDING_REVIEW",
                "2026-08-19T00:00:00Z", 0, "ENG-FIC-0002",
                "seeded-evid-2", None, None,
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO mates VALUES (?, ?, ?)",
            ("MATE-FIC-0002", "EVD-FIC-0002", "Fictional MATE assessment (second engagement)"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO conclusions "
            "(conclusion_id, mate_id, status, title, engagement_id, evidence_id, "
            " version, conclusion_type, summary, approved_by, approved_at, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "CON-FIC-0002",
                "MATE-FIC-0002",
                "CANDIDATE",
                "Fictional candidate (other engagement)",
                "ENG-FIC-0002",
                "EVD-FIC-0002",
                1,
                "CONCLUSION",
                "A CANDIDATE conclusion from a different engagement.",
                None,
                None,
                "2026-08-19T00:00:00Z",
            ),
        )
        # ── Release packages ────────────────────────────────────
        # Do not add the version-3 draft while the fixed Phase 6A
        # published package needs its version-3 upgrade release.
        connection.execute(
            "INSERT OR IGNORE INTO client_release_packages "
            "(release_id, engagement_id, release_version, status, created_at,"
            " created_by, published_at, published_by, withdrawn_at,"
            " withdrawn_by, withdrawal_reason)"
            " SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
            " WHERE NOT EXISTS ("
            "     SELECT 1 FROM client_release_packages legacy"
            "     WHERE legacy.release_id = 'REL-FIC-PUBLISHED'"
            "       AND legacy.engagement_id = 'ENG-FIC-0001'"
            "       AND legacy.status = 'PUBLISHED'"
            "       AND NOT EXISTS ("
            "           SELECT 1 FROM client_release_entries entry"
            "           WHERE entry.release_id = legacy.release_id"
            "             AND entry.source_record_type = 'ACTION'"
            "       )"
            " ) AND NOT EXISTS ("
            "     SELECT 1 FROM client_release_packages existing_version"
            "     WHERE existing_version.engagement_id = 'ENG-FIC-0001'"
            "       AND existing_version.release_version = 3"
            "       AND existing_version.release_id IS NOT 'REL-FIC-DRAFT'"
            " ) AND NOT EXISTS ("
            "     SELECT 1 FROM client_release_packages upgrade"
            "     WHERE upgrade.release_id = 'REL-FIC-PHASE6B1-UPGRADE'"
            " )",
            (
                "REL-FIC-DRAFT",
                "ENG-FIC-0001", 3, "DRAFT",
                "2026-08-19T09:00:00Z", "Fictional Site Auditor",
                None, None, None, None, None,
            ),
        )
        draft_package = connection.execute(
            "SELECT engagement_id, created_at, created_by "
            "FROM client_release_packages "
            "WHERE release_id = 'REL-FIC-DRAFT'"
        ).fetchone()
        if draft_package is not None:
            connection.execute(
                "INSERT OR IGNORE INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "EVT-REL-FIC-DRAFT-CREATED",
                    draft_package["engagement_id"],
                    "RELEASE_CREATED",
                    draft_package["created_at"],
                    draft_package["created_by"],
                ),
            )
        connection.execute(
            "INSERT OR IGNORE INTO client_release_packages "
            "(release_id, engagement_id, release_version, status, created_at,"
            " created_by, published_at, published_by, withdrawn_at,"
            " withdrawn_by, withdrawal_reason)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "REL-FIC-PUBLISHED",
                "ENG-FIC-0001", 2, "DRAFT",
                "2026-08-19T09:30:00Z", "Fictional Site Auditor",
                None, None,
                None, None, None,
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO engagement_audit_events "
            "(event_id, engagement_id, event_type, recorded_at, actor) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "EVT-REL-FIC-PUB-CREATED",
                "ENG-FIC-0001",
                "RELEASE_CREATED",
                "2026-08-19T09:30:00Z",
                "Fictional Site Auditor",
            ),
        )
        # Build the fictional withdrawn package through the normal
        # DRAFT -> PUBLISHED -> WITHDRAWN lifecycle.  Skip this optional
        # seed if another package is already current during an upgrade.
        existing_withdrawn = connection.execute(
            "SELECT 1 FROM client_release_packages "
            "WHERE release_id = 'REL-FIC-WITHDRAWN'"
        ).fetchone()
        current_published = connection.execute(
            "SELECT 1 FROM client_release_packages "
            "WHERE engagement_id = 'ENG-FIC-0001' "
            "AND status = 'PUBLISHED'"
        ).fetchone()
        phase6b1_upgrade_exists = connection.execute(
            "SELECT 1 FROM client_release_packages "
            "WHERE release_id = 'REL-FIC-PHASE6B1-UPGRADE'"
        ).fetchone()
        if (
            existing_withdrawn is None
            and current_published is None
            and phase6b1_upgrade_exists is None
        ):
            connection.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                " created_at, created_by) "
                "VALUES (?, ?, ?, 'DRAFT', ?, ?)",
                (
                    "REL-FIC-WITHDRAWN", "ENG-FIC-0001", 1,
                    "2026-08-19T09:00:00Z", "Fictional Site Auditor",
                ),
            )
            connection.execute(
                "INSERT OR IGNORE INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "EVT-REL-FIC-WDN-CREATED", "ENG-FIC-0001",
                    "RELEASE_CREATED", "2026-08-19T09:00:00Z",
                    "Fictional Site Auditor",
                ),
            )
            connection.execute(
                "INSERT INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "RLE-FIC-WDN-1", "REL-FIC-WITHDRAWN", "CONCLUSION",
                    "CON-FIC-0001", 1, "EVD-FIC-0001",
                    "Approved field capture conclusion",
                    "The field capture control is suitably designed for "
                    "fictional mobile evidence collection under the pilot scope.",
                ),
            )
            connection.execute(
                "UPDATE client_release_packages "
                "SET status = 'PUBLISHED', "
                "published_at = '2026-08-19T10:00:00Z', "
                "published_by = 'Fictional Site Auditor' "
                "WHERE release_id = 'REL-FIC-WITHDRAWN'"
            )
            connection.execute(
                "UPDATE client_release_packages "
                "SET status = 'WITHDRAWN', "
                "withdrawn_at = '2026-08-19T10:30:00Z', "
                "withdrawn_by = 'Fictional Site Auditor', "
                "withdrawal_reason = 'Superseded by updated release' "
                "WHERE release_id = 'REL-FIC-WITHDRAWN'"
            )
            connection.execute(
                "INSERT OR IGNORE INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "EVT-REL-FIC-WDN-WITHDRAWN", "ENG-FIC-0001",
                    "RELEASE_WITHDRAWN", "2026-08-19T10:30:00Z",
                    "Fictional Site Auditor",
                ),
            )
        # ── Phase 6B1: approved action source ───────────────────
        connection.execute(
            "INSERT OR IGNORE INTO approved_actions "
            "(action_id, engagement_id, version, description, owner, "
            " target_date, approval_status, delivery_status, "
            " approved_by, approved_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ACT-FIC-0001",
                "ENG-FIC-0001",
                1,
                "Review and update the mobile field capture process "
                "to reduce photo upload errors observed during the inspection.",
                "Fictional Safety Manager",
                "2026-09-30",
                "APPROVED",
                "OPEN",
                "Fictional Site Auditor",
                "2026-08-19T09:30:00Z",
                "2026-08-19T09:30:00Z",
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO engagement_audit_events "
            "(event_id, engagement_id, event_type, recorded_at, actor) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "EVT-ACT-FIC-0001-APPROVED",
                "ENG-FIC-0001",
                "ACTION_APPROVED",
                "2026-08-19T09:30:00Z",
                "Fictional Site Auditor",
            ),
        )

        # Upgrade the fixed fictional Phase 6A current package without
        # changing its entries or original publication metadata.  The
        # fixed new ID makes repeated initialization a no-op.
        legacy_current = connection.execute(
            "SELECT engagement_id, release_version FROM client_release_packages p "
            "WHERE p.release_id = 'REL-FIC-PUBLISHED' "
            "AND p.engagement_id = 'ENG-FIC-0001' "
            "AND p.status = 'PUBLISHED' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM client_release_entries e "
            "  WHERE e.release_id = p.release_id "
            "  AND e.source_record_type = 'ACTION'"
            ") "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM client_release_packages current "
            "  WHERE current.engagement_id = p.engagement_id "
            "  AND current.status = 'PUBLISHED' "
            "  AND current.release_id != p.release_id"
            ")"
        ).fetchone()
        upgrade_package = connection.execute(
            "SELECT status FROM client_release_packages "
            "WHERE release_id = 'REL-FIC-PHASE6B1-UPGRADE'"
        ).fetchone()
        legacy_conclusion_entry = connection.execute(
            "SELECT source_record_version, "
            "approved_evidence_reference_id, display_title, "
            "display_summary FROM client_release_entries "
            "WHERE release_id = 'REL-FIC-PUBLISHED' "
            "AND source_record_type = 'CONCLUSION' "
            "AND source_record_id = 'CON-FIC-0001' "
            "ORDER BY release_entry_id LIMIT 1"
        ).fetchone()
        if (
            legacy_current is not None
            and upgrade_package is None
            and legacy_conclusion_entry is not None
        ):
            # Include DRAFT and WITHDRAWN packages. Publication requires a
            # version that is unique and greater than every package version.
            next_release_version = connection.execute(
                "SELECT COALESCE(MAX(release_version), 0) + 1 "
                "AS next_release_version "
                "FROM client_release_packages WHERE engagement_id = ?",
                (legacy_current["engagement_id"],),
            ).fetchone()["next_release_version"]
            connection.execute(
                "INSERT INTO client_release_packages "
                "(release_id, engagement_id, release_version, status, "
                " created_at, created_by) "
                "VALUES (?, ?, ?, 'DRAFT', ?, ?)",
                (
                    "REL-FIC-PHASE6B1-UPGRADE",
                    "ENG-FIC-0001",
                    next_release_version,
                    "2026-08-19T10:30:00Z",
                    "Fictional Site Auditor",
                ),
            )
            connection.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "EVT-REL-FIC-PHASE6B1-UPGRADE-CREATED",
                    "ENG-FIC-0001",
                    "RELEASE_CREATED",
                    "2026-08-19T10:30:00Z",
                    "Fictional Site Auditor",
                ),
            )
            connection.execute(
                "INSERT INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "RLE-FIC-PHASE6B1-UPGRADE-CONCLUSION",
                    "REL-FIC-PHASE6B1-UPGRADE",
                    "CONCLUSION",
                    "CON-FIC-0001",
                    legacy_conclusion_entry["source_record_version"],
                    legacy_conclusion_entry[
                        "approved_evidence_reference_id"
                    ],
                    legacy_conclusion_entry["display_title"],
                    legacy_conclusion_entry["display_summary"],
                ),
            )
            connection.execute(
                "INSERT INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary, action_owner, action_target_date, "
                " action_delivery_status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "RLE-FIC-PHASE6B1-UPGRADE-ACTION",
                    "REL-FIC-PHASE6B1-UPGRADE",
                    "ACTION",
                    "ACT-FIC-0001",
                    1,
                    "EVD-FIC-0001",
                    "Improve field capture workflow",
                    "Review and update the mobile field capture process "
                    "to reduce photo upload errors observed during the inspection.",
                    "Fictional Safety Manager",
                    "2026-09-30",
                    "OPEN",
                ),
            )
            connection.execute(
                "UPDATE client_release_packages "
                "SET status = 'WITHDRAWN', "
                "withdrawn_at = '2026-08-19T10:45:00Z', "
                "withdrawn_by = 'Fictional Site Auditor', "
                "withdrawal_reason = 'Superseded by Phase 6B1 action release' "
                "WHERE release_id = 'REL-FIC-PUBLISHED' "
                "AND status = 'PUBLISHED'"
            )
            connection.execute(
                "INSERT INTO engagement_audit_events "
                "(event_id, engagement_id, event_type, recorded_at, actor) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "EVT-REL-FIC-PUBLISHED-PHASE6B1-WITHDRAWN",
                    "ENG-FIC-0001",
                    "RELEASE_WITHDRAWN",
                    "2026-08-19T10:45:00Z",
                    "Fictional Site Auditor",
                ),
            )
            connection.execute(
                "UPDATE client_release_packages "
                "SET status = 'PUBLISHED', "
                "published_at = '2026-08-19T11:00:00Z', "
                "published_by = 'Fictional Site Auditor' "
                "WHERE release_id = 'REL-FIC-PHASE6B1-UPGRADE' "
                "AND status = 'DRAFT'"
            )

        # On a fresh database, assemble the original fictional package
        # while it is DRAFT.  Reopen never changes a terminal package.
        existing_publish = connection.execute(
            "SELECT 1 FROM client_release_packages "
            "WHERE release_id = 'REL-FIC-PUBLISHED' "
            "  AND status != 'DRAFT'"
        ).fetchone()
        if existing_publish is None:
            # The package may be PUBLISHED from a previous store run
            # whose audit events were dropped.  Drop the INSERT guard
            # temporarily so entries can be reassembled; it is recreated
            # unconditionally after both seed calls.
            connection.execute(
                "DROP TRIGGER IF EXISTS "
                "client_release_entries_no_insert_after_publish"
            )
            connection.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary, action_owner, action_target_date, "
                " action_delivery_status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "RLE-FIC-ACT-1",
                    "REL-FIC-PUBLISHED",
                    "ACTION",
                    "ACT-FIC-0001",
                    1,
                    "EVD-FIC-0001",
                    "Improve field capture workflow",
                    "Review and update the mobile field capture process "
                    "to reduce photo upload errors observed during the inspection.",
                    "Fictional Safety Manager",
                    "2026-09-30",
                    "OPEN",
                ),
            )

            connection.execute(
                "INSERT OR IGNORE INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, source_record_id,"
                " source_record_version, approved_evidence_reference_id, display_title,"
                " display_summary)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "RLE-FIC-PUB-1",
                    "REL-FIC-PUBLISHED",
                    "CONCLUSION",
                    "CON-FIC-0001", 1,
                    "EVD-FIC-0001",
                    "Approved field capture conclusion",
                    "The field capture control is suitably designed for "
                    "fictional mobile evidence collection under the pilot scope.",
                ),
            )
            # Publish the release after all entries are assembled.
            # Only transition from DRAFT → PUBLISHED; if the package
            # is already PUBLISHED (e.g. seed recovery after audit
            # events were dropped), the publish step is a no-op.
            connection.execute(
                "UPDATE client_release_packages "
                "SET status = 'PUBLISHED', "
                "    published_at = '2026-08-19T10:00:00Z', "
                "    published_by = 'Fictional Site Auditor' "
                "WHERE release_id = 'REL-FIC-PUBLISHED' "
                "  AND status = 'DRAFT'"
            )
            # The RELEASE_PUBLISHED audit event is inserted
            # automatically by the
            # client_release_packages_auto_publish_event trigger.

        relationships = (
            ("REL-FIC-0001", "OBL-FIC-0001", "RSK-FIC-0001", "OBLIGATION_TO_RISK", "ACTIVE"),
            ("REL-FIC-0002", "RSK-FIC-0001", "CTL-FIC-0001", "RISK_TO_CONTROL", "ACTIVE"),
            ("REL-FIC-0003", "CTL-FIC-0001", "OWN-FIC-0001", "CONTROL_TO_OWNER", "ACTIVE"),
            ("REL-FIC-0004", "OWN-FIC-0001", "EVD-FIC-0001", "OWNER_TO_EVIDENCE", "ACTIVE"),
            ("REL-FIC-0005", "EVD-FIC-0001", "MATE-FIC-0001", "EVIDENCE_TO_MATE", "ACTIVE"),
            ("REL-FIC-0006", "MATE-FIC-0001", "CON-FIC-0001", "MATE_TO_CONCLUSION", "ACTIVE"),
            ("REL-FIC-0007", "EVD-FIC-0001", "MATE-FIC-0001", "CONTRA", "OPEN"),
        )
        connection.executemany(
            "INSERT OR IGNORE INTO relationships VALUES (?, ?, ?, ?, ?)", relationships
        )
    def create_engagement_draft(
        self, draft: "EngagementDraft", actor: str
    ) -> EngagementStoreRecord:
        """Create one DRAFT and its immutable creation event in one transaction."""
        values = self._normalise_draft(draft)
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    self._engagement_select() + " WHERE creation_attempt_key = ?",
                    (values["creation_attempt_key"],),
                ).fetchone()
                if existing is not None:
                    if existing["state"] == "DRAFT":
                        self._check_reference_is_available(
                            connection, values["reference"], existing["engagement_id"]
                        )
                        connection.execute(
                            """
                            UPDATE engagement_setups SET
                                title = ?, reference = ?, authority = ?, purpose = ?, scope = ?,
                                exclusions = ?, review_start_date = ?, review_end_date = ?,
                                evidence_cut_off_date = ?, accountable_auditor = ?,
                                data_classification = ?, is_fictional = ?
                            WHERE engagement_id = ? AND state = 'DRAFT'
                            """,
                            (*list(values.values())[1:], existing["engagement_id"]),
                        )
                        existing = connection.execute(
                            self._engagement_select() + " WHERE setup.engagement_id = ?",
                            (existing["engagement_id"],),
                        ).fetchone()
                    connection.commit()
                    return self._engagement_record(existing)
                self._check_reference_is_available(connection, values["reference"], None)
                engagement_id = f"ENG-{uuid.uuid4().hex[:12].upper()}"
                created_at = utc_now()
                connection.execute(
                    """
                    INSERT INTO engagement_setups (
                        engagement_id, creation_attempt_key, title, reference, authority, purpose,
                        scope, exclusions, review_start_date, review_end_date, evidence_cut_off_date,
                        accountable_auditor, data_classification, is_fictional, state, created_at,
                        activated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, NULL)
                    """,
                    (engagement_id, *values.values(), created_at),
                )
                connection.execute(
                    "INSERT INTO engagement_audit_events VALUES (?, ?, ?, ?, ?)",
                    (
                        f"EVT-{uuid.uuid4().hex[:12].upper()}",
                        engagement_id,
                        "ENGAGEMENT_CREATED",
                        created_at,
                        actor,
                    ),
                )
                row = connection.execute(
                    self._engagement_select() + " WHERE setup.engagement_id = ?", (engagement_id,)
                ).fetchone()
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        if row is None:
            raise RuntimeError("Engagement draft was not saved")
        return self._engagement_record(row)

    def get_engagement(self, engagement_id: str) -> EngagementStoreRecord:
        self._validate_engagement_id(engagement_id)
        with self.connect() as connection:
            row = connection.execute(
                self._engagement_select() + " WHERE setup.engagement_id = ?", (engagement_id,)
            ).fetchone()
        if row is None:
            raise EngagementNotFoundError()
        return self._engagement_record(row)

    def activate_engagement(
        self,
        engagement_id: str,
        actor: str,
        validate: Callable[[EngagementStoreRecord], None],
    ) -> EngagementStoreRecord:
        """Activate a DRAFT, record the event, and select it atomically."""
        self._validate_engagement_id(engagement_id)
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    self._engagement_select() + " WHERE setup.engagement_id = ?", (engagement_id,)
                ).fetchone()
                if row is None:
                    raise EngagementNotFoundError()
                validate(self._engagement_record(row))
                if row["state"] == "DRAFT":
                    activated_at = utc_now()
                    connection.execute(
                        "UPDATE engagement_setups SET state = ?, activated_at = ? WHERE engagement_id = ?",
                        ("READY_FOR_CAPTURE", activated_at, engagement_id),
                    )
                    connection.execute(
                        "INSERT INTO engagement_audit_events VALUES (?, ?, ?, ?, ?)",
                        (
                            f"EVT-{uuid.uuid4().hex[:12].upper()}",
                            engagement_id,
                            "ENGAGEMENT_ACTIVATED",
                            activated_at,
                            actor,
                        ),
                    )
                connection.execute(
                    """
                    INSERT INTO current_engagement (current_slot, engagement_id) VALUES (1, ?)
                    ON CONFLICT(current_slot) DO UPDATE SET engagement_id = excluded.engagement_id
                    """,
                    (engagement_id,),
                )
                row = connection.execute(
                    self._engagement_select() + " WHERE setup.engagement_id = ?", (engagement_id,)
                ).fetchone()
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        if row is None:
            raise RuntimeError("Engagement activation was not saved")
        return self._engagement_record(row)

    def select_current_engagement(
        self,
        engagement_id: str,
        validate: Callable[[EngagementStoreRecord], None],
    ) -> EngagementStoreRecord:
        self._validate_engagement_id(engagement_id)
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    self._engagement_select() + " WHERE setup.engagement_id = ?", (engagement_id,)
                ).fetchone()
                if row is None:
                    raise EngagementNotFoundError()
                validate(self._engagement_record(row))
                connection.execute(
                    """
                    INSERT INTO current_engagement (current_slot, engagement_id) VALUES (1, ?)
                    ON CONFLICT(current_slot) DO UPDATE SET engagement_id = excluded.engagement_id
                    """,
                    (engagement_id,),
                )
                row = connection.execute(
                    self._engagement_select() + " WHERE setup.engagement_id = ?", (engagement_id,)
                ).fetchone()
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        if row is None:
            raise RuntimeError("Current Engagement was not saved")
        return self._engagement_record(row)

    def current_engagement(self) -> EngagementStoreRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                self._engagement_select() + " WHERE current.current_slot = 1"
            ).fetchone()
        return self._engagement_record(row) if row is not None else None

    def summary(self) -> dict[str, Any]:
        with self.connect() as connection:
            current = connection.execute(
                self._engagement_select() + " WHERE current.current_slot = 1"
            ).fetchone()
            counts = connection.execute(
                """
                SELECT
                    COUNT(*) AS captured,
                    SUM(status = 'PENDING_REVIEW') AS pending_review,
                    SUM(status = 'REVIEWED') AS reviewed
                FROM evidence
                WHERE is_capture = 1 AND engagement_id = ?
                """,
                (current["engagement_id"] if current is not None else None,),
            ).fetchone()
            open_conflicts = connection.execute(
                """
                SELECT COUNT(*)
                FROM relationships
                WHERE relationship_type = ?
                    AND status = ?
                    AND EXISTS (
                        SELECT 1
                        FROM evidence
                        WHERE evidence.is_capture = 1
                            AND evidence.engagement_id = ?
                            AND evidence.evidence_id IN (
                                relationships.source_record_id,
                                relationships.target_record_id
                            )
                    )
                """,
                ("CONTRA", "OPEN", current["engagement_id"] if current is not None else None),
            ).fetchone()[0]
            recent_captures = connection.execute(
                """
                SELECT evidence_id, engagement_id, filename, media_type, media_path, status, captured_at
                FROM evidence WHERE is_capture = 1 AND engagement_id = ?
                ORDER BY captured_at DESC, evidence_id DESC
                LIMIT 10
                """,
                (current["engagement_id"] if current is not None else None,),
            ).fetchall()
            pending_review = connection.execute(
                """
                SELECT evidence_id, engagement_id, filename, media_type, media_path, status, captured_at
                FROM evidence
                WHERE is_capture = 1 AND engagement_id = ? AND status = ?
                ORDER BY captured_at DESC, evidence_id DESC
                """,
                (current["engagement_id"] if current is not None else None, "PENDING_REVIEW"),
            ).fetchall()
            reviewed_unlinked = connection.execute(
                """
                SELECT evidence_id, engagement_id, filename, media_type, media_path, status, captured_at
                FROM evidence AS e
                WHERE e.is_capture = 1 AND e.engagement_id = ? AND e.status = 'REVIEWED'
                    AND NOT EXISTS (
                        SELECT 1 FROM proposed_evidence_links AS p WHERE p.evidence_id = e.evidence_id
                    )
                ORDER BY e.captured_at DESC, e.evidence_id DESC
                """,
                (current["engagement_id"] if current is not None else None,),
            ).fetchall()
        return {
            "engagement": current["title"] if current is not None else "No current Engagement",
            "current_engagement": (
                self._engagement_record(current).as_dict() if current is not None else None
            ),
            "chain": ["Obligation", "Risk", "Control", "Owner", "Evidence", "MATE", "Conclusion"],
            "counts": {
                "captured": counts["captured"],
                "pending_review": counts["pending_review"] or 0,
                "reviewed": counts["reviewed"] or 0,
                "open_conflicts": open_conflicts,
            },
            "recent_captures": [self._evidence_json(row) for row in recent_captures],
            "pending_review": [self._evidence_json(row) for row in pending_review],
            "reviewed_unlinked": [self._evidence_json(row) for row in reviewed_unlinked],
        }

    def engagement_summary(self) -> dict[str, Any]:
        """Return a read-only Engagement Control Summary from existing records."""
        with self.connect() as connection:
            current_row = connection.execute(
                self._engagement_select() + " WHERE current.current_slot = 1"
            ).fetchone()
            if current_row is None:
                return {"has_engagement": False}
            engagement = self._engagement_record(current_row).as_dict()
            engagement_id = engagement["engagement_id"]

            counts = connection.execute(
                """
                SELECT
                    COUNT(*) AS captured,
                    SUM(status = 'PENDING_REVIEW') AS pending_review,
                    SUM(status = 'REVIEWED') AS reviewed
                FROM evidence
                WHERE is_capture = 1 AND engagement_id = ?
                """,
                (engagement_id,),
            ).fetchone()
            total_captured: int = counts["captured"]
            pending_review: int = counts["pending_review"] or 0
            reviewed: int = counts["reviewed"] or 0

            open_conflicts = connection.execute(
                """
                SELECT COUNT(*)
                FROM relationships
                WHERE relationship_type = ?
                    AND status = ?
                    AND EXISTS (
                        SELECT 1
                        FROM evidence
                        WHERE evidence.is_capture = 1
                            AND evidence.engagement_id = ?
                            AND evidence.evidence_id IN (
                                relationships.source_record_id,
                                relationships.target_record_id
                            )
                    )
                """,
                ("CONTRA", "OPEN", engagement_id),
            ).fetchone()[0]

            open_gaps = connection.execute(
                """
                SELECT COUNT(*)
                FROM evidence_review_contexts rc
                JOIN evidence e ON rc.evidence_id = e.evidence_id
                WHERE e.engagement_id = ?
                    AND e.is_capture = 1
                    AND rc.gap_status NOT IN ('NOT_REQUESTED', 'NOT_APPLICABLE')
                """,
                (engagement_id,),
            ).fetchone()[0]

            pending_items = connection.execute(
                """
                SELECT evidence_id, filename, captured_at
                FROM evidence
                WHERE is_capture = 1 AND engagement_id = ? AND status = 'PENDING_REVIEW'
                ORDER BY captured_at DESC, evidence_id DESC
                LIMIT 5
                """,
                (engagement_id,),
            ).fetchall()

            recent_events = connection.execute(
                """
                SELECT event_type, recorded_at, actor
                FROM engagement_audit_events
                WHERE engagement_id = ?
                ORDER BY recorded_at DESC
                LIMIT 10
                """,
                (engagement_id,),
            ).fetchall()

        recommendation = self._derive_recommendation(
            engagement, total_captured, pending_review, open_conflicts, open_gaps
        )
        return {
            "has_engagement": True,
            "engagement": engagement,
            "evidence": {
                "captured": total_captured,
                "pending_review": pending_review,
                "reviewed": reviewed,
            },
            "open_conflicts": open_conflicts,
            "open_gaps": open_gaps,
            "pending_items": [dict(row) for row in pending_items],
            "recent_events": [dict(row) for row in recent_events],
            "recommendation": recommendation,
        }

    @staticmethod
    def _derive_recommendation(
        engagement: dict[str, Any],
        total_captured: int,
        pending_review: int,
        open_conflicts: int,
        open_gaps: int,
    ) -> str:
        if engagement.get("state") == "DRAFT":
            return "Activate the Engagement to begin evidence capture."
        if total_captured == 0:
            return "Capture evidence for the Engagement."
        if pending_review > 0:
            return f"Review {pending_review} evidence item(s) pending review."
        if open_conflicts > 0:
            return f"Review {open_conflicts} open relationship conflict(s)."
        if open_gaps > 0:
            return f"Address {open_gaps} open gap(s) where a controlled source has been identified."
        return "All evidence reviewed. No open conflicts or gaps."

    @staticmethod
    def _evidence_json(row: sqlite3.Row) -> dict[str, Any]:
        media_path = row["media_path"]
        return {
            "evidence_id": row["evidence_id"],
            "engagement_id": row["engagement_id"],
            "filename": row["filename"],
            "media_type": row["media_type"],
            "status": row["status"],
            "captured_at": row["captured_at"],
            "media_url": (
                f"/workbench/evidence/{row['evidence_id']}/media" if media_path else None
            ),
        }

    def capture(
        self,
        filename: str,
        media_type: str,
        content: bytes,
        actor: str,
        validate_current: Callable[[EngagementStoreRecord], None],
        capture_attempt_key: str | None = None,
    ) -> dict[str, str]:
        """Write one capture only after the current Engagement is locked and validated."""
        filename = self._canonical_filename(filename)
        capture_attempt_key = capture_attempt_key or uuid.uuid4().hex
        if not CAPTURE_ATTEMPT_KEY_PATTERN.fullmatch(capture_attempt_key):
            raise ValueError("Invalid capture attempt key")
        extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}[media_type]
        evidence_id = f"EVD-{uuid.uuid4().hex[:12].upper()}"
        media_path = PurePosixPath("media") / f"{evidence_id}.{extension}"
        target_path = self._media_file_path(media_path)
        captured_at = utc_now()
        request_sha256 = self._request_sha256(filename, media_type, content)
        media_written = False
        try:
            with self.connect() as connection:
                try:
                    connection.execute("BEGIN IMMEDIATE")
                    current = connection.execute(
                        self._engagement_select() + " WHERE current.current_slot = 1"
                    ).fetchone()
                    if current is None:
                        raise NoReadyCurrentEngagementError()
                    current_record = self._engagement_record(current)
                    validate_current(current_record)
                    existing = connection.execute(
                        """
                        SELECT evidence_id, engagement_id, request_sha256, media_type, media_path, status
                        FROM evidence WHERE capture_attempt_key = ?
                        """,
                        (capture_attempt_key,),
                    ).fetchone()
                    if existing is not None:
                        if (
                            existing["engagement_id"] == current_record.engagement_id
                            and existing["request_sha256"] == request_sha256
                        ):
                            connection.commit()
                            return {
                                "evidence_id": existing["evidence_id"],
                                "engagement_id": current_record.engagement_id,
                                "status": existing["status"],
                                "media_type": existing["media_type"],
                                "media_path": existing["media_path"],
                            }
                        raise CaptureAttemptConflictError("Capture attempt key conflicts")
                    with target_path.open("xb") as media_file:
                        media_written = True
                        media_file.write(content)
                    connection.execute(
                        """
                        INSERT INTO evidence (
                            evidence_id, owner_id, filename, media_type, media_path, status,
                            captured_at, is_capture, engagement_id, capture_attempt_key, request_sha256
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            evidence_id,
                            "OWN-FIC-0001",
                            filename,
                            media_type,
                            media_path.as_posix(),
                            "PENDING_REVIEW",
                            captured_at,
                            1,
                            current_record.engagement_id,
                            capture_attempt_key,
                            request_sha256,
                        ),
                    )
                    connection.execute(
                        "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?)",
                        (
                            f"EVT-{uuid.uuid4().hex[:12].upper()}",
                            evidence_id,
                            "CAPTURED",
                            captured_at,
                            actor,
                        ),
                    )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
        except Exception:
            if media_written:
                target_path.unlink(missing_ok=True)
            raise
        return {
            "evidence_id": evidence_id,
            "engagement_id": current_record.engagement_id,
            "status": "PENDING_REVIEW",
            "media_type": media_type,
            "media_path": media_path.as_posix(),
        }

    @staticmethod
    def _canonical_filename(filename: str) -> str:
        canonical_filename = filename.strip()
        if not canonical_filename:
            raise ValueError("Invalid filename")
        return canonical_filename

    @staticmethod
    def _request_sha256(filename: str, media_type: str, content: bytes) -> str:
        digest = sha256()
        for value in (filename.encode("utf-8"), media_type.encode("ascii"), content):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
        return digest.hexdigest()

    @staticmethod
    def _engagement_select() -> str:
        return """
            SELECT
                setup.engagement_id,
                setup.creation_attempt_key,
                setup.title,
                setup.reference,
                setup.authority,
                setup.purpose,
                setup.scope,
                setup.exclusions,
                setup.review_start_date,
                setup.review_end_date,
                setup.evidence_cut_off_date,
                setup.accountable_auditor,
                setup.data_classification,
                setup.is_fictional,
                setup.state,
                setup.created_at,
                setup.activated_at,
                CASE WHEN current.current_slot = 1 THEN 1 ELSE 0 END AS current
            FROM engagement_setups AS setup
            LEFT JOIN current_engagement AS current ON current.engagement_id = setup.engagement_id
        """

    @staticmethod
    def _engagement_record(row: sqlite3.Row) -> EngagementStoreRecord:
        is_fictional = row["is_fictional"]
        return EngagementStoreRecord(
            engagement_id=row["engagement_id"],
            creation_attempt_key=row["creation_attempt_key"],
            title=row["title"],
            reference=row["reference"],
            authority=row["authority"],
            purpose=row["purpose"],
            scope=row["scope"],
            exclusions=row["exclusions"],
            review_start_date=row["review_start_date"],
            review_end_date=row["review_end_date"],
            evidence_cut_off_date=row["evidence_cut_off_date"],
            accountable_auditor=row["accountable_auditor"],
            data_classification=row["data_classification"],
            is_fictional=bool(is_fictional) if is_fictional is not None else None,
            state=row["state"],
            created_at=row["created_at"],
            activated_at=row["activated_at"],
            current=bool(row["current"]),
        )

    @staticmethod
    def _normalise_draft(draft: "EngagementDraft") -> dict[str, object]:
        values = {
            "creation_attempt_key": draft.creation_attempt_key,
            "title": draft.title,
            "reference": draft.reference,
            "authority": draft.authority,
            "purpose": draft.purpose,
            "scope": draft.scope,
            "exclusions": draft.exclusions,
            "review_start_date": draft.review_start_date,
            "review_end_date": draft.review_end_date,
            "evidence_cut_off_date": draft.evidence_cut_off_date,
            "accountable_auditor": draft.accountable_auditor,
            "data_classification": draft.data_classification,
            "is_fictional": draft.is_fictional,
        }
        return {
            key: (value.strip() or None) if isinstance(value, str) else value
            for key, value in values.items()
        }

    @staticmethod
    def _check_reference_is_available(
        connection: sqlite3.Connection, reference: object, engagement_id: str | None
    ) -> None:
        if reference is None:
            return
        duplicate = connection.execute(
            "SELECT engagement_id FROM engagement_setups WHERE reference = ?",
            (reference,),
        ).fetchone()
        if duplicate is not None and duplicate["engagement_id"] != engagement_id:
            raise DuplicateEngagementReferenceError()

    def evidence_review_state(self, evidence_id: str) -> dict[str, object] | None:
        """Return the safe review state for one Evidence Item."""
        with self.connect() as connection:
            connection.execute("BEGIN")
            evidence = self._review_evidence(connection, evidence_id)
            if evidence is None:
                connection.commit()
                return None
            engagement = self._safe_current_engagement(connection, evidence["engagement_id"])
            context = connection.execute(
                "SELECT * FROM evidence_review_contexts WHERE evidence_id = ?", (evidence_id,)
            ).fetchone()
            available_controls = connection.execute(
                """
                SELECT c.control_id, c.title
                FROM controls AS c
                JOIN risks AS r ON r.risk_id = c.risk_id
                JOIN obligations AS o ON o.obligation_id = r.obligation_id
                WHERE o.engagement_id = ?
                ORDER BY c.control_id
                """,
                (evidence["engagement_id"],),
            ).fetchall()
            questions = connection.execute(
                """
                SELECT q.question_id, q.control_id, q.question_type, q.parent_question_id,
                       q.created_at, q.created_by, v.version, v.question_text, v.purpose,
                       v.created_at AS version_created_at, v.created_by AS version_created_by
                FROM audit_questions AS q
                JOIN audit_question_versions AS v ON v.question_id = q.question_id
                WHERE q.engagement_id = ?
                ORDER BY q.created_at, q.question_id, v.version
                """,
                (evidence["engagement_id"],),
            ).fetchall()
            decisions = connection.execute(
                """
                SELECT decision_id, question_id, question_version, status, reason, decided_at, decided_by
                FROM audit_question_decisions WHERE question_id IN (
                    SELECT question_id FROM audit_questions WHERE engagement_id = ?
                ) ORDER BY decided_at, decision_id
                """,
                (evidence["engagement_id"],),
            ).fetchall()
            proposed_links = connection.execute(
                """
                SELECT proposal_id, evidence_id, question_id, question_version, relevance, reason,
                       proposed_at, proposed_by
                FROM proposed_evidence_links WHERE evidence_id = ? ORDER BY proposed_at, proposal_id
                """,
                (evidence_id,),
            ).fetchall()
            completion = connection.execute(
                """
                SELECT c.completed_at, r.reviewer, r.reviewed_at, r.notes
                FROM evidence_review_completions AS c
                JOIN reviews AS r ON r.review_id = c.review_id
                WHERE c.evidence_id = ? ORDER BY c.completed_at LIMIT 1
                """,
                (evidence_id,),
            ).fetchone()
            connection.commit()
        evidence_json = self._evidence_json(evidence)
        return {
            "evidence_id": evidence_id,
            "evidence": evidence_json,
            "original_media_url": evidence_json["media_url"],
            "engagement": dict(engagement),
            "source_context": self._context_json(context),
            "available_controls": [dict(row) for row in available_controls],
            "question_versions": [dict(row) for row in questions],
            "decisions": [dict(row) for row in decisions],
            "proposed_links": [dict(row) for row in proposed_links],
            "completion": dict(completion) if completion is not None else None,
            "completion_state": evidence["status"],
        }

    def evidence_suggestions(self, evidence_id: str) -> dict[str, object]:
        """Return advisory extraction suggestions for fictional evidence source text.

        Reads source_text from the evidence record and runs the deterministic
        extraction adapter. Results are cached per evidence_id — source text
        is immutable once captured, so cached suggestions never stale.
        Returns an empty list when no source_text exists or evidence is not
        found. No write path.
        """
        cached = self._suggestions_cache.get(evidence_id)
        if cached is not None:
            return {"evidence_id": evidence_id, "suggestions": cached}

        with self.connect() as connection:
            row = connection.execute(
                "SELECT evidence_id, source_text FROM evidence WHERE evidence_id = ?",
                (evidence_id,),
            ).fetchone()
            if row is None:
                result: list[dict[str, object]] = []
            else:
                source_text = row["source_text"]
                if not source_text or not source_text.strip():
                    result = []
                else:
                    adapter = EvidenceExtractionAdapter()
                    suggestions = adapter.extract(source_text)
                    result = [
                        {
                            "type": s.type,
                            "text": s.text,
                            "source_start": s.start,
                            "source_end": s.end,
                        }
                        for s in suggestions
                    ]
            self._suggestions_cache[evidence_id] = result
            return {"evidence_id": evidence_id, "suggestions": result}

    # ---- Graph projection (Phase 5) ---------------------------------------

    def graph_projection(self) -> dict[str, object]:
        """Return a read-only graph projection of the current engagement.

        Collects fictional records as nodes and relationships as edges.
        Returns nodes, edges, and warnings in a provider-neutral structure.
        """
        engagement = self.current_engagement()
        if engagement is None:
            return {"engagement_id": None, "nodes": [], "edges": [], "warnings": []}

        engagement_id = engagement.engagement_id
        with self.connect() as connection:
            # --- Nodes ---
            nodes: list[dict[str, object]] = []
            # engagement_setup
            es_row = connection.execute(
                "SELECT engagement_id, title, reference, state, accountable_auditor "
                "FROM engagement_setups WHERE engagement_id = ?",
                (engagement_id,),
            ).fetchone()
            if es_row:
                nodes.append({
                    "id": es_row["engagement_id"],
                    "type": "engagement",
                    "label": es_row["title"],
                    "reference": es_row["reference"],
                    "state": es_row["state"],
                })

            # obligations
            for row in connection.execute(
                "SELECT obligation_id, title FROM obligations WHERE engagement_id = ?",
                (engagement_id,),
            ).fetchall():
                nodes.append({"id": row["obligation_id"], "type": "obligation", "label": row["title"]})

            # risks
            for row in connection.execute(
                "SELECT r.risk_id, r.title FROM risks r "
                "JOIN obligations o ON r.obligation_id = o.obligation_id "
                "WHERE o.engagement_id = ?",
                (engagement_id,),
            ).fetchall():
                nodes.append({"id": row["risk_id"], "type": "risk", "label": row["title"]})

            # controls
            for row in connection.execute(
                "SELECT c.control_id, c.title FROM controls c "
                "JOIN risks r ON c.risk_id = r.risk_id "
                "JOIN obligations o ON r.obligation_id = o.obligation_id "
                "WHERE o.engagement_id = ?",
                (engagement_id,),
            ).fetchall():
                nodes.append({"id": row["control_id"], "type": "control", "label": row["title"]})

            # owners
            for row in connection.execute(
                "SELECT ow.owner_id, ow.name FROM owners ow "
                "JOIN controls c ON ow.control_id = c.control_id "
                "JOIN risks r ON c.risk_id = r.risk_id "
                "JOIN obligations o ON r.obligation_id = o.obligation_id "
                "WHERE o.engagement_id = ?",
                (engagement_id,),
            ).fetchall():
                nodes.append({"id": row["owner_id"], "type": "owner", "label": row["name"]})

            # evidence
            evidence_id_set: set[str] = set()
            for row in connection.execute(
                "SELECT evidence_id, filename, media_type, status, is_capture, source_text "
                "FROM evidence WHERE engagement_id = ?",
                (engagement_id,),
            ).fetchall():
                node: dict[str, object] = {
                    "id": row["evidence_id"],
                    "type": "evidence",
                    "label": row["filename"],
                    "media_type": row["media_type"],
                    "status": row["status"],
                    "is_capture": bool(row["is_capture"]),
                }
                if row["source_text"]:
                    node["has_source_text"] = True
                nodes.append(node)
                evidence_id_set.add(row["evidence_id"])

            # mates
            for row in connection.execute(
                "SELECT m.mate_id, m.title FROM mates m "
                "JOIN evidence e ON m.evidence_id = e.evidence_id "
                "WHERE e.engagement_id = ?",
                (engagement_id,),
            ).fetchall():
                nodes.append({"id": row["mate_id"], "type": "mate", "label": row["title"]})

            # conclusions
            for row in connection.execute(
                "SELECT c.conclusion_id, c.title, c.status FROM conclusions c "
                "JOIN mates m ON c.mate_id = m.mate_id "
                "JOIN evidence e ON m.evidence_id = e.evidence_id "
                "WHERE e.engagement_id = ?",
                (engagement_id,),
            ).fetchall():
                nodes.append({
                    "id": row["conclusion_id"],
                    "type": "conclusion",
                    "label": row["title"],
                    "status": row["status"],
                })

            # --- Edges (approved relationships only) ---
            node_ids = {n["id"] for n in nodes}
            edges: list[dict[str, object]] = []
            warnings: list[dict[str, object]] = []

            # Scope relationships query to only rows that reference records
            # within the current engagement — avoids false "outside the
            # engagement graph" warnings from cross-engagement relationships.
            if node_ids:
                id_list = sorted(node_ids)
                placeholders = ",".join("?" for _ in id_list)
                rel_rows = connection.execute(
                    f"SELECT * FROM relationships "
                    f"WHERE source_record_id IN ({placeholders}) "
                    f"   OR target_record_id IN ({placeholders})",
                    id_list + id_list,
                ).fetchall()
            else:
                rel_rows = []

            for row in rel_rows:
                source = row["source_record_id"]
                target = row["target_record_id"]
                rtype = row["relationship_type"]
                rstatus = row["status"]
                is_approved = rstatus == "ACTIVE" and rtype != "CONTRA"

                edge = {
                    "source": source,
                    "target": target,
                    "type": rtype,
                    "status": rstatus,
                }

                if source in node_ids and target in node_ids:
                    if is_approved:
                        edges.append(edge)
                    else:
                        warnings.append({
                            "level": "WARNING",
                            "record_id": row["relationship_id"],
                            "detail": f"Unapproved relationship: {source} → {target} ({rtype}, {rstatus})",
                        })
                else:
                    warnings.append({
                        "level": "WARNING",
                        "record_id": row["relationship_id"],
                        "detail": f"Relationship {source} → {target} ({rtype}) references records outside the engagement graph",
                    })

            # --- Evidence warnings ---
            for row in connection.execute(
                "SELECT evidence_id, is_capture, source_text, status "
                "FROM evidence WHERE engagement_id = ?",
                (engagement_id,),
            ).fetchall():
                if not row["source_text"] or not row["source_text"].strip():
                    warnings.append({
                        "level": "INFO",
                        "record_id": row["evidence_id"],
                        "detail": f"Evidence {row['evidence_id']} has no source text — review suggestions unavailable",
                    })
                if not bool(row["is_capture"]):
                    warnings.append({
                        "level": "INFO",
                        "record_id": row["evidence_id"],
                        "detail": f"Evidence {row['evidence_id']} was not field-captured (is_capture=0)",
                    })

            return {
                "engagement_id": engagement_id,
                "nodes": nodes,
                "edges": edges,
                "warnings": warnings,
            }

    def save_evidence_review_context(
        self, evidence_id: str, context: dict[str, object], actor: str
    ) -> dict[str, object]:
        values = self._normalise_context(context)
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                evidence = self._review_evidence(connection, evidence_id)
                if evidence is None:
                    connection.rollback()
                    return None  # type: ignore[return-value]
                if evidence["status"] != "PENDING_REVIEW":
                    raise RuntimeError("Evidence Review context is frozen")
                self._validate_raw_source_origin(connection, evidence, values)
                self._validate_context_references(connection, evidence, values)
                connection.execute(
                    """
                    INSERT INTO evidence_review_contexts (
                        evidence_id, provider, origin, source_date, source_version, source_location,
                        description, freshness, limitations, duplicate_evidence_id, source_evidence_ids,
                        gap_status, gap_explanation, gap_materiality, updated_at, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(evidence_id) DO UPDATE SET
                        provider = excluded.provider, origin = excluded.origin,
                        source_date = excluded.source_date, source_version = excluded.source_version,
                        source_location = excluded.source_location, description = excluded.description,
                        freshness = excluded.freshness, limitations = excluded.limitations,
                        duplicate_evidence_id = excluded.duplicate_evidence_id,
                        source_evidence_ids = excluded.source_evidence_ids,
                        gap_status = excluded.gap_status, gap_explanation = excluded.gap_explanation,
                        gap_materiality = excluded.gap_materiality, updated_at = excluded.updated_at,
                        updated_by = excluded.updated_by
                    """,
                    (evidence_id, *values.values(), utc_now(), actor),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.evidence_review_state(evidence_id)

    def create_audit_question(self, question: dict[str, object], actor: str) -> dict[str, object]:
        values = self._normalise_question(question)
        question_id = f"AQ-{uuid.uuid4().hex[:12].upper()}"
        created_at = utc_now()
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._safe_current_engagement(connection, values["engagement_id"])
                self._validate_control(connection, values["engagement_id"], values["control_id"])
                self._validate_question_parent(connection, values, None)
                connection.execute(
                    """INSERT INTO audit_questions VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (question_id, values["engagement_id"], values["control_id"], values["question_type"],
                     values["parent_question_id"], created_at, actor),
                )
                connection.execute(
                    """INSERT INTO audit_question_versions
                    (question_id, version, question_text, purpose, created_at, created_by)
                    VALUES (?, 1, ?, ?, ?, ?)""",
                    (question_id, values["question_text"], values["purpose"], created_at, actor),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self._question_version(question_id, 1)

    def create_audit_question_version(
        self, question_id: str, version: dict[str, object], actor: str
    ) -> dict[str, object]:
        question_text = self._required_text(version.get("question_text"), "Question text")
        purpose = self._required_text(version.get("purpose"), "Audit Question purpose")
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                question = self._safe_question(connection, question_id)
                next_version = connection.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM audit_question_versions WHERE question_id = ?",
                    (question_id,),
                ).fetchone()[0]
                connection.execute(
                    """INSERT INTO audit_question_versions
                    (question_id, version, question_text, purpose, created_at, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (question_id, next_version, question_text, purpose, utc_now(), actor),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self._question_version(question_id, next_version)

    def record_audit_question_decision(
        self, question_id: str, decision: dict[str, object], actor: str
    ) -> dict[str, object]:
        key = decision.get("decision_attempt_key")
        if not isinstance(key, str) or not DECISION_ATTEMPT_KEY_PATTERN.fullmatch(key):
            raise ValueError("Invalid decision attempt key")
        version = decision.get("question_version")
        if not isinstance(version, int) or isinstance(version, bool) or version <= 0:
            raise ValueError("Question version must be a positive integer")
        status = decision.get("status")
        if status not in {"APPROVED", "REJECTED", "CHANGES_REQUIRED"}:
            raise ValueError("Use a controlled decision status")
        reason = self._required_text(decision.get("reason"), "Decision reason")
        request_sha256 = self._decision_sha256(question_id, version, status, reason)
        decided_at = utc_now()
        result = {
            "decision_id": f"AQD-{uuid.uuid4().hex[:12].upper()}", "question_id": question_id,
            "question_version": version, "status": status, "reason": reason,
            "decided_at": decided_at, "decided_by": actor,
        }
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._safe_question(connection, question_id)
                previous = connection.execute(
                    """SELECT decision_id, question_id, question_version, status, reason, decided_at, decided_by,
                              request_sha256
                    FROM audit_question_decisions WHERE decision_attempt_key = ?""",
                    (key,),
                ).fetchone()
                if previous is not None:
                    if previous["request_sha256"] != request_sha256:
                        raise RuntimeError("Decision attempt key conflicts")
                    connection.commit()
                    return self._decision_json(previous)
                exists = connection.execute(
                    "SELECT 1 FROM audit_question_versions WHERE question_id = ? AND version = ?",
                    (question_id, version),
                ).fetchone()
                if exists is None:
                    raise ValueError("Audit Question version does not exist")
                duplicate = connection.execute(
                    "SELECT 1 FROM audit_question_decisions WHERE question_id = ? AND question_version = ?",
                    (question_id, version),
                ).fetchone()
                if duplicate is not None:
                    raise RuntimeError("An exact Audit Question version already has a decision")
                connection.execute(
                    """INSERT INTO audit_question_decisions (
                        decision_id, decision_attempt_key, request_sha256, question_id, question_version,
                        status, reason, decided_at, decided_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        result["decision_id"], key, request_sha256, result["question_id"],
                        result["question_version"], result["status"], result["reason"],
                        result["decided_at"], result["decided_by"],
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return result

    def create_proposed_link(
        self, evidence_id: str, proposal: dict[str, object], actor: str
    ) -> dict[str, object]:
        question_id = self._required_text(proposal.get("question_id"), "Question identifier")
        version = proposal.get("question_version")
        if not isinstance(version, int) or isinstance(version, bool) or version <= 0:
            raise ValueError("Question version must be a positive integer")
        relevance = proposal.get("relevance")
        if relevance not in {"SUPPORTS", "WEAKENS", "CONTRADICTS"}:
            raise ValueError("Use a controlled relevance")
        result = {
            "proposal_id": f"PRL-{uuid.uuid4().hex[:12].upper()}", "evidence_id": evidence_id,
            "question_id": question_id, "question_version": version, "relevance": relevance,
            "reason": self._required_text(proposal.get("reason"), "Proposal reason"),
            "proposed_at": utc_now(), "proposed_by": actor,
        }
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                evidence = self._review_evidence(connection, evidence_id)
                if evidence is None:
                    connection.rollback()
                    return None  # type: ignore[return-value]
                if evidence["status"] != "PENDING_REVIEW":
                    raise RuntimeError("Evidence Review proposed links are frozen")
                question = self._safe_question(connection, question_id)
                if question["engagement_id"] != evidence["engagement_id"]:
                    raise ValueError("Audit Question belongs to a different Engagement")
                exists = connection.execute(
                    "SELECT 1 FROM audit_question_versions WHERE question_id = ? AND version = ?",
                    (question_id, version),
                ).fetchone()
                if exists is None:
                    raise ValueError("Audit Question version does not exist")
                duplicate = connection.execute(
                    """SELECT 1 FROM proposed_evidence_links
                    WHERE evidence_id = ? AND question_id = ? AND question_version = ?""",
                    (evidence_id, question_id, version),
                ).fetchone()
                if duplicate is not None:
                    raise RuntimeError("An exact Evidence Review proposed link already exists")
                connection.execute(
                    "INSERT INTO proposed_evidence_links VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    tuple(result.values()),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return result

    def complete_evidence_review(
        self, evidence_id: str, completion: dict[str, object], actor: str
    ) -> dict[str, object]:
        key = completion.get("completion_attempt_key")
        if not isinstance(key, str) or not COMPLETION_ATTEMPT_KEY_PATTERN.fullmatch(key):
            raise ValueError("Invalid completion attempt key")
        notes = self._required_text(completion.get("notes", "Evidence review completed."), "Review notes")
        request_sha256 = self._completion_sha256(evidence_id, notes)
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                evidence = self._review_evidence(connection, evidence_id)
                if evidence is None:
                    connection.rollback()
                    return None  # type: ignore[return-value]
                previous = connection.execute(
                    """SELECT c.evidence_id, c.request_sha256, c.completed_at, r.reviewer, r.reviewed_at, r.notes
                    FROM evidence_review_completions AS c JOIN reviews AS r ON r.review_id = c.review_id
                    WHERE c.completion_attempt_key = ?""",
                    (key,),
                ).fetchone()
                if previous is not None:
                    if previous["evidence_id"] != evidence_id or previous["request_sha256"] != request_sha256:
                        raise RuntimeError("Completion attempt key conflicts")
                    connection.commit()
                    return self._completion_json(evidence_id, previous)
                if evidence["status"] != "PENDING_REVIEW":
                    raise RuntimeError("Evidence is not available for review completion")
                context = connection.execute(
                    "SELECT * FROM evidence_review_contexts WHERE evidence_id = ?", (evidence_id,)
                ).fetchone()
                if context is None:
                    raise ValueError("Save source context before review completion")
                self._validate_context_references(connection, evidence, dict(context))
                reviewed_at = utc_now()
                review_id = f"REV-{uuid.uuid4().hex[:12].upper()}"
                connection.execute("UPDATE evidence SET status = 'REVIEWED' WHERE evidence_id = ?", (evidence_id,))
                connection.execute(
                    """INSERT INTO reviews VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(evidence_id) DO UPDATE SET reviewer = excluded.reviewer,
                        reviewed_at = excluded.reviewed_at, notes = excluded.notes""",
                    (review_id, evidence_id, actor, reviewed_at, notes),
                )
                review = connection.execute(
                    "SELECT review_id, reviewer, reviewed_at, notes FROM reviews WHERE evidence_id = ?",
                    (evidence_id,),
                ).fetchone()
                connection.execute(
                    "INSERT INTO evidence_review_completions VALUES (?, ?, ?, ?, ?)",
                    (evidence_id, key, request_sha256, review["review_id"], reviewed_at),
                )
                connection.execute(
                    "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?)",
                    (f"EVT-{uuid.uuid4().hex[:12].upper()}", evidence_id,
                     "EVIDENCE_REVIEW_COMPLETED", reviewed_at, actor),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {"evidence_id": evidence_id, "status": "REVIEWED", "reviewer": actor,
                "reviewed_at": reviewed_at, "notes": notes, "completed_at": reviewed_at}

    def _review_evidence(self, connection: sqlite3.Connection, evidence_id: str) -> sqlite3.Row | None:
        self._validate_evidence_id(evidence_id)
        evidence = connection.execute(
            """SELECT e.evidence_id, e.engagement_id, e.filename, e.media_type, e.media_path,
                      e.status, e.captured_at, e.is_capture
               FROM evidence AS e WHERE e.evidence_id = ?""", (evidence_id,)
        ).fetchone()
        if evidence is None:
            return None
        self._safe_current_engagement(connection, evidence["engagement_id"])
        return evidence

    @staticmethod
    def _safe_current_engagement(connection: sqlite3.Connection, engagement_id: object) -> sqlite3.Row:
        row = connection.execute(
            """SELECT setup.engagement_id, setup.title, setup.reference, setup.state,
                      setup.data_classification FROM engagement_setups AS setup
               JOIN current_engagement AS current ON current.engagement_id = setup.engagement_id
               WHERE setup.engagement_id = ? AND setup.state = 'READY_FOR_CAPTURE'
                 AND setup.is_fictional = 1
                 AND setup.data_classification IN ('FICTIONAL', 'PUBLIC', 'AUDITCO_OWNED')""",
            (engagement_id,),
        ).fetchone()
        if row is None:
            raise EvidenceReviewG0Error("G0 blocks this Evidence Review")
        return row

    def _safe_question(self, connection: sqlite3.Connection, question_id: str) -> sqlite3.Row:
        question = connection.execute(
            "SELECT * FROM audit_questions WHERE question_id = ?", (question_id,)
        ).fetchone()
        if question is None:
            raise KeyError(question_id)
        self._safe_current_engagement(connection, question["engagement_id"])
        return question

    @staticmethod
    def _validate_control(connection: sqlite3.Connection, engagement_id: object, control_id: object) -> None:
        control = connection.execute(
            """SELECT 1 FROM controls AS c JOIN risks AS r ON r.risk_id = c.risk_id
               JOIN obligations AS o ON o.obligation_id = r.obligation_id
               WHERE c.control_id = ? AND o.engagement_id = ?""", (control_id, engagement_id)
        ).fetchone()
        if control is None:
            raise ValueError("Control does not belong to the Engagement")

    @staticmethod
    def _validate_question_parent(
        connection: sqlite3.Connection, values: dict[str, object], current_question_id: str | None
    ) -> None:
        question_type = values["question_type"]
        parent_id = values["parent_question_id"]
        if question_type == "MAIN":
            if parent_id is not None:
                raise ValueError("MAIN Audit Questions cannot have a parent")
            return
        if parent_id is None:
            raise ValueError("This Audit Question type requires a MAIN parent")
        parent = connection.execute(
            "SELECT * FROM audit_questions WHERE question_id = ?", (parent_id,)
        ).fetchone()
        if parent is None or parent["question_type"] != "MAIN":
            raise ValueError("Parent Audit Question must be MAIN")
        if parent["engagement_id"] != values["engagement_id"] or parent["control_id"] != values["control_id"]:
            raise ValueError("Parent Audit Question must use the same Engagement and Control")

    def _validate_context_references(
        self, connection: sqlite3.Connection, evidence: sqlite3.Row, values: dict[str, object]
    ) -> None:
        evidence_id = evidence["evidence_id"]
        duplicate_id = values["duplicate_evidence_id"]
        source_ids = json.loads(values["source_evidence_ids"])
        if duplicate_id == evidence_id:
            raise ValueError("Duplicate Evidence Item must differ from this item")
        if evidence_id in source_ids:
            raise ValueError("Source Evidence Item must differ from this item")
        identifiers = [identifier for identifier in [duplicate_id, *source_ids] if identifier is not None]
        for identifier in identifiers:
            source = connection.execute(
                "SELECT evidence_id, engagement_id FROM evidence WHERE evidence_id = ?", (identifier,)
            ).fetchone()
            if source is None or source["engagement_id"] != evidence["engagement_id"]:
                raise ValueError("Source Evidence Item must be in the same Engagement")
        if values["origin"] == "RAW" and source_ids:
            raise ValueError("RAW evidence cannot have source Evidence Items")
        if values["origin"] == "DERIVED":
            if not source_ids:
                raise ValueError("Derived evidence requires source Evidence Items")
            raw_count = connection.execute(
                """SELECT COUNT(*) FROM evidence_review_contexts AS context
                   JOIN evidence AS source ON source.evidence_id = context.evidence_id
                   WHERE context.evidence_id IN ({}) AND context.origin = 'RAW'
                     AND source.engagement_id = ?""".format(",".join("?" for _ in source_ids)),
                (*source_ids, evidence["engagement_id"]),
            ).fetchone()[0]
            if raw_count != len(source_ids):
                raise ValueError("Every derived source must have saved RAW context")

    @staticmethod
    def _validate_raw_source_origin(
        connection: sqlite3.Connection, evidence: sqlite3.Row, values: dict[str, object]
    ) -> None:
        existing = connection.execute(
            "SELECT origin FROM evidence_review_contexts WHERE evidence_id = ?",
            (evidence["evidence_id"],),
        ).fetchone()
        if existing is None or existing["origin"] != "RAW" or values["origin"] == "RAW":
            return
        derived_contexts = connection.execute(
            """SELECT source_evidence_ids FROM evidence_review_contexts
               WHERE origin = 'DERIVED'"""
        ).fetchall()
        if any(
            evidence["evidence_id"] in json.loads(context["source_evidence_ids"])
            for context in derived_contexts
        ):
            raise ValueError("Referenced RAW Evidence Item cannot change origin")

    @staticmethod
    def _normalise_context(context: dict[str, object]) -> dict[str, object]:
        controlled = {
            "origin": {"RAW", "DERIVED", "AUDITOR_AUTHORED"},
            "freshness": {"CURRENT", "STALE", "SUPERSEDED", "UNCERTAIN"},
            "gap_status": {"NOT_REQUESTED", "REQUESTED_NOT_PROVIDED", "UNAVAILABLE", "STALE", "INADEQUATE", "NOT_APPLICABLE"},
        }
        optional: dict[str, object] = {}
        for key in ("provider", "source_date", "source_version", "source_location", "description", "limitations", "duplicate_evidence_id", "gap_explanation", "gap_materiality"):
            value = context.get(key)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{key} must be text")
            optional[key] = value.strip() if isinstance(value, str) and value.strip() else None
        controlled_values: dict[str, object] = {}
        for key, choices in controlled.items():
            value = context.get(key)
            if value not in choices:
                raise ValueError(f"Use a controlled {key}")
            controlled_values[key] = value
        if optional["gap_materiality"] not in {"MATERIAL", "NOT_MATERIAL", "UNDETERMINED", None}:
            raise ValueError("Use controlled gap materiality")
        if controlled_values["gap_status"] not in {"NOT_REQUESTED", "NOT_APPLICABLE"}:
            if optional["gap_explanation"] is None or optional["gap_materiality"] is None:
                raise ValueError("Gap explanation and materiality are required")
        source_ids = context.get("source_evidence_ids", [])
        if not isinstance(source_ids, list) or not all(isinstance(value, str) for value in source_ids):
            raise ValueError("Source Evidence Items must be a list of identifiers")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Source Evidence Items must be unique")
        for source_id in source_ids:
            WorkbenchStore._validate_evidence_id(source_id)
        return {
            "provider": optional["provider"],
            "origin": controlled_values["origin"],
            "source_date": optional["source_date"],
            "source_version": optional["source_version"],
            "source_location": optional["source_location"],
            "description": optional["description"],
            "freshness": controlled_values["freshness"],
            "limitations": optional["limitations"],
            "duplicate_evidence_id": optional["duplicate_evidence_id"],
            "source_evidence_ids": json.dumps(source_ids, separators=(",", ":")),
            "gap_status": controlled_values["gap_status"],
            "gap_explanation": optional["gap_explanation"],
            "gap_materiality": optional["gap_materiality"],
        }

    @staticmethod
    def _normalise_question(question: dict[str, object]) -> dict[str, object]:
        question_type = question.get("question_type")
        if question_type not in {"MAIN", "IMPLEMENTATION", "EFFECTIVENESS"}:
            raise ValueError("Use a controlled Audit Question type")
        engagement_id = WorkbenchStore._required_text(question.get("engagement_id"), "Engagement identifier")
        control_id = WorkbenchStore._required_text(question.get("control_id"), "Control identifier")
        parent_id = question.get("parent_question_id")
        if parent_id is not None:
            parent_id = WorkbenchStore._required_text(parent_id, "Parent Audit Question identifier")
        return {"engagement_id": engagement_id, "control_id": control_id,
                "question_type": question_type, "parent_question_id": parent_id,
                "question_text": WorkbenchStore._required_text(question.get("question_text"), "Question text"),
                "purpose": WorkbenchStore._required_text(question.get("purpose"), "Audit Question purpose")}

    @staticmethod
    def _required_text(value: object, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} is required")
        return value.strip()

    def _question_version(self, question_id: str, version: int) -> dict[str, object]:
        with self.connect() as connection:
            question = self._safe_question(connection, question_id)
            row = connection.execute(
                "SELECT * FROM audit_question_versions WHERE question_id = ? AND version = ?",
                (question_id, version),
            ).fetchone()
        if row is None:
            raise KeyError(question_id)
        return {**dict(question), **dict(row)}

    @staticmethod
    def _context_json(row: sqlite3.Row | None) -> dict[str, object] | None:
        if row is None:
            return None
        result = dict(row)
        result["source_evidence_ids"] = json.loads(result["source_evidence_ids"])
        return result

    @staticmethod
    def _completion_sha256(evidence_id: str, notes: str) -> str:
        return sha256(
            json.dumps({"evidence_id": evidence_id, "notes": notes}, sort_keys=True).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _decision_sha256(question_id: str, version: int, status: str, reason: str) -> str:
        return sha256(
            json.dumps(
                {
                    "question_id": question_id,
                    "question_version": version,
                    "status": status,
                    "reason": reason,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _decision_json(row: sqlite3.Row) -> dict[str, object]:
        return {
            "decision_id": row["decision_id"],
            "question_id": row["question_id"],
            "question_version": row["question_version"],
            "status": row["status"],
            "reason": row["reason"],
            "decided_at": row["decided_at"],
            "decided_by": row["decided_by"],
        }

    @staticmethod
    def _completion_json(evidence_id: str, row: sqlite3.Row) -> dict[str, object]:
        return {"evidence_id": evidence_id, "status": "REVIEWED", "reviewer": row["reviewer"],
                "reviewed_at": row["reviewed_at"], "notes": row["notes"],
                "completed_at": row["completed_at"]}

    # ── Snapshot / Change Record / Export ──────────────────────

    def _capture_snapshot(self, connection: sqlite3.Connection) -> dict[str, object]:
        """Capture a read-only snapshot of all records in the current engagement.

        Returns a dict with nodes, edges, warnings, and a content hash.
        This is a self-contained snapshot — does not depend on graph_projection().
        Uses the passed connection to avoid opening a second connection
        that would conflict with the caller's transaction.
        """
        row = connection.execute(
            self._engagement_select() + " WHERE current.current_slot = 1"
        ).fetchone()
        if row is None:
            return {
                "engagement_id": None,
                "nodes": [],
                "edges": [],
                "warnings": [],
                "content_hash": sha256(b"").hexdigest(),
            }
        engagement_id = row["engagement_id"]

        # ── Nodes (same 8 types as graph_projection) ──
        nodes: list[dict[str, object]] = []

        es_row = connection.execute(
            "SELECT engagement_id, title, reference, state, accountable_auditor "
            "FROM engagement_setups WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchone()
        if es_row:
            nodes.append({
                "id": es_row["engagement_id"], "type": "engagement",
                "label": es_row["title"], "reference": es_row["reference"],
                "state": es_row["state"],
            })

        for row in connection.execute(
            "SELECT obligation_id, title FROM obligations WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchall():
            nodes.append({"id": row["obligation_id"], "type": "obligation", "label": row["title"]})

        for row in connection.execute(
            "SELECT r.risk_id, r.title FROM risks r "
            "JOIN obligations o ON r.obligation_id = o.obligation_id "
            "WHERE o.engagement_id = ?",
            (engagement_id,),
        ).fetchall():
            nodes.append({"id": row["risk_id"], "type": "risk", "label": row["title"]})

        for row in connection.execute(
            "SELECT c.control_id, c.title FROM controls c "
            "JOIN risks r ON c.risk_id = r.risk_id "
            "JOIN obligations o ON r.obligation_id = o.obligation_id "
            "WHERE o.engagement_id = ?",
            (engagement_id,),
        ).fetchall():
            nodes.append({"id": row["control_id"], "type": "control", "label": row["title"]})

        for row in connection.execute(
            "SELECT ow.owner_id, ow.name FROM owners ow "
            "JOIN controls c ON ow.control_id = c.control_id "
            "JOIN risks r ON c.risk_id = r.risk_id "
            "JOIN obligations o ON r.obligation_id = o.obligation_id "
            "WHERE o.engagement_id = ?",
            (engagement_id,),
        ).fetchall():
            nodes.append({"id": row["owner_id"], "type": "owner", "label": row["name"]})

        evidence_id_set: set[str] = set()
        for row in connection.execute(
            "SELECT evidence_id, filename, status, is_capture, source_text "
            "FROM evidence WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchall():
            node: dict[str, object] = {
                "id": row["evidence_id"], "type": "evidence",
                "label": row["filename"], "status": row["status"],
                "is_capture": bool(row["is_capture"]),
            }
            if row["source_text"]:
                node["has_source_text"] = True
            nodes.append(node)
            evidence_id_set.add(row["evidence_id"])

        for row in connection.execute(
            "SELECT m.mate_id, m.title FROM mates m "
            "JOIN evidence e ON m.evidence_id = e.evidence_id "
            "WHERE e.engagement_id = ?",
            (engagement_id,),
        ).fetchall():
            nodes.append({"id": row["mate_id"], "type": "mate", "label": row["title"]})

        for row in connection.execute(
            "SELECT c.conclusion_id, c.title, c.status FROM conclusions c "
            "JOIN mates m ON c.mate_id = m.mate_id "
            "JOIN evidence e ON m.evidence_id = e.evidence_id "
            "WHERE e.engagement_id = ?",
            (engagement_id,),
        ).fetchall():
            nodes.append({
                "id": row["conclusion_id"], "type": "conclusion",
                "label": row["title"], "status": row["status"],
            })

        # ── Approved edges ──
        node_ids = {n["id"] for n in nodes}
        edges: list[dict[str, object]] = []
        warnings: list[dict[str, object]] = []

        # Scope relationships to only rows referencing this engagement's records
        if node_ids:
            id_list = sorted(node_ids)
            placeholders = ",".join("?" for _ in id_list)
            rel_rows = connection.execute(
                f"SELECT * FROM relationships "
                f"WHERE source_record_id IN ({placeholders}) "
                f"   OR target_record_id IN ({placeholders})",
                id_list + id_list,
            ).fetchall()
        else:
            rel_rows = []

        for row in rel_rows:
            source = row["source_record_id"]
            target = row["target_record_id"]
            rtype = row["relationship_type"]
            rstatus = row["status"]
            is_approved = rstatus == "ACTIVE" and rtype != "CONTRA"

            edge = {"source": source, "target": target, "type": rtype, "status": rstatus}

            if source in node_ids and target in node_ids:
                if is_approved:
                    edges.append(edge)
                else:
                    warnings.append({
                        "level": "WARNING", "record_id": row["relationship_id"],
                        "detail": f"Unapproved relationship: {source} → {target} ({rtype}, {rstatus})",
                    })
            else:
                warnings.append({
                    "level": "WARNING", "record_id": row["relationship_id"],
                    "detail": f"Relationship {source} → {target} ({rtype}) references records outside the engagement graph",
                })

        # Evidence warnings
        for row in connection.execute(
            "SELECT evidence_id, is_capture, source_text, status "
            "FROM evidence WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchall():
            if not row["source_text"] or not row["source_text"].strip():
                warnings.append({
                    "level": "INFO", "record_id": row["evidence_id"],
                    "detail": f"Evidence {row['evidence_id']} has no source text — review suggestions unavailable",
                })
            if not bool(row["is_capture"]):
                warnings.append({
                    "level": "INFO", "record_id": row["evidence_id"],
                    "detail": f"Evidence {row['evidence_id']} was not field-captured (is_capture=0)",
                })

        # Content hash
        payload = json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True, default=str)
        content_hash = sha256(payload.encode()).hexdigest()

        return {
            "engagement_id": engagement_id,
            "nodes": nodes,
            "edges": edges,
            "warnings": warnings,
            "content_hash": content_hash,
        }

    def create_snapshot(self, idempotency_key: str) -> dict[str, object]:
        """Create one immutable snapshot of the current engagement.

        If an existing snapshot with the same content hash exists,
        return that snapshot (idempotent).
        """
        with self.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                snapshot = self._capture_snapshot(connection)
                if snapshot["engagement_id"] is None:
                    connection.rollback()
                    raise ValueError("No current engagement — cannot create snapshot")
                content_hash = snapshot["content_hash"]

                # Idempotency: return existing snapshot with same content hash
                existing = connection.execute(
                    "SELECT * FROM snapshots WHERE content_hash = ?",
                    (content_hash,),
                ).fetchone()
                if existing is not None:
                    connection.commit()
                    return {
                        "snapshot_id": existing["snapshot_id"],
                        "engagement_id": existing["engagement_id"],
                        "content_hash": existing["content_hash"],
                        "created_at": existing["created_at"],
                        "node_count": existing["node_count"],
                        "edge_count": existing["edge_count"],
                        "warning_count": existing["warning_count"],
                        "idempotent": True,
                    }

                snapshot_id = f"SNP-{content_hash[:12].upper()}"
                created_at = utc_now()
                snapshot_json = json.dumps({
                    "nodes": snapshot["nodes"],
                    "edges": snapshot["edges"],
                    "warnings": snapshot["warnings"],
                }, sort_keys=True, default=str)
                connection.execute(
                    "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        snapshot_id,
                        snapshot["engagement_id"],
                        content_hash,
                        created_at,
                        len(snapshot["nodes"]),
                        len(snapshot["edges"]),
                        len(snapshot["warnings"]),
                        snapshot_json,
                    ),
                )
                connection.commit()
                return {
                    "snapshot_id": snapshot_id,
                    "engagement_id": snapshot["engagement_id"],
                    "content_hash": content_hash,
                    "created_at": created_at,
                    "node_count": len(snapshot["nodes"]),
                    "edge_count": len(snapshot["edges"]),
                    "warning_count": len(snapshot["warnings"]),
                    "idempotent": False,
                }
            except Exception:
                connection.rollback()
                raise

    def detect_changes(self, snapshot_id: str, export_id: str, idempotency_key: str) -> list[ChangeRecord]:
        """Detect changes between the latest prior snapshot and the current one.

        Returns append-only change records. If no prior snapshot exists,
        all current records are reported as 'added'.

        Checks idempotency: if change records with this idempotency_key
        already exist, returns the existing records (never 409).
        """
        from src.ace.workbench.change_record import ChangeRecord

        with self.connect() as connection:
            # Idempotency check
            existing = connection.execute(
                "SELECT * FROM change_records WHERE idempotency_key = ? ORDER BY timestamp",
                (idempotency_key,),
            ).fetchall()
            if existing:
                return [
                    ChangeRecord(
                        change_id=row["change_id"],
                        export_id=row["export_id"],
                        record_id=row["record_id"],
                        snapshot_id=row["snapshot_id"],
                        evidence_id=row["evidence_id"],
                        idempotency_key=row["idempotency_key"],
                        timestamp=row["timestamp"],
                        change_type=row["change_type"],  # type: ignore[arg-type]
                        record_type=row["record_type"],
                        label=row["label"],
                        detail=row["detail"],
                    )
                    for row in existing
                ]

            current = self._capture_snapshot(connection)
            current_engagement_id = current.get("engagement_id")

            # Find the prior snapshot (latest before this one, same engagement)
            if current_engagement_id:
                prior = connection.execute(
                    "SELECT * FROM snapshots WHERE snapshot_id != ? "
                    "AND engagement_id = ? "
                    "ORDER BY created_at DESC LIMIT 1",
                    (snapshot_id, current_engagement_id),
                ).fetchone()
            else:
                prior = None

            current_node_ids = {n["id"] for n in current["nodes"]}
            current_node_map = {n["id"]: n for n in current["nodes"]}
            # Build edge identity sets (source→target→type tuples)
            current_edge_ids: set[tuple[str, str, str]] = {
                (str(e["source"]), str(e["target"]), str(e["type"]))
                for e in current["edges"]
            }

            prior_node_ids: set[str] = set()
            prior_node_map: dict[str, dict[str, object]] = {}
            prior_edge_ids: set[tuple[str, str, str]] = set()
            if prior is not None:
                prior_snap = self._capture_snapshot_for_id(connection, prior["snapshot_id"])
                if prior_snap is not None:
                    prior_node_ids = {n["id"] for n in prior_snap["nodes"]}
                    prior_node_map = {n["id"]: n for n in prior_snap["nodes"]}
                    prior_edge_ids = {
                        (str(e["source"]), str(e["target"]), str(e["type"]))
                        for e in prior_snap.get("edges", [])
                    }

            changes: list[ChangeRecord] = []

            # Added: in current but not in prior
            for nid in current_node_ids - prior_node_ids:
                node = current_node_map[nid]
                evidence_id = nid if node.get("type") == "evidence" else None
                changes.append(ChangeRecord.make(
                    export_id=export_id,
                    record_id=str(nid),
                    snapshot_id=snapshot_id,
                    evidence_id=evidence_id,
                    idempotency_key=idempotency_key,
                    change_type="added",
                    record_type=str(node.get("type", "unknown")),
                    label=str(node.get("label", "")),
                ))

            # Removed: in prior but not in current
            for nid in prior_node_ids - current_node_ids:
                node = prior_node_map.get(nid, {"type": "unknown", "label": ""})
                evidence_id = nid if node.get("type") == "evidence" else None
                changes.append(ChangeRecord.make(
                    export_id=export_id,
                    record_id=str(nid),
                    snapshot_id=snapshot_id,
                    evidence_id=evidence_id,
                    idempotency_key=idempotency_key,
                    change_type="removed",
                    record_type=str(node.get("type", "unknown")),
                    label=str(node.get("label", "")),
                ))

            # Modified: in both but content differs
            for nid in current_node_ids & prior_node_ids:
                cur_node = current_node_map[nid]
                prior_node = prior_node_map.get(nid)
                if prior_node is not None and cur_node != prior_node:
                    evidence_id = nid if cur_node.get("type") == "evidence" else None
                    changes.append(ChangeRecord.make(
                        export_id=export_id,
                        record_id=str(nid),
                        snapshot_id=snapshot_id,
                        evidence_id=evidence_id,
                        idempotency_key=idempotency_key,
                        change_type="modified",
                        record_type=str(cur_node.get("type", "unknown")),
                        label=str(cur_node.get("label", "")),
                        detail="Record content changed between snapshots",
                    ))

            # Edge-level change detection — relationship edges as first-class records
            added_edges = current_edge_ids - prior_edge_ids
            removed_edges = prior_edge_ids - current_edge_ids
            for src, tgt, etype in added_edges:
                changes.append(ChangeRecord.make(
                    export_id=export_id,
                    record_id=f"{src}→{tgt}",
                    snapshot_id=snapshot_id,
                    evidence_id=None,
                    idempotency_key=idempotency_key,
                    change_type="added",
                    record_type="relationship",
                    label=f"{src} → {tgt}",
                    detail=f"Relationship {etype} was added between snapshots",
                ))
            for src, tgt, etype in removed_edges:
                changes.append(ChangeRecord.make(
                    export_id=export_id,
                    record_id=f"{src}→{tgt}",
                    snapshot_id=snapshot_id,
                    evidence_id=None,
                    idempotency_key=idempotency_key,
                    change_type="removed",
                    record_type="relationship",
                    label=f"{src} → {tgt}",
                    detail=f"Relationship {etype} was removed between snapshots",
                ))

            # Persist change records (append-only via trigger, but INSERT is safe)
            for ch in changes:
                connection.execute(
                    "INSERT INTO change_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        ch.change_id, ch.export_id, ch.record_id, ch.snapshot_id,
                        ch.evidence_id, ch.idempotency_key, ch.timestamp,
                        ch.change_type, ch.record_type, ch.label, ch.detail,
                    ),
                )

            return changes

    def _capture_snapshot_for_id(
        self, connection: sqlite3.Connection, snapshot_id: str
    ) -> dict[str, object] | None:
        """Reconstruct a snapshot from stored data."""
        snap_row = connection.execute(
            "SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        if snap_row is None:
            return None
        try:
            data = json.loads(snap_row["snapshot_data"])
        except (json.JSONDecodeError, KeyError):
            return {"nodes": [], "edges": [], "warnings": []}
        return {
            "nodes": data.get("nodes", []),
            "edges": data.get("edges", []),
            "warnings": data.get("warnings", []),
        }

    def media(self, evidence_id: str) -> tuple[Path, str] | None:
        self._validate_evidence_id(evidence_id)
        with self.connect() as connection:
            try:
                connection.execute("BEGIN")
                row = self._review_evidence(connection, evidence_id)
                if row is None:
                    connection.commit()
                    return None
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        if row is None or row["media_path"] is None:
            return None
        file_path = self._media_file_path(PurePosixPath(row["media_path"]))
        if not file_path.is_file():
            return None
        return file_path, row["media_type"]

    def review(self, evidence_id: str, reviewer: str, notes: str) -> dict[str, str] | None:
        notes = self._required_text(notes, "Review notes")
        request_sha256 = self._completion_sha256(evidence_id, notes)
        return self.complete_evidence_review(
            evidence_id,
            {"completion_attempt_key": f"legacy-{request_sha256}", "notes": notes},
            reviewer,
        )  # type: ignore[return-value]

    def _media_file_path(self, media_path: PurePosixPath) -> Path:
        if (
            media_path.is_absolute()
            or media_path.parts[:1] != ("media",)
            or ".." in media_path.parts
            or len(media_path.parts) != 2
        ):
            raise ValueError("Unsafe media path")
        file_path = (self.data_dir / Path(*media_path.parts)).resolve()
        try:
            file_path.relative_to(self.media_dir.resolve())
        except ValueError as error:
            raise ValueError("Unsafe media path") from error
        return file_path

    @staticmethod
    def _validate_evidence_id(evidence_id: str) -> None:
        if not EVIDENCE_ID_PATTERN.fullmatch(evidence_id):
            raise ValueError("Invalid evidence identifier")

    @staticmethod
    def _validate_engagement_id(engagement_id: str) -> None:
        if not ENGAGEMENT_ID_PATTERN.fullmatch(engagement_id):
            raise EngagementNotFoundError()
