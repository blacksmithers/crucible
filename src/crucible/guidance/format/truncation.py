"""Per-entity guidance truncation (port of ``guidance/format/truncation.ts``)."""

from __future__ import annotations

from ...types.config import ValidatorConfig
from ...types.guidance import GuidanceEntry, GuidanceResult


def apply_truncation(
    per_entity: dict[str, list[GuidanceEntry]], config: ValidatorConfig
) -> GuidanceResult:
    limit = config["guidance"]["topNPerEntity"]["default"]
    truncated_per_entity: dict[str, list[GuidanceEntry]] = {}
    any_truncated = False
    for entity_id, messages in per_entity.items():
        if len(messages) > limit:
            any_truncated = True
        truncated_per_entity[entity_id] = messages[:limit]
    return GuidanceResult(per_entity=truncated_per_entity, truncated=any_truncated)
