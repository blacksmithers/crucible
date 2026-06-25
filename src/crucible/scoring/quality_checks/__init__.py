"""Named quality checks (port of ``scoring/quality-checks/*``).

Each check takes the resolved field value and returns whether it passes. The
"has list of objects with non-empty fields" checks are vacuously true on an
empty array (the minCount check guards emptiness separately).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

QualityCheck = Callable[[Any], bool]

_VALID_LAYERS = frozenset(
    {
        "database",
        "backend",
        "frontend",
        "infrastructure",
        "devops",
        "observability",
        "auth",
        "integration",
        "testing",
    }
)


def _is_nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and v != ""


def check_given_when_then(value: Any) -> bool:
    if not isinstance(value, list) or len(value) == 0:
        return False
    return all(
        isinstance(ac, dict)
        and _is_nonempty_str(ac.get("given"))
        and _is_nonempty_str(ac.get("when"))
        and _is_nonempty_str(ac.get("then"))
        for ac in value
    )


def check_has_file_paths(value: Any) -> bool:
    if not isinstance(value, list) or len(value) == 0:
        return False
    return all(isinstance(e, str) and ("/" in e or "." in e) for e in value)


def check_has_code(value: Any) -> bool:
    if not isinstance(value, list) or len(value) == 0:
        return False
    return all(isinstance(e, dict) and _is_nonempty_str(e.get("filePath")) for e in value)


def check_has_type_definitions(value: Any) -> bool:
    if not isinstance(value, list) or len(value) == 0:
        return False
    return all(
        isinstance(e, dict)
        and _is_nonempty_str(e.get("filePath"))
        and _is_nonempty_str(e.get("typeName"))
        for e in value
    )


def check_requirement_has_ac(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    if len(value) == 0:
        return True
    return all(
        isinstance(req, dict)
        and isinstance(req.get("acceptanceCriteria"), list)
        and len(req["acceptanceCriteria"]) >= 1
        for req in value
    )


def check_nfr_has_metric_and_target(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    if len(value) == 0:
        return True
    return all(
        isinstance(nfr, dict)
        and _is_nonempty_str(nfr.get("metric"))
        and _is_nonempty_str(nfr.get("target"))
        for nfr in value
    )


def check_goal_has_success_criteria(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    if len(value) == 0:
        return True
    return all(
        isinstance(goal, dict)
        and isinstance(goal.get("successCriteria"), list)
        and len(goal["successCriteria"]) >= 1
        for goal in value
    )


def check_guardrail_has_rationale_and_consequence(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    if len(value) == 0:
        return True
    return all(
        isinstance(g, dict)
        and _is_nonempty_str(g.get("rationale"))
        and _is_nonempty_str(g.get("consequence"))
        for g in value
    )


def check_tech_has_layer(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    if len(value) == 0:
        return True
    return all(isinstance(item, dict) and item.get("layer") in _VALID_LAYERS for item in value)


def check_range(value: Any, bounds: dict[str, float]) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    return bounds["min"] <= value <= bounds["max"]


QUALITY_CHECKS: dict[str, QualityCheck] = {
    "given-when-then": check_given_when_then,
    "has-file-paths": check_has_file_paths,
    "has-code": check_has_code,
    "has-type-definitions": check_has_type_definitions,
    "requirement-has-acceptance-criteria": check_requirement_has_ac,
    "nfr-has-metric-and-target": check_nfr_has_metric_and_target,
    "goal-has-success-criteria": check_goal_has_success_criteria,
    "guardrail-has-rationale-and-consequence": check_guardrail_has_rationale_and_consequence,
    "tech-has-layer": check_tech_has_layer,
}

__all__ = ["QUALITY_CHECKS", "QualityCheck", "check_range"]
