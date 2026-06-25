"""Topology penalties (port of ``scoring/topology.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..types.config import ValidatorConfig


@dataclass(frozen=True)
class TopologyResult:
    root_count: int
    leaf_count: int
    island_count: int
    total_tickets: int
    root_ratio: float
    leaf_ratio: float
    root_ratio_exceeded: bool
    leaf_ratio_exceeded: bool
    total_penalty: float


def compute_topology_penalties(spec: dict[str, Any], config: ValidatorConfig) -> TopologyResult:
    all_tickets = [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]
    total = len(all_tickets)

    if total == 0:
        return TopologyResult(0, 0, 0, 0, 0.0, 0.0, False, False, 0.0)

    has_dependents: set[str] = set()
    for ticket in all_tickets:
        for dep in ticket.get("dependencies") or []:
            has_dependents.add(dep.get("ticketId"))

    roots: list[str] = []
    leaves: list[str] = []
    islands: list[str] = []
    for ticket in all_tickets:
        is_root = len(ticket.get("dependencies") or []) == 0
        is_leaf = ticket.get("id") not in has_dependents
        if is_root:
            roots.append(ticket.get("id"))
        if is_leaf:
            leaves.append(ticket.get("id"))
        if is_root and is_leaf:
            islands.append(ticket.get("id"))

    topo = config["topology"]
    root_ratio = len(roots) / total
    leaf_ratio = len(leaves) / total
    root_exceeded = root_ratio > topo["maxRootRatio"]
    leaf_exceeded = leaf_ratio > topo["maxLeafRatio"]

    total_penalty = 0.0
    if root_exceeded:
        total_penalty += topo["rootPenalty"] * len(roots)
    if leaf_exceeded:
        total_penalty += topo["leafPenalty"] * len(leaves)
    # Island penalty is cumulative on top of root+leaf (no ratio gate).
    total_penalty += topo["islandPenalty"] * len(islands)

    return TopologyResult(
        root_count=len(roots),
        leaf_count=len(leaves),
        island_count=len(islands),
        total_tickets=total,
        root_ratio=root_ratio,
        leaf_ratio=leaf_ratio,
        root_ratio_exceeded=root_exceeded,
        leaf_ratio_exceeded=leaf_exceeded,
        total_penalty=total_penalty,
    )
