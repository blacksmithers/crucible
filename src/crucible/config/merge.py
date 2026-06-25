"""Config deep-merge (port of ``config/merge.ts``)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..types.config import ValidatorConfig
from .schema import validate_config


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, override_val in override.items():
        base_val = base.get(key)
        if (
            isinstance(override_val, dict)
            and isinstance(base_val, dict)
        ):
            result[key] = _deep_merge(base_val, override_val)
        else:
            # Arrays and primitives replace wholesale.
            result[key] = override_val
    return result


def merge_config(
    base: ValidatorConfig,
    *overrides: dict[str, Any],
) -> ValidatorConfig:
    """Deep-merge partial configs onto a base, then validate the result.

    Object fields merge recursively; arrays and primitives are replaced. Later
    overrides win. Inputs are not mutated.
    """
    result: dict[str, Any] = deepcopy(base)
    for override in overrides:
        result = _deep_merge(result, override)
    return validate_config(result)
