"""Field/entity resolution for the guidance engine (port of ``value-resolver.ts``)."""

from __future__ import annotations

from typing import Any

from ...types.enums import EntityType


def resolve_field_value(entity: dict[str, Any], field_path: str) -> Any:
    dot = field_path.find(".")
    if dot == -1:
        return None
    current: Any = entity
    for part in field_path[dot + 1 :].split("."):
        if current is None or not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def get_entity_type(entity: dict[str, Any]) -> EntityType:
    if isinstance(entity.get("epics"), list):
        return "specification"
    if isinstance(entity.get("tickets"), list):
        return "epic"
    return "ticket"


def entry_matches_entity_type(field_path: str, entity_type: EntityType) -> bool:
    return field_path.startswith(entity_type + ".")
