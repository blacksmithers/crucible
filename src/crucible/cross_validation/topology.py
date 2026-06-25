"""Topology-bound cross-validation checks (port of ``topology-{roots,leaves}-exceed.ts``)."""

from __future__ import annotations

import math
from typing import Any

from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


def max_allowed(total_tickets: int, ratio: float, cap: int) -> int:
    return min(math.ceil(total_tickets * ratio), cap)


def check_topology_roots_exceed(
    spec: dict[str, Any], config: ValidatorConfig
) -> list[CrossValidationFinding]:
    all_tickets = _all_tickets(spec)
    total = len(all_tickets)
    if total == 0:
        return []

    roots = [t for t in all_tickets if len(t.get("dependencies") or []) == 0]
    root_count = len(roots)
    topo = config["crossValidation"]["topology"]
    maximum = max_allowed(total, topo["rootRatio"], topo["rootCap"])
    if root_count <= maximum:
        return []

    sorted_root_ids = sorted(t["id"] for t in roots)
    return [
        CrossValidationFinding(
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
        )
    ]


def check_topology_leaves_exceed(
    spec: dict[str, Any], config: ValidatorConfig
) -> list[CrossValidationFinding]:
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
    maximum = max_allowed(total, topo["leafRatio"], topo["leafCap"])
    if leaf_count <= maximum:
        return []

    sorted_leaf_ids = sorted(t["id"] for t in leaves)
    return [
        CrossValidationFinding(
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
        )
    ]
