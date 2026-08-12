# Plan: F1 — Grammar→Rule Affinity via `Rule.target_grammars`

- **Status:** Implemented (verified: `pyright` 0 errors, `ruff` clean, `import-linter` kept, `pytest` 782 passed; NOT committed)
- **Branch context:** build on a dedicated feature branch (e.g. `feat/f1-grammar-rule-affinity`),
  branched from current `main`. Depends only on the already-committed contract-surface
  homogeneity (`CapabilityContract`, `resolve_output_format`) — no other in-flight work.
- **Goal of this plan:** replace the orchestrator's cartesian product of
  (every recognition × every rule) with declared grammar→rule affinity, satisfying
  `ARCHITECTURE.md:201` ("Each grammar's notation flows to its corresponding validation
  rule") without changing any capability's observable behavior.

---

## 1. Goal & non-goals

**Goal:** every `Rule` subclass declares the set of grammars whose notations it is
allowed to validate (`target_grammars`). The engine skips rules that do not apply to a
notation *before* calling `matches()`, so routing is explicit and capability-agnostic.

**In scope:**
- `Rule.__init_subclass__` enforces `target_grammars` at class-definition time.
- Orchestrator affinity filter + identical-tuple candidate dedup (replay-safety).
- Engine invariant: every declared grammar name must exist in the capability.
- Annotate all 18 production `Rule` subclasses with their true acceptance domain.
- TDD tests proving ambiguity is preserved and replay hashes are stable.

> **Note — replay-hash removed; do not use as a sample.** The `replay_hash` (replay-hash / byte-identical canonicalization) mechanism referenced in the paragraph above was **removed** from Paxman (see `docs/adr/0002-remove-replay-hash.md`). The text above reflects the pre-removal design and MUST NOT be copied, adapted, or used as a template for future work.

**Non-goals (explicitly out of scope — separate findings in the audit):**
- **F2** `include_*` feature gating (grammar-gate vs rule-gate unification).
- **F3** grammar-time canonicalization / single-source authority tables.
- **F4** `output_format` consumption hook (`format_value`). `output_format` is left
  exactly as it behaves today; this plan only relies on the already-true fact that
  `Resolution` is computed from canonical values *before* any formatting (see the
  presentational-only invariant just added to `HOW_TO_ADD_NEW_CAPABILITY.md`).

---

## 2. The unanimous rule (target state)

| Area | Single unanimous implementation |
|------|----------------------------------|
| Affinity declaration | Every `Rule` subclass defines `target_grammars: ClassVar[frozenset[str]]` — the set of `Grammar.name` strings whose notations this rule may validate. Declared next to `name`/`strategy`/`provenance`/`citation`. |
| Enforcement | `Rule.__init_subclass__` requires `target_grammars` to be present, a non-empty iterable of `str`. Missing / empty / non-str → `TypeError` at import. |
| Routing | Engine compares `recognition.grammar.grammar_name` against `rule.target_grammars`; if absent, the rule is skipped for that recognition. One line in `_collect_candidates`. |
| Replay-safety | `_collect_candidates` dedups identical `(value, recognition_rule, validation_rule)` tuples so the candidate multiset is stable under over-declaration. |
| Name integrity | Engine validates every `target_grammars` entry exists in `capability.get_grammars()` names; dangling name → `ContractError`. |
| Capability-agnosticism | Engine reads only declared string names; it never inspects notation `shape` or fields. |

**Key property:** `target_grammars` is a *routing* hint, not a *validation* replacement.
Each rule keeps its existing value-level `matches()`/`normalize()` logic as defense-in-depth.
The declared set must equal the rule's *effective* acceptance domain (derived from the
audit's cross-capability map), so behavior and the replay hash are byte-identical.

> **Note — replay-hash removed; do not use as a sample.** The `replay_hash` (replay-hash / byte-identical canonicalization) mechanism referenced in the paragraph above was **removed** from Paxman (see `docs/adr/0002-remove-replay-hash.md`). The text above reflects the pre-removal design and MUST NOT be copied, adapted, or used as a template for future work.

---

## 3. Findings recap (audit F1 → target)

- **F1 (DEFECT):** `orchestrator.py:131-132` runs an unchecked cartesian product. No
  grammar→rule affinity exists; each capability invented its own self-filter
  (`shape` guards, `ipaddress` parse failures, regex that can't match the wrong shape,
  positional convention). This contradicts `ARCHITECTURE.md:201`.
- **Target:** declare affinity on the rule (`target_grammars`), add the one-line
  orchestrator filter, keep the engine capability-agnostic. Replay-safe *if*
  `_collect_candidates` dedups identical tuples (audit's own condition).
- **Not a 1:1 simplification:** 6 of 18 rules are genuinely multi-grammar (see map).
  The natural form is `frozenset[str]`, not a single grammar name.

---

## 4. Ground-truth `target_grammars` map (the exact annotations)

Derived from the audit's per-capability affinity map (effective acceptance domain of each
rule today). **This is the contract the implementation must satisfy — do not simplify to
1:1 or ambiguity will be silently lost.**

### Email (grammars: `standard_recognition`, `obfuscated_recognition`, `localhost_recognition`)
| Rule class (file) | `target_grammars` |
|---|---|
| `Section341AddrSpec` (`Email/rules/rfc_5322_ed2008.py`) | `{standard_recognition, obfuscated_recognition}` |
| `Section63localhost` (`Email/rules/rfc_6761_ed2012.py`) | `{localhost_recognition}` |

### Date (grammars: `iso8601_recognition`, `us_recognition`, `european_recognition`)
| Rule class (file) | `target_grammars` |
|---|---|
| `Section431CalendarDate` (`Date/rules/iso_8601_ed2019.py`) | `{iso8601_recognition}` |
| `Section1DateFormat` (`Date/rules/us_federal_rules_ed2023.py`) | `{us_recognition, european_recognition}` |
| `Section4DateFormat` (`Date/rules/en_50160_ed2010.py`) | `{us_recognition, european_recognition}` |

> Both US and EU rules declare **both** slash grammars. Their mutual cross-acceptance is
> what produces `AMBIGUOUS` for `01/02/2026`. A naive 1:1 mapping would delete ambiguity.

### Country (grammars: `alpha2_recognition`, `alpha3_recognition`, `numeric_recognition`, `name_recognition`)
| Rule class (file) | `target_grammars` |
|---|---|
| `SectionAlpha2Codes` (`Country/rules/iso_3166_ed2024.py`) | `{alpha2_recognition}` |
| `SectionAlpha3Codes` (`Country/rules/iso_3166_ed2024.py`) | `{alpha3_recognition}` |
| `SectionNumericCodes` (`Country/rules/iso_3166_ed2024.py`) | `{numeric_recognition}` |
| `SectionNames` (`Country/rules/iso_3166_ed2024.py`) | `{name_recognition}` |
| `SectionLocalizedNames` (`Country/rules/cldr_localized_ed2025.py`) | `{name_recognition}` |
| `SectionHistoricalNames` (`Country/rules/iso_3166_historical_ed2020.py`) | `{name_recognition, alpha2_recognition, numeric_recognition}` |

### IP (grammars: `ipv4_recognition`, `ipv6_recognition`)
| Rule class (file) | `target_grammars` |
|---|---|
| `Section3Dot2IPv4Address` (`IP/rules/rfc_791_ed1981.py`) | `{ipv4_recognition}` |
| `Section4IPv6TextRepresentation` (`IP/rules/rfc_5952_ed2010.py`) | `{ipv6_recognition}` |

### Phone (grammars: `e164_recognition`, `international_00_recognition`, `tel_uri_recognition`, `national_recognition`)
| Rule class (file) | `target_grammars` |
|---|---|
| `Section6_1InternationalNumber` (`Phone/rules/e164_ed2010.py`) | `{e164_recognition, international_00_recognition}` |
| `Section6_2CountryCode` (`Phone/rules/e164_ed2010.py`) | `{e164_recognition, international_00_recognition}` |
| `Section3TelUri` (`Phone/rules/rfc_3966_ed2004.py`) | `{tel_uri_recognition}` |
| `Section1_1NANPStructure` (`Phone/rules/nanp_ed2024.py`) | `{national_recognition}` |
| `Section1_2ServiceNPA` (`Phone/rules/nanp_ed2024.py`) | `{national_recognition}` |

---

## 5. Implementation steps (ordered)

### Step 1 — `Rule.target_grammars` enforcement (`paxman/core/domain.py`)
**Files:** `paxman/core/domain.py` (`Rule` base, lines 131-156).

- Extend the required-metadata tuple in `Rule.__init_subclass__` (currently
  `("name", "strategy", "provenance", "citation")` at line 144) to include
  `"target_grammars"`.
- After the presence check, validate it: must be a non-empty iterable; every element
  must be a `str`. On violation raise `TypeError` with a message naming the offending
  subclass and the exact problem (missing / empty / non-str element).
- Add `target_grammars: ClassVar[frozenset[str]]` as a no-value annotation on the base
  `Rule` (mirrors how `name`/`strategy`/`provenance`/`citation` are declared), so the
  type checker sees the attribute. Subclasses assign the concrete `frozenset`.
- **Why first:** every subsequent step and every rule annotation depends on this
  contract existing; making it mandatory now surfaces any unannotated `Rule` subclass at
  import (including test stubs — see Step 4).

### Step 2 — Orchestrator affinity filter + dedup (`paxman/engine/orchestrator.py`)
**Files:** `paxman/engine/orchestrator.py` (`_collect_candidates` lines 126-152;
`run_capability` lines 49-70).

- In `_collect_candidates`, before `rule.matches(...)` (before line 134), add:
  ```python
  if recognition.grammar.grammar_name not in rule.target_grammars:
      continue
  ```
- After the collection loop, dedup identical candidate tuples. Because provenance is
  deterministic per `(rule, grammar)` pair, collapse on
  `(value, recognition_rule, validation_rule)` keeping the first occurrence:
  ```python
  seen: set[tuple[str, str, str]] = set()
  deduped: list[Candidate] = []
  for c in candidates:
      key = (c.value, c.recognition_rule, c.validation_rule)
      if key not in seen:
          seen.add(key)
          deduped.append(c)
  return deduped
  ```
- **Why:** the filter realizes F1; dedup keeps the replay hash stable if any future
  author over-declares `target_grammars` (audit's replay-safety condition).

> **Note — replay-hash removed; do not use as a sample.** The `replay_hash` (replay-hash / byte-identical canonicalization) mechanism referenced in the paragraph above was **removed** from Paxman (see `docs/adr/0002-remove-replay-hash.md`). The text above reflects the pre-removal design and MUST NOT be copied, adapted, or used as a template for future work.

### Step 3 — Engine affinity invariant (`paxman/engine/orchestrator.py`)
**Files:** `paxman/engine/orchestrator.py` (new helper; call in `run_capability` after
`_filter_rules`, line 57).

- Add `_validate_affinity(capability, rules)` that builds the set of grammar names from
  `capability.get_grammars()` and, for each active rule, checks every entry in
  `rule.target_grammars` is present. On a dangling name raise `ContractError` with a
  message naming the rule and the missing grammar.
- Call it in `run_capability` between `_filter_rules` and `_collect_candidates`.
- **Why:** catches typos / grammar renames that would silently exclude a rule (the
  scalability risk called out in the F1 analysis). Cheap, runs once per pipeline call.

### Step 4 — Annotate the 18 production rules (parallel per capability)
**Files:** the 18 rule files in the map (§4).

- Add, immediately after the existing `citation = ...` line in each rule class:
  ```python
  target_grammars: ClassVar[frozenset[str]] = frozenset(
      {"standard_recognition", "obfuscated_recognition"}  # example — use the map value
  )
  ```
- Do **not** alter `name`, `strategy`, `provenance`, `citation`, or any
  `matches()`/`normalize()` logic. The value-level discriminators remain as defense-in-depth.
- **Parallelize:** one agent per capability (Email, Date, Country, IP, Phone), each given
  the exact `target_grammars` frozenset from §4 for that capability's rule classes. Agents
  must read each rule file, confirm the class name, and insert the attribute; they must
  NOT change behavior. Each agent runs `uv run pyright paxman/capabilities/<Cap>` and
  `uv run ruff check paxman/capabilities/<Cap>` on its own files (not the full suite, to
  avoid cross-capability import failures mid-flight).
- **Test stubs are in scope too:** `tests/integration/test_pipeline.py` defines
  `StubRule` (line 119) and `ExplodingRule` (line 142), and
  `tests/unit/test_rule_metadata.py` defines `_BareRule` (66) / `_IncompleteRule` (80).
  These subclass `Rule` and would break import once Step 1 lands. Action:
  - Give `StubRule` and `ExplodingRule` a plausible `target_grammars`
    (e.g. `frozenset({"standard_recognition"})` — they use `EmailNotation`).
  - Keep `_BareRule` / `_IncompleteRule` as **negative** metadata-enforcement fixtures:
    they must continue to *omit* at least one required attribute so the existing
    `TypeError` assertions still hold. Add **new** negative fixtures
    (`_NoTargetGrammars`, `_EmptyTargetGrammars`, `_NonStrTargetGrammars`) that omit /
    empty / mis-type `target_grammars` so Step 1's validation is itself tested.
- **Why parallel:** the 18 edits are independent files; per-capability agents eliminate
  the bulk of mechanical work while the core (Steps 1-3) is done once.

### Step 5 — TDD tests (see §6)
Write tests first against the *current* behavior baseline where possible, then implement,
then confirm green.

---

## 6. Test plan (TDD red-green)

**A. Enforcement (unit — `tests/unit/test_rule_metadata.py`)**
1. `_NoTargetGrammars` (omits `target_grammars`) → import raises `TypeError`.
2. `_EmptyTargetGrammars` (`target_grammars = frozenset()`) → `TypeError`.
3. `_NonStrTargetGrammars` (`target_grammars = frozenset({1})`) → `TypeError`.
4. `StubRule` with valid `target_grammars` imports cleanly (regression guard).

**B. Ambiguity preserved (integration — `tests/integration/test_pipeline.py`)**
5. Date `01/02/2026` with `output_format` ∈ {unset, `"ISO"`, `"US"`, `"EU"`}:
   - `status == Resolution.AMBIGUOUS`
   - distinct `candidate.value` set == `{"2026-01-02", "2026-02-01"}`
   - candidate count == 4 (two rules × two slash grammars)
   This proves the presentational-only invariant: status is independent of `output_format`.
6. Date `12/12/2026` → `SUCCESS` (both interpretations agree) — confirms F1 does not
   *create* false ambiguity.

**C. Behavior parity / replay stability (integration + property)**
7. **Hash snapshot:** on the *base* branch first, capture
   `result.version_stamp.replay_hash` for a matrix of representative inputs across all
   five capabilities (success / invalid / ambiguous / missing cases). Encode as expected
   constants. After implementation, assert equality. This is the audit's replay-safety
   gate made concrete. (If base-branch capture is impractical, assert the weaker
   invariant: for each representative input, post-change candidate `(value,
   recognition_rule, validation_rule)` multiset equals the multiset that *would* result
   from the cartesian product restricted to `grammar_name in rule.target_grammars` —
   encode as a hand-checked expectation per input.)
8. Property test: for random valid inputs, `status` is invariant under `output_format`
   changes (where the capability offers alternative formats).
9. `_validate_affinity` fires: a stub capability whose rule declares a non-existent
   grammar name → `run_capability` raises `ContractError`.

> **Note — replay-hash removed; do not use as a sample.** The `replay_hash` (replay-hash / byte-identical canonicalization) mechanism referenced in the paragraph above was **removed** from Paxman (see `docs/adr/0002-remove-replay-hash.md`). The text above reflects the pre-removal design and MUST NOT be copied, adapted, or used as a template for future work.

---

## 7. Verification (quality gates)

```bash
uv run pyright --strict paxman/ tests/   # zero errors; no # type: ignore / # noqa
uv run ruff check paxman/ tests/
uv run ruff format --check paxman/ tests/
uv run import-linter lint                # capability import boundaries intact
uv run pytest tests/ -v                  # all green, no skips without justification
```
All five capabilities must continue to pass their existing grammar/rule/capability/
integration/e2e suites unchanged in outcome.

---

## 8. Risks / watch-outs (carried from the F1 analysis)

1. **Replay-hash change** — avoided because `target_grammars` == each rule's *effective*
   acceptance domain, so candidate multiplicity is identical to today. The Step 2 dedup
   is defense-in-depth. Gate: Step 6.7 hash-snapshot test.
2. **Silent ambiguity loss** — the only way this regresses is a worker writing 1:1 for
   Date's US/EU rules. The §4 map explicitly requires both slash grammars; Step 6.5
   locks it with an `AMBIGUOUS` assertion.
3. **MISSING vs INVALID semantics** — unaffected. F1 only changes *which* rules see
   *which* notations; because the declared set equals the effective domain, every
   capability's status distribution is unchanged.
4. **Test-stub import breakage** — Step 1 makes `target_grammars` mandatory, so the
   `Rule` subclasses in tests (StubRule, ExplodingRule, the metadata fixtures) must be
   updated (Step 4). Forgotten stubs fail the whole suite at collection time — caught
   immediately by Step 7's `pytest`.
5. **Dangling grammar name** — handled by Step 3's `_validate_affinity`; also protects
   future capabilities from silent over/under-routing.
6. **`target_grammars` keyed on grammar *names*, not notation *shape*** — this is
   intentional (keeps the engine capability-agnostic). The cost is manual maintenance
   when a new grammar reuses an existing shape (the Phone `e164`/`international_00`
   pattern). Step 3's invariant plus the `HOW_TO` presentational-only section document
   the discipline; no runtime shape coupling is introduced.

> **Note — replay-hash removed; do not use as a sample.** The `replay_hash` (replay-hash / byte-identical canonicalization) mechanism referenced in the paragraph above was **removed** from Paxman (see `docs/adr/0002-remove-replay-hash.md`). The text above reflects the pre-removal design and MUST NOT be copied, adapted, or used as a template for future work.

---

## 9. Out-of-scope follow-ups (do NOT bundle into this plan)

- **F2** `include_*` unification (grammar-gate vs rule-gate declared metadata).
- **F4** `format_value` engine hook (rules emit default canonical only).
- **F3** single-source authority tables / move recognition-time canonicalization into rules.
- Making `RuleStrategy` checked (separate audit Tier-3 item).
