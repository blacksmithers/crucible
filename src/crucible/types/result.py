"""Validation result contracts (port of ``types/result.ts``).

These are the public, serialized output shapes. Optional layer fields appear
only when requested via ``returns``. The discriminated ``ScoringResult`` keeps
explicit ``null`` for the skipped variant (set in the engine) while the active
variant omits unset optionals — see ``CamelModel`` for the fidelity rule.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import model_serializer

from ._base import CamelModel
from .cascade import CascadeFailure, CascadeFloors
from .config import ScoringWeights
from .enums import Severity, Tier
from .guidance import GuidanceResult
from .phase import SinglePhase


# ---------------------------------------------------------------------------
# Structural layer
# ---------------------------------------------------------------------------
class StructuralFinding(CamelModel):
    category: str
    severity: Severity
    field: str
    message: str
    # M4.16 optional rich shape (entity-count check populates these).
    guidance: str | None = None
    operations: list[str] | None = None
    context: dict[str, Any] | None = None


class InvalidField(CamelModel):
    field_path: str
    reason: str


class StructuralResult(CamelModel):
    missing_fields: list[str]
    invalid_fields: list[InvalidField]
    findings: list[StructuralFinding]


# ---------------------------------------------------------------------------
# Scoring layer
# ---------------------------------------------------------------------------
class PerFieldScore(CamelModel):
    earned: float
    possible: float
    tier: Tier


class GlobalScoreBreakdown(CamelModel):
    spec_block: float
    epic_block: float
    ticket_block: float
    epic_avg: float | None
    ticket_avg: float | None
    weights: ScoringWeights


class ScoringResultActive(CamelModel):
    skipped: Literal[False] = False
    local_score: float
    global_score: float | None = None
    per_field: dict[str, PerFieldScore]
    per_entity_score: dict[str, float] | None = None
    topology_penalties: float | None = None
    gate_result: Literal["pass", "fail"]
    threshold: float
    global_score_breakdown: GlobalScoreBreakdown | None = None
    cascade_floors: CascadeFloors | None = None
    cascade_failures: list[CascadeFailure] | None = None


class ScoringResultSkipped(CamelModel):
    skipped: Literal[True] = True
    reason: Literal["no-rubric-for-phase"] = "no-rubric-for-phase"
    local_score: None = None
    global_score: None = None
    per_field: dict[str, Any] = {}  # noqa: RUF012 — always {} in output
    gate_result: Literal["n/a"] = "n/a"
    threshold: None = None

    @model_serializer
    def _serialize(self) -> dict[str, Any]:
        # Fixed shape with explicit nulls kept (mirrors the TS skipped record),
        # emitted in full even when nested under a parent dumped exclude_unset.
        return {
            "skipped": True,
            "reason": self.reason,
            "localScore": None,
            "globalScore": None,
            "perField": {},
            "gateResult": "n/a",
            "threshold": None,
        }


ScoringResult = ScoringResultActive | ScoringResultSkipped


# ---------------------------------------------------------------------------
# Cross-validation layer
# ---------------------------------------------------------------------------
class CrossValidationFinding(CamelModel):
    category: str
    severity: Severity
    field: str
    message: str
    entity_ids: list[str]
    primary_entity_id: str
    operations: list[str]
    context: dict[str, Any] | None = None


class CrossValidationEmission(CamelModel):
    finding: CrossValidationFinding
    guidance: str


class SkippedCheck(CamelModel):
    name: str
    reason: str


class CrossValidationResult(CamelModel):
    findings: list[CrossValidationFinding]
    skipped: bool | None = None
    reason: str | None = None
    ran_checks: list[str] | None = None
    skipped_checks: list[SkippedCheck] | None = None


# ---------------------------------------------------------------------------
# Top-level results
# ---------------------------------------------------------------------------
class ValidationResultMeta(CamelModel):
    validator_version: str
    generated_at: str
    active_entity_id: str | list[str] | None = None
    resolution: Literal["all", "by-epic", "by-ticket", "mixed"] | None = None
    warnings: list[str] | None = None


class ValidationResult(CamelModel):
    phase: SinglePhase
    passed: bool
    meta: ValidationResultMeta
    structural: StructuralResult | None = None
    scoring: ScoringResult | None = None
    cross_validation: CrossValidationResult | None = None
    guidance: GuidanceResult | None = None


class ValidationResultAllMeta(CamelModel):
    validator_version: str
    generated_at: str


class ValidationResultAll(CamelModel):
    phase: Literal["all"] = "all"
    passed: bool
    # Keys are the six concrete phase names (snake_case, never camelCased).
    by_phase: dict[str, ValidationResult]
    meta: ValidationResultAllMeta
