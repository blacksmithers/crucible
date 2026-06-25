"""Requirement / NFR coverage checks (port of ``checks/coverage.ts``)."""

from __future__ import annotations

from typing import Any

from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding

_NFR_CATEGORY_TO_TEST_TYPE = {"performance": "performance", "accessibility": "a11y"}


def validate_requirement_coverage(
    spec: dict[str, Any], scoped_epics: list[dict[str, Any]], _config: ValidatorConfig
) -> list[CrossValidationFinding]:
    requirements = spec.get("requirements")
    if not isinstance(requirements, list) or len(requirements) == 0:
        return []

    req_ids = {r.get("id") for r in requirements}
    epic_by_covered_req: dict[str, list[str]] = {}
    for epic in scoped_epics:
        for req_id in epic.get("requirementsCovered") or []:
            epic_by_covered_req.setdefault(req_id, []).append(epic["id"])

    findings: list[CrossValidationFinding] = []
    for req in requirements:
        if req.get("id") not in epic_by_covered_req:
            findings.append(
                CrossValidationFinding(
                    category="requirement-coverage",
                    severity="error",
                    field=f"specification.requirements[id={req.get('id')}]",
                    message=(
                        f'Requirement "{req.get("title")}" (id={req.get("id")}) is not '
                        f"covered by any epic in scope."
                    ),
                    entity_ids=[req.get("id")],
                    primary_entity_id=req.get("id"),
                    operations=["update_epic"],
                )
            )

    for epic in scoped_epics:
        for req_id in epic.get("requirementsCovered") or []:
            if req_id not in req_ids:
                findings.append(
                    CrossValidationFinding(
                        category="requirement-orphan-coverage",
                        severity="error",
                        field=f"epics[id={epic['id']}].requirementsCovered",
                        message=(
                            f'Epic "{epic["id"]}" references requirement "{req_id}" which '
                            f"does not exist in the specification"
                        ),
                        entity_ids=[epic["id"]],
                        primary_entity_id=epic["id"],
                        operations=["update_epic"],
                    )
                )
    return findings


def validate_nfr_coverage(
    spec: dict[str, Any], scoped_epics: list[dict[str, Any]], _config: ValidatorConfig
) -> list[CrossValidationFinding]:
    nfrs = spec.get("nonFunctionalRequirements")
    if not isinstance(nfrs, list) or len(nfrs) == 0:
        return []

    nfr_ids = {n.get("id") for n in nfrs}
    epics_by_covered_nfr: dict[str, list[str]] = {}
    for epic in scoped_epics:
        for nfr_id in epic.get("nfrsCovered") or []:
            epics_by_covered_nfr.setdefault(nfr_id, []).append(epic["id"])

    findings: list[CrossValidationFinding] = []
    for nfr in nfrs:
        covering = epics_by_covered_nfr.get(nfr.get("id"), [])
        if not covering:
            findings.append(
                CrossValidationFinding(
                    category="nfr-coverage",
                    severity="error",
                    field=f"specification.nonFunctionalRequirements[id={nfr.get('id')}]",
                    message=(
                        f'NFR "{nfr.get("description")}" (category={nfr.get("category")}) '
                        f"is not covered by any epic."
                    ),
                    entity_ids=[nfr.get("id")],
                    primary_entity_id=nfr.get("id"),
                    operations=["update_epic"],
                )
            )
            continue

        suggested = _NFR_CATEGORY_TO_TEST_TYPE.get(nfr.get("category"))
        if not suggested:
            continue
        for epic_id in covering:
            cov_epic: dict[str, Any] | None = next(
                (e for e in scoped_epics if e["id"] == epic_id), None
            )
            if cov_epic is None:
                continue
            verification = [
                t for t in (cov_epic.get("tickets") or []) if t.get("ticketType") == "verification"
            ]
            if not verification:
                continue
            any_declares = any(
                suggested in ((t.get("testSpecification") or {}).get("testTypes") or [])
                for t in verification
            )
            if not any_declares:
                findings.append(
                    CrossValidationFinding(
                        category="nfr-test-type-mismatch",
                        severity="warning",
                        field=f"epics[id={epic_id}].tickets",
                        message=(
                            f'Epic "{cov_epic.get("title")}" covers NFR "{nfr.get("description")}" '
                            f"but no verification ticket declares testType={suggested}."
                        ),
                        entity_ids=[epic_id],
                        primary_entity_id=epic_id,
                        operations=["update_ticket"],
                    )
                )

    for epic in scoped_epics:
        for nfr_id in epic.get("nfrsCovered") or []:
            if nfr_id not in nfr_ids:
                findings.append(
                    CrossValidationFinding(
                        category="nfr-orphan-coverage",
                        severity="error",
                        field=f"epics[id={epic['id']}].nfrsCovered",
                        message=(
                            f'Epic "{epic["id"]}" references NFR "{nfr_id}" which does not '
                            f"exist in the specification"
                        ),
                        entity_ids=[epic["id"]],
                        primary_entity_id=epic["id"],
                        operations=["update_epic"],
                    )
                )
    return findings
