"""Wave-coordination cross-validation checks (emissions).

Port of ``cross-validation/{wave-size-exceed,wave-concurrent-modification,
wave-deletion-after-modification,wave-deletion-after-creation}.ts``.
"""

from __future__ import annotations

import math
from typing import Any

from ..engines.wave_calculator import compute_waves, tickets_by_wave
from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding
from .emission import CVEmission


def _ticket_by_id(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {t["id"]: t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])}


def propose_wave_split(wave_tickets: list[dict[str, Any]]) -> dict[str, Any]:
    sorted_tickets = sorted(wave_tickets, key=lambda t: t["id"])
    base_size = math.ceil(len(sorted_tickets) / 2)
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


def check_wave_size_exceed(spec: dict[str, Any], config: ValidatorConfig) -> list[CVEmission]:
    waves = compute_waves(spec)
    by_wave = tickets_by_wave(waves)
    maximum = config["crossValidation"]["waves"]["maxTicketsPerWave"]
    ticket_by_id = _ticket_by_id(spec)

    emissions: list[CVEmission] = []
    for wave_number, ticket_ids in sorted(by_wave.items()):
        if len(ticket_ids) <= maximum:
            continue
        proposal = propose_wave_split([ticket_by_id[i] for i in ticket_ids if i in ticket_by_id])
        sorted_ids = sorted(ticket_ids)
        base_join = ", ".join(proposal["baseWaveTicketIds"])
        inter_join = ", ".join(proposal["intermediateWaveTicketIds"])
        emissions.append(
            CVEmission(
                finding=CrossValidationFinding(
                    category="wave-size-exceed",
                    severity="error",
                    field="specification.tickets",
                    message=(
                        f"Wave {wave_number} has {len(ticket_ids)} tickets, max allowed {maximum}"
                    ),
                    entity_ids=sorted_ids,
                    primary_entity_id=proposal["baseWaveTicketIds"][0],
                    operations=["update_ticket"],
                    context={
                        "wave": wave_number,
                        "currentSize": len(ticket_ids),
                        "maxAllowed": maximum,
                        "splitProposal": proposal,
                    },
                ),
                guidance=(
                    f"Wave {wave_number} has {len(ticket_ids)} tickets — exceeds the configured "
                    f"maximum ({maximum} per wave). Too much parallelism in the same wave "
                    "indicates that dependencies between related tickets were not declared — some "
                    "of these tickets likely depend on each other but it was not made explicit. "
                    f"Simple split suggestion (arbitrary algorithm, humans should review): keep "
                    f'[{base_join}] in the current wave, and add "{proposal["suggestedAnchor"]}" '
                    f"to the dependencies of tickets [{inter_join}] to create an intermediate "
                    f"wave. Result: wave {wave_number} with {len(proposal['baseWaveTicketIds'])} "
                    f"tickets, intermediate wave with "
                    f"{len(proposal['intermediateWaveTicketIds'])} tickets. Algorithm splits by "
                    "alphabetic order with an arbitrary anchor — adjust to reflect real semantic "
                    f"relationships between tickets when known. Alternatively, if {maximum}+ "
                    "tickets really are independent (unlikely in practice), raise "
                    "maxTicketsPerWave in the config."
                ),
            )
        )
    return emissions


def check_wave_concurrent_modification(spec: dict[str, Any]) -> list[CVEmission]:
    waves = compute_waves(spec)
    ticket_by_id = _ticket_by_id(spec)

    wave_file_map: dict[str, list[str]] = {}
    for a in waves.assignments:
        ticket = ticket_by_id.get(a.ticket_id)
        if ticket is None:
            continue
        for path in ticket.get("filesToBeModified") or []:
            wave_file_map.setdefault(f"{a.wave}\0{path}", []).append(a.ticket_id)

    emissions: list[CVEmission] = []
    for key, ticket_ids in wave_file_map.items():
        if len(ticket_ids) < 2:
            continue
        sep = key.index("\0")
        wave = int(key[:sep])
        path = key[sep + 1 :]
        sorted_ids = sorted(ticket_ids)
        quoted = " and ".join(f'"{t}"' for t in sorted_ids)
        emissions.append(
            CVEmission(
                finding=CrossValidationFinding(
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
                ),
                guidance=(
                    f'Tickets {quoted} are in wave {wave} and all modify "{path}". When waves '
                    "execute in parallel, simultaneous modifications to the same file cause merge "
                    "conflicts and lost work. Resolve by adding dependencies between the tickets "
                    "to force sequential order (one ticket modifies first, another after) OR "
                    "consolidating into a single ticket if the split does not make sense OR "
                    "moving the modifications to separate files if they are independent. The "
                    "choice depends on whether the modifications are logically related "
                    "(consolidate) or independent (separate)."
                ),
            )
        )
    return emissions


