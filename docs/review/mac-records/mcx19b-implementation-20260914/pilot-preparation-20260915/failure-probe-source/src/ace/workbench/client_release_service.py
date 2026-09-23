"""Internal service boundary for client release lifecycle operations.

The caller owns the SQLite transaction and passes its active connection to
every operation.  This deliberately prevents a second connection from being
opened inside a release transaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import count
import sqlite3
from typing import Callable, TypeVar

from src.ace.domain.release import ReleasePackage
from src.ace.workbench.release_storage import ClientReleaseStorage


_SAVEPOINT_SEQUENCE = count()
_ASCII_WHITESPACE = " \t\n\v\f\r"
_OperationResult = TypeVar("_OperationResult")


class ClientReleaseNotFoundError(LookupError):
    """The requested client release package does not exist."""


class ClientReleaseStateError(ValueError):
    """The requested lifecycle operation is not valid for the package state."""


class ClientReleaseValidationError(ValueError):
    """A draft cannot be considered ready before SQLite publication checks."""


@dataclass(frozen=True)
class CurrentClientRelease:
    """The immutable package and entries selected for the client view."""

    package: dict[str, object]
    entries: list[dict[str, object]]


@dataclass(frozen=True)
class ClientReleaseHistoryRecord:
    """One stored package history row, including supported legacy identifiers."""

    release_id: str | None
    engagement_id: str
    release_version: int
    status: str
    created_at: str
    created_by: str
    published_at: str | None
    published_by: str | None
    withdrawn_at: str | None
    withdrawn_by: str | None
    withdrawal_reason: str | None

    @classmethod
    def from_row(cls, row: dict[str, object]) -> "ClientReleaseHistoryRecord":
        return cls(
            release_id=row["release_id"],
            engagement_id=row["engagement_id"],
            release_version=row["release_version"],
            status=row["status"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            published_at=row["published_at"],
            published_by=row["published_by"],
            withdrawn_at=row["withdrawn_at"],
            withdrawn_by=row["withdrawn_by"],
            withdrawal_reason=row["withdrawal_reason"],
        )


class ClientReleaseService:
    """Coordinate release lifecycle calls while SQLite remains authoritative."""

    def __init__(self, storage: ClientReleaseStorage | None = None) -> None:
        self._storage = storage or ClientReleaseStorage()

    def build_draft(
        self, connection: sqlite3.Connection, package: ReleasePackage
    ) -> ReleasePackage:
        if package.status != "DRAFT":
            raise ClientReleaseStateError("New release packages must be DRAFT")
        if any(
            value is not None
            for value in (
                package.published_at,
                package.published_by,
                package.withdrawn_at,
                package.withdrawn_by,
                package.withdrawal_reason,
            )
        ):
            raise ClientReleaseStateError(
                "DRAFT release packages cannot contain terminal metadata"
            )
        self._in_savepoint(
            connection,
            lambda: self._create_draft_with_audit_event(connection, package),
        )
        return self._require_package(connection, package.release_id)

    @staticmethod
    def begin_release_write(connection: sqlite3.Connection) -> None:
        """Start a fresh caller-owned immediate transaction for version allocation."""
        if connection.in_transaction:
            raise ClientReleaseStateError(
                "Release allocation must begin before an active caller transaction"
            )
        connection.execute("BEGIN IMMEDIATE")

    def build_next_draft(
        self,
        connection: sqlite3.Connection,
        release_id: str,
        engagement_id: str,
        created_at: str,
        created_by: str,
    ) -> ReleasePackage:
        """Build a DRAFT in the caller's immediate allocation transaction.

        Version selection includes DRAFT, PUBLISHED, WITHDRAWN, and supported
        legacy history rows. The caller must begin a fresh `BEGIN IMMEDIATE`
        transaction before any reads and retains transaction ownership.
        """
        package = self._in_savepoint(
            connection,
            lambda: self._build_next_draft(
                connection,
                release_id,
                engagement_id,
                created_at,
                created_by,
            ),
        )
        return self._require_package(connection, package.release_id)

    def validate_release(
        self, connection: sqlite3.Connection, release_id: str
    ) -> ReleasePackage:
        package = self._require_package(connection, release_id)
        if package.status != "DRAFT":
            raise ClientReleaseStateError("Only DRAFT releases can be published")
        if self._storage.entry_count(connection, release_id) == 0:
            raise ClientReleaseValidationError(
                "Release package must contain at least one valid entry"
            )
        # Source lineage, timestamps, audit history, versioning, and immutable
        # transition validation remain active in SQLite publication triggers.
        return package

    def publish_release(
        self,
        connection: sqlite3.Connection,
        release_id: str,
        published_at: str,
        published_by: str,
    ) -> ReleasePackage:
        self._in_savepoint(
            connection,
            lambda: self._publish_validated(
                connection, release_id, published_at, published_by
            ),
        )
        return self._require_package(connection, release_id)

    def withdraw_release(
        self,
        connection: sqlite3.Connection,
        release_id: str,
        withdrawn_at: str,
        withdrawn_by: str,
        withdrawal_reason: str | None = None,
    ) -> ReleasePackage:
        package = self._require_package(connection, release_id)
        if package.status != "PUBLISHED":
            raise ClientReleaseStateError("Only PUBLISHED releases can be withdrawn")
        if package.published_at is None:
            raise ClientReleaseStateError("PUBLISHED releases require a publication time")
        published_at = self._canonical_utc_timestamp(
            package.published_at, "Published time"
        )
        withdrawal_time = self._canonical_utc_timestamp(
            withdrawn_at, "Withdrawal time"
        )
        if withdrawal_time < published_at:
            raise ClientReleaseValidationError(
                "Withdrawal time must not be before publication time"
            )
        if (
            not isinstance(withdrawn_by, str)
            or not withdrawn_by
            or withdrawn_by.strip(_ASCII_WHITESPACE) != withdrawn_by
        ):
            raise ClientReleaseValidationError(
                "Withdrawal actor must be nonblank and trimmed"
            )
        self._in_savepoint(
            connection,
            lambda: self._withdraw_with_audit_event(
                connection,
                package,
                withdrawal_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                withdrawn_by,
                withdrawal_reason,
            ),
        )
        return self._require_package(connection, release_id)

    def get_current_release(
        self, connection: sqlite3.Connection, engagement_id: str
    ) -> CurrentClientRelease | None:
        current = self._storage.current_release(connection, engagement_id)
        if current is None:
            return None
        package, entries = current
        return CurrentClientRelease(package=package, entries=entries)

    def get_release_history(
        self, connection: sqlite3.Connection, engagement_id: str
    ) -> list[ClientReleaseHistoryRecord]:
        return [
            ClientReleaseHistoryRecord.from_row(package)
            for package in self._storage.release_history(connection, engagement_id)
        ]

    def get_engagement(
        self, connection: sqlite3.Connection, engagement_id: str
    ) -> dict[str, object] | None:
        """Read engagement metadata through the same connection as the release."""
        return self._storage.engagement(connection, engagement_id)

    def _require_package(
        self, connection: sqlite3.Connection, release_id: str
    ) -> ReleasePackage:
        package = self._storage.release_package(connection, release_id)
        if package is None:
            raise ClientReleaseNotFoundError(f"Client release not found: {release_id}")
        return ReleasePackage.model_validate(package)

    def _publish_validated(
        self,
        connection: sqlite3.Connection,
        release_id: str,
        published_at: str,
        published_by: str,
    ) -> None:
        self.validate_release(connection, release_id)
        self._storage.publish(connection, release_id, published_at, published_by)

    def _create_draft_with_audit_event(
        self, connection: sqlite3.Connection, package: ReleasePackage
    ) -> None:
        self._storage.insert_draft(connection, package)
        self._storage.insert_creation_audit_event(connection, package)

    def _build_next_draft(
        self,
        connection: sqlite3.Connection,
        release_id: str,
        engagement_id: str,
        created_at: str,
        created_by: str,
    ) -> ReleasePackage:
        if not self._storage.engagement_exists(connection, engagement_id):
            raise ClientReleaseValidationError(
                f"Release engagement not found: {engagement_id}"
            )
        package = ReleasePackage(
            release_id=release_id,
            engagement_id=engagement_id,
            release_version=self._storage.next_release_version(
                connection, engagement_id
            ),
            status="DRAFT",
            created_at=created_at,
            created_by=created_by,
        )
        self._create_draft_with_audit_event(connection, package)
        return package

    def _withdraw_with_audit_event(
        self,
        connection: sqlite3.Connection,
        package: ReleasePackage,
        withdrawn_at: str,
        withdrawn_by: str,
        withdrawal_reason: str | None,
    ) -> None:
        self._storage.withdraw(
            connection,
            package.release_id,
            withdrawn_at,
            withdrawn_by,
            withdrawal_reason,
        )
        self._storage.insert_withdrawal_audit_event(
            connection, package, withdrawn_at, withdrawn_by
        )

    @staticmethod
    def _canonical_utc_timestamp(value: object, label: str) -> datetime:
        if not isinstance(value, str):
            raise ClientReleaseValidationError(f"{label} must be canonical UTC")
        try:
            parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=UTC
            )
        except ValueError as error:
            raise ClientReleaseValidationError(
                f"{label} must be canonical UTC"
            ) from error
        if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
            raise ClientReleaseValidationError(f"{label} must be canonical UTC")
        return parsed

    @staticmethod
    def _in_savepoint(
        connection: sqlite3.Connection, operation: Callable[[], _OperationResult]
    ) -> _OperationResult:
        ClientReleaseService._require_active_transaction(connection)
        savepoint = f"client_release_service_{next(_SAVEPOINT_SEQUENCE)}"
        connection.execute(f"SAVEPOINT {savepoint}")
        try:
            result = operation()
        except BaseException:
            connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise
        connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        return result

    @staticmethod
    def _require_active_transaction(connection: sqlite3.Connection) -> None:
        if not connection.in_transaction:
            raise ClientReleaseStateError(
                "Release lifecycle operations require an active caller transaction"
            )
