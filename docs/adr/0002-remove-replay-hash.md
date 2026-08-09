# ADR-0002: Remove the Replay Hash, Keep Determinism as a Property

## Status

Accepted — supersedes ADR-0001, Key Design Decisions #6 ("Replay Hash for
Determinism") and Data Flow step 8 ("Compute replay_hash").

## Context

ADR-0001 decision #6 introduced the replay hash: a SHA-256 of canonical bytes
(input, `contract.as_dict()`, status, and the serialized candidate set
including `recognition_rule`, `validation_rule`, and provenance). Its stated
rationale was "Auditability and reproducibility", with the hash intended to
"break on edition changes". It is enforced by
`tests/integration/test_default_replay_hashes.py`, which pins per-capability
baseline literals.

As Paxman grew to nine shipped capabilities (a tenth in development), the hash
became a constraint on the layer that should be the most permissive:

- **Every recognition-surface extension shifts the hash.** Adding a grammar,
  an alias or plural table, or a spelling variant changes the candidate set or
  provenance serialization and forces baseline-literal churn in
  `test_default_replay_hashes.py` across all capabilities — whether or not any
  user-visible behavior changed. The SI Unit plan's Task 11 dedicates an
  entire step to locking a hash that any later recognition extension (e.g.
  plural names) immediately invalidates.
- **The ceremony now dominates evolution decisions.** AGENTS.md codifies
  "Never modify baseline replay-hash literals" as an anti-pattern. The
  practical effect is a stability-over-usefulness bias: the recognition layer
  — the layer that makes Paxman "smarter" by widening the input surface — is
  the layer most penalized for evolving.

The layered contract that ADR-0001 already specifies is the correct model and
is already implemented in `paxman/engine/orchestrator.py`:

- Recognition (`_recognize`) runs all active grammars exhaustively, emitting
  multiple span-bearing `RecognizedRep`s. No status is computed here.
- Validation (`_collect_candidates`) routes recognitions to rules, reducing
  or producing candidates. No ambiguity is computed here.
- The result layer (`_dedup_candidates`, `_determine_status`) deduplicates
  candidates: one surviving distinct value is SUCCESS, more than one is
  AMBIGUOUS, none (with recognitions) is INVALID. MISSING is produced only
  when nothing was recognized, so no validation ever ran.

The replay hash is not part of that contract. It is an external audit artifact
bolted onto it.

**Determinism is not the fingerprint.** The pipeline is deterministic by
construction: a frozen registry, deterministic ordering, and exhaustive rule
validation. The replay hash is a self-certifying fingerprint *of* that
determinism. Removing the fingerprint does not make the pipeline
nondeterministic; it removes an artifact that consumers do not read and that
churns on every behavior extension.

## Decision

Remove the replay hash from Paxman.

1. **`VersionStamp` loses `replay_hash`; `paxman_version` stays.** Consumers
   keep a version answer; only the fingerprint goes.
2. **Delete the hash machinery** from the engine: `_compute_replay_hash`,
   `_candidate_to_dict`, and `_provenance_to_dict` (the last two exist solely
   for hash serialization).
3. **Delete `tests/integration/test_default_replay_hashes.py`.** No
   per-capability hash baselines are added anywhere else.
4. **Revisit `CapabilityContract.as_dict()` / `_extra_dict_fields()`.** Their
   documented rationale — "replay-deterministic keys" — dies with the hash.
   Keep `as_dict()` only if it earns its place as contract introspection;
   update the nested AGENTS.md conventions (core + capabilities) to match
   whatever survives.
5. **Reaffirm the layered contract unchanged** — recognition emits multiple
   RecognizedReps and never computes status; validation produces candidates
   and never computes ambiguity; the result layer deduplicates candidates
   into SUCCESS / AMBIGUOUS / INVALID; MISSING arises only from recognition
   with no validation run. Add an invariant test locking this: status is
   computed only in `_determine_status`.
6. **Reinvest the regression coverage (condition of acceptance).** The hash
   was a cheap CI net for candidate-multiset and provenance drift that
   value-level assertions miss. Every per-capability pipeline test that
   previously asserted a baseline hash must instead assert, for its locked
   rows, the candidate multiset (count + canonical values) and the set of
   provenance authorities. The SI Unit plan's e2e table already names the
   validating authority per row — that column becomes an enforced assertion.

## Consequences

### Positive

- Recognition-surface growth — new grammars, alias/plural tables, spelling
  variants — no longer carries hash-baseline ceremony. Where the architecture
  allows, behavior extensions become data-adds.
- Smaller surface: one `VersionStamp` field, three engine helpers, and a whole
  test file disappear; the "never modify baseline replay-hash literals"
  anti-pattern and its documentation vanish.
- The change is decoupled from the layered contract, which was already right;
  no status semantics move.

### Negative

- Consumers lose the self-certifying byte-for-byte fingerprint: automatic
  cross-run/cross-version drift detection by hash comparison is no longer
  available.
- CI loses an inexpensive whole-pipeline drift detector. If the candidate-
  multiset/provenance assertions from Decision #6 are not implemented in the
  same change, the regression net is silently weakened.
- Breaking public API change: `ExecutionResult.version_stamp.replay_hash`
  disappears. Acceptable at 0.x; would be semver-major at >= 1.0.

### Risks

- **Coverage reinvestment quality.** If the new assertions check only
  status + canonical value, provenance-drift detection is lost. Mitigation:
  each pipeline test asserts candidate count and the provenance-authority set
  per locked row.
- **Incomplete documentation sweep.** 55 files reference the hash. Mitigation:
  this ADR lands before code; the sweep covers ARCHITECTURE.md, AGENTS.md
  (root, core, capabilities, tests), CONTEXT.md, SECURITY.md,
  CONTRIBUTING.md, TESTING_STRATEGY.md, HOW_TO_ADD_NEW_CAPABILITY.md, and
  capability_homogeneity_audit.md. Historical capability plans are left as
  historical records.

## Alternatives Considered

1. **Keep the hash, make it opt-in (contract flag / method).** Rejected — the
   cost lives in the baseline ceremony and the evolution constraint, which an
   opt-in flag does not remove; it also keeps two divergent code paths.
2. **Keep the hash but auto-rebaseline on every change.** Rejected — turns a
   regression net into a rubber stamp; CI would green unintended drift.
3. **Replace the fingerprint with semantic drift assertions.** Adopted — the
   candidate-multiset/provenance assertions in Decision #6 are the real
   regression net, and they are more diagnostic than a hash: a hash says
   "something changed"; an assertion says what changed.
4. **Drop `version_stamp` entirely.** Rejected — `paxman_version` is cheap and
   useful to consumers; only the hash is removed.

## References

- ADR-0001 — Key Design Decisions #6 (superseded), #5, #7, #16 (reaffirmed);
  Data Flow step 8 (superseded)
- `paxman/engine/orchestrator.py` — `_recognize`, `_collect_candidates`,
  `_dedup_candidates`, `_determine_status` (unchanged), `_compute_replay_hash`
  (removed)
- `paxman/core/domain.py` — `VersionStamp` (replay_hash removed)
- `tests/integration/test_default_replay_hashes.py` (removed)
- `docs/superpowers/plans/2026-08-09-si-units-capability.md` — Task 11
  (replay-hash step dropped)
