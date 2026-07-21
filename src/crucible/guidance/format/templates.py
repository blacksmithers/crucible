"""Composite-pattern prose templates.

The canonical guidance prose the engine emits for each pattern lives in the
i18n catalog (``crucible.i18n.catalog_en``); these functions assemble the
per-pattern substitutions and render the catalog template for the context's
language.
"""

from __future__ import annotations

from typing import Any

from ... import i18n
from ...types.context import PhaseContext
from ...types.finding import CompositeFinding


def _leaf(field_path: str) -> str:
    return ".".join(field_path.split(".")[1:])


def _find_epic(spec: dict[str, Any], eid: str) -> dict[str, Any] | None:
    return next((e for e in (spec.get("epics") or []) if e["id"] == eid), None)


def _find_ticket(spec: dict[str, Any], tid: str) -> dict[str, Any] | None:
    return next(
        (t for e in (spec.get("epics") or []) for t in (e.get("tickets") or []) if t["id"] == tid),
        None,
    )


def format_foundation_gap(
    composite: CompositeFinding, context: PhaseContext, spec: dict[str, Any]
) -> str:
    lang = context.language
    missing_fields = "\n".join(f"  - {_leaf(f.field_path)}" for f in composite.grouped_findings)

    if composite.entity_type == "specification":
        return i18n.render(
            i18n.text(lang, "guidance.foundationGap.specification"),
            {"title": spec.get("title"), "missingFields": missing_fields},
        )

    if composite.entity_type == "epic":
        epic = _find_epic(spec, composite.entity_id)
        epic_title = epic["title"] if epic else composite.entity_id
        return i18n.render(
            i18n.text(lang, "guidance.foundationGap.epic"),
            {
                "title": epic_title,
                "missingFields": missing_fields,
                "entityId": composite.entity_id,
            },
        )

    if composite.entity_type == "ticket":
        ticket = _find_ticket(spec, composite.entity_id)
        ticket_title = ticket["title"] if ticket else composite.entity_id
        return i18n.render(
            i18n.text(lang, "guidance.foundationGap.ticket"),
            {
                "title": ticket_title,
                "missingFields": missing_fields,
                "entityId": composite.entity_id,
            },
        )

    return i18n.render(
        i18n.text(lang, "guidance.foundationGap.fallback"),
        {"entityId": composite.entity_id, "count": len(composite.grouped_findings)},
    )


def format_tactical_gap(
    composite: CompositeFinding, context: PhaseContext, spec: dict[str, Any]
) -> str:
    lang = context.language
    missing_fields = "\n".join(f"  - {_leaf(f.field_path)}" for f in composite.grouped_findings)

    if composite.entity_type == "ticket":
        ticket = _find_ticket(spec, composite.entity_id)
        ticket_title = ticket["title"] if ticket else composite.entity_id
        return i18n.render(
            i18n.text(lang, "guidance.tacticalGap.ticket"),
            {
                "title": ticket_title,
                "missingFields": missing_fields,
                "entityId": composite.entity_id,
            },
        )

    if composite.entity_type == "epic":
        epic = _find_epic(spec, composite.entity_id)
        epic_title = epic["title"] if epic else composite.entity_id
        return i18n.render(
            i18n.text(lang, "guidance.tacticalGap.epic"),
            {
                "title": epic_title,
                "missingFields": missing_fields,
                "entityId": composite.entity_id,
            },
        )

    entity_label = (
        i18n.render(
            i18n.text(lang, "guidance.tacticalGap.specLabel"), {"title": spec.get("title")}
        )
        if composite.entity_type == "specification"
        else composite.entity_id
    )
    return i18n.render(
        i18n.text(lang, "guidance.tacticalGap.fallback"),
        {"entityLabel": entity_label, "missingFields": missing_fields},
    )


def format_conditional_gap(
    composite: CompositeFinding, context: PhaseContext, spec: dict[str, Any]
) -> str:
    lang = context.language
    ticket = _find_ticket(spec, composite.entity_id)
    ticket_title = ticket["title"] if ticket else composite.entity_id
    test_spec = ticket.get("testSpecification") if ticket else None

    missing: list[str] = []
    if not test_spec or not test_spec.get("testTypes"):
        missing.append(i18n.text(lang, "guidance.conditionalGap.testTypes"))
    if not test_spec or not test_spec.get("qualityGates"):
        missing.append(i18n.text(lang, "guidance.conditionalGap.qualityGates"))
    if not test_spec or not test_spec.get("testCommands"):
        missing.append(i18n.text(lang, "guidance.conditionalGap.testCommands"))
    if not test_spec or test_spec.get("coverageTarget") is None:
        missing.append(i18n.text(lang, "guidance.conditionalGap.coverageTarget"))
    missing_str = (
        "\n".join(missing) if missing else i18n.text(lang, "guidance.conditionalGap.absent")
    )

    return i18n.render(
        i18n.text(lang, "guidance.conditionalGap.frame"),
        {"title": ticket_title, "missing": missing_str, "entityId": composite.entity_id},
    )
