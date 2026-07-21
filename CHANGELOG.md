# Changelog

All notable changes to `crucible` (`crucible-forge`) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/); this project
adheres to [Semantic Versioning](https://semver.org/).

## 0.3.0

Tracks the reference engine (`@specforge/validator`) from **`0.1.20`** through
**`0.1.49`** (MB.9 → MB.13). All goldens were regenerated from the current TS
`validate()` and the port is byte-equivalent across every phase.

The sync itself lands only in `ticket_decomposition`, `ticket_expansion` and
`cross_validation` — `planning_spec`, `epic_decomposition` and `epic_expansion`
are untouched by it. Separately, a cross-language differential fuzz audit run for
this release surfaced a set of **pre-existing** parity defects (present since
`0.2.0` or earlier, in code the eight fixed goldens never exercised); they are
fixed here too and are listed under **Fixed**.

### Added

- **`file-provenance` cross-validation check** (MB.10) — a single static
  file-graph model replacing four separate checks. Four invariants over the
  existence set `E = existingFiles ∪ createdPaths`: *consume-exists* (now also
  covering `filesToBeDeleted`), *consume-ordered* (transitive dependency on an
  in-spec creator; grep-provenanced paths are exempt), *create-fresh* (creating
  a path that already exists in the repo), and *no-delete-of-spec-touched*.
- **`concurrent-modification` cross-validation check** (MB.10) — two tickets
  modifying the same path must be ordered by a dependency path. Replaces the
  same-wave heuristic with mutual reachability in the DAG, so it is robust to
  unrelated edge edits and also fires across waves.
- **`ValidationContext.existingFiles`** — optional grep evidence, tri-state:
  absent → strict spec-internal existence; present (even empty) → union with
  `filesToBeCreated`. The engine remains filesystem-free; the caller injects it.
- **`crucible.na_eligible`** (MB.11) — the shared N/A-eligibility allow-set:
  `{ rubric naEligible fields } ∪ { cross-cutting scopes }`. Exposes
  `na_eligible_scopes_for()` and `is_na_eligible_scope()`. Formalizes
  `ticket.dependencies`, which the cross-validation checks read off
  `fieldDeclarations` directly but which has no rubric entry.
- **`cycle_analysis`** (MB.12) and **`creator_election`** (MB.13) — pure
  analyzers returning structured values (never findings) for cycle-resolution
  and shared-file provenance planning.
- `compute_grep_candidates()` — the paths a caller should probe to supply
  `existingFiles`.

### Changed

- **`blueprint-coverage` moved from `cross_validation` to `ticket_decomposition`**
  (MB.9), where it is now a direct structural gate rather than a registry check.
  Consequently `ticket.blueprintReferences` is no longer scored in
  `ticket_expansion`, which rescales that phase's scores (a former `localScore`
  of 80 now reads 78.95 — the rubric denominator shrank, the answer did not).
- **Guidance is WHAT-only** (MB.11) — `orphan-reference`, `island-ticket` and
  `topology-roots-exceed` state the structural fact and the remedies; the
  invocation mechanics left the prose. The machine hint is `finding.operations`.
  `topology-leaves-exceed` is deliberately untouched.
- **`data/defaults.yml` synced with the reference engine.** This also corrects a
  pre-existing drift the 0.2.0 sync missed: `arrayMinCounts.epic.tickets.default`
  was still `3` in the packaged YAML, while upstream had already lowered it to
  `2` before the 0.1.20 baseline (locked 2026-06-14). `CONFIG_DEFAULTS` already
  carried `2`, so only the YAML — which is what `load_defaults()` actually reads
  — was wrong.

### Removed

- Cross-validation checks `files-to-be-referenced`,
  `wave-concurrent-modification`, `wave-deletion-after-creation` and
  `wave-deletion-after-modification` — subsumed by `file-provenance` and
  `concurrent-modification`. The registry goes from 13 to 11 checks.
