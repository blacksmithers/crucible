"""C2 — config layer: loading, defaults, merge, validation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from crucible.config import (
    CONFIG_DEFAULTS,
    ConfigValidationError,
    load_defaults,
    load_from_file,
    merge_config,
    validate_config,
)
from crucible.config.schema import apply_defaults

CONFIGS = Path(__file__).resolve().parents[1] / "fixtures" / "test-surface" / "configs"


def test_load_defaults_core_values() -> None:
    cfg = load_defaults()
    assert cfg["thresholds"] == {"global": 80, "specification": 80, "epic": 70, "ticket": 70}
    assert cfg["tiers"] == {"critical": 3, "recommended": 2, "enrichment": 1, "contextual": 0.5}
    assert cfg["scoring"]["weights"] == {"spec": 0.2, "epics": 0.3, "tickets": 0.5}
    bp = cfg["crossValidation"]["checks"]["blueprint-coverage"]
    assert bp["minTicketsPerBlueprint"] == 2


def test_config_defaults_diverge_from_yaml_faithfully() -> None:
    # defaults.ts (CONFIG_DEFAULTS) and defaults.yml (load_defaults) are
    # intentionally out of sync in the TS source — the port preserves that.
    sr_hc = CONFIG_DEFAULTS["structuralRequirements"]
    assert sr_hc["arrayMinCounts"]["epic"]["tickets"]["default"] == 2
    assert sr_hc["arrayMaxCounts"]["specification"]["epics"]["default"] == 15

    sr_yml = load_defaults()["structuralRequirements"]
    assert sr_yml["arrayMinCounts"]["epic"]["tickets"]["default"] == 3
    assert sr_yml["arrayMaxCounts"]["specification"]["epics"]["default"] == 50


def test_load_test_surface_configs() -> None:
    default_cfg = load_from_file(str(CONFIGS / "default.yml"))
    assert default_cfg["structuralRequirements"]["enforceTypes"] is True

    untyped = load_from_file(str(CONFIGS / "no-types-enforced.yml"))
    assert untyped["structuralRequirements"]["enforceTypes"] is False


def test_merge_config_overrides_and_revalidates() -> None:
    merged = merge_config(load_defaults(), {"thresholds": {"global": 85}})
    assert merged["thresholds"]["global"] == 85
    # untouched keys survive the deep merge
    assert merged["thresholds"]["ticket"] == 70


def test_apply_defaults_injects_optionals() -> None:
    raw = {
        "structuralRequirements": {"arrayMinCounts": {}},
        "crossValidation": {"checks": {"blueprint-coverage": {"enabled": True}}},
    }
    out = apply_defaults(deepcopy(raw))
    sr = out["structuralRequirements"]
    assert sr["enforceTypes"] is True
    assert sr["arrayMaxCounts"] == {}
    assert sr["complexityDrivenMinCounts"] == {}
    assert out["crossValidation"]["checks"]["blueprint-coverage"]["minTicketsPerBlueprint"] == 2


def test_validate_config_rejects_bad_weights() -> None:
    bad = deepcopy(CONFIG_DEFAULTS)
    bad["scoring"]["weights"] = {"spec": 0.5, "epics": 0.3, "tickets": 0.5}
    with pytest.raises(ConfigValidationError):
        validate_config(bad)


def test_validate_config_rejects_bad_threshold_entry() -> None:
    bad = deepcopy(CONFIG_DEFAULTS)
    bad["structuralRequirements"]["arrayMinCounts"]["specification"]["goals"] = {
        "default": 99,
        "min": 1,
        "max": 20,
    }
    with pytest.raises(ConfigValidationError):
        validate_config(bad)
