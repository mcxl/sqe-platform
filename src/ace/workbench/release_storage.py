"""SQLite adapter for the internal client release service boundary."""

from __future__ import annotations

import sqlite3

from src.ace.domain.release import ReleasePackage


class ClientReleaseStorage:
    """Execute release persistence operations on a caller-owned connection."""

    @staticmethod
    def current_release(
        connection: sqlite3.Connection, engagement_id: str
    ) -> tuple[dict[str, object], list[dict[str, object]]] | None:
        package = connection.execute(
            """
            SELECT * FROM client_release_packages
            WHERE engagement_id = ? AND status = 'PUBLISHED'
            ORDER BY release_version DESC LIMIT 1
            """,
            (engagement_id,),
        ).fetchone()
        if package is None:
            return None
        entries = connection.execute(
            """
            SELECT * FROM client_release_entries
            WHERE release_id = ?
            ORDER BY release_entry_id
            """,
            (package["release_id"],),
        ).fetchall()
        return dict(package), [dict(entry) for entry in entries]

    @staticmethod
    def release_package(
        connection: sqlite3.Connection, release_id: str
    ) -> dict[str, object] | None:
        row = connection.execute(
            "SELECT * FROM client_release_packages WHERE release_id = ?",
            (release_id,),
        ).fetchone()
        return None if row is None else dict(row)

    @staticmethod
    def release_history(
        connection: sqlite3.Connection, engagement_id: str
    ) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in connection.execute(
                """
                SELECT * FROM client_release_packages
                WHERE engagement_id = ?
                ORDER BY release_version DESC
                """,
                (engagement_id,),
            ).fetchall()
        ]

    @staticmethod
    def engagement(
        connection: sqlite3.Connection, engagement_id: str
    ) -> dict[str, object] | None:
        """Return the metadata required to project one release safely."""
        row = connection.execute(
            "SELECT title, state, is_fictional, data_classification "
            "FROM engagement_setups WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchone()
        return None if row is None else dict(row)

    @staticmethod
    def next_release_version(
        connection: sqlite3.Connection, engagement_id: str
    ) -> int:
        """Read the next version after every stored package, including history."""
        return connection.execute(
            "SELECT COALESCE(MAX(release_version), 0) + 1 AS next_release_version "
            "FROM client_release_packages WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchone()["next_release_version"]

    @staticmethod
    def engagement_exists(
        connection: sqlite3.Connection, engagement_id: str
    ) -> bool:
        """Return whether the target engagement exists for release allocation."""
        return connection.execute(
            "SELECT 1 FROM engagement_setups WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchone() is not None

    @staticmethod
    def entry_count(connection: sqlite3.Connection, release_id: str) -> int:
        return connection.execute(
            "SELECT COUNT(*) AS count FROM client_release_entries WHERE release_id = ?",
            (release_id,),
        ).fetchone()["count"]

    @staticmethod
    def insert_draft(
        connection: sqlite3.Connection, package: ReleasePackage
    ) -> None:
        connection.execute(
            """
            INSERT INTO client_release_packages
            (release_id, engagement_id, release_version, status, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                package.release_id,
                package.engagement_id,
                package.release_version,
                package.status,
                package.created_at,
                package.created_by,
            ),
        )

    @staticmethod
    def insert_creation_audit_event(
        connection: sqlite3.Connection, package: ReleasePackage
    ) -> None:
        """Persist the immutable audit event for a newly created package."""
        connection.execute(
            """
            INSERT INTO engagement_audit_events
            (event_id, engagement_id, event_type, recorded_at, actor)
            VALUES (?, ?, 'RELEASE_CREATED', ?, ?)
            """,
            (
                f"EVT-{package.release_id}-CREATED",
                package.engagement_id,
                package.created_at,
                package.created_by,
            ),
        )

    @staticmethod
    def publish(
        connection: sqlite3.Connection,
        release_id: str,
        published_at: str,
        published_by: str,
    ) -> None:
        connection.execute(
            """
            UPDATE client_release_packages
            SET status = 'PUBLISHED', published_at = ?, published_by = ?
            WHERE release_id = ?
            """,
            (published_at, published_by, release_id),
        )

    @staticmethod
    def withdraw(
        connection: sqlite3.Connection,
        release_id: str,
        withdrawn_at: str,
        withdrawn_by: str,
        withdrawal_reason: str | None,
    ) -> None:
        connection.execute(
            """
            UPDATE client_release_packages
            SET status = 'WITHDRAWN', withdrawn_at = ?, withdrawn_by = ?,
                withdrawal_reason = ?
            WHERE release_id = ?
            """,
            (withdrawn_at, withdrawn_by, withdrawal_reason, release_id),
        )

    @staticmethod
    def insert_withdrawal_audit_event(
        connection: sqlite3.Connection,
        package: ReleasePackage,
        withdrawn_at: str,
        withdrawn_by: str,
    ) -> None:
        """Persist the immutable audit event after a package withdrawal."""
        connection.execute(
            """
            INSERT INTO engagement_audit_events
            (event_id, engagement_id, event_type, recorded_at, actor)
            VALUES (?, ?, 'RELEASE_WITHDRAWN', ?, ?)
            """,
            (
                f"EVT-{package.release_id}-WDN",
                package.engagement_id,
                withdrawn_at,
                withdrawn_by,
            ),
        )