- Composite guidance patterns `linkage-gap` and `integrity-gap` (MB.10.7), and
  their two literals from `CompositePatternId`. They were double-locked dead —
  phase-gated to `cross_validation`, which never calls `compose_findings` — and
  they baked flow-invocation syntax into the validator. Removing them changes no
  observable output.

### Fixed

All of the following are **pre-existing** divergences — none is a regression of
the `0.1.49` sync. They were caught by the differential fuzz audit, not by the
goldens, and each is verified byte-for-byte against the reference.

- **`validate(spec, {phase: "all"})` omitted the top-level `phase: "all"`** from
  the JSON. The field existed on the model with a default, but `to_json_dict`
  serializes with `exclude_unset=True` and neither construction site passed it.
  It diverged in every phase-`"all"` run, including the smallest input, and went
  unseen for two releases because no golden covered phase `"all"`. Fixed at both
  sites; phase `"all"` is now a differential case, pinning the `ValidationResultAll`
  shape.
- **Averages diverged in the last ULP.** Score means used `sum()/len()`, and
  CPython ≥ 3.12 gives float `sum()` Neumaier compensated summation — *more*
  accurate than the reference's `reduce((a, b) => a + b, 0)`, and therefore a
  different double (e.g. the cross-validation seed averaged to `…76` in Python,
  `…77` in JS). Being more accurate is still being different, and it can flip a
  cascade-gate decision. Replaced with naive left-to-right accumulation in
  `scoring/global_._avg` and `scoring/per_entity`.
