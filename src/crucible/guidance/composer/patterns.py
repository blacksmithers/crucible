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
