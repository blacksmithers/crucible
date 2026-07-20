"""crucible — deterministic validation engine for OpenSpec v1.1 specifications.

Faithful Python port of the SpecForge ``@specforge/validator`` engine.

``validate(spec, context)`` is the single entry point. All four return layers
(``structural``, ``scoring``, ``crossValidation``, ``guidance``) are complete
and verified byte-for-byte against the reference engine.
"""

from __future__ import annotations

from . import models, types
from .api import validate
from .api.input_validation import ValidatorInputError
from .config import (
    CONFIG_DEFAULTS,
    PLANNING_CONFIG_DOMAIN,
    PLANNING_CONFIG_SCHEMA_VERSION,
    ConfigValidationError,
    PlanningConfigOverridesSchema,
    PlanningConfigResolver,
    ValidatorConfigSchema,
    ValidatorConfigSnapshotSchema,
    load_defaults,
    load_from_file,
    load_partial_from_file,
    merge_config,
)
from .cross_validation.concurrent_modification import check_concurrent_modification
from .cross_validation.creator_election import elect_file_creators
from .cross_validation.cycle_analysis import analyze_cycle_edges
from .cross_validation.file_provenance import (
    FileProvenanceContext,
    check_file_consistency,
    check_file_provenance,
    compute_grep_candidates,
)
from .models import Blueprint, Epic, Specification, Ticket
from .na_eligible import (
    CROSS_CUTTING_NA_ELIGIBLE_SCOPES,
    is_na_eligible_scope,
    na_eligible_scopes_for,
)
from .structural import validate_structural

__all__ = [
    "CONFIG_DEFAULTS",
    "CROSS_CUTTING_NA_ELIGIBLE_SCOPES",
    "PLANNING_CONFIG_DOMAIN",
    "PLANNING_CONFIG_SCHEMA_VERSION",
    "Blueprint",
    "ConfigValidationError",
    "Epic",
    "FileProvenanceContext",
    "PlanningConfigOverridesSchema",
    "PlanningConfigResolver",
    "Specification",
    "Ticket",
    "ValidatorConfigSchema",
    "ValidatorConfigSnapshotSchema",
    "ValidatorInputError",
    "__version__",
    "analyze_cycle_edges",
    "check_concurrent_modification",
    "check_file_consistency",
    "check_file_provenance",
    "compute_grep_candidates",
    "elect_file_creators",
    "is_na_eligible_scope",
    "load_defaults",
    "load_from_file",
    "load_partial_from_file",
    "merge_config",
    "models",
    "na_eligible_scopes_for",
    "types",
    "validate",
    "validate_structural",
]

__version__ = "0.3.0"
