"""Per-field scoring (port of ``scoring/per-field.ts``)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..guidance.engine.applicability import is_applicable, is_config_applicable
from ..guidance.engine.resolver import resolve_threshold
from ..types.config import ValidatorConfig
from ..types.enums import Tier
from ..types.rubric import RubricEntry, StructuralCheck
from .field_declarations import is_field_declared_na, validate_na_declaration
from .quality_checks import QUALITY_CHECKS, check_range
from .tiers import tier_weight


@dataclass(frozen=True)
class PerFieldResult:
    earned: float
    possible: float
    tier: Tier


def get_field_value(entity: dict[str, Any], field_path: str) -> Any:
    # Strip the entity-type prefix ('specification.goals' -> 'goals').
    dot = field_path.find(".")
    key = field_path if dot == -1 else field_path[dot + 1 :]
    current: Any = entity
    for part in key.split("."):
        if current is None or not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _run_structural_checks(
    entry: RubricEntry,
    value: Any,
    config: ValidatorConfig,
    entity: dict[str, Any],
) -> bool:
    checks = entry.structural_checks
    count_check = next((c for c in checks if c.type == "minCount"), None)
    item_length_check = next(
        (c for c in checks if c.type == "minLength" and c.applies_to == "items"), None
    )
    field_length_check = next(
        (c for c in checks if c.type == "minLength" and (c.applies_to in ("field", None))),
        None,
    )
    item_field_checks = [c for c in checks if c.type == "array-item-field-min-length"]
    other_checks = [
        c
        for c in checks
        if c.type not in ("minCount", "minLength", "array-item-field-min-length")
    ]

    # Cascade: minCount first.
    if count_check is not None:
        minimum = resolve_threshold(count_check, config, entity)
        if not isinstance(value, list) or len(value) < minimum:
            return False

    # Item minLength (only meaningful on a list).
    if item_length_check is not None and isinstance(value, list):
        minimum = resolve_threshold(item_length_check, config, entity)
        if any(isinstance(item, str) and len(item) < minimum for item in value):
            return False

    # Array item object-field minLength.
    if item_field_checks and isinstance(value, list):
        for check in item_field_checks:
            sub_field = check.param
            minimum = resolve_threshold(check, config, entity)
            for item in value:
                v = item.get(sub_field) if isinstance(item, dict) else None
                if not isinstance(v, str) or len(v) < minimum:
                    return False

    # Field minLength.
    if field_length_check is not None:
        minimum = resolve_threshold(field_length_check, config, entity)
        if not isinstance(value, str) or len(value) < minimum:
            return False

    # Other checks.
    return all(_run_other_check(check, value) for check in other_checks)


def _run_other_check(check: StructuralCheck, value: Any) -> bool:
    if check.type == "present":
        return value is not None and value != ""
    if check.type == "enumMember":
        allowed = check.param
        return isinstance(allowed, list) and value in allowed
    if check.type == "pattern":
        return isinstance(value, str) and re.search(str(check.param), value) is not None
    if check.type == "range":
        return check_range(value, check.param)
    fn = QUALITY_CHECKS.get(check.type)
    if fn is not None:
        return fn(value)
    return True


def compute_per_field(
    entity: dict[str, Any],
    entries: list[RubricEntry],
    config: ValidatorConfig,
) -> dict[str, PerFieldResult]:
    result: dict[str, PerFieldResult] = {}

    for entry in entries:
        if not is_applicable(entity, entry):
            continue
        possible = tier_weight(entry.tier, config)

        if not is_config_applicable(entry, config):
            # Bug-for-bug: config-disabled type checks earn full points.
            result[entry.id] = PerFieldResult(possible, possible, entry.tier)
            continue

        if is_field_declared_na(entity, entry.field_path):
            na_result = validate_na_declaration(entity, entry.field_path, entry, config)
            earned = possible if na_result.valid else 0.0
            result[entry.id] = PerFieldResult(earned, possible, entry.tier)
            continue

        value = get_field_value(entity, entry.field_path)
        fulfilled = _run_structural_checks(entry, value, config, entity)
        result[entry.id] = PerFieldResult(possible if fulfilled else 0.0, possible, entry.tier)

    return result
