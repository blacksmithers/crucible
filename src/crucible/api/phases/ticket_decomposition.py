"""ticket_decomposition phase (port of ``api/phases/ticket-decomposition.ts``)."""

from __future__ import annotations

from typing import Any

from ...engines.ratios import check_impl_verification_ratio
from ...guidance.fixed_prompts import build_ticket_decomposition_guidance
from ...structural import validate_structural
from ...types.config import ValidatorConfig
from ...types.result import CrossValidationResult, ScoringResultSkipped, ValidationResult
from ..scope_resolver import resolve_epic_scope
from ._common import build_meta


def validate_ticket_decomposition(
    spec: dict[str, Any], active_entity_id: str | list[str] | None, config: ValidatorConfig
) -> ValidationResult:
    scoped_epics = resolve_epic_scope(spec, active_entity_id)
    structural = validate_structural(spec, config, "ticket_decomposition")
    ratio_findings = check_impl_verification_ratio(spec, scoped_epics, config)

    passed = (
        not ratio_findings
        and not structural.invalid_fields
        and not any(f.severity == "error" for f in structural.findings)
    )

    epic_id = active_entity_id[0] if isinstance(active_entity_id, list) else active_entity_id

    kwargs: dict[str, Any] = {
        "phase": "ticket_decomposition",
        "passed": passed,
        "structural": structural,
        "scoring": ScoringResultSkipped(),
        "cross_validation": CrossValidationResult(
            skipped=False,
            findings=ratio_findings,
            ran_checks=["impl-verification-ratio"],
            skipped_checks=[],
        ),
        "meta": build_meta(active_entity_id=active_entity_id),
    }
    if epic_id:
        kwargs["guidance"] = build_ticket_decomposition_guidance(spec, epic_id)

    return ValidationResult(**kwargs)
