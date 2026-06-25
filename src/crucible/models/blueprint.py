"""Blueprint entity (port of ``spec-types/schema/blueprint.ts``)."""

from __future__ import annotations

from ._base import Entity
from .enums import BlueprintCategory, BlueprintCoverageType, BlueprintFormat


class Blueprint(Entity):
    id: str
    title: str
    description: str | None = None
    slug: str | None = None
    category: BlueprintCategory
    format: BlueprintFormat | None = None
    coverage_type: BlueprintCoverageType = BlueprintCoverageType.TICKET
    content: str
    notes: str | None = None
    version: str | None = None
    order: int | None = None
    tags: list[str] | None = None
