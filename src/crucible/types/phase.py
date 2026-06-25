"""Lifecycle phases and output layers (port of ``types/phase.ts``)."""

from __future__ import annotations

from typing import Literal, get_args

# A single concrete phase (everything except the ``all`` aggregate).
SinglePhase = Literal[
    "planning_spec",
    "epic_decomposition",
    "epic_expansion",
    "ticket_decomposition",
    "ticket_expansion",
    "cross_validation",
]

# The phase the spec is in for a ``validate()`` call. ``all`` runs every phase.
ValidationPhase = Literal[
    "planning_spec",
    "epic_decomposition",
    "epic_expansion",
    "ticket_decomposition",
    "ticket_expansion",
    "cross_validation",
    "all",
]

# One of the four output layers ``validate()`` can produce.
ReturnLayer = Literal["structural", "scoring", "crossValidation", "guidance"]

SINGLE_PHASES: tuple[SinglePhase, ...] = get_args(SinglePhase)
VALIDATION_PHASES: tuple[ValidationPhase, ...] = get_args(ValidationPhase)
RETURN_LAYERS: tuple[ReturnLayer, ...] = get_args(ReturnLayer)
