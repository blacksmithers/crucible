"""Blueprint-coverage cross-validation check (port of ``blueprint-ticket-coverage.ts``)."""

from __future__ import annotations

from typing import Any

from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding


def check_blueprint_ticket_coverage(
    spec: dict[str, Any], config: ValidatorConfig
) -> list[CrossValidationFinding]:
    all_tickets = [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]
    min_tickets = config["crossValidation"]["checks"]["blueprint-coverage"][
        "minTicketsPerBlueprint"
    ]

    blueprint_links: dict[str, list[str]] = {}
    for ticket in all_tickets:
        for ref in ticket.get("blueprintReferences") or []:
            blueprint_links.setdefault(ref["blueprintId"], []).append(ticket["id"])

    findings: list[CrossValidationFinding] = []
    for blueprint in spec.get("blueprints") or []:
        if blueprint.get("coverageType") != "ticket":
            continue
        linked = blueprint_links.get(blueprint["id"], [])
        if len(linked) < min_tickets:
            entity_ids = [blueprint["id"], *sorted(linked)]
            findings.append(
                CrossValidationFinding(
                    category="blueprint-coverage",
                    severity="error",
                    field=f"blueprints[id={blueprint.get('id')}]",
                    message=(
                        f'Blueprint "{blueprint.get("title")}" has {len(linked)} linked '
                        f"tickets; minimum {min_tickets}"
                    ),
                    entity_ids=entity_ids,
                    primary_entity_id=blueprint["id"],
                    operations=["update_ticket", "update_blueprint", "delete_blueprint"],
                )
            )
    return findings
