"""Presence checks (port of ``structural/presence.ts``).

Operates on the normalized camelCase spec dict (mirrors how the TS engine reads
the object). ``None`` epics/tickets are treated as empty.
"""

from __future__ import annotations

from typing import Any

ARCHITECTURE_MIN_LENGTH = 200


def check_presence(spec: dict[str, Any]) -> list[str]:
    missing: list[str] = []

    architecture = spec.get("architecture")
    if not architecture or len(architecture) < ARCHITECTURE_MIN_LENGTH:
        missing.append("architecture")
    if not spec.get("scope"):
        missing.append("scope")
    if not spec.get("goals"):
        missing.append("goals")
    if not spec.get("requirements"):
        missing.append("requirements")

    for epic in spec.get("epics") or []:
        epic_prefix = f"epic[id={epic.get('id')}]"

        epic_arch = epic.get("architecture")
        if epic_arch is not None and 0 < len(epic_arch) < ARCHITECTURE_MIN_LENGTH:
            missing.append(f"{epic_prefix}.architecture")

        for ticket in epic.get("tickets") or []:
            ticket_prefix = f"ticket[id={ticket.get('id')}]"
            if not ticket.get("acceptanceCriteria"):
                missing.append(f"{ticket_prefix}.acceptanceCriteria")
            if not ticket.get("implementationSteps"):
                missing.append(f"{ticket_prefix}.implementationSteps")

    return missing
