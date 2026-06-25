"""Structural-check evaluation for findings (port of ``engine/structural-checks.ts``).

Unlike the scoring layer's boolean ``run_structural_checks``, this returns a
*status* (fulfilled / missing / partial) plus per-item offenders and threshold
context, which the finding engine turns into ``Finding`` records.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ...scoring.quality_checks import QUALITY_CHECKS, check_range
from ...types.config import ValidatorConfig
from ...types.enums import FindingStatus
from ...types.finding import ThresholdContext
from ...types.rubric import StructuralCheck
from .resolver import resolve_threshold


@dataclass(frozen=True)
class PerItemFinding:
    item_index: int
    item_actual_length: int
    expected_min_length: int


@dataclass
class StructuralEvaluationResult:
    status: FindingStatus
    threshold_context: ThresholdContext | None = None
    per_item_findings: list[PerItemFinding] | None = field(default=None)


def run_structural_check(check: StructuralCheck, value: Any) -> bool:
    if check.type == "present":
        return value is not None and value != ""
    if check.type == "enumMember":
        return isinstance(check.param, list) and value in check.param
    if check.type == "pattern":
        return isinstance(value, str) and re.search(str(check.param), value) is not None
    if check.type == "range":
        return check_range(value, check.param)
    named = QUALITY_CHECKS.get(check.type)
    return named(value) if named else False


def evaluate_structural_checks(
    checks: list[StructuralCheck],
    value: Any,
    config: ValidatorConfig,
    entity: dict[str, Any] | None = None,
) -> StructuralEvaluationResult:
    count_check = next((c for c in checks if c.type == "minCount"), None)
    item_length_check = next(
        (c for c in checks if c.type == "minLength" and c.applies_to == "items"), None
    )
    field_length_check = next(
        (c for c in checks if c.type == "minLength" and c.applies_to in ("field", None)), None
    )
    other_checks = [
        c
        for c in checks
        if c.type not in ("minCount", "minLength", "array-item-field-min-length")
    ]

    # Step 1: minCount — cascade gatekeeper for arrays.
    if count_check is not None:
        minimum = resolve_threshold(count_check, config, entity)
        actual = len(value) if isinstance(value, list) else 0
        if actual < minimum:
            return StructuralEvaluationResult(
                status="missing",
                threshold_context=ThresholdContext(
                    check_type="minCount", expected=int(minimum), actual=actual
                ),
            )

    # Step 2: per-item minLength.
    if item_length_check is not None and isinstance(value, list):
        minimum = resolve_threshold(item_length_check, config, entity)
        offenders = [
            PerItemFinding(idx, len(item), int(minimum))
            for idx, item in enumerate(value)
            if isinstance(item, str) and len(item) < minimum
        ]
        if offenders:
            return StructuralEvaluationResult(status="partial", per_item_findings=offenders)

    # Step 2b: per-item object-field minLength.
    item_field_checks = [c for c in checks if c.type == "array-item-field-min-length"]
    if item_field_checks and isinstance(value, list):
        offenders = []
        for check in item_field_checks:
            sub_field = check.param
            minimum = resolve_threshold(check, config, entity)
            for idx, item in enumerate(value):
                field_val = item.get(sub_field) if isinstance(item, dict) else None
                actual = len(field_val) if isinstance(field_val, str) else 0
                if actual < minimum:
                    offenders.append(PerItemFinding(idx, actual, int(minimum)))
        if offenders:
            return StructuralEvaluationResult(status="partial", per_item_findings=offenders)

    # Step 3: whole-field minLength.
    if field_length_check is not None:
        minimum = resolve_threshold(field_length_check, config, entity)
        actual = len(value) if isinstance(value, str) else 0
        if actual < minimum:
            return StructuralEvaluationResult(
                status="missing",
                threshold_context=ThresholdContext(
                    check_type="minLength", expected=int(minimum), actual=actual
                ),
            )

    # Step 4: other checks.
    for check in other_checks:
        if not run_structural_check(check, value):
            return StructuralEvaluationResult(status="missing")

    return StructuralEvaluationResult(status="fulfilled")
