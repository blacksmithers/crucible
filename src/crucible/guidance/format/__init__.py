"""Guidance formatting (port of ``guidance/format/index.ts``)."""

from __future__ import annotations

from typing import Any

from ...types.context import PhaseContext
from ...types.finding import CompositeFinding, Finding
from ...types.guidance import GuidanceEntry, GuidanceMessage, GuidanceResult
from .individual_formatter import format_individual_finding
from .templates import (
    format_conditional_gap,
    format_foundation_gap,
    format_integrity_gap,
    format_linkage_gap,
    format_tactical_gap,
)
from .truncation import apply_truncation

_TEMPLATE_BY_PATTERN = {
    "foundation-gap": format_foundation_gap,
    "tactical-gap": format_tactical_gap,
    "conditional-gap": format_conditional_gap,
    "linkage-gap": format_linkage_gap,
    "integrity-gap": format_integrity_gap,
}

__all__ = ["format_guidance"]


def _sort_key(entry: GuidanceEntry) -> tuple[float, float]:
    return (-entry.global_impact_on_fix, -entry.points_lost)


def format_guidance(
    composites: list[CompositeFinding],
    individuals: list[Finding],
    context: PhaseContext,
    spec: dict[str, Any],
) -> GuidanceResult:
    per_entity: dict[str, list[GuidanceEntry]] = {}

    for composite in composites:
        template_fn = _TEMPLATE_BY_PATTERN.get(composite.pattern_id)
        if template_fn is None:
            continue
        message = template_fn(composite, context, spec)
        per_entity.setdefault(composite.entity_id, []).append(
            GuidanceMessage(
                pattern_id=composite.pattern_id,
                entity_id=composite.entity_id,
                entity_type=composite.entity_type,
                message=message,
                operations=composite.suggested_operations,
                points_lost=composite.total_points_lost,
                global_impact_on_fix=composite.total_global_impact_on_fix,
            )
        )

    for finding in individuals:
        per_entity.setdefault(finding.entity_id, []).append(
            format_individual_finding(finding, context, spec)
        )

    for entity_id in per_entity:
        per_entity[entity_id] = sorted(per_entity[entity_id], key=_sort_key)

    return apply_truncation(per_entity, context.config)
