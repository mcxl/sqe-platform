"""Failure-first tests for the pure client release projection adapter."""

from __future__ import annotations

import ast
from pathlib import Path

from src.ace.workbench import client_release_projection
from src.ace.workbench.client_release_projection import ClientReleaseProjection


_PACKAGE = {
    "release_version": 2,
    "published_at": "2026-08-19T10:00:00Z",
}
_ENGAGEMENT = {
    "title": "Fictional Mobile Field Capture Engagement",
    "state": "READY_FOR_CAPTURE",
}
_CONCLUSION = {
    "source_record_type": "CONCLUSION",
    "display_title": "Approved field capture conclusion",
    "display_summary": "Fictional conclusion summary.",
    "approved_evidence_reference_id": "EVD-FIC-0001",
}
_FORBIDDEN_PERSISTENCE_MODULES = (
    "aiosqlite",
    "sqlalchemy",
    "sqlite3",
    "src.ace.workbench",
)
_FORBIDDEN_OWNERSHIP_CALLS = {
    "__import__",
    "begin",
    "begin_release_write",
    "commit",
    "connect",
    "cursor",
    "execute",
    "open",
    "rollback",
    "savepoint",
    "transaction",
}


def _projection_boundary_violations(module: ast.AST) -> set[str]:
    """Return direct persistence dependencies or connection-ownership calls."""
    violations: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            modules = (name.name for name in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                violations.add("relative import")
            modules = (
                ()
                if node.module is None
                else (node.module, *(f"{node.module}.{name.name}" for name in node.names))
            )
        else:
            modules = ()
        for imported in modules:
            if any(
                imported == forbidden or imported.startswith(f"{forbidden}.")
                for forbidden in _FORBIDDEN_PERSISTENCE_MODULES
            ):
                violations.add(f"persistence import: {imported}")

        if isinstance(node, ast.Call) and isinstance(
            node.func, (ast.Name, ast.Attribute)
        ):
            operation = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
            )
            if operation in _FORBIDDEN_OWNERSHIP_CALLS:
                violations.add(f"ownership call: {operation}")
    return violations


def _action(
    description: str,
    *,
    owner: str = "Fictional Owner",
    target_date: str = "2026-09-30",
    delivery_status: str = "OPEN",
) -> dict[str, object]:
    return {
        "source_record_type": "ACTION",
        "display_summary": description,
        "action_owner": owner,
        "action_target_date": target_date,
        "action_delivery_status": delivery_status,
    }


class TestClientReleaseProjection:
    def test_projects_current_release_exactly(self) -> None:
        response = ClientReleaseProjection().project(
            _PACKAGE, [_CONCLUSION, _action("Fictional action")], _ENGAGEMENT
        )

        assert response.model_dump() == {
            "engagement_name": "Fictional Mobile Field Capture Engagement",
            "review_status": "READY_FOR_CAPTURE",
            "release_version": 2,
            "published_at": "2026-08-19T10:00:00Z",
            "conclusion": {
                "title": "Approved field capture conclusion",
                "summary": "Fictional conclusion summary.",
                "evidence_reference_id": "EVD-FIC-0001",
            },
            "actions": [
                {
                    "description": "Fictional action",
                    "owner": "Fictional Owner",
                    "target_date": "2026-09-30",
                    "status": "OPEN",
                }
            ],
        }

    def test_returns_existing_unavailable_response_without_current_release(self) -> None:
        response = ClientReleaseProjection().project(None, [], None)

        assert response.model_dump() == {
            "engagement_name": "Release unavailable",
            "review_status": "",
            "release_version": 0,
            "published_at": "",
            "conclusion": None,
            "actions": [],
        }

    def test_returns_existing_missing_engagement_response(self) -> None:
        response = ClientReleaseProjection().project(_PACKAGE, [], None)

        assert response.model_dump() == {
            "engagement_name": "Engagement not found",
            "review_status": "",
            "release_version": 0,
            "published_at": "",
            "conclusion": None,
            "actions": [],
        }

    def test_filters_entries_and_preserves_supplied_order(self) -> None:
        response = ClientReleaseProjection().project(
            _PACKAGE,
            [
                _action("First valid action"),
                _action("Invalid delivery", delivery_status="PENDING"),
                _CONCLUSION,
                _action("Missing owner", owner=""),
                {"source_record_type": "UNKNOWN"},
                _action("Invalid date", target_date="2026-02-30"),
                _action("Second valid action", delivery_status="COMPLETE"),
            ],
            _ENGAGEMENT,
        )

        assert response.conclusion is not None
        assert response.conclusion.title == "Approved field capture conclusion"
        assert [action.description for action in response.actions] == [
            "First valid action",
            "Second valid action",
        ]

    def test_has_no_persistence_or_connection_ownership_dependencies(self) -> None:
        """The adapter has no persistence dependency or direct ownership call."""
        module = ast.parse(
            Path(client_release_projection.__file__).read_text(encoding="utf-8")
        )
        assert not _projection_boundary_violations(module)

        regression_module = ast.Module(
            body=[
                ast.ImportFrom(
                    module="release_storage",
                    names=[ast.alias(name="ClientReleaseStorage")],
                    level=1,
                ),
                ast.ImportFrom(
                    module="src.ace",
                    names=[ast.alias(name="workbench")],
                    level=0,
                ),
                ast.Expr(
                    ast.Call(
                        func=ast.Name(id="begin_release_write"), args=[], keywords=[]
                    )
                ),
                ast.Expr(
                    ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="connection"), attr="execute"
                        ),
                        args=[],
                        keywords=[],
                    )
                ),
            ],
            type_ignores=[],
        )
        assert _projection_boundary_violations(regression_module) == {
            "persistence import: src.ace.workbench",
            "relative import",
            "ownership call: begin_release_write",
            "ownership call: execute",
        }
