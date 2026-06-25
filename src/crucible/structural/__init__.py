"""Structural validation layer (port of ``@specforge/validator`` ``src/structural``)."""

from __future__ import annotations

from .._spec import SpecInput, to_spec_dict
from ..types.config import ValidatorConfig
from ..types.phase import ValidationPhase
from ..types.result import StructuralFinding, StructuralResult
from .duplicate_order import check_duplicate_order
from .entity_count_check import check_entity_counts
from .format import check_format
from .presence import check_presence
from .version_resolver import resolve_schema

__all__ = [
    "check_duplicate_order",
    "check_entity_counts",
    "check_format",
    "check_presence",
    "resolve_schema",
    "validate_structural",
]


def validate_structural(
    spec: SpecInput,
    config: ValidatorConfig | None = None,
    phase: ValidationPhase | None = None,
) -> StructuralResult:
    """Run structural-only validation against an OpenSpec v1.1 spec.

    Always runs presence, format, and duplicate-order checks. Pass ``config``
    and ``phase`` to enable phase-aware entity-count checks (M4.16).
    """
    spec_dict = to_spec_dict(spec)

    findings: list[StructuralFinding] = []
    for epic in spec_dict.get("epics") or []:
        for ticket in epic.get("tickets") or []:
            findings.extend(check_duplicate_order(ticket))

    if config is not None and phase is not None:
        findings.extend(check_entity_counts(spec_dict, config, phase))

    return StructuralResult(
        missing_fields=check_presence(spec_dict),
        invalid_fields=check_format(spec_dict),
        findings=findings,
    )
