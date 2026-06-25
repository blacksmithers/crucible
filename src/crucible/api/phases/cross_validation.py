"""cross_validation phase (port of ``api/phases/cross-validation.ts``).

Guidance layer deferred (C7) — the per-finding guidance prose (built from the
cross-validation emissions) is not yet assembled, so ``guidance`` is unset.
"""

from __future__ import annotations

import json
from typing import Any

from ...cross_validation import run_cross_validation
from ...structural import validate_structural
from ...types.config import ValidatorConfig
from ...types.result import ValidationResult
from ._common import build_meta


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
    cross_validation = run_cross_validation(spec, config, "cross_validation")

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
        meta=build_meta(active_entity_id=active_entity_id, warnings=warnings or None),
    )
