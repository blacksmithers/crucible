"""Topology-bound cross-validation checks (port of ``topology-{roots,leaves}-exceed.ts``)."""

from __future__ import annotations

import math
from typing import Any

from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding
from .emission import CVEmission


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


def max_allowed(total_tickets: int, ratio: float, cap: int) -> int:
    return min(math.ceil(total_tickets * ratio), cap)


def check_topology_roots_exceed(spec: dict[str, Any], config: ValidatorConfig) -> list[CVEmission]:
    all_tickets = _all_tickets(spec)
    total = len(all_tickets)
    if total == 0:
        return []

    roots = [t for t in all_tickets if len(t.get("dependencies") or []) == 0]
    root_count = len(roots)
    topo = config["crossValidation"]["topology"]
    root_ratio, root_cap = topo["rootRatio"], topo["rootCap"]
    maximum = max_allowed(total, root_ratio, root_cap)
    if root_count <= maximum:
        return []

    sorted_root_ids = sorted(t["id"] for t in roots)
    ratio_pct = f"{root_ratio * 100:.0f}"
    formula = f"min(ceil({total} × {root_ratio}), {root_cap}) = {maximum}"
    return [
        CVEmission(
            finding=CrossValidationFinding(
                category="topology-roots-exceed",
                severity="error",
                field="specification.tickets",
                message=f"{root_count} root tickets exceed maximum {maximum} ({total} total)",
                entity_ids=sorted_root_ids,
                primary_entity_id=sorted_root_ids[0],
                operations=["update_ticket"],
                context={
                    "rootCount": root_count,
                    "totalTickets": total,
                    "maxAllowed": maximum,
                    "rootIds": sorted_root_ids,
                },
            ),
            guidance=(
                f"Spec has {root_count} tickets without dependencies (roots), but the maximum "
                f"allowed is {maximum} (computed: {formula}, ratio {ratio_pct}% capped at "
                f"{root_cap}). Too many roots indicates that sequencing was under-declared — "
                "several tickets can start in parallel, but this rarely reflects the reality of "
                "implementation. Establish dependencies between related tickets to reflect the "
                "real execution order, or justify legitimate roots via "
                "fieldDeclarations.dependencies with an explicit reason for each. Real "
                "foundational tickets (3–5 roots) are acceptable when justified; the excess is "
                "almost always a lack of articulation."
            ),
        )
    ]


def check_topology_leaves_exceed(spec: dict[str, Any], config: ValidatorConfig) -> list[CVEmission]:
    all_tickets = _all_tickets(spec)
    total = len(all_tickets)
    if total == 0:
        return []

    has_dependents: set[str] = set()
    for ticket in all_tickets:
        for dep in ticket.get("dependencies") or []:
            has_dependents.add(dep["ticketId"])
    leaves = [t for t in all_tickets if t["id"] not in has_dependents]
    leaf_count = len(leaves)
    topo = config["crossValidation"]["topology"]
    leaf_ratio, leaf_cap = topo["leafRatio"], topo["leafCap"]
    maximum = max_allowed(total, leaf_ratio, leaf_cap)
    if leaf_count <= maximum:
        return []

    sorted_leaf_ids = sorted(t["id"] for t in leaves)
    ratio_pct = f"{leaf_ratio * 100:.0f}"
    formula = f"min(ceil({total} × {leaf_ratio}), {leaf_cap}) = {maximum}"
    return [
        CVEmission(
            finding=CrossValidationFinding(
                category="topology-leaves-exceed",
                severity="error",
                field="specification.tickets",
                message=f"{leaf_count} leaf tickets exceed maximum {maximum} ({total} total)",
                entity_ids=sorted_leaf_ids,
                primary_entity_id=sorted_leaf_ids[0],
                operations=["update_ticket", "create_ticket"],
                context={
                    "leafCount": leaf_count,
                    "totalTickets": total,
                    "maxAllowed": maximum,
                    "leafIds": sorted_leaf_ids,
                },
            ),
            guidance=(
                f"Spec has {leaf_count} tickets with no dependents (leaves), but the maximum "
                f"allowed is {maximum} (computed: {formula}, ratio {ratio_pct}% capped at "
                f"{leaf_cap}). Too many leaves indicates that the set of terminal tickets does "
                "not converge — some of them likely should feed into other tickets (e.g., "
                "implementation tickets that should be consumed by verification or integration "
                "tickets). Consider adding integration/verification tickets that depend on the "
                "existing leaves, or consolidate tickets that produce similar outputs."
            ),
        )
    ]
