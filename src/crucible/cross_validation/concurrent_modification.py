"""Concurrent-modification cross-validation check (emissions).

Port of ``cross-validation/concurrent-modification.ts`` — invariante #6
(MB.10.4), rewritten OFF the wave engine onto dependency reachability.
Supersedes the wave-literal ``wave-concurrent-modification``.
"""

from __future__ import annotations

from typing import Any

from ..types.result import CrossValidationFinding
from .emission import CVEmission
from .file_provenance import build_transitive_deps


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


def check_concurrent_modification(spec: dict[str, Any]) -> list[CVEmission]:
    """Two tickets that modify the same file must be ORDERED by an explicit
    dependency path: one must be (transitively) reachable from the other in the
    dependency DAG. When a pair of same-file modifiers is MUTUALLY UNREACHABLE
    (neither reaches the other), their edits are unordered → concurrent
    modification → error.

    Reachability is the SAME primitive as invariante #2 (consume-ordered, see
    :func:`build_transitive_deps`) and is robust to unrelated dependency edits.

    Disposition: rollback (``operations: ['update_ticket']``) — the fix is ticket
    REWORK (merge the modifiers into one ticket, or split the file so each ticket
    owns a distinct path), NOT "just add a dependency".
    """
    all_tickets = _all_tickets(spec)

    adj: dict[str, list[str]] = {}
    for ticket in all_tickets:
        adj[ticket["id"]] = [d["ticketId"] for d in (ticket.get("dependencies") or [])]

    # path → tickets that modify it (stable declaration order, de-duplicated).
    file_to_modifiers: dict[str, list[str]] = {}
    for ticket in all_tickets:
        tid = ticket["id"]
        for path in ticket.get("filesToBeModified") or []:
            modifiers = file_to_modifiers.setdefault(path, [])
            if tid not in modifiers:
                modifiers.append(tid)

    dep_cache: dict[str, set[str]] = {}

    def reaches(from_id: str, to_id: str) -> bool:
        return to_id in build_transitive_deps(from_id, adj, dep_cache)

    emissions: list[CVEmission] = []
    for path, modifiers in file_to_modifiers.items():
        if len(modifiers) < 2:
            continue

        # Every ticket that participates in at least one mutually-unreachable
        # pair on this path (neither ticket reaches the other in the dep DAG).
        unordered: set[str] = set()
        for i in range(len(modifiers)):
            for j in range(i + 1, len(modifiers)):
                a = modifiers[i]
                b = modifiers[j]
                if not reaches(a, b) and not reaches(b, a):
                    unordered.add(a)
                    unordered.add(b)
        if not unordered:
            continue

        sorted_ids = sorted(unordered)
        joined = ", ".join(sorted_ids)
        quoted = " and ".join(f'"{t}"' for t in sorted_ids)
        emissions.append(
            CVEmission(
                finding=CrossValidationFinding(
                    category="concurrent-modification",
                    severity="error",
                    field=f"filesToBeModified:{path}",
                    message=(
                        f'Tickets [{joined}] modify the same file "{path}" but are mutually '
                        f"dependency-independent (no ordering path exists between them)"
                    ),
                    entity_ids=sorted_ids,
                    primary_entity_id=sorted_ids[0],
                    operations=["update_ticket"],
                    context={"path": path, "ticketIds": sorted_ids},
                ),
                guidance=(
                    f'Tickets {quoted} all modify "{path}", but no dependency path orders them '
                    f"relative to each other in the dependency DAG — their edits to the same "
                    f"file are unordered and mutually independent."
                ),
            )
        )

    return emissions
