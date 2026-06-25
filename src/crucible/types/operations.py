"""Planning operation names (port of ``types/operations.ts``)."""

from __future__ import annotations

from typing import Literal, TypeGuard, get_args

OperationName = Literal[
    "set_metadata",
    "create_epic",
    "update_epic",
    "delete_epic",
    "create_ticket",
    "update_ticket",
    "delete_ticket",
    "add_dependencies",
    "remove_dependency",
    "create_blueprint",
    "update_blueprint",
    "delete_blueprint",
    "link_blueprint",
    "unlink_blueprint",
    "get_ticket",
    "get_status",
    "gps",
]

OPERATION_NAMES: tuple[OperationName, ...] = get_args(OperationName)


def is_operation_name(value: str) -> TypeGuard[OperationName]:
    return value in OPERATION_NAMES
