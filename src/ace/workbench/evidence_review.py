"""Evidence Review rules for the fictional local workbench."""

from __future__ import annotations

from typing import Any

from src.ace.workbench.engagement import EngagementG0Error
from src.ace.workbench.storage import EvidenceReviewG0Error, WorkbenchStore


class EvidenceReviewError(Exception):
    """Base error for an Evidence Review action."""


class EvidenceReviewNotFoundError(EvidenceReviewError):
    """The requested safe Evidence Item does not exist."""


class EvidenceReviewValidationError(EvidenceReviewError):
    """The controlled review data is not valid."""


class EvidenceReviewConflictError(EvidenceReviewError):
    """The request conflicts with immutable review state."""


class EvidenceReviewService:
    """Apply Evidence Review rules while WorkbenchStore owns SQLite transactions."""

    def __init__(self, workbench_store: WorkbenchStore) -> None:
        self._store = workbench_store

    def get(self, evidence_id: str) -> dict[str, object]:
        return self._call(self._store.evidence_review_state, evidence_id)

    def save_context(
        self, evidence_id: str, context: dict[str, object], actor: str
    ) -> dict[str, object]:
        self._check_path_identifier(evidence_id, context.get("evidence_id"), "Evidence")
        return self._call(self._store.save_evidence_review_context, evidence_id, context, actor)

    def create_question(self, question: dict[str, object], actor: str) -> dict[str, object]:
        return self._call(self._store.create_audit_question, question, actor)

    def create_question_version(
        self, question_id: str, version: dict[str, object], actor: str
    ) -> dict[str, object]:
        self._check_path_identifier(question_id, version.get("question_id"), "question")
        return self._call(self._store.create_audit_question_version, question_id, version, actor)

    def decide_question(
        self, question_id: str, decision: dict[str, object], actor: str
    ) -> dict[str, object]:
        self._check_path_identifier(question_id, decision.get("question_id"), "question")
        return self._call(self._store.record_audit_question_decision, question_id, decision, actor)

    def propose_link(
        self, evidence_id: str, proposal: dict[str, object], actor: str
    ) -> dict[str, object]:
        self._check_path_identifier(evidence_id, proposal.get("evidence_id"), "Evidence")
        return self._call(self._store.create_proposed_link, evidence_id, proposal, actor)

    def complete(
        self, evidence_id: str, completion: dict[str, object], actor: str
    ) -> dict[str, object]:
        self._check_path_identifier(evidence_id, completion.get("evidence_id"), "Evidence")
        return self._call(
            self._store.complete_evidence_review,
            evidence_id,
            completion,
            actor,
        )

    def complete_legacy(self, evidence_id: str, notes: str, actor: str) -> dict[str, object]:
        return self._call(self._store.review, evidence_id, actor, notes)

    @staticmethod
    def _check_path_identifier(path_value: str, body_value: object, label: str) -> None:
        if body_value is not None and body_value != path_value:
            raise EvidenceReviewValidationError(f"{label} identifier does not match the path")

    @staticmethod
    def _call(method: Any, *args: object, **kwargs: object) -> dict[str, object]:
        try:
            result = method(*args, **kwargs)
        except (EngagementG0Error, EvidenceReviewG0Error):
            raise
        except KeyError as error:
            raise EvidenceReviewNotFoundError() from error
        except ValueError as error:
            raise EvidenceReviewValidationError(str(error)) from error
        except RuntimeError as error:
            raise EvidenceReviewConflictError(str(error)) from error
        if result is None:
            raise EvidenceReviewNotFoundError()
        return result
