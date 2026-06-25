"""Composite-pattern detectors (port of ``guidance/composer/patterns/*``)."""

from __future__ import annotations

from typing import Any

from ...types.context import PhaseContext
from ...types.finding import CompositeFinding, Finding
from ...types.operations import OperationName


def _ops_for(entity_type: str) -> list[OperationName]:
    if entity_type == "specification":
        return ["set_metadata"]
    if entity_type == "epic":
        return ["update_epic"]
    return ["update_ticket"]


def _group_by_entity(findings: list[Finding]) -> dict[str, list[Finding]]:
    grouped: dict[str, list[Finding]] = {}
    for f in findings:
        grouped.setdefault(f.entity_id, []).append(f)
    return grouped


def detect_foundation_gap(
    findings: list[Finding], _context: PhaseContext, _spec: dict[str, Any]
) -> list[CompositeFinding]:
    missing_critical = [f for f in findings if f.status == "missing" and f.tier == "critical"]
    composites: list[CompositeFinding] = []
    for entity_id, group in _group_by_entity(missing_critical).items():
        if len(group) < 2:
            continue
        entity_type = group[0].entity_type
        composites.append(
            CompositeFinding(
                pattern_id="foundation-gap",
                entity_id=entity_id,
                entity_type=entity_type,
                grouped_findings=group,
                total_points_lost=sum(f.points_lost for f in group),
                total_global_impact_on_fix=sum(f.global_impact_on_fix for f in group),
                primary_verb="DECLARE",
                suggested_operations=_ops_for(entity_type),
            )
        )
    return composites


def detect_tactical_gap(
    findings: list[Finding], _context: PhaseContext, _spec: dict[str, Any]
) -> list[CompositeFinding]:
    critical_by_entity: dict[str, bool] = {}
    for f in findings:
        if f.tier != "critical":
            continue
        if f.status == "missing":
            critical_by_entity[f.entity_id] = False
        elif f.entity_id not in critical_by_entity:
            critical_by_entity[f.entity_id] = True

    missing_rec = [
        f for f in findings if f.status == "missing" and f.tier in ("recommended", "enrichment")
    ]
    grouped: dict[str, list[Finding]] = {}
    for f in missing_rec:
        if critical_by_entity.get(f.entity_id) is False:
            continue
        grouped.setdefault(f.entity_id, []).append(f)

    composites: list[CompositeFinding] = []
    for entity_id, group in grouped.items():
        if len(group) < 2:
            continue
        entity_type = group[0].entity_type
        composites.append(
            CompositeFinding(
                pattern_id="tactical-gap",
                entity_id=entity_id,
                entity_type=entity_type,
                grouped_findings=group,
                total_points_lost=sum(f.points_lost for f in group),
                total_global_impact_on_fix=sum(f.global_impact_on_fix for f in group),
                primary_verb="EVALUATE",
                suggested_operations=_ops_for(entity_type),
            )
        )
    return composites


def _matches_test_spec(field_path: str) -> bool:
    return field_path == "ticket.testSpecification" or field_path.startswith(
        "ticket.testSpecification."
    )


def detect_conditional_gap(
    findings: list[Finding], _context: PhaseContext, spec: dict[str, Any]
) -> list[CompositeFinding]:
    verification_ids = {
        t["id"]
        for e in (spec.get("epics") or [])
        for t in (e.get("tickets") or [])
        if t.get("ticketType") == "verification"
    }
    conditional_missing = [
        f
        for f in findings
        if f.status == "missing"
        and _matches_test_spec(f.field_path)
        and f.entity_id in verification_ids
    ]
    composites: list[CompositeFinding] = []
    for entity_id, group in _group_by_entity(conditional_missing).items():
        composites.append(
            CompositeFinding(
                pattern_id="conditional-gap",
                entity_id=entity_id,
                entity_type="ticket",
                grouped_findings=group,
                total_points_lost=sum(f.points_lost for f in group),
                total_global_impact_on_fix=sum(f.global_impact_on_fix for f in group),
                primary_verb="DECLARE",
                suggested_operations=["update_ticket"],
            )
        )
    return composites


