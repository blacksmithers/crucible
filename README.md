<h1 align="center">🔥 crucible</h1>

<p align="center"><i>A self-contained, deterministic validation engine for OpenSpec v1.1 specifications.</i></p>

<p align="center">
  <a href="https://github.com/blacksmithers/crucible/actions"><img src="https://github.com/blacksmithers/crucible/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/crucible-forge/"><img src="https://img.shields.io/pypi/v/crucible-forge.svg" alt="PyPI"></a>
  <img src="https://img.shields.io/pypi/pyversions/crucible-forge.svg" alt="Python versions">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License: Apache 2.0">
  <img src="https://img.shields.io/badge/types-mypy%20strict-blue.svg" alt="mypy strict">
</p>

<p align="center">
  <code>pip install crucible-forge</code> &nbsp;•&nbsp; <code>import crucible</code>
</p>

---

`crucible` takes a software **specification** (with its epics and tickets), scores
it against a fixed, configurable rubric, and reports a **readiness gate** — with
**no LLM, fully deterministic**. Same input, same score, every time.

It is a faithful Python port of the SpecForge `@specforge/validator` engine,
extracted as a standalone library, and is the **planning gate** of
[SpecSmither](https://github.com/blacksmithers/specsmither). The output is
**byte-equivalent to the reference TypeScript engine**, verified by differential
tests across every phase and output layer.

## Why

- 🎯 **Deterministic** — pure scoring, no model calls. Reproducible in CI.
- 📦 **Self-contained** — pure Python; only `pydantic` and `pyyaml` at runtime.
- 🔬 **Faithful** — output matches the reference TS validator (differential-tested).
- 🎚️ **Configurable** — every threshold, tier weight, and check lives in config.
- 🏷️ **Typed** — ships `py.typed`; passes `mypy --strict`.

## Install

```bash
pip install crucible-forge      # → import crucible
# or
uv add crucible-forge
```

Requires Python ≥ 3.11.

## Quick start

```python
from crucible import validate, load_defaults

result = validate(spec, {
    "phase": "planning_spec",
    "config": load_defaults(),                      # optional — loaded by default
    "returns": ["structural", "scoring", "guidance"],
})

if result.scoring and not result.scoring.skipped:
    print(result.scoring.gate_result)   # 'pass' | 'fail'
    print(result.scoring.local_score)   # e.g. 86.11
    print(result.passed)                # overall gate for the phase

# Canonical camelCase JSON (matches the reference engine):
result.to_json_dict()
```

`spec` may be a `crucible.Specification` model **or** a plain `dict` (camelCase,
the OpenSpec v1.1 shape). The `context` accepts the original keys
(`phase`, `activeEntityId`, `config`, `returns`) or their snake_case forms.

## The model

A spec is a hierarchy:

```
Specification → Epic → Ticket  (+ acceptance criteria, impl steps, tests, files, dependencies)
                                    ↘ ticket dependency DAG ↙
```

`validate()` walks this tree and produces up to four **output layers**:

| layer | what it reports |
|---|---|
| `structural` | schema issues — missing fields, format violations, duplicate orders, entity counts |
| `scoring` | the readiness score + gate (rubric tiers, weighted blocks, topology penalties, cascade floors) |
| `crossValidation` | cross-entity consistency — cycles, orphan/island tickets, file conflicts, wave coordination, blueprint coverage |
| `guidance` | human-readable, prioritized fix suggestions composed from the above |

Request the layers you want via `returns`; a single phase returns whatever it
computes, and `phase: "all"` defaults to `["scoring"]`.

## Phases

`validate()` is driven by `context["phase"]`:

| phase | scope | needs `activeEntityId` |
|---|---|:---:|
| `planning_spec` | spec-level fields | |
| `epic_decomposition` | spec + the epic list | |
| `epic_expansion` | one epic's fields | ✓ |
| `ticket_decomposition` | tickets under one epic | |
| `ticket_expansion` | one ticket's fields | ✓ |
| `cross_validation` | full-tree consistency checks | |
| `all` | every phase, keyed under `by_phase` | |

```python
# Summative gate over the whole tree:
allr = validate(spec, {"phase": "all", "returns": ["scoring", "crossValidation"]})
planning_passed = (
    allr.by_phase["planning_spec"].scoring
    and allr.by_phase["planning_spec"].scoring.gate_result == "pass"
)
```

## Structural-only

When you just need the schema check (no scoring/guidance):

```python
from crucible import validate_structural, load_defaults

res = validate_structural(spec, load_defaults(), "planning_spec")
if not res.missing_fields and not res.invalid_fields:
    ...  # schema-clean
```

## Configuration

Every gate is config-driven. `load_defaults()` returns the packaged
`ValidatorConfig` (thresholds, tier weights, the 53-entry rubric thresholds,
topology penalties, cross-validation rules). Layer overrides with `merge_config`:

```python
from crucible import load_defaults, merge_config

config = merge_config(load_defaults(), {"thresholds": {"global": 85}})
```

The scoring rubric (53 entries: 16 spec · 17 epic · 20 ticket) ships as a data
asset at `crucible/guidance/rubric/data/rubric.json`, generated verbatim from the
reference source.

## Public API

```python
from crucible import (
    validate, validate_structural,            # entry points
    load_defaults, load_from_file,            # config loading
    load_partial_from_file, merge_config,
    HARDCODED_DEFAULTS, ValidatorConfigSchema,
    PlanningConfigResolver,                    # project/spec config resolution
    ValidatorInputError,                      # raised on bad context
    Specification, Epic, Ticket, Blueprint,   # OpenSpec models
    models, types,                            # full model + result namespaces
)
```

## Development

```bash
uv sync --all-extras --dev
uv run ruff check src tests
uv run mypy
uv run pytest                 # 125 tests, incl. differential vs the TS engine
```

Fidelity is verified against golden output generated from the current TS source
(`tools/*.mjs`); the golden files are committed, so CI needs no Node. See
[`docs/VALIDATOR-PORT-NOTES.md`](docs/VALIDATOR-PORT-NOTES.md) for the strategy
(including why the reference repo's own fixtures are stale).

## Status

`0.1.0` — a **complete** port, **verified byte-for-byte against the current TS
validator** across every phase and all four output layers (structural · scoring
· crossValidation · guidance).

## License

Apache 2.0 © Gabriel Augusto / blacksmithers
