"""Composite-pattern prose templates (port of ``guidance/format/templates/*``).

Strings are verbatim from the TS source.
"""

from __future__ import annotations

import math
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


def format_linkage_gap(
    composite: CompositeFinding, context: PhaseContext, spec: dict[str, Any]
) -> str:
    all_tickets = [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]

    if "link_blueprint" in composite.suggested_operations:
        min_tickets = context.config["crossValidation"]["checks"]["blueprint-coverage"][
            "minTicketsPerBlueprint"
        ]
        link_count: dict[str, int] = {}
        for ticket in all_tickets:
            for ref in ticket.get("blueprintReferences") or []:
                link_count[ref["blueprintId"]] = link_count.get(ref["blueprintId"], 0) + 1
        orphans = [
            b
            for b in (spec.get("blueprints") or [])
            if b.get("coverageType") == "ticket" and link_count.get(b["id"], 0) < min_tickets
        ]
        orphan_list = "\n".join(
            f'  - {b["id"]} "{b.get("title")}" ({link_count.get(b["id"], 0)} linked)'
            for b in orphans
        )
        return (
            f"{len(orphans)} blueprint(s) (coverageType: ticket) in spec "
            f'"{spec.get("title")}" have fewer than {min_tickets} tickets linked:\n'
            f"{orphan_list}\n\n"
            "EXPLORE tickets in this spec that benefit from each blueprint and ADD the "
            "references. If a blueprint has no benefiting tickets, EVALUATE whether it should "
            "be transversal (coverageType: 'all') instead, or shouldn't exist.\n\n"
            "Operations available:\n"
            "  - action_planning_session({ operation: { type: 'link_blueprint', ticketId, "
            "blueprintId, context?, section? }})\n"
            "  - action_planning_session({ operation: { type: 'update_blueprint', blueprintId, "
            "coverageType: 'all' }})\n"
            "  - action_planning_session({ operation: { type: 'delete_blueprint', blueprintId }})"
        )

    if "add_dependencies" in composite.suggested_operations:
        file_to_creator: dict[str, str] = {}
        for ticket in all_tickets:
            for path in ticket.get("filesToBeCreated") or []:
                file_to_creator[path] = ticket["id"]
            for path in ticket.get("filesToBeModified") or []:
                file_to_creator.setdefault(path, ticket["id"])
        missing_deps: list[tuple[str, str]] = []
        for ticket in all_tickets:
            deps = {d["ticketId"] for d in (ticket.get("dependencies") or [])}
            for path in ticket.get("filesToBeReferenced") or []:
                creator = file_to_creator.get(path)
                if creator and creator != ticket["id"] and creator not in deps:
                    missing_deps.append((ticket["id"], creator))
        dep_list = "\n".join(
            f"  - {tid} references files created by {cid}" for tid, cid in missing_deps
        )
        return (
            f"{len(missing_deps)} ticket(s) reference files modified by other tickets without "
            f"declaring dependencies:\n"
            f"{dep_list}\n\n"
            "ADD all missing dependency declarations in a SINGLE call. The operation accepts up "
            "to 5000 pairs and the server validates the complete graph before any write.\n\n"
            "Operation available: action_planning_session({\n"
            "  operation: {\n"
            "    type: 'add_dependencies',\n"
            "    dependencies: [{ ticketId, dependsOnId, type? }, ...]\n"
            "  }\n"
            "})"
        )

    return f'EXPLORE and ADD missing linkages for spec "{spec.get("title")}".'


def format_integrity_gap(
    composite: CompositeFinding, context: PhaseContext, spec: dict[str, Any]
) -> str:
    all_tickets = [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]
    ops = composite.suggested_operations

    if "remove_dependency" in ops:
        return (
            f'Circular dependency detected in spec "{spec.get("title")}".\n\n'
            "RECONCILE by identifying the cycle and removing the redundant dependency that "
            "creates the loop.\n\n"
            "Operations available:\n"
            "  - action_planning_session({ operation: { type: 'remove_dependency', ticketId, "
            "dependsOnId }})"
        )

    if "update_ticket" in ops and "add_dependencies" in ops:
        file_to_tickets: dict[str, list[str]] = {}
        for ticket in all_tickets:
            for path in ticket.get("filesToBeCreated") or []:
                file_to_tickets.setdefault(path, []).append(ticket["id"])
        conflicts = [(p, ids) for p, ids in file_to_tickets.items() if len(ids) > 1]
        conflict_list = "\n".join(
            f"  - '{path}' declared in filesToBeCreated of {' AND '.join(ids)}"
            for path, ids in conflicts
        )
        return (
            f"{len(conflicts)} file path conflict(s) detected in spec "
            f'"{spec.get("title")}":\n'
            f"{conflict_list}\n\n"
            "RECONCILE by deciding which ticket owns the file creation. The other ticket should "
            "declare it as filesToBeModified instead, with dependencies on the owner.\n\n"
            "Operations available:\n"
            "  - action_planning_session({ operation: { type: 'update_ticket', ticketId, ... }})\n"
            "  - action_planning_session({ operation: { type: 'add_dependencies', "
            "dependencies: [...] }})"
        )

    if "create_ticket" in ops:
        imp_count = sum(1 for t in all_tickets if t.get("ticketType") == "implementation")
        ver_count = sum(1 for t in all_tickets if t.get("ticketType") == "verification")
        ratio = f"{imp_count / ver_count:.1f}" if ver_count > 0 else "N/A"
        max_ratio = context.config["crossValidation"]["ratios"]["implementationToVerification"][
            "max"
        ]
        return (
            f'Spec "{spec.get("title")}" has an imbalanced implementation:verification ratio '
            f"({ratio}:1, max: {max_ratio}:1).\n\n"
            "EVALUATE which implementation tickets lack corresponding verification tickets, then "
            "CREATE verification tickets to restore the balance.\n\n"
            "Operations available:\n"
            "  - action_planning_session({ operation: { type: 'create_ticket', epicId, title, "
            "description? }})"
        )

    if "create_blueprint" in ops:
        epic_count = len(spec.get("epics") or [])
        bp_count = sum(
            1 for b in (spec.get("blueprints") or []) if b.get("coverageType") == "ticket"
        )
        min_ratio = context.config["crossValidation"]["ratios"]["blueprintToEpic"]["min"]
        return (
            f'Spec "{spec.get("title")}" has {bp_count} ticket-scoped blueprint(s) for '
            f"{epic_count} epic(s) (need ≥{math.ceil(epic_count * min_ratio)}).\n\n"
            "EXPLORE which architectural concerns are not yet documented as blueprints, then "
            "CREATE additional ones.\n\n"
            "Categories available: flowchart, architecture, state, sequence, erd, mockup, adr, "
            "component, deployment, api, algorithm, protocol, glossary, design-system\n\n"
            "Operation available: action_planning_session({\n"
            "  operation: { type: 'create_blueprint', title, content, category, format?, "
            "coverageType }\n"
            "})"
        )

    return f'RECONCILE structural integrity issues in spec "{spec.get("title")}".'
