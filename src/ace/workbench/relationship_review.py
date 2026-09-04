"""Controlled Relationship Review actions for fictional planning records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from src.ace.domain.assessment import ApprovedMATEAssessment
from src.ace.domain.trace import (
    AccountableRoleRecord,
    BindingObligationRecord,
    PlanningControlRecord,
    RiskRecord,
)
from src.ace.workbench.action_result import ActionResult, ActionResultState
from src.ace.workbench.relationship_review_storage import (
    DECISION_KEY_PATTERN,
    DECISIONS,
    PREVIEW_TOKEN_PATTERN,
    RelationshipReviewStorage,
)


class RelationshipReviewActorKind(str, Enum):
    """The two actor kinds for this bounded review path."""

    AGENT = "AGENT"
    ACCOUNTABLE_AUDITOR = "ACCOUNTABLE_AUDITOR"


@dataclass(frozen=True)
class RelationshipReviewActor:
    """One identified actor in the Relationship Review boundary."""

    kind: RelationshipReviewActorKind
    actor_id: str


@dataclass(frozen=True)
class RelationshipTraceInputs:
    """Existing domain inputs supplied to the accepted trace engine."""

    obligation: BindingObligationRecord
    risk: RiskRecord
    control: PlanningControlRecord
    accountable_role: AccountableRoleRecord
    mate_assessment: ApprovedMATEAssessment


class RelationshipReviewService:
    """Apply actor controls while SQLite owns final transactions."""

    def __init__(
        self,
        workbench_store: object,
        trace_input_provider: Callable[[], RelationshipTraceInputs | None]
        | None = None,
    ) -> None:
        self._storage = RelationshipReviewStorage(workbench_store)
        self._trace_input_provider = trace_input_provider

    def get_queue(self, actor: RelationshipReviewActor) -> dict[str, object]:
        stored = self._storage.queue()
        blocked = self._blocked_access(stored)
        if blocked is not None:
            return blocked
        return self._response(
            ActionResult(
                ActionResultState.NEEDS_REVIEW,
                "RELATIONSHIP_QUEUE_READY",
                "Relationship Review queue is ready.",
                self._permitted_actions(actor, "read_item"),
            ),
            engagement_id=stored["engagement_id"],
            queue=stored["queue"],
        )

    def get_item(
        self, relationship_id: str, actor: RelationshipReviewActor
    ) -> dict[str, object]:
        stored = self._storage.state(relationship_id)
        blocked = self._blocked_access(stored)
        if blocked is not None:
            return blocked
        return self._response(
            ActionResult(
                ActionResultState.NEEDS_REVIEW,
                "RELATIONSHIP_REVIEW_READY",
                "Relationship Review item is ready.",
                self._permitted_actions(
                    actor, "save_draft", "request_approval_preview"
                ),
            ),
            state=self._public_state(stored["state"]),
        )

    def save_draft(
        self,
        relationship_id: str,
        draft: dict[str, object],
        actor: RelationshipReviewActor,
    ) -> dict[str, object]:
        normalised = self._normalise_draft(draft)
        stored = self._storage.save_draft(
            relationship_id, normalised, actor.actor_id
        )
        blocked = self._blocked_access(stored)
        if blocked is not None:
            return blocked
        if stored["outcome"] == "version_stale":
            return self._response(self._version_stale())
        return self._response(
            ActionResult(
                ActionResultState.OK,
                "RELATIONSHIP_DRAFT_SAVED",
                "Relationship Review draft is saved.",
                self._permitted_actions(actor, "request_approval_preview"),
            ),
            state=self._public_state(stored["state"]),
        )

    def request_approval_preview(
        self,
        relationship_id: str,
        request: dict[str, object],
        actor: RelationshipReviewActor,
    ) -> dict[str, object]:
        normalised = self._normalise_preview(request)
        stored = self._storage.preview(relationship_id, normalised)
        blocked = self._blocked_access(stored)
        if blocked is not None:
            return blocked
        if stored["outcome"] == "version_stale":
            return self._response(self._version_stale())
        return self._response(
            ActionResult(
                ActionResultState.NEEDS_APPROVAL,
                "RELATIONSHIP_APPROVAL_PREVIEW_READY",
                "Approval preview is ready.",
                self._permitted_actions(
                    actor, "save_draft", "request_approval_preview"
                ),
            ),
            state=self._public_state(stored["state"]),
            approval_reason=normalised["approval_reason"],
            preview_token=stored["preview_token"],
        )

    def record_decision(
        self,
        relationship_id: str,
        request: dict[str, object],
        actor: RelationshipReviewActor,
    ) -> dict[str, object]:
        if actor.kind is not RelationshipReviewActorKind.ACCOUNTABLE_AUDITOR:
            return self._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "ACCOUNTABLE_AUDITOR_REQUIRED",
                    "The Accountable Auditor must record a final decision.",
                    ("save_draft", "request_approval_preview"),
                )
            )
        normalised = self._normalise_decision(request)
        trace_inputs = self._storage.prepare_trace_inputs(
            relationship_id, normalised, self._trace_input_provider
        )
        stored = self._storage.finalise(
            relationship_id,
            normalised,
            actor.actor_id,
            lambda: trace_inputs,
        )
        blocked = self._blocked_access(stored)
        if blocked is not None:
            return blocked
        outcome = stored["outcome"]
        if outcome == "retry":
            return self._recorded_response(stored["result"])
        if outcome == "key_conflict":
            return self._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "RELATIONSHIP_DECISION_KEY_CONFLICT",
                    "Decision key conflicts with a different request.",
                    (),
                )
            )
        if outcome == "already_recorded":
            return self._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "RELATIONSHIP_DECISION_ALREADY_RECORDED",
                    "A decision already exists for this Relationship version.",
                    ("read_item",),
                )
            )
        if outcome == "version_stale":
            return self._response(self._version_stale())
        if outcome == "preview_stale":
            return self._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "RELATIONSHIP_PREVIEW_STALE",
                    "Approval preview is stale. Request a current preview.",
                    ("request_approval_preview",),
                )
            )
        if outcome == "mate_required":
            return self._response(
                ActionResult(
                    ActionResultState.NEEDS_EVIDENCE,
                    "RELATIONSHIP_MATE_REQUIRED",
                    "Approved MATE assessment is required for the accepted planning trace.",
                    (),
                )
            )
        return self._recorded_response(stored["result"])

    def create_revision(
        self,
        relationship_id: str,
        request: dict[str, object],
        actor: RelationshipReviewActor,
    ) -> dict[str, object]:
        """Create one corrected immutable proposal after CHANGES_REQUIRED."""
        if actor.kind is not RelationshipReviewActorKind.ACCOUNTABLE_AUDITOR:
            return self._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "ACCOUNTABLE_AUDITOR_REQUIRED",
                    "The Accountable Auditor must create a Relationship revision.",
                    (),
                )
            )
        stored = self._storage.create_revision(
            relationship_id, self._normalise_revision(request), actor.actor_id
        )
        blocked = self._blocked_access(stored)
        if blocked is not None:
            return blocked
        outcome = stored["outcome"]
        if outcome == "retry":
            return self._revision_response(stored["result"])
        if outcome == "key_conflict":
            return self._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "RELATIONSHIP_REVISION_KEY_CONFLICT",
                    "Revision key conflicts with a different request.",
                    (),
                )
            )
        if outcome == "version_stale":
            return self._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "RELATIONSHIP_REVISION_STALE",
                    "Relationship version is stale. Read the current item.",
                    ("read_item",),
                )
            )
        if outcome == "not_allowed":
            return self._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "RELATIONSHIP_REVISION_NOT_ALLOWED",
                    "A current CHANGES_REQUIRED decision is required for a revision.",
                    ("read_item",),
                )
            )
        if outcome == "source_boundary_invalid":
            return self._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "RELATIONSHIP_REVISION_SOURCE_BOUNDARY_INVALID",
                    "Revision sources must be unique and belong to the original proposal.",
                    ("read_item",),
                )
            )
        return self._revision_response(stored["result"])

    def _recorded_response(self, result: dict[str, object]) -> dict[str, object]:
        clean_result = dict(result)
        if "state" in clean_result:
            clean_result["state"] = self._public_state(clean_result["state"])
        if result.get("mate_required"):
            action = ActionResult(
                ActionResultState.NEEDS_EVIDENCE,
                "RELATIONSHIP_MATE_REQUIRED",
                "Approved MATE assessment is required for the accepted planning trace.",
                (),
            )
        else:
            action = ActionResult(
                ActionResultState.OK,
                "RELATIONSHIP_DECISION_RECORDED",
                "Relationship decision is recorded.",
                ("read_item",),
            )
        return self._response(action, **clean_result)

    def _revision_response(self, result: dict[str, object]) -> dict[str, object]:
        clean_result = dict(result)
        clean_result["state"] = self._public_state(clean_result["state"])
        return self._response(
            ActionResult(
                ActionResultState.OK,
                "RELATIONSHIP_REVISION_CREATED",
                "Relationship revision is created.",
                ("read_item",),
            ),
            **clean_result,
        )

    @staticmethod
    def _normalise_draft(draft: dict[str, object]) -> dict[str, object]:
        allowed = {"relationship_version", "proposed_decision", "draft_reason"}
        if set(draft) - allowed:
            raise ValueError("Review draft contains unsupported fields")
        version = RelationshipReviewService._positive_version(
            draft.get("relationship_version")
        )
        proposed_decision = draft.get("proposed_decision")
        if proposed_decision is not None and proposed_decision not in DECISIONS:
            raise ValueError("Proposed decision is invalid")
        reason = RelationshipReviewService._optional_text(
            draft.get("draft_reason"), "Draft reason"
        )
        return {
            "relationship_version": version,
            "proposed_decision": proposed_decision,
            "draft_reason": reason,
        }

    @staticmethod
    def _normalise_preview(request: dict[str, object]) -> dict[str, object]:
        if set(request) != {"relationship_version", "approval_reason"}:
            raise ValueError("Approval preview request is invalid")
        return {
            "relationship_version": RelationshipReviewService._positive_version(
                request.get("relationship_version")
            ),
            "approval_reason": RelationshipReviewService._required_text(
                request.get("approval_reason"), "Approval reason"
            ),
        }

    @staticmethod
    def _normalise_decision(request: dict[str, object]) -> dict[str, object]:
        allowed = {
            "relationship_version",
            "decision",
            "reason",
            "decision_key",
            "preview_token",
        }
        required = {
            "relationship_version",
            "decision",
            "reason",
            "decision_key",
        }
        if set(request) - allowed or not required.issubset(request):
            raise ValueError("Decision request is invalid")
        decision = request.get("decision")
        if decision not in DECISIONS:
            raise ValueError("Decision is invalid")
        decision_key = request.get("decision_key")
        if not isinstance(decision_key, str) or DECISION_KEY_PATTERN.fullmatch(
            decision_key
        ) is None:
            raise ValueError("Decision key is invalid")
        token = request.get("preview_token")
        if token is not None and (
            not isinstance(token, str)
            or PREVIEW_TOKEN_PATTERN.fullmatch(token) is None
        ):
            raise ValueError("Preview token is invalid")
        if decision == "APPROVED" and token is None:
            raise ValueError("APPROVED requires a preview token")
        return {
            "relationship_version": RelationshipReviewService._positive_version(
                request.get("relationship_version")
            ),
            "decision": decision,
            "reason": RelationshipReviewService._required_text(
                request.get("reason"), "Decision reason"
            ),
            "decision_key": decision_key,
            "preview_token": token,
        }

    @staticmethod
    def _normalise_revision(request: dict[str, object]) -> dict[str, object]:
        required = {
            "prior_relationship_version",
            "revision_key",
            "rationale",
            "supporting_source_ids",
            "gaps",
            "contradictions",
            "duplicate_warnings",
        }
        if set(request) != required:
            raise ValueError("Revision request is invalid")
        revision_key = request.get("revision_key")
        if not isinstance(revision_key, str) or DECISION_KEY_PATTERN.fullmatch(revision_key) is None:
            raise ValueError("Revision key is invalid")
        return {
            "prior_relationship_version": RelationshipReviewService._positive_version(
                request.get("prior_relationship_version")
            ),
            "revision_key": revision_key,
            "rationale": RelationshipReviewService._required_text(
                request.get("rationale"), "Revision rationale"
            ),
            "supporting_source_ids": RelationshipReviewService._string_list(
                request.get("supporting_source_ids"), "Supporting source identifiers", True
            ),
            "gaps": RelationshipReviewService._string_list(request.get("gaps"), "Gaps", False),
            "contradictions": RelationshipReviewService._string_list(
                request.get("contradictions"), "Contradictions", False
            ),
            "duplicate_warnings": RelationshipReviewService._string_list(
                request.get("duplicate_warnings"), "Duplicate warnings", False
            ),
        }

    @staticmethod
    def _positive_version(value: object) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("Relationship version is invalid")
        return value

    @staticmethod
    def _required_text(value: object, label: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{label} is invalid")
        stripped = value.strip()
        if not stripped or len(stripped) > 4000:
            raise ValueError(f"{label} is invalid")
        return stripped

    @staticmethod
    def _optional_text(value: object, label: str) -> str | None:
        if value is None:
            return None
        return RelationshipReviewService._required_text(value, label)

    @staticmethod
    def _string_list(value: object, label: str, required: bool) -> list[str]:
        if not isinstance(value, list) or len(value) > 100 or (required and not value):
            raise ValueError(f"{label} is invalid")
        return [RelationshipReviewService._required_text(item, label) for item in value]

    @staticmethod
    def _blocked_access(stored: dict[str, object]) -> dict[str, object] | None:
        if stored["outcome"] == "g0":
            return RelationshipReviewService._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "G0_REAL_CLIENT_BLOCKED",
                    "G0 blocks real-client Relationship Review data.",
                    (),
                )
            )
        if stored["outcome"] == "engagement_required":
            return RelationshipReviewService._response(
                ActionResult(
                    ActionResultState.BLOCKED,
                    "RELATIONSHIP_ENGAGEMENT_REQUIRED",
                    "A current READY_FOR_CAPTURE Engagement is required.",
                    (),
                )
            )
        return None

    @staticmethod
    def _version_stale() -> ActionResult:
        return ActionResult(
            ActionResultState.BLOCKED,
            "RELATIONSHIP_VERSION_STALE",
            "Relationship version is stale. Read the current item.",
            ("read_item",),
        )

    @staticmethod
    def _public_state(state: object) -> dict[str, object]:
        if not isinstance(state, dict):
            raise RuntimeError("Relationship Review state is invalid")
        return {
            key: value
            for key, value in state.items()
            if key != "proposal_snapshot_json"
        }

    @staticmethod
    def _permitted_actions(
        actor: RelationshipReviewActor, *agent_actions: str
    ) -> tuple[str, ...]:
        if actor.kind is RelationshipReviewActorKind.ACCOUNTABLE_AUDITOR:
            return (*agent_actions, "submit_decision")
        return agent_actions

    @staticmethod
    def _response(result: ActionResult, **values: object) -> dict[str, object]:
        return {"result": result.as_dict(), **values}
