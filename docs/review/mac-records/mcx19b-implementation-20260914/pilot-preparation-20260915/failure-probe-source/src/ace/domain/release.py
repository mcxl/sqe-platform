"""Phase 6A/6B1 — Client release domain models.

ConclusionRecord maps to the existing ``conclusions`` SQLite table.
ReleasePackage and ReleaseEntry are new tables for the client release boundary.
ActionRecord maps to the new ``approved_actions`` table.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

UTC = timezone.utc


# ── Conclusion ──────────────────────────────────────────────────

ConclusionType = Literal["CONCLUSION"]
ConclusionStatus = Literal["CANDIDATE", "APPROVED"]


class ConclusionRecord(BaseModel):
    """One approved or candidate conclusion.

    Maps to the ``conclusions`` table (extended with approval columns).
    """

    conclusion_id: str
    engagement_id: str
    mate_id: str
    evidence_id: str
    version: int = 1
    conclusion_type: ConclusionType = "CONCLUSION"
    summary: str
    status: ConclusionStatus
    approved_by: str | None = None
    approved_at: str | None = None
    created_at: str


# ── Action ──────────────────────────────────────────────────────

ApprovalStatus = Literal["CANDIDATE", "APPROVED"]
DeliveryStatus = Literal["OPEN", "COMPLETE"]


class ActionRecord(BaseModel):
    """One approved or candidate action.

    Maps to the ``approved_actions`` table.
    """

    action_id: str
    engagement_id: str
    version: int = 1
    description: str
    owner: str
    target_date: str
    approval_status: ApprovalStatus
    delivery_status: DeliveryStatus
    approved_by: str | None = None
    approved_at: str | None = None
    created_at: str


# ── Release package ─────────────────────────────────────────────

ReleasePackageStatus = Literal["DRAFT", "PUBLISHED", "WITHDRAWN"]


class ReleasePackage(BaseModel):
    """An immutable client release package.

    Maps to the ``client_release_packages`` table.
    """

    release_id: str
    engagement_id: str
    release_version: int
    status: ReleasePackageStatus
    created_at: str
    created_by: str
    published_at: str | None = None
    published_by: str | None = None
    withdrawn_at: str | None = None
    withdrawn_by: str | None = None
    withdrawal_reason: str | None = None


# ── Release entry ───────────────────────────────────────────────

SourceRecordType = Literal["CONCLUSION", "ACTION"]


class ReleaseEntry(BaseModel):
    """One published source record inside a release package.

    Maps to the ``client_release_entries`` table.
    """

    release_entry_id: str
    release_id: str
    source_record_type: SourceRecordType
    source_record_id: str
    source_record_version: int
    approved_evidence_reference_id: str
    display_title: str
    display_summary: str


# ── Client API response ─────────────────────────────────────────


class ClientReleaseResponse(BaseModel):
    """The current published release as seen by the client."""

    engagement_name: str
    review_status: str
    release_version: int
    published_at: str
    conclusion: "ClientConclusionEntry | None" = None
    actions: list["ClientActionEntry"] = Field(default_factory=list)


class ClientConclusionEntry(BaseModel):
    """A single released conclusion visible to the client."""

    title: str
    summary: str
    evidence_reference_id: str


class ClientActionEntry(BaseModel):
    """A single released action visible to the client.

    Only description, owner, target_date, and delivery_status are
    exposed.  Internal fields (approved_by, action_id, etc.) are
    intentionally excluded.
    """

    description: str
    owner: str
    target_date: str
    status: str
