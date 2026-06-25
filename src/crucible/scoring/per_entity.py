"""Per-entity scoring (port of ``scoring/per-entity.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..types.config import ValidatorConfig
from ..types.rubric import RubricEntry
from .per_field import PerFieldResult, compute_per_field


@dataclass(frozen=True)
class EntityScoreResult:
    local_score: float
    per_field: dict[str, PerFieldResult]


def compute_entity_score(
    entity: dict[str, Any],
    applicable_entries: list[RubricEntry],
    config: ValidatorConfig,
) -> EntityScoreResult:
    per_field = compute_per_field(entity, applicable_entries, config)

    total_earned = sum(f.earned for f in per_field.values())
    total_possible = sum(f.possible for f in per_field.values())

    local_score = 100.0 if total_possible == 0 else (total_earned / total_possible) * 100

    return EntityScoreResult(local_score=local_score, per_field=per_field)
