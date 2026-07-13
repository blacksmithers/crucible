# Changelog

All notable changes to `crucible` (`crucible-forge`) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/); this project
adheres to [Semantic Versioning](https://semver.org/).

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
