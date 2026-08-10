# ADR-0002 Removal — Implementation Plan

| **Title** | Remove the replay hash, keep determinism as a property |
| **Date** | 2026-08-10 |
| **Status** | Draft — ready for review |
| **Branch** | `refactor/remove-replay-hash` (commit per task) |
| **Authoritative spec** | `docs/adr/0002-remove-replay-hash.md` — where this plan and the ADR disagree, the ADR wins |
| **Supersedes** | ADR-0001 Key Design Decisions #6 ("Replay Hash for Determinism") and Data Flow step 8 |

> **For agentic workers.** This plan is written to be executed by a worker
> agent one task at a time. Every task is TDD: **Step 1 RED** (write/adjust
> the failing test first), **Step 2 GREEN** (make it pass), then the scoped
> verify command and the commit. Do not skip steps, do not reorder tasks, do
> not "improve" the design — D-decisions are locked (§1). The full suite is
> only green after Task 12; the per-task verify commands are scoped so each
> task is independently green. Commit with the exact message given for each
> task.

---

## §1 Cross-Part Contract

### Goal

Implement ADR-0002: delete the replay hash from Paxman. `VersionStamp`
keeps only `paxman_version`; the engine loses `_compute_replay_hash`,
`_candidate_to_dict`, and `_provenance_to_dict`; the baseline suite
`tests/integration/test_default_replay_hashes.py` is deleted; and — per
explicit user decision on ADR Decision #4 — **`as_dict()` and
`_extra_dict_fields()` are removed entirely** (protocol, base class, all nine
capability overrides, and their tests). Regression coverage is reinvested as
candidate-multiset + provenance-authority assertions (ADR Decision #6,
condition of acceptance). A new invariant test locks "status is computed only
in `_determine_status`" (ADR Decision #5).

### D-Decisions (locked — do not revisit without a new ADR)

- **D1 — `VersionStamp` keeps `paxman_version`, loses `replay_hash`.** The
  dataclass has exactly one field afterwards. Consumers keep a version answer;
  only the fingerprint goes.
- **D2 — Engine machinery deleted outright.** `_compute_replay_hash`,
  `_candidate_to_dict`, `_provenance_to_dict` are removed from
  `paxman/engine/orchestrator.py` (the last two exist solely for hash
  serialization). `import hashlib` and `import json` go with them if nothing
  else uses them. `_build_version_stamp` simplifies to a `VersionStamp`
  carrying only `paxman_version` (keep the helper or inline it — your call).
- **D3 — Baseline suite deleted.** `tests/integration/test_default_replay_hashes.py`
  is removed. No per-capability hash baselines are added anywhere else.
- **D4 — `as_dict()` / `_extra_dict_fields()` removed entirely.** From the
  `Contract` protocol, from `CapabilityContract` (base method + extension
  hook + docstrings), and from all nine capability contract modules. Any
  `Any` import left unused by the removal is dropped (ruff F401 will name it).
- **D5 — Layered contract reaffirmed unchanged.** Recognition emits multiple
  RecognizedReps and never computes status; validation produces candidates
  and never computes ambiguity; the result layer deduplicates candidates into
  SUCCESS / AMBIGUOUS / INVALID; MISSING arises only from recognition with no
  validation run. No status semantics move.
- **D6 — Regression coverage reinvested (condition of acceptance).** Every
  pipeline/property test that previously asserted `replay_hash` equality or
  `len(...) == 64` must instead assert, for its locked rows: the candidate
  multiset (count + canonical values) and the set of provenance authorities.
  The SI Unit plan's e2e-table convention (validating authority named per
  row) becomes an enforced assertion here.
- **D7 — Docs sweep is part of the change.** ARCHITECTURE.md, AGENTS.md
  (root, core, capabilities, tests), CONTEXT.md, SECURITY.md,
  CONTRIBUTING.md, TESTING_STRATEGY.md, HOW_TO_ADD_NEW_CAPABILITY.md, and
  `capability_homogeneity_audit.md` are swept of replay-hash references.
  `docs/superpowers/plans/*`, `docs/report/*`, `docs/research/*`,
  `docs/adr/0001`, `docs/adr/0002`, and README.md are **excluded** (historical
  records / intentional references / no references). The nested AGENTS.md
  `as_dict()`/`_extra_dict_fields()` conventions are rewritten, not just
  stripped of "replay_hash" wording.

