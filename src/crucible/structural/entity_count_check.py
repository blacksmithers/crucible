"""Entity-count checks (port of ``structural/entity-count-check.ts``).

Phase-scoped min/max count gates for ``specification.epics`` and
``epic.tickets``. Guidance strings are copied verbatim from the TS source
(Portuguese), as they appear in the golden snapshots.
"""

from __future__ import annotations

from typing import Any

from ..types.config import ValidatorConfig
from ..types.phase import ValidationPhase
from ..types.result import StructuralFinding


def _context(**kwargs: Any) -> dict[str, Any]:
    # Mirror JSON.stringify: drop keys whose value is None (TS undefined).
    return {k: v for k, v in kwargs.items() if v is not None}


def check_entity_counts(
    spec: dict[str, Any],
    config: ValidatorConfig,
    phase: ValidationPhase,
) -> list[StructuralFinding]:
    findings: list[StructuralFinding] = []
    sr = config["structuralRequirements"]
    min_counts = sr["arrayMinCounts"]
    max_counts = sr["arrayMaxCounts"]
    phase_scoping = sr["arrayCountPhases"]

    def should_check(entity: str, field: str) -> bool:
        allowed = phase_scoping.get(entity, {}).get(field)
        if not allowed:
            return False
        return phase in allowed

    def bound(counts: dict[str, Any], entity: str, field: str) -> Any:
        return counts.get(entity, {}).get(field, {}).get("default")

    if should_check("specification", "epics"):
        epics_count = len(spec.get("epics") or [])
        epics_min = bound(min_counts, "specification", "epics")
        epics_max = bound(max_counts, "specification", "epics")
        title = spec.get("title")

        if epics_min is not None and epics_count < epics_min:
            findings.append(
                StructuralFinding(
                    category="entity-count-below-min",
                    severity="error",
                    field="specification.epics",
                    message=f"Specification has {epics_count} epic(s); minimum is {epics_min}",
                    guidance=(
                        f'Specification "{title}" tem {epics_count} épico(s). '
                        f"Mínimo configurado: {epics_min}. Decomponha o trabalho em mais épicos "
                        "pra habilitar paralelização e fronteiras claras de responsabilidade. "
                        "Cada épico deve representar um conjunto coeso de funcionalidades que pode "
                        "ser implementado e validado independentemente."
                    ),
                    operations=["create_epic"],
                    context=_context(
                        currentCount=epics_count,
                        configuredMin=epics_min,
                        configuredMax=epics_max,
                    ),
                )
            )

        if epics_max is not None and epics_count > epics_max:
            findings.append(
                StructuralFinding(
                    category="entity-count-above-max",
                    severity="error",
                    field="specification.epics",
                    message=f"Specification has {epics_count} epic(s); maximum is {epics_max}",
                    guidance=(
                        f'Specification "{title}" tem {epics_count} épicos — excede o máximo '
                        f"configurado de {epics_max}. Excesso de épicos indica scope muito amplo "
                        "ou granularidade errada. Considere consolidar épicos relacionados ou "
                        "splittar a spec em múltiplas specs com escopos coesos. Se o trabalho é "
                        "genuinamente massivo, ajuste arrayMaxCounts no config."
                    ),
                    operations=["update_epic", "delete_epic"],
                    context=_context(
                        currentCount=epics_count,
                        configuredMin=epics_min,
                        configuredMax=epics_max,
                    ),
                )
            )

    if should_check("epic", "tickets"):
        tickets_min = bound(min_counts, "epic", "tickets")
        tickets_max = bound(max_counts, "epic", "tickets")

        for epic in spec.get("epics") or []:
            tickets_count = len(epic.get("tickets") or [])
            epic_id = epic.get("id")
            epic_title = epic.get("title")

            if tickets_min is not None and tickets_count < tickets_min:
                findings.append(
                    StructuralFinding(
                        category="entity-count-below-min",
                        severity="error",
                        field=f"epics[id={epic_id}].tickets",
                        message=(
                            f'Epic "{epic_title}" has {tickets_count} ticket(s); '
                            f"minimum is {tickets_min}"
                        ),
                        guidance=(
                            f'Épico "{epic_title}" tem {tickets_count} ticket(s). '
                            f"Mínimo configurado: {tickets_min}. Quebre a implementação em unidades "
                            "menores e executáveis. Cada ticket deve representar trabalho focado que "
                            "pode ser implementado e revisado independentemente. Se o épico é "
                            "genuinamente atômico, considere se ele deveria ser uma seção de outro épico."
                        ),
                        operations=["create_ticket"],
                        context=_context(
                            epicId=epic_id,
                            currentCount=tickets_count,
                            configuredMin=tickets_min,
                            configuredMax=tickets_max,
                        ),
                    )
                )

            if tickets_max is not None and tickets_count > tickets_max:
                findings.append(
                    StructuralFinding(
                        category="entity-count-above-max",
                        severity="error",
                        field=f"epics[id={epic_id}].tickets",
                        message=(
                            f'Epic "{epic_title}" has {tickets_count} ticket(s); '
                            f"maximum is {tickets_max}"
                        ),
                        guidance=(
                            f'Épico "{epic_title}" tem {tickets_count} tickets — excede o máximo '
                            f"configurado de {tickets_max}. Excesso de tickets indica que o épico "
                            "cobre trabalho amplo demais. Considere splittar o épico em múltiplos "
                            "épicos com responsabilidades coesas. Alternativamente, consolide tickets "
                            "relacionados se a granularidade está fina demais."
                        ),
                        operations=["update_ticket", "delete_ticket", "create_epic"],
                        context=_context(
                            epicId=epic_id,
                            currentCount=tickets_count,
                            configuredMin=tickets_min,
                            configuredMax=tickets_max,
                        ),
                    )
                )

    return findings
