"""Blueprint-coverage cross-validation check (emissions; port of ``blueprint-ticket-coverage.ts``)."""

from __future__ import annotations

from typing import Any

from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding
from .emission import CVEmission


def check_blueprint_ticket_coverage(
    spec: dict[str, Any], config: ValidatorConfig
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
                        operations=["update_ticket", "update_blueprint", "delete_blueprint"],
                    ),
                    guidance=(
                        f'Blueprint "{title}" is linked to {len(linked)} ticket{plural}; '
                        f"configured minimum: {min_tickets}. Underused blueprints indicate that "
                        "the architectural pattern was not propagated to implementation — either "
                        "the blueprint is unnecessary, or tickets that should consume it are "
                        "missing. Review the tickets and link the blueprint to more tickets that "
                        "should follow it, consolidate tickets that should use the blueprint but "
                        "do not declare it, or remove the blueprint if it has no practical use in "
                        "the current spec. Blueprints exist to propagate architectural "
                        "decisions — without propagation they are dead weight."
                    ),
                )
            )
    return emissions
