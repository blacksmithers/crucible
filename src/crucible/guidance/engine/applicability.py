"""Rubric applicability (port of ``guidance/engine/applicability.ts``).

Operates on the normalized camelCase entity dict.
"""

from __future__ import annotations

from typing import Any

from ...types.config import ValidatorConfig
from ...types.rubric import RubricEntry


def is_applicable(entity: dict[str, Any], entry: RubricEntry) -> bool:
    cond = entry.conditional_applicability
    if cond is None:
        return True
    return bool(entity.get(cond.field) == cond.equals)


def is_config_applicable(entry: RubricEntry, config: ValidatorConfig) -> bool:
    if entry.applicability_check == "enforceTypes":
        return bool(config["structuralRequirements"]["enforceTypes"])
    return True
