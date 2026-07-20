"""ticket_decomposition phase (port of ``api/phases/ticket-decomposition.ts``)."""

from __future__ import annotations

from typing import Any

from ...cross_validation.blueprint import check_blueprint_ticket_coverage
from ...engines.ratios import check_impl_verification_ratio
from ...guidance.fixed_prompts import build_ticket_decomposition_guidance
from ...structural import validate_structural
from ...types.config import ValidatorConfig
from ...types.result import CrossValidationResult, ScoringResultSkipped, ValidationResult
from ..scope_resolver import resolve_epic_scope
from ._common import build_meta


def validate_ticket_decomposition(
    spec: dict[str, Any],
    active_entity_id: str | list[str] | None,
    config: ValidatorConfig,
    _existing_files: frozenset[str] | None = None,
) -> ValidationResult:
    scoped_epics = resolve_epic_scope(spec, active_entity_id)
    structural = validate_structural(spec, config, "ticket_decomposition")
    ratio_findings = check_impl_verification_ratio(spec, scoped_epics, config)
    # MB.9.3 — blueprint↔ticket coverage is a decomposition-phase structural gate now
    # (reparented out of cross_validation): tickets are born here + the agent has global
    # task context, so it links each ticket-coverage blueprint to >= minTicketsPerBlueprint
    # tickets via link_blueprint_to_tickets. Called DIRECTLY (mirroring
    # check_impl_verification_ratio) because ticket_decomposition is binary and never
    # invokes run_cross_validation.
    blueprint_coverage_findings = [e.finding for e in check_blueprint_ticket_coverage(spec, config)]

    passed = (
        not ratio_findings
        and not blueprint_coverage_findings
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
            findings=[*ratio_findings, *blueprint_coverage_findings],
            ran_checks=["impl-verification-ratio", "blueprint-coverage"],
            skipped_checks=[],
        ),
        "meta": build_meta(active_entity_id=active_entity_id),
    }
    if epic_id:
        kwargs["guidance"] = build_ticket_decomposition_guidance(spec, epic_id)

    return ValidationResult(**kwargs)
