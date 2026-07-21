"""Unified file-provenance cross-validation (``crucible.cross_validation.file_provenance``).

Covers the four static invariants (#1 consume-exists, #2 consume-ordered,
#3 create-fresh, #5 no-delete-of-spec-touched), the folded single-creator check
(#4), the TRI-STATE ``existing_files`` semantics, ``compute_grep_candidates``
and ``build_file_provenance_maps``.

Assertions are structural (categories / operations / fields / entity ids /
counts / emission order) — never the guidance prose.
"""

from __future__ import annotations

from typing import Any

from crucible.config import load_defaults
from crucible.cross_validation.emission import CVEmission
from crucible.cross_validation.file_provenance import (
    FileProvenanceContext,
    build_file_provenance_maps,
    build_transitive_deps,
    check_file_consistency,
    check_file_provenance,
    compute_grep_candidates,
)

CONFIG = load_defaults()


def _ticket(tid: str, **fields: Any) -> dict[str, Any]:
    return {"id": tid, **fields}


def _deps(*ticket_ids: str) -> list[dict[str, str]]:
    return [{"ticketId": t, "type": "requires"} for t in ticket_ids]


def _spec(*tickets: dict[str, Any]) -> dict[str, Any]:
    return {"id": "spec-1", "epics": [{"id": "epic-1", "tickets": list(tickets)}]}


def _fields(emissions: list[CVEmission]) -> list[str]:
    return [e.finding.field for e in emissions]


def _categories(emissions: list[CVEmission]) -> list[str]:
    return [e.finding.category for e in emissions]


# ---------------------------------------------------------------------------
# invariante #1 — consume-exists, and the TRI-STATE `existing_files`
# ---------------------------------------------------------------------------
def test_consume_exists_absent_ctx_is_strict_spec_internal() -> None:
    spec = _spec(_ticket("T1", filesToBeModified=["src/a.ts"]))
    out = check_file_provenance(spec, CONFIG)
    assert len(out) == 1
    f = out[0].finding
    assert f.category == "file-provenance"
    assert f.severity == "error"
    assert f.field == "tickets[id=T1].filesToBeModified:src/a.ts"
    assert f.entity_ids == ["T1"]
    assert f.primary_entity_id == "T1"
    assert f.operations == ["create_ticket", "update_ticket"]


def test_consume_exists_ctx_with_none_matches_no_ctx_at_all() -> None:
    spec = _spec(_ticket("T1", filesToBeReferenced=["src/a.ts"]))
    without_ctx = check_file_provenance(spec, CONFIG)
    with_none = check_file_provenance(spec, CONFIG, FileProvenanceContext())
    with_explicit_none = check_file_provenance(
        spec, CONFIG, FileProvenanceContext(existing_files=None)
    )
    assert _fields(without_ctx) == _fields(with_none) == _fields(with_explicit_none)
    assert len(without_ctx) == 1


def test_consume_exists_empty_frozenset_means_grep_ran_and_confirmed_nothing() -> None:
    # PRESENT-but-empty is NOT the same state as ABSENT: it is positive evidence
    # that the path does not exist → still a real finding.
    spec = _spec(_ticket("T1", filesToBeDeleted=["src/gone.ts"]))
    out = check_file_provenance(spec, CONFIG, FileProvenanceContext(existing_files=frozenset()))
    assert len(out) == 1
    assert out[0].finding.field == "tickets[id=T1].filesToBeDeleted:src/gone.ts"
    assert out[0].finding.operations == ["create_ticket", "update_ticket"]


def test_consume_exists_populated_set_unions_with_created_paths() -> None:
    spec = _spec(
        _ticket("T1", filesToBeReferenced=["src/legacy.ts"], filesToBeModified=["src/other.ts"]),
    )
    ctx = FileProvenanceContext(existing_files=frozenset({"src/legacy.ts"}))
    out = check_file_provenance(spec, CONFIG, ctx)
    # Only the path grep did NOT find is reported.
    assert _fields(out) == ["tickets[id=T1].filesToBeModified:src/other.ts"]


