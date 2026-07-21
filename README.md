<p align="center">
  <img src="assets/crucibleforge-logo.svg" alt="crucible" width="440">
</p>

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

It is the **planning gate** of
[SpecSmither](https://github.com/blacksmithers/specsmither), packaged as a
standalone library with a stable API and a conformance suite that pins its output
across every phase and layer.

## Why

- 🎯 **Deterministic** — pure scoring, no model calls. Reproducible in CI.
- 📦 **Self-contained** — pure Python; only `pydantic` and `pyyaml` at runtime.
- 🔬 **Conformance-tested** — a golden suite pins every phase and output layer.
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

# Canonical camelCase JSON:
result.to_json_dict()
```

`spec` may be a `crucible.Specification` model **or** a plain `dict` (camelCase,
the OpenSpec v1.1 shape). The `context` accepts the original keys
(`phase`, `activeEntityId`, `config`, `returns`, `existingFiles`, `language`) or
their snake_case forms.

`existingFiles` is optional grep evidence for the file-provenance check — the set
of paths that already exist in the real repository. It is tri-state: **omit** it
and existence is judged strictly against what the spec creates; **pass it** (even
empty) and it is unioned with those paths, so a brownfield file no ticket creates
stops being reported as missing. The engine never touches the filesystem itself —
you supply the set (`crucible.compute_grep_candidates(spec)` tells you which
paths are worth probing).

## Guidance language (i18n)

The `guidance` layer's prose can be emitted in another language via
`context["language"]`. Default is `"en"`; `"pt-br"` (aliases `pt`, `pt_BR`)
ships in the package:

```python
result = validate(spec, {
    "phase": "planning_spec",
    "returns": ["guidance"],
    "language": "pt-br",
})
# → 'Especificação "Minha Spec" — fase planning_spec incompleta. ...'
```

Only guidance **prose** is translated — scores, finding `message`s, field
paths, and operation names stay canonical, so machine consumers are unaffected.
An unsupported tag raises `ValidatorInputError`. Translations are packaged JSON
catalogs (`crucible/i18n/data/<lang>.json`) that overlay the canonical English;
a missing key falls back to English rather than failing.

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
asset at `crucible/guidance/rubric/data/rubric.json`.

## Public API

```python
from crucible import (
    validate, validate_structural,            # entry points
    load_defaults, load_from_file,            # config loading
    load_partial_from_file, merge_config,
    CONFIG_DEFAULTS, ValidatorConfigSchema,
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
uv run pytest
```

Behavior is pinned by a golden conformance corpus. The full corpus is kept local
to the maintainer; the tests that ship and run in CI are the unit suites for the
self-contained modules (file-provenance, concurrent-modification, cycle-analysis,
creator-election, na-eligible), the format and UTF-16 suites, and the property
and smoke tests — no fixtures needed. Every release is cut only after the full
conformance corpus passes.

## Status

`0.3.0` — stable across every phase and all four output layers (structural ·
scoring · crossValidation · guidance).

Highlights of this release: file coordination is now a single static
**file-provenance** model (four invariants over an existence set that an optional
`existingFiles` context supplies — the engine stays filesystem-free), and
**concurrent-modification** orders same-file writers by dependency reachability
instead of wave collision. `blueprint-coverage` moved to `ticket_decomposition`,
which rescales `ticket_expansion` scores. N/A eligibility became a shared
allow-set (`crucible.na_eligible`). Two pure analyzers — `cycle_analysis` and
`creator_election` — compute cycle-resolution and shared-file plans. The format
gate is now strict (no coercion, `null`-rejecting optionals, UTF-16 string
lengths). See [`CHANGELOG.md`](CHANGELOG.md) for the full list, including breaking
renames in `OperationName`.

## License

Apache 2.0 © Gabriel Augusto Gonçalves / blacksmithers
