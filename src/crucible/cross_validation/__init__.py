"""Cross-validation layer.

Runs the 11-entry registry (insertion order preserved), honoring each check's
``enabled`` flag and ``enabledPhases``. Each check yields emissions (finding +
guidance prose); the layer result carries findings, the guidance layer consumes
the prose.

At most 10 run in ``cross_validation``: ``blueprint-coverage`` is
registry-resident but phase-gated out of it (it is called directly
by ``validate_ticket_decomposition``) — see ``config/defaults.py``.

Checks receive a third ``ctx`` argument carrying the grep evidence
(``existing_files``); only ``file-provenance`` reads it today. The fourth
``language`` argument selects the guidance-prose catalog (``crucible.i18n``) —
finding ``message``s stay canonical English (data layer), only the emission
``guidance`` prose is translated.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..types.config import ValidatorConfig
from ..types.phase import ValidationPhase
from ..types.result import CrossValidationFinding, CrossValidationResult, SkippedCheck
from .blueprint import check_blueprint_ticket_coverage
from .concurrent_modification import check_concurrent_modification
from .dependency_graph import (
    check_broken_reference,
    check_island_ticket,
    check_orphan_reference,
    detect_cycles,
)
from .emission import CVEmission
from .file_provenance import (
    FileProvenanceContext,
    check_file_consistency,
    check_file_provenance,
)
from .topology import check_topology_leaves_exceed, check_topology_roots_exceed
from .waves import check_wave_size_exceed

CheckFn = Callable[
    [dict[str, Any], ValidatorConfig, FileProvenanceContext, str], list[CVEmission]
]

# Insertion order is the finding order.
CHECK_REGISTRY: dict[str, CheckFn] = {
    "circular-dependency": lambda spec, _cfg, _ctx, lang: detect_cycles(spec, lang),
    "broken-reference": lambda spec, _cfg, _ctx, lang: check_broken_reference(spec, lang),
    "orphan-reference": lambda spec, cfg, _ctx, lang: check_orphan_reference(spec, cfg, lang),
    "island-ticket": lambda spec, cfg, _ctx, lang: check_island_ticket(spec, cfg, lang),
    "topology-roots-exceed": lambda spec, cfg, _ctx, lang: check_topology_roots_exceed(
        spec, cfg, lang
    ),
    "topology-leaves-exceed": lambda spec, cfg, _ctx, lang: check_topology_leaves_exceed(
        spec, cfg, lang
    ),
    "wave-size-exceed": lambda spec, cfg, _ctx, lang: check_wave_size_exceed(spec, cfg, lang),
    "concurrent-modification": lambda spec, _cfg, _ctx, lang: check_concurrent_modification(
        spec, lang
    ),
    "file-conflict": lambda spec, _cfg, _ctx, lang: check_file_consistency(spec, lang),
    "file-provenance": lambda spec, cfg, ctx, lang: check_file_provenance(spec, cfg, ctx, lang),
    "blueprint-coverage": lambda spec, cfg, _ctx, lang: check_blueprint_ticket_coverage(
        spec, cfg, lang
    ),
}

__all__ = ["CHECK_REGISTRY", "CrossValidationRunOutput", "run_cross_validation"]


@dataclass(frozen=True)
class CrossValidationRunOutput:
    result: CrossValidationResult
    emissions: list[CVEmission]


def run_cross_validation(
    spec: dict[str, Any],
    config: ValidatorConfig,
    phase: ValidationPhase,
    existing_files: frozenset[str] | None = None,
    language: str = "en",
) -> CrossValidationRunOutput:
    checks_config = config["crossValidation"]["checks"]
    ctx = FileProvenanceContext(existing_files=existing_files)

    emissions: list[CVEmission] = []
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
        check_emissions = check_fn(spec, config, ctx, language)
        emissions.extend(check_emissions)
        findings.extend(e.finding for e in check_emissions)
        ran_checks.append(check_name)

    if not ran_checks:
        return CrossValidationRunOutput(
            result=CrossValidationResult(
                skipped=True, reason="no-checks-active-for-phase", findings=[]
            ),
            emissions=[],
        )

    return CrossValidationRunOutput(
        result=CrossValidationResult(
            skipped=False,
            findings=findings,
            ran_checks=ran_checks,
            skipped_checks=skipped_checks,
        ),
        emissions=emissions,
    )
