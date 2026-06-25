"""ticket_expansion phase (port of ``api/phases/ticket-expansion.ts``)."""

from __future__ import annotations

from typing import Any

from ...checks.na_validation import validate_na_ticket
from ...guidance.rubric import get_rubric_for_phase
from ...scoring import (
    CascadeGateInput,
    compute_cascade_floors,
    compute_entity_score,
    compute_global_score,
    evaluate_cascade_gate,
)
from ...structural import validate_structural
from ...types.config import ValidatorConfig
from ...types.result import CrossValidationResult, ValidationResult
from ..scope_resolver import resolve_ticket_scope
from ._common import build_active_scoring, build_meta


def validate_ticket_expansion(
    spec: dict[str, Any], active_entity_id: str | list[str] | None, config: ValidatorConfig
) -> ValidationResult:
    scope = resolve_ticket_scope(spec, active_entity_id)
    tickets = scope.tickets
    structural = validate_structural(spec, config, "ticket_expansion")

    ticket_entries = [
        e for e in get_rubric_for_phase("ticket_expansion") if e.field_path.startswith("ticket.")
    ]
    per_entity_score: dict[str, float] = {}
    scores: list[float] = []
    for ticket in tickets:
        result = compute_entity_score(ticket, ticket_entries, config)
        per_entity_score[ticket["id"]] = result.local_score
        scores.append(result.local_score)
    avg_local = 100.0 if not scores else sum(scores) / len(scores)

    breakdown = compute_global_score(spec, config["scoring"]["weights"], config)
    cascade_floors = compute_cascade_floors(config)
    cascade = evaluate_cascade_gate(
        CascadeGateInput(
            global_score=breakdown.global_score,
            spec_block=breakdown.spec_block,
            epic_block=breakdown.epic_block,
            phase="ticket_expansion",
            floors=cascade_floors,
        )
    )

    threshold = config["thresholds"]["ticket"]
    gate_result = "pass" if avg_local >= threshold and cascade.gate_result == "pass" else "fail"

    scoring = build_active_scoring(
        local_score=avg_local,
        per_field={},
        breakdown=breakdown,
        cascade_floors=cascade_floors,
        cascade_failures=cascade.cascade_failures,
        gate_result=gate_result,
        threshold=threshold,
        per_entity_score=per_entity_score,
    )

    na_findings = [f for t in tickets for f in validate_na_ticket(t, config)]

    passed = (
        gate_result == "pass"
        and not structural.invalid_fields
        and not any(f.severity == "error" for f in structural.findings)
        and not na_findings
    )

    cross_validation = (
        CrossValidationResult(
            skipped=False,
            findings=na_findings,
            ran_checks=["na-validation"],
            skipped_checks=[],
        )
        if na_findings
        else None
    )

    return ValidationResult(
        phase="ticket_expansion",
        passed=passed,
        structural=structural,
        scoring=scoring,
        cross_validation=cross_validation,
        meta=build_meta(active_entity_id=active_entity_id, resolution=scope.resolution),
    )
