"""Schema-format checks.

Runs the strict OpenSpec schema and maps Pydantic validation errors to the
``{fieldPath, reason}`` shape, producing the messages and path formatting the
format gate emits. Two skip rules apply: missing required fields (handled by
presence) and ``too_small`` on ``architecture``/``scope``.
"""

from __future__ import annotations

import re
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


def _received(value: Any) -> str:
    """The type token for an input value (used in the ``Expected X, received Y``
    invalid_type message)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


# Pydantic strict type-mismatch error -> the expected type token.
_INVALID_TYPE_EXPECTED = {
    "string_type": "string",
    "int_type": "number",
    "float_type": "number",
    "model_type": "object",
    "dict_type": "object",
    "list_type": "array",
}


def _invalid_type_reason(err: ErrorDetails) -> str | None:
    """Build the ``Expected {expected}, received {received}`` message for a strict
    type mismatch (a coerced-away value or an explicit null on an optional)."""
    etype = err["type"]
    expected = _INVALID_TYPE_EXPECTED.get(etype)
    if expected is None:
        return None
    value = err.get("input")
    # An integer field given a non-integer number reports the integer refinement:
    # "Expected integer, received float".
    if etype == "int_type" and isinstance(value, float) and not isinstance(value, bool):
        return "Expected integer, received float"
    return f"Expected {expected}, received {_received(value)}"


def _enum_reason(err: ErrorDetails) -> str:
    """Build the ``Invalid enum value. Expected a | b, received 'x'`` message.

    Pydantic's ``ctx['expected']`` pre-formats the options as ``'a', 'b' or 'c'``;
    the quoted tokens are extracted and rejoined with the ``' | '`` separator.
    """
    ctx = err.get("ctx") or {}
    options = re.findall(r"'[^']*'", str(ctx.get("expected", "")))
    joined = " | ".join(options)
    received = err.get("input")
    return f"Invalid enum value. Expected {joined}, received '{received}'"


def _reason(err: ErrorDetails) -> str:
    etype = err["type"]
    ctx = err.get("ctx") or {}
    if etype == "enum":
        return _enum_reason(err)
    invalid_type = _invalid_type_reason(err)
    if invalid_type is not None:
        return invalid_type
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
