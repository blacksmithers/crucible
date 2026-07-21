"""Blueprint-coverage cross-validation check (emissions)."""

from __future__ import annotations

from typing import Any

from .. import i18n
from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding
from .emission import CVEmission


def check_blueprint_ticket_coverage(
    spec: dict[str, Any], config: ValidatorConfig, language: str = "en"
) -> list[CVEmission]:
    all_tickets = [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]
    min_tickets = config["crossValidation"]["checks"]["blueprint-coverage"][
        "minTicketsPerBlueprint"
    ]

    blueprint_links: dict[str, list[str]] = {}
    for ticket in all_tickets:
        for ref in ticket.get("blueprintReferences") or []:
            blueprint_links.setdefault(ref["blueprintId"], []).append(ticket["id"])

    emissions: list[CVEmission] = []
    for blueprint in spec.get("blueprints") or []:
        if blueprint.get("coverageType") != "ticket":
            continue
        linked = blueprint_links.get(blueprint["id"], [])
        if len(linked) < min_tickets:
            title = blueprint.get("title")
            entity_ids = [blueprint["id"], *sorted(linked)]
            plural = "" if len(linked) == 1 else "s"
            emissions.append(
                CVEmission(
                    finding=CrossValidationFinding(
                        category="blueprint-coverage",
                        severity="error",
                        field=f"blueprints[id={blueprint['id']}]",
                        message=(
                            f'Blueprint "{title}" has {len(linked)} linked tickets; '
                            f"minimum {min_tickets}"
                        ),
                        entity_ids=entity_ids,
                        primary_entity_id=blueprint["id"],
                        # link_blueprint_to_tickets is the sole writer of
                        # ticket.blueprintReferences; update_ticket no longer writes it.
                        operations=[
                            "link_blueprint_to_tickets",
                            "update_blueprint",
                            "delete_blueprint",
                        ],
                    ),
                    guidance=i18n.render(
                        i18n.text(language, "cv.blueprintCoverage"),
                        {
                            "title": title,
                            "linkedCount": len(linked),
                            "plural": plural,
                            "minTickets": min_tickets,
                        },
                    ),
                )
            )
    return emissions
