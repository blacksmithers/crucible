"""Concurrent-modification check (invariante #6) —
``crucible.cross_validation.concurrent_modification``.

Same-file modifiers must be ORDERED by dependency reachability; only MUTUALLY
unreachable pairs are findings. Assertions are structural (category, field,
entity ids, operations, context keys, counts).
"""

from __future__ import annotations

from typing import Any

from crucible.cross_validation.concurrent_modification import check_concurrent_modification
from crucible.cross_validation.emission import CVEmission


def _ticket(tid: str, **fields: Any) -> dict[str, Any]:
    return {"id": tid, **fields}


def _deps(*ticket_ids: str) -> list[dict[str, str]]:
    return [{"ticketId": t, "type": "requires"} for t in ticket_ids]


def _spec(*tickets: dict[str, Any]) -> dict[str, Any]:
    return {"id": "spec-1", "epics": [{"id": "epic-1", "tickets": list(tickets)}]}


def _fields(emissions: list[CVEmission]) -> list[str]:
    return [e.finding.field for e in emissions]


# ---------------------------------------------------------------------------
# The finding shape
# ---------------------------------------------------------------------------
def test_mutually_unreachable_modifiers_are_a_finding() -> None:
    spec = _spec(
        _ticket("T2", filesToBeModified=["src/a.ts"]),
        _ticket("T1", filesToBeModified=["src/a.ts"]),
    )
    out = check_concurrent_modification(spec)
    assert len(out) == 1
    f = out[0].finding
    assert f.category == "concurrent-modification"
    assert f.severity == "error"
    assert f.field == "filesToBeModified:src/a.ts"
    assert f.entity_ids == ["T1", "T2"]
    assert f.primary_entity_id == "T1"
    assert f.operations == ["update_ticket"]


def test_context_carries_path_and_ticket_ids_and_no_wave_key() -> None:
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/a.ts"]),
    )
    context = check_concurrent_modification(spec)[0].finding.context
    assert context is not None
    assert context == {"path": "src/a.ts", "ticketIds": ["T1", "T2"]}
    assert "wave" not in context


def test_message_names_the_path_without_asserting_the_prose() -> None:
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/a.ts"]),
    )
    assert '"src/a.ts"' in check_concurrent_modification(spec)[0].finding.message


# ---------------------------------------------------------------------------
# Ordering by dependency reachability
# ---------------------------------------------------------------------------
def test_direct_dependency_orders_the_pair() -> None:
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/a.ts"], dependencies=_deps("T1")),
    )
    assert check_concurrent_modification(spec) == []


def test_transitive_dependency_orders_the_pair() -> None:
    # T3 → T2 → T1: the two modifiers (T1, T3) are ordered through T2.
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", dependencies=_deps("T1")),
        _ticket("T3", filesToBeModified=["src/a.ts"], dependencies=_deps("T2")),
    )
    assert check_concurrent_modification(spec) == []


def test_reachability_is_direction_agnostic() -> None:
    # The earlier-declared ticket depending on the later one is just as ordered.
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"], dependencies=_deps("T2")),
        _ticket("T2", filesToBeModified=["src/a.ts"]),
    )
    assert check_concurrent_modification(spec) == []


def test_a_sibling_dependency_does_not_order_the_pair() -> None:
    # Both modifiers depend on a common root, but neither reaches the other.
    spec = _spec(
        _ticket("T0"),
        _ticket("T1", filesToBeModified=["src/a.ts"], dependencies=_deps("T0")),
        _ticket("T2", filesToBeModified=["src/a.ts"], dependencies=_deps("T0")),
    )
    out = check_concurrent_modification(spec)
    assert len(out) == 1
    assert out[0].finding.entity_ids == ["T1", "T2"]


def test_only_the_unordered_participants_are_listed() -> None:
    # T1 → T2 is ordered; T3 is unreachable from both → the finding names the
    # tickets that take part in at least one unordered pair.
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/a.ts"], dependencies=_deps("T1")),
        _ticket("T3", filesToBeModified=["src/a.ts"]),
    )
    out = check_concurrent_modification(spec)
    assert len(out) == 1
    assert out[0].finding.entity_ids == ["T1", "T2", "T3"]


def test_a_fully_chained_trio_is_clean() -> None:
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/a.ts"], dependencies=_deps("T1")),
        _ticket("T3", filesToBeModified=["src/a.ts"], dependencies=_deps("T2")),
    )
    assert check_concurrent_modification(spec) == []


# ---------------------------------------------------------------------------
# Modifier collection
# ---------------------------------------------------------------------------
def test_a_single_modifier_is_never_a_finding() -> None:
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/b.ts"]),
    )
    assert check_concurrent_modification(spec) == []


def test_the_same_ticket_listing_a_path_twice_is_deduplicated() -> None:
    spec = _spec(_ticket("T1", filesToBeModified=["src/a.ts", "src/a.ts"]))
    assert check_concurrent_modification(spec) == []


def test_created_and_referenced_paths_are_not_considered() -> None:
    spec = _spec(
        _ticket("T1", filesToBeCreated=["src/a.ts"], filesToBeReferenced=["src/b.ts"]),
        _ticket("T2", filesToBeCreated=["src/a.ts"], filesToBeReferenced=["src/b.ts"]),
    )
    assert check_concurrent_modification(spec) == []


def test_modifiers_are_collected_across_epics() -> None:
    spec = {
        "id": "spec-1",
        "epics": [
            {"id": "e1", "tickets": [_ticket("T1", filesToBeModified=["src/a.ts"])]},
            {"id": "e2", "tickets": [_ticket("T2", filesToBeModified=["src/a.ts"])]},
        ],
    }
    out = check_concurrent_modification(spec)
    assert len(out) == 1
    assert out[0].finding.entity_ids == ["T1", "T2"]


def test_one_finding_per_path_in_first_declaration_order() -> None:
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/z.ts", "src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/a.ts", "src/z.ts"]),
    )
    out = check_concurrent_modification(spec)
    assert _fields(out) == ["filesToBeModified:src/z.ts", "filesToBeModified:src/a.ts"]


def test_empty_spec_is_clean() -> None:
    assert check_concurrent_modification({"id": "spec-1"}) == []
    assert check_concurrent_modification({"id": "spec-1", "epics": []}) == []
