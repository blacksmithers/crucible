"""Leaf literal aliases shared across the validator type contracts.

Kept in a dependency-free module so that ``rubric``, ``finding``, ``guidance``
and ``result`` can all import them without cycles.
"""

from __future__ import annotations

from typing import Literal

# Tier classification for a rubric entry.
Tier = Literal["critical", "recommended", "enrichment", "contextual"]

# Imperative action verbs a rubric entry suggests.
ActionVerb = Literal[
    "EXPLORE",
    "EVALUATE",
    "DECLARE",
    "CREATE",
    "ADD",
    "JUSTIFY",
    "RECONCILE",
    "DECOMPOSE",
]

# Per-field fulfilment status.
FindingStatus = Literal["missing", "partial", "fulfilled"]

# Entity a finding/guidance message is about.
EntityType = Literal["specification", "epic", "ticket"]

# Composite guidance grouping patterns.
CompositePatternId = Literal[
    "foundation-gap",
    "tactical-gap",
    "conditional-gap",
]

# Finding severity used by structural + cross-validation layers.
Severity = Literal["error", "warning"]
