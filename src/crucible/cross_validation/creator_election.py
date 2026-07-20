"""Creator-election ANALYZER (pure, structured value — no findings, no prose).

Port of ``cross-validation/creator-election.ts`` (MB.13.1).

When the cross_validation gate denies with the file-provenance blocker set, the
bare per-line findings ("modifies X but no ticket creates it") leave the actor
patching one file at a time and rediscovering the rest — the provenance ↔
ordering ↔ acyclicity TRILEMMA. This analyzer COMPUTES the whole resolution as a
pure function over the spec: for each ORPHAN shared file (touched by ≥1 ticket,
created by no ticket, and not grep-existing), it elects the topologically
EARLIEST toucher as the creator, emits the exact ``modifier → creator``
dependencies for the other touchers, and VERIFIES — per file, greedily in rank
order — that the union with the existing DAG stays acyclic.

Reuses the two existing primitives wholesale (no new invariant, a new synthesis):

- :func:`~.file_provenance.build_file_provenance_maps` — its ``created_paths``
  set decides "created by no ticket".
- :func:`~.dependency_graph.detect_cycles` — the acyclicity check, run on a
  SYNTHETIC spec whose ``ticket.dependencies`` = the candidate union
  (``detect_cycles`` takes a spec and derives edges from ``dependencies``, not an
  edge-list). In crucible it returns ``list[CVEmission]``, so acyclicity is
  ``len(detect_cycles(...)) == 0`` — mirroring the TS ``.length === 0``.

⚠ ``build_file_provenance_maps`` tracks created/modified only — NOT
``filesToBeReferenced``. So the per-file touch map here computes the
``references`` role itself: a file REFERENCED (but never created) with no grep
backing is ALSO an orphan.

⚠ DETERMINISM: the TS iterates ``Map``s in INSERTION order and that order is
observable in the output (toucher order within equal ranks, candidate order
before the final by-file sort). The Python port therefore uses ``dict`` — never
``set`` — for the toucher/role maps.

PURE — no I/O, no formatting; RETURNS a structured value rather than emitting a
finding (the finding seam flattens to ``{category, message}`` and would drop the
structure).
"""

from __future__ import annotations

import sys
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field
from typing import Any, Literal

from .dependency_graph import detect_cycles
from .file_provenance import build_file_provenance_maps

#: How a ticket touches a file. An orphan is never ``creates`` (by definition).
ToucherRole = Literal["creates", "modifies", "references"]

#: The per-file resolution status:
#:
#: - ``clean``    — ``required_deps ∪ (existing ∪ already-accepted clean deps)``
#:                  is acyclic (a DAG); the election is safe to apply.
#: - ``conflict`` — adding the elected ``modifier → creator`` deps closes a cycle
#:                  (an EXISTING dep already contradicts the natural order, e.g.
#:                  points ``creator → modifier``) → hand to ``get_ticket``, do
#:                  NOT auto-apply.
CreatorPlanStatus = Literal["clean", "conflict"]


@dataclass(frozen=True)
class FileToucher:
    """A ticket that touches the orphan file, tagged with its
    (highest-precedence) role."""

    ticket_id: str
    role: ToucherRole


@dataclass(frozen=True)
class RequiredDep:
    """One auto-derived dependency: ``from_ticket_id`` REQUIRES ``to_ticket_id``
    (the elected creator). Same directional convention as the structural cycle
    edges (from REQUIRES to)."""

    from_ticket_id: str
    to_ticket_id: str


@dataclass(frozen=True)
class FileCreatorPlan:
    """The computed resolution for ONE orphan shared file."""

    #: The orphan path (touched by ≥1 ticket, created by no ticket, not grep-existing).
    file: str
    #: Every ticket that touches the file, by role, sorted by rank then id.
    touchers: list[FileToucher]
    #: The elected creator: the min-rank toucher (tie-break ticket.order, then id).
    elected_creator: str
    #: The rank basis for the election (e.g. "Epic epic-1 order 2 / ticket order 1").
    reason: str
    #: ``{T requires elected_creator}`` for every OTHER toucher T (sorted by
    #: from_ticket_id). Empty for a single-toucher orphan (elect-and-flip
    #: ``modifies``/``references`` → ``creates``, no deps).
    required_deps: list[RequiredDep]
    #: ``clean`` (union acyclic → apply) or ``conflict`` (existing dep contradicts).
    status: CreatorPlanStatus


@dataclass(frozen=True)
class CreatorElectionResult:
    """The structured plan value the analyzer returns (NOT a formatted string,
    NOT a finding)."""

    plans: list[FileCreatorPlan] = field(default_factory=list)


