"""Partial-config override validation (port of ``config/overrides-schema.ts``).

A project override is a sparse ``DeepPartial<ValidatorConfig>``: the user may
set just one threshold without supplying the rest. Cross-field refinements
(weights summing to 1.0, etc.) are **not** enforced on a partial — they only
become meaningful after the override is deep-merged over the defaults
(re-checked by :func:`crucible.config.schema.validate_config`). This validator
therefore checks only the threshold entries that are present.
"""

from __future__ import annotations

from typing import Any

from .schema import _THRESHOLD_SECTIONS, _validate_threshold_entries


def validate_overrides(partial: dict[str, Any]) -> dict[str, Any]:
    sr = partial.get("structuralRequirements")
    if isinstance(sr, dict):
        for section in _THRESHOLD_SECTIONS:
            if section in sr:
                _validate_threshold_entries(sr[section], f"structuralRequirements.{section}")
    return partial


class _PlanningConfigOverridesSchema:
    """Zod-like wrapper exposing ``.parse`` for API parity."""

    def parse(self, partial: dict[str, Any]) -> dict[str, Any]:
        return validate_overrides(partial)


PlanningConfigOverridesSchema = _PlanningConfigOverridesSchema()