### Out of scope

- No behavior change to recognition/validation/status semantics (D5).
- No edits to historical capability plans, including the SI Unit plan's
  Task 11 (its replay-hash step is already marked dropped by ADR-0002
  References; do not touch that file).
- No changes to `paxman/core/__init__.py` re-exports (`VersionStamp` stays
  re-exported).

---

## §2 Tasks

### Task 1 — `refactor(core): remove replay_hash from VersionStamp`

**Step 1 RED — `tests/unit/test_version_stamp.py`**
- Rewrite every `VersionStamp(...)` construction (lines ~13, 19-20, 25-26,
  31) to `VersionStamp(paxman_version="0.1.0")` — no `replay_hash` argument.
- Add a test asserting the dataclass surface is exactly `("paxman_version",)`
  (e.g. via `dataclasses.fields`) and that `replay_hash` is gone
  (`assert not hasattr(vs, "replay_hash")`).
- Run: `uv run pytest tests/unit/test_version_stamp.py -q` → RED (field still
  exists).

**Step 2 GREEN — `paxman/core/domain.py`**
- `VersionStamp` (lines 177-182): delete the `replay_hash: str` field; update
  the docstring from "Replay integrity metadata." to "Version metadata."
  (or similar — no "replay" wording).

**Verify**
```bash
uv run pytest tests/unit/test_version_stamp.py -q
uv run ruff check paxman/core/domain.py tests/unit/test_version_stamp.py
```

**Commit**
```
refactor(core): remove replay_hash from VersionStamp
```

---

### Task 2 — `refactor(engine): drop replay-hash computation`

**Step 1 RED**
- No new test — the RED state is the broken construction in
  `paxman/engine/orchestrator.py:342-343` (`VersionStamp(..., replay_hash=...)`
  no longer exists). Confirm with:
  `uv run pyright paxman/engine/orchestrator.py` → error.

**Step 2 GREEN — `paxman/engine/orchestrator.py`**
- Delete `_provenance_to_dict` (346-356), `_candidate_to_dict` (359-369), and
  `_compute_replay_hash` (372-389) — the last two exist solely for hash
  serialization.
- Simplify `_build_version_stamp` (335-343) to return
  `VersionStamp(paxman_version=PAXMAN_VERSION)` (drop the now-unused `text`,
  `candidates`, `contract`, `status` parameters, or inline the helper — update
  the call site in `run_capability` accordingly).
- Delete `import hashlib` and `import json` (lines 5-6) if nothing else uses
  them. Keep `Any` (still used by `_filter_rules`/`_collect_candidates`).
- Update the `_collect_candidates` docstring line 255: "so the replay hash is
  stable regardless of routing" → state the real invariant ("so the candidate
  multiset is stable regardless of routing" / dedup rationale without replay
  wording).

**Verify**
```bash
uv run ruff check paxman/engine/orchestrator.py
uv run pyright paxman/engine/orchestrator.py
```

**Commit**
```
refactor(engine): drop replay-hash computation
```

---

### Task 3 — `test: remove replay-hash baseline suite`

**Step 1 GREEN (deletion — no RED step)**
- `git rm tests/integration/test_default_replay_hashes.py`. Do not recreate
  any hash-baseline table anywhere.

**Verify**
```bash
test ! -f tests/integration/test_default_replay_hashes.py
git status --short tests/integration/test_default_replay_hashes.py   # deleted
```

**Commit**
```
test: remove replay-hash baseline suite
```

---

### Task 4 — `test(integration): replace replay determinism with canonical determinism`

**Step 1 RED**
- In each file below, replace every `replay_hash` assertion (`==` between
  results, `len(...) == 64`) with a determinism + candidate-multiset +
  provenance assertion on the SAME locked rows:

| File | Anchor lines |
|------|--------------|
| `tests/integration/test_pipeline.py` | 97, 108, 580 (+ comment at 511-512 referencing `test_default_replay_hashes.py` — rewrite it) |
| `tests/integration/test_phone_pipeline.py` | 250-251 |
| `tests/integration/test_money_pipeline.py` | 239-240 |
| `tests/integration/test_country_pipeline.py` | 357, 361, 367 |
| `tests/integration/test_url_pipeline.py` | 118-119 |
| `tests/integration/test_format_value_seam.py` | module docstring line 4 ("...status, and replay hashing." — drop "replay hashing") |

