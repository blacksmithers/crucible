"""Context input validation."""

from __future__ import annotations

from typing import Any

from ..i18n import SUPPORTED_LANGUAGES, normalize_language

_VALID_PHASES = {
    "planning_spec",
    "epic_decomposition",
    "epic_expansion",
    "ticket_decomposition",
    "ticket_expansion",
    "cross_validation",
    "all",
}

# Only the per-entity SCORE phases require an active entity.
_PHASES_REQUIRING_ENTITY_ID = {"epic_expansion", "ticket_expansion"}

_VALID_RETURNS = {"structural", "scoring", "crossValidation", "guidance"}


class ValidatorInputError(Exception):
    """Raised when ``validate`` receives an invalid context."""

    def __init__(self, message: str) -> None:
        super().__init__(f"[Validator] {message}")
        self.name = "ValidatorInputError"


def validate_input(context: dict[str, Any]) -> None:
    phase = context.get("phase")
    if phase is not None and phase not in _VALID_PHASES:
        raise ValidatorInputError(
            f"Invalid phase '{phase}'. Must be one of: {', '.join(sorted(_VALID_PHASES))}"
        )

    active = context.get("activeEntityId")
    has_entity_id = len(active) > 0 if isinstance(active, list) else active is not None

    if phase is not None and phase in _PHASES_REQUIRING_ENTITY_ID and not has_entity_id:
        raise ValidatorInputError(f"Phase '{phase}' requires activeEntityId")

    returns = context.get("returns")
    if returns:
        for r in returns:
            if r not in _VALID_RETURNS:
                raise ValidatorInputError(
                    f"Invalid return layer '{r}'. Must be one of: "
                    f"{', '.join(sorted(_VALID_RETURNS))}"
                )

    language = context.get("language")
    if language is not None and (
        not isinstance(language, str) or normalize_language(language) is None
    ):
        raise ValidatorInputError(
            f"Invalid language '{language}'. Must be one of: "
            f"{', '.join(SUPPORTED_LANGUAGES)}"
        )

    if not context.get("config"):
        raise ValidatorInputError("context.config is required")
