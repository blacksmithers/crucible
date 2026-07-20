"""Composite-pattern prose templates (port of ``guidance/format/templates/*``).

Strings are verbatim from the TS source.
"""

from __future__ import annotations

from typing import Any

from ...types.context import PhaseContext
from ...types.finding import CompositeFinding


def _leaf(field_path: str) -> str:
    return ".".join(field_path.split(".")[1:])


def _find_epic(spec: dict[str, Any], eid: str) -> dict[str, Any] | None:
    return next((e for e in (spec.get("epics") or []) if e["id"] == eid), None)


def _find_ticket(spec: dict[str, Any], tid: str) -> dict[str, Any] | None:
    return next(
        (t for e in (spec.get("epics") or []) for t in (e.get("tickets") or []) if t["id"] == tid),
        None,
    )


def format_foundation_gap(
    composite: CompositeFinding, _context: PhaseContext, spec: dict[str, Any]
) -> str:
    missing_fields = "\n".join(f"  - {_leaf(f.field_path)}" for f in composite.grouped_findings)

    if composite.entity_type == "specification":
        return (
            f'Specification "{spec.get("title")}" — planning_spec phase incomplete.\n\n'
            f"The following structural curriculum steps are not yet fulfilled:\n"
            f"{missing_fields}\n\n"
            "DECLARE these foundational fields together. They are interdependent: goals scope "
            "what architecture must achieve, architecture constrains what scope can promise, "
            "scope determines which requirements are in or out.\n\n"
            "Operation available: action_planning_session({\n"
            "  operation: { type: 'set_metadata', goals, architecture, requirements, scope, ... }\n"
            "})"
        )

    if composite.entity_type == "epic":
        epic = _find_epic(spec, composite.entity_id)
        epic_title = epic["title"] if epic else composite.entity_id
        return (
            f'Epic "{epic_title}" — epic_expansion phase has critical gaps:\n'
            f"{missing_fields}\n\n"
            "DECLARE these together via a single update.\n\n"
            "Operation available: action_planning_session({\n"
            f"  operation: {{ type: 'update_epic', epicId: \"{composite.entity_id}\", "
            "architecture, scope, objective, ... }\n"
            "})"
        )

    if composite.entity_type == "ticket":
        ticket = _find_ticket(spec, composite.entity_id)
        ticket_title = ticket["title"] if ticket else composite.entity_id
        return (
            f'Ticket "{ticket_title}" — ticket_expansion has critical gaps:\n'
            f"{missing_fields}\n\n"
            "DECLARE all together. Files determine scope, AC determines verifiability, steps "
            "determine execution sequence, ticketType determines whether testSpecification is "
            "required.\n\n"
            "Operation available: action_planning_session({\n"
            f"  operation: {{ type: 'update_ticket', ticketId: \"{composite.entity_id}\", ... }}\n"
            "})"
        )

    return (
        f"DECLARE: {composite.entity_id} has {len(composite.grouped_findings)} "
        "missing critical fields."
    )


def format_tactical_gap(
    composite: CompositeFinding, _context: PhaseContext, spec: dict[str, Any]
) -> str:
    missing_fields = "\n".join(f"  - {_leaf(f.field_path)}" for f in composite.grouped_findings)

    if composite.entity_type == "ticket":
        ticket = _find_ticket(spec, composite.entity_id)
        ticket_title = ticket["title"] if ticket else composite.entity_id
        return (
            f'Ticket "{ticket_title}" has the following recommended fields incomplete:\n'
            f"{missing_fields}\n\n"
            "EVALUATE the behavior the declared files must produce, then DECLARE the missing "
            "fields.\n\n"
            "Operation available: action_planning_session({\n"
            f"  operation: {{ type: 'update_ticket', ticketId: \"{composite.entity_id}\", ... }}\n"
            "})"
        )

    if composite.entity_type == "epic":
        epic = _find_epic(spec, composite.entity_id)
        epic_title = epic["title"] if epic else composite.entity_id
        return (
            f'Epic "{epic_title}" has the following recommended fields incomplete:\n'
            f"{missing_fields}\n\n"
            "EVALUATE what is needed, then DECLARE these fields in a single update.\n\n"
            "Operation available: action_planning_session({\n"
            f"  operation: {{ type: 'update_epic', epicId: \"{composite.entity_id}\", ... }}\n"
            "})"
        )

    entity_label = (
        f'Specification "{spec.get("title")}"'
        if composite.entity_type == "specification"
        else composite.entity_id
    )
    return (
        f"{entity_label} has recommended fields incomplete:\n"
        f"{missing_fields}\n\n"
        "EVALUATE and DECLARE the missing fields."
    )


def format_conditional_gap(
    composite: CompositeFinding, _context: PhaseContext, spec: dict[str, Any]
) -> str:
    ticket = _find_ticket(spec, composite.entity_id)
    ticket_title = ticket["title"] if ticket else composite.entity_id
    test_spec = ticket.get("testSpecification") if ticket else None

    missing: list[str] = []
    if not test_spec or not test_spec.get("testTypes"):
        missing.append("  - testTypes empty (minimum 1)")
    if not test_spec or not test_spec.get("qualityGates"):
        missing.append("  - qualityGates empty (minimum 1)")
    if not test_spec or not test_spec.get("testCommands"):
        missing.append("  - testCommands empty")
    if not test_spec or test_spec.get("coverageTarget") is None:
        missing.append("  - coverageTarget not set")
    missing_str = "\n".join(missing) if missing else "  - testSpecification absent"

    return (
        f"Verification ticket \"{ticket_title}\" has ticketType='verification' but "
        f"testSpecification is incomplete:\n"
        f"{missing_str}\n\n"
        "DECLARE the complete test specification covering what this verification must assert "
        "and how.\n\n"
        "Operation available: action_planning_session({\n"
        f"  operation: {{ type: 'update_ticket', ticketId: \"{composite.entity_id}\", "
        "testSpecification: { testTypes, qualityGates, testCommands, coverageTarget } }\n"
        "})"
    )
