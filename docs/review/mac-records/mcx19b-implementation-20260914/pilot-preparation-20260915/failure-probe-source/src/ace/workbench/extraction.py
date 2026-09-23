"""Deterministic regex-based evidence extraction adapter.

Produces FACT and WARNING suggestions with exact source character spans.
Same input always produces the same output. No external calls, no LLM.

Patterns can be customised at construction time or extended at runtime
via add_rule(). Use DEFAULT_RULES for the built-in set.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_Rule = tuple[re.Pattern[str], str]

# ---------------------------------------------------------------------------
# Built-in patterns — these ship with the adapter and can be replaced or
# extended per instance.
# ---------------------------------------------------------------------------
DEFAULT_RULES: list[_Rule] = [
    # --- Dates ---
    (
        re.compile(
            r"(?:\b(?:on|dated|completed\s+on|performed\s+on|conducted\s+on)\s+)"
            r"(\d{1,2}\s+(?:January|February|March|April|May|June|"
            r"July|August|September|October|November|December)\s+\d{4})",
            re.IGNORECASE,
        ),
        "FACT",
    ),
    (
        re.compile(
            r"(?:\b(?:on|dated|completed\s+on|performed\s+on|conducted\s+on)\s+)"
            r"(\d{1,2}\s+(?:January|February|March|April|May|June|"
            r"July|August|September|October|November|December))",
            re.IGNORECASE,
        ),
        "FACT",
    ),
    # --- Completions ---
    (
        re.compile(
            r"(?P<text>(?:inspection|audit|review|assessment|test|check|survey|"
            r"examination|walkthrough)\s+(?:was|has\s+been|is)\s+"
            r"(?:completed|finished|finalised|finalized|done|conducted|performed|carried\s+out))",
            re.IGNORECASE,
        ),
        "FACT",
    ),
    # --- Approvals ---
    (
        re.compile(
            r"(?P<text>(?:approved|authorised|authorized|signed\s+off)(?:\s+by\s+\w+(?:\s+\w+)?)?)",
            re.IGNORECASE,
        ),
        "FACT",
    ),
    # --- Responsibility ---
    (
        re.compile(
            r"(?P<text>(?:responsible\s+(?:person|officer|manager)|"
            r"accountable\s+(?:person|officer|manager)|"
            r"assigned\s+to)\s+\w+(?:\s+\w+)?)",
            re.IGNORECASE,
        ),
        "FACT",
    ),
    # --- Warnings: missing ---
    (
        re.compile(
            r"(?P<text>(?:no|without)\s+(?:quorum|record|minutes|sign-off|approval|"
            r"authorisation|authorization|certificate|attendance)\s+(?:was\s+)?"
            r"(?:recorded|present|obtained|provided|available|noted|documented)?)",
            re.IGNORECASE,
        ),
        "WARNING",
    ),
    # --- Warnings: not completed ---
    (
        re.compile(
            r"(?P<text>(?:inspection|audit|review|assessment|test|check)\s+"
            r"(?:was|has\s+been|is)\s+not\s+(?:completed|finished|finalised|finalized|done|"
            r"conducted|performed|carried\s+out))",
            re.IGNORECASE,
        ),
        "WARNING",
    ),
    # --- Warnings: overdue ---
    (
        re.compile(
            r"(?P<text>(?:overdue|past\s+due|behind\s+schedule|"
            r"not\s+yet\s+(?:completed|received|submitted|provided)))",
            re.IGNORECASE,
        ),
        "WARNING",
    ),
    # --- Warnings: requires ---
    (
        re.compile(
            r"(?P<text>(?:requires|needs)\s+(?:further|additional|follow-up|"
            r"review|inspection|approval|verification|clarification))",
            re.IGNORECASE,
        ),
        "WARNING",
    ),
    # --- Numbers / quantities ---
    (
        re.compile(
            r"(?P<text>\b\d+\s+(?:items|records|documents|findings|observations|"
            r"non-conformances|nonconformances|deficiencies|issues)\s+"
            r"(?:identified|found|noted|recorded|raised|reported))",
            re.IGNORECASE,
        ),
        "FACT",
    ),
    # --- References ---
    (
        re.compile(
            r"(?P<text>(?:reference|ref|document)\s+(?:number|no|#)?\s*"
            r"[A-Z]{2,6}[-–—]\d{2,6})",
            re.IGNORECASE,
        ),
        "FACT",
    ),
]


@dataclass(frozen=True)
class Suggestion:
    """One advisory extraction from a source text."""

    type: str  # "FACT" or "WARNING"
    text: str  # the exact extracted substring
    start: int  # character offset in source_text
    end: int  # character offset in source_text


class EvidenceExtractionAdapter:
    """Deterministic rule-based evidence text extraction.

    Usage:
        adapter = EvidenceExtractionAdapter()          # built-in patterns
        adapter = EvidenceExtractionAdapter(custom)    # replace all patterns
        adapter.add_rule(pattern, "FACT")              # extend at runtime
        suggestions = adapter.extract(source_text)
    """

    def __init__(self, rules: list[tuple[re.Pattern[str], str]] | None = None) -> None:
        """Create an adapter with an optional custom rule set.

        Args:
            rules: If provided, used instead of DEFAULT_RULES.
                   A shallow copy is made so callers can reuse the list safely.
        """
        self._rules: list[_Rule] = list(rules) if rules is not None else list(DEFAULT_RULES)

    def add_rule(self, pattern: re.Pattern[str], label: str) -> None:
        """Register an additional extraction rule at runtime.

        Args:
            pattern: A compiled regex.  Group 0 (the full match) is used as
                     the suggestion text.
            label:  ``"FACT"`` or ``"WARNING"``.
        """
        self._rules.append((pattern, label))

    def extract(self, source_text: str) -> list[Suggestion]:
        """Return advisory suggestions for the given source text.

        Args:
            source_text: The evidence source to analyse.

        Returns:
            A list of Suggestion objects. Empty list when source_text
            is empty or no patterns match.
        """
        if not source_text or not source_text.strip():
            return []

        suggestions: list[Suggestion] = []
        seen_spans: set[tuple[int, int]] = set()

        for pattern, suggestion_type in self._rules:
            for match in pattern.finditer(source_text):
                span = (match.start(), match.end())
                if span in seen_spans:
                    continue
                seen_spans.add(span)
                suggestions.append(
                    Suggestion(
                        type=suggestion_type,
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                    )
                )

        suggestions.sort(key=lambda s: s.start)
        return suggestions