- The replacement pattern (D6), for each locked row:
  - Determinism: `result1.canonicalized_value == result2.canonicalized_value`
    and `result1.status == result2.status` (and, where meaningful,
    `[c.value for c in result1.candidates] == [c.value for c in result2.candidates]`).
  - Candidate multiset: `len(result.candidates) == N` and the set of
    canonical values, e.g. `{c.value for c in result.candidates} == {...}`.
  - Provenance authorities: `{p.authority for c in result.candidates for p in c.provenance} == {...}`.
  - `version_stamp` sanity: `isinstance(result.version_stamp.paxman_version, str)`.
- Run the touched files → RED only where the old assertion shape was removed
  and the new assertions are not yet satisfied (a few may already pass —
  fine, the point is the new coverage exists).

**Step 2 GREEN**
- No source change required (determinism is by construction, D5) — GREEN is
  the assertions passing. If any new assertion fails, that is a REAL
  regression: investigate before proceeding.

**Verify**
```bash
uv run pytest tests/integration -q
```

**Commit**
```
test(integration): replace replay determinism with canonical determinism
```

---

### Task 5 — `refactor(core): remove as_dict from Contract protocol`

**Step 1 RED — `tests/unit/test_contract.py`**
- Delete the `as_dict` method from `_FullyCompliantContract` (40-48),
  `_MissingCapabilityName` (102-103), and `_NoneYear` (169-170).
- Delete `test_missing_as_dict_fails_isinstance` (112-113) and
  `test_as_dict_returns_correct_keys` (128-138).
- Add the inverse invariant: a class with all six properties and NO `as_dict`
  satisfies the protocol (`isinstance(..., Contract)` is True). Reuse
  `_MissingAsDict` (rename to `_NoAsDict` / reuse as the positive case) or
  add a small new fake.
- Run: `uv run pytest tests/unit/test_contract.py -q` → RED while `as_dict`
  is still in the protocol.

**Step 2 GREEN — `paxman/core/contract.py`**
- Delete the `as_dict` member from the `Contract` protocol (49-51).
- Drop `Any` from the `typing` import (line 4) if nothing else uses it (ruff
  F401 will confirm).

**Verify**
```bash
uv run pytest tests/unit/test_contract.py -q
uv run ruff check paxman/core/contract.py tests/unit/test_contract.py
uv run pyright paxman/core/contract.py
```

**Commit**
```
refactor(core): remove as_dict from Contract protocol
```

---

### Task 6 — `refactor(core): remove as_dict/_extra_dict_fields from CapabilityContract`

**Step 1 RED**
- `tests/unit/test_capability_contract.py`:
  - Delete `_ExtraDictContract` (43-47), `test_as_dict_emits_standard_keys`
    (118-127), `test_as_dict_standard_values` (130-138),
    `test_as_dict_appends_extra_dict_fields` (141-152).
  - Add a test asserting `not hasattr(_TestContract(), "as_dict")` (the base
    class no longer exposes the method).
- `tests/unit/test_capability_surface.py`:
  - Delete docstring items 15-16 (the `as_dict()` key-set and
    `_extra_dict_fields` collision items) and the `_STANDARD_KEYS` definition
    if nothing else uses it.
  - Delete `test_as_dict_replay_shape` (234-242) and
    `test_extra_dict_fields_do_not_collide_with_standard_keys` (249-257).
  - Keep every non-as_dict surface test intact.
- Run both files → RED.

**Step 2 GREEN — `paxman/core/capability_contract.py`**
- Delete `as_dict()` (90-104) and `_extra_dict_fields()` (106-113).
- Rewrite the module docstring (lines 1-9) and class docstring (21-44): drop
  "replay-deterministic keys", the `_extra_dict_fields()` bullet and the
  "Override `_extra_dict_fields()`" requirement — the unanimous surface is
  now the standard fields + `output_format` resolution + `active_grammars`.
- Drop `Any` from the `typing` import (line 16) if unused afterwards (ruff
  F401).

**Verify**
```bash
uv run pytest tests/unit/test_capability_contract.py tests/unit/test_capability_surface.py -q
uv run ruff check paxman/core/capability_contract.py tests/unit/test_capability_contract.py tests/unit/test_capability_surface.py
uv run pyright paxman/core/capability_contract.py
```

**Commit**
```
refactor(core): remove as_dict from CapabilityContract
```

---

