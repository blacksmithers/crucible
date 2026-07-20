# Changelog

All notable changes to `crucible` (`crucible-forge`) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/); this project
adheres to [Semantic Versioning](https://semver.org/).

## 0.3.0

Tracks the reference engine (`@specforge/validator`) from **`0.1.20`** through
**`0.1.49`** (MB.9 → MB.13). All goldens were regenerated from the current TS
`validate()` and the port is byte-equivalent across every phase.

`planning_spec`, `epic_decomposition` and `epic_expansion` are unchanged — the
whole of this release lands in `ticket_decomposition`, `ticket_expansion` and
`cross_validation`.

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

### Notes

- The parity fixtures and the seven differential suites are now local-only: they
  are generated from (or are inputs to) the private reference engine, so they
  only run where that checkout exists. Regenerate with `tools/gen_*.mjs`.
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
