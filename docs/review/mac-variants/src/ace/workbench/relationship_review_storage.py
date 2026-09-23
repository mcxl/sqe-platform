"""SQLite persistence for the fictional Relationship Review path."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import UTC, datetime
from hashlib import sha256
from typing import TYPE_CHECKING, Any, Callable

from src.ace.domain.assessment import (
    ApprovedMATEAssessment,
    AuditorDecisionStatus,
    MateDimension,
)
from src.ace.domain.trace import (
    AccountableRoleRecord,
    AuditorRelationshipDecision,
    BindingObligationRecord,
    PlanningControlRecord,
    ProposedTraceRelationship,
    RiskRecord,
    TraceRelationshipType,
)
from src.ace.engine.approval import rehydrate_verified_g0_mate
from src.ace.engine.tracing import build_accepted_planning_trace

if TYPE_CHECKING:
    from src.ace.workbench.relationship_review import RelationshipTraceInputs


DECISIONS = {"APPROVED", "REJECTED", "CHANGES_REQUIRED"}
REQUIRED_RELATIONSHIP_TYPES = {relationship_type.value for relationship_type in TraceRelationshipType}
DECISION_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{7,127}$")
PREVIEW_TOKEN_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _loads(value: str) -> dict[str, Any]:
    return json.loads(value)


class RelationshipReviewStorage:
    """Keep Relationship Review records in the external workbench database."""

    def __init__(self, workbench_store: Any) -> None:
        self._store = workbench_store

    @staticmethod
    def initialise(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS relationship_review_items (
                relationship_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL REFERENCES engagement_setups(engagement_id),
                relationship_type TEXT NOT NULL,
                source_record_id TEXT NOT NULL,
                target_record_id TEXT NOT NULL,
                title TEXT NOT NULL,
                material_risk_priority INTEGER,
                waiting_since TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS relationship_review_versions (
                relationship_id TEXT NOT NULL REFERENCES relationship_review_items(relationship_id),
                relationship_version INTEGER NOT NULL CHECK (relationship_version > 0),
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                PRIMARY KEY (relationship_id, relationship_version)
            );
            CREATE TABLE IF NOT EXISTS relationship_review_drafts (
                relationship_id TEXT PRIMARY KEY REFERENCES relationship_review_items(relationship_id),
                current_version INTEGER NOT NULL CHECK (current_version > 0),
                proposed_decision TEXT CHECK (
                    proposed_decision IN ('APPROVED', 'REJECTED', 'CHANGES_REQUIRED')
                    OR proposed_decision IS NULL
                ),
                draft_reason TEXT,
                updated_at TEXT NOT NULL,
                updated_by TEXT NOT NULL,
                FOREIGN KEY (relationship_id, current_version)
                    REFERENCES relationship_review_versions(relationship_id, relationship_version)
            );
            CREATE TABLE IF NOT EXISTS relationship_review_decisions (
                decision_id TEXT PRIMARY KEY,
                relationship_id TEXT NOT NULL,
                relationship_version INTEGER NOT NULL,
                decision_status TEXT NOT NULL CHECK (
                    decision_status IN ('APPROVED', 'REJECTED', 'CHANGES_REQUIRED')
                ),
                reason TEXT NOT NULL CHECK (length(trim(reason)) > 0),
                decided_at TEXT NOT NULL,
                decided_by TEXT NOT NULL,
                preview_token TEXT,
                FOREIGN KEY (relationship_id, relationship_version)
                    REFERENCES relationship_review_versions(relationship_id, relationship_version),
                UNIQUE (relationship_id, relationship_version)
            );
            CREATE TABLE IF NOT EXISTS relationship_review_events (
                event_id TEXT PRIMARY KEY,
                relationship_id TEXT NOT NULL,
                relationship_version INTEGER NOT NULL,
                decision_id TEXT NOT NULL REFERENCES relationship_review_decisions(decision_id),
                event_type TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                actor TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS relationship_review_retries (
                decision_key TEXT PRIMARY KEY,
                relationship_id TEXT NOT NULL,
                relationship_version INTEGER NOT NULL CHECK (relationship_version > 0),
                request_sha256 TEXT NOT NULL,
                result_json TEXT NOT NULL,
                decision_id TEXT NOT NULL REFERENCES relationship_review_decisions(decision_id),
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (relationship_id, relationship_version)
                    REFERENCES relationship_review_versions(relationship_id, relationship_version)
            );
            CREATE TABLE IF NOT EXISTS approved_relationships (
                relationship_id TEXT NOT NULL,
                relationship_version INTEGER NOT NULL,
                decision_id TEXT NOT NULL UNIQUE REFERENCES relationship_review_decisions(decision_id),
                approved_at TEXT NOT NULL,
                approved_by TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                PRIMARY KEY (relationship_id, relationship_version)
            );
            CREATE TABLE IF NOT EXISTS accepted_planning_traces (
                trace_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL REFERENCES engagement_setups(engagement_id),
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS relationship_trace_input_snapshots (
                engagement_id TEXT PRIMARY KEY REFERENCES engagement_setups(engagement_id),
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL
            );
            CREATE TRIGGER IF NOT EXISTS relationship_review_items_no_update
            BEFORE UPDATE ON relationship_review_items BEGIN
                SELECT RAISE(ABORT, 'Relationship Review items are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_review_items_no_delete
            BEFORE DELETE ON relationship_review_items BEGIN
                SELECT RAISE(ABORT, 'Relationship Review items are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_review_versions_no_update
            BEFORE UPDATE ON relationship_review_versions BEGIN
                SELECT RAISE(ABORT, 'Relationship proposal versions are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_review_versions_no_delete
            BEFORE DELETE ON relationship_review_versions BEGIN
                SELECT RAISE(ABORT, 'Relationship proposal versions are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_review_decisions_no_update
            BEFORE UPDATE ON relationship_review_decisions BEGIN
                SELECT RAISE(ABORT, 'Relationship decisions are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_review_decisions_no_delete
            BEFORE DELETE ON relationship_review_decisions BEGIN
                SELECT RAISE(ABORT, 'Relationship decisions are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_review_events_no_update
            BEFORE UPDATE ON relationship_review_events BEGIN
                SELECT RAISE(ABORT, 'Relationship events are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_review_events_no_delete
            BEFORE DELETE ON relationship_review_events BEGIN
                SELECT RAISE(ABORT, 'Relationship events are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_review_retries_no_update
            BEFORE UPDATE ON relationship_review_retries BEGIN
                SELECT RAISE(ABORT, 'Relationship retry records are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_review_retries_no_delete
            BEFORE DELETE ON relationship_review_retries BEGIN
                SELECT RAISE(ABORT, 'Relationship retry records are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS approved_relationships_no_update
            BEFORE UPDATE ON approved_relationships BEGIN
                SELECT RAISE(ABORT, 'Approved Relationships are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS approved_relationships_no_delete
            BEFORE DELETE ON approved_relationships BEGIN
                SELECT RAISE(ABORT, 'Approved Relationships are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS accepted_planning_traces_no_update
            BEFORE UPDATE ON accepted_planning_traces BEGIN
                SELECT RAISE(ABORT, 'Accepted Planning Traces are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS accepted_planning_traces_no_delete
            BEFORE DELETE ON accepted_planning_traces BEGIN
                SELECT RAISE(ABORT, 'Accepted Planning Traces are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_trace_input_snapshots_no_update
            BEFORE UPDATE ON relationship_trace_input_snapshots BEGIN
                SELECT RAISE(ABORT, 'Relationship Trace Inputs are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS relationship_trace_input_snapshots_no_delete
            BEFORE DELETE ON relationship_trace_input_snapshots BEGIN
                SELECT RAISE(ABORT, 'Relationship Trace Inputs are immutable');
            END;
            """
        )
        RelationshipReviewStorage._seed(connection)

    @staticmethod
    def _seed(connection: sqlite3.Connection) -> None:
        engagement = connection.execute(
            "SELECT engagement_id FROM engagement_setups WHERE engagement_id = 'ENG-FIC-0001'"
        ).fetchone()
        if engagement is None:
            return
        records = (
            (
                "REL-FIC-0001",
                "OBLIGATION_APPLIES_TO_RISK",
                "OBL-FIC-0001",
                "RSK-FIC-0001",
                "Fictional obligation applies to risk",
                4,
                "2026-08-01T00:00:00Z",
                ["SRC-FIC-OBLIGATION", "SRC-FIC-RISK"],
            ),
            (
                "REL-FIC-0002",
                "CONTROL_TREATS_RISK",
                "CTL-FIC-0001",
                "RSK-FIC-0001",
                "Fictional control treats risk",
                3,
                "2026-08-02T00:00:00Z",
                ["SRC-FIC-CONTROL", "SRC-FIC-RISK"],
            ),
            (
                "REL-FIC-0003",
                "ROLE_ACCOUNTABLE_FOR_CONTROL",
                "ROLE-FIC-0001",
                "CTL-FIC-0001",
                "Fictional role is accountable for control",
                2,
                "2026-08-03T00:00:00Z",
                ["SRC-FIC-ROLE", "SRC-FIC-CONTROL"],
            ),
            (
                "REL-FIC-0004",
                "CONTROL_HAS_APPROVED_MATE_ASSESSMENT",
                "CTL-FIC-0001",
                "MATE:CTL-FIC-0001",
                "Fictional control has approved MATE assessment",
                1,
                "2026-08-04T00:00:00Z",
                ["SRC-FIC-CONTROL"],
            ),
        )
        for relationship_id, relationship_type, source, target, title, priority, waiting_since, sources in records:
            connection.execute(
                """INSERT OR IGNORE INTO relationship_review_items (
                       relationship_id, engagement_id, relationship_type,
                       source_record_id, target_record_id, title,
                       material_risk_priority, waiting_since
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    relationship_id,
                    engagement["engagement_id"],
                    relationship_type,
                    source,
                    target,
                    title,
                    priority,
                    waiting_since,
                ),
            )
            snapshot = {
                "relationship_version": 1,
                "rationale": "Fictional relationship proposal awaiting review.",
                "supporting_source_ids": sources,
                "gaps": ["No gap identified."],
                "contradictions": ["No contradiction identified."],
                "duplicate_warnings": ["No duplicate warning identified."],
            }
            connection.execute(
                "INSERT OR IGNORE INTO relationship_review_versions VALUES (?, 1, ?, ?, 'seed')",
                (relationship_id, _json(snapshot), "2026-08-01T00:00:00Z"),
            )
            connection.execute(
                "INSERT OR IGNORE INTO relationship_review_drafts VALUES (?, 1, NULL, NULL, ?, 'seed')",
                (relationship_id, "2026-08-01T00:00:00Z"),
            )
        connection.execute(
            """INSERT OR IGNORE INTO relationship_trace_input_snapshots
               VALUES (?, ?, ?, ?)""",
            (
                "ENG-FIC-0001",
                _json(RelationshipReviewStorage._fictional_trace_input_snapshot()),
                "2026-08-01T00:00:00Z",
                "seed",
            ),
        )

    @staticmethod
    def _fictional_trace_input_snapshot() -> dict[str, object]:
        def source(source_id: str) -> dict[str, str]:
            return {
                "source_id": source_id,
                "document_title": "Fictional planning source",
                "document_version": "1",
                "source_location": "Fictional register",
                "source_wording": "Fictional current source wording.",
                "status": "CURRENT",
            }

        decisions = [
            {
                "decision_id": f"DEC-MATE-{dimension.value}",
                "proposal_id": f"PROP-MATE-{dimension.value}",
                "proposal_version": 1,
                "dimension": dimension.value,
                "decision_status": "APPROVED",
                "approved_answer": True,
                "final_sufficiency": "SUFFICIENT_FOR_DESIGN_ASSESSMENT",
                "reviewer_id": "auditor",
                "review_notes": "Fictional MATE approval.",
                "reviewed_at": "2026-08-01T00:00:00Z",
            }
            for dimension in MateDimension
        ]
        return {
            "obligation": {
                "obligation_id": "OBL-FIC-0001",
                "title": "Fictional obligation",
                "binding_instrument": "Fictional instrument",
                "clause": "1",
                "obligation_text": "Fictional obligation text.",
                "source_reference": source("SRC-FIC-OBLIGATION"),
            },
            "risk": {
                "risk_id": "RSK-FIC-0001",
                "title": "Fictional risk",
                "risk_statement": "Fictional risk statement.",
                "source_reference": source("SRC-FIC-RISK"),
            },
            "control": {
                "control_id": "CTL-FIC-0001",
                "title": "Fictional control",
                "design_statement": "Fictional control statement.",
                "source_reference": source("SRC-FIC-CONTROL"),
            },
            "accountable_role": {
                "accountability_id": "ROLE-FIC-0001",
                "subject_type": "JOB_ROLE",
                "subject_title": "Fictional accountable role",
                "accountability_statement": "Fictional accountability statement.",
                "source_reference": source("SRC-FIC-ROLE"),
            },
            "mate_assessment": {
                "control_id": "CTL-FIC-0001",
                "title": "Fictional control",
                "description": "Fictional MATE assessment.",
                "hazard_category": "GOVERNANCE_OVERSIGHT",
                "confidence_score": 1.0,
                "reviewer_notes": "Fictional approved MATE snapshot.",
                "decisions": decisions,
                "dimensions": {
                    "mandate": True,
                    "accountability": True,
                    "trigger": True,
                    "escalation": True,
                },
            },
        }

    def queue(self) -> dict[str, object]:
        with self._store.connect() as connection:
            access = self._current_engagement(connection)
            if access["outcome"] != "ready":
                return access
            rows = connection.execute(
                """SELECT item.relationship_id, item.engagement_id, item.title,
                          item.relationship_type, draft.current_version,
                          item.material_risk_priority, item.waiting_since
                   FROM relationship_review_items AS item
                   JOIN relationship_review_drafts AS draft USING (relationship_id)
                   WHERE item.engagement_id = ?
                   ORDER BY item.material_risk_priority IS NULL,
                            item.material_risk_priority DESC,
                            item.waiting_since ASC""",
                (access["engagement_id"],),
            ).fetchall()
        return {
            "outcome": "ready",
            "engagement_id": access["engagement_id"],
            "queue": [dict(row) for row in rows],
        }

    def state(self, relationship_id: str) -> dict[str, object]:
        with self._store.connect() as connection:
            access = self._current_engagement(connection)
            if access["outcome"] != "ready":
                return access
            return {
                "outcome": "ready",
                "state": self._state(connection, relationship_id, str(access["engagement_id"])),
            }

    def save_draft(
        self, relationship_id: str, draft: dict[str, object], actor: str
    ) -> dict[str, object]:
        with self._store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                access = self._current_engagement(connection)
                if access["outcome"] != "ready":
                    connection.rollback()
                    return access
                state = self._state(
                    connection, relationship_id, str(access["engagement_id"])
                )
                if draft["relationship_version"] != state["current_version"]:
                    connection.rollback()
                    return {"outcome": "version_stale"}
                connection.execute(
                    """UPDATE relationship_review_drafts
                       SET proposed_decision = ?, draft_reason = ?,
                           updated_at = ?, updated_by = ?
                       WHERE relationship_id = ?""",
                    (
                        draft.get("proposed_decision"),
                        draft.get("draft_reason"),
                        _now(),
                        actor,
                        relationship_id,
                    ),
                )
                result = self._state(
                    connection, relationship_id, str(access["engagement_id"])
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {"outcome": "saved", "state": result}

    def preview(
        self, relationship_id: str, request: dict[str, object]
    ) -> dict[str, object]:
        with self._store.connect() as connection:
            access = self._current_engagement(connection)
            if access["outcome"] != "ready":
                return access
            state = self._state(
                connection, relationship_id, str(access["engagement_id"])
            )
            if request["relationship_version"] != state["current_version"]:
                return {"outcome": "version_stale"}
            token = self._preview_token(state, str(request["approval_reason"]))
        return {"outcome": "ready", "state": state, "preview_token": token}

    def trace_inputs(self) -> RelationshipTraceInputs | None:
        """Load the one validated fictional trace-input snapshot for the current Engagement."""
        with self._store.connect() as connection:
            access = self._current_engagement(connection)
            if access["outcome"] != "ready":
                return None
            return self._trace_inputs_for_engagement(
                connection, str(access["engagement_id"])
            )

    def _trace_inputs_for_engagement(
        self, connection: sqlite3.Connection, engagement_id: str
    ) -> RelationshipTraceInputs | None:
        row = connection.execute(
            """SELECT snapshot_json, created_at, created_by FROM relationship_trace_input_snapshots
               WHERE engagement_id = ?""",
            (engagement_id,),
        ).fetchone()
        if row is None:
            return None
        try:
            # This public G0 store contains one immutable, controlled fixture only.
            # Do not treat a changed SQLite row as trusted persistence.
            if (
                row["created_at"] != "2026-08-01T00:00:00Z"
                or row["created_by"] != "seed"
                or row["snapshot_json"] != _json(self._fictional_trace_input_snapshot())
            ):
                return None
            snapshot = _loads(row["snapshot_json"])
            from src.ace.workbench.relationship_review import RelationshipTraceInputs

            trace_inputs = RelationshipTraceInputs(
                obligation=BindingObligationRecord.model_validate(snapshot["obligation"]),
                risk=RiskRecord.model_validate(snapshot["risk"]),
                control=PlanningControlRecord.model_validate(snapshot["control"]),
                accountable_role=AccountableRoleRecord.model_validate(
                    snapshot["accountable_role"]
                ),
                mate_assessment=rehydrate_verified_g0_mate(
                    snapshot["mate_assessment"],
                    row["created_at"],
                    row["created_by"],
                ),
            )
        except (KeyError, TypeError, ValueError):
            return None
        if (
            trace_inputs.mate_assessment.control_id != trace_inputs.control.control_id
            or not self._approved_mate_matches_dimensions(trace_inputs.mate_assessment)
        ):
            return None
        return trace_inputs

    def prepare_trace_inputs(
        self,
        relationship_id: str,
        request: dict[str, object],
        trace_input_provider: Callable[[], RelationshipTraceInputs | None] | None,
    ) -> RelationshipTraceInputs | None:
        """Load trace inputs while a read transaction holds the validated boundary."""
        with self._store.connect() as connection:
            connection.execute("BEGIN")
            try:
                if not self._requires_accepted_trace(
                    connection, relationship_id, request
                ):
                    return None
                if trace_input_provider is None:
                    access = self._current_engagement(connection)
                    return self._trace_inputs_for_engagement(
                        connection, str(access["engagement_id"])
                    )
                try:
                    return trace_input_provider()
                except ValueError:
                    return None
            finally:
                connection.rollback()

    def _requires_accepted_trace(
        self,
        connection: sqlite3.Connection,
        relationship_id: str,
        request: dict[str, object],
    ) -> bool:
        if request["decision"] != "APPROVED":
            return False
        access = self._current_engagement(connection)
        if access["outcome"] != "ready":
            return False
        engagement_id = str(access["engagement_id"])
        item = connection.execute(
            "SELECT engagement_id FROM relationship_review_items WHERE relationship_id = ?",
            (relationship_id,),
        ).fetchone()
        if item is None:
            raise KeyError(relationship_id)
        if item["engagement_id"] != engagement_id:
            return False
        existing_retry = connection.execute(
            "SELECT 1 FROM relationship_review_retries WHERE decision_key = ?",
            (request["decision_key"],),
        ).fetchone()
        if existing_retry is not None:
            return False
        state = self._state(connection, relationship_id, engagement_id)
        if request["relationship_version"] != state["current_version"]:
            return False
        existing_decision = connection.execute(
            """SELECT 1 FROM relationship_review_decisions
               WHERE relationship_id = ? AND relationship_version = ?""",
            (relationship_id, state["current_version"]),
        ).fetchone()
        if existing_decision is not None:
            return False
        expected_token = self._preview_token(state, str(request["reason"]))
        if request.get("preview_token") != expected_token:
            return False
        rows = connection.execute(
            """SELECT item.relationship_id, item.relationship_type,
                      decision.decision_status
               FROM relationship_review_items AS item
               JOIN relationship_review_drafts AS draft USING (relationship_id)
               LEFT JOIN relationship_review_decisions AS decision
                 ON decision.relationship_id = item.relationship_id
                AND decision.relationship_version = draft.current_version
               WHERE item.engagement_id = ?""",
            (engagement_id,),
        ).fetchall()
        return (
            len(rows) == len(REQUIRED_RELATIONSHIP_TYPES)
            and {row["relationship_type"] for row in rows}
            == REQUIRED_RELATIONSHIP_TYPES
            and all(
                row["relationship_id"] == relationship_id
                or row["decision_status"] == "APPROVED"
                for row in rows
            )
        )

    @staticmethod
    def _approved_mate_matches_dimensions(mate: ApprovedMATEAssessment) -> bool:
        if len(mate.decisions) != len(MateDimension):
            return False
        dimensions = [decision.dimension for decision in mate.decisions]
        if set(dimensions) != set(MateDimension) or len(dimensions) != len(set(dimensions)):
            return False
        decision_ids = [decision.decision_id for decision in mate.decisions]
        if len(decision_ids) != len(set(decision_ids)):
            return False
        return all(
            decision.decision_status is AuditorDecisionStatus.APPROVED
            and decision.approved_answer
            is getattr(mate.dimensions, decision.dimension.field_name)
            for decision in mate.decisions
        )

    def finalise(
        self,
        relationship_id: str,
        request: dict[str, object],
        actor: str,
        trace_input_provider: Callable[[], RelationshipTraceInputs | None],
    ) -> dict[str, object]:
        canonical = _json({"relationship_id": relationship_id, **request})
        request_hash = sha256(canonical.encode("utf-8")).hexdigest()
        with self._store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                access = self._current_engagement(connection)
                if access["outcome"] != "ready":
                    connection.rollback()
                    return access
                engagement_id = str(access["engagement_id"])
                item = connection.execute(
                    "SELECT engagement_id FROM relationship_review_items WHERE relationship_id = ?",
                    (relationship_id,),
                ).fetchone()
                if item is None:
                    raise KeyError(relationship_id)
                if item["engagement_id"] != engagement_id:
                    connection.rollback()
                    if request["decision"] == "APPROVED":
                        return {"outcome": "preview_stale"}
                    return {"outcome": "engagement_required"}

                existing_retry = connection.execute(
                    """SELECT relationship_id, relationship_version,
                              request_sha256, result_json
                       FROM relationship_review_retries WHERE decision_key = ?""",
                    (request["decision_key"],),
                ).fetchone()
                if existing_retry is not None:
                    connection.rollback()
                    if (
                        existing_retry["relationship_id"] == relationship_id
                        and existing_retry["relationship_version"]
                        == request["relationship_version"]
                        and existing_retry["request_sha256"] == request_hash
                    ):
                        return {
                            "outcome": "retry",
                            "result": _loads(existing_retry["result_json"]),
                        }
                    return {"outcome": "key_conflict"}

                state = self._state(connection, relationship_id, engagement_id)
                if request["relationship_version"] != state["current_version"]:
                    connection.rollback()
                    return {"outcome": "version_stale"}
                existing_decision = connection.execute(
                    """SELECT decision_id FROM relationship_review_decisions
                       WHERE relationship_id = ? AND relationship_version = ?""",
                    (relationship_id, state["current_version"]),
                ).fetchone()
                if existing_decision is not None:
                    connection.rollback()
                    return {"outcome": "already_recorded"}
                if request["decision"] == "APPROVED":
                    expected_token = self._preview_token(state, str(request["reason"]))
                    if request.get("preview_token") != expected_token:
                        connection.rollback()
                        return {"outcome": "preview_stale"}

                decided_at = _now()
                decision_id = f"RDEC-{uuid.uuid4().hex[:16].upper()}"
                connection.execute(
                    "INSERT INTO relationship_review_decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        decision_id,
                        relationship_id,
                        state["current_version"],
                        request["decision"],
                        request["reason"],
                        decided_at,
                        actor,
                        request.get("preview_token"),
                    ),
                )
                self._insert_event(
                    connection,
                    relationship_id,
                    int(state["current_version"]),
                    decision_id,
                    actor,
                    decided_at,
                )
                if request["decision"] == "APPROVED":
                    connection.execute(
                        "INSERT INTO approved_relationships VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            relationship_id,
                            state["current_version"],
                            decision_id,
                            decided_at,
                            actor,
                            self._approved_snapshot(state),
                        ),
                    )
                result = {
                    "decision_id": decision_id,
                    "state": self._state(connection, relationship_id, engagement_id),
                }
                if (
                    request["decision"] == "APPROVED"
                    and self._all_current_versions_approved(connection, engagement_id)
                ):
                    try:
                        trace_inputs = trace_input_provider()
                    except ValueError:
                        trace_inputs = None
                    if trace_inputs is None:
                        connection.rollback()
                        return {"outcome": "mate_required"}
                    try:
                        trace = self._build_trace(connection, engagement_id, trace_inputs)
                    except ValueError:
                        connection.rollback()
                        return {"outcome": "mate_required"}
                    connection.execute(
                        "INSERT INTO accepted_planning_traces VALUES (?, ?, ?, ?, ?)",
                        (
                            f"TRACE-{uuid.uuid4().hex[:16].upper()}",
                            engagement_id,
                            trace.model_dump_json(),
                            decided_at,
                            actor,
                        ),
                    )
                    result["trace_created"] = True
                connection.execute(
                    """INSERT INTO relationship_review_retries
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        request["decision_key"],
                        relationship_id,
                        state["current_version"],
                        request_hash,
                        _json(result),
                        decision_id,
                        decided_at,
                    ),
                )
                connection.commit()
                return {"outcome": "recorded", "result": result}
            except Exception:
                connection.rollback()
                raise

    def create_revision(
        self, relationship_id: str, request: dict[str, object], actor: str
    ) -> dict[str, object]:
        """Create the one controlled correction after CHANGES_REQUIRED."""
        canonical = _json({"relationship_id": relationship_id, **request})
        request_hash = sha256(canonical.encode("utf-8")).hexdigest()
        with self._store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                access = self._current_engagement(connection)
                if access["outcome"] != "ready":
                    connection.rollback()
                    return access
                engagement_id = str(access["engagement_id"])
                item = connection.execute(
                    "SELECT engagement_id FROM relationship_review_items WHERE relationship_id = ?",
                    (relationship_id,),
                ).fetchone()
                if item is None:
                    raise KeyError(relationship_id)
                if item["engagement_id"] != engagement_id:
                    connection.rollback()
                    return {"outcome": "engagement_required"}
                existing_retry = connection.execute(
                    """SELECT relationship_id, relationship_version, request_sha256, result_json
                       FROM relationship_review_retries WHERE decision_key = ?""",
                    (request["revision_key"],),
                ).fetchone()
                if existing_retry is not None:
                    connection.rollback()
                    if (
                        existing_retry["relationship_id"] == relationship_id
                        and existing_retry["relationship_version"]
                        == request["prior_relationship_version"]
                        and existing_retry["request_sha256"] == request_hash
                    ):
                        return {"outcome": "retry", "result": _loads(existing_retry["result_json"])}
                    return {"outcome": "key_conflict"}
                state = self._state(connection, relationship_id, engagement_id)
                if request["prior_relationship_version"] != state["current_version"]:
                    connection.rollback()
                    return {"outcome": "version_stale"}
                decision = connection.execute(
                    """SELECT decision_id, decision_status, reason FROM relationship_review_decisions
                       WHERE relationship_id = ? AND relationship_version = ?""",
                    (relationship_id, state["current_version"]),
                ).fetchone()
                if decision is None or decision["decision_status"] != "CHANGES_REQUIRED":
                    connection.rollback()
                    return {"outcome": "not_allowed"}
                original_version = connection.execute(
                    """SELECT snapshot_json FROM relationship_review_versions
                       WHERE relationship_id = ? AND relationship_version = 1""",
                    (relationship_id,),
                ).fetchone()
                if original_version is None:
                    raise RuntimeError("Original Relationship proposal version is missing")
                source_boundary = set(
                    _loads(original_version["snapshot_json"])["supporting_source_ids"]
                )
                supporting_source_ids = request["supporting_source_ids"]
                if (
                    len(supporting_source_ids) != len(set(supporting_source_ids))
                    or not set(supporting_source_ids).issubset(source_boundary)
                ):
                    connection.rollback()
                    return {"outcome": "source_boundary_invalid"}
                created_at = _now()
                next_version = int(state["current_version"]) + 1
                snapshot = {
                    "relationship_version": next_version,
                    "rationale": request["rationale"],
                    "supporting_source_ids": request["supporting_source_ids"],
                    "gaps": request["gaps"],
                    "contradictions": request["contradictions"],
                    "duplicate_warnings": request["duplicate_warnings"],
                    "revision_request": decision["reason"],
                }
                connection.execute(
                    "INSERT INTO relationship_review_versions VALUES (?, ?, ?, ?, ?)",
                    (relationship_id, next_version, _json(snapshot), created_at, actor),
                )
                connection.execute(
                    """UPDATE relationship_review_drafts
                       SET current_version = ?, proposed_decision = NULL,
                           draft_reason = NULL, updated_at = ?, updated_by = ?
                       WHERE relationship_id = ?""",
                    (next_version, created_at, actor, relationship_id),
                )
                result = {
                    "decision_id": decision["decision_id"],
                    "state": self._state(connection, relationship_id, engagement_id),
                }
                connection.execute(
                    """INSERT INTO relationship_review_retries
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        request["revision_key"],
                        relationship_id,
                        request["prior_relationship_version"],
                        request_hash,
                        _json(result),
                        decision["decision_id"],
                        created_at,
                    ),
                )
                connection.commit()
                return {"outcome": "created", "result": result}
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _current_engagement(connection: sqlite3.Connection) -> dict[str, object]:
        row = connection.execute(
            """SELECT setup.engagement_id, setup.state, setup.is_fictional,
                      setup.data_classification
               FROM current_engagement AS current
               JOIN engagement_setups AS setup
                 ON setup.engagement_id = current.engagement_id
               WHERE current.current_slot = 1"""
        ).fetchone()
        if row is None or row["state"] != "READY_FOR_CAPTURE":
            return {"outcome": "engagement_required"}
        if row["is_fictional"] != 1 or row["data_classification"] != "FICTIONAL":
            return {"outcome": "g0"}
        return {"outcome": "ready", "engagement_id": row["engagement_id"]}

    @staticmethod
    def _insert_event(
        connection: sqlite3.Connection,
        relationship_id: str,
        version: int,
        decision_id: str,
        actor: str,
        recorded_at: str,
    ) -> None:
        connection.execute(
            """INSERT INTO relationship_review_events VALUES (
                   ?, ?, ?, ?, 'RELATIONSHIP_DECISION_RECORDED', ?, ?
               )""",
            (
                f"REVT-{uuid.uuid4().hex[:16].upper()}",
                relationship_id,
                version,
                decision_id,
                recorded_at,
                actor,
            ),
        )

    def _state(
        self,
        connection: sqlite3.Connection,
        relationship_id: str,
        engagement_id: str,
    ) -> dict[str, object]:
        item = connection.execute(
            """SELECT item.*, draft.current_version, draft.proposed_decision,
                      draft.draft_reason, draft.updated_at, draft.updated_by
               FROM relationship_review_items AS item
               JOIN relationship_review_drafts AS draft USING (relationship_id)
               WHERE item.relationship_id = ? AND item.engagement_id = ?""",
            (relationship_id, engagement_id),
        ).fetchone()
        if item is None:
            raise KeyError(relationship_id)
        current_version = connection.execute(
            """SELECT snapshot_json FROM relationship_review_versions
               WHERE relationship_id = ? AND relationship_version = ?""",
            (relationship_id, item["current_version"]),
        ).fetchone()
        if current_version is None:
            raise RuntimeError("Current Relationship proposal version is missing")
        current_snapshot = _loads(current_version["snapshot_json"])
        versions = connection.execute(
            """SELECT relationship_version, snapshot_json, created_at, created_by
               FROM relationship_review_versions
               WHERE relationship_id = ? ORDER BY relationship_version""",
            (relationship_id,),
        ).fetchall()
        decisions = connection.execute(
            """SELECT decision_id, relationship_version, decision_status,
                      reason, decided_at, decided_by
               FROM relationship_review_decisions
               WHERE relationship_id = ? ORDER BY decided_at""",
            (relationship_id,),
        ).fetchall()
        review_draft = {
            "relationship_version": item["current_version"],
            "proposed_decision": item["proposed_decision"],
            "draft_reason": item["draft_reason"],
            "updated_at": item["updated_at"],
            "updated_by": item["updated_by"],
        }
        return {
            "relationship_id": item["relationship_id"],
            "engagement_id": item["engagement_id"],
            "title": item["title"],
            "relationship_type": item["relationship_type"],
            "source_record_id": item["source_record_id"],
            "target_record_id": item["target_record_id"],
            "current_version": item["current_version"],
            "rationale": current_snapshot["rationale"],
            "source_support": current_snapshot["supporting_source_ids"],
            "gaps": current_snapshot["gaps"],
            "contradictions": current_snapshot["contradictions"],
            "duplicate_warnings": current_snapshot["duplicate_warnings"],
            "review_draft": review_draft,
            "version_history": [
                {
                    "version": row["relationship_version"],
                    **_loads(row["snapshot_json"]),
                    "created_at": row["created_at"],
                    "created_by": row["created_by"],
                }
                for row in versions
            ],
            "decisions": [dict(row) for row in decisions],
            "proposal_snapshot_json": current_version["snapshot_json"],
        }

    @staticmethod
    def _preview_token(state: dict[str, object], approval_reason: str) -> str:
        content = {
            "engagement_id": state["engagement_id"],
            "relationship": {
                "relationship_id": state["relationship_id"],
                "relationship_type": state["relationship_type"],
                "source_record_id": state["source_record_id"],
                "target_record_id": state["target_record_id"],
                "title": state["title"],
            },
            "relationship_version": state["current_version"],
            "proposal_snapshot": _loads(str(state["proposal_snapshot_json"])),
            "approval_reason": approval_reason.strip(),
        }
        return sha256(_json(content).encode("utf-8")).hexdigest()

    @staticmethod
    def _approved_snapshot(state: dict[str, object]) -> str:
        return _json(
            {
                "identity": {
                    "engagement_id": state["engagement_id"],
                    "relationship_id": state["relationship_id"],
                    "relationship_type": state["relationship_type"],
                    "source_record_id": state["source_record_id"],
                    "target_record_id": state["target_record_id"],
                    "title": state["title"],
                },
                "relationship_version": state["current_version"],
                "proposal": _loads(str(state["proposal_snapshot_json"])),
            }
        )

    @staticmethod
    def _create_next_version(
        connection: sqlite3.Connection,
        relationship_id: str,
        state: dict[str, object],
        revision_request: str,
        actor: str,
        created_at: str,
    ) -> None:
        next_version = int(state["current_version"]) + 1
        snapshot = _loads(str(state["proposal_snapshot_json"]))
        snapshot["relationship_version"] = next_version
        snapshot["revision_request"] = revision_request
        connection.execute(
            "INSERT INTO relationship_review_versions VALUES (?, ?, ?, ?, ?)",
            (relationship_id, next_version, _json(snapshot), created_at, actor),
        )
        connection.execute(
            """UPDATE relationship_review_drafts
               SET current_version = ?, proposed_decision = NULL,
                   draft_reason = NULL, updated_at = ?, updated_by = ?
               WHERE relationship_id = ?""",
            (next_version, created_at, actor, relationship_id),
        )

    @staticmethod
    def _all_current_versions_approved(
        connection: sqlite3.Connection, engagement_id: str
    ) -> bool:
        rows = connection.execute(
            """SELECT item.relationship_type, decision.decision_status
               FROM relationship_review_items AS item
               JOIN relationship_review_drafts AS draft USING (relationship_id)
               LEFT JOIN relationship_review_decisions AS decision
                 ON decision.relationship_id = item.relationship_id
                AND decision.relationship_version = draft.current_version
               WHERE item.engagement_id = ?""",
            (engagement_id,),
        ).fetchall()
        return (
            len(rows) == len(REQUIRED_RELATIONSHIP_TYPES)
            and {row["relationship_type"] for row in rows}
            == REQUIRED_RELATIONSHIP_TYPES
            and all(row["decision_status"] == "APPROVED" for row in rows)
        )

    def _build_trace(
        self,
        connection: sqlite3.Connection,
        engagement_id: str,
        trace_inputs: RelationshipTraceInputs,
    ):
        rows = connection.execute(
            """SELECT item.relationship_id
               FROM relationship_review_items AS item
               WHERE item.engagement_id = ?
               ORDER BY item.relationship_type""",
            (engagement_id,),
        ).fetchall()
        states = [
            self._state(connection, row["relationship_id"], engagement_id)
            for row in rows
        ]
        relationships = tuple(
            ProposedTraceRelationship(
                relationship_id=str(state["relationship_id"]),
                relationship_version=int(state["current_version"]),
                relationship_type=TraceRelationshipType(str(state["relationship_type"])),
                source_record_id=str(state["source_record_id"]),
                target_record_id=str(state["target_record_id"]),
                supporting_source_ids=tuple(state["source_support"]),
                rationale=str(state["rationale"]),
            )
            for state in states
        )
        decisions = []
        for state in states:
            row = connection.execute(
                """SELECT * FROM relationship_review_decisions
                   WHERE relationship_id = ? AND relationship_version = ?""",
                (state["relationship_id"], state["current_version"]),
            ).fetchone()
            if row is None:
                raise RuntimeError("Approved Relationship decision is missing")
            decisions.append(
                AuditorRelationshipDecision(
                    decision_id=row["decision_id"],
                    relationship_id=str(state["relationship_id"]),
                    relationship_version=int(state["current_version"]),
                    relationship_type=TraceRelationshipType(
                        str(state["relationship_type"])
                    ),
                    decision_status=AuditorDecisionStatus(row["decision_status"]),
                    reviewer_id=row["decided_by"],
                    review_notes=row["reason"],
                    reviewed_at=row["decided_at"],
                )
            )
        return build_accepted_planning_trace(
            obligation=trace_inputs.obligation,
            risk=trace_inputs.risk,
            control=trace_inputs.control,
            accountable_role=trace_inputs.accountable_role,
            relationships=relationships,
            decisions=tuple(decisions),
            mate_assessment=trace_inputs.mate_assessment,
        )
