"""Phase dispatch (port of ``api/dispatcher.ts``)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..types.config import ValidatorConfig
from ..types.phase import SinglePhase
from ..types.result import ValidationResult, ValidationResultAll, ValidationResultAllMeta
from .phases import (
    validate_cross_validation,
    validate_epic_decomposition,
    validate_epic_expansion,
    validate_planning_spec,
    validate_ticket_decomposition,
    validate_ticket_expansion,
)
from .version import get_validator_version

_PHASES = {
    "planning_spec": validate_planning_spec,
    "epic_decomposition": validate_epic_decomposition,
    "epic_expansion": validate_epic_expansion,
    "ticket_decomposition": validate_ticket_decomposition,
    "ticket_expansion": validate_ticket_expansion,
    "cross_validation": validate_cross_validation,
}


def validate_single(
    spec: dict[str, Any],
    phase: SinglePhase,
    active_entity_id: str | list[str] | None,
    config: ValidatorConfig,
) -> ValidationResult:
    fn = _PHASES.get(phase)
    if fn is None:
        raise ValueError(f"Unknown phase: {phase}")
    return fn(spec, active_entity_id, config)


def validate_all(
    spec: dict[str, Any],
    active_entity_id: str | list[str] | None,
    config: ValidatorConfig,
) -> ValidationResultAll:
    by_phase = {
        phase: fn(spec, active_entity_id, config) for phase, fn in _PHASES.items()
    }
    passed = all(r.passed for r in by_phase.values())
    return ValidationResultAll(
        passed=passed,
        by_phase=by_phase,
        meta=ValidationResultAllMeta(
            validator_version=get_validator_version(),
            generated_at=datetime.now(UTC).isoformat(),
        ),
    )
