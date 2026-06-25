"""Wave calculator (port of ``engines/wave-calculator.ts``).

Assigns each ticket to an execution wave (longest-prerequisite-chain layering)
over the dependency DAG. Used by the wave-coordination cross-validation checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WaveAssignment:
    ticket_id: str
    wave: int


@dataclass(frozen=True)
class WaveCalculationResult:
    assignments: list[WaveAssignment]
    unassigned: list[str]
    total_waves: int


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


def compute_waves(spec: dict[str, Any]) -> WaveCalculationResult:
    all_tickets = _all_tickets(spec)
    all_ids = {t["id"] for t in all_tickets}

    dependency_map: dict[str, set[str]] = {}
    for ticket in all_tickets:
        deps = {
            d["ticketId"]
            for d in (ticket.get("dependencies") or [])
            if d["ticketId"] in all_ids
        }
        dependency_map[ticket["id"]] = deps

    waves: dict[str, int] = {}
    remaining = {t["id"] for t in all_tickets}

    current_wave = 1
    while remaining:
        eligible: list[str] = []
        for ticket_id in remaining:
            deps = dependency_map[ticket_id]
            if not deps:
                eligible.append(ticket_id)
                continue
            if all(
                waves.get(dep_id) is not None and waves[dep_id] < current_wave
                for dep_id in deps
            ):
                eligible.append(ticket_id)

        if not eligible:
            break

        for ticket_id in eligible:
            waves[ticket_id] = current_wave
            remaining.discard(ticket_id)
        current_wave += 1

    assignments = [WaveAssignment(ticket_id=tid, wave=w) for tid, w in waves.items()]
    assignments.sort(key=lambda a: (a.wave, a.ticket_id))

    unassigned = sorted(remaining)
    total_waves = max(waves.values()) if waves else 0

    return WaveCalculationResult(
        assignments=assignments, unassigned=unassigned, total_waves=total_waves
    )


def tickets_by_wave(result: WaveCalculationResult) -> dict[int, list[str]]:
    by_wave: dict[int, list[str]] = {}
    for a in result.assignments:
        by_wave.setdefault(a.wave, []).append(a.ticket_id)
    for ids in by_wave.values():
        ids.sort()
    return by_wave
