"""Hardcoded default validator config (verbatim port of ``config/defaults.ts``).

This mirrors the TS ``HARDCODED_DEFAULTS`` literal exactly — including the
points where it intentionally diverges from the shipped ``defaults.yml`` (e.g.
``arrayMaxCounts`` caps and ``epic.tickets``/``guardrails`` minimums). It is the
fallback used by :func:`crucible.config.load.load_defaults` when the packaged
YAML is unreadable, and the canonical ``HARDCODED_DEFAULTS`` export.
"""

from __future__ import annotations

from copy import deepcopy

from ..types.config import ValidatorConfig

_CROSS_CHECK_PHASES = ["cross_validation", "all"]


def _check(extra: dict[str, object] | None = None) -> dict[str, object]:
    base: dict[str, object] = {"enabled": True, "enabledPhases": list(_CROSS_CHECK_PHASES)}
    if extra:
        base.update(extra)
    return base


_HARDCODED_DEFAULTS: ValidatorConfig = {
    "thresholds": {"global": 80, "specification": 80, "epic": 70, "ticket": 70},
    "tiers": {"critical": 3, "recommended": 2, "enrichment": 1, "contextual": 0.5},
    "topology": {
        "rootPenalty": -3,
        "leafPenalty": -3,
        "islandPenalty": -6,
        "maxRootRatio": 0.25,
        "maxLeafRatio": 0.25,
    },
    "naReason": {"minLength": 20},
    "crossValidation": {
        "ratios": {
            "blueprintToEpic": {"min": 0.5},
            "implementationToVerification": {"min": 1, "max": 10},
        },
        "topology": {"rootRatio": 0.25, "rootCap": 5, "leafRatio": 0.25, "leafCap": 5},
        "waves": {"maxTicketsPerWave": 5},
        "checks": {
            "circular-dependency": _check(),
            "broken-reference": _check(),
            "orphan-reference": _check(),
            "island-ticket": _check(),
            "topology-roots-exceed": _check(),
            "topology-leaves-exceed": _check(),
            "wave-size-exceed": _check(),
            "wave-concurrent-modification": _check(),
            "wave-deletion-after-modification": _check(),
            "wave-deletion-after-creation": _check(),
            "file-conflict": _check(),
            "files-to-be-referenced": _check(),
            "blueprint-coverage": _check({"minTicketsPerBlueprint": 2}),
        },
    },
    "guidance": {"topNPerEntity": {"default": 5, "min": 1, "max": 100}},
    "scoring": {"weights": {"spec": 0.2, "epics": 0.3, "tickets": 0.5}},
    "structuralRequirements": {
        "enforceTypes": True,
        "arrayMinCounts": {
            "specification": {
                "goals": {"default": 3, "min": 1, "max": 20},
                "requirements": {"default": 3, "min": 1, "max": 30},
                "acceptanceCriteria": {"default": 1, "min": 1, "max": 50},
                "nonFunctionalRequirements": {"default": 1, "min": 1, "max": 30},
                "guardrails": {"default": 2, "min": 1, "max": 20},
                "techStack": {"default": 1, "min": 1, "max": 30},
                "folderStructures": {"default": 1, "min": 1, "max": 10},
                "sharedPatterns": {"default": 1, "min": 1, "max": 20},
                "scope": {
                    "inScope": {"default": 3, "min": 1, "max": 20},
                    "outOfScope": {"default": 1, "min": 1, "max": 20},
                    "assumptions": {"default": 1, "min": 1, "max": 20},
                    "externalDependencies": {"default": 1, "min": 1, "max": 20},
                },
                "epics": {"default": 2, "min": 0, "max": 50},
            },
            "epic": {
                "goals": {"default": 1, "min": 1, "max": 10},
                "acceptanceCriteria": {"default": 1, "min": 1, "max": 20},
                "validationCommands": {"default": 1, "min": 1, "max": 20},
                "apiContracts": {"default": 1, "min": 1, "max": 20},
                "sharedPatterns": {"default": 1, "min": 1, "max": 20},
                "fileStructures": {"default": 1, "min": 1, "max": 20},
                "scope": {
                    "inScope": {"default": 3, "min": 1, "max": 20},
                    "outOfScope": {"default": 1, "min": 1, "max": 20},
                    "assumptions": {"default": 1, "min": 1, "max": 20},
                    "externalDependencies": {"default": 1, "min": 1, "max": 20},
                },
                "tickets": {"default": 2, "min": 0, "max": 50},
            },
            "ticket": {
                "guardrails": {"default": 1, "min": 1, "max": 20},
                "codeReferences": {"default": 1, "min": 1, "max": 20},
                "typeReferences": {"default": 1, "min": 1, "max": 20},
                "blueprintReferences": {"default": 1, "min": 1, "max": 20},
                "testSpecification": {
                    "testTypes": {"default": 1, "min": 1, "max": 10},
                    "qualityGates": {"default": 1, "min": 1, "max": 20},
                    "testCommands": {"default": 1, "min": 1, "max": 10},
                },
            },
        },
        "arrayMaxCounts": {
            "specification": {"epics": {"default": 15, "min": 1, "max": 1000}},
            "epic": {"tickets": {"default": 15, "min": 1, "max": 1000}},
        },
        "arrayCountPhases": {
            "specification": {
                "epics": ["epic_decomposition", "epic_expansion", "cross_validation"],
            },
            "epic": {
                "tickets": ["ticket_decomposition", "ticket_expansion", "cross_validation"],
            },
        },
        "stringMinLengths": {
            "specification": {
                "architecture": {"default": 200, "min": 50, "max": 5000},
                "background": {"default": 50, "min": 20, "max": 2000},
            },
            "epic": {
                "architecture": {"default": 200, "min": 50, "max": 5000},
                "objective": {"default": 100, "min": 20, "max": 1000},
                "description": {"default": 50, "min": 20, "max": 1000},
            },
            "ticket": {
                "description": {"default": 50, "min": 10, "max": 500},
            },
        },
        "itemMinLengths": {
            "specification": {
                "goals": {"default": 20, "min": 5, "max": 500},
                "requirements": {"default": 20, "min": 5, "max": 500},
                "guardrails": {"default": 20, "min": 5, "max": 500},
                "nonFunctionalRequirements": {"default": 30, "min": 10, "max": 500},
            },
            "epic": {
                "goals": {"default": 20, "min": 5, "max": 500},
                "validationCommands": {"default": 5, "min": 3, "max": 500},
            },
            "ticket": {
                "guardrails": {"default": 20, "min": 5, "max": 500},
            },
        },
        "arrayItemFieldMinLengths": {
            "specification": {
                "goals": {
                    "title": {"default": 5, "min": 1, "max": 200},
                    "description": {"default": 30, "min": 10, "max": 1000},
                },
                "requirements": {
                    "title": {"default": 5, "min": 1, "max": 200},
                    "description": {"default": 30, "min": 10, "max": 1000},
                },
            },
            "ticket": {
                "codeSnippets": {"content": {"default": 50, "min": 10, "max": 5000}},
                "typeSnippets": {"content": {"default": 50, "min": 10, "max": 5000}},
            },
        },
        "complexityDrivenMinCounts": {
            "ticket": {
                "codeSnippets": {"small": 1, "medium": 2, "large": 3, "xlarge": 4},
                "typeSnippets": {"small": 1, "medium": 1, "large": 2, "xlarge": 2},
                "acceptanceCriteria": {"small": 2, "medium": 3, "large": 5, "xlarge": 7},
                "implementationSteps": {"small": 2, "medium": 4, "large": 6, "xlarge": 10},
            },
        },
    },
}


def hardcoded_defaults() -> ValidatorConfig:
    """A fresh deep copy of the hardcoded defaults (callers may mutate)."""
    return deepcopy(_HARDCODED_DEFAULTS)


# Public constant mirroring the TS ``HARDCODED_DEFAULTS`` export. Treated as
# read-only; use :func:`hardcoded_defaults` when a mutable copy is needed.
HARDCODED_DEFAULTS: ValidatorConfig = _HARDCODED_DEFAULTS
