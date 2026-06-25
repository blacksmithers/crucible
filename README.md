<h1 align="center">crucible</h1>

<p align="center"><i>A self-contained, deterministic validation engine for OpenSpec v1.1 specifications.</i></p>

<p align="center">
  <code>pip install crucible-forge</code> &nbsp;•&nbsp; <code>import crucible</code>
</p>

---

`crucible` scores a specification (and its epics and tickets) against a fixed,
configurable rubric and reports a readiness gate — **no LLM, fully
deterministic**. It is a faithful Python port of the SpecForge `@specforge/validator`
engine, extracted as a standalone open-source library.

It is the **planning gate** of [SpecSmither](https://github.com/blacksmithers/specsmither):
the same rubric, scoring formula, topology penalties, and cross-validation
checks, with byte-equivalent output to the original TypeScript engine (verified
by differential snapshot tests).

## Why

- **Deterministic** — same input, same score, every time. No model calls.
- **Self-contained** — pure Python; only `pydantic` and `pyyaml` at runtime.
- **Faithful** — output matches the reference TS validator (snapshot-tested).
- **Configurable** — every threshold, tier weight, and check lives in config.

## Quick start

```python
from crucible import validate, load_defaults

result = validate(spec, {
    "phase": "planning_spec",
    "config": load_defaults(),
    "returns": ["structural", "scoring", "guidance"],
})

if result.scoring and not result.scoring.skipped:
    print(result.scoring.gate_result, result.scoring.local_score)
```

`spec` may be a `crucible.Specification` model or a plain `dict`.

### Phases

`validate()` is driven by `context["phase"]`:

| phase | scope |
|---|---|
| `planning_spec` | spec-level fields |
| `epic_decomposition` | spec + the epic list |
| `epic_expansion` | one epic's fields (needs `activeEntityId`) |
| `ticket_decomposition` | tickets under one epic (needs `activeEntityId`) |
| `ticket_expansion` | one ticket's fields (needs `activeEntityId`) |
| `cross_validation` | full-tree consistency checks |
| `all` | every phase, keyed under `by_phase` |

## Status

Early development (`0.1.0.dev`). The gate-relevant engine is complete and
**verified byte-for-byte against the current TS validator**:

| Layer | Status |
|---|---|
| config (rubric, thresholds, defaults) | ✅ complete |
| structural (presence, schema/format, duplicate-order, entity-count) | ✅ differential-verified |
| scoring (53-entry rubric, tiers, topology, cascade) | ✅ differential-verified |
| cross-validation (13 checks) | ✅ differential-verified |
| `validate()` API (6 phases + dispatcher) | ✅ differential-verified |
| guidance (advisory prose composition) | ⏳ not yet ported |

So `validate(..., returns=["structural", "scoring", "crossValidation"])` is
faithful; the `guidance` layer (advisory messages — not part of the gate
decision) is pending. See [`docs/VALIDATOR-PORT-NOTES.md`](docs/VALIDATOR-PORT-NOTES.md)
for the fidelity strategy.

## License

MIT
