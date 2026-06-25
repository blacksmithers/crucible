"""Rubric finding generation (port of ``guidance/engine/index.ts`` ``executeRubric``)."""

from __future__ import annotations

from typing import Any

from ...scoring.field_declarations import validate_na_declaration
from ...types.context import PhaseContext
from ...types.enums import EntityType
from ...types.finding import Finding, ThresholdContext
from ...types.phase import ValidationPhase
from ...types.rubric import RubricEntry
from ..rubric import get_rubric_for_phase
from .applicability import is_applicable, is_config_applicable
from .structural_checks import evaluate_structural_checks
from .value_resolver import entry_matches_entity_type, get_entity_type, resolve_field_value


def derive_leaf_field(field_path: str) -> str:
    last = field_path.split(".")[-1]
    return last.removesuffix("[]")


def compute_global_impact_on_fix(
    points_lost: float,
    entity_type: EntityType,
    spec: dict[str, Any],
    weights: dict[str, float],
) -> float:
    if entity_type == "specification":
        return points_lost * weights["spec"]
    if entity_type == "epic":
        n = len(spec.get("epics") or [])
        return 0.0 if n == 0 else points_lost * weights["epics"] / n
    m = sum(len(e.get("tickets") or []) for e in (spec.get("epics") or []))
    return 0.0 if m == 0 else points_lost * weights["tickets"] / m


def _resolve_entities_for_scope(
    spec: dict[str, Any], phase: ValidationPhase, active_entity_id: str | list[str] | None
) -> list[dict[str, Any]]:
    if phase == "planning_spec":
        return [spec]

    ids = (
        []
        if active_entity_id is None
        else (active_entity_id if isinstance(active_entity_id, list) else [active_entity_id])
    )
    epics = spec.get("epics") or []

    if phase == "epic_expansion":
        return [e for e in epics if e["id"] in ids] if ids else epics

    if phase == "ticket_expansion":
        all_tickets = [t for e in epics for t in (e.get("tickets") or [])]
        if ids:
            resolved: list[dict[str, Any]] = []
            for eid in ids:
                by_ticket = [t for t in all_tickets if t["id"] == eid]
                if by_ticket:
                    resolved.extend(by_ticket)
                else:
                    resolved.extend(
                        t for e in epics if e["id"] == eid for t in (e.get("tickets") or [])
                    )
            return list({t["id"]: t for t in resolved}.values())
        return all_tickets

    return [spec]


def _emit_findings_for_entry(
    entry: RubricEntry,
    entity: dict[str, Any],
    entity_type: EntityType,
    spec: dict[str, Any],
    context: PhaseContext,
    total_possible_raw: float,
) -> list[Finding]:
    config = context.config
    weights = config["scoring"]["weights"]
    na_result = validate_na_declaration(entity, entry.field_path, entry, config)

    entity_id = entity["id"]
    field_path = entry.field_path
    field = derive_leaf_field(field_path)
    raw_weight = config["tiers"][entry.tier]
    base_points_lost = (raw_weight / total_possible_raw) * 100 if total_possible_raw > 0 else 0.0

    def _finding(**overrides: Any) -> Finding:
        kwargs: dict[str, Any] = {
            "rubric_entry_id": entry.id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "field_path": field_path,
            "field": field,
            "tier": entry.tier,
            "primary_verbs": entry.primary_verbs,
        }
        kwargs.update(overrides)
        return Finding(**kwargs)

    if na_result.valid:
        return [_finding(status="fulfilled", points_lost=0.0, global_impact_on_fix=0.0)]

    if na_result.reason in ("reason-missing", "reason-too-short"):
        return [
            _finding(
                status="missing",
                points_lost=base_points_lost,
                global_impact_on_fix=compute_global_impact_on_fix(
                    base_points_lost, entity_type, spec, weights
                ),
                na_without_reason=True,
            )
        ]

    value = resolve_field_value(entity, entry.field_path)
    result = evaluate_structural_checks(entry.structural_checks, value, config, entity)

    if result.status == "fulfilled":
        return [_finding(status="fulfilled", points_lost=0.0, global_impact_on_fix=0.0)]

    if result.per_item_findings:
        array_length = max(len(value), 1) if isinstance(value, list) else 1
        out: list[Finding] = []
        for offender in result.per_item_findings:
            item_points = base_points_lost / array_length
            out.append(
                _finding(
                    status="partial",
                    points_lost=item_points,
                    global_impact_on_fix=compute_global_impact_on_fix(
                        item_points, entity_type, spec, weights
                    ),
                    threshold_context=ThresholdContext(
                        check_type="minLengthItem",
                        expected=offender.expected_min_length,
                        actual=offender.item_actual_length,
                        item_index=offender.item_index,
                    ),
                )
            )
        return out

    return [
        _finding(
            status=result.status,
            points_lost=base_points_lost,
            global_impact_on_fix=compute_global_impact_on_fix(
                base_points_lost, entity_type, spec, weights
            ),
            threshold_context=result.threshold_context,
        )
    ]


def _process_phase(
    spec: dict[str, Any], phase: ValidationPhase, context: PhaseContext
) -> list[Finding]:
    phase_rubric = get_rubric_for_phase(phase)
    if not phase_rubric:
        return []

    entities = _resolve_entities_for_scope(spec, phase, context.active_entity_id)
    findings: list[Finding] = []
    for entity in entities:
        entity_type = get_entity_type(entity)
        applicable = [
            e
            for e in phase_rubric
            if entry_matches_entity_type(e.field_path, entity_type)
            and is_applicable(entity, e)
            and is_config_applicable(e, context.config)
        ]
        total_possible_raw = sum(context.config["tiers"][e.tier] for e in applicable)
        for entry in applicable:
            findings.extend(
                _emit_findings_for_entry(
                    entry, entity, entity_type, spec, context, total_possible_raw
                )
            )
    return findings


def execute_rubric(spec: dict[str, Any], context: PhaseContext) -> list[Finding]:
    if context.phase == "cross_validation":
        out: list[Finding] = []
        for phase in ("planning_spec", "epic_expansion", "ticket_expansion"):
            out.extend(_process_phase(spec, phase, context))
        return out
    return _process_phase(spec, context.phase, context)
