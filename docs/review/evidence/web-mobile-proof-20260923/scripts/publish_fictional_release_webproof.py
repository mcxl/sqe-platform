"""Disposable proof script: publish a new fictional release through ClientReleaseService.

Run from the repository root with the same ACE_DATA_DIR as the running app:

    uv run --no-sync python docs/review/evidence/web-mobile-proof-20260923/scripts/publish_fictional_release_webproof.py

Fictional data only (G0). Not a product file. Not imported by any test.
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.ace.workbench.client_release_service import ClientReleaseService
from src.ace.workbench.storage import WorkbenchStore

RELEASE_ID = "REL-FIC-WEBPROOF-20260923"
ENGAGEMENT_ID = "ENG-FIC-0001"
ACTOR = "fictional-auditor"


def main() -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    service = ClientReleaseService()
    store = WorkbenchStore()
    with store.connect() as conn:
        service.begin_release_write(conn)
        current = service.get_current_release(conn, ENGAGEMENT_ID)
        if current is None:
            raise SystemExit("No current published release to supersede")
        old_id = current.package["release_id"]
        print("current release", old_id, "v", current.package["release_version"])

        draft = service.build_next_draft(
            conn,
            release_id=RELEASE_ID,
            engagement_id=ENGAGEMENT_ID,
            created_at=now,
            created_by=ACTOR,
        )
        print("draft", draft.release_id, "v", draft.release_version)

        # Copy the approved source entries from the current package into the
        # new draft with new entry identifiers. Source lineage is unchanged.
        for index, entry in enumerate(current.entries, start=1):
            conn.execute(
                "INSERT INTO client_release_entries "
                "(release_entry_id, release_id, source_record_type, "
                " source_record_id, source_record_version, "
                " approved_evidence_reference_id, display_title, "
                " display_summary, action_owner, action_target_date, "
                " action_delivery_status) "
                "SELECT ?, ?, source_record_type, source_record_id, "
                " source_record_version, approved_evidence_reference_id, "
                " display_title, display_summary, action_owner, "
                " action_target_date, action_delivery_status "
                "FROM client_release_entries WHERE release_entry_id = ?",
                (f"RLE-FIC-WEBPROOF-{index}", RELEASE_ID, entry["release_entry_id"]),
            )

        service.withdraw_release(
            conn,
            old_id,
            withdrawn_at=now,
            withdrawn_by=ACTOR,
            withdrawal_reason="Superseded by web mobile proof release",
        )
        published = service.publish_release(
            conn, RELEASE_ID, published_at=now, published_by=ACTOR
        )
        conn.commit()
        print("published", published.release_id, "v", published.release_version, published.published_at)


if __name__ == "__main__":
    main()