@dataclass(frozen=True)
class _DepEdge:
    """A directed dependency edge ``from_id`` REQUIRES ``to_id`` (mirrors how
    :func:`detect_cycles` reads deps). ``from`` is a Python keyword, hence the
    ``_id`` suffixes."""

    from_id: str
    to_id: str


@dataclass(frozen=True)
class _Candidate:
    """A plan before the per-file acyclicity pass decides its ``status``; carries
    the internal ``elected_rank`` (dropped from the returned plan)."""

    file: str
    touchers: list[FileToucher]
    elected_creator: str
    reason: str
    required_deps: list[RequiredDep]
    elected_rank: int


# Role precedence when a single ticket touches a file in more than one role: a
# creation outranks a modify outranks a reference. (An orphan never has a
# `creates` toucher — the file is created by no ticket — but the precedence is
# complete.)
ROLE_PRECEDENCE: dict[ToucherRole, int] = {
    "creates": 0,
    "modifies": 1,
    "references": 2,
}

# Sentinel for an ABSENT `epic.order` / `ticket.order` (both optional): sort
# after every defined order, then the ticket-id tie-break makes the rank TOTAL.
# (The TS uses `Number.MAX_SAFE_INTEGER`; only its RELATIVE position matters.)
ORDER_ABSENT = sys.maxsize


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


def _order_or_absent(order: Any) -> int:
    """``order ?? ORDER_ABSENT`` — ``None`` (absent) sorts last; ``0`` is a
    legitimate order and must NOT be coerced (the TS ``??`` is null-ish only)."""
    return ORDER_ABSENT if order is None else int(order)