### Task 7 — `refactor(capabilities): remove _extra_dict_fields overrides`

**Step 1 RED**
- No new test needed — the RED state is the orphaned overrides once the base
  hook is gone (pyright flags them). Confirm:
  `uv run pyright paxman/capabilities/` → errors on the overrides.

**Step 2 GREEN — delete `_extra_dict_fields` from all nine contract modules**

| Capability | File | Override line |
|------------|------|---------------|
| URL | `paxman/capabilities/URL/contract.py` | 35 (+ docstring mentions at 18, 36) |
| IP | `paxman/capabilities/IP/contract.py` | 28 |
| Country | `paxman/capabilities/Country/contract.py` | 52 (+ docstring mention at 53) |
| Currency | `paxman/capabilities/Currency/contract.py` | 97 (+ docstring at 98) |
| Email | `paxman/capabilities/Email/contract.py` | 31 |
| ISBN | `paxman/capabilities/ISBN/contract.py` | 48 (+ docstring at 49) |
| Date | `paxman/capabilities/Date/contract.py` | 35 |
| Phone | `paxman/capabilities/Phone/contract.py` | 111 |
| Money | `paxman/capabilities/Money/contract.py` | 111 (+ docstring at 112) |

- Also remove any docstring text in these files that says the method exists
  "for replay hash" / "for the replay-hash surface".
- If a contract's `typing` import (`object`/`Any`) becomes unused after the
  override removal, drop it (ruff F401 will name it).

**Verify**
```bash
uv run ruff check paxman/capabilities/
uv run pyright paxman/capabilities/
```

**Commit**
```
refactor(capabilities): remove _extra_dict_fields overrides
```

---

### Task 8 — `test(capabilities): drop as_dict surface tests`

**Step 1 GREEN (deletion — no RED step)**

Remove every `as_dict` test / fixture from the capability suites:

| File | Anchor |
|------|--------|
| `tests/capabilities/isbn/test_contract.py` | `test_as_dict_includes_features` (54-56) |
| `tests/capabilities/money/test_contract.py` | as_dict tests |
| `tests/capabilities/phone/test_capability.py` | as_dict tests |
| `tests/capabilities/currency/test_contract.py` | `test_as_dict_replay_keys` (58-59) |
| `tests/capabilities/date/test_capability.py` | as_dict tests |
| `tests/capabilities/ip/test_capability.py` | as_dict tests |
| `tests/capabilities/country/test_capability.py` | `test_as_dict_contains_all_fields` (109-112), `test_as_dict_contains_output_format` (183-186), `test_as_dict_default_output_format` (190-193) |
| `tests/capabilities/url/test_contract.py` | as_dict tests (+ comment at 76 mentioning the replay-hash surface — drop it) |
| `tests/capabilities/url/test_rule.py` | as_dict in a fake (line 37) |

If removing a test leaves imports unused (e.g. `Any`), drop them (ruff F401).

**Verify**
```bash
uv run pytest tests/capabilities -q
uv run ruff check tests/capabilities/
```

**Commit**
```
test(capabilities): drop as_dict surface tests
```

---

### Task 9 — `test: remove as_dict from test doubles`

**Step 1 GREEN (deletion — no RED step)**

Remove the `as_dict` method from every fake contract in non-capability
suites (the protocol no longer requires it):

| File | Lines |
|------|-------|
| `tests/integration/test_feature_gating.py` | 114, 204 |
| `tests/integration/test_pipeline.py` | 245, 260, 434 |
| `tests/integration/test_recognition_seam.py` | 176 |
| `tests/integration/test_format_value_seam.py` | 142, 247 |
| `tests/e2e/test_canonicalize.py` | 96 |
| `tests/unit/test_recognized_rep.py` | 39 |

If a fake becomes otherwise empty or an import becomes unused, tidy it (ruff
F401/F811 will name issues).

**Verify**
```bash
uv run pytest tests/integration tests/e2e tests/unit/test_recognized_rep.py -q
uv run ruff check tests/integration/ tests/e2e/ tests/unit/test_recognized_rep.py
```

**Commit**
```
test: remove as_dict from test doubles
```

---

### Task 10 — `test(property): replace money replay determinism`

**Step 1 RED — `tests/property/test_money_properties.py`**
- Line 57: replace the `replay_hash` equality assertion with
  canonical-determinism assertions on the same locked rows
  (`canonicalized_value` / `status` / candidate value set equal across
  runs).
