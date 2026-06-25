"""Composite-finding composition (port of ``guidance/composer/index.ts``)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ...types.context import PhaseContext
from ...types.finding import CompositeFinding, Finding
from .patterns import (
    detect_conditional_gap,
    detect_foundation_gap,
    detect_integrity_gap,
    detect_linkage_gap,
    detect_tactical_gap,
)

PatternFn = Callable[[list[Finding], PhaseContext, dict[str, Any]], list[CompositeFinding]]

_PATTERNS_BY_PHASE: dict[str, list[PatternFn]] = {
    "planning_spec": [detect_foundation_gap, detect_conditional_gap],
    "epic_decomposition": [],
    "epic_expansion": [detect_foundation_gap, detect_tactical_gap],
    "ticket_decomposition": [],
    "ticket_expansion": [detect_foundation_gap, detect_tactical_gap, detect_conditional_gap],
    "cross_validation": [
        detect_foundation_gap,
        detect_tactical_gap,
        detect_conditional_gap,
        detect_linkage_gap,
        detect_integrity_gap,
    ],
}

__all__ = ["compose_findings"]


def compose_findings(
    findings: list[Finding], context: PhaseContext, spec: dict[str, Any]
) -> list[CompositeFinding]:
    results: list[CompositeFinding] = []
    for pattern in _PATTERNS_BY_PHASE.get(context.phase, []):
        results.extend(pattern(findings, context, spec))
    return results
