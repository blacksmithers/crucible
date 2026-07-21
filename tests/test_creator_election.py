"""Creator-election analyzer (MB.13.1) — ``crucible.cross_validation.creator_election``.

Structural coverage of the pure plan value: which files get a plan (orphans
only), the min-rank election, the derived ``modifier → creator`` deps, the
per-file ``clean``/``conflict`` status and the effect of the grep-existing set.
"""

from __future__ import annotations

from typing import Any

from crucible.cross_validation.creator_election import (
    FileToucher,
    RequiredDep,
    elect_file_creators,
)


def _ticket(tid: str, epic_id: str = "e1", **fields: Any) -> dict[str, Any]:
    return {"id": tid, "epicId": epic_id, **fields}


def _epic(epic_id: str, *tickets: dict[str, Any], order: int | None = None) -> dict[str, Any]:
    epic: dict[str, Any] = {"id": epic_id, "tickets": list(tickets)}
    if order is not None:
        epic["order"] = order
    return epic


def _spec(*epics: dict[str, Any]) -> dict[str, Any]:
    return {"id": "spec-1", "epics": list(epics)}


def _deps(*ticket_ids: str) -> list[dict[str, str]]:
    return [{"ticketId": t, "type": "requires"} for t in ticket_ids]


# ---------------------------------------------------------------------------
# Which files get a plan
# ---------------------------------------------------------------------------
def test_a_created_file_is_never_an_orphan() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", order=1, filesToBeCreated=["src/a.ts"]),
            _ticket("T2", order=2, filesToBeModified=["src/a.ts"]),
        )
    )
    assert elect_file_creators(spec).plans == []


def test_a_referenced_only_file_is_an_orphan_too() -> None:
    spec = _spec(_epic("e1", _ticket("T1", order=1, filesToBeReferenced=["src/a.ts"])))
    [plan] = elect_file_creators(spec).plans
    assert plan.file == "src/a.ts"
    assert plan.touchers == [FileToucher(ticket_id="T1", role="references")]


def test_a_deleted_only_file_gets_no_plan() -> None:
    spec = _spec(_epic("e1", _ticket("T1", order=1, filesToBeDeleted=["src/a.ts"])))
    assert elect_file_creators(spec).plans == []


def test_a_grep_existing_file_is_not_an_orphan() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", order=1, filesToBeModified=["src/a.ts", "src/b.ts"]),
            _ticket("T2", order=2, filesToBeModified=["src/a.ts"]),
        )
    )
    # Strict spec-internal model (ABSENT) → both paths are orphans.
    assert [p.file for p in elect_file_creators(spec).plans] == ["src/a.ts", "src/b.ts"]
    # Grep says "src/a.ts" already exists → it needs no creator.
    assert [p.file for p in elect_file_creators(spec, {"src/a.ts"}).plans] == ["src/b.ts"]
    # An empty (but present) grep set changes nothing — nothing exists.
    assert [p.file for p in elect_file_creators(spec, frozenset()).plans] == [
        "src/a.ts",
        "src/b.ts",
    ]


def test_plans_are_sorted_by_file() -> None:
    spec = _spec(
        _epic("e1", _ticket("T1", order=1, filesToBeModified=["src/z.ts", "src/a.ts", "src/m.ts"]))
    )
    assert [p.file for p in elect_file_creators(spec).plans] == [
        "src/a.ts",
        "src/m.ts",
        "src/z.ts",
    ]


def test_an_empty_spec_yields_no_plans() -> None:
    assert elect_file_creators({"id": "spec-1"}).plans == []


# ---------------------------------------------------------------------------
# The election: min rank (epic order → ticket order → id)
# ---------------------------------------------------------------------------
def test_epic_order_dominates_ticket_order_and_id() -> None:
    spec = _spec(
        _epic("e2", _ticket("T-a", epic_id="e2", order=1, filesToBeModified=["x.ts"]), order=2),
        _epic("e1", _ticket("T-b", epic_id="e1", order=9, filesToBeModified=["x.ts"]), order=1),
    )
    [plan] = elect_file_creators(spec).plans
    assert plan.elected_creator == "T-b"
    assert plan.touchers == [
        FileToucher(ticket_id="T-b", role="modifies"),
        FileToucher(ticket_id="T-a", role="modifies"),
    ]
    assert plan.reason == "Epic e1 order 1 / ticket order 9"


def test_ticket_order_zero_is_a_legitimate_order() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T-a", order=5, filesToBeModified=["x.ts"]),
            _ticket("T-b", order=0, filesToBeModified=["x.ts"]),
            order=1,
        )
    )
    [plan] = elect_file_creators(spec).plans
    assert plan.elected_creator == "T-b"
    assert plan.reason == "Epic e1 order 1 / ticket order 0"


def test_absent_orders_fall_back_to_the_ticket_id_tie_break() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T-b", filesToBeModified=["x.ts"]),
            _ticket("T-a", filesToBeModified=["x.ts"]),
        )
    )
    [plan] = elect_file_creators(spec).plans
    assert plan.elected_creator == "T-a"
    assert plan.reason == "Epic e1 order unset / ticket order unset"


