"""planning_spec phase (port of ``api/phases/planning-spec.ts``).

Guidance layer deferred (C7) — ``guidance`` is left unset.
"""

from __future__ import annotations

from typing import Any

from ...checks.na_validation import validate_na_spec
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
from ...types.result import ValidationResult
from ._common import build_active_scoring, build_meta, per_field_to_scores


def validate_planning_spec(
    spec: dict[str, Any], active_entity_id: str | list[str] | None, config: ValidatorConfig
) -> ValidationResult:
    structural = validate_structural(spec, config, "planning_spec")

    spec_entries = [
        e for e in get_rubric_for_phase("planning_spec") if e.field_path.startswith("specification.")
    ]
    entity_score = compute_entity_score(spec, spec_entries, config)

    breakdown = compute_global_score(spec, config["scoring"]["weights"], config)
    cascade_floors = compute_cascade_floors(config)
    cascade = evaluate_cascade_gate(
        CascadeGateInput(
            global_score=breakdown.global_score,
            spec_block=breakdown.spec_block,
            epic_block=breakdown.epic_block,
            phase="planning_spec",
            floors=cascade_floors,
        )
    )

    threshold = config["thresholds"]["specification"]
    gate_result = (
        "pass" if entity_score.local_score >= threshold and cascade.gate_result == "pass" else "fail"
    )

    scoring = build_active_scoring(
        local_score=entity_score.local_score,
        per_field=per_field_to_scores(entity_score.per_field),
        breakdown=breakdown,
        cascade_floors=cascade_floors,
        cascade_failures=cascade.cascade_failures,
        gate_result=gate_result,
        threshold=threshold,
    )

    na_findings = validate_na_spec(spec, config)
    passed = (
        gate_result == "pass"
        and not structural.invalid_fields
        and not any(f.severity == "error" for f in structural.findings)
        and not na_findings
    )

    return ValidationResult(
        phase="planning_spec",
        passed=passed,
        structural=structural,
        scoring=scoring,
        meta=build_meta(active_entity_id=active_entity_id),
    )
