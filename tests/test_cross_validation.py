"""C6 — cross-validation layer, differential against golden from the current TS.

The committed test-surface snapshots are stale AND inconsistent with the
committed seeds (seed-cross-validation has ``dependencies: null``, which the
current TS crashes on). So cross-validation is verified against
``fixtures/golden/cross_validation.json`` generated from the current TS source
(see ``tools/gen_cv_golden.mjs``), with ``dependencies`` null→[] normalized on
both sides — a fair engine-logic differential on identical input.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from crucible.config import load_defaults
from crucible.cross_validation import run_cross_validation

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "fixtures" / "test-surface" / "cases"
GOLDEN = json.loads(
    (ROOT / "fixtures" / "golden" / "cross_validation.json").read_text(encoding="utf-8")
)
_CONFIG = load_defaults()


def _seed_path(key: str) -> Path:
    if key.startswith("violations/"):
        return CASES / "violations" / "cross-validation" / key.split("/", 1)[1]
    return CASES / f"{key}.json"


def _load_normalized(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("$testSurface", None)
    for epic in raw.get("epics") or []:
        for ticket in epic.get("tickets") or []:
            if ticket.get("dependencies") is None:
                ticket["dependencies"] = []
    return raw


@pytest.mark.parametrize("key", list(GOLDEN.keys()))
def test_cross_validation_matches_golden(key: str) -> None:
    seed = _load_normalized(_seed_path(key))
    actual = run_cross_validation(seed, _CONFIG, "cross_validation").to_json_dict()
    assert actual == GOLDEN[key]
