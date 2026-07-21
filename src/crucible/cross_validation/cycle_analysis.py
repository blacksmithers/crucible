"""Cycle-resolution ANALYZER — pure, structured, finding-free.

When the ``create_dependencies`` batch pre-check denies with ``cycle_detected``,
the bare "remove the offending edge" guidance names no specific edge and gives
no basis for the decision. This analyzer turns each cyclic edge into an EVIDENCE
packet the lifecycle deny renders so the agent can JUDGE which
dependency is real — INDICATIVE, never auto-cutting.

For each edge ``from → to`` on a detected cycle (``from REQUIRES to``), it
computes:

- **file**  — is the edge grounded in a file? ``from → to`` is file-backed ⇔
  ``from`` CONSUMES (``filesToBeReferenced ∪ filesToBeModified``) a file whose
  single-valued PROVIDER is ``to``. Provider(f) = ``file_to_creator[f]`` = the
  in-spec CREATOR (``filesToBeCreated``), or — for a brownfield file no ticket
  creates — the FIRST ticket that modifies it (the standin). This is exactly
  the consume-ordered invariant (#2), reused (via
  :func:`~crucible.cross_validation.file_provenance.build_file_provenance_maps`)
  — no new rule.
- **epic**  — are ``from`` and ``to`` in the SAME epic or DIFFERENT epics?
- **order** — same-epic → the two tickets' ``order``; cross-epic → the two
  epics' ``order`` (``spec.epics[].order``). The earlier one is the natural
  predecessor.
- **hint**  — the natural-precedence direction the evidence favors:
  file-grounded direction wins; else the order-earlier side is the predecessor;
  else ``ambiguous``.

The input is a validator-native structural edge-list, NOT lifecycle's
``DetectedCycle``: the lifecycle caller maps ``batch.cycles`` (whose
``cyclePath`` is already ``{fromTicketId,toTicketId}[]``) into
:class:`StructuralCycle`. It is PURE — no I/O, no formatting, no findings.

The analyzer emits ONLY file + epic + order evidence. It does NOT emit the
intra-batch-vs-persisted tag (its input carries no batch/persisted
distinction) — that tag is computed lifecycle-side and merged onto
each per-edge packet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .file_provenance import build_file_provenance_maps


@dataclass(frozen=True)
class StructuralCycleEdge:
    """A single directed cyclic edge: ``from REQUIRES to`` (same shape as
    lifecycle's ``DependencyEdge``)."""

    from_ticket_id: str
    to_ticket_id: str


@dataclass(frozen=True)
class StructuralCycle:
    """One detected cycle as an ordered edge list. ``cycle_path`` from
    ``findPath`` can be N>2 hops (not just a 2-cycle), so the analyzer handles
    any length."""

    cycle_path: list[StructuralCycleEdge]


EpicRelationship = Literal["same-epic", "different-epic"]

#: The order signal basis: same-epic edges compare ticket order, cross-epic
#: compare epic order.
OrderBasis = Literal["ticket", "epic"]

#: Which precedence direction the evidence favors for an edge ``from → to``:
#:
#: - ``forward``   — the edge's own direction (``to`` is the natural predecessor
#:   of ``from``); keep it.
#: - ``reverse``   — the OPPOSITE direction is favored (``from`` should precede
#:   ``to``); this edge is likely the spurious one.
#: - ``ambiguous`` — no file evidence either way and no distinguishing order (or
#:   a genuine bidirectional file contradiction).
PrecedenceHint = Literal["forward", "reverse", "ambiguous"]

#: Aggregate shape of a cycle, generalized to any length:
#:
#: - ``all-file-backed``  — EVERY edge is file-backed → a GENUINE circular file
#:   dependency (each ticket provides a distinct file the other consumes); the
#:   file assignment is contradictory → reshape files, don't drop an edge.
#: - ``none-file-backed`` — NO edge is file-backed → an invented ordering; lean
#:   on the epic/order signal + ``get_ticket``.
#: - ``one-file-backed``  — the MIXED case (≥1 but not all file-backed) → strong
#:   hint to keep the file-backed edge(s) and review the rest.
CycleShapeTag = Literal["all-file-backed", "none-file-backed", "one-file-backed"]


@dataclass(frozen=True)
class CycleEdgeEvidence:
    """The per-edge evidence packet."""

    from_ticket_id: str
    to_ticket_id: str
    #: True ⇔ ``from`` consumes a file whose single-valued provider is ``to``
    #: (this edge's direction).
    file_backed: bool
    #: The file(s) that justify the edge — ``from``-consumed paths whose
    #: provider is ``to``. Sorted.
    justifying_files: list[str]
    #: SAME epic vs DIFFERENT epics.
    epic_relationship: EpicRelationship
    from_epic_id: str | None
    to_epic_id: str | None
    #: ``ticket`` when same-epic (ticket ``order``), ``epic`` when cross-epic
    #: (epic ``order``).
    order_basis: OrderBasis
    #: ``from``'s order on the ``order_basis`` scale (``None`` when the
    #: entity/``order`` is absent).
    from_order: int | None
    #: ``to``'s order on the ``order_basis`` scale (``None`` when the
    #: entity/``order`` is absent).
    to_order: int | None
    #: The direction the file ∪ order evidence favors.
    precedence_hint: PrecedenceHint


@dataclass(frozen=True)
class CycleAnalysis:
    """The full analysis for one detected cycle."""

    cycle_path: list[StructuralCycleEdge]
    edges: list[CycleEdgeEvidence]
    shape_tag: CycleShapeTag


def analyze_cycle_edges(
    cycles: list[StructuralCycle],
    spec: dict[str, Any],
) -> list[CycleAnalysis]:
    """Analyze each detected cycle's edges against the spec's file-provenance
    model + the epic/ticket order, producing an indicative evidence packet per
    edge plus a per-cycle shape tag. Pure — no I/O, no formatting.
    """
    file_to_creator = build_file_provenance_maps(spec).file_to_creator
    ticket_by_id: dict[str, dict[str, Any]] = {}
    epic_order_by_id: dict[str, int | None] = {}
    for epic in spec.get("epics") or []:
        epic_order_by_id[epic["id"]] = epic.get("order")
        for ticket in epic.get("tickets") or []:
            ticket_by_id[ticket["id"]] = ticket

    def justifying_files_for(consumer_id: str, provider_id: str) -> list[str]:
        """The files ``consumer`` consumes (references ∪ modifies) whose
        single-valued provider is ``provider``."""
        consumer = ticket_by_id.get(consumer_id)
        if consumer is None:
            return []
        # Insertion-ordered de-duplication of the referenced ∪ modified paths.
        consumed: dict[str, None] = dict.fromkeys(
            [
                *(consumer.get("filesToBeReferenced") or []),
                *(consumer.get("filesToBeModified") or []),
            ]
        )
        files = [path for path in consumed if file_to_creator.get(path) == provider_id]
        return sorted(files)

    analyses: list[CycleAnalysis] = []
    for cycle in cycles:
        edges: list[CycleEdgeEvidence] = []
        for edge in cycle.cycle_path:
            from_ticket_id, to_ticket_id = edge.from_ticket_id, edge.to_ticket_id
            from_ticket = ticket_by_id.get(from_ticket_id)
            to_ticket = ticket_by_id.get(to_ticket_id)

            # ---- file signal (this edge's own direction: from → to) ----
            justifying_files = justifying_files_for(from_ticket_id, to_ticket_id)
            file_backed = len(justifying_files) > 0
            # The reverse edge's file backing (to consumes a file from provides) —
            # used only to orient the precedence hint (a genuine bidirectional file
            # dependency is contradictory → ambiguous, deferred to the
            # `all-file-backed` shape tag).
            reverse_file_backed = len(justifying_files_for(to_ticket_id, from_ticket_id)) > 0

            # ---- epic signal ----
            from_epic_id = from_ticket.get("epicId") if from_ticket is not None else None
            to_epic_id = to_ticket.get("epicId") if to_ticket is not None else None
            epic_relationship: EpicRelationship = (
                "same-epic"
                if from_epic_id is not None
                and to_epic_id is not None
                and from_epic_id == to_epic_id
                else "different-epic"
            )

            # ---- order signal ----
            order_basis: OrderBasis = "ticket" if epic_relationship == "same-epic" else "epic"
            if order_basis == "ticket":
                from_order = from_ticket.get("order") if from_ticket is not None else None
                to_order = to_ticket.get("order") if to_ticket is not None else None
            else:
                from_order = (
                    epic_order_by_id.get(from_epic_id) if from_epic_id is not None else None
                )
                to_order = epic_order_by_id.get(to_epic_id) if to_epic_id is not None else None

            # ---- natural-precedence hint (file ∪ order) ----
            precedence_hint = _resolve_hint(file_backed, reverse_file_backed, from_order, to_order)

            edges.append(
                CycleEdgeEvidence(
                    from_ticket_id=from_ticket_id,
                    to_ticket_id=to_ticket_id,
                    file_backed=file_backed,
                    justifying_files=justifying_files,
                    epic_relationship=epic_relationship,
                    from_epic_id=from_epic_id,
                    to_epic_id=to_epic_id,
                    order_basis=order_basis,
                    from_order=from_order,
                    to_order=to_order,
                    precedence_hint=precedence_hint,
                )
            )

        analyses.append(
            CycleAnalysis(
                cycle_path=cycle.cycle_path,
                edges=edges,
                shape_tag=_shape_tag_for(edges),
            )
        )

    return analyses


def _resolve_hint(
    forward_file_backed: bool,
    reverse_file_backed: bool,
    from_order: int | None,
    to_order: int | None,
) -> PrecedenceHint:
    """Precedence hint for an edge ``from → to``, file evidence taking priority
    over order:

    - file-grounded ONE way → that direction (both ways → ``ambiguous``, a real
      file contradiction the shape tag surfaces);
    - else order-earlier side is the natural predecessor (``to`` earlier →
      ``forward``, ``from`` earlier → ``reverse``);
    - else ``ambiguous``.
    """
    if forward_file_backed and not reverse_file_backed:
        return "forward"
    if reverse_file_backed and not forward_file_backed:
        return "reverse"
    if forward_file_backed and reverse_file_backed:
        return "ambiguous"
    if from_order is not None and to_order is not None and from_order != to_order:
        # Edge from → to means "to is the predecessor". The earlier side is the
        # natural predecessor: to earlier ⇒ the edge agrees (forward); from
        # earlier ⇒ reverse.
        return "forward" if to_order < from_order else "reverse"
    return "ambiguous"


def _shape_tag_for(edges: list[CycleEdgeEvidence]) -> CycleShapeTag:
    """Aggregate shape tag over a cycle's per-edge file classification,
    generalized to any cycle length: ``all-file-backed`` = every edge,
    ``none-file-backed`` = no edge, ``one-file-backed`` = the mixed remainder.
    """
    backed = len([e for e in edges if e.file_backed])
    if len(edges) > 0 and backed == len(edges):
        return "all-file-backed"
    if backed == 0:
        return "none-file-backed"
    return "one-file-backed"
