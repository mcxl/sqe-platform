"""Pure projection of a selected client release into the existing response model."""

from __future__ import annotations

import datetime
from collections.abc import Mapping, Sequence

from src.ace.domain.release import (
    ClientActionEntry,
    ClientConclusionEntry,
    ClientReleaseResponse,
)


class ClientReleaseProjection:
    """Project caller-supplied release snapshots without persistence access."""

    def project(
        self,
        package: Mapping[str, object] | None,
        entries: Sequence[Mapping[str, object]],
        engagement: Mapping[str, object] | None,
    ) -> ClientReleaseResponse:
        """Return the established client response for selected release data."""
        if package is None:
            return ClientReleaseResponse(
                engagement_name="Release unavailable",
                review_status="",
                release_version=0,
                published_at="",
                conclusion=None,
                actions=[],
            )
        if engagement is None:
            return ClientReleaseResponse(
                engagement_name="Engagement not found",
                review_status="",
                release_version=0,
                published_at="",
                conclusion=None,
                actions=[],
            )

        conclusion = None
        actions: list[ClientActionEntry] = []
        for entry in entries:
            if entry["source_record_type"] == "CONCLUSION":
                conclusion = ClientConclusionEntry(
                    title=entry["display_title"],
                    summary=entry["display_summary"],
                    evidence_reference_id=entry["approved_evidence_reference_id"],
                )
            elif entry["source_record_type"] == "ACTION":
                owner = entry.get("action_owner", "") or ""
                target_date = entry.get("action_target_date", "") or ""
                delivery = entry.get("action_delivery_status", "") or ""
                if not owner or not target_date:
                    continue
                if delivery not in ("OPEN", "COMPLETE"):
                    continue
                try:
                    parsed = datetime.date.fromisoformat(target_date)
                except ValueError:
                    continue
                if parsed.isoformat() != target_date:
                    continue
                actions.append(
                    ClientActionEntry(
                        description=entry["display_summary"],
                        owner=owner,
                        target_date=target_date,
                        status=delivery,
                    )
                )

        return ClientReleaseResponse(
            engagement_name=engagement["title"],
            review_status=engagement["state"],
            release_version=package["release_version"],
            published_at=package["published_at"] or "",
            conclusion=conclusion,
            actions=actions,
        )
