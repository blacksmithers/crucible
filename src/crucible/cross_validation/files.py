"""File-coordination cross-validation checks (emissions).

Port of ``cross-validation/{file-consistency,files-to-be-referenced}.ts``.
"""

from __future__ import annotations

from typing import Any

from ..types.result import CrossValidationFinding
from .emission import CVEmission


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


def check_file_consistency(spec: dict[str, Any]) -> list[CVEmission]:
    all_tickets = _all_tickets(spec)
    file_to_tickets: dict[str, list[str]] = {}
    for ticket in all_tickets:
        for path in ticket.get("filesToBeCreated") or []:
            file_to_tickets.setdefault(path, []).append(ticket["id"])

    emissions: list[CVEmission] = []
    for path, ticket_ids in file_to_tickets.items():
        if len(ticket_ids) <= 1:
            continue
        sorted_ids = sorted(ticket_ids)
        list_str = ", ".join(sorted_ids)
        emissions.append(
            CVEmission(
                finding=CrossValidationFinding(
                    category="file-conflict",
                    severity="error",
                    field=f"filesToBeCreated:{path}",
                    message=(
                        f'File "{path}" is in filesToBeCreated of multiple tickets: {list_str}'
                    ),
                    entity_ids=sorted_ids,
                    primary_entity_id=sorted_ids[0],
                    operations=["update_ticket"],
                ),
                guidance=(
                    f'Tickets [{list_str}] all declare creating "{path}". Two or more tickets '
                    "creating the same file produce merge conflicts and duplicated work — at "
                    "runtime, distinct agents would attempt to create the same file. Reassign "
                    "creation of the file to a single ticket OR consolidate the tickets if the "
                    "responsibility split does not make sense. The choice depends on which ticket "
                    'is the semantic "owner" of the file — typically the ticket that defines the '
                    "structure/contract should create it; other tickets that need the file "
                    "declare filesToBeReferenced + dependencies."
                ),
            )
        )
    return emissions


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


def check_files_to_be_referenced(spec: dict[str, Any]) -> list[CVEmission]:
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
            file_to_creator.setdefault(path, tid)

    emissions: list[CVEmission] = []
    for ticket in all_tickets:
        tid = ticket["id"]
        transitive = _build_transitive_deps(tid, adj, dep_cache)
        for path in ticket.get("filesToBeReferenced") or []:
            creator = file_to_creator.get(path)
            if creator and creator != tid and creator not in transitive:
                emissions.append(
                    CVEmission(
                        finding=CrossValidationFinding(
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
                        ),
                        guidance=(
                            f'Ticket "{tid}" lists "{path}" in filesToBeReferenced, and ticket '
                            f'"{creator}" creates/modifies that file, but "{tid}" does not '
                            f"declare dependencies on the creator. Broken reference at runtime — "
                            f'when an agent executes "{tid}", the topological order does not '
                            f'guarantee that "{creator}" ran first. Resolve in one of three '
                            f'ways: (1) add "{creator}" to "{tid}".dependencies to force the '
                            "correct order, OR (2) move the file creation to a ticket that is "
                            f'already a predecessor of "{tid}", OR (3) remove filesToBeReferenced '
                            "if the file is not actually needed by this ticket."
                        ),
                    )
                )
            elif not creator:
                emissions.append(
                    CVEmission(
                        finding=CrossValidationFinding(
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
                        ),
                        guidance=(
                            f'Ticket "{tid}" lists "{path}" in filesToBeReferenced, but no ticket '
                            f"creates or modifies that file in the spec. Broken reference at "
                            f'runtime — when an agent executes "{tid}", the file will not exist. '
                            "Resolve in one of three ways: (1) add filesToBeCreated or "
                            f"filesToBeModified containing this path on some ticket that precedes "
                            f'"{tid}" via dependencies, OR (2) declare dependencies on an '
                            "existing ticket that creates/modifies the file (if the work already "
                            "exists but isn't connected), OR (3) remove filesToBeReferenced if "
                            "the file is not actually needed by this ticket."
                        ),
                    )
                )
    return emissions