def test_all_three_consumer_roles_are_checked_in_declaration_order() -> None:
    spec = _spec(
        _ticket(
            "T1",
            filesToBeReferenced=["r.ts"],
            filesToBeModified=["m.ts"],
            filesToBeDeleted=["d.ts"],
        )
    )
    out = check_file_provenance(spec, CONFIG)
    assert _fields(out) == [
        "tickets[id=T1].filesToBeReferenced:r.ts",
        "tickets[id=T1].filesToBeModified:m.ts",
        "tickets[id=T1].filesToBeDeleted:d.ts",
    ]
    assert set(_categories(out)) == {"file-provenance"}


def test_missing_existence_suppresses_the_ordering_finding_for_the_same_path() -> None:
    spec = _spec(_ticket("T1", filesToBeModified=["src/a.ts"]))
    out = check_file_provenance(spec, CONFIG)
    assert len(out) == 1
    assert out[0].finding.operations == ["create_ticket", "update_ticket"]


# ---------------------------------------------------------------------------
# invariante #2 — consume-ordered
# ---------------------------------------------------------------------------
def test_consume_ordered_missing_edge_is_an_error() -> None:
    spec = _spec(
        _ticket("T1", filesToBeCreated=["src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/a.ts"]),
    )
    out = check_file_provenance(spec, CONFIG)
    assert len(out) == 1
    f = out[0].finding
    assert f.category == "file-provenance"
    assert f.field == "tickets[id=T2].filesToBeModified:src/a.ts"
    assert f.entity_ids == ["T2"]
    assert f.primary_entity_id == "T2"
    assert f.operations == ["create_dependencies"]


def test_consume_ordered_direct_dependency_satisfies_it() -> None:
    spec = _spec(
        _ticket("T1", filesToBeCreated=["src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/a.ts"], dependencies=_deps("T1")),
    )
    assert check_file_provenance(spec, CONFIG) == []


def test_consume_ordered_transitive_dependency_satisfies_it() -> None:
    spec = _spec(
        _ticket("T1", filesToBeCreated=["src/a.ts"]),
        _ticket("T2", dependencies=_deps("T1")),
        _ticket("T3", filesToBeReferenced=["src/a.ts"], dependencies=_deps("T2")),
    )
    assert check_file_provenance(spec, CONFIG) == []


def test_consume_ordered_ignores_the_creator_consuming_its_own_file() -> None:
    spec = _spec(_ticket("T1", filesToBeCreated=["src/a.ts"], filesToBeModified=["src/a.ts"]))
    assert check_file_provenance(spec, CONFIG) == []


def test_consume_ordered_does_not_apply_to_deletions() -> None:
    # `filesToBeDeleted` is existence-only (not `ordered`) — the only finding
    # here is invariante #5, not a missing ordering edge.
    spec = _spec(
        _ticket("T1", filesToBeCreated=["src/a.ts"]),
        _ticket("T2", filesToBeDeleted=["src/a.ts"]),
    )
    out = check_file_provenance(spec, CONFIG)
    assert len(out) == 1
    assert out[0].finding.field == "tickets[id=T2].filesToBeDeleted:src/a.ts"
    assert out[0].finding.operations == ["update_ticket", "delete_ticket"]


def test_grep_provenance_needs_no_ordering_edge() -> None:
    # "src/a.ts" is modified by T1 (the standin provider) and referenced by T2
    # with no dependency between them — but grep says the file pre-exists, so
    # the ordering invariant does not apply.
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeReferenced=["src/a.ts"]),
    )
    assert check_file_provenance(spec, CONFIG) != []  # strict model: both consume-exists
    ctx = FileProvenanceContext(existing_files=frozenset({"src/a.ts"}))
    assert check_file_provenance(spec, CONFIG, ctx) == []


# ---------------------------------------------------------------------------
# invariante #3 — create-fresh
# ---------------------------------------------------------------------------
def test_create_fresh_is_a_noop_without_grep_evidence() -> None:
    spec = _spec(_ticket("T1", filesToBeCreated=["src/a.ts"]))
    assert check_file_provenance(spec, CONFIG) == []
    empty_grep = FileProvenanceContext(existing_files=frozenset())
    assert check_file_provenance(spec, CONFIG, empty_grep) == []


