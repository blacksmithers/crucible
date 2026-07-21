"""``check_format`` parity with the reference Zod schema on malformed input.

The strict schema (``_strict_schema``) mirrors ``@specforge/spec-types``. Zod does
not coerce, ``.optional()`` rejects an explicit ``null`` (``.nullish()`` accepts
it), numeric bounds are enforced, and strings are measured in UTF-16 units. The
Python port previously diverged on all of these — a coerced value, an explicit
null, a negative "nonnegative", or an emoji length flipped ``passed``.

Each expected list below is the exact ``[(fieldPath, reason)]`` the reference
``checkFormat`` produced for the same input. The base spec is schema-valid, so a
mutation's expected output is precisely the invalid field(s) it introduces.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from crucible.structural.format import check_format

_EMOJI = "\U0001f600"


def _base() -> dict[str, Any]:
    def crit(i: int) -> dict[str, Any]:
        return {"id": f"ac{i}", "given": "g", "when": "w", "then": "t", "order": 1}

    def goal(i: int) -> dict[str, Any]:
        return {
            "id": f"g{i}",
            "title": "T",
            "description": "D",
            "type": "business",
            "successCriteria": ["s"],
        }

    def req(i: int) -> dict[str, Any]:
        return {
            "id": f"r{i}",
            "title": "T",
            "description": "D",
            "type": "functional",
            "acceptanceCriteria": [crit(i)],
        }

    return {
        "schemaVersion": "1.1",
        "id": "s1",
        "projectId": "p1",
        "title": "T",
        "status": "draft",
        "goals": [goal(1), goal(2), goal(3)],
        "requirements": [req(1), req(2), req(3)],
        "architecture": "arch",
        "scope": {"inScope": ["a", "b", "c"], "outOfScope": ["x"]},
        "techStack": [],
        "folderStructures": [{"id": "f1", "scope": "root", "content": "c"}],
        "acceptanceCriteria": [],
        "nonFunctionalRequirements": [],
        "guardrails": [],
        "epics": [],
        "blueprints": [],
    }


def _set(**kw: Any) -> Callable[[dict[str, Any]], None]:
    def apply(s: dict[str, Any]) -> None:
        s.update(kw)

    return apply


# label -> (mutation, expected [(fieldPath, reason)] captured from the reference)
_CASES: dict[str, tuple[Callable[[dict[str, Any]], None], list[tuple[str, str]]]] = {
    "valid_base": (lambda s: None, []),
    # defect 1 — no coercion
    "coerce_str_for_number": (
        _set(estimatedMinutes="10"),
        [("estimatedMinutes", "Expected number, received string")],
    ),
    "coerce_bool_for_number": (
        _set(estimatedMinutes=True),
        [("estimatedMinutes", "Expected number, received boolean")],
    ),
    "coerce_number_for_string": (
        _set(title=5),
        [("title", "Expected string, received number")],
    ),
    "array_item_coerce": (
        lambda s: s["scope"]["inScope"].__setitem__(0, 5),
        [("scope.inScope[0]", "Expected string, received number")],
    ),
    "nested_string_for_number": (
        lambda s: s["requirements"][0]["acceptanceCriteria"][0].update(order="1"),
        [("requirements[0].acceptanceCriteria[0].order", "Expected number, received string")],
    ),
    # defect 2 — .optional() rejects explicit null
    "null_optional_string": (
        _set(description=None),
        [("description", "Expected string, received null")],
    ),
    "null_optional_number": (
        _set(estimatedMinutes=None),
        [("estimatedMinutes", "Expected number, received null")],
    ),
    "null_optional_array": (
        _set(sharedPatterns=None),
        [("sharedPatterns", "Expected array, received null")],
    ),
    "null_optional_object": (
        _set(epicTargets=None),
        [("epicTargets", "Expected object, received null")],
    ),
    # defect 5 — restored numeric bound
    "negative_nonnegative": (
        _set(estimatedMinutes=-1),
        [("estimatedMinutes", "Number must be greater than or equal to 0")],
    ),
    # enum message parity
    "invalid_enum": (
        lambda s: s["goals"][0].update(type="nope"),
        [
            (
                "goals[0].type",
                "Invalid enum value. Expected 'business' | 'technical' | 'user' | "
                "'operational', received 'nope'",
            )
        ],
    ),
    # defect 3 — UTF-16 length: 10 emoji is 20 UTF-16 units, clears min(20)
    "nullish_reason_emoji_passes": (
        _set(fieldDeclarations={"background": {"value": "N/A", "reason": _EMOJI * 10}}),
        [],
    ),
    "reason_ascii_short_fails": (
        _set(fieldDeclarations={"background": {"value": "N/A", "reason": "x" * 19}}),
        [("fieldDeclarations.background.reason", "String must contain at least 20 character(s)")],
    ),
}


def test_base_is_schema_valid() -> None:
    assert check_format(_base()) == []


@pytest.mark.parametrize("label", list(_CASES))
def test_check_format_matches_reference(label: str) -> None:
    mutate, expected = _CASES[label]
    spec = _base()
    mutate(spec)
    actual = sorted((f.field_path, f.reason) for f in check_format(spec))
    assert actual == sorted(expected)
