"""Fixed decomposition-phase prompts."""

from __future__ import annotations

from typing import Any

from .. import i18n
from ..types.guidance import GuidanceMessage, GuidanceResult


def build_epic_decomposition_guidance(
    spec: dict[str, Any], language: str = "en"
) -> GuidanceResult:
    message = GuidanceMessage(
        pattern_id="individual",
        entity_id=spec["id"],
        entity_type="specification",
        message=i18n.text(language, "guidance.fixed.epicDecomposition"),
        operations=["create_epic", "update_epic", "delete_epic"],
        points_lost=0,
        global_impact_on_fix=0,
    )
    return GuidanceResult(per_entity={spec["id"]: [message]}, truncated=False)


def build_ticket_decomposition_guidance(
    spec: dict[str, Any], active_epic_id: str, language: str = "en"
) -> GuidanceResult:
    epic = next((e for e in (spec.get("epics") or []) if e["id"] == active_epic_id), None)
    if epic is None:
        return GuidanceResult(per_entity={}, truncated=False)
    message = GuidanceMessage(
        pattern_id="individual",
        entity_id=epic["id"],
        entity_type="epic",
        message=i18n.text(language, "guidance.fixed.ticketDecomposition"),
        operations=["create_ticket", "update_ticket", "delete_ticket"],
        points_lost=0,
        global_impact_on_fix=0,
    )
    return GuidanceResult(per_entity={epic["id"]: [message]}, truncated=False)
