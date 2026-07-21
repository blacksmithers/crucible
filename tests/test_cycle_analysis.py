"""Cycle-resolution analyzer (MB.12.1) — ``crucible.cross_validation.cycle_analysis``.

Pure evidence packets: file-backing, epic relationship + order basis, the
precedence hint (file evidence dominates order) and the three shape tags.
"""

from __future__ import annotations

from typing import Any

from crucible.cross_validation.cycle_analysis import (
    StructuralCycle,
    StructuralCycleEdge,
    analyze_cycle_edges,
)


def _ticket(tid: str, epic_id: str = "e1", **fields: Any) -> dict[str, Any]:
    return {"id": tid, "epicId": epic_id, **fields}


def _spec(*epics: dict[str, Any]) -> dict[str, Any]:
    return {"id": "spec-1", "epics": list(epics)}


def _epic(epic_id: str, *tickets: dict[str, Any], order: int | None = None) -> dict[str, Any]:
    epic: dict[str, Any] = {"id": epic_id, "tickets": list(tickets)}
    if order is not None:
        epic["order"] = order
    return epic


def _cycle(*pairs: tuple[str, str]) -> StructuralCycle:
    return StructuralCycle(
        cycle_path=[StructuralCycleEdge(from_ticket_id=a, to_ticket_id=b) for a, b in pairs]
    )


# ---------------------------------------------------------------------------
# File signal
# ---------------------------------------------------------------------------
def test_edge_is_file_backed_when_from_consumes_a_file_to_creates() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", filesToBeModified=["src/a.ts"]),
            _ticket("T2", filesToBeCreated=["src/a.ts"]),
        )
    )
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"))], spec)
    edge = analysis.edges[0]
    assert edge.from_ticket_id == "T1"
    assert edge.to_ticket_id == "T2"
    assert edge.file_backed is True
    assert edge.justifying_files == ["src/a.ts"]
    assert edge.precedence_hint == "forward"
    assert analysis.shape_tag == "all-file-backed"


def test_reverse_edge_of_a_file_dependency_is_not_file_backed_and_hints_reverse() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", filesToBeModified=["src/a.ts"]),
            _ticket("T2", filesToBeCreated=["src/a.ts"]),
        )
    )
    [analysis] = analyze_cycle_edges([_cycle(("T2", "T1"))], spec)
    edge = analysis.edges[0]
    assert edge.file_backed is False
    assert edge.justifying_files == []
    assert edge.precedence_hint == "reverse"
    assert analysis.shape_tag == "none-file-backed"


def test_a_modifier_standin_provides_the_file_when_nobody_creates_it() -> None:
    # No creator → the FIRST modifier is the provider (MB.10 rule, reused).
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", filesToBeModified=["src/a.ts"]),
            _ticket("T2", filesToBeReferenced=["src/a.ts"]),
        )
    )
    [analysis] = analyze_cycle_edges([_cycle(("T2", "T1"))], spec)
    assert analysis.edges[0].file_backed is True
    assert analysis.edges[0].justifying_files == ["src/a.ts"]


def test_justifying_files_union_references_and_modifications_sorted_and_deduped() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket(
                "T1",
                filesToBeReferenced=["src/z.ts", "src/a.ts"],
                filesToBeModified=["src/a.ts", "src/m.ts"],
            ),
            _ticket("T2", filesToBeCreated=["src/z.ts", "src/a.ts", "src/m.ts"]),
        )
    )
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"))], spec)
    assert analysis.edges[0].justifying_files == ["src/a.ts", "src/m.ts", "src/z.ts"]


def test_created_files_alone_do_not_back_an_edge() -> None:
    # `filesToBeCreated` is a PROVIDER role, never a consumption.
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", filesToBeCreated=["src/a.ts"]),
            _ticket("T2", filesToBeCreated=["src/b.ts"]),
        )
    )
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"))], spec)
    assert analysis.edges[0].file_backed is False


# ---------------------------------------------------------------------------
# Epic signal + order basis
# ---------------------------------------------------------------------------
def test_same_epic_uses_the_ticket_order_basis() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", order=1),
            _ticket("T2", order=2),
            order=7,
        )
    )
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"))], spec)
    edge = analysis.edges[0]
    assert edge.epic_relationship == "same-epic"
    assert edge.from_epic_id == "e1"
    assert edge.to_epic_id == "e1"
    assert edge.order_basis == "ticket"
    assert (edge.from_order, edge.to_order) == (1, 2)


def test_different_epic_uses_the_epic_order_basis() -> None:
    spec = _spec(
        _epic("e1", _ticket("T1", epic_id="e1", order=9), order=1),
        _epic("e2", _ticket("T2", epic_id="e2", order=3), order=2),
    )
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"))], spec)
    edge = analysis.edges[0]
    assert edge.epic_relationship == "different-epic"
    assert edge.from_epic_id == "e1"
    assert edge.to_epic_id == "e2"
    assert edge.order_basis == "epic"
    assert (edge.from_order, edge.to_order) == (1, 2)


def test_a_missing_epic_id_degrades_to_different_epic() -> None:
    spec = _spec(
        _epic("e1", {"id": "T1", "order": 1}, {"id": "T2", "order": 2}, order=4),
    )
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"))], spec)
    edge = analysis.edges[0]
    assert edge.epic_relationship == "different-epic"
    assert (edge.from_epic_id, edge.to_epic_id) == (None, None)
    assert edge.order_basis == "epic"
    assert (edge.from_order, edge.to_order) == (None, None)
    assert edge.precedence_hint == "ambiguous"


