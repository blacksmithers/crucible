"""Guidance layer output contracts (port of ``types/guidance.ts``)."""

from __future__ import annotations

from typing import Any, Literal

from ._base import CamelModel
from .enums import CompositePatternId, EntityType, Severity
from .operations import OperationName


class GuidanceMessage(CamelModel):
    pattern_id: CompositePatternId | Literal["individual"]
    entity_id: str
    entity_type: EntityType
    message: str
    operations: list[OperationName]
    points_lost: float
    global_impact_on_fix: float


class GuidanceCrossValidationEntry(CamelModel):
    pattern_id: Literal["cross-validation"] = "cross-validation"
    category: str
    severity: Severity
    field_path: str
    primary_entity_id: str
    entity_ids: list[str]
    message: str
    operations: list[str]
    points_lost: Literal[0] = 0
    global_impact_on_fix: Literal[0] = 0
    context: dict[str, Any] | None = None


GuidanceEntry = GuidanceMessage | GuidanceCrossValidationEntry


class GuidanceResult(CamelModel):
    per_entity: dict[str, list[GuidanceEntry]]
    truncated: bool | None = None