def test_create_fresh_fires_when_grep_confirms_the_path_exists() -> None:
    spec = _spec(_ticket("T1", filesToBeCreated=["src/a.ts"]))
    ctx = FileProvenanceContext(existing_files=frozenset({"src/a.ts"}))
    out = check_file_provenance(spec, CONFIG, ctx)
    assert len(out) == 1
    f = out[0].finding
    assert f.category == "file-provenance"
    assert f.field == "tickets[id=T1].filesToBeCreated:src/a.ts"
    assert f.entity_ids == ["T1"]
    assert f.operations == ["update_ticket"]


def test_create_fresh_is_emitted_after_the_consumer_roles_of_the_same_ticket() -> None:
    spec = _spec(
        _ticket("T1", filesToBeCreated=["src/a.ts"], filesToBeModified=["src/missing.ts"])
    )
    ctx = FileProvenanceContext(existing_files=frozenset({"src/a.ts"}))
    out = check_file_provenance(spec, CONFIG, ctx)
    assert _fields(out) == [
        "tickets[id=T1].filesToBeModified:src/missing.ts",
        "tickets[id=T1].filesToBeCreated:src/a.ts",
    ]


# ---------------------------------------------------------------------------
# invariante #5 — no-delete-of-spec-touched
# ---------------------------------------------------------------------------
def test_delete_of_spec_created_path_names_producer_then_deleter() -> None:
    spec = _spec(
        _ticket("T1", filesToBeCreated=["src/a.ts"]),
        _ticket("T2", filesToBeDeleted=["src/a.ts"], dependencies=_deps("T1")),
    )
    out = check_file_provenance(spec, CONFIG)
    assert len(out) == 1
    f = out[0].finding
    assert f.entity_ids == ["T1", "T2"]
    assert f.primary_entity_id == "T2"
    assert f.operations == ["update_ticket", "delete_ticket"]


def test_delete_of_spec_modified_path_also_fires() -> None:
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeDeleted=["src/a.ts"]),
    )
    ctx = FileProvenanceContext(existing_files=frozenset({"src/a.ts"}))
    out = check_file_provenance(spec, CONFIG, ctx)
    assert _fields(out) == ["tickets[id=T2].filesToBeDeleted:src/a.ts"]
    assert out[0].finding.entity_ids == ["T1", "T2"]


def test_self_delete_of_own_creation_lists_only_that_ticket() -> None:
    spec = _spec(_ticket("T1", filesToBeCreated=["src/a.ts"], filesToBeDeleted=["src/a.ts"]))
    out = check_file_provenance(spec, CONFIG)
    assert len(out) == 1
    assert out[0].finding.entity_ids == ["T1"]
    assert out[0].finding.primary_entity_id == "T1"


def test_delete_of_untouched_existing_path_is_clean() -> None:
    spec = _spec(_ticket("T1", filesToBeDeleted=["src/legacy.ts"]))
    ctx = FileProvenanceContext(existing_files=frozenset({"src/legacy.ts"}))
    assert check_file_provenance(spec, CONFIG, ctx) == []


# ---------------------------------------------------------------------------
# invariante #4 — single creator (keeps its own `file-conflict` category)
# ---------------------------------------------------------------------------
def test_file_consistency_flags_multiple_creators_with_sorted_ids() -> None:
    spec = _spec(
        _ticket("T9", filesToBeCreated=["src/a.ts"]),
        _ticket("T2", filesToBeCreated=["src/a.ts"]),
        _ticket("T5", filesToBeCreated=["src/a.ts"]),
    )
    out = check_file_consistency(spec)
    assert len(out) == 1
    f = out[0].finding
    assert f.category == "file-conflict"
    assert f.field == "filesToBeCreated:src/a.ts"
    assert f.entity_ids == ["T2", "T5", "T9"]
    assert f.primary_entity_id == "T2"
    assert f.operations == ["update_ticket"]


