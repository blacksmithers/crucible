"""Operation descriptions (port of ``guidance/format/operations-vocabulary.ts``)."""

from __future__ import annotations

from ...types.operations import OperationName

OPERATION_DESCRIPTIONS: dict[str, str] = {
    "set_metadata": "Update spec-level fields (goals, architecture, requirements, scope, ...)",
    "create_epic": "Create a new epic (minimal: title + description + objective)",
    "update_epic": "Update epic fields (architecture, scope, objective, ...)",
    "delete_epic": "Delete an epic and all its tickets",
    "create_ticket": "Create a new ticket (minimal: epicId + title)",
    "update_ticket": "Update ticket fields (acceptanceCriteria, implementationSteps, ...)",
    "delete_ticket": "Delete a ticket",
    "add_dependencies": "Declare ticket dependencies in batch (up to 5000 pairs)",
    "remove_dependency": "Remove a single dependency link",
    "create_blueprint": "Create a new blueprint (title, content, category, coverageType)",
    "update_blueprint": "Update blueprint fields (coverageType, content, ...)",
    "delete_blueprint": "Delete a blueprint",
    "link_blueprint": "Link a blueprint to a specific ticket",
    "unlink_blueprint": "Remove a blueprint link from a ticket",
    "get_ticket": "Read a ticket for exploration mid-session",
    "get_status": "Get a snapshot of spec/epic/ticket status",
    "gps": "Full X-ray of the specification",
}


def describe_operation(op: OperationName) -> str:
    return OPERATION_DESCRIPTIONS.get(op, op)
