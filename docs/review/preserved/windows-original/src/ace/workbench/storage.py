"""SQLite storage for fictional local workbench evidence."""

from __future__ import annotations

import os
import re
import sqlite3
import uuid
from hashlib import sha256
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from src.ace.workbench.engagement import EngagementDraft


EVIDENCE_ID_PATTERN = re.compile(r"^EVD-(?:FIC-\d{4}|[A-F0-9]{12})$")
ENGAGEMENT_ID_PATTERN = re.compile(r"^ENG-(?:FIC-\d{4}|[A-F0-9]{12})$")
CAPTURE_ATTEMPT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{7,127}$")
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPOSITORY_ROOT.parent / "sqe-local-data"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_data_dir() -> Path:
    """Return the external local data directory without creating it."""
    configured_dir = os.environ.get("ACE_DATA_DIR")
    data_dir = Path(configured_dir) if configured_dir else DEFAULT_DATA_DIR
    resolved_dir = data_dir.expanduser().resolve()
    try:
        resolved_dir.relative_to(REPOSITORY_ROOT)
    except ValueError:
        return resolved_dir
    raise RuntimeError("ACE_DATA_DIR must be outside the source workspace")


class EngagementNotFoundError(LookupError):
    """The controlled Engagement does not exist."""


class DuplicateEngagementReferenceError(ValueError):
    """The Engagement reference is already controlled by another draft."""


class NoReadyCurrentEngagementError(RuntimeError):
    """Capture is blocked until a ready current Engagement exists."""


class CaptureAttemptConflictError(RuntimeError):
    """A capture attempt key was reused with a different request."""


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
        self.data_dir = data_dir or resolve_data_dir()
        self.media_dir = self.data_dir / "media"
        self.database_path = self.data_dir / "workbench.sqlite3"

    def connect(self) -> sqlite3.Connection:
        self.media_dir.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        self._initialise(connection)
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
                request_sha256 TEXT
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
                    event_type IN ('ENGAGEMENT_CREATED', 'ENGAGEMENT_ACTIVATED')
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
            """
        )
        self._add_evidence_columns(connection)
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS evidence_capture_attempt_key_unique
            ON evidence(capture_attempt_key)
            WHERE capture_attempt_key IS NOT NULL
            """
        )
        self._seed_fictional_chain(connection)
        connection.commit()

    @staticmethod
    def _add_evidence_columns(connection: sqlite3.Connection) -> None:
        existing_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(evidence)")
        }
        for column, definition in (
            ("engagement_id", "TEXT REFERENCES engagement_setups(engagement_id)"),
            ("capture_attempt_key", "TEXT"),
            ("request_sha256", "TEXT"),
        ):
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE evidence ADD COLUMN {column} {definition}")

    @staticmethod
    def _seed_fictional_chain(connection: sqlite3.Connection) -> None:
        connection.execute(
            "INSERT OR IGNORE INTO engagements VALUES (?, ?, ?)",
            ("ENG-FIC-0001", "Fictional Mobile Field Capture Engagement", "EOI-FIC-0001"),
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
                is_capture
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO mates VALUES (?, ?, ?)",
            ("MATE-FIC-0001", "EVD-FIC-0001", "Fictional MATE assessment"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO conclusions VALUES (?, ?, ?, ?)",
            (
                "CON-FIC-0001",
                "MATE-FIC-0001",
                "CANDIDATE",
                "Fictional conclusion candidate",
            ),
        )
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
        }

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

    def media(self, evidence_id: str) -> tuple[Path, str] | None:
        self._validate_evidence_id(evidence_id)
        with self.connect() as connection:
            row = connection.execute(
                "SELECT media_path, media_type FROM evidence WHERE evidence_id = ?", (evidence_id,)
            ).fetchone()
        if row is None or row["media_path"] is None:
            return None
        file_path = self._media_file_path(PurePosixPath(row["media_path"]))
        if not file_path.is_file():
            return None
        return file_path, row["media_type"]

    def review(self, evidence_id: str, reviewer: str, notes: str) -> dict[str, str] | None:
        self._validate_evidence_id(evidence_id)
        reviewed_at = utc_now()
        with self.connect() as connection:
            evidence = connection.execute(
                "SELECT evidence_id FROM evidence WHERE evidence_id = ?", (evidence_id,)
            ).fetchone()
            if evidence is None:
                return None
            connection.execute(
                "UPDATE evidence SET status = ? WHERE evidence_id = ?", ("REVIEWED", evidence_id)
            )
            connection.execute(
                """
                INSERT INTO reviews VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(evidence_id) DO UPDATE SET
                    reviewer = excluded.reviewer,
                    reviewed_at = excluded.reviewed_at,
                    notes = excluded.notes
                """,
                (f"REV-{uuid.uuid4().hex[:12].upper()}", evidence_id, reviewer, reviewed_at, notes),
            )
            connection.execute(
                "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?)",
                (f"EVT-{uuid.uuid4().hex[:12].upper()}", evidence_id, "REVIEWED", reviewed_at, reviewer),
            )
            connection.commit()
        return {
            "evidence_id": evidence_id,
            "status": "REVIEWED",
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "notes": notes,
        }

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
