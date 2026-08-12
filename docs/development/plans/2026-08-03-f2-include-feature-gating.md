# Plan: F2 — Unify `include_*` Feature Gating via `Rule.requires_features`

- **Status:** Draft (analysis → plan only; NOT implemented, NOT committed)
- **Branch context:** build on a branch that already contains F1 (`Rule.target_grammars` +
  the orchestrator affinity filter are prerequisites — F2 extends the same
  `Rule.__init_subclass__` metadata enforcement and `_filter_rules` machinery).
- **Goal of this plan:** remove the ad-hoc, per-rule `include_*` gating (the
  `cast(Contract, ...)`-then-`return False` pattern inside `matches()`) and replace it
  with one engine-enforced declaration pattern that scales to every capability.

---

## 1. Goal & non-goals

**Goal:** two feature *kinds* are gated through exactly one declared mechanism each,
enforced by the engine — never by casts inside `matches()`:

- **Input-shape features** (which formats the recognizer may produce) → toggle grammars
  via `active_grammars`. Disabled → `MISSING` (fails-fast, unchanged).
- **Authority features** (which authorities may validate a recognized value) → declared
  as `Rule.requires_features` metadata, checked by the engine in `_filter_rules`.
  Disabled → `INVALID` (recognized but no rule validates, unchanged).

**In scope:**
- `Rule.requires_features: ClassVar[frozenset[str]]` enforced by `__init_subclass__`.
- Engine filter in `_filter_rules` using `getattr(contract, feature, False)` — capability-agnostic.
- Remove the two Country cast-gates (`SectionHistoricalNames`, `SectionLocalizedNames`).
- Annotate the remaining 16 production rules and the test stubs with
  `requires_features = frozenset()` (unanimous surface).
- TDD tests proving the `MISSING`/`INVALID` split is preserved.

**Non-goals (out of scope — separate findings):**
- **F3** grammar-time canonicalization / single-source authority tables.
- **F4** `format_value` hook — note: the audit addendum (A) already established Date
  honors `output_format`; F4 needs re-scoping, not implementation as originally written.
- **F5** static-vs-toggleable `active_grammars` — already adjudicated ACCEPTED.
- The four `cast(CountryContract, ...)` calls in `iso_3166_ed2024.py` (lines 77/127/185/241)
  access `output_format`, not feature flags — they stay untouched.
- Making `RuleStrategy` checked (separate Tier-3 item).

---

## 2. The unanimous rule (target state)

| Area | Single unanimous implementation |
|------|----------------------------------|
| Feature declaration | Every `Rule` subclass declares `requires_features: ClassVar[frozenset[str]]` — the set of contract field names (e.g. `"include_historical"`) that must be truthy for the rule to run. Most rules declare `frozenset()`. |
| Enforcement | `Rule.__init_subclass__` requires `requires_features` (presence; empty allowed). Element-type is pyright-enforced via the annotation. |
| Engine check | The engine first validates that every declared feature exists on the contract; a dangling feature name raises `ContractError`. It then drops any rule where `getattr(contract, feature, False)` is falsy for any required feature — the **final** filter, after pinned/excluded/year. Capability-agnostic: no cast, no shape knowledge. |
| Rule code | `matches()` contains **no** `include_*` / feature gating and no `cast(Contract, ...)` for gating. Value validation only. |
| Input-shape features | Stay in `active_grammars` (Email `include_obfuscated`, `include_localhost`; IP `include_ipv6`). Disabled → `MISSING`. Unchanged. |
| Authority features | `Rule.requires_features` (Country `include_localized`, `include_historical`). Disabled → `INVALID`. Unchanged. |

**Key property:** the split is semantic, not cosmetic — grammar-gates produce `MISSING`,
authority-gates produce `INVALID`. F2 keeps that split by moving only the *authority*
locus to `requires_features`; it must NOT move input-shape features to rule-gating
(that would flip Email `MISSING`→`INVALID`, a documented regression).

---

## 3. Findings recap (audit F2 → target)

