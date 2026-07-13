"""ME.15.3 — expansion-phase local gate is ALL-PASS, not the average.

The single-entity differential goldens can't exercise this: with one scoped
entity the mean equals that entity's score, so ``avg >= threshold`` and
``all(s >= threshold)`` are identical. These tests build a *multi-entity
straddle* (one entity above the threshold, one below, with the **mean still
above** it) and assert the gate now **fails** — the exact case the old
average-based gate let through (a strong entity masking a weak one).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from crucible import validate
from crucible.config import load_defaults

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "fixtures" / "test-surface" / "cases"

_RICH_EPIC_FIELDS = [
    "architecture",
    "scope",
    "goals",
    "acceptanceCriteria",
    "apiContracts",
    "sharedPatterns",
    "nonFunctionalRequirements",
    "dataModel",
    "folderStructures",
]
_RICH_TICKET_FIELDS = [
    "description",
    "implementationSteps",
    "acceptanceCriteria",
    "testSpecifications",
    "codeSnippets",
    "fileStructures",
    "technicalNotes",
]


def _seed(name: str) -> dict[str, Any]:
    raw = json.loads((CASES / name).read_text(encoding="utf-8"))
    raw.pop("$testSurface", None)
    raw["epics"] = raw.get("epics") or []
    raw["blueprints"] = raw.get("blueprints") or []
    for epic in raw["epics"]:
        epic["tickets"] = epic.get("tickets") or []
        for ticket in epic["tickets"]:
            ticket["dependencies"] = ticket.get("dependencies") or []
    return raw


def test_epic_expansion_gate_is_all_pass_not_average() -> None:
    config = load_defaults()
    threshold = config["thresholds"]["epic"]

    seed = _seed("seed-epic-expansion.json")
    rich = seed["epics"][0]
    thin = copy.deepcopy(rich)
    thin["id"] = "ep-2"
    thin["title"] = "Thin Epic"
    for field in _RICH_EPIC_FIELDS:
        thin.pop(field, None)
    seed["epics"] = [rich, thin]

    result = validate(
        seed,
        {"phase": "epic_expansion", "activeEntityId": ["ep-1", "ep-2"], "config": config},
    )
    scoring = result.scoring
    assert scoring is not None and not scoring.skipped
    scores = scoring.per_entity_score
    mean = sum(scores.values()) / len(scores)

    # Precondition: a genuine straddle whose MEAN clears the threshold.
    assert any(s >= threshold for s in scores.values())
    assert any(s < threshold for s in scores.values())
    assert mean >= threshold  # the old average gate would have PASSED here

    # ME.15.3: one weak epic can no longer be masked by the mean.
    assert scoring.gate_result == "fail"
    assert result.passed is False
    # The mean is still reported as the phase local score (only the gate changed).
    assert scoring.local_score == mean


def test_ticket_expansion_gate_is_all_pass_not_average() -> None:
    config = load_defaults()
    threshold = config["thresholds"]["ticket"]

    seed = _seed("seed-ticket-expansion.json")
    epic = seed["epics"][0]
    rich = epic["tickets"][0]
    thin = copy.deepcopy(rich)
    thin["id"] = "tkt-1-2"
    thin["title"] = "Thin Ticket"
    for field in _RICH_TICKET_FIELDS:
        thin.pop(field, None)
    epic["tickets"] = [rich, thin]

    result = validate(
        seed,
        {"phase": "ticket_expansion", "activeEntityId": ["tkt-1-1", "tkt-1-2"], "config": config},
    )
    scoring = result.scoring
    assert scoring is not None and not scoring.skipped
    scores = scoring.per_entity_score
    mean = sum(scores.values()) / len(scores)

    assert any(s >= threshold for s in scores.values())
    assert any(s < threshold for s in scores.values())
    assert mean >= threshold  # old average gate would have PASSED

    assert scoring.gate_result == "fail"
    assert result.passed is False
    assert scoring.local_score == mean
