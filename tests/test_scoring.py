"""C4 — scoring layer, differential against golden values from the current TS.

The committed test-surface snapshots are stale relative to the current rubric
(scope decomposition), so scoring is verified against ``fixtures/golden/scoring.json``
generated from the current TS source (see ``tools/gen_scoring_golden.mjs``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from crucible.config import load_defaults, merge_config
from crucible.guidance.rubric import epic_entries, specification_entries, ticket_entries
from crucible.scoring import (
    compute_cascade_floors,
    compute_entity_score,
    compute_global_score,
    compute_topology_penalties,
)

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "fixtures" / "test-surface" / "cases"
GOLDEN = json.loads((ROOT / "fixtures" / "golden" / "scoring.json").read_text(encoding="utf-8"))

_DEFAULTS = load_defaults()
_NO_TYPES = merge_config(_DEFAULTS, {"structuralRequirements": {"enforceTypes": False}})


def _config_for(case: str) -> Any:
    return _NO_TYPES if case.endswith("__no-types") else _DEFAULTS


def _seed_for(case: str) -> dict[str, Any]:
    name = case.split("__", 1)[0]
    raw = json.loads((CASES / f"{name}.json").read_text(encoding="utf-8"))
    raw.pop("$testSurface", None)
    return raw


def _pf_json(per_field: Any) -> dict[str, Any]:
    return {
        k: {"earned": v.earned, "possible": v.possible, "tier": v.tier}
        for k, v in per_field.items()
    }


SEED_CASES = list(GOLDEN["seeds"].keys())


def test_cascade_floors() -> None:
    floors = compute_cascade_floors(_DEFAULTS)
    assert [floors.spec_only, floors.spec_plus_epics, floors.total] == [
        GOLDEN["cascadeFloors"]["specOnly"],
        GOLDEN["cascadeFloors"]["specPlusEpics"],
        GOLDEN["cascadeFloors"]["total"],
    ]


@pytest.mark.parametrize("case", SEED_CASES)
def test_spec_entity_score(case: str) -> None:
    cfg = _config_for(case)
    spec = _seed_for(case)
    g = GOLDEN["seeds"][case]
    score = compute_entity_score(spec, specification_entries, cfg)
    assert score.local_score == g["specLocalScore"]
    assert _pf_json(score.per_field) == g["specPerField"]


@pytest.mark.parametrize("case", SEED_CASES)
def test_epic_and_ticket_scores(case: str) -> None:
    cfg = _config_for(case)
    spec = _seed_for(case)
    g = GOLDEN["seeds"][case]

    epics = spec.get("epics") or []
    epic_scores = [
        {"id": e.get("id"), "score": compute_entity_score(e, epic_entries, cfg).local_score}
        for e in epics
    ]
    ticket_scores = [
        {"id": t.get("id"), "score": compute_entity_score(t, ticket_entries, cfg).local_score}
        for e in epics
        for t in (e.get("tickets") or [])
    ]
    assert epic_scores == g["epicScores"]
    assert ticket_scores == g["ticketScores"]


@pytest.mark.parametrize("case", [c for c in SEED_CASES if GOLDEN["seeds"][c]["global"]])
def test_global_score(case: str) -> None:
    cfg = _config_for(case)
    spec = _seed_for(case)
    g = GOLDEN["seeds"][case]["global"]
    gb = compute_global_score(spec, cfg["scoring"]["weights"], cfg)
    assert gb.global_score == g["globalScore"]
    assert gb.spec_block == g["specBlock"]
    assert gb.epic_block == g["epicBlock"]
    assert gb.ticket_block == g["ticketBlock"]
    assert gb.spec_score == g["specScore"]
    assert gb.epic_avg == g["epicAvg"]
    assert gb.ticket_avg == g["ticketAvg"]
    assert gb.topology_penalty == g["topologyPenalty"]


@pytest.mark.parametrize("case", [c for c in SEED_CASES if GOLDEN["seeds"][c]["topology"]])
def test_topology(case: str) -> None:
    cfg = _config_for(case)
    spec = _seed_for(case)
    t = GOLDEN["seeds"][case]["topology"]
    topo = compute_topology_penalties(spec, cfg)
    assert topo.total_penalty == t["totalPenalty"]
    assert topo.root_count == t["rootCount"]
    assert topo.leaf_count == t["leafCount"]
    assert topo.island_count == t["islandCount"]
