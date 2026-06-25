"""File-coordination cross-validation checks (non-wave).

Port of ``cross-validation/{file-consistency,files-to-be-referenced}.ts``.
"""

from __future__ import annotations

from typing import Any

from ..types.result import CrossValidationFinding


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


def check_file_consistency(spec: dict[str, Any]) -> list[CrossValidationFinding]:
    all_tickets = _all_tickets(spec)
    file_to_tickets: dict[str, list[str]] = {}
    for ticket in all_tickets:
        for path in ticket.get("filesToBeCreated") or []:
            file_to_tickets.setdefault(path, []).append(ticket["id"])

    findings: list[CrossValidationFinding] = []
    for path, ticket_ids in file_to_tickets.items():
        if len(ticket_ids) > 1:
            sorted_ids = sorted(ticket_ids)
            findings.append(
                CrossValidationFinding(
                    category="file-conflict",
                    severity="error",
                    field=f"filesToBeCreated:{path}",
                    message=(
                        f'File "{path}" is in filesToBeCreated of multiple tickets: '
                        f"{', '.join(sorted_ids)}"
                    ),
                    entity_ids=sorted_ids,
                    primary_entity_id=sorted_ids[0],
                    operations=["update_ticket"],
                )
            )
    return findings


def _build_transitive_deps(
    ticket_id: str, adj: dict[str, list[str]], cache: dict[str, set[str]]
) -> set[str]:
    if ticket_id in cache:
        return cache[ticket_id]
    result: set[str] = set()
    stack = list(adj.get(ticket_id, []))
    visiting: set[str] = set()
    while stack:
        current = stack.pop()
        if current in visiting or current == ticket_id:
            continue
        visiting.add(current)
        result.add(current)
        stack.extend(adj.get(current, []))
    cache[ticket_id] = result
    return result


def check_files_to_be_referenced(spec: dict[str, Any]) -> list[CrossValidationFinding]:
    all_tickets = _all_tickets(spec)
    adj: dict[str, list[str]] = {}
    file_to_creator: dict[str, str] = {}
    dep_cache: dict[str, set[str]] = {}

    for ticket in all_tickets:
        tid = ticket["id"]
        adj[tid] = [d["ticketId"] for d in (ticket.get("dependencies") or [])]
        for path in ticket.get("filesToBeCreated") or []:
            file_to_creator[path] = tid
        for path in ticket.get("filesToBeModified") or []:
            if path not in file_to_creator:
                file_to_creator[path] = tid

    findings: list[CrossValidationFinding] = []
    for ticket in all_tickets:
        tid = ticket["id"]
        transitive = _build_transitive_deps(tid, adj, dep_cache)
        for path in ticket.get("filesToBeReferenced") or []:
            creator = file_to_creator.get(path)
            if creator and creator != tid and creator not in transitive:
                findings.append(
                    CrossValidationFinding(
                        category="files-to-be-referenced",
                        severity="error",
                        field=f"tickets[id={tid}].filesToBeReferenced:{path}",
                        message=(
                            f'Ticket "{tid}" references "{path}" but does not declare '
                            f'dependencies on creator "{creator}"'
                        ),
                        entity_ids=[tid],
                        primary_entity_id=tid,
                        operations=["update_ticket", "create_ticket"],
                    )
                )
            elif not creator:
                findings.append(
                    CrossValidationFinding(
                        category="files-to-be-referenced",
                        severity="error",
                        field=f"tickets[id={tid}].filesToBeReferenced:{path}",
                        message=(
                            f'Ticket "{tid}" references "{path}" but no ticket '
                            f"creates/modifies it"
                        ),
                        entity_ids=[tid],
                        primary_entity_id=tid,
                        operations=["update_ticket", "create_ticket"],
                    )
                )
    return findings
