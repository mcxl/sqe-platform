"""Controlled Engagement setup service for the fictional ACE workbench."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Literal

from src.ace.workbench.storage import (
    DuplicateEngagementReferenceError,
    EngagementNotFoundError,
    EngagementStoreRecord,
    WorkbenchStore,
)


EngagementState = Literal["DRAFT", "READY_FOR_CAPTURE"]
DataClassification = Literal["FICTIONAL", "PUBLIC", "AUDITCO_OWNED", "REAL_CLIENT"]


class EngagementError(Exception):
    """Base error for controlled Engagement actions."""


class EngagementValidationError(EngagementError):
    """The Engagement is not ready for the requested action."""


class EngagementG0Error(EngagementError):
    """G0 blocks real-client or non-fictional Engagement work."""


class EngagementConflictError(EngagementError):
    """An Engagement action conflicts with controlled state."""


class EngagementNotFoundServiceError(EngagementError):
    """The requested Engagement does not exist."""


@dataclass(frozen=True)
class EngagementRecord:
    """The controlled Engagement state exposed by pages and the API."""

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
    data_classification: DataClassification | None
    is_fictional: bool | None
    state: EngagementState
    created_at: str
    activated_at: str | None
    current: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EngagementDraft:
    """Safe draft values accepted by the service."""

    creation_attempt_key: str
    title: str | None = None
    reference: str | None = None
    authority: str | None = None
    purpose: str | None = None
    scope: str | None = None
    exclusions: str | None = None
    review_start_date: str | None = None
    review_end_date: str | None = None
    evidence_cut_off_date: str | None = None
    accountable_auditor: str | None = None
    data_classification: DataClassification | None = None
    is_fictional: bool | None = None


class EngagementService:
    """Apply Engagement state rules while WorkbenchStore owns SQLite access."""

    def __init__(self, workbench_store: WorkbenchStore) -> None:
        self._store = workbench_store

    def create_draft(self, draft: EngagementDraft, actor: str) -> EngagementRecord:
        self._reject_real_client(draft.data_classification, draft.is_fictional)
        try:
            record = self._store.create_engagement_draft(draft, actor)
        except DuplicateEngagementReferenceError as error:
            raise EngagementConflictError("Engagement reference already exists") from error
        if record.state == "READY_FOR_CAPTURE":
            self._validate_current_g0(record)
        else:
            self._reject_real_client(record.data_classification, record.is_fictional)
        return self._record(record)

    def get(self, engagement_id: str) -> EngagementRecord:
        return self._record(self._safe_store_record(engagement_id))

    def activate(self, engagement_id: str, confirmed: bool, actor: str) -> EngagementRecord:
        if not confirmed:
            raise EngagementValidationError("Confirm the Engagement setup before activation")
        try:
            return self._record(
                self._store.activate_engagement(
                    engagement_id, actor, self._validate_activation
                )
            )
        except EngagementNotFoundError as error:
            raise EngagementNotFoundServiceError("Engagement does not exist") from error

    def select_current(self, engagement_id: str) -> EngagementRecord:
        try:
            return self._record(
                self._store.select_current_engagement(
                    engagement_id, self._validate_current_capture
                )
            )
        except EngagementNotFoundError as error:
            raise EngagementNotFoundServiceError("Engagement does not exist") from error

    def current(self) -> EngagementRecord | None:
        record = self._store.current_engagement()
        if record is None:
            return None
        self._validate_current_g0(record)
        if record.state != "READY_FOR_CAPTURE":
            return None
        return self._record(record)

    def capture(
        self,
        filename: str,
        media_type: str,
        content: bytes,
        actor: str,
        capture_attempt_key: str | None = None,
    ) -> dict[str, str]:
        """Capture evidence only for the locked, safe current Engagement."""
        return self._store.capture(
            filename,
            media_type,
            content,
            actor,
            self._validate_current_capture,
            capture_attempt_key,
        )

    @staticmethod
    def _reject_real_client(
        data_classification: DataClassification | None, is_fictional: bool | None
    ) -> None:
        if data_classification == "REAL_CLIENT" or is_fictional is False:
            raise EngagementG0Error("G0 blocks real-client Engagement setup")

    def _validate_activation(self, record: EngagementStoreRecord) -> None:
        if record.state not in {"DRAFT", "READY_FOR_CAPTURE"}:
            raise EngagementConflictError("Invalid Engagement state")
        if record.state == "READY_FOR_CAPTURE":
            self._validate_current_g0(record)
        else:
            self._reject_real_client(record.data_classification, record.is_fictional)
        required_values = {
            "title": record.title,
            "reference": record.reference,
            "authority": record.authority,
            "purpose": record.purpose,
            "scope": record.scope,
            "exclusions": record.exclusions,
            "review start date": record.review_start_date,
            "review end date": record.review_end_date,
            "evidence cut-off date": record.evidence_cut_off_date,
            "accountable auditor": record.accountable_auditor,
            "data classification": record.data_classification,
        }
        missing = [name for name, value in required_values.items() if not self._is_present(value)]
        if missing:
            raise EngagementValidationError("Complete all Engagement setup fields before activation")
        if record.is_fictional is None:
            raise EngagementValidationError("Confirm the fictional Engagement status before activation")
        if record.is_fictional is not True:
            raise EngagementG0Error("G0 blocks real-client Engagement setup")
        try:
            review_start = date.fromisoformat(record.review_start_date or "")
            review_end = date.fromisoformat(record.review_end_date or "")
            evidence_cut_off = date.fromisoformat(record.evidence_cut_off_date or "")
        except ValueError as error:
            raise EngagementValidationError("Use ISO review and evidence cut-off dates") from error
        if review_start > review_end:
            raise EngagementValidationError("The review end date must not precede the start date")
        if not review_start <= evidence_cut_off <= review_end:
            raise EngagementValidationError("The evidence cut-off date must be within the review period")

    def _validate_current_capture(self, record: EngagementStoreRecord) -> None:
        self._validate_current_g0(record)
        if record.state != "READY_FOR_CAPTURE":
            raise EngagementConflictError("Only READY_FOR_CAPTURE Engagements can be current")

    def _validate_current_g0(self, record: EngagementStoreRecord) -> None:
        self._reject_real_client(record.data_classification, record.is_fictional)
        if record.data_classification not in {"FICTIONAL", "PUBLIC", "AUDITCO_OWNED"}:
            raise EngagementG0Error("G0 blocks real-client Engagement setup")
        if record.is_fictional is not True:
            raise EngagementG0Error("G0 blocks real-client Engagement setup")

    @staticmethod
    def _is_present(value: object | None) -> bool:
        return isinstance(value, str) and bool(value.strip())

    @staticmethod
    def _record(record: EngagementStoreRecord) -> EngagementRecord:
        return EngagementRecord(**record.as_dict())

    def _safe_store_record(self, engagement_id: str) -> EngagementStoreRecord:
        try:
            record = self._store.get_engagement(engagement_id)
        except EngagementNotFoundError as error:
            raise EngagementNotFoundServiceError("Engagement does not exist") from error
        if record.state == "READY_FOR_CAPTURE":
            self._validate_current_g0(record)
        else:
            self._reject_real_client(record.data_classification, record.is_fictional)
        return record
