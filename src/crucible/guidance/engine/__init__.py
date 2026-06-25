"""Guidance engine internals (applicability + threshold resolution)."""

from __future__ import annotations

from .applicability import is_applicable, is_config_applicable
from .finding_engine import compute_global_impact_on_fix, derive_leaf_field, execute_rubric
from .resolver import resolve_source, resolve_threshold
from .value_resolver import entry_matches_entity_type, get_entity_type, resolve_field_value

__all__ = [
    "compute_global_impact_on_fix",
    "derive_leaf_field",
    "entry_matches_entity_type",
    "execute_rubric",
    "get_entity_type",
    "is_applicable",
    "is_config_applicable",
    "resolve_field_value",
    "resolve_source",
    "resolve_threshold",
]
