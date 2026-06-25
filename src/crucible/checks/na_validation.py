"""N/A declaration checks (port of ``checks/na-validation.ts``).

Emitted as cross-validation findings by the per-entity phases (planning_spec,
epic_expansion, ticket_expansion). Operates on the normalized entity dict.
"""

from __future__ import annotations

from typing import Any

from ..guidance.rubric import ALL_RUBRIC_ENTRIES
from ..scoring.field_declarations import validate_na_declaration
from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding
from ..types.rubric import RubricEntry


def _field_key(field_path: str) -> str:
    dot = field_path.find(".")
    return field_path[dot + 1 :] if dot != -1 else field_path


def _entries_by_flat_path(prefix: str) -> dict[str, RubricEntry]:
    return {
        _field_key(e.field_path): e
        for e in ALL_RUBRIC_ENTRIES
        if e.field_path.startswith(prefix + ".")
    }


def _check_na_on_entity(
    entity: dict[str, Any], label: str, config: ValidatorConfig, prefix: str
) -> list[CrossValidationFinding]:
    decls = entity.get("fieldDeclarations")
    if not decls:
        return []

    entity_id = entity.get("id") or ""
    entries = _entries_by_flat_path(prefix)

    findings: list[CrossValidationFinding] = []
    for flat_path in decls:
        entry = entries.get(flat_path)
        if entry is None:
            continue
        result = validate_na_declaration(entity, entry.field_path, entry, config)
        if not result.valid and result.reason != "not-declared":
            message = (
                result.message
                or f'Invalid N/A declaration for "{entry.field_path}" on {label}'
            )
            findings.append(
                CrossValidationFinding(
                    category="na-validation",
                    severity="error" if result.reason == "not-eligible" else "warning",
                    field=entry.field_path,
                    message=message,
                    entity_ids=[entity_id],
                    primary_entity_id=entity_id,
                    operations=[],
                )
            )
    return findings


def validate_na_spec(spec: dict[str, Any], config: ValidatorConfig) -> list[CrossValidationFinding]:
    return _check_na_on_entity(spec, f'specification "{spec.get("title")}"', config, "specification")


def validate_na_epic(epic: dict[str, Any], config: ValidatorConfig) -> list[CrossValidationFinding]:
    return _check_na_on_entity(epic, f'epic "{epic.get("title")}"', config, "epic")


def validate_na_ticket(
    ticket: dict[str, Any], config: ValidatorConfig
) -> list[CrossValidationFinding]:
    return _check_na_on_entity(ticket, f'ticket "{ticket.get("title")}"', config, "ticket")
