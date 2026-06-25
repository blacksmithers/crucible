"""Threshold resolution (port of ``guidance/engine/resolver.ts``).

Resolves a structural check's numeric threshold from its ``config:<dot.path>``
source (static entry → ``.default``; complexity-driven → per-complexity bucket)
or from an inline numeric ``param``.
"""

from __future__ import annotations

from typing import Any

from ...types.config import ValidatorConfig
from ...types.rubric import StructuralCheck

_COMPLEXITY_DRIVEN_PREFIX = "config:structuralRequirements.complexityDrivenMinCounts."


def _get_by_dot_path(obj: Any, path: str) -> Any:
    acc: Any = obj
    for key in path.split("."):
        if acc is None or not isinstance(acc, dict):
            return None
        acc = acc.get(key)
    return acc


def resolve_source(source: str, config: ValidatorConfig) -> float:
    if not source.startswith("config:"):
        raise ValueError(f'Invalid source: "{source}". Must start with \'config:\'')
    path = source[len("config:") :]
    value = _get_by_dot_path(config, path)

    if value is None:
        raise ValueError(f'Config path not found: "{path}"')
    if isinstance(value, dict) and "default" in value:
        return float(value["default"])
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    raise ValueError(f'Config path "{path}" resolved to non-numeric: {type(value).__name__}')


def _resolve_complexity_driven(
    source: str, config: ValidatorConfig, entity: dict[str, Any] | None
) -> float:
    path = source[len("config:") :]
    value = _get_by_dot_path(config, path)
    if not isinstance(value, dict):
        raise ValueError(f'complexityDrivenMinCounts path not found: "{path}"')
    # Schema requires complexity on Ticket; fall back to 'medium' for entities
    # that bypassed validation (mirrors the TS resolver).
    complexity = (entity or {}).get("complexity") or "medium"
    driven = value.get(complexity)
    if not isinstance(driven, (int, float)) or isinstance(driven, bool):
        raise ValueError(
            f'complexityDrivenMinCounts at "{path}" is missing complexity "{complexity}"'
        )
    return float(driven)


def resolve_threshold(
    check: StructuralCheck,
    config: ValidatorConfig,
    entity: dict[str, Any] | None = None,
) -> float:
    if check.source:
        if check.source.startswith(_COMPLEXITY_DRIVEN_PREFIX):
            return _resolve_complexity_driven(check.source, config, entity)
        return resolve_source(check.source, config)
    if isinstance(check.param, (int, float)) and not isinstance(check.param, bool):
        return float(check.param)
    raise ValueError(
        f"StructuralCheck type='{check.type}' has neither source nor numeric param"
    )
