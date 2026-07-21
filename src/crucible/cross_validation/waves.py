"""Wave-coordination cross-validation checks (emissions).

The wave-concurrent-modification and wave-deletion-after-{creation,
modification} checks were replaced by the static file-graph model: see
``concurrent_modification.py`` (dependency-reachability, not same-wave) and
``file_provenance.py`` invariant #5 (no-delete-of-spec-touched). ``wave-size-
exceed`` is the last check with a wave timeline, so it is now the only consumer
of ``engines/wave_calculator``.
"""

from __future__ import annotations

import math
from typing import Any

from .. import i18n
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


def check_wave_size_exceed(
    spec: dict[str, Any], config: ValidatorConfig, language: str = "en"
) -> list[CVEmission]:
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
                guidance=i18n.render(
                    i18n.text(language, "cv.waveSizeExceed"),
                    {
                        "waveNumber": wave_number,
                        "ticketCount": len(ticket_ids),
                        "maximum": maximum,
                        "baseJoin": base_join,
                        "suggestedAnchor": proposal["suggestedAnchor"],
                        "interJoin": inter_join,
                        "baseCount": len(proposal["baseWaveTicketIds"]),
                        "intermediateCount": len(proposal["intermediateWaveTicketIds"]),
                    },
                ),
            )
        )
    return emissions
