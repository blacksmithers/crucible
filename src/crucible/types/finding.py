"""Internal finding contracts (port of ``types/finding.ts``).

Intermediate values produced by the scoring/guidance pipeline; composed into
the public ``GuidanceResult`` entries. Internal → dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .enums import ActionVerb, CompositePatternId, EntityType, FindingStatus, Tier
from .operations import OperationName


@dataclass(frozen=True)
class ThresholdContext:
    check_type: Literal["minCount", "minLength", "minLengthItem"]
    expected: int
    actual: int
    item_index: int | None = None


@dataclass
class Finding:
    rubric_entry_id: str
    entity_id: str
    entity_type: EntityType
    field_path: str
    field: str
    status: FindingStatus
    tier: Tier
    primary_verbs: list[ActionVerb]
    points_lost: float
    global_impact_on_fix: float
    na_without_reason: bool | None = None
    threshold_context: ThresholdContext | None = None


@dataclass
class CompositeFinding:
    pattern_id: CompositePatternId
    entity_id: str
    entity_type: EntityType
    grouped_findings: list[Finding]
    total_points_lost: float
    total_global_impact_on_fix: float
    primary_verb: ActionVerb
    suggested_operations: list[OperationName]
