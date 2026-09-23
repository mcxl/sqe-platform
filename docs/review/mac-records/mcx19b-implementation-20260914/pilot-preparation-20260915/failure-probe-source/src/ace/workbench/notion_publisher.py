"""Fictional Notion publisher boundary for the ACE workbench.

This is a test double — no network calls, no real Notion API.
The boundary provides:
- publish(): Accepts an export and returns a stable publication ID.
- is_published(): Checks idempotency key — returns existing publication, never 409.
- simulate_failure(): For testing failure handling.

Publication IDs are deterministic SHA-256 hashes of the idempotency key.
Duplicate publication is prevented by checking the internal published-key set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class PublicationResult:
    """Result of a publication attempt."""

    publication_id: str
    idempotency_key: str
    published: bool  # True if new, False if already published (idempotent)
    error: str | None = None


class NotionPublisher:
    """Fictional Notion publisher — no network, no real API.

    The boundary is one-way: write-only. It never reads from Notion.
    """

    def __init__(self) -> None:
        self._published_keys: set[str] = set()
        self._publications: dict[str, PublicationResult] = {}
        self._failure_mode: bool = False

    # ── public API ──────────────────────────────────────────────

    def publish(
        self,
        idempotency_key: str,
        export_id: str,
        summary: dict[str, object] | None = None,
    ) -> PublicationResult:
        """Publish an export to fictional Notion.

        Idempotency — if the key has been published before, return the
        existing publication result (never 409).

        If _failure_mode is active, returns a failed result.
        """
        if self._failure_mode:
            return PublicationResult(
                publication_id="",
                idempotency_key=idempotency_key,
                published=False,
                error="Simulated Notion publication failure",
            )

        # Check-before-create: return existing publication on key collision
        existing = self._publications.get(idempotency_key)
        if existing is not None:
            return existing

        # Deterministic publication ID from idempotency key
        pub_id = f"NTN-{sha256(idempotency_key.encode()).hexdigest()[:16].upper()}"
        result = PublicationResult(
            publication_id=pub_id,
            idempotency_key=idempotency_key,
            published=True,
        )
        self._published_keys.add(idempotency_key)
        self._publications[idempotency_key] = result
        return result

    def is_published(self, idempotency_key: str) -> bool:
        """Check whether an idempotency key has already been published."""
        return idempotency_key in self._published_keys

    # ── test helpers ───────────────────────────────────────────

    def simulate_failure(self, active: bool = True) -> None:
        """Toggle failure mode for testing error handling."""
        self._failure_mode = active

    def reset(self) -> None:
        """Clear all published records (for test isolation)."""
        self._published_keys.clear()
        self._publications.clear()
        self._failure_mode = False
