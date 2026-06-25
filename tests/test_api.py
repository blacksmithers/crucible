"""C9 — public API smoke tests (model + dict input, all-mode, input errors)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from crucible import (
    Specification,
    ValidatorInputError,
    types,
    validate,
    validate_structural,
)

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "fixtures" / "test-surface" / "cases"


def _seed(name: str) -> dict[str, Any]:
    raw = json.loads((CASES / name).read_text(encoding="utf-8"))
    raw.pop("$testSurface", None)
    return raw


def test_validate_accepts_dict() -> None:
    result = validate(_seed("seed-planning-spec.json"), {"phase": "planning_spec"})
    assert isinstance(result, types.ValidationResult)
    assert result.phase == "planning_spec"
    assert result.scoring is not None and not result.scoring.skipped


def test_validate_accepts_model() -> None:
    spec = Specification.model_validate(_seed("seed-planning-spec.json"))
    result = validate(spec, {"phase": "planning_spec"})
    assert isinstance(result, types.ValidationResult)
    assert result.scoring is not None


def test_validate_all_mode() -> None:
    seed = _seed("seed-planning-spec.json")
    result = validate(seed, {"phase": "all", "returns": ["scoring", "structural"]})
    assert isinstance(result, types.ValidationResultAll)
    assert set(result.by_phase.keys()) == {
        "planning_spec",
        "epic_decomposition",
        "epic_expansion",
        "ticket_decomposition",
        "ticket_expansion",
        "cross_validation",
    }


def test_validate_default_config_loaded() -> None:
    # No config passed → defaults are loaded internally.
    result = validate(_seed("seed-planning-spec.json"), {"phase": "planning_spec"})
    assert result.passed in (True, False)


def test_invalid_phase_raises() -> None:
    with pytest.raises(ValidatorInputError):
        validate(_seed("seed-planning-spec.json"), {"phase": "bogus"})


def test_phase_requiring_entity_id_raises() -> None:
    with pytest.raises(ValidatorInputError):
        validate(_seed("seed-planning-spec.json"), {"phase": "epic_expansion"})


def test_validate_structural_standalone() -> None:
    result = validate_structural(_seed("seed-planning-spec.json"))
    assert isinstance(result, types.StructuralResult)
    assert result.missing_fields == []