def detect_linkage_gap(
    _findings: list[Finding], context: PhaseContext, spec: dict[str, Any]
) -> list[CompositeFinding]:
    if context.phase != "cross_validation":
        return []

    composites: list[CompositeFinding] = []
    all_tickets = [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]
    w_spec = context.config["scoring"]["weights"]["spec"]

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
    if orphans:
        total = len(orphans) * 5
        composites.append(
            CompositeFinding(
                pattern_id="linkage-gap",
                entity_id=spec["id"],
                entity_type="specification",
                grouped_findings=[],
                total_points_lost=total,
                total_global_impact_on_fix=total * w_spec,
                primary_verb="ADD",
                suggested_operations=["link_blueprint", "update_blueprint", "delete_blueprint"],
            )
        )

    file_to_creator: dict[str, str] = {}
    for ticket in all_tickets:
        for path in ticket.get("filesToBeCreated") or []:
            file_to_creator[path] = ticket["id"]
        for path in ticket.get("filesToBeModified") or []:
            file_to_creator.setdefault(path, ticket["id"])

    missing_deps = 0
    for ticket in all_tickets:
        deps = {d["ticketId"] for d in (ticket.get("dependencies") or [])}
        for path in ticket.get("filesToBeReferenced") or []:
            creator = file_to_creator.get(path)
            if creator and creator != ticket["id"] and creator not in deps:
                missing_deps += 1

    if missing_deps > 0:
        total = missing_deps * 3
        composites.append(
            CompositeFinding(
                pattern_id="linkage-gap",
                entity_id=spec["id"],
                entity_type="specification",
                grouped_findings=[],
                total_points_lost=total,
                total_global_impact_on_fix=total * w_spec,
                primary_verb="ADD",
                suggested_operations=["add_dependencies"],
            )
        )
    return composites


def _has_cycle(spec: dict[str, Any]) -> bool:
    all_tickets = [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]
    adj = {t["id"]: [d["ticketId"] for d in (t.get("dependencies") or [])] for t in all_tickets}
    visited: set[str] = set()
    in_stack: set[str] = set()

    def dfs(node: str) -> bool:
        if node in in_stack:
            return True
        if node in visited:
            return False
        visited.add(node)
        in_stack.add(node)
        for neighbor in adj.get(node, []):
            if dfs(neighbor):
                return True
        in_stack.discard(node)
        return False

    return any(t["id"] not in visited and dfs(t["id"]) for t in all_tickets)


def detect_integrity_gap(
    _findings: list[Finding], context: PhaseContext, spec: dict[str, Any]
) -> list[CompositeFinding]:
    if context.phase != "cross_validation":
        return []

    composites: list[CompositeFinding] = []
    all_tickets = [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]
    w_spec = context.config["scoring"]["weights"]["spec"]

    file_to_tickets: dict[str, list[str]] = {}
    for ticket in all_tickets:
        for path in ticket.get("filesToBeCreated") or []:
            file_to_tickets.setdefault(path, []).append(ticket["id"])
    conflicts = [ids for ids in file_to_tickets.values() if len(ids) > 1]

    if conflicts:
        total = len(conflicts) * 5
        composites.append(
            CompositeFinding(
                pattern_id="integrity-gap",
                entity_id=spec["id"],
                entity_type="specification",
                grouped_findings=[],
                total_points_lost=total,
                total_global_impact_on_fix=total * w_spec,
                primary_verb="RECONCILE",
                suggested_operations=["update_ticket", "add_dependencies"],
            )
        )

    if all_tickets and _has_cycle(spec):
        composites.append(
            CompositeFinding(
                pattern_id="integrity-gap",
                entity_id=spec["id"],
                entity_type="specification",
                grouped_findings=[],
                total_points_lost=20,
                total_global_impact_on_fix=20 * w_spec,
                primary_verb="RECONCILE",
                suggested_operations=["remove_dependency"],
            )
        )

    imp_count = sum(1 for t in all_tickets if t.get("ticketType") == "implementation")
    ver_count = sum(1 for t in all_tickets if t.get("ticketType") == "verification")
    max_ratio = context.config["crossValidation"]["ratios"]["implementationToVerification"]["max"]
    if all_tickets and (ver_count == 0 or (ver_count > 0 and imp_count / ver_count > max_ratio)):
        composites.append(
            CompositeFinding(
                pattern_id="integrity-gap",
                entity_id=spec["id"],
                entity_type="specification",
                grouped_findings=[],
                total_points_lost=10,
                total_global_impact_on_fix=10 * w_spec,
                primary_verb="CREATE",
                suggested_operations=["create_ticket"],
            )
        )

    epic_count = len(spec.get("epics") or [])
    if epic_count > 0:
        bp_count = sum(
            1 for b in (spec.get("blueprints") or []) if b.get("coverageType") == "ticket"
        )
        min_ratio = context.config["crossValidation"]["ratios"]["blueprintToEpic"]["min"]
        if bp_count / epic_count < min_ratio:
            composites.append(
                CompositeFinding(
                    pattern_id="integrity-gap",
                    entity_id=spec["id"],
                    entity_type="specification",
                    grouped_findings=[],
                    total_points_lost=8,
                    total_global_impact_on_fix=8 * w_spec,
                    primary_verb="CREATE",
                    suggested_operations=["create_blueprint"],
                )
            )
    return composites
