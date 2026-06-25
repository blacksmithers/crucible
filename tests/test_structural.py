"""C3 — structural layer, differential against the golden violation snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from crucible.config import load_from_file
from crucible.structural import validate_structural

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "test-surface"
CONFIGS = FIXTURES / "configs"
VIOLATION_SEEDS = FIXTURES / "cases" / "violations"
VIOLATION_SNAPSHOTS = FIXTURES / "snapshots" / "violations"

PHASE_DIR_TO_PHASE = {
    "planning-spec": "planning_spec",
    "epic-decomposition": "epic_decomposition",
    "epic-expansion": "epic_expansion",
    "ticket-decomposition": "ticket_decomposition",
    "ticket-expansion": "ticket_expansion",
    "cross-validation": "cross_validation",
}


def _case_name(phase_dir: str, seed_file: str) -> str:
    stem = seed_file[:-5] if seed_file.endswith(".json") else seed_file
    if stem.startswith("seed-violation-"):
        stem = stem[len("seed-violation-") :]
    return f"violation-{phase_dir}-{stem}"


def _load_seed(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("$testSurface", None)
    return raw


def _discover() -> list[tuple[str, Path, Path]]:
    cases: list[tuple[str, Path, Path]] = []
    for phase_dir in sorted(p.name for p in VIOLATION_SEEDS.iterdir() if p.is_dir()):
        if phase_dir not in PHASE_DIR_TO_PHASE:
            continue
        for seed in sorted((VIOLATION_SEEDS / phase_dir).glob("*.json")):
            name = _case_name(phase_dir, seed.name)
            snap = VIOLATION_SNAPSHOTS / phase_dir / f"{name}.snapshot.json"
            if snap.exists():
                cases.append((name, seed, snap))
    return cases


CASES = _discover()


def test_cases_discovered() -> None:
    assert len(CASES) >= 20  # the corpus has ~25 violation cases


@pytest.mark.parametrize("name,seed_path,snap_path", CASES, ids=[c[0] for c in CASES])
def test_structural_matches_snapshot(name: str, seed_path: Path, snap_path: Path) -> None:
    phase_dir = seed_path.parent.name
    phase = PHASE_DIR_TO_PHASE[phase_dir]
    config = load_from_file(str(CONFIGS / "default.yml"))
    seed = _load_seed(seed_path)

    snapshot = json.loads(snap_path.read_text(encoding="utf-8"))
    expected = snapshot["output"].get("structural")
    if expected is None:
        pytest.skip("snapshot has no structural layer for this phase")

    actual = validate_structural(seed, config, phase).to_json_dict()
    assert actual == expected
