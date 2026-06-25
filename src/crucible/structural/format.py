"""Schema-format checks (port of ``structural/format.ts``).

Runs the strict OpenSpec schema and maps Pydantic validation errors to the
Zod-style ``{fieldPath, reason}`` shape, reproducing the messages and path
formatting the TS engine emits. Mirrors the two skip rules: missing required
fields (handled by presence) and ``too_small`` on ``architecture``/``scope``.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from ..types.result import InvalidField
from ._strict_schema import SpecificationStrict

_TOO_SMALL_TYPES = frozenset(
    {"too_short", "string_too_short", "greater_than", "greater_than_equal"}
)


def _path_to_string(path: tuple[Any, ...]) -> str:
    parts: list[str] = []
    for i, p in enumerate(path):
        if isinstance(p, int):
            parts.append(f"[{p}]")
        else:
            parts.append(p if i == 0 else f".{p}")
    return "".join(parts).replace(".[", "[")


def _reason(err: ErrorDetails) -> str:
    etype = err["type"]
    ctx = err.get("ctx") or {}
    if etype == "too_short":
        return f"Array must contain at least {ctx.get('min_length')} element(s)"
    if etype == "string_too_short":
        return f"String must contain at least {ctx.get('min_length')} character(s)"
    if etype == "too_long":
        return f"Array must contain at most {ctx.get('max_length')} element(s)"
    if etype == "string_too_long":
        return f"String must contain at most {ctx.get('max_length')} character(s)"
    if etype == "greater_than_equal":
        return f"Number must be greater than or equal to {ctx.get('ge')}"
    if etype == "greater_than":
        return f"Number must be greater than {ctx.get('gt')}"
    if etype == "less_than_equal":
        return f"Number must be less than or equal to {ctx.get('le')}"
    if etype == "less_than":
        return f"Number must be less than {ctx.get('lt')}"
    # Fallback: Pydantic message (covers rare enum/literal/type cases not in the
    # golden corpus). Differential tests cover the array/string-min cases above.
    return str(err.get("msg", ""))


def check_format(spec: dict[str, Any]) -> list[InvalidField]:
    try:
        SpecificationStrict.model_validate(spec)
        return []
    except ValidationError as exc:
        invalid: list[InvalidField] = []
        for err in exc.errors():
            etype = err["type"]
            loc = err["loc"]
            # Missing required fields are handled by presence checks.
            if etype == "missing":
                continue
            # too_small on architecture/scope is handled by presence.
            if etype in _TOO_SMALL_TYPES and any(
                p in ("architecture", "scope") for p in loc
            ):
                continue
            invalid.append(
                InvalidField(field_path=_path_to_string(loc), reason=_reason(err))
            )
        return invalid
