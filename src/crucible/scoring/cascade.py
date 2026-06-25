"""Cascade floors + gate (port of ``scoring/cascade.ts``)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..types.cascade import CascadeFailure, CascadeFloors
from ..types.config import ValidatorConfig
from ..types.phase import ValidationPhase


def _js_round(x: float) -> float:
    # Mirror JS Math.round (round half toward +Infinity).
    return math.floor(x + 0.5)


def _round2(n: float) -> float:
    return _js_round(n * 100) / 100


def _num(n: float) -> str:
    # Mirror JS Number->string in template literals (no trailing ".0").
    if isinstance(n, int) or float(n).is_integer():
        return str(int(n))
    return repr(n)


def compute_cascade_floors(config: ValidatorConfig) -> CascadeFloors:
    global_threshold = config["thresholds"]["global"]
    weights = config["scoring"]["weights"]
    epics = weights["epics"]
    tickets = weights["tickets"]
    return CascadeFloors(
        spec_only=max(0, global_threshold - (epics + tickets) * 100),
        spec_plus_epics=max(0, global_threshold - tickets * 100),
        total=global_threshold,
    )


def phase_includes_epics(phase: ValidationPhase) -> bool:
    return phase in (
        "epic_expansion",
        "ticket_decomposition",
        "ticket_expansion",
        "cross_validation",
        "all",
    )


def phase_includes_tickets(phase: ValidationPhase) -> bool:
    return phase in ("ticket_expansion", "cross_validation", "all")


@dataclass(frozen=True)
class CascadeGateInput:
    global_score: float
    spec_block: float
    epic_block: float
    phase: ValidationPhase
    floors: CascadeFloors


@dataclass(frozen=True)
class CascadeGateResult:
    gate_result: str  # 'pass' | 'fail'
    cascade_failures: list[CascadeFailure]


def evaluate_cascade_gate(inp: CascadeGateInput) -> CascadeGateResult:
    floors = inp.floors
    spec_block = inp.spec_block
    epic_block = inp.epic_block
    failures: list[CascadeFailure] = []

    if spec_block < floors.spec_only:
        failures.append(
            CascadeFailure(
                level="specOnly",
                expected=floors.spec_only,
                actual=_round2(spec_block),
                message=(
                    f"Spec contribution {_num(_round2(spec_block))} below minimum "
                    f"{_num(floors.spec_only)}. Improve spec score before advancing."
                ),
            )
        )

    if phase_includes_epics(inp.phase) and spec_block + epic_block < floors.spec_plus_epics:
        failures.append(
            CascadeFailure(
                level="specPlusEpics",
                expected=floors.spec_plus_epics,
                actual=_round2(spec_block + epic_block),
                message=(
                    f"Spec + epics contribution {_num(_round2(spec_block + epic_block))} "
                    f"below minimum {_num(floors.spec_plus_epics)}. Improve spec or epic scores."
                ),
            )
        )

    if phase_includes_tickets(inp.phase) and inp.global_score < floors.total:
        failures.append(
            CascadeFailure(
                level="total",
                expected=floors.total,
                actual=_round2(inp.global_score),
                message=(
                    f"Global score {_num(_round2(inp.global_score))} below threshold "
                    f"{_num(floors.total)}."
                ),
            )
        )

    return CascadeGateResult(
        gate_result="pass" if not failures else "fail",
        cascade_failures=failures,
    )
