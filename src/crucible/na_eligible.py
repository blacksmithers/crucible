"""The shared N/A-eligibility allow-set.

The eligibility SOURCE a ``justify`` operation validates a ``scope`` against.

Why this is its own top-level module: the primary justify scope,
``dependencies``, is NOT a rubric body field — it is a cross-cutting justifiable
scope that the cross-validation checks read DIRECTLY off ``fieldDeclarations``
(``dependency_graph.check_orphan_reference`` and ``check_island_ticket`` read
``decls["dependencies"]`` via ``_has_dependencies_na_justification``). So
eligibility is a SHARED allow-set — { the rubric ``naEligible`` fields per
entity } ∪ { the cross-cutting ``dependencies`` (ticket) } — derived here from
``ALL_RUBRIC_ENTRIES`` (single source of truth, no drift).

The scope keys are the CANONICAL bare ``fieldDeclarations`` keys the checks
read: the rubric ``field_path`` with the entity prefix stripped
(``ticket.codeReferences`` → ``codeReferences``,
``ticket.testSpecification.testCommands`` → ``testSpecification.testCommands``),
exactly matching the ``_field_key`` of ``checks/na_validation.py``.
"""

from __future__ import annotations

from typing import Literal, get_args

from .guidance.rubric import ALL_RUBRIC_ENTRIES

__all__ = [
    "CROSS_CUTTING_NA_ELIGIBLE_SCOPES",
    "NaEligibleEntity",
    "is_na_eligible_scope",
    "na_eligible_scopes_for",
]

NaEligibleEntity = Literal["specification", "epic", "ticket"]

_ENTITIES: tuple[NaEligibleEntity, ...] = get_args(NaEligibleEntity)


def _field_key(field_path: str) -> str:
    """Strip the entity prefix from a rubric ``field_path`` → canonical key."""
    dot = field_path.find(".")
    return field_path[dot + 1 :] if dot != -1 else field_path


# Cross-cutting justifiable scopes that are NOT rubric body fields but ARE read
# directly as ``fieldDeclarations[scope]`` by the cross-validation checks (they
# have no rubric entry, so eligibility for them comes from THIS list, unioned
# with the rubric fields). ``dependencies`` (ticket) is the flagship — the
# foundational-root N/A that unblocks cross_validation. Kept explicit + tiny so
# a new cross-cutting scope is a one-line add.
CROSS_CUTTING_NA_ELIGIBLE_SCOPES: dict[NaEligibleEntity, tuple[str, ...]] = {
    "specification": (),
    "epic": (),
    "ticket": ("dependencies",),
}


def _build_allow_sets() -> dict[NaEligibleEntity, frozenset[str]]:
    out: dict[NaEligibleEntity, set[str]] = {e: set() for e in _ENTITIES}
    for entry in ALL_RUBRIC_ENTRIES:
        dot = entry.field_path.find(".")
        prefix = entry.field_path[:dot] if dot != -1 else ""
        if prefix not in _ENTITIES:
            continue
        if not entry.na_eligible:
            continue
        out[prefix].add(_field_key(entry.field_path))
    for entity in _ENTITIES:
        out[entity].update(CROSS_CUTTING_NA_ELIGIBLE_SCOPES[entity])
    return {e: frozenset(s) for e, s in out.items()}


_ALLOW_SETS: dict[NaEligibleEntity, frozenset[str]] = _build_allow_sets()


def na_eligible_scopes_for(entity: NaEligibleEntity) -> frozenset[str]:
    """The N/A-eligible ``fieldDeclarations`` scopes for an entity kind.

    { rubric ``naEligible`` fields } ∪ { cross-cutting scopes (e.g. ticket
    ``dependencies``) }.
    """
    return _ALLOW_SETS[entity]


def is_na_eligible_scope(entity: NaEligibleEntity, scope: str) -> bool:
    """True when ``scope`` may be declared N/A on the given entity kind."""
    return scope in _ALLOW_SETS[entity]