- **The format gate was too lenient — it accepted specs the reference rejects,**
  flipping `passed` false→true. The strict schema (`_strict_schema`) now mirrors
  `@specforge/spec-types` field by field:
  - No coercion. Scalars are strict, so a numeric string, a boolean, or an
    explicit `null` is rejected — matching `z.string()` / `z.number()` /
    `z.number().int()`, which never coerce.
  - `.optional()` rejects an explicit `null` (accepts only a missing key); the
    three genuine `.nullish()` fields (`coverageTarget`, blueprint-ref
    `context`/`section`) still accept `null`. Rendering every optional as
    `X | None` had erased that distinction.
  - Restored numeric bounds that had been dropped (`order` / `estimatedMinutes`
    nonnegative, `ticketNumber` positive, the `EpicTargets` / acceptance-criterion
    / implementation-step minimums) and dropped fields (code/type-snippet `order`,
    ticket/blueprint `tags`); string-array elements are strict, so a non-string
    element is rejected rather than coerced.
  - `TestSpecification` no longer enforces `testTypes`/`qualityGates` ≥ 1 — a
    shape-only relaxation upstream made before the `0.1.20` baseline that the
    `0.2.0` sync should have carried. The port had been rejecting an
    empty-but-present `testSpecification` at `ticket_decomposition`.
  - Error messages now reproduce Zod's exact wording — `Expected {type}, received
    {type}` for type mismatches (including `null`) and `Invalid enum value.
    Expected a | b, received 'x'` for enum mismatches — so parity is on the
    message, not just pass/fail.
- **String lengths are measured in UTF-16 code units**, the unit the reference
  uses (JS `String.length`), not Python code points. They agree on the BMP and
  diverge on astral characters (emoji): a description of emoji near a rubric
  minimum scored differently, and an N/A `reason` of emoji cleared `min(20)` in
  JS but not in Python. Applied in scoring (`per_field`), guidance
  (`structural-checks`) and the schema (`crucible._utf16.utf16_len`).

One micro-divergence is left, documented in `_strict_schema`: a float that is
integer-valued (JSON `2.0`) satisfies `z.number().int()` in JS but Pydantic
strict `int` rejects it. Real producers emit `2`, never `2.0`, for integer
fields, so it is inert in practice.

### Breaking

- `OperationName` renames: `add_dependencies` → `create_dependencies`,
  `remove_dependency` → `delete_dependencies`, `link_blueprint` →
  `link_blueprint_to_tickets`, `unlink_blueprint` →
  `unlink_blueprint_to_tickets`.
- `CompositePatternId` no longer accepts `linkage-gap` / `integrity-gap`.
- Finding categories `files-to-be-referenced`, `wave-concurrent-modification`,
  `wave-deletion-after-creation` and `wave-deletion-after-modification` no longer
  exist. (`wave-size-exceed` remains — it is the last check with a wave timeline.)
- **`crossValidation.checks` keys renamed**, and this fails *silently*. A full
  config loaded through `load_from_file()` is not merged over the defaults, and
  an absent check key is treated as disabled — so a 0.2.0 config keeps validating
  without error while `concurrent-modification` and `file-provenance` never run,
  and `blueprint-coverage` still fires in `cross_validation`, duplicating the gate
  that now lives in `ticket_decomposition`. Rename
  `wave-concurrent-modification` / `wave-deletion-after-{creation,modification}`
  / `files-to-be-referenced` → `concurrent-modification` / `file-provenance`, and
  set `blueprint-coverage.enabledPhases` to `[all]`.
- `ticket_expansion` scores change (see above).
- **Format validation is strict** (see **Fixed**). A spec that only passed under
  `0.2.0` because of the old lax coercion or `null`-tolerance — a numeric string
  for a number, an explicit `null` on an optional, a negative `order` — is now
  flagged, exactly as the reference flags it. This is a bug fix toward parity, but
  it can turn a previously-`passed` spec into a failing one.

### Notes

- The parity fixtures and the differential suites are local-only: they are
  generated from (or are inputs to) the private reference engine, so they only
  run where that checkout exists. Regenerate with `tools/gen_*.mjs`. What ships
  and runs in public CI are the unit suites for the self-contained modules
  (file-provenance, concurrent-modification, cycle-analysis, creator-election,
  na-eligible), the format/UTF-16 parity suites, and the property and smoke tests.
- `get_validator_version()` still returns `0.1.0` — the reference engine's own
  `api/version.ts` has not been bumped.

## 0.2.0

Tracks the reference engine (`@specforge/validator`) from the `0.1.0` port baseline
(commit `15f61c4d`) through **`0.1.20`**. All differential goldens were regenerated
from the current TS `validate()` and remain byte-equivalent.

### Changed

- **Expansion-phase gate is ALL-PASS, not the average** (ME.15.3). In
  `epic_expansion` and `ticket_expansion`, the local gate now requires **every**
  scoped entity to clear its threshold; previously the *mean* was compared, so a
  strong entity could mask a sub-threshold one (a phase reached e.g. a 72.5 /
  70.08 mean while individual entities sat below 70 and still "passed"). The mean
  is still reported as the phase `localScore`; only the pass/fail decision changed.
- **Entity-count findings embed the epic id** — the `epic.tickets` below-min /
  above-max structural findings now read `Epic "…" (epicId: …) has N ticket(s); …`
  so the id travels inline in the message (the `context.epicId` was already present).
- **Decomposition guidance advances via `complete_planning_session`** — the fixed
  epic/ticket decomposition prompts previously named a phantom verb
  (`complete_decomposition_phase`).

### Notes

- No config or ratio-engine changes were needed: crucible already carried the
  synced `epic.tickets` default (`2`) and never ported the deleted
  `checkImplVerificationRatioAll` overload.
- The reference engine's Amplify **enum-parity schema-coverage metacheck**
  (`schema-coverage/*`, added over this range) is **intentionally not ported** —
  it is a repo-internal CI check over an Amplify GraphQL schema that crucible, a
  self-contained runtime validator, does not ship.

## 0.1.0

- Initial release: a complete, differential-tested Python port of the SpecForge
  `@specforge/validator` engine (structural · scoring · cross-validation ·
  guidance), byte-equivalent to the reference TypeScript across every phase.
