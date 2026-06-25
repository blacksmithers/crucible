"""Public ``validate`` entry point (port of ``api/validate.ts``).

NOTE: the guidance layer is not yet assembled (C7), so single-phase results do
not carry a ``guidance`` field, and ``returns=['guidance']`` yields nothing.
The structural, scoring, and crossValidation layers are complete.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from .._spec import SpecInput, to_spec_dict
from ..config import load_defaults
from ..types.phase import ReturnLayer, SinglePhase
from ..types.result import ValidationResult, ValidationResultAll
from .dispatcher import validate_all, validate_single
from .input_validation import validate_input

_DEFAULT_RETURNS_ALL: list[ReturnLayer] = ["scoring"]

_LAYER_ATTR = {
    "structural": "structural",
    "scoring": "scoring",
    "crossValidation": "cross_validation",
    "guidance": "guidance",
}


def _normalize_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    ctx: dict[str, Any] = dict(context) if context else {}
    out: dict[str, Any] = {}
    if "phase" in ctx:
        out["phase"] = ctx["phase"]
    if "activeEntityId" in ctx:
        out["activeEntityId"] = ctx["activeEntityId"]
    elif "active_entity_id" in ctx:
        out["activeEntityId"] = ctx["active_entity_id"]
    if "config" in ctx:
        out["config"] = ctx["config"]
    if "returns" in ctx:
        out["returns"] = ctx["returns"]
    return out


def _filter_all_returns(
    result: ValidationResultAll, returns: list[ReturnLayer]
) -> ValidationResultAll:
    new_by_phase: dict[str, ValidationResult] = {}
    for phase, r in result.by_phase.items():
        kwargs: dict[str, Any] = {"phase": r.phase, "passed": r.passed, "meta": r.meta}
        for layer, attr in _LAYER_ATTR.items():
            value = getattr(r, attr)
            if layer in returns and value is not None:
                kwargs[attr] = value
        new_by_phase[phase] = ValidationResult(**kwargs)
    return ValidationResultAll(passed=result.passed, by_phase=new_by_phase, meta=result.meta)


def validate(
    spec: SpecInput, context: Mapping[str, Any] | None = None
) -> ValidationResult | ValidationResultAll:
    """Run validation on an OpenSpec v1.1 spec.

    Driven by ``context['phase']``. A concrete phase returns a
    :class:`ValidationResult`; ``'all'`` (or omitted) returns a
    :class:`ValidationResultAll` keyed under ``by_phase``.
    """
    ctx = _normalize_context(context)
    if not ctx.get("config"):
        ctx["config"] = load_defaults()

    validate_input(ctx)

    phase = ctx.get("phase") or "all"
    spec_dict = to_spec_dict(spec)

    if phase == "all":
        result = validate_all(spec_dict, ctx.get("activeEntityId"), ctx["config"])
        return _filter_all_returns(result, ctx.get("returns") or _DEFAULT_RETURNS_ALL)

    return validate_single(
        spec_dict, cast(SinglePhase, phase), ctx.get("activeEntityId"), ctx["config"]
    )