def elect_file_creators(
    spec: dict[str, Any],
    existing_files: AbstractSet[str] | None = None,
) -> CreatorElectionResult:
    """Elect a creator for every orphan shared file + the exact modifier→creator
    deps, verified acyclic per file in rank order. Pure — no I/O, no formatting.

    :param spec: the specification under gate.
    :param existing_files: the grep-existing real-repo file set (the CPS
        double-call, pass-2). A file present here is NOT an orphan (it exists),
        so it gets no plan entry. ABSENT (``None``) → strict spec-internal model
        (every touched-but-uncreated file is an orphan).
    """
    all_tickets = _all_tickets(spec)

    # Single-valued provenance: `created_paths` decides "created by no ticket" —
    # a modify-only path is NOT in it (its `file_to_creator` standin does not
    # make it created), so it stays an orphan candidate.
    created_paths = build_file_provenance_maps(spec).created_paths

    # --- rank: a stable linearization over epic.order → ticket.order → id ------
    # Both orders are optional; ORDER_ABSENT + the id tie-break keep the rank
    # TOTAL. "Consistent with the current DAG" in the happy path; when it is NOT,
    # the per-file acyclicity check below flags the conflict.
    ticket_by_id: dict[str, dict[str, Any]] = {}
    epic_order_by_id: dict[str, Any] = {}
    for epic in spec.get("epics") or []:
        epic_order_by_id[epic["id"]] = epic.get("order")
        for ticket in epic.get("tickets") or []:
            ticket_by_id[ticket["id"]] = ticket

    def epic_order_of(ticket: dict[str, Any]) -> Any:
        """`epicOrderById.get(ticket.epicId)` — ``None`` both for an unknown epic
        and for a known epic with no ``order`` (the TS collapses the same way)."""
        epic_id = ticket.get("epicId")
        if not isinstance(epic_id, str):
            return None
        return epic_order_by_id.get(epic_id)

    ordered_tickets = sorted(
        all_tickets,
        key=lambda t: (
            _order_or_absent(epic_order_of(t)),
            _order_or_absent(t.get("order")),
            t["id"],
        ),
    )
    rank_by_id: dict[str, int] = {t["id"]: i for i, t in enumerate(ordered_tickets)}

    def rank_of(ticket_id: str) -> int:
        return rank_by_id.get(ticket_id, ORDER_ABSENT)

    # --- per-file touch map (computes the `references` role itself) ------------
    # Only `modifies` / `references` matter: a `creates` path is never an orphan.
    # dict (not set): the insertion order of the touchers is observable output.
    file_touchers: dict[str, dict[str, ToucherRole]] = {}

    def add_toucher(file: str, ticket_id: str, role: ToucherRole) -> None:
        roles = file_touchers.setdefault(file, {})
        existing = roles.get(ticket_id)
        if existing is None or ROLE_PRECEDENCE[role] < ROLE_PRECEDENCE[existing]:
            # Re-assigning an existing key keeps its original position, as the
            # TS `Map.set` does.
            roles[ticket_id] = role

    for ticket in all_tickets:
        for path in ticket.get("filesToBeModified") or []:
            add_toucher(path, ticket["id"], "modifies")
        for path in ticket.get("filesToBeReferenced") or []:
            add_toucher(path, ticket["id"], "references")

    # --- candidate plans (status decided in the acyclicity pass below) ---------
    candidates: list[_Candidate] = []
    for file, roles in file_touchers.items():
        # Orphan = touched ∧ created by no ticket ∧ not grep-existing.
        if file in created_paths:
            continue
        if existing_files is not None and file in existing_files:
            continue

        toucher_ids = list(roles.keys())
        elected_creator = toucher_ids[0]
        for tid in toucher_ids:
            if rank_of(tid) < rank_of(elected_creator):
                elected_creator = tid

        touchers = sorted(
            (FileToucher(ticket_id=tid, role=roles[tid]) for tid in toucher_ids),
            key=lambda t: (rank_of(t.ticket_id), t.ticket_id),
        )

        required_deps = [
            RequiredDep(from_ticket_id=tid, to_ticket_id=elected_creator)
            for tid in sorted(tid for tid in toucher_ids if tid != elected_creator)
        ]

        elected_ticket = ticket_by_id.get(elected_creator)
        epic_id = elected_ticket.get("epicId") if elected_ticket is not None else None
        epic_order = epic_order_of(elected_ticket) if elected_ticket is not None else None
        ticket_order = elected_ticket.get("order") if elected_ticket is not None else None
        reason = (
            f"Epic {epic_id if epic_id is not None else 'unknown'} "
            f"order {epic_order if epic_order is not None else 'unset'} "
            f"/ ticket order {ticket_order if ticket_order is not None else 'unset'}"
        )

        candidates.append(
            _Candidate(
                file=file,
                touchers=touchers,
                elected_creator=elected_creator,
                reason=reason,
                required_deps=required_deps,
                elected_rank=rank_of(elected_creator),
            )
        )

    # --- acyclicity: PER FILE, greedily in elected-creator rank order ----------
    # `status` is per-file (not one global boolean). Process the orphans by their
    # elected creator's rank; accept a file's deps only if the union with the
    # existing DAG + the already-accepted clean deps stays acyclic. A cycle drops
    # ONLY that file's auto-deps (the others stay clean) — a mixed spec resolves
    # the clean files and flags only the contradictory ones.
    existing_edges: list[_DepEdge] = [
        _DepEdge(from_id=ticket["id"], to_id=dep["ticketId"])
        for ticket in all_tickets
        for dep in (ticket.get("dependencies") or [])
    ]
    all_ticket_ids = [t["id"] for t in all_tickets]

    accepted_edges: list[_DepEdge] = []
    ordered_candidates = sorted(candidates, key=lambda c: (c.elected_rank, c.file))

    status_by_file: dict[str, CreatorPlanStatus] = {}
    for candidate in ordered_candidates:
        if not candidate.required_deps:
            # Single-toucher orphan (elect-and-flip `modifies`/`references` →
            # `creates`): no added edge → trivially acyclic.
            status_by_file[candidate.file] = "clean"
            continue
        candidate_edges = [
            _DepEdge(from_id=d.from_ticket_id, to_id=d.to_ticket_id)
            for d in candidate.required_deps
        ]
        synthetic = _build_synthetic_spec(
            all_ticket_ids, [*existing_edges, *accepted_edges, *candidate_edges]
        )
        if len(detect_cycles(synthetic)) == 0:
            accepted_edges.extend(candidate_edges)
            status_by_file[candidate.file] = "clean"
        else:
            status_by_file[candidate.file] = "conflict"

    plans = sorted(
        (
            FileCreatorPlan(
                file=c.file,
                touchers=c.touchers,
                elected_creator=c.elected_creator,
                reason=c.reason,
                required_deps=c.required_deps,
                status=status_by_file.get(c.file, "clean"),
            )
            for c in candidates
        ),
        key=lambda p: p.file,
    )

    return CreatorElectionResult(plans=plans)


def _build_synthetic_spec(ticket_ids: list[str], edges: list[_DepEdge]) -> dict[str, Any]:
    """A minimal spec carrying only what :func:`detect_cycles` reads: the ticket
    ids and their ``dependencies`` (``{"ticketId": ...}``). Every ticket id is
    present (so isolated nodes exist); the ``edges`` become each ticket's
    ``dependencies`` (``from`` requires ``to``).

    Needed because ``detect_cycles`` takes a spec, not an edge-list, and its DFS
    is a private closure.
    """
    deps_by_from: dict[str, list[dict[str, str]]] = {tid: [] for tid in ticket_ids}
    for edge in edges:
        deps_by_from.setdefault(edge.from_id, []).append(
            {"ticketId": edge.to_id, "type": "requires"}
        )
    tickets = [{"id": tid, "dependencies": deps_by_from.get(tid) or []} for tid in ticket_ids]
    return {"epics": [{"tickets": tickets}]}
