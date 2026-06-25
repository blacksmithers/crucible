"""Config loading (port of ``config/load.ts``)."""

from __future__ import annotations

from copy import deepcopy
from importlib import resources
from typing import Any, cast

import yaml

from ..types.config import ValidatorConfig
from .defaults import CONFIG_DEFAULTS
from .schema import validate_config


def load_defaults() -> ValidatorConfig:
    """Load the canonical default config from the packaged ``defaults.yml``.

    Validated through the schema; falls back to :data:`CONFIG_DEFAULTS` if the
    packaged YAML is missing or fails to parse, so callers always get a usable
    config.
    """
    try:
        raw = (
            resources.files("crucible.config.data")
            .joinpath("defaults.yml")
            .read_text(encoding="utf-8")
        )
        parsed = cast(ValidatorConfig, yaml.safe_load(raw))
        return validate_config(parsed)
    except Exception:
        return deepcopy(CONFIG_DEFAULTS)


def load_from_file(file_path: str) -> ValidatorConfig:
    """Load and validate a complete config from a YAML file on disk."""
    with open(file_path, encoding="utf-8") as fh:
        parsed = cast(ValidatorConfig, yaml.safe_load(fh))
    return validate_config(parsed)


def load_partial_from_file(file_path: str) -> dict[str, Any]:
    """Load a partial config from a YAML file without validation."""
    with open(file_path, encoding="utf-8") as fh:
        return cast("dict[str, Any]", yaml.safe_load(fh))
