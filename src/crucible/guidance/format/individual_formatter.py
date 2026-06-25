"""Individual-finding prose (port of ``guidance/format/individual-formatter.ts``)."""

from __future__ import annotations

from typing import Any

from ...types.context import PhaseContext
from ...types.finding import Finding
from ...types.guidance import GuidanceMessage
from ...types.rubric import RubricEntry
from ..engine.resolver import resolve_threshold
from ..engine.value_resolver import resolve_field_value
from ..rubric import ALL_RUBRIC_ENTRIES

_ENTRY_BY_ID = {e.id: e for e in ALL_RUBRIC_ENTRIES}


def _num_str(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _substitute_placeholders(
    template: str,
    finding: Finding,
    field_value: Any,
    context: PhaseContext,
    entity: dict[str, Any] | None,
) -> str:
    entry = _ENTRY_BY_ID.get(finding.rubric_entry_id)
    if entry is None:
        return template

    checks = entry.structural_checks
    count_check = next((c for c in checks if c.type == "minCount"), None)
    item_length_check = next(
        (c for c in checks if c.type == "minLength" and c.applies_to == "items"), None
    )
    field_length_check = next(
        (c for c in checks if c.type == "minLength" and c.applies_to in ("field", None)), None
    )
    item_field_length_check = next(
        (c for c in checks if c.type == "array-item-field-min-length"), None
    )

    config = context.config
    tc = finding.threshold_context
    resolved_item_min = None
    if item_length_check is not None:
        resolved_item_min = resolve_threshold(item_length_check, config, entity)
    elif item_field_length_check is not None:
        resolved_item_min = resolve_threshold(item_field_length_check, config, entity)

    subs: dict[str, Any] = {
        "minCount": resolve_threshold(count_check, config, entity) if count_check else None,
        "actualCount": len(field_value) if isinstance(field_value, list) else None,
        "minLength": resolve_threshold(field_length_check, config, entity)
        if field_length_check
        else None,
        "actualLength": len(field_value) if isinstance(field_value, str) else None,
        "itemMinLength": resolved_item_min,
        "itemIndex": tc.item_index if tc else None,
        "itemActualLength": tc.actual if tc and tc.check_type == "minLengthItem" else None,
    }

    result = template
    for key, val in subs.items():
        if val is not None:
            result = result.replace(f"{{{key}}}", _num_str(val))
    return result


def _resolve_entity(finding: Finding, spec: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    if finding.entity_type == "specification":
        return spec.get("title", ""), spec
    if finding.entity_type == "epic":
        epic = next((e for e in (spec.get("epics") or []) if e["id"] == finding.entity_id), None)
        return (epic.get("title", finding.entity_id) if epic else finding.entity_id), epic
    ticket = next(
        (
            t
            for e in (spec.get("epics") or [])
            for t in (e.get("tickets") or [])
            if t["id"] == finding.entity_id
        ),
        None,
    )
    return (ticket.get("title", finding.entity_id) if ticket else finding.entity_id), ticket


def format_individual_finding(
    finding: Finding, context: PhaseContext, spec: dict[str, Any]
) -> GuidanceMessage:
    entry: RubricEntry | None = _ENTRY_BY_ID.get(finding.rubric_entry_id)
    field_name = ".".join(finding.field_path.split(".")[1:])
    verb = finding.primary_verbs[0] if finding.primary_verbs else "DECLARE"
    entity_type_cap = finding.entity_type[0].upper() + finding.entity_type[1:]

    entity_label, entity = _resolve_entity(finding, spec)
    field_value = resolve_field_value(entity, finding.field_path) if entity else None

    if finding.na_without_reason:
        na_prompt = (entry.na_without_reason_prompt if entry else None) or (
            f"Either populate the field, or add naReason explaining why this field doesn't "
            f"apply to this {entity_type_cap}."
        )
        message = (
            f'{entity_type_cap} "{entity_label}" — field "{field_name}" is marked N/A but no '
            f"naReason provided. {na_prompt}"
        )
    else:
        raw_prompt = (entry.curriculum_prompt if entry else None) or f'{verb} the "{field_name}" field.'
        prompt = _substitute_placeholders(raw_prompt, finding, field_value, context, entity)
        status_label = "incomplete" if finding.status == "partial" else "missing"
        message = f'{entity_type_cap} "{entity_label}" — {status_label} "{field_name}". {prompt}'

    return GuidanceMessage(
        pattern_id="individual",
        entity_id=finding.entity_id,
        entity_type=finding.entity_type,
        message=message,
        operations=entry.available_operations if entry else [],
        points_lost=finding.points_lost,
        global_impact_on_fix=finding.global_impact_on_fix,
    )
