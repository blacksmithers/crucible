"""The 53-entry rubric (port of ``guidance/rubric/{specification,epic,ticket}.ts``).

The entries are loaded from a packaged ``rubric.json`` generated verbatim from
the TS source (see ``tools/dump_rubric.mjs``) — pure data, guaranteeing the 53
entries match the reference engine exactly.
"""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any

from ...types.phase import ValidationPhase
from ...types.rubric import ConditionalApplicability, RubricEntry, StructuralCheck

__all__ = [
    "ALL_RUBRIC_ENTRIES",
    "epic_entries",
    "get_rubric_for_phase",
    "specification_entries",
    "ticket_entries",
]


def _build_check(raw: dict[str, Any]) -> StructuralCheck:
    return StructuralCheck(
        type=raw["type"],
        param=raw.get("param"),
        source=raw.get("source"),
        applies_to=raw.get("appliesTo"),
    )


def _build_entry(raw: dict[str, Any]) -> RubricEntry:
    cond_raw = raw.get("conditionalApplicability")
    cond = (
        ConditionalApplicability(field=cond_raw["field"], equals=cond_raw["equals"])
        if cond_raw is not None
        else None
    )
    return RubricEntry(
        id=raw["id"],
        field_path=raw["fieldPath"],
        curriculum_phase=raw["curriculumPhase"],
        curriculum_step=raw["curriculumStep"],
        tier=raw["tier"],
        structural_checks=[_build_check(c) for c in raw["structuralChecks"]],
        na_eligible=raw["naEligible"],
        primary_verbs=list(raw["primaryVerbs"]),
        curriculum_prompt=raw["curriculumPrompt"],
        available_operations=list(raw["availableOperations"]),
        prerequisite=raw.get("prerequisite"),
        conditional_applicability=cond,
        applicability_check=raw.get("applicabilityCheck"),
        na_without_reason_prompt=raw.get("naWithoutReasonPrompt"),
        composes_with=raw.get("composesWith"),
    )


def _load_all() -> list[RubricEntry]:
    raw = (
        resources.files("crucible.guidance.rubric.data")
        .joinpath("rubric.json")
        .read_text(encoding="utf-8")
    )
    return [_build_entry(e) for e in json.loads(raw)]


ALL_RUBRIC_ENTRIES: list[RubricEntry] = _load_all()

specification_entries: list[RubricEntry] = [
    e for e in ALL_RUBRIC_ENTRIES if e.field_path.startswith("specification.")
]
epic_entries: list[RubricEntry] = [
    e for e in ALL_RUBRIC_ENTRIES if e.field_path.startswith("epic.")
]
ticket_entries: list[RubricEntry] = [
    e for e in ALL_RUBRIC_ENTRIES if e.field_path.startswith("ticket.")
]


@cache
def get_rubric_for_phase(phase: ValidationPhase) -> tuple[RubricEntry, ...]:
    if phase in ("cross_validation", "all"):
        return tuple(ALL_RUBRIC_ENTRIES)
    return tuple(e for e in ALL_RUBRIC_ENTRIES if e.curriculum_phase == phase)