- **F2 (DEFECT, ad-hoc form):** Email `include_obfuscated=True` adds
  `obfuscated_recognition` to `active_grammars` (grammar-gate → `MISSING` when off);
  Country `include_localized`/`include_historical` are static `active_grammars`, gated
  *inside the rule* as `cast(CountryContract, contract); if not contract.include_X: return False`.
  The subclass cast silently narrows the `Contract` protocol inside `matches()` — latent-fragile
  (a rule receiving a non-Country contract would `AttributeError`).
- **Oracle's verdict:** one *single* mechanism is wrong — the two feature kinds are
  semantically distinct (`MISSING` vs `INVALID`). The defect is the ad-hoc, per-rule
  implementation, not the existence of two loci.
- **Target:** one declaration pattern with engine enforcement for both loci — input-shape
  → `active_grammars`; authority → `Rule.requires_features` checked in `_filter_rules`.
  Never via casts in `matches()`. Document in `HOW_TO_ADD_NEW_CAPABILITY.md`.

---

## 4. Ground-truth feature map (the exact annotations)

### Authority features → `Rule.requires_features` (only these two)
| Rule class (file) | `requires_features` |
|---|---|
| `SectionHistoricalNames` (`Country/rules/iso_3166_historical_ed2020.py`) | `frozenset({"include_historical"})` |
| `SectionLocalizedNames` (`Country/rules/cldr_localized_ed2025.py`) | `frozenset({"include_localized"})` |

### Input-shape features → stay as `active_grammars` (NO rule metadata; unchanged)
| Capability | Flag | Grammar toggled | Off ⇒ status |
|---|---|---|---|
| Email | `include_obfuscated` (default False) | `obfuscated_recognition` | `MISSING` |
| Email | `include_localhost` (default True) | `localhost_recognition` | `MISSING` |
| IP | `include_ipv6` (default True) | `ipv6_recognition` | `MISSING` |

### All other rules → `requires_features = frozenset()`
The remaining **16** production rules (Email 2, Date 3, Country 4 others, IP 2, Phone 5)
declare an empty frozenset — the unanimous surface.

### Test stubs (in scope, or import breaks once Step 1 lands)
- `tests/integration/test_pipeline.py`: `StubRule`, `ExplodingRule`, `_PhantomRule` → `frozenset()`.
- `tests/unit/test_capability.py`: `StubRule` → `frozenset()`.
- `tests/unit/test_rule_metadata.py`: `_EmptyTargetGrammars` → add `requires_features = frozenset()`
  (so its negative test still targets the *target_grammars non-empty* error, not a missing-attr error).
- Keep `_BareRule` / `_IncompleteRule` as negative fixtures (they omit required attrs).
- Extend `_RULE_METADATA_ATTRS` to `("name", "strategy", "provenance", "citation", "target_grammars", "requires_features")`.

---

## 5. Implementation steps (ordered)

### Step 1 — `Rule.requires_features` enforcement (`paxman/core/domain.py`)
- Add `requires_features: ClassVar[frozenset[str]]` to the base `Rule` annotations
  (next to `target_grammars`).
- Extend the required tuple in `__init_subclass__` to
  `("name", "strategy", "provenance", "citation", "target_grammars", "requires_features")`.
- **No non-empty check** (empty is the common, valid case) — unlike `target_grammars`.
  Type/element-type stay pyright-enforced.
- **Why first:** makes the attribute mandatory; unannotated subclasses (including test
  stubs) fail at import, surfacing every site that needs Step 4's empty annotation.

### Step 2 — Engine feature filter (`paxman/engine/orchestrator.py` `_filter_rules`)
- After pinning/exclusion and year filtering have produced `active_rules`, validate every
  declared feature name before the feature-enabled filter:
  ```python
  for rule in active_rules:
      missing = [
          feature for feature in rule.requires_features if not hasattr(contract, feature)
      ]
      if missing:
          raise ContractError(
              f"Rule {rule.name!r} requires missing contract feature(s): {sorted(missing)}"
          )
  ```
- Then append this as the **final** filter (after the year filter, before `return active_rules`):
  ```python
  active_rules = [
      r
      for r in active_rules
      if all(getattr(contract, feature, False) for feature in r.requires_features)
  ]
  ```
