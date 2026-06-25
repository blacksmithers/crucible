"""epic_decomposition phase (port of ``api/phases/epic-decomposition.ts``)."""

from __future__ import annotations

from typing import Any

from ...engines.ratios import check_blueprint_epic_ratio
from ...guidance.fixed_prompts import build_epic_decomposition_guidance
from ...structural import validate_structural
from ...types.config import ValidatorConfig
from ...types.result import CrossValidationResult, ScoringResultSkipped, ValidationResult
from ._common import build_meta


def validate_epic_decomposition(
    spec: dict[str, Any], _active_entity_id: str | list[str] | None, config: ValidatorConfig
) -> ValidationResult:
    structural = validate_structural(spec, config, "epic_decomposition")
    ratio_findings = check_blueprint_epic_ratio(spec, config)

    passed = (
        not ratio_findings
        and not structural.invalid_fields
        and not any(f.severity == "error" for f in structural.findings)
    )

    return ValidationResult(
        phase="epic_decomposition",
        passed=passed,
        structural=structural,
        scoring=ScoringResultSkipped(),
        cross_validation=CrossValidationResult(
            skipped=False,
            findings=ratio_findings,
            ran_checks=["blueprint-epic-ratio"],
            skipped_checks=[],
        ),
        guidance=build_epic_decomposition_guidance(spec),
        meta=build_meta(),
    )