def test_file_consistency_is_silent_for_a_single_creator() -> None:
    spec = _spec(
        _ticket("T1", filesToBeCreated=["src/a.ts"]),
        _ticket("T2", filesToBeCreated=["src/b.ts"]),
    )
    assert check_file_consistency(spec) == []


# ---------------------------------------------------------------------------
# build_file_provenance_maps
# ---------------------------------------------------------------------------
def test_provenance_maps_creation_wins_over_an_earlier_modifier_standin() -> None:
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeCreated=["src/a.ts"]),
    )
    maps = build_file_provenance_maps(spec)
    assert maps.file_to_creator["src/a.ts"] == "T2"
    assert maps.created_paths == {"src/a.ts"}
    assert maps.modified_paths == {"src/a.ts"}


def test_provenance_maps_first_modifier_stands_in_when_nobody_creates() -> None:
    spec = _spec(
        _ticket("T1", filesToBeModified=["src/a.ts"]),
        _ticket("T2", filesToBeModified=["src/a.ts"]),
    )
    maps = build_file_provenance_maps(spec)
    assert maps.file_to_creator["src/a.ts"] == "T1"
    assert maps.created_paths == set()


def test_provenance_maps_a_later_creator_overrides_an_earlier_creator() -> None:
    spec = _spec(
        _ticket("T1", filesToBeCreated=["src/a.ts"]),
        _ticket("T2", filesToBeCreated=["src/a.ts"]),
    )
    assert build_file_provenance_maps(spec).file_to_creator["src/a.ts"] == "T2"


def test_provenance_maps_span_epics_in_flatmap_order() -> None:
    spec = {
        "id": "spec-1",
        "epics": [
            {"id": "e1", "tickets": [_ticket("T1", filesToBeModified=["src/a.ts"])]},
            {"id": "e2", "tickets": [_ticket("T2", filesToBeModified=["src/a.ts"])]},
        ],
    }
    assert build_file_provenance_maps(spec).file_to_creator["src/a.ts"] == "T1"


def test_provenance_maps_of_an_empty_spec_are_empty() -> None:
    maps = build_file_provenance_maps({"id": "spec-1"})
    assert maps.file_to_creator == {}
    assert maps.created_paths == set()
    assert maps.modified_paths == set()


# ---------------------------------------------------------------------------
# build_transitive_deps
# ---------------------------------------------------------------------------
def test_transitive_deps_closure_is_memoised_and_cycle_safe() -> None:
    adj = {"A": ["B"], "B": ["C"], "C": ["A"]}
    cache: dict[str, set[str]] = {}
    assert build_transitive_deps("A", adj, cache) == {"B", "C"}
    assert cache["A"] == {"B", "C"}
    # Cached value is returned as-is on the second call.
    assert build_transitive_deps("A", adj, cache) is cache["A"]
    assert build_transitive_deps("D", adj, cache) == set()


# ---------------------------------------------------------------------------
# compute_grep_candidates
# ---------------------------------------------------------------------------
def test_grep_candidates_are_sorted_deduplicated_and_include_every_created_path() -> None:
    spec = _spec(
        _ticket(
            "T1",
            filesToBeCreated=["src/z.ts", "src/a.ts"],
            filesToBeModified=["src/m.ts"],
        ),
        _ticket(
            "T2",
            filesToBeReferenced=["src/m.ts", "src/z.ts"],
            filesToBeDeleted=["src/d.ts"],
        ),
    )
    candidates = compute_grep_candidates(spec)
    assert candidates == ["src/a.ts", "src/d.ts", "src/m.ts", "src/z.ts"]
    assert candidates == sorted(candidates)
    assert len(candidates) == len(set(candidates))
    # (b) — created paths are seeded independently of the consume-exists channel.
    assert {"src/a.ts", "src/z.ts"} <= set(candidates)


def test_grep_candidates_seed_created_paths_even_with_no_consumers() -> None:
    spec = _spec(_ticket("T1", filesToBeCreated=["src/only-created.ts"]))
    assert compute_grep_candidates(spec) == ["src/only-created.ts"]


def test_grep_candidates_of_an_empty_spec() -> None:
    assert compute_grep_candidates({"id": "spec-1", "epics": []}) == []