- `getattr(contract, feature, False)` is capability-agnostic for the value check. A
  missing feature name is **not** silently treated as false: it is malformed rule
  metadata or a malformed capability contract and must fail fast with `ContractError`,
  just as F1 fails fast on dangling grammar names.
- **Why last:** pinned/excluded/year selection happens first; a pinned rule whose feature
  is disabled still yields `INVALID` — identical to the current in-`matches()` gate.

### Step 3 — Remove the Country cast-gates
**`Country/rules/cldr_localized_ed2025.py`** (`SectionLocalizedNames`):
- Delete `country_contract = cast(CountryContract, contract)` and
  `if not country_contract.include_localized: return False` (lines 48-50).
- Remove now-unused imports: `from typing import cast` (line 5),
  `from paxman.capabilities.Country.contract import CountryContract` (line 7).
- Add `requires_features = frozenset({"include_localized"})` after `target_grammars`.
- Update the class/method docstrings to say the engine activates this rule only when
  `include_localized` is enabled; `matches()` itself validates notation/table membership.

**`Country/rules/iso_3166_historical_ed2020.py`** (`SectionHistoricalNames`):
- Delete the same pattern (lines 84-86) and the unused `cast`/`CountryContract` imports.
- Add `requires_features = frozenset({"include_historical"})`.
- The rest of `matches()` (shape dispatch against the former-name tables) is untouched.
- Update the class/method docstrings with the same engine-owned gating wording.
- Update `tests/capabilities/country/test_rules.py`: the existing
  `test_rejects_when_disabled` and `test_rejects_historical_numeric_when_disabled`
  assert the old in-`matches()` gate and must be replaced with notation-validation tests.
  Feature-off pipeline behavior is covered by §6.B; direct rule tests must no longer
  expect `matches()` to inspect `include_historical`.

### Step 4 — Annotate the remaining 16 production rules + test stubs
- Add `requires_features = frozenset()` after `target_grammars` in every other `Rule`
  subclass (per §4 map). Parallelize one agent per capability (Email, Date, Country,
  IP, Phone) exactly as F1, each running `uv run pyright paxman/capabilities/<Cap>` and
  `uv run ruff check paxman/capabilities/<Cap>` on its own files — NOT full pytest.
- Update the test stubs per §4.
- **Why parallel:** mechanical, independent files.

### Step 5 — Document the pattern in `HOW_TO_ADD_NEW_CAPABILITY.md`
Add to the "Rule metadata" subsection (Step 5 / unanimous surface):
- Document the existing `target_grammars` declaration alongside the new field; both are
  required class metadata and both are enforced by `Rule.__init_subclass__`.
- `requires_features` is a required `ClassVar[frozenset[str]]` of contract field names
  that must be truthy for the rule to run; engine-enforced in `_filter_rules`.
- Two-locus feature policy: input-shape features toggle grammars via `active_grammars`
  (disabled ⇒ `MISSING`); authority features are declared on the rule (disabled ⇒ `INVALID`).
- **Hard rule:** never gate inside `matches()` via `cast(Contract, ...)` — the engine
  owns feature routing.

---

## 6. Test plan (TDD red-green)

**A. Enforcement (unit — `tests/unit/test_rule_metadata.py`)**
1. Extend `_RULE_METADATA_ATTRS` with `"requires_features"` — the existing
   `test_missing_single_metadata_attribute_raises` parametrize then covers
   missing-`requires_features` automatically.
2. `_EmptyTargetGrammars` (already negative for empty `target_grammars`) gets
   `requires_features = frozenset()` so it still raises the `target_grammars` non-empty error.
- Update the two existing direct `SectionHistoricalNames.matches()` tests that assert
  feature-disabled rejection; after F2, rule tests validate notation semantics only and
  integration tests validate engine feature gating.

**B. Authority-gating behavior preserved (integration — Country)**
3. `include_historical=False`, input `"Burma"` → `INVALID` (recognized, historical rule excluded).
4. `include_historical=True`, input `"Burma"` → `SUCCESS`, `canonicalized_value == "BU"`
   (the historical rule returns the former entity's code `BU`, not successor code `MM`; this
   is locked by `tests/capabilities/country/test_rules.py:377-381`).
