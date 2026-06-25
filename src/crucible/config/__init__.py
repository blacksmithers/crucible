"""Validator configuration (port of ``@specforge/validator`` ``src/config``)."""

from __future__ import annotations

from .defaults import HARDCODED_DEFAULTS, hardcoded_defaults
from .load import load_defaults, load_from_file, load_partial_from_file
from .merge import merge_config
from .overrides import PlanningConfigOverridesSchema, validate_overrides
from .resolver import (
    PLANNING_CONFIG_DOMAIN,
    PLANNING_CONFIG_SCHEMA_VERSION,
    IConfigStore,
    PlanningConfigResolver,
)
from .schema import ConfigValidationError, ValidatorConfigSchema, validate_config
from .snapshot import ValidatorConfigSnapshotSchema

__all__ = [
    "HARDCODED_DEFAULTS",
    "PLANNING_CONFIG_DOMAIN",
    "PLANNING_CONFIG_SCHEMA_VERSION",
    "ConfigValidationError",
    "IConfigStore",
    "PlanningConfigOverridesSchema",
    "PlanningConfigResolver",
    "ValidatorConfigSchema",
    "ValidatorConfigSnapshotSchema",
    "hardcoded_defaults",
    "load_defaults",
    "load_from_file",
    "load_partial_from_file",
    "merge_config",
    "validate_config",
    "validate_overrides",
]
