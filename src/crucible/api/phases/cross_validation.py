"""cross_validation phase (port of ``api/phases/cross-validation.ts``)."""

from __future__ import annotations

import json
from typing import Any

from ...cross_validation import run_cross_validation
from ...cross_validation.emission import CVEmission
from ...structural import validate_structural
from ...types.config import ValidatorConfig
from ...types.guidance import GuidanceCrossValidationEntry, GuidanceEntry, GuidanceResult
from ...types.result import ValidationResult
from ._common import build_meta


def _adapt_emission(emission: CVEmission) -> GuidanceCrossValidationEntry:
    f = emission.finding
    kwargs: dict[str, Any] = {
        "pattern_id": "cross-validation",
        "category": f.category,
        "severity": f.severity,
        "field_path": f.field,
        "primary_entity_id": f.primary_entity_id,
        "entity_ids": f.entity_ids,
        "message": emission.guidance,
        "operations": f.operations,
        "points_lost": 0,
        "global_impact_on_fix": 0,
    }
    if f.context is not None:
        kwargs["context"] = f.context
    return GuidanceCrossValidationEntry(**kwargs)


def validate_cross_validation(
    spec: dict[str, Any], active_entity_id: str | list[str] | None, config: ValidatorConfig
) -> ValidationResult:
    warnings: list[str] = []
    if active_entity_id is not None:
        warnings.append(
            f"cross_validation phase ignores activeEntityId; received: "
            f"{json.dumps(active_entity_id)}"
        )

    structural = validate_structural(spec, config, "cross_validation")
    run = run_cross_validation(spec, config, "cross_validation")
    cross_validation = run.result

    per_entity: dict[str, list[GuidanceEntry]] = {}
    for emission in run.emissions:
        adapted = _adapt_emission(emission)
        for entity_id in emission.finding.entity_ids:
            per_entity.setdefault(entity_id, []).append(adapted)
    guidance = GuidanceResult(per_entity=per_entity)

    passed = (
        not structural.invalid_fields
        and not any(f.severity == "error" for f in structural.findings)
        and not cross_validation.findings
    )

    return ValidationResult(
        phase="cross_validation",
        passed=passed,
        structural=structural,
        cross_validation=cross_validation,
        guidance=guidance,
        meta=build_meta(active_entity_id=active_entity_id, warnings=warnings or None),
    )
