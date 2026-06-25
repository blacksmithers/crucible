"""Duplicate-order checks (port of ``structural/duplicate-order.ts``)."""

from __future__ import annotations

from typing import Any

from ..types.result import StructuralFinding


def _find_duplicates(numbers: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    dups: list[Any] = []
    dup_set: set[Any] = set()
    for n in numbers:
        if n in seen and n not in dup_set:
            dups.append(n)
            dup_set.add(n)
        seen.add(n)
    return dups


def check_duplicate_order(ticket: dict[str, Any]) -> list[StructuralFinding]:
    findings: list[StructuralFinding] = []
    tid = ticket.get("id")

    ac_orders = [a.get("order") for a in (ticket.get("acceptanceCriteria") or [])]
    for order in _find_duplicates(ac_orders):
        findings.append(
            StructuralFinding(
                category="duplicate-order",
                severity="error",
                field=f"tickets[id={tid}].acceptanceCriteria[order={order}]",
                message=(
                    f"Multiple acceptanceCriteria items have order={order}; "
                    "order values must be unique within a ticket"
                ),
            )
        )

    is_orders = [s.get("order") for s in (ticket.get("implementationSteps") or [])]
    for order in _find_duplicates(is_orders):
        findings.append(
            StructuralFinding(
                category="duplicate-order",
                severity="error",
                field=f"tickets[id={tid}].implementationSteps[order={order}]",
                message=(
                    f"Multiple implementationSteps items have order={order}; "
                    "order values must be unique within a ticket"
                ),
            )
        )

    return findings