def test_reason_reports_unknown_epic_when_the_ticket_has_no_epic_id() -> None:
    spec = _spec(_epic("e1", {"id": "T1", "filesToBeModified": ["x.ts"]}, order=3))
    [plan] = elect_file_creators(spec).plans
    assert plan.reason == "Epic unknown order unset / ticket order unset"


def test_a_ticket_touching_a_file_twice_keeps_the_highest_precedence_role() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket(
                "T1",
                order=1,
                filesToBeReferenced=["x.ts"],
                filesToBeModified=["x.ts"],
            ),
        )
    )
    [plan] = elect_file_creators(spec).plans
    assert plan.touchers == [FileToucher(ticket_id="T1", role="modifies")]


# ---------------------------------------------------------------------------
# required_deps
# ---------------------------------------------------------------------------
def test_a_single_toucher_orphan_needs_no_dependency() -> None:
    spec = _spec(_epic("e1", _ticket("T1", order=1, filesToBeModified=["x.ts"])))
    [plan] = elect_file_creators(spec).plans
    assert plan.elected_creator == "T1"
    assert plan.required_deps == []
    assert plan.status == "clean"


def test_every_other_toucher_gets_a_dep_on_the_creator_sorted_by_source() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket("T-b", order=2, filesToBeModified=["x.ts"]),
            _ticket("T-a", order=3, filesToBeReferenced=["x.ts"]),
            _ticket("T-c", order=1, filesToBeModified=["x.ts"]),
            order=1,
        )
    )
    [plan] = elect_file_creators(spec).plans
    assert plan.elected_creator == "T-c"
    assert plan.required_deps == [
        RequiredDep(from_ticket_id="T-a", to_ticket_id="T-c"),
        RequiredDep(from_ticket_id="T-b", to_ticket_id="T-c"),
    ]
    assert [t.ticket_id for t in plan.touchers] == ["T-c", "T-b", "T-a"]
    assert [t.role for t in plan.touchers] == ["modifies", "modifies", "references"]
    assert plan.status == "clean"


def test_an_already_declared_dependency_is_still_emitted_as_required() -> None:
    # The plan is the full target state, not a diff against the existing DAG.
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", order=1, filesToBeModified=["x.ts"]),
            _ticket("T2", order=2, filesToBeModified=["x.ts"], dependencies=_deps("T1")),
            order=1,
        )
    )
    [plan] = elect_file_creators(spec).plans
    assert plan.required_deps == [RequiredDep(from_ticket_id="T2", to_ticket_id="T1")]
    assert plan.status == "clean"


# ---------------------------------------------------------------------------
# status: clean vs conflict (per file, greedy in rank order)
# ---------------------------------------------------------------------------
def test_an_existing_dependency_pointing_the_wrong_way_is_a_conflict() -> None:
    spec = _spec(
        _epic(
            "e1",
            # T1 is elected (rank 0) but already REQUIRES T2 → adding T2 → T1
            # closes a cycle.
            _ticket("T1", order=1, filesToBeModified=["x.ts"], dependencies=_deps("T2")),
            _ticket("T2", order=2, filesToBeModified=["x.ts"]),
            order=1,
        )
    )
    [plan] = elect_file_creators(spec).plans
    assert plan.elected_creator == "T1"
    assert plan.required_deps == [RequiredDep(from_ticket_id="T2", to_ticket_id="T1")]
    assert plan.status == "conflict"


def test_a_conflicting_file_does_not_contaminate_the_clean_ones() -> None:
    spec = _spec(
        _epic(
            "e1",
            _ticket(
                "T1",
                order=1,
                filesToBeModified=["bad.ts"],
                dependencies=_deps("T2"),
            ),
            _ticket("T2", order=2, filesToBeModified=["bad.ts"]),
            _ticket("T3", order=3, filesToBeModified=["good.ts"]),
            _ticket("T4", order=4, filesToBeModified=["good.ts"]),
            order=1,
        )
    )
    by_file = {p.file: p for p in elect_file_creators(spec).plans}
    assert by_file["bad.ts"].status == "conflict"
    assert by_file["good.ts"].status == "clean"
    assert by_file["good.ts"].elected_creator == "T3"


def test_multi_file_elections_that_compose_stay_clean() -> None:
    # T1 creates nothing; both orphans elect a creator and the union of the two
    # dep sets is still a DAG.
    spec = _spec(
        _epic(
            "e1",
            _ticket("T1", order=1, filesToBeModified=["a.ts"]),
            _ticket("T2", order=2, filesToBeModified=["a.ts", "b.ts"]),
            _ticket("T3", order=3, filesToBeModified=["b.ts"]),
            order=1,
        )
    )
    plans = elect_file_creators(spec).plans
    assert [(p.file, p.elected_creator, p.status) for p in plans] == [
        ("a.ts", "T1", "clean"),
        ("b.ts", "T2", "clean"),
    ]


def test_orphans_are_collected_across_epics() -> None:
    spec = _spec(
        _epic("e1", _ticket("T1", epic_id="e1", order=1, filesToBeModified=["x.ts"]), order=1),
        _epic("e2", _ticket("T2", epic_id="e2", order=1, filesToBeReferenced=["x.ts"]), order=2),
    )
    [plan] = elect_file_creators(spec).plans
    assert plan.elected_creator == "T1"
    assert plan.required_deps == [RequiredDep(from_ticket_id="T2", to_ticket_id="T1")]
    assert plan.status == "clean"
