"""epic_expansion phase (port of ``api/phases/epic-expansion.ts``)."""

from __future__ import annotations

from typing import Any

from ...checks.coverage import validate_nfr_coverage, validate_requirement_coverage
from ...checks.na_validation import validate_na_epic
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
from ..scope_resolver import resolve_epic_scope
from ._common import build_active_scoring, build_meta


def validate_epic_expansion(
    spec: dict[str, Any], active_entity_id: str | list[str] | None, config: ValidatorConfig
) -> ValidationResult:
    scoped_epics = resolve_epic_scope(spec, active_entity_id)
    structural = validate_structural(spec, config, "epic_expansion")

    epic_entries = [
        e for e in get_rubric_for_phase("epic_expansion") if e.field_path.startswith("epic.")
    ]
    per_entity_score: dict[str, float] = {}
    scores: list[float] = []
    for epic in scoped_epics:
        result = compute_entity_score(epic, epic_entries, config)
        per_entity_score[epic["id"]] = result.local_score
        scores.append(result.local_score)
    avg_local = 100.0 if not scores else sum(scores) / len(scores)

    breakdown = compute_global_score(spec, config["scoring"]["weights"], config)
    cascade_floors = compute_cascade_floors(config)
    cascade = evaluate_cascade_gate(
        CascadeGateInput(
            global_score=breakdown.global_score,
            spec_block=breakdown.spec_block,
            epic_block=breakdown.epic_block,
            phase="epic_expansion",
            floors=cascade_floors,
        )
    )

    threshold = config["thresholds"]["epic"]
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

    na_findings = [f for e in scoped_epics for f in validate_na_epic(e, config)]
    coverage_findings = [
        *validate_requirement_coverage(spec, scoped_epics, config),
        *validate_nfr_coverage(spec, scoped_epics, config),
    ]
    all_local = [*na_findings, *coverage_findings]

    passed = (
        gate_result == "pass"
        and not structural.invalid_fields
        and not any(f.severity == "error" for f in structural.findings)
        and not all_local
    )

    return ValidationResult(
        phase="epic_expansion",
        passed=passed,
        structural=structural,
        scoring=scoring,
        cross_validation=CrossValidationResult(
            skipped=False,
            findings=all_local,
            ran_checks=["na-validation", "requirement-coverage", "nfr-coverage"],
            skipped_checks=[],
        ),
        meta=build_meta(active_entity_id=active_entity_id),
    )
