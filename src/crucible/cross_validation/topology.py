"""Topology-bound cross-validation checks."""

from __future__ import annotations

import math
from typing import Any

from .. import i18n
from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding
from .emission import CVEmission


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


def max_allowed(total_tickets: int, ratio: float, cap: int) -> int:
    return min(math.ceil(total_tickets * ratio), cap)


def check_topology_roots_exceed(
    spec: dict[str, Any], config: ValidatorConfig, language: str = "en"
) -> list[CVEmission]:
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
                # remedy: establish dependencies (create_dependencies) or justify
                # the legitimate roots' `dependencies` N/A via the dedicated `justify` op.
                # Dropped the stale update_ticket N/A hint. (NOT applied to
                # topology-leaves-exceed — its remedy is "add integration/verification
                # tickets / consolidate", not a justification.)
                operations=["create_dependencies", "justify"],
                context={
                    "rootCount": root_count,
                    "totalTickets": total,
                    "maxAllowed": maximum,
                    "rootIds": sorted_root_ids,
                },
            ),
            # WHAT only (structural fact + remedies). The "how" (which op, which
            # payload) is lifecycle-owned; the machine hint is `finding.operations`
            # (create_dependencies / justify). No `fieldDeclarations` mechanic (point #1).
            guidance=i18n.render(
                i18n.text(language, "cv.topologyRootsExceed"),
                {
                    "rootCount": root_count,
                    "maximum": maximum,
                    "formula": formula,
                    "ratioPct": ratio_pct,
                    "rootCap": root_cap,
                },
            ),
        )
    ]


def check_topology_leaves_exceed(
    spec: dict[str, Any], config: ValidatorConfig, language: str = "en"
) -> list[CVEmission]:
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
            guidance=i18n.render(
                i18n.text(language, "cv.topologyLeavesExceed"),
                {
                    "leafCount": leaf_count,
                    "maximum": maximum,
                    "formula": formula,
                    "ratioPct": ratio_pct,
                    "leafCap": leaf_cap,
                },
            ),
        )
    ]
