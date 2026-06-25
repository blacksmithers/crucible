"""Fixed decomposition-phase prompts (port of ``guidance/fixed-prompts.ts``)."""

from __future__ import annotations

from typing import Any

from ..types.guidance import GuidanceMessage, GuidanceResult

_EPIC_DECOMPOSITION_TEMPLATE = (
    "Decomposition phase. Review the current set of epics and decide whether "
    "the decomposition is sufficient. Available operations: create_epic, "
    "update_epic, delete_epic. To advance to the next phase, invoke "
    "complete_decomposition_phase explicitly."
)

_TICKET_DECOMPOSITION_TEMPLATE = (
    "Decomposition phase. Review the current set of tickets in this epic and "
    "decide whether the decomposition is sufficient. Available operations: "
    "create_ticket, update_ticket, delete_ticket. To advance to the next phase, "
    "invoke complete_decomposition_phase explicitly."
)


def build_epic_decomposition_guidance(spec: dict[str, Any]) -> GuidanceResult:
    message = GuidanceMessage(
        pattern_id="individual",
        entity_id=spec["id"],
        entity_type="specification",
        message=_EPIC_DECOMPOSITION_TEMPLATE,
        operations=["create_epic", "update_epic", "delete_epic"],
        points_lost=0,
        global_impact_on_fix=0,
    )
    return GuidanceResult(per_entity={spec["id"]: [message]}, truncated=False)


def build_ticket_decomposition_guidance(
    spec: dict[str, Any], active_epic_id: str
) -> GuidanceResult:
    epic = next((e for e in (spec.get("epics") or []) if e["id"] == active_epic_id), None)
    if epic is None:
        return GuidanceResult(per_entity={}, truncated=False)
    message = GuidanceMessage(
        pattern_id="individual",
        entity_id=epic["id"],
        entity_type="epic",
        message=_TICKET_DECOMPOSITION_TEMPLATE,
        operations=["create_ticket", "update_ticket", "delete_ticket"],
        points_lost=0,
        global_impact_on_fix=0,
    )
    return GuidanceResult(per_entity={epic["id"]: [message]}, truncated=False)
