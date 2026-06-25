"""Leaf literal aliases shared across the validator type contracts.

Kept in a dependency-free module so that ``rubric``, ``finding``, ``guidance``
and ``result`` can all import them without cycles.
"""

from __future__ import annotations

from typing import Literal

# Tier classification for a rubric entry (result.ts).
Tier = Literal["critical", "recommended", "enrichment", "contextual"]

# Imperative action verbs a rubric entry suggests (rubric.ts).
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

# Per-field fulfilment status (finding.ts).
FindingStatus = Literal["missing", "partial", "fulfilled"]

# Entity a finding/guidance message is about.
EntityType = Literal["specification", "epic", "ticket"]

# Composite guidance grouping patterns (finding.ts).
CompositePatternId = Literal[
    "foundation-gap",
    "tactical-gap",
    "conditional-gap",
    "linkage-gap",
    "integrity-gap",
]

# Finding severity used by structural + cross-validation layers (result.ts).
Severity = Literal["error", "warning"]
