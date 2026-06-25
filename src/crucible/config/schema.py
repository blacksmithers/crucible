"""Config validation + default injection (port of ``config/schema.ts``).

The TS source uses Zod. Here we keep the runtime config as a plain ``dict`` and
reproduce the two behaviors that affect output: (1) ``.default()`` injection for
omitted optional fields, and (2) refinement checks that raise on invalid input.
Validation never mutates values beyond injecting the documented defaults.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..types.config import ValidatorConfig

_THRESHOLD_SECTIONS = (
    "arrayMinCounts",
    "arrayMaxCounts",
    "stringMinLengths",
    "itemMinLengths",
    "arrayItemFieldMinLengths",
)


class ConfigValidationError(ValueError):
    """Raised when a config fails schema validation (mirrors a Zod parse error)."""


def _is_threshold_entry(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and {"default", "min", "max"} <= value.keys()
        and all(isinstance(value[k], (int, float)) for k in ("default", "min", "max"))
    )


def apply_defaults(cfg: ValidatorConfig) -> ValidatorConfig:
    """Inject the optional-field defaults the Zod schema would supply."""
    sr = cfg.get("structuralRequirements")
    if isinstance(sr, dict):
        sr.setdefault("enforceTypes", True)
        sr.setdefault("arrayMaxCounts", {})
        sr.setdefault("arrayCountPhases", {})
        sr.setdefault("arrayItemFieldMinLengths", {})
        sr.setdefault("complexityDrivenMinCounts", {})

    checks = cfg.get("crossValidation", {}).get("checks", {})
    bp = checks.get("blueprint-coverage") if isinstance(checks, dict) else None
    if isinstance(bp, dict):
        bp.setdefault("minTicketsPerBlueprint", 2)
    return cfg


def _validate_threshold_entries(node: Any, path: str) -> None:
    if _is_threshold_entry(node):
        default, lo, hi = node["default"], node["min"], node["max"]
        if not (lo <= default <= hi):
            raise ConfigValidationError(f"{path}: default must be within [min, max]")
        if not (hi > lo):
            raise ConfigValidationError(f"{path}: max must be strictly greater than min")
        return
    if isinstance(node, dict):
        for key, child in node.items():
            _validate_threshold_entries(child, f"{path}.{key}")


def _validate_refinements(cfg: ValidatorConfig) -> None:
    thresholds = cfg.get("thresholds", {})
    for key in ("global", "specification", "epic", "ticket"):
        val = thresholds.get(key)
        if isinstance(val, (int, float)) and not (0 <= val <= 100):
            raise ConfigValidationError(f"thresholds.{key} must be within [0, 100]")

    weights = cfg.get("scoring", {}).get("weights", {})
    if {"spec", "epics", "tickets"} <= weights.keys():
        total = weights["spec"] + weights["epics"] + weights["tickets"]
        if abs(total - 1.0) >= 1e-6:
            raise ConfigValidationError("scoring.weights must sum to 1.0")

    top_n = cfg.get("guidance", {}).get("topNPerEntity", {})
    if {"default", "min", "max"} <= top_n.keys() and not (
        top_n["min"] <= top_n["default"] <= top_n["max"]
    ):
        raise ConfigValidationError("guidance.topNPerEntity.default must be within [min, max]")

    sr = cfg.get("structuralRequirements", {})
    for section in _THRESHOLD_SECTIONS:
        if section in sr:
            _validate_threshold_entries(sr[section], f"structuralRequirements.{section}")


def validate_config(raw: ValidatorConfig) -> ValidatorConfig:
    """Parse + validate a full config (mirror of ``ValidatorConfigSchema.parse``)."""
    cfg = apply_defaults(deepcopy(raw))
    _validate_refinements(cfg)
    return cfg


class _ValidatorConfigSchema:
    """Zod-like wrapper exposing ``.parse`` for API parity with the TS source."""

    def parse(self, raw: ValidatorConfig) -> ValidatorConfig:
        return validate_config(raw)


ValidatorConfigSchema = _ValidatorConfigSchema()