def test_unknown_ticket_ids_produce_an_empty_evidence_packet() -> None:
    spec = _spec(_epic("e1", _ticket("T1")))
    [analysis] = analyze_cycle_edges([_cycle(("ghost-a", "ghost-b"))], spec)
    edge = analysis.edges[0]
    assert edge.file_backed is False
    assert edge.justifying_files == []
    assert edge.epic_relationship == "different-epic"
    assert (edge.from_order, edge.to_order) == (None, None)
    assert edge.precedence_hint == "ambiguous"


# ---------------------------------------------------------------------------
# Precedence hint
# ---------------------------------------------------------------------------
def test_order_decides_the_hint_when_there_is_no_file_evidence() -> None:
    spec = _spec(_epic("e1", _ticket("T1", order=1), _ticket("T2", order=2)))
    forward_edge = analyze_cycle_edges([_cycle(("T2", "T1"))], spec)[0].edges[0]
    reverse_edge = analyze_cycle_edges([_cycle(("T1", "T2"))], spec)[0].edges[0]
    # `to` earlier ⇒ the edge agrees with the natural order.
    assert forward_edge.precedence_hint == "forward"
    # `from` earlier ⇒ the edge points backwards.
    assert reverse_edge.precedence_hint == "reverse"


def test_equal_or_absent_orders_are_ambiguous() -> None:
    equal = _spec(_epic("e1", _ticket("T1", order=3), _ticket("T2", order=3)))
    absent = _spec(_epic("e1", _ticket("T1"), _ticket("T2")))
    assert analyze_cycle_edges([_cycle(("T1", "T2"))], equal)[0].edges[0].precedence_hint == (
        "ambiguous"
    )
    assert analyze_cycle_edges([_cycle(("T1", "T2"))], absent)[0].edges[0].precedence_hint == (
        "ambiguous"
    )


def test_file_evidence_dominates_a_contradicting_order() -> None:
    # Order says T1 is earlier (⇒ reverse), but T1 consumes a file T2 creates
    # (⇒ forward). The file wins.
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", order=1, filesToBeModified=["src/a.ts"]),
            _ticket("T2", order=2, filesToBeCreated=["src/a.ts"]),
        )
    )
    edge = analyze_cycle_edges([_cycle(("T1", "T2"))], spec)[0].edges[0]
    assert edge.file_backed is True
    assert edge.precedence_hint == "forward"


def test_bidirectional_file_backing_is_ambiguous() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", order=1, filesToBeCreated=["src/a.ts"], filesToBeModified=["src/b.ts"]),
            _ticket("T2", order=2, filesToBeCreated=["src/b.ts"], filesToBeModified=["src/a.ts"]),
        )
    )
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"), ("T2", "T1"))], spec)
    assert [e.precedence_hint for e in analysis.edges] == ["ambiguous", "ambiguous"]
    assert [e.file_backed for e in analysis.edges] == [True, True]
    assert analysis.shape_tag == "all-file-backed"


# ---------------------------------------------------------------------------
# Shape tags + top-level shape of the result
# ---------------------------------------------------------------------------
def test_shape_tag_none_file_backed() -> None:
    spec = _spec(_epic("e1", _ticket("T1"), _ticket("T2")))
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"), ("T2", "T1"))], spec)
    assert analysis.shape_tag == "none-file-backed"
    assert all(e.file_backed is False for e in analysis.edges)


def test_shape_tag_one_file_backed_is_the_mixed_case() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", filesToBeModified=["src/a.ts"]),
            _ticket("T2", filesToBeCreated=["src/a.ts"]),
        )
    )
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"), ("T2", "T1"))], spec)
    assert [e.file_backed for e in analysis.edges] == [True, False]
    assert analysis.shape_tag == "one-file-backed"


def test_shape_tag_generalizes_to_a_three_hop_cycle() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", filesToBeModified=["src/a.ts"]),
            _ticket("T2", filesToBeCreated=["src/a.ts"], filesToBeModified=["src/b.ts"]),
            _ticket("T3", filesToBeCreated=["src/b.ts"]),
        )
    )
    [analysis] = analyze_cycle_edges([_cycle(("T1", "T2"), ("T2", "T3"), ("T3", "T1"))], spec)
    assert len(analysis.edges) == 3
    assert [e.file_backed for e in analysis.edges] == [True, True, False]
    assert analysis.shape_tag == "one-file-backed"


def test_an_edgeless_cycle_is_none_file_backed() -> None:
    [analysis] = analyze_cycle_edges([_cycle()], _spec(_epic("e1")))
    assert analysis.edges == []
    assert analysis.shape_tag == "none-file-backed"


def test_analyses_preserve_input_order_and_cycle_paths() -> None:
    spec = _spec(_epic("e1", _ticket("T1"), _ticket("T2"), _ticket("T3")))
    cycles = [_cycle(("T1", "T2")), _cycle(("T2", "T3"), ("T3", "T2"))]
    analyses = analyze_cycle_edges(cycles, spec)
    assert len(analyses) == 2
    assert analyses[0].cycle_path == cycles[0].cycle_path
    assert analyses[1].cycle_path == cycles[1].cycle_path
    assert [len(a.edges) for a in analyses] == [1, 2]


def test_no_cycles_yields_no_analyses() -> None:
    assert analyze_cycle_edges([], _spec(_epic("e1", _ticket("T1")))) == []
