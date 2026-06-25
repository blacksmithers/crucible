"""Ratio engines (port of ``engines/{blueprint-epic-ratio,impl-verification-ratio}.ts``)."""

from __future__ import annotations

from typing import Any

from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding


def check_blueprint_epic_ratio(
    spec: dict[str, Any], config: ValidatorConfig
) -> list[CrossValidationFinding]:
    epics = spec.get("epics") or []
    epic_count = len(epics)
    if epic_count == 0:
        return []

    blueprint_count = sum(
        1 for b in (spec.get("blueprints") or []) if b.get("coverageType") == "ticket"
    )
    min_ratio = config["crossValidation"]["ratios"]["blueprintToEpic"]["min"]
    ratio = blueprint_count / epic_count

    if ratio < min_ratio:
        return [
            CrossValidationFinding(
                category="blueprint-epic-ratio",
                severity="error",
                field="specification.blueprints",
                message=(
                    f"{blueprint_count} ticket-scoped blueprints for {epic_count} epics "
                    f"(ratio {ratio:.2f}); min {min_ratio}"
                ),
                entity_ids=[spec["id"]],
                primary_entity_id=spec["id"],
                operations=["create_blueprint"],
            )
        ]
    return []


def check_impl_verification_ratio(
    spec: dict[str, Any], scoped_epics: list[dict[str, Any]], config: ValidatorConfig
) -> list[CrossValidationFinding]:
    all_tickets = [t for e in scoped_epics for t in (e.get("tickets") or [])]
    if not all_tickets:
        return []

    ratios = config["crossValidation"]["ratios"]["implementationToVerification"]
    minimum, maximum = ratios["min"], ratios["max"]
    imp_count = sum(1 for t in all_tickets if t.get("ticketType") == "implementation")
    ver_count = sum(1 for t in all_tickets if t.get("ticketType") == "verification")

    if ver_count == 0 and imp_count > 0:
        return [
            CrossValidationFinding(
                category="impl-verification-ratio",
                severity="error",
                field="specification.tickets",
                message=f"{imp_count} implementation tickets and 0 verification tickets",
                entity_ids=[spec["id"]],
                primary_entity_id=spec["id"],
                operations=["create_ticket"],
            )
        ]

    if ver_count > 0:
        ratio = imp_count / ver_count
        if ratio < minimum or ratio > maximum:
            return [
                CrossValidationFinding(
                    category="impl-verification-ratio",
                    severity="error",
                    field="specification.tickets",
                    message=(
                        f"Ratio implementation:verification is {ratio:.1f}:1; "
                        f"allowed range [{minimum}, {maximum}]"
                    ),
                    entity_ids=[spec["id"]],
                    primary_entity_id=spec["id"],
                    operations=["create_ticket"],
                )
            ]
    return []
