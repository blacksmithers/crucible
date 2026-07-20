"""MB.11.1 — the shared N/A-eligibility allow-set (``crucible.na_eligible``).

Structural coverage only: which SCOPE KEYS are eligible per entity kind, that the
allow-set is exactly ``rubric naEligible ∪ cross-cutting``, and that the
predicate agrees with the set.
"""

from __future__ import annotations

from typing import Any

import pytest

from crucible.guidance.rubric import ALL_RUBRIC_ENTRIES
from crucible.na_eligible import (
    CROSS_CUTTING_NA_ELIGIBLE_SCOPES,
    NaEligibleEntity,
    is_na_eligible_scope,
    na_eligible_scopes_for,
)

ENTITIES: tuple[NaEligibleEntity, ...] = ("specification", "epic", "ticket")


def _rubric_scopes_for(entity: NaEligibleEntity) -> set[str]:
    """The rubric-derived half of the allow-set, re-derived independently."""
    out: set[str] = set()
    for entry in ALL_RUBRIC_ENTRIES:
        prefix, _, tail = entry.field_path.partition(".")
        if prefix != entity or not tail:
            continue
        if entry.na_eligible:
            out.add(tail)
    return out


# ---------------------------------------------------------------------------
# The three per-entity sets
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("entity", ENTITIES)
def test_every_entity_has_a_non_empty_frozenset(entity: NaEligibleEntity) -> None:
    scopes = na_eligible_scopes_for(entity)
    assert isinstance(scopes, frozenset)
    assert scopes


@pytest.mark.parametrize("entity", ENTITIES)
def test_allow_set_is_rubric_union_cross_cutting(entity: NaEligibleEntity) -> None:
    expected = _rubric_scopes_for(entity) | set(CROSS_CUTTING_NA_ELIGIBLE_SCOPES[entity])
    assert na_eligible_scopes_for(entity) == expected


@pytest.mark.parametrize("entity", ENTITIES)
def test_scopes_are_bare_keys_without_the_entity_prefix(entity: NaEligibleEntity) -> None:
    for scope in na_eligible_scopes_for(entity):
        assert not scope.startswith(("specification.", "epic.", "ticket."))
        assert scope


def test_nested_scopes_keep_their_dotted_tail() -> None:
    ticket = na_eligible_scopes_for("ticket")
    assert "testSpecification.testCommands" in ticket
    assert "testSpecification.coverageTarget" in ticket
    assert "scope.assumptions" in na_eligible_scopes_for("specification")
    assert "scope.assumptions" in na_eligible_scopes_for("epic")


def test_entity_sets_are_distinct() -> None:
    spec = na_eligible_scopes_for("specification")
    epic = na_eligible_scopes_for("epic")
    ticket = na_eligible_scopes_for("ticket")
    assert spec != epic != ticket
    # A scope may legitimately be shared (spec/epic both carry `scope.*`)...
    assert {"scope.assumptions", "sharedPatterns"} <= (spec & epic)
    # ...while entity-owned scopes stay put.
    assert "codeReferences" in ticket
    assert "codeReferences" not in spec and "codeReferences" not in epic
    assert "goals" in epic and "goals" not in spec and "goals" not in ticket
    assert "background" in spec and "background" not in epic and "background" not in ticket


# ---------------------------------------------------------------------------
# The cross-cutting union (`dependencies`)
# ---------------------------------------------------------------------------
def test_dependencies_is_eligible_for_ticket_only() -> None:
    assert "dependencies" in na_eligible_scopes_for("ticket")
    assert "dependencies" not in na_eligible_scopes_for("epic")
    assert "dependencies" not in na_eligible_scopes_for("specification")


def test_dependencies_is_cross_cutting_not_rubric_derived() -> None:
    # It is NOT a rubric body field — eligibility comes purely from the
    # cross-cutting list, which is what makes the union load-bearing.
    assert "dependencies" not in _rubric_scopes_for("ticket")
    assert CROSS_CUTTING_NA_ELIGIBLE_SCOPES["ticket"] == ("dependencies",)
    assert CROSS_CUTTING_NA_ELIGIBLE_SCOPES["epic"] == ()
    assert CROSS_CUTTING_NA_ELIGIBLE_SCOPES["specification"] == ()


@pytest.mark.parametrize("entity", ENTITIES)
def test_cross_cutting_scopes_are_all_present_in_the_allow_set(entity: NaEligibleEntity) -> None:
    declared = set(CROSS_CUTTING_NA_ELIGIBLE_SCOPES[entity])
    assert declared <= na_eligible_scopes_for(entity)


# ---------------------------------------------------------------------------
# is_na_eligible_scope
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("entity", ENTITIES)
def test_predicate_agrees_with_the_set(entity: NaEligibleEntity) -> None:
    for scope in na_eligible_scopes_for(entity):
        assert is_na_eligible_scope(entity, scope) is True


def test_predicate_rejects_unknown_and_misprefixed_scopes() -> None:
    assert is_na_eligible_scope("ticket", "dependencies") is True
    assert is_na_eligible_scope("ticket", "ticket.dependencies") is False
    assert is_na_eligible_scope("ticket", "notAField") is False
    assert is_na_eligible_scope("ticket", "") is False
    # A field that exists in the rubric but is not N/A-eligible.
    assert is_na_eligible_scope("ticket", "id") is False
    assert is_na_eligible_scope("ticket", "title") is False


def test_unknown_entity_raises() -> None:
    bogus: Any = "blueprint"
    with pytest.raises(KeyError):
        na_eligible_scopes_for(bogus)
    with pytest.raises(KeyError):
        is_na_eligible_scope(bogus, "dependencies")


def test_allow_sets_are_stable_between_calls() -> None:
    assert na_eligible_scopes_for("ticket") is na_eligible_scopes_for("ticket")
