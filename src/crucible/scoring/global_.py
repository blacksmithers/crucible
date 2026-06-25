"""Global (cross-layer) scoring (port of ``scoring/global.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..guidance.rubric import epic_entries, specification_entries, ticket_entries
from ..types.config import ScoringWeights, ValidatorConfig
from .per_entity import compute_entity_score
from .topology import compute_topology_penalties


@dataclass(frozen=True)
class GlobalScoreBreakdown:
    global_score: float
    spec_block: float
    epic_block: float
    ticket_block: float
    spec_score: float
    epic_avg: float | None
    ticket_avg: float | None
    topology_penalty: float
    weights: ScoringWeights


def _avg(xs: list[float]) -> float:
    if not xs:
        raise ValueError("avg([]) is undefined; caller must guard")
    return sum(xs) / len(xs)


def compute_global_score(
    spec: dict[str, Any],
    weights: ScoringWeights,
    config: ValidatorConfig,
) -> GlobalScoreBreakdown:
    epics = spec.get("epics") or []

    spec_score = compute_entity_score(spec, specification_entries, config).local_score
    epic_scores = [compute_entity_score(e, epic_entries, config).local_score for e in epics]
    ticket_scores = [
        compute_entity_score(t, ticket_entries, config).local_score
        for e in epics
        for t in (e.get("tickets") or [])
    ]

    epic_avg = _avg(epic_scores) if epic_scores else None
    ticket_avg = _avg(ticket_scores) if ticket_scores else None

    # Empty layer -> 0 contribution, never inflates the score.
    spec_block = weights["spec"] * spec_score
    epic_block = weights["epics"] * epic_avg if epic_avg is not None else 0.0
    ticket_block = weights["tickets"] * ticket_avg if ticket_avg is not None else 0.0

    topology = compute_topology_penalties(spec, config)
    global_score = max(0.0, spec_block + epic_block + ticket_block + topology.total_penalty)

    return GlobalScoreBreakdown(
        global_score=global_score,
        spec_block=spec_block,
        epic_block=epic_block,
        ticket_block=ticket_block,
        spec_score=spec_score,
        epic_avg=epic_avg,
        ticket_avg=ticket_avg,
        topology_penalty=topology.total_penalty,
        weights=weights,
    )
