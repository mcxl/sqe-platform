"""Change record model for ACE export authorities.

Immutable dataclass representing one detected change between snapshots.
Change IDs are deterministic SHA-256 hashes of the change tuple.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal


ChangeType = Literal["added", "removed", "modified"]


@dataclass(frozen=True)
class ChangeRecord:
    """One append-only change record detected between two snapshots."""

    change_id: str
    export_id: str
    record_id: str
    snapshot_id: str
    evidence_id: str | None
    idempotency_key: str
    timestamp: str
    change_type: ChangeType
    record_type: str
    label: str
    detail: str

    @classmethod
    def make(
        cls,
        export_id: str,
        record_id: str,
        snapshot_id: str,
        evidence_id: str | None,
        idempotency_key: str,
        change_type: ChangeType,
        record_type: str,
        label: str,
        detail: str = "",
    ) -> ChangeRecord:
        """Create a ChangeRecord with a deterministic change_id."""
        timestamp = (
            datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )
        # Time-based change_id from the unique change tuple + timestamp
        payload = (
            f"{export_id}|{record_id}|{snapshot_id}|{change_type}|{timestamp}"
        ).encode()
        change_id = f"CHG-{sha256(payload).hexdigest()[:12].upper()}"
        return cls(
            change_id=change_id,
            export_id=export_id,
            record_id=record_id,
            snapshot_id=snapshot_id,
            evidence_id=evidence_id,
            idempotency_key=idempotency_key,
            timestamp=timestamp,
            change_type=change_type,
            record_type=record_type,
            label=label,
            detail=detail,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "change_id": self.change_id,
            "export_id": self.export_id,
            "record_id": self.record_id,
            "snapshot_id": self.snapshot_id,
            "evidence_id": self.evidence_id,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp,
            "change_type": self.change_type,
            "record_type": self.record_type,
            "label": self.label,
            "detail": self.detail,
        }
