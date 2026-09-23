"""Small shared action-result records for workbench responses."""

from dataclasses import asdict, dataclass
from enum import Enum
import re


STABLE_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
ACTION_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


class ActionResultState(str, Enum):
    """The controlled state of one workbench action."""

    OK = "OK"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ActionResult:
    """A JSON-safe result without workflow policy behaviour."""

    state: ActionResultState
    code: str
    message: str
    permitted_actions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.state, ActionResultState):
            raise ValueError("action result state is invalid")
        if not isinstance(self.permitted_actions, tuple):
            raise ValueError("permitted actions must use an immutable tuple")
        if not isinstance(self.code, str) or STABLE_CODE_PATTERN.fullmatch(self.code) is None:
            raise ValueError("action result code is blank or malformed")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("action result message cannot be blank")
        if any(
            not isinstance(action, str) or not action.strip()
            for action in self.permitted_actions
        ):
            raise ValueError("permitted action names cannot be empty")
        if any(
            ACTION_NAME_PATTERN.fullmatch(action) is None
            for action in self.permitted_actions
        ):
            raise ValueError("permitted action names are malformed")
        if len(self.permitted_actions) != len(set(self.permitted_actions)):
            raise ValueError("permitted action names must be unique")

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["state"] = self.state.value
        result["permitted_actions"] = list(self.permitted_actions)
        return result
