"""Scoring layer (port of ``@specforge/validator`` ``src/scoring``)."""

from __future__ import annotations

from .cascade import (
    CascadeGateInput,
    CascadeGateResult,
    compute_cascade_floors,
    evaluate_cascade_gate,
    phase_includes_epics,
    phase_includes_tickets,
)
from .field_declarations import (
    NAValidationResult,
    is_field_declared_na,
    validate_na_declaration,
)
from .global_ import GlobalScoreBreakdown, compute_global_score
from .per_entity import EntityScoreResult, compute_entity_score
from .per_field import PerFieldResult, compute_per_field, get_field_value
from .quality_checks import QUALITY_CHECKS, check_range
from .tiers import tier_weight
from .topology import TopologyResult, compute_topology_penalties

__all__ = [
    "QUALITY_CHECKS",
    "CascadeGateInput",
    "CascadeGateResult",
    "EntityScoreResult",
    "GlobalScoreBreakdown",
    "NAValidationResult",
    "PerFieldResult",
    "TopologyResult",
    "check_range",
    "compute_cascade_floors",
    "compute_entity_score",
    "compute_global_score",
    "compute_per_field",
    "compute_topology_penalties",
    "evaluate_cascade_gate",
    "get_field_value",
    "is_field_declared_na",
    "phase_includes_epics",
    "phase_includes_tickets",
    "tier_weight",
    "validate_na_declaration",
]
