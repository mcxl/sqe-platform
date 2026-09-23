import pytest


def test_action_result_is_immutable_json_safe_and_rejects_bad_actions() -> None:
    from src.ace.workbench.action_result import ActionResult, ActionResultState

    result = ActionResult(
        state=ActionResultState.NEEDS_APPROVAL,
        code="RELATIONSHIP_APPROVAL_PREVIEW_READY",
        message="Approval preview is ready.",
        permitted_actions=("submit_decision", "save_draft"),
    )

    assert result.as_dict() == {
        "state": "NEEDS_APPROVAL",
        "code": "RELATIONSHIP_APPROVAL_PREVIEW_READY",
        "message": "Approval preview is ready.",
        "permitted_actions": ["submit_decision", "save_draft"],
    }
    with pytest.raises((AttributeError, TypeError)):
        result.code = "OTHER"  # type: ignore[misc]
    with pytest.raises(ValueError, match="empty"):
        ActionResult(ActionResultState.OK, "CODE", "Message.", ("",))
    with pytest.raises(ValueError, match="unique"):
        ActionResult(ActionResultState.OK, "CODE", "Message.", ("save", "save"))
    with pytest.raises(ValueError, match="tuple"):
        ActionResult(ActionResultState.OK, "CODE", "Message.", ["save"])  # type: ignore[arg-type]


def test_action_result_rejects_raw_string_state() -> None:
    from src.ace.workbench.action_result import ActionResult

    with pytest.raises(ValueError, match="state"):
        ActionResult("OK", "CODE", "Message.", ())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("code", "message", "actions"),
    [
        ("", "Message.", ()),
        ("bad-code", "Message.", ()),
        ("CODE", "   ", ()),
        ("CODE", "Message.", ("Bad Action",)),
        ("CODE", "Message.", ("bad-action",)),
    ],
)
def test_action_result_rejects_blank_or_malformed_fields(
    code: str, message: str, actions: tuple[str, ...]
) -> None:
    from src.ace.workbench.action_result import ActionResult, ActionResultState

    with pytest.raises(ValueError):
        ActionResult(ActionResultState.OK, code, message, actions)
