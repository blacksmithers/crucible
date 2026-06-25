"""Cross-validation layer (port of ``@specforge/validator`` ``src/cross-validation``).

Findings only — the per-finding guidance prose is produced by the guidance
layer. Runs the 13-check registry (insertion order preserved), honoring each
check's ``enabled`` flag and ``enabledPhases``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..types.config import ValidatorConfig
from ..types.phase import ValidationPhase
from ..types.result import CrossValidationFinding, CrossValidationResult, SkippedCheck
from .blueprint import check_blueprint_ticket_coverage
from .dependency_graph import (
    check_broken_reference,
    check_island_ticket,
    check_orphan_reference,
    detect_cycles,
)
from .files import check_file_consistency, check_files_to_be_referenced
from .topology import check_topology_leaves_exceed, check_topology_roots_exceed
from .waves import (
    check_wave_concurrent_modification,
    check_wave_deletion_after_creation,
    check_wave_deletion_after_modification,
    check_wave_size_exceed,
)

CheckFn = Callable[[dict[str, Any], ValidatorConfig], list[CrossValidationFinding]]

# Insertion order is the finding order — mirrors the TS CHECK_REGISTRY.
CHECK_REGISTRY: dict[str, CheckFn] = {
    "circular-dependency": lambda spec, _cfg: detect_cycles(spec),
    "broken-reference": lambda spec, _cfg: check_broken_reference(spec),
    "orphan-reference": check_orphan_reference,
    "island-ticket": check_island_ticket,
    "topology-roots-exceed": check_topology_roots_exceed,
    "topology-leaves-exceed": check_topology_leaves_exceed,
    "wave-size-exceed": check_wave_size_exceed,
    "wave-concurrent-modification": lambda spec, _cfg: check_wave_concurrent_modification(spec),
    "wave-deletion-after-modification": lambda spec, _cfg: check_wave_deletion_after_modification(
        spec
    ),
    "wave-deletion-after-creation": lambda spec, _cfg: check_wave_deletion_after_creation(spec),
    "file-conflict": lambda spec, _cfg: check_file_consistency(spec),
    "files-to-be-referenced": lambda spec, _cfg: check_files_to_be_referenced(spec),
    "blueprint-coverage": check_blueprint_ticket_coverage,
}

__all__ = ["CHECK_REGISTRY", "run_cross_validation"]


def run_cross_validation(
    spec: dict[str, Any],
    config: ValidatorConfig,
    phase: ValidationPhase,
) -> CrossValidationResult:
    checks_config = config["crossValidation"]["checks"]

    findings: list[CrossValidationFinding] = []
    ran_checks: list[str] = []
    skipped_checks: list[SkippedCheck] = []

    for check_name, check_fn in CHECK_REGISTRY.items():
        check_config = checks_config.get(check_name)
        if not check_config or not check_config.get("enabled"):
            skipped_checks.append(SkippedCheck(name=check_name, reason="disabled"))
            continue
        if phase not in check_config["enabledPhases"]:
            skipped_checks.append(
                SkippedCheck(name=check_name, reason=f"phase-not-enabled ({phase})")
            )
            continue
        findings.extend(check_fn(spec, config))
        ran_checks.append(check_name)

    if not ran_checks:
        return CrossValidationResult(
            skipped=True, reason="no-checks-active-for-phase", findings=[]
        )

    return CrossValidationResult(
        skipped=False,
        findings=findings,
        ran_checks=ran_checks,
        skipped_checks=skipped_checks,
    )
