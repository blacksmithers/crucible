"""crucible — deterministic validation engine for OpenSpec v1.1 specifications.

Faithful Python port of the SpecForge ``@specforge/validator`` engine.

``validate(spec, context)`` is the single entry point. The structural, scoring,
and cross-validation layers are complete; the guidance prose layer is not yet
assembled (so ``returns=['guidance']`` yields nothing yet).
"""

from __future__ import annotations

from . import models, types
from .api import validate
from .api.input_validation import ValidatorInputError
from .config import (
    HARDCODED_DEFAULTS,
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
from .models import Blueprint, Epic, Specification, Ticket
from .structural import validate_structural

__all__ = [
    "HARDCODED_DEFAULTS",
    "PLANNING_CONFIG_DOMAIN",
    "PLANNING_CONFIG_SCHEMA_VERSION",
    "Blueprint",
    "ConfigValidationError",
    "Epic",
    "PlanningConfigOverridesSchema",
    "PlanningConfigResolver",
    "Specification",
    "Ticket",
    "ValidatorConfigSchema",
    "ValidatorConfigSnapshotSchema",
    "ValidatorInputError",
    "__version__",
    "load_defaults",
    "load_from_file",
    "load_partial_from_file",
    "merge_config",
    "models",
    "types",
    "validate",
    "validate_structural",
]

__version__ = "0.1.0.dev0"
