"""Operation descriptions."""

from __future__ import annotations

from ... import i18n
from ...types.operations import OperationName

_OPS: tuple[str, ...] = (
    "set_metadata",
    "create_epic",
    "update_epic",
    "delete_epic",
    "create_ticket",
    "update_ticket",
    "delete_ticket",
    "create_dependencies",
    "delete_dependencies",
    "create_blueprint",
    "update_blueprint",
    "delete_blueprint",
    "link_blueprint_to_tickets",
    "unlink_blueprint_to_tickets",
    "get_ticket",
    "get_status",
    "gps",
)

# English snapshot kept as a public mapping; the strings live in the i18n
# catalog under ``operations.<name>``.
OPERATION_DESCRIPTIONS: dict[str, str] = {
    op: i18n.text("en", f"operations.{op}") for op in _OPS
}


def describe_operation(op: OperationName, language: str = "en") -> str:
    if op in _OPS:
        return i18n.text(language, f"operations.{op}")
    return op