- Line 91: replace `len(result.version_stamp.replay_hash) == 64` with a
  `paxman_version` sanity assertion plus, where the row is SUCCESS, the
  candidate-multiset + provenance-authority assertions (D6).
- Run: `uv run pytest tests/property -q` → RED where assertions are reshaped.

**Step 2 GREEN**
- No source change expected (determinism by construction, D5). Any failing
  new assertion is a real regression — investigate.

**Verify**
```bash
uv run pytest tests/property -q
```

**Commit**
```
test(property): replace money replay determinism
```

---

### Task 11 — `test: lock status computation to _determine_status`

**Step 1 RED — new test file `tests/unit/test_status_computation_invariant.py`**
- ADR Decision #5: add an invariant test proving **status is computed only in
  `_determine_status`** in `paxman/engine/orchestrator.py`.
- Follow the project's source-scan test precedent (like
  `tests/unit/test_rule_output_format_purity.py` / `test_grammar_semantic_purity.py`):
  AST-scan `orchestrator.py`, find every `Resolution.` member access, and
  assert each occurrence lives inside `_determine_status` (or
  `_extract_canonical_value`, which only READS status) — i.e. no other
  function constructs or assigns a `Resolution`. A behavioral companion
  assertion is also fine (e.g. `_recognize` returns no status-bearing type),
  but the AST scan is the lock.
- Mark with the `unit` marker.
- Run: `uv run pytest tests/unit/test_status_computation_invariant.py -q` →
  RED (the scan finds violations or the test is not yet written).

**Step 2 GREEN**
- The invariant must hold on the current code (D5 says the layered contract
  is already correct). If the scan finds a genuine violation, that is a real
  architectural drift — STOP and flag it rather than weakening the test.

**Verify**
```bash
uv run pytest tests/unit/test_status_computation_invariant.py -q
uv run pytest tests/unit -q
```

**Commit**
```
test: lock status computation to _determine_status
```

---

### Task 12 — `docs: sweep replay-hash references`

**Step 1 GREEN (docs edits — no RED step)**

Rewrite these files, removing ALL replay-hash references (and, per D7, the
`as_dict()` / `_extra_dict_fields()` conventions):