5. Do **not** use `"Deutschland"` as a public Country pipeline fixture: the current
   `NameGrammar` recognizes English, historical, and Chinese tables, not the Spanish /
   French / German CLDR keys. Current behavior is `MISSING` with either localized flag;
   making it `SUCCESS` belongs to F3's recognition/table remediation, not F2.
6. Add an engine-level localized-feature fixture instead: a grammar named
   `"name_recognition"` emits `CountryNotation(shape="name", value="Estados Unidos")`
   (a key in `LOCALIZED_TO_ALPHA2`), and `SectionLocalizedNames` is the only active rule.
   With `include_localized=False` the result is `INVALID`; with it enabled the result is
   `SUCCESS` with `canonicalized_value == "US"`. This tests the F2 engine gate without
   conflating it with F3's incomplete localized recognition.
7. Pinned rule + disabled feature: `pinned_rules=["Section-historical-names"]` with
   `include_historical=False`, input `"Burma"` → `INVALID` (feature filter applies after pinning).

**C. Grammar-gate `MISSING` semantics preserved (integration — Email/IP)**
8. Email `include_obfuscated=False`, input `"user at example dot com"` → `MISSING`;
   `include_obfuscated=True` → `SUCCESS`.
9. IP `include_ipv6=False`, input `"2001:db8::1"` → `MISSING`; `include_ipv6=True` → `SUCCESS`.

**D. Feature metadata integrity (unit/integration)**
10. A rule declaring a nonexistent feature (for example `"not_a_contract_field"`) must
    cause `ContractError` before candidate collection; feature-name typos must not silently
    turn a valid input into `INVALID`.
11. A real feature present on the contract but set to `False` must exclude the rule and
    preserve `INVALID`; a real feature set to `True` must allow the rule to run. The
    localized fixture in B covers both paths without relying on direct `matches()` calls.

---

## 7. Verification (quality gates)

```bash
uv run pyright            # 0 errors (strict via config; no # type: ignore / # noqa)
uv run ruff check paxman tests
uv run ruff format --check paxman tests
uv run import-linter lint
uv run pytest tests -q    # all green
```
All five capabilities' existing suites must pass unchanged in outcome.

---

## 8. Risks / watch-outs

1. **MISSING vs INVALID flip** — the only way F2 regresses is moving an input-shape
   feature (Email obfuscated/localhost, IP ipv6) to `requires_features`. §4 locks them
   as grammar-gates; Step 6.C asserts `MISSING` stays `MISSING`.
2. **Unused imports** — removing the Country gates leaves `cast` / `CountryContract`
   imports unused; Step 3 removes them explicitly (ruff would flag otherwise).
3. **Test-stub import breakage** — Step 1 makes `requires_features` mandatory; every
   `Rule` subclass in tests must declare it (Step 4), else collection fails immediately.
4. **`_EmptyTargetGrammars` ordering** — must keep `requires_features = frozenset()` so
   the missing-attr check passes first and the *empty target_grammars* error still fires
   (its assertion matches `"non-empty"`).
5. **Pinned-rule interaction** — `requires_features` is enforced *after* pinning; a pinned
   gated rule yields `INVALID` (matches today). Do not move the filter before pinning.
6. **Feature-name integrity** — a misspelled `requires_features` entry must not silently
   exclude a rule. Step 2 fails fast with `ContractError` when the contract lacks a
   declared feature; a present-but-false feature remains the intentional `INVALID` path.

---

## 9. Out-of-scope follow-ups (do NOT bundle)

- **F4** — re-scope first (audit Addendum A: Date already honors `output_format`).
- **F3** — single-source authority tables / raw-token grammars.
- **Tier-3 hygiene batch** (candidate for a later plan): freeze the 11 mutable authority
  dicts with `MappingProxyType` (#8/#10); drop the dead `"EQUatorial GUINEA"` key (#13);
  make `RuleStrategy` checked or drop it (#1-3); fix the `iso_3166_ed2024` `reference_url`
  (#12). These are low-risk, independent, and could be bundled into one "rule-layer
  hygiene" plan after F2.
