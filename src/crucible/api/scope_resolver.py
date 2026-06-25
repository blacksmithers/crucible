"""Entity scope resolution (port of ``api/scope-resolver.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

TicketResolution = Literal["all", "by-epic", "by-ticket", "mixed"]


@dataclass(frozen=True)
class ResolvedTicketScope:
    tickets: list[dict[str, Any]]
    resolution: TicketResolution


def _as_ids(active_entity_id: str | list[str] | None) -> list[str]:
    if isinstance(active_entity_id, list):
        return active_entity_id
    return [active_entity_id] if active_entity_id is not None else []


def resolve_epic_scope(
    spec: dict[str, Any], active_entity_id: str | list[str] | None
) -> list[dict[str, Any]]:
    epics = spec.get("epics") or []
    if not active_entity_id:
        return epics

    resolved: list[dict[str, Any]] = []
    for eid in _as_ids(active_entity_id):
        epic = next((e for e in epics if e.get("id") == eid), None)
        if epic is None:
            raise ValueError(f"activeEntityId '{eid}' does not match any epic in spec")
        resolved.append(epic)
    return resolved


def resolve_ticket_scope(
    spec: dict[str, Any], active_entity_id: str | list[str] | None
) -> ResolvedTicketScope:
    epics = spec.get("epics") or []
    if not active_entity_id:
        return ResolvedTicketScope(
            tickets=[t for e in epics for t in (e.get("tickets") or [])],
            resolution="all",
        )

    resolved: list[dict[str, Any]] = []
    resolutions: set[str] = set()
    for eid in _as_ids(active_entity_id):
        epic = next((e for e in epics if e.get("id") == eid), None)
        if epic is not None:
            resolved.extend(epic.get("tickets") or [])
            resolutions.add("by-epic")
            continue
        ticket = next(
            (t for e in epics for t in (e.get("tickets") or []) if t.get("id") == eid), None
        )
        if ticket is not None:
            resolved.append(ticket)
            resolutions.add("by-ticket")
            continue
        raise ValueError(f"activeEntityId '{eid}' does not match any epic or ticket in spec")

    unique = list({t["id"]: t for t in resolved}.values())
    resolution: TicketResolution = (
        cast(TicketResolution, next(iter(resolutions))) if len(resolutions) == 1 else "mixed"
    )
    return ResolvedTicketScope(tickets=unique, resolution=resolution)
