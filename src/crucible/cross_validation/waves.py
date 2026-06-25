"""Wave-coordination cross-validation checks.

Port of ``cross-validation/{wave-size-exceed,wave-concurrent-modification,
wave-deletion-after-modification,wave-deletion-after-creation}.ts``.
"""

from __future__ import annotations

import math
from typing import Any

from ..engines.wave_calculator import compute_waves, tickets_by_wave
from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding


def _ticket_by_id(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        t["id"]: t
        for e in (spec.get("epics") or [])
        for t in (e.get("tickets") or [])
    }


def propose_wave_split(wave_tickets: list[dict[str, Any]]) -> dict[str, Any]:
    sorted_tickets = sorted(wave_tickets, key=lambda t: t["id"])
    n = len(sorted_tickets)
    base_size = math.ceil(n / 2)
    base = sorted_tickets[:base_size]
    intermediate = sorted_tickets[base_size:]
    anchor = base[0]["id"]
    return {
        "baseWaveTicketIds": [t["id"] for t in base],
        "intermediateWaveTicketIds": [t["id"] for t in intermediate],
        "suggestedAnchor": anchor,
        "instruction": (
            f'For each ticket in intermediateWaveTicketIds, add "{anchor}" to its dependencies'
        ),
    }


def check_wave_size_exceed(
    spec: dict[str, Any], config: ValidatorConfig
) -> list[CrossValidationFinding]:
    waves = compute_waves(spec)
    by_wave = tickets_by_wave(waves)
    maximum = config["crossValidation"]["waves"]["maxTicketsPerWave"]
    ticket_by_id = _ticket_by_id(spec)

    findings: list[CrossValidationFinding] = []
    for wave_number, ticket_ids in sorted(by_wave.items()):
        if len(ticket_ids) <= maximum:
            continue
        tickets_in_wave = [ticket_by_id[i] for i in ticket_ids if i in ticket_by_id]
        proposal = propose_wave_split(tickets_in_wave)
        sorted_ids = sorted(ticket_ids)
        findings.append(
            CrossValidationFinding(
                category="wave-size-exceed",
                severity="error",
                field="specification.tickets",
                message=f"Wave {wave_number} has {len(ticket_ids)} tickets, max allowed {maximum}",
                entity_ids=sorted_ids,
                primary_entity_id=proposal["baseWaveTicketIds"][0],
                operations=["update_ticket"],
                context={
                    "wave": wave_number,
                    "currentSize": len(ticket_ids),
                    "maxAllowed": maximum,
                    "splitProposal": proposal,
                },
            )
        )
    return findings


def check_wave_concurrent_modification(spec: dict[str, Any]) -> list[CrossValidationFinding]:
    waves = compute_waves(spec)
    ticket_by_id = _ticket_by_id(spec)

    wave_file_map: dict[str, list[str]] = {}
    for a in waves.assignments:
        ticket = ticket_by_id.get(a.ticket_id)
        if ticket is None:
            continue
        for path in ticket.get("filesToBeModified") or []:
            wave_file_map.setdefault(f"{a.wave}\0{path}", []).append(a.ticket_id)

    findings: list[CrossValidationFinding] = []
    for key, ticket_ids in wave_file_map.items():
        if len(ticket_ids) < 2:
            continue
        sep = key.index("\0")
        wave = int(key[:sep])
        path = key[sep + 1 :]
        sorted_ids = sorted(ticket_ids)
        findings.append(
            CrossValidationFinding(
                category="wave-concurrent-modification",
                severity="error",
                field=f"filesToBeModified:{path}",
                message=(
                    f"Tickets [{', '.join(sorted_ids)}] modify same file "
                    f'"{path}" in same wave ({wave})'
                ),
                entity_ids=sorted_ids,
                primary_entity_id=sorted_ids[0],
                operations=["update_ticket"],
                context={"wave": wave, "path": path, "ticketIds": sorted_ids},
            )
        )
    return findings


def _deletion_after(
    spec: dict[str, Any], source_field: str, category: str, creator_key: str
) -> list[CrossValidationFinding]:
    waves = compute_waves(spec)
    ticket_by_id = _ticket_by_id(spec)

    sources: dict[str, list[dict[str, Any]]] = {}
    for a in waves.assignments:
        ticket = ticket_by_id.get(a.ticket_id)
        if ticket is None:
            continue
        for path in ticket.get(source_field) or []:
            sources.setdefault(path, []).append({"ticketId": a.ticket_id, "wave": a.wave})

    findings: list[CrossValidationFinding] = []
    for a in waves.assignments:
        deleter = ticket_by_id.get(a.ticket_id)
        if deleter is None:
            continue
        for path in deleter.get("filesToBeDeleted") or []:
            for src in sources.get(path, []):
                if src["wave"] < a.wave:
                    findings.append(
                        CrossValidationFinding(
                            category=category,
                            severity="error",
                            field=f"filesToBeDeleted:{path}",
                            message=(
                                f'Ticket "{a.ticket_id}" (wave {a.wave}) deletes file '
                                f'"{path}" {"modified" if source_field == "filesToBeModified" else "created"} '
                                f'by ticket "{src["ticketId"]}" (wave {src["wave"]})'
                            ),
                            entity_ids=[src["ticketId"], a.ticket_id],
                            primary_entity_id=a.ticket_id,
                            operations=["update_ticket", "delete_ticket"],
                            context={
                                "path": path,
                                creator_key: src["ticketId"],
                                f"{creator_key.replace('TicketId', 'Wave')}": src["wave"],
                                "deleterTicketId": a.ticket_id,
                                "deleterWave": a.wave,
                            },
                        )
                    )
    return findings


def check_wave_deletion_after_modification(spec: dict[str, Any]) -> list[CrossValidationFinding]:
    return _deletion_after(
        spec, "filesToBeModified", "wave-deletion-after-modification", "modifierTicketId"
    )


def check_wave_deletion_after_creation(spec: dict[str, Any]) -> list[CrossValidationFinding]:
    return _deletion_after(
        spec, "filesToBeCreated", "wave-deletion-after-creation", "creatorTicketId"
    )