| File | Known references |
|------|------------------|
| `AGENTS.md` (root) | ANTI-PATTERNS "Never modify baseline replay-hash literals to green test_default_replay_hashes.py — fix the regression." → delete the bullet (and the "Never guess/infer..." line stays); check COMMANDS/STRUCTURE for stray mentions |
| `paxman/core/AGENTS.md` | line 27 (`_extra_dict_fields()` — "never hand-write `as_dict()` (it feeds `replay_hash`)" → rewrite the Contracts convention to drop as_dict entirely), line 38 (ANTI-PATTERNS "No hand-written `as_dict()` ... always `_extra_dict_fields()`" → delete) |
| `paxman/capabilities/AGENTS.md` | line 41 (contract convention mentions `_extra_dict_fields()` → rewrite), line 54 ("Never modify baseline replay-hash literals..." → delete), line 58 (quality-gate mention of replay-hash tests → delete) |
| `tests/AGENTS.md` | line 12 (integration dir description "...replay hashes..." → drop), line 30 (table row "Baseline replay hashes (do not edit literals)" → delete) |
| `ARCHITECTURE.md` | every replay-hash reference (ADR-0001 step 8 / decision #6 text) → rewrite to describe determinism-by-construction and the layered contract; check the e2e-table convention for authority columns stays |
| `CONTEXT.md` | domain-glossary mentions of replay hash → remove/adjust |
| `SECURITY.md` | any replay-hash mention → remove |
| `CONTRIBUTING.md` | any replay-hash mention → remove |
| `TESTING_STRATEGY.md` | baseline-suite and replay-determinism sections → rewrite to candidate-multiset/provenance coverage |
| `HOW_TO_ADD_NEW_CAPABILITY.md` | any replay-hash / `as_dict` / `_extra_dict_fields` guidance → remove or rewrite; check the e2e-table authority-column guidance is preserved (it becomes the D6 enforcement pattern) |
| `capability_homogeneity_audit.md` | (repo root) any replay-hash / as_dict references → remove/adjust |

Do NOT touch: `docs/superpowers/plans/*`, `docs/report/*`, `docs/research/*`,
`docs/adr/0001`, `docs/adr/0002`, `README.md`.

**Verify** (zero hits outside the excluded paths)
```bash
grep -rn "replay_hash\|replay-hash\|replay hash\|Replay Hash\|_extra_dict_fields" \
  --include="*.md" --include="*.py" \
  --exclude-dir=plans --exclude-dir=report --exclude-dir=research \
  --exclude="0001-clean-architecture-pipeline.md" \
  --exclude="0002-remove-replay-hash.md" \
  . | grep -v "docs/adr/" || echo "CLEAN"
```

**Commit**
```
docs: sweep replay-hash references
```

---

### Task 13 — Final gate (no commit)

**Verify — full pre-PR gate** (authoritative per `.github/workflows/ci.yml`):
```bash
uv run ruff check . && uv run ruff format --check . && uv run pyright && \
  uv run import-linter lint && uv run pytest
```
Coverage gate (one include pattern per package — the brace shorthand
`paxman/{core,capabilities,engine,api}/*` is not expanded by the installed
coverage version and reports "No data to report"):
```bash
uv run coverage report --include="paxman/core/*" --fail-under=95
uv run coverage report --include="paxman/capabilities/*" --fail-under=95
uv run coverage report --include="paxman/engine/*" --fail-under=95
uv run coverage report --include="paxman/api/*" --fail-under=95
```
Zero-grep proof (same command as Task 12 Verify) returns CLEAN.

If any gate fails, fix it in a follow-up commit — never by weakening a test,
never by restoring replay-hash code, and never by editing the excluded
historical docs.

---

## §3 Traps

1. **Ordering is load-bearing.** Task 2 must precede Task 5 (orchestrator is
   the only non-test caller of `contract.as_dict()`, inside
   `_compute_replay_hash`). Task 1 must precede Task 2 (orchestrator
   constructs `VersionStamp(replay_hash=...)`). Do not reorder.
2. **`Any` orphan imports.** `contract.py` (`Any` used only by `as_dict`),
   `capability_contract.py` (`Any` used only by `as_dict`/`_extra_dict_fields`),
   and possibly several capability contracts lose their last `Any`/`object`
   usage — let ruff F401 name them, drop them.
3. **`test_pipeline.py` comment at 511-512** references
   `test_default_replay_hashes.py` — Task 3 deletes that file, so the comment
   must be rewritten in Task 4 (same file).
4. **D6 is the condition of acceptance.** Deleting replay-hash assertions
   WITHOUT adding candidate-multiset/provenance assertions is a silent
   coverage regression. Every `replay_hash` assertion removed in Tasks 4 and
   10 must be replaced in the same edit.
5. **`test_capability_surface.py` `_STANDARD_KEYS`** — only delete it if
   nothing else in the file uses it; check first.
6. **Fakes with `as_dict` only.** If removing `as_dict` leaves a fake with no
   methods, keep the class (protocol fakes are still referenced) but drop the
   now-dead method.
7. **Never touch the excluded paths** (D7). Historical plans, reports,
   research, and ADR-0001/0002 keep their references — they are records of
   what was decided, and ADR-0002 itself documents the removal.
8. **`Resolution` uses outside `_determine_status`.** Task 11's scan may flag
   `Resolution.SUCCESS` inside `_extract_canonical_value` — that function
   only READS status; allowlist it explicitly in the test with a comment.
9. **No test weakening.** If a reinvested assertion fails after the engine
   cleanup, it signals a genuine drift — investigate, don't relax.

---

## §4 Definition of Done

- [ ] `VersionStamp` has exactly one field (`paxman_version`); no
      `replay_hash` anywhere in `paxman/`.
- [ ] No `as_dict`, `_extra_dict_fields`, `_compute_replay_hash`,
      `_candidate_to_dict`, or `_provenance_to_dict` anywhere in `paxman/` or
      `tests/`.
- [ ] `tests/integration/test_default_replay_hashes.py` deleted.
- [ ] Every former replay-hash assertion replaced with
      candidate-multiset + provenance-authority assertions (D6).
- [ ] `tests/unit/test_status_computation_invariant.py` locks status
      computation to `_determine_status`.
- [ ] Zero-grep proof clean outside the excluded paths (Task 12 Verify).
- [ ] Full pre-PR gate green: `ruff check . && ruff format --check . &&
      pyright && import-linter lint && pytest` and 95% coverage.
