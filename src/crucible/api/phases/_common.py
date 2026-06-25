"""Shared helpers for phase assembly."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ...guidance.composer import compose_findings
from ...guidance.engine import execute_rubric
from ...guidance.format import format_guidance
from ...scoring.global_ import GlobalScoreBreakdown as _InternalBreakdown
from ...scoring.per_field import PerFieldResult
from ...types.cascade import CascadeFailure, CascadeFloors
from ...types.context import PhaseContext
from ...types.guidance import GuidanceResult
from ...types.result import (
    GlobalScoreBreakdown,
    PerFieldScore,
    ScoringResultActive,
    ValidationResultMeta,
)
from ..version import get_validator_version


def build_guidance(spec: dict[str, Any], context: PhaseContext) -> GuidanceResult:
    findings = execute_rubric(spec, context)
    composites = compose_findings(findings, context, spec)
    composed_ids = {f.rubric_entry_id for c in composites for f in c.grouped_findings}
    individuals = [
        f
        for f in findings
        if f.rubric_entry_id not in composed_ids and f.status != "fulfilled"
    ]
    return format_guidance(composites, individuals, context, spec)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def build_meta(
    *,
    active_entity_id: str | list[str] | None = None,
    resolution: str | None = None,
    warnings: list[str] | None = None,
) -> ValidationResultMeta:
    kwargs: dict[str, object] = {
        "validator_version": get_validator_version(),
        "generated_at": now_iso(),
    }
    if active_entity_id is not None:
        kwargs["active_entity_id"] = active_entity_id
    if resolution is not None:
        kwargs["resolution"] = resolution
    if warnings:
        kwargs["warnings"] = warnings
    return ValidationResultMeta(**kwargs)


def per_field_to_scores(per_field: dict[str, PerFieldResult]) -> dict[str, PerFieldScore]:
    return {
        k: PerFieldScore(earned=v.earned, possible=v.possible, tier=v.tier)
        for k, v in per_field.items()
    }


def breakdown_model(b: _InternalBreakdown) -> GlobalScoreBreakdown:
    return GlobalScoreBreakdown(
        spec_block=b.spec_block,
        epic_block=b.epic_block,
        ticket_block=b.ticket_block,
        epic_avg=b.epic_avg,
        ticket_avg=b.ticket_avg,
        weights=b.weights,
    )


def build_active_scoring(
    *,
    local_score: float,
    per_field: dict[str, PerFieldScore],
    breakdown: _InternalBreakdown,
    cascade_floors: CascadeFloors,
    cascade_failures: list[CascadeFailure],
    gate_result: str,
    threshold: float,
    per_entity_score: dict[str, float] | None = None,
) -> ScoringResultActive:
    kwargs: dict[str, object] = {
        "skipped": False,
        "local_score": local_score,
        "global_score": breakdown.global_score,
        "per_field": per_field,
        "topology_penalties": breakdown.topology_penalty,
        "gate_result": gate_result,
        "threshold": threshold,
        "global_score_breakdown": breakdown_model(breakdown),
        "cascade_floors": cascade_floors,
        "cascade_failures": cascade_failures,
    }
    if per_entity_score is not None:
        kwargs["per_entity_score"] = per_entity_score
    return ScoringResultActive(**kwargs)
