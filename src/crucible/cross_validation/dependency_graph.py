"""Dependency-graph cross-validation checks (cycles, broken/orphan/island refs).

Emissions (finding + guidance prose).
"""

from __future__ import annotations

from typing import Any

from .. import i18n
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


def detect_cycles(spec: dict[str, Any], language: str = "en") -> list[CVEmission]:
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
                            guidance=i18n.render(
                                i18n.text(language, "cv.circularDependency"),
                                {"arrow": arrow},
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


def check_broken_reference(spec: dict[str, Any], language: str = "en") -> list[CVEmission]:
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
                        guidance=i18n.render(
                            i18n.text(language, "cv.brokenReference"),
                            {"ticketId": tid, "depId": dep_id},
                        ),
                    )
                )
    return emissions


def check_orphan_reference(
    spec: dict[str, Any], config: ValidatorConfig, language: str = "en"
) -> list[CVEmission]:
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
                    # the remedy is either add a dependency (create_dependencies)
                    # or justify the root's `dependencies` N/A (the dedicated `justify` op).
                    # Dropped the stale update_ticket/create_ticket N/A hint (justification
                    # no longer rides update_*).
                    operations=["create_dependencies", "justify"],
                ),
                # WHAT only (structural fact + the two remedies). The "how"
                # (which op, which payload) is NOT the validator's job: the machine hint is
                # `finding.operations` (create_dependencies / justify) and the invocation
                # prose is lifecycle-owned. No `fieldDeclarations` mechanic here
                # (guidance-source boundary, point #1).
                guidance=i18n.render(
                    i18n.text(language, "cv.orphanReference"), {"ticketId": tid}
                ),
            )
        )
    return emissions


def check_island_ticket(
    spec: dict[str, Any], config: ValidatorConfig, language: str = "en"
) -> list[CVEmission]:
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
                    # remedy: add a dependency edge (create_dependencies) or
                    # justify the isolation via the dedicated `justify` op. Dropped the
                    # stale update_ticket N/A hint.
                    operations=["create_dependencies", "justify"],
                ),
                # WHAT only (structural fact + remedies). The "how" (which op,
                # which payload) is lifecycle-owned; the machine hint is
                # `finding.operations` (create_dependencies / justify). No
                # `fieldDeclarations` mechanic (point #1).
                guidance=i18n.render(
                    i18n.text(language, "cv.islandTicket"), {"ticketId": tid}
                ),
            )
        )
    return emissions
