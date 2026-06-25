"""Validator API layer (port of ``@specforge/validator`` ``src/api``)."""

from __future__ import annotations

from .input_validation import ValidatorInputError, validate_input
from .phase_classification import (
    is_human_judgment_phase,
    phase_includes_epics,
    phase_includes_tickets,
)
from .scope_resolver import resolve_epic_scope, resolve_ticket_scope
from .validate import validate
from .version import get_validator_version

__all__ = [
    "ValidatorInputError",
    "get_validator_version",
    "is_human_judgment_phase",
    "phase_includes_epics",
    "phase_includes_tickets",
    "resolve_epic_scope",
    "resolve_ticket_scope",
    "validate",
    "validate_input",
]