def _deletion_after(
    spec: dict[str, Any], source_field: str, category: str, creator_key: str, scenario: str
) -> list[CVEmission]:
    waves = compute_waves(spec)
    ticket_by_id = _ticket_by_id(spec)

    sources: dict[str, list[dict[str, Any]]] = {}
    for a in waves.assignments:
        ticket = ticket_by_id.get(a.ticket_id)
        if ticket is None:
            continue
        for path in ticket.get(source_field) or []:
            sources.setdefault(path, []).append({"ticketId": a.ticket_id, "wave": a.wave})

    emissions: list[CVEmission] = []
    for a in waves.assignments:
        deleter = ticket_by_id.get(a.ticket_id)
        if deleter is None:
            continue
        for path in deleter.get("filesToBeDeleted") or []:
            for src in sources.get(path, []):
                if src["wave"] < a.wave:
                    msg_verb = "modified" if source_field == "filesToBeModified" else "created"
                    rel = "modified" if source_field == "filesToBeModified" else "creates"
                    emissions.append(
                        CVEmission(
                            finding=CrossValidationFinding(
                                category=category,
                                severity="error",
                                field=f"filesToBeDeleted:{path}",
                                message=(
                                    f'Ticket "{a.ticket_id}" (wave {a.wave}) deletes file '
                                    f'"{path}" {msg_verb} by ticket "{src["ticketId"]}" '
                                    f'(wave {src["wave"]})'
                                ),
                                entity_ids=[src["ticketId"], a.ticket_id],
                                primary_entity_id=a.ticket_id,
                                operations=["update_ticket", "delete_ticket"],
                                context={
                                    "path": path,
                                    creator_key: src["ticketId"],
                                    creator_key.replace("TicketId", "Wave"): src["wave"],
                                    "deleterTicketId": a.ticket_id,
                                    "deleterWave": a.wave,
                                },
                            ),
                            guidance=(
                                f'Ticket "{a.ticket_id}" (wave {a.wave}) deletes "{path}", but '
                                f'ticket "{src["ticketId"]}" (wave {src["wave"]}) {rel} that '
                                f"same file. {scenario}"
                            ),
                        )
                    )
    return emissions


_MOD_SCENARIO = (
    "Deleting a file after modifications from prior waves makes the previous work pointless — "
    "likely a planning smell. Three possible scenarios: (1) the modifying ticket should not "
    "exist (futile modification — remove the filesToBeModified entry), (2) the deletion is wrong "
    "(the file is needed — remove the filesToBeDeleted entry), or (3) the deletion should occur "
    "before the modification (reorganize: move the deletion to a wave before the modification, "
    "or move the modification to a different ticket that operates on another file). Review the "
    "intent of both tickets."
)

_CREATE_SCENARIO = (
    "Creating a file in one wave and deleting it in another is futile work at planning time — "
    "except in legitimate cases like intermediate build artifacts. Likely either: (1) the "
    "creating ticket should not exist (remove the filesToBeCreated entry), or (2) the deletion "
    "is wrong (the file is needed — remove the filesToBeDeleted entry), or (3) the two tickets "
    "represent incompatible phases and should be consolidated/rewritten. If this is a legitimate "
    "intermediate build-artifact flow (rare in planning specs), justify it in the description of "
    "both tickets."
)


def check_wave_deletion_after_modification(spec: dict[str, Any]) -> list[CVEmission]:
    return _deletion_after(
        spec,
        "filesToBeModified",
        "wave-deletion-after-modification",
        "modifierTicketId",
        _MOD_SCENARIO,
    )


def check_wave_deletion_after_creation(spec: dict[str, Any]) -> list[CVEmission]:
    return _deletion_after(
        spec,
        "filesToBeCreated",
        "wave-deletion-after-creation",
        "creatorTicketId",
        _CREATE_SCENARIO,
    )
