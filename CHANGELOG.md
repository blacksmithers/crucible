# Changelog

All notable changes to `crucible` (`crucible-forge`) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/); this project
adheres to [Semantic Versioning](https://semver.org/).

## 0.4.0

Guidance internationalization: the `guidance` layer's prose can now be emitted
in Brazilian Portuguese. Default English output is byte-identical to 0.3.0 —
scoring, structural, and cross-validation data layers are untouched.

### Added

- **Guidance internationalization (`context["language"]`)** — the `guidance`
  layer's prose can now be emitted in Brazilian Portuguese via
  `language: "pt-br"` (aliases `pt`, `pt_BR`; default `"en"`, unchanged
  output). Covers every guidance source: the 53 rubric `curriculumPrompt`s and
  28 `naWithoutReasonPrompt`s, individual-finding frames, composite-pattern
  templates (foundation/tactical/conditional gap), the fixed decomposition
  prompts, operation descriptions, and all cross-validation emission prose.
  Scores, finding `message`s, field paths, and operation names stay canonical
  English. Translations live in `crucible/i18n/data/<lang>.json` as an overlay
  catalog with per-key English fallback; an unsupported tag raises
  `ValidatorInputError`.

## 0.3.0

This release reworks file coordination in the cross-validation layer, formalizes
N/A eligibility, adds two dependency-graph analyzers, and tightens the format
gate. The `planning_spec`, `epic_decomposition` and `epic_expansion` phases are
behaviorally unchanged; the new work lands in `ticket_decomposition`,
`ticket_expansion` and `cross_validation`, alongside a set of format-gate and
numeric-precision fixes that apply across the engine.

### Added

- **`file-provenance` cross-validation check** — a single static file-graph model
  for file coordination. Four invariants over the existence set
  `E = existingFiles ∪ createdPaths`: *consume-exists* (a consumed path — now
  including `filesToBeDeleted` — must exist), *consume-ordered* (a consumer of an
  in-spec-created path must depend on the creator transitively; grep-provenanced
  paths are exempt), *create-fresh* (creating a path that already exists), and
  *no-delete-of-spec-touched*.
- **`concurrent-modification` cross-validation check** — two tickets modifying the
  same path must be ordered by a dependency path. Uses mutual reachability in the
  dependency DAG, so it is robust to unrelated edge edits and fires across waves.
- **`ValidationContext.existingFiles`** — optional grep evidence for
  file-provenance, tri-state: absent → strict spec-internal existence; present
  (even empty) → union with `filesToBeCreated`. The engine stays
  filesystem-free; the caller supplies the set.
- **`crucible.na_eligible`** — the shared N/A-eligibility allow-set,
  `{ rubric naEligible fields } ∪ { cross-cutting scopes }`, exposing
  `na_eligible_scopes_for()` and `is_na_eligible_scope()`. Formalizes
  `ticket.dependencies`, which the cross-validation checks read off
  `fieldDeclarations` directly but which has no rubric entry.
- **`cycle_analysis` and `creator_election`** — two pure analyzers returning
  structured values (not findings) for cycle-resolution and shared-file
  provenance planning.
- **`compute_grep_candidates()`** — the paths a caller should probe to populate
  `existingFiles`.

### Changed

- **`blueprint-coverage` moved from `cross_validation` to `ticket_decomposition`**,
  where it is now a direct structural gate rather than a registry check. As a
  result `ticket.blueprintReferences` is no longer scored in `ticket_expansion`,
  which rescales that phase (a former `localScore` of 80 now reads 78.95 — the
  rubric denominator shrank, the answer did not).
- **Guidance is WHAT-only** — `orphan-reference`, `island-ticket` and
  `topology-roots-exceed` state the structural fact and the remedies; the concrete
  invocation mechanics are left to the caller. The machine-readable hint is
  `finding.operations`. `topology-leaves-exceed` is deliberately unchanged.
- **Default-config correction.** The packaged `data/defaults.yml` carried
  `arrayMinCounts.epic.tickets.default = 3`, while `CONFIG_DEFAULTS` (the
  authoritative hardcoded defaults, and what the gate uses) has `2`. The YAML —
  which is what `load_defaults()` reads — is now `2`.

### Removed

- Cross-validation checks `files-to-be-referenced`,
  `wave-concurrent-modification`, `wave-deletion-after-creation` and
  `wave-deletion-after-modification` — subsumed by `file-provenance` and
  `concurrent-modification`. The registry goes from 13 to 11 checks.
- Composite guidance patterns `linkage-gap` and `integrity-gap`, and their two
  literals from `CompositePatternId`. They were unreachable — phase-gated to
  `cross_validation`, which never composes findings — so removing them changes no
  observable output. The file-graph findings they anticipated now live in the
  `file-provenance` / `concurrent-modification` checks.

### Fixed

- **`validate(spec, {phase: "all"})` now includes the top-level `phase: "all"`**
  in the JSON. It was dropped because the result serializes with
  `exclude_unset=True` and the field was never set explicitly; both construction
  sites now set it. Phase `"all"` (a distinct `ValidationResultAll` shape) is now
  covered by the conformance suite.
- **Averages could shift by a ULP.** Score means used `sum()/len()`, and on
  CPython ≥ 3.12 `sum()` applies compensated (Neumaier) summation, which can land
  on a different float than a plain accumulation and, at a threshold boundary,
  flip a cascade-gate decision. Averaging now accumulates left-to-right in
  `scoring/global_._avg` and `scoring/per_entity`, for an order-defined result.
- **The format gate is now strict and matches the OpenSpec v1.1 schema exactly.**
  Previously it silently coerced and over-accepted, which could turn a malformed
  spec into a passing one. Now:
  - No coercion — a numeric string, a boolean, or an explicit `null` is rejected
    where a number or string is required.
  - An optional field accepts a missing key but rejects an explicit `null`; the
    three nullable fields (`coverageTarget`, blueprint-ref `context` / `section`)
    still accept `null`.
  - Restored numeric bounds (`order` / `estimatedMinutes` ≥ 0, `ticketNumber` > 0,
    the `EpicTargets` / acceptance-criterion / implementation-step minimums) and
    fields (code/type-snippet `order`, ticket/blueprint `tags`); string-array
    elements must be strings, not coercible values.
  - `testSpecification` no longer requires non-empty `testTypes` / `qualityGates`
    — those minimums are a `ticket_expansion` rubric concern, not a shape check,
    so a present-but-empty `testSpecification` no longer fails
    `ticket_decomposition`.
  - Schema errors report `Expected {type}, received {type}` for type mismatches
    (including `null`) and `Invalid enum value. Expected a | b, received 'x'` for
    enum mismatches.

  Note: an integer field accepts only integer literals — a float such as JSON
  `2.0` is rejected; emit `2`.
- **String lengths count UTF-16 code units.** Rubric minimum-length gates and the
  schema previously counted Unicode code points, which agrees for common text but
  not for astral characters (an emoji is two UTF-16 units). A field of emoji near
  a minimum now scores and validates by UTF-16 length — in scoring, guidance and
  the schema — via `crucible._utf16.utf16_len`.

### Breaking

- `OperationName` renames: `add_dependencies` → `create_dependencies`,
  `remove_dependency` → `delete_dependencies`, `link_blueprint` →
  `link_blueprint_to_tickets`, `unlink_blueprint` → `unlink_blueprint_to_tickets`.
- `CompositePatternId` no longer accepts `linkage-gap` / `integrity-gap`.
- Finding categories `files-to-be-referenced`, `wave-concurrent-modification`,
  `wave-deletion-after-creation` and `wave-deletion-after-modification` no longer
  exist (`wave-size-exceed` remains — the last check with a wave timeline).
- **`crossValidation.checks` keys renamed, and the mismatch fails *silently*.** A
  full config loaded through `load_from_file()` is not merged over the defaults,
  and an absent check key is treated as disabled — so a `0.2.0` config keeps
  validating without error while `concurrent-modification` and `file-provenance`
  never run, and `blueprint-coverage` still fires in `cross_validation`,
  duplicating the gate now in `ticket_decomposition`. Rename
  `wave-concurrent-modification` / `wave-deletion-after-{creation,modification}` /
  `files-to-be-referenced` → `concurrent-modification` / `file-provenance`, and set
  `blueprint-coverage.enabledPhases` to `[all]`.
- `ticket_expansion` scores change (see **Changed**).
- **Format validation is strict** (see **Fixed**). A spec that only passed under
  `0.2.0` because of the old coercion or `null`-tolerance — a numeric string for a
  number, an explicit `null` on an optional, a negative `order` — is now flagged.
  This is a correctness fix, but it can turn a previously-passing spec into a
  failing one.

### Notes

- The full golden conformance corpus is kept local to the maintainer; the tests
  that ship and run in CI are the module unit suites (file-provenance,
  concurrent-modification, cycle-analysis, creator-election, na-eligible), the
  format and UTF-16 suites, and the property and smoke tests.

## 0.2.0

Behavioral corrections to the expansion gate and to structural findings.

### Changed

- **The expansion-phase gate is ALL-PASS, not the average.** In `epic_expansion`
  and `ticket_expansion`, the local gate now requires **every** scoped entity to
  clear its threshold; previously the *mean* was compared, so a strong entity
  could mask a sub-threshold one (a phase reached e.g. a 72.5 / 70.08 mean while
  individual entities sat below 70 and still "passed"). The mean is still reported
  as the phase `localScore`; only the pass/fail decision changed.
- **Entity-count findings embed the epic id** — the `epic.tickets` below-min /
  above-max structural findings now read `Epic "…" (epicId: …) has N ticket(s); …`
  so the id travels inline in the message.
- **Decomposition guidance advances via `complete_planning_session`** — the fixed
  epic/ticket decomposition prompts previously named a verb
  (`complete_decomposition_phase`) that does not exist.

## 0.1.0

- Initial release. A self-contained, deterministic validation engine for OpenSpec
  v1.1 specifications: the structural, scoring, cross-validation and guidance
  layers over a configurable rubric, driven by a combinatorial
  `validate(spec, context)` API across phases, modes and output layers. Pure
  Python, no model calls — same input, same score, every time.
