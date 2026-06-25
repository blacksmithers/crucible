"""Tier weights (port of ``scoring/tiers.ts``)."""

from __future__ import annotations

from ..types.config import ValidatorConfig
from ..types.enums import Tier


def tier_weight(tier: Tier, config: ValidatorConfig) -> float:
    return float(config["tiers"][tier])
