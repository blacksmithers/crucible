"""Dependency-graph cross-validation checks (cycles, broken/orphan/island refs).

Port of ``cross-validation/{circular-dependencies,broken-reference,
orphan-reference,island-ticket}.ts`` — emissions (finding + guidance prose).
"""

from __future__ import annotations

from typing import Any

from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding
from .emission import CVEmission


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


def _has_dependencies_na_justification(ticket: dict[str, Any], config: ValidatorConfig) -> bool:
    decls = ticket.get("fieldDeclarations")
    decl = decls.get("dependencies") if isinstance(decls, dict) else None
    if not isinstance(decl, dict) or decl.get("value") != "N/A":
        return False
    reason = decl.get("reason")
    if not reason:
        return False
    return bool(len(reason) >= config["naReason"]["minLength"])


def detect_cycles(spec: dict[str, Any]) -> list[CVEmission]:
    all_tickets = _all_tickets(spec)
    adj: dict[str, list[str]] = {
        t["id"]: [d["ticketId"] for d in (t.get("dependencies") or [])] for t in all_tickets
    }

    emissions: list[CVEmission] = []
    visited: set[str] = set()
    reported: set[str] = set()

    def dfs(node: str, path: list[str]) -> None:
        path_set = set(path)
        for neighbor in adj.get(node, []):
            if neighbor in path_set:
                cycle = [*path[path.index(neighbor) :], neighbor]
                cycle_key = ",".join(sorted(cycle))
                if cycle_key not in reported:
                    reported.add(cycle_key)
                    cycle_ids = cycle[:-1]
                    primary = cycle_ids[0]
                    arrow = " → ".join(cycle)
                    emissions.append(
                        CVEmission(
                            finding=CrossValidationFinding(
                                category="circular-dependency",
                                severity="error",
                                field=f"tickets[id={primary}].dependencies",
                                message=f"Cycle detected: {arrow}",
                                entity_ids=cycle_ids,
                                primary_entity_id=primary,
                                operations=["update_ticket"],
                            ),
                            guidance=(
                                f"Dependency cycle detected: {arrow}. Cycles break topological "
                                "ordering and stall execution at runtime — no ticket in the cycle "
                                "can start because each one waits on the other. Remove one of the "
                                "dependencies in the cycle (typically the least critical) or "
                                "restructure the work split to eliminate the circularity. If two "
                                "tickets have a natural circular dependency, they may need to be "
                                "consolidated into a single ticket."
                            ),
                        )
                    )
                continue
            if neighbor not in visited:
                dfs(neighbor, [*path, neighbor])

    for ticket in all_tickets:
        tid = ticket["id"]
        if tid not in visited:
            dfs(tid, [tid])
            visited.add(tid)

    return emissions


def check_broken_reference(spec: dict[str, Any]) -> list[CVEmission]:
    all_tickets = _all_tickets(spec)
    all_ids = {t["id"] for t in all_tickets}
    emissions: list[CVEmission] = []

    for ticket in all_tickets:
        tid = ticket["id"]
        for dep in ticket.get("dependencies") or []:
            dep_id = dep["ticketId"]
            if dep_id not in all_ids:
                emissions.append(
                    CVEmission(
                        finding=CrossValidationFinding(
                            category="broken-reference",
                            severity="error",
                            field=f"tickets[id={tid}].dependencies",
                            message=(
                                f'Ticket "{tid}" dependencies references non-existent '
                                f'ticket "{dep_id}"'
                            ),
                            entity_ids=[tid],
                            primary_entity_id=tid,
                            operations=["update_ticket", "create_ticket"],
                        ),
                        guidance=(
                            f'Ticket "{tid}" references "{dep_id}" in dependencies, but '
                            f'"{dep_id}" does not exist in any epic of the spec. Broken '
                            "references cause immediate failure at runtime when the lifecycle "
                            "tries to resolve dependencies to compute execution order. Resolve by "
                            "creating the missing ticket (if it's part of the real work) OR by "
                            "removing the reference (if it was a typo or a renamed ticket)."
                        ),
                    )
                )
    return emissions


def check_orphan_reference(spec: dict[str, Any], config: ValidatorConfig) -> list[CVEmission]:
    all_tickets = _all_tickets(spec)
    if not all_tickets:
        return []

    has_dependents: set[str] = set()
    for ticket in all_tickets:
        for dep in ticket.get("dependencies") or []:
            has_dependents.add(dep["ticketId"])

    emissions: list[CVEmission] = []
    for ticket in all_tickets:
        tid = ticket["id"]
        is_root = len(ticket.get("dependencies") or []) == 0
        is_leaf = tid not in has_dependents
        if not is_root or is_leaf:
            continue
        if _has_dependencies_na_justification(ticket, config):
            continue
        emissions.append(
            CVEmission(
                finding=CrossValidationFinding(
                    category="orphan-reference",
                    severity="error",
                    field=f"tickets[id={tid}].dependencies",
                    message=(
                        f'Ticket "{tid}" has no dependencies but has dependents — root unjustified'
                    ),
                    entity_ids=[tid],
                    primary_entity_id=tid,
                    operations=["update_ticket", "create_ticket"],
                ),
                guidance=(
                    f'Ticket "{tid}" declares no dependencies (no prior work listed), but other '
                    "tickets depend on it. Unjustified roots indicate that preparatory work was "
                    "implicitly assumed — there's likely setup, infrastructure, or modeling that "
                    "precedes this ticket but wasn't articulated in the spec. Add tickets that "
                    "precede this work in dependencies OR explicitly justify via "
                    'fieldDeclarations.dependencies with reason "foundational ticket — no prior '
                    'work" (or similar) if the ticket is genuinely the starting point.'
                ),
            )
        )
    return emissions


def check_island_ticket(spec: dict[str, Any], config: ValidatorConfig) -> list[CVEmission]:
    all_tickets = _all_tickets(spec)
    if not all_tickets:
        return []

    has_dependents: set[str] = set()
    for ticket in all_tickets:
        for dep in ticket.get("dependencies") or []:
            has_dependents.add(dep["ticketId"])

    emissions: list[CVEmission] = []
    for ticket in all_tickets:
        tid = ticket["id"]
        is_root = len(ticket.get("dependencies") or []) == 0
        is_leaf = tid not in has_dependents
        if not (is_root and is_leaf):
            continue
        if _has_dependencies_na_justification(ticket, config):
            continue
        emissions.append(
            CVEmission(
                finding=CrossValidationFinding(
                    category="island-ticket",
                    severity="error",
                    field=f"tickets[id={tid}].dependencies",
                    message=f'Ticket "{tid}" is isolated — no dependencies and no dependents',
                    entity_ids=[tid],
                    primary_entity_id=tid,
                    operations=["update_ticket"],
                ),
                guidance=(
                    f'Ticket "{tid}" has neither dependencies nor dependents — it is fully '
                    "isolated from the execution graph. Isolated tickets break wave computation "
                    "because there is no natural execution order, and may indicate work "
                    "disconnected from the rest of the spec (likely a planning smell). Add "
                    "dependencies pointing to a ticket that precedes this work OR make another "
                    "ticket depend on this one OR justify the isolation via "
                    "fieldDeclarations.dependencies with an explicit reason (e.g., \"standalone "
                    'setup ticket, intentionally isolated from dependency graph").'
                ),
            )
        )
    return emissions
