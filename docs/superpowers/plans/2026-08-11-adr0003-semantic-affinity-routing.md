# ADR-0003 Semantic Affinity Routing — Implementation Plan

| **Title** | Route rules by meaning, not grammar name |
| **Date** | 2026-08-11 |
| **Status** | In progress — Tasks 1-2 landed, Tasks 3-10 pending |
| **Branch** | `refactor/semantic-affinity-routing` (commit per task) |
| **Authoritative spec** | `docs/adr/0003-semantic-affinity-routing.md` — where this plan and the ADR disagree on design, the ADR wins; verified file inventories (D10) supersede the ADR's pre-migration snapshot |
| **Supersedes** | `Rule.target_grammars` grammar-name affinity (F1 fix, PR #19) — the routing key becomes `semantics` |

> **For agentic workers.** This plan is written to be executed by a worker
> agent one task at a time. Every task is TDD: **Step 1 RED** (write/adjust
> the failing test first), **Step 2 GREEN** (make it pass), then the scoped
> verify command and the commit. Do not skip steps, do not reorder tasks, do
> not "improve" the design — D-decisions are locked (§1). The full suite is
> only green after Task 4; the per-task verify commands are scoped so each
> task is independently green. Commit with the exact message given for each
> task. **Pure-mechanical tasks are exempt from a meaningful RED step** —
> Tasks 2, 4, and 9 say so explicitly and their instruction wins. Task 10 is
> a verify-only gate with **no commit**, so the exact-commit-message
> requirement does not apply to it.

> **Progress — COMPLETE.** All ten tasks landed.
>
> | Task | Status | Commit |
> |------|--------|--------|
> | Task 1 — declare `semantics` on all shipped grammars | ✅ landed | `ebf21bb` |
> | Task 2 — rename `target_grammars` → `target_semantics` | ✅ landed | `f8ac1f6` |
> | Task 3 — enforce `Grammar.semantics` at class-definition time | ✅ landed | `0ea7727` |
> | Task 4 — engine routes on semantics | ✅ landed | `0f0f9d1` |
> | Task 5 — Phase 2: Date coalescing | ✅ landed | `3c592b8` |
> | Task 6 — Phase 2: Email coalescing | ✅ landed | `9317596` |
> | Task 7 — Phase 2: Phone coalescing | ✅ landed | `abae3e4` (`fd22152` prep fix) |
> | Task 8 — consistency guard | ✅ landed | `36315dc` |
> | Task 9 — docs sweep | ✅ landed | `f6f7790` |
> | Task 10 — final gate (no commit) | ✅ green | follow-up `125c06d` |
>
> Execution notes for the follow-up session that ran Tasks 5-10:
>
> - Task 5 also updated `tests/unit/test_grammar_shipped_grammars_declare_semantics_identity`
>   (now `test_shipped_grammars_declare_semantics_identity`) via a module-level
>   `_COALESCED_SEMANTICS` allowlist, so every commit stayed green — approved
>   deviation; the allowlist mirrors D6 exactly and is itself locked by the
>   guard's enumeration-completeness test.
> - M1/M2 (orchestrator docstring KeyError invariant + drop the duplicate
>   sentence at ARCHITECTURE.md:201) and M3 (README fail-fast mechanism, from
>   Task 5 execution) were folded into Task 9. Task 5's RED driver 2 failed
>   with a silent-exclusion `assert False`, not the plan-predicted
>   `ContractError` — README's claim is accurate and now documented precisely.
> - Task 8's multi-member group count is scoped per capability (Currency and
>   Money share `code_recognition`/`symbol_recognition`/`word_recognition`
>   across capabilities; routing is per-capability, so groups are enumerated
>   per capability).
> - Task 10 gate: `ruff format --check .` flags 8 pre-existing historical
>   docs (`docs/research/*`, `docs/superpowers/plans/*` — untouched on this
>   branch, forbidden to edit, out of CI scope); the CI-authoritative gate
>   (`ruff check paxman/ tests/ && ruff format --check paxman/ tests/`) is
>   fully green. All ten plan tasks are done — do not re-execute them.

---

## §1 Cross-Part Contract

### Goal

Implement ADR-0003: replace grammar-name affinity with **semantic affinity**.
`Grammar` gains a required `semantics: ClassVar[str]` enforced by a new
`Grammar.__init_subclass__`; `Rule.target_grammars` is **replaced** by
`Rule.target_semantics` (identical enforcement); the engine routes on
semantics at all three sites (`_validate_affinity`, `_collect_candidates`,
`_activated_rules`). Phase 1 is a byte-identical rename (`semantics == name`
for every shipped grammar); Phase 2 coalesces same-meaning grammars in Date,
Email, and Phone; a consistency-guard test locks same-semantics/same-field-
mapping; docs are swept. Provenance and candidate dedup stay name-based —
output is byte-identical to today for every existing input, excluding the
digit-glued date class (post-plan lookaround tightening; see Out of scope).

### D-Decisions (locked — do not revisit without a new ADR)

- **D1 — Phase 1 identity: `semantics == name` for all 26 shipped
  grammars.** Routing keyed on semantics with `semantics == name` is
  set-equal to name routing, so behavior is byte-identical (ADR Migration
  #1). The identity is locked by a test (Task 1), not by convention.
- **D2 — The rename is atomic.** `target_grammars` → `target_semantics`
  lands in ONE commit across `domain.py` (Rule ABC), `orchestrator.py`, the
  21 rule files (29 declarations), `extensions.py` (docstring), and the 12
  test files (47 hits). Any split-brain state is an import-time `TypeError`
  from `Rule.__init_subclass__` — the sweep must be atomic (ADR-0002 plan
  trap #3 precedent).
- **D3 — Enforcement mirrors `Rule`'s.** `Grammar.__init_subclass__`
  requires `semantics` as a non-empty `str`, checked at class-definition
  time. The ABC annotates `semantics: ClassVar[str]`; subclasses declare
  bare `semantics = "..."` (matching the existing `name = "..."` style).
  Inherited values satisfy the check (use `vars(cls).get(attribute,
  getattr(cls, attribute))` exactly like `Rule` at domain.py:211) — so
  `_CountingLongGrammar(_ProbeLongGrammar)` in
  `tests/integration/test_recognition_seam.py` needs no edit.
- **D4 — Test doubles updated in the same commit as enforcement.** Adding
  `Grammar.__init_subclass__` import-fails every test-defined `Grammar`
  subclass lacking `semantics` (18 classes in 8 files). They declare
  `semantics == <their name>` (Phase-1 identity) in the same commit as the
  enforcement lands (Task 3).
- **D5 — Engine routing.** `_validate_affinity` validates
  `rule.target_semantics` against the composed semantics set
  `{g.semantics for g in all_grammars}`; `_collect_candidates` routes via a
  `semantics_by_name: dict[str, str] = {g.name: g.semantics ...}` map built
  at composition time (`recognition.grammar.grammar_name` → semantics →
  membership in `rule.target_semantics`); `_activated_rules` activates a
  community rule when any extra-named grammar's semantics is in the rule's
  `target_semantics`. Provenance (`recognition_rule`/`validation_rule`) and
  `_dedup_candidates` stay name-based, unchanged (ADR §4).
- **D6 — Phase 2 coalescing scope.** Coalesce exactly three groups, one
  capability per task, each verified by the per-capability pipeline tests:
  Date `iso8601_recognition` + `slash_iso_recognition` →
  `"iso8601_calendar_date"` (ADR's worked example), Email
  `standard_recognition` + `obfuscated_recognition` → `"rfc5322_addr_spec"`,
  Phone `e164_recognition` + `international_00_recognition` →
  `"e164_international"`. Within Date, `us_recognition` →
  `"us_calendar_date"` and `european_recognition` →
  `"european_calendar_date"` (the ADR's own id vocabulary); the two Date
  rules targeting `{"us_recognition","european_recognition"}` become
  `{"us_calendar_date","european_calendar_date"}` — a two-element set
  becomes a two-id set, **no widening**.
- **D7 — No-coalesce set (locked, widening is the failure mode).** Date
  US/European stay separate (divergent field mapping — the F1 hazard the
  ADR exists to prevent). Country `iso_3166_historical_ed2020.py` keeps
  three distinct ids (one rule, three shapes). **ISBN is NOT coalesced**:
  `isbn13_recognition` and `isbn10_recognition` keep identity ids because
  the check-digit authorities differ (ISO 2108 mod-10 vs Users' Manual
  mod-11); collapsing them would widen `iso_2108_ed2017.py`'s authority to
  ISBN-10 input — exactly the "never widen" drift ADR risk #2 forbids. The
  range rule (`isbn_range_message_ed2026.py`) keeps both ids. All other
  capabilities (Country, Currency, IP, Money, URL) keep identity ids —
  their 1:1 grammar↔rule mapping means the identity id already names the
  meaning; renaming is cosmetic churn outside the ADR's migration scope.
- **D8 — Consistency guard is test-time, generic, and per-task-extended.**
  A new `tests/unit/test_grammar_semantics_consistency.py` groups every
  shipped grammar class by its declared `semantics` and, for each
  multi-member group, asserts identical notation field mapping +
  canonicalization expectations over shared probe rows. Modeled on the
  `test_grammar_semantic_purity.py` precedent. Written at Task 5 with Date
  probe rows (its first real subject), extended with Email/Phone rows in the
  same commits as those coalescings — the new group's lookup failing before
  coalescing is each task's RED step. Singleton groups pass by construction.
- **D9 — Docs sweep.** 6 in-scope files at repo root (32 references) + the
  2 nested AGENTS.md under `paxman/` are swept (ADR Migration #4). Historical
  records are excluded (ADR-0002 precedent): `docs/superpowers/plans/*`,
  `docs/report/*`, `docs/research/*`, `docs/adr/*`. The zero-grep proof must
  exclude generated dirs (`htmlcov/`, `.hypothesis/`, `.pytest_cache/`,
  `.venv/`) or it fails on a dirty local checkout.
- **D10 — Ground truth over ADR claims.** The ADR's "55 files reference
  `target_grammars`" (L205) was a pre-migration estimate. Verified by
  re-counting at the migration start commit: **55 files** — 44 sweep-relevant
  (26 under `paxman/` — 24 `.py` + 2 nested AGENTS.md, 12 test files, 6
  repo-root doc files, `HOW_TO_ADD_NEW_GRAMMAR.md` included) plus 8 plan + 3
  research files excluded by D9. Where the ADR and this plan disagree on
  counts/paths, this plan's verified inventory wins (the ADR's count is
  superseded as stale).

### Out of scope

- No behavior change to recognition/validation/status semantics (Phase 1 is
  byte-identical; Phase 2 coalesces declarations only). Post-plan correction:
  the date grammars' digit-lookaround bounds were tightened so digit-glued
  ids like `12026-01-15` no longer partially match — deliberate, so "no
  behavior change" excludes that digit-glued class only.
- No rename of `GrammarRule.grammar_name`, `RecognizedRep`, `Candidate`,
  or `_dedup_candidates` keys — provenance stays name-based (ADR §4).
- No edits to historical plans/research/ADR files (D9).
- No new runtime semantics introspection by the engine (ADR Migration #3 —
  the consistency guard is test-time only).
- No semantic-id renaming outside the coalescing capabilities (D6/D7).

---

## §2 Tasks

### Task 1 — `feat(core): declare semantics on all shipped grammars`

> ✅ **LANDED** — commit `ebf21bb` (2026-08-11). Do not re-execute; the
> progress banner in §2's header supersedes this task's steps.

Phase 1 identity: every shipped grammar declares `semantics = "<its own
name>"`. No enforcement yet — these are inert attributes until Task 3.

**Step 1 RED — new file `tests/unit/test_grammar_semantics_metadata.py`**
- Add `test_shipped_grammars_declare_semantics_identity`: for each of the
  nine shipped capabilities, for each grammar returned by
  `capability.get_grammars()`: assert `isinstance(grammar.semantics, str)`,
  `grammar.semantics != ""`, and `grammar.semantics == grammar.name`.
- Mark with the `unit` marker.
- Run: `uv run pytest tests/unit/test_grammar_semantics_metadata.py -q` →
  RED (`AttributeError: ... has no attribute 'semantics'`).

**Step 2 GREEN — add `semantics = "<name>"` to all 26 shipped grammar files**
(one bare class attribute each, placed after the `name` declaration,
mirroring the existing `name = "..."` style):

| Capability | File | Grammar class | `semantics` value |
|------------|------|---------------|-------------------|
| Country | `grammar/alpha2_recognition.py` | `Alpha2Grammar` | `"alpha2_recognition"` |
| Country | `grammar/alpha3_recognition.py` | `Alpha3Grammar` | `"alpha3_recognition"` |
| Country | `grammar/numeric_recognition.py` | `NumericGrammar` | `"numeric_recognition"` |
| Country | `grammar/name_recognition.py` | `NameGrammar` | `"name_recognition"` |
| Currency | `grammar/code_recognition.py` | `CodeRecognition` | `"code_recognition"` |
| Currency | `grammar/symbol_recognition.py` | `SymbolRecognition` | `"symbol_recognition"` |
| Currency | `grammar/word_recognition.py` | `WordRecognition` | `"word_recognition"` |
| Date | `grammar/iso8601_recognition.py` | `ISO8601DateGrammar` | `"iso8601_recognition"` |
| Date | `grammar/us_recognition.py` | `USDateGrammar` | `"us_recognition"` |
| Date | `grammar/european_recognition.py` | `EuropeanDateGrammar` | `"european_recognition"` |
| Date | `grammar/slash_iso_recognition.py` | `SlashISODateGrammar` | `"slash_iso_recognition"` |
| Email | `grammar/standard_recognition.py` | `StandardEmailGrammar` | `"standard_recognition"` |
| Email | `grammar/obfuscated_recognition.py` | `ObfuscatedEmailGrammar` | `"obfuscated_recognition"` |
| Email | `grammar/localhost_recognition.py` | `LocalhostEmailGrammar` | `"localhost_recognition"` |
| IP | `grammar/ipv4_recognition.py` | `IPv4Grammar` | `"ipv4_recognition"` |
| IP | `grammar/ipv6_recognition.py` | `IPv6Grammar` | `"ipv6_recognition"` |
| ISBN | `grammar/isbn13_recognition.py` | `ISBN13RecognitionGrammar` | `"isbn13_recognition"` |
| ISBN | `grammar/isbn10_recognition.py` | `ISBN10RecognitionGrammar` | `"isbn10_recognition"` |
| Money | `grammar/code_recognition.py` | `CodeRecognition` | `"code_recognition"` |
| Money | `grammar/symbol_recognition.py` | `SymbolRecognition` | `"symbol_recognition"` |
| Money | `grammar/word_recognition.py` | `WordRecognition` | `"word_recognition"` |
| Phone | `grammar/e164_recognition.py` | `E164Grammar` | `"e164_recognition"` |
| Phone | `grammar/tel_uri_recognition.py` | `TelUriGrammar` | `"tel_uri_recognition"` |
| Phone | `grammar/international_00_recognition.py` | `International00Grammar` | `"international_00_recognition"` |
| Phone | `grammar/national_recognition.py` | `NationalGrammar` | `"national_recognition"` |
| URL | `grammar/absolute_uri_recognition.py` | `AbsoluteUriRecognition` | `"absolute_uri_recognition"` |

All files are under `paxman/capabilities/<Capability>/`.

**Verify**
```bash
uv run pytest tests/unit/test_grammar_semantics_metadata.py -q
uv run pytest -q
uv run ruff check paxman/capabilities/ tests/unit/test_grammar_semantics_metadata.py
```

**Commit**
```
feat(core): declare semantics on all shipped grammars
```

---

### Task 2 — `refactor: rename target_grammars to target_semantics`

> ✅ **LANDED** — commit `f8ac1f6` (2026-08-11). Do not re-execute; the
> progress banner in §2's header supersedes this task's steps. Zero
> `target_grammars` hits remain in `paxman/` or `tests/` (verified).

The atomic rename (D2). Pure mechanical sweep — **no RED test**; the RED
state is the intermediate breakage demonstrated in Step 1 below, fixed by
Step 2 in the same commit.

**Step 1 RED (demonstrate breakage — do not commit)**
- In `paxman/core/domain.py` only, rename the five `target_grammars` sites in
  `Rule` (L191 annotation, L202 required tuple, L210 type-check loop, L218
  non-empty guard, L219 error message) to `target_semantics`.
- Run: `uv run pytest tests/unit/test_rule_metadata.py -q` → RED
  (`TypeError: must define Rule metadata`) and
  `uv run pyright paxman/capabilities/` → RED. This proves the sweep below
  is mandatory and atomic.

**Step 2 GREEN — sweep every remaining site in one commit**

Source (`paxman/`):
| File | Sites |
|------|-------|
| `paxman/core/domain.py` | already renamed in Step 1 (5 sites) |
| `paxman/engine/orchestrator.py` | L287 (`_validate_affinity` read), L312 (`_collect_candidates` route), L399 (`_activated_rules` intersection), plus docstrings L302, L346, L389 |
| `paxman/core/extensions.py` | docstring L71 (`register_rule`) |

Rule files — rename the attribute name in all 29 declarations (values
unchanged — Phase 1 identity):

| File | Decl lines | Set value (unchanged) |
|------|-----------|-----------------------|
| `Country/rules/iso_3166_ed2024.py` | L61, L101, L141, L189 | `{"alpha2_recognition"}` / `{"alpha3_recognition"}` / `{"numeric_recognition"}` / `{"name_recognition"}` |
| `Country/rules/cldr_localized_ed2025.py` | L48 | `{"name_recognition"}` |
| `Country/rules/iso_3166_historical_ed2020.py` | L69-71 (multi-line) | `{"name_recognition","alpha2_recognition","numeric_recognition"}` |
| `Currency/rules/iso_4217_ed2015.py` | L45 | `{"code_recognition"}` |
| `Currency/rules/cldr_currencies_ed2025.py` | L125, L169 | `{"symbol_recognition"}` / `{"word_recognition"}` |
| `Date/rules/iso_8601_ed2019.py` | L36 | `{"iso8601_recognition","slash_iso_recognition"}` |
| `Date/rules/en_50160_ed2010.py` | L33 | `{"us_recognition","european_recognition"}` |
| `Date/rules/us_federal_rules_ed2023.py` | L33 | `{"us_recognition","european_recognition"}` |
| `Email/rules/rfc_5322_ed2008.py` | L36 | `{"standard_recognition","obfuscated_recognition"}` |
| `Email/rules/rfc_6761_ed2012.py` | L36 | `{"localhost_recognition"}` |
| `IP/rules/rfc_791_ed1981.py` | L33 | `{"ipv4_recognition"}` |
| `IP/rules/rfc_5952_ed2010.py` | L34 | `{"ipv6_recognition"}` |
| `ISBN/rules/iso_2108_ed2017.py` | L32, L55 | `{"isbn13_recognition"}` (both) |
| `ISBN/rules/isbn_users_manual_ed2012.py` | L34 | `{"isbn10_recognition"}` |
| `ISBN/rules/isbn_range_message_ed2026.py` | L37 | `{"isbn13_recognition","isbn10_recognition"}` |
| `Money/rules/iso_4217_ed2015.py` | L76 | `{"code_recognition"}` |
| `Money/rules/cldr_currencies_ed2025.py` | L136, L199 | `{"symbol_recognition"}` / `{"word_recognition"}` |
| `Phone/rules/rfc_3966_ed2004.py` | L34 | `{"tel_uri_recognition"}` |
| `Phone/rules/e164_ed2010.py` | L69, L111 | `{"e164_recognition","international_00_recognition"}` (both) |
| `Phone/rules/nanp_ed2024.py` | L93, L148 | `{"national_recognition"}` (both) |
| `URL/rules/whatwg_url_standard.py` | L43 | `{"absolute_uri_recognition"}` |

All under `paxman/capabilities/<Capability>/`.

Tests — rename the attribute everywhere (values unchanged). 12 files, 47
hits:
| File | Sites |
|------|-------|
| `tests/unit/test_capability.py` | L38 `StubRule` |
| `tests/unit/test_extensions.py` | L85 `_DotDateRule`, L102 `_NamelessRule` |
| `tests/unit/test_rule_metadata.py` | `_RULE_METADATA_ATTRS` (L15-22, `"target_grammars"` at L20 → `"target_semantics"`), L97 conditional `if missing != "target_grammars":`, L118 class `_EmptyTargetGrammars` → `_EmptyTargetSemantics`, `match=` regexes embedding the attribute name (L85, L111 `"non-empty"`, L152 `"must be frozenset[str]"`) |
| `tests/integration/test_feature_gating.py` | L148 `_DanglingFeatureRule`, L214 `_DanglingGrammarRule`, docstring L58 |
| `tests/integration/test_recognition_seam.py` | L101 `_LongRule`, L126 `_ShortRule`, L403 `_CommunityRule` |
| `tests/integration/test_grammar_extensions.py` | L89 `DotDateRule`, L112 `SecondDateRule`, L135 `CommunityISO8601Rule`, L155 `DanglingDateRule`, docstring L149 |
| `tests/integration/test_format_value_seam.py` | L78 `_TokenRule`, L180 `_DualTokenRule` |
| `tests/integration/test_pipeline.py` | L167 `StubRule`, L192 `ExplodingRule`, L388 `_PhantomRule`, docstrings L374, L440 |
| `tests/capabilities/isbn/test_rules.py` | L182, L188, L194, L200-202 (`TestRuleConventions`) |
| `tests/capabilities/money/test_rules.py` | L145-147, L263-265, L378-380 + method names `test_target_grammars` → `test_target_semantics` |
| `tests/capabilities/currency/test_rules.py` | L100-102, L239-241, L309-311 + method names `test_target_grammars` → `test_target_semantics` |
| `tests/capabilities/url/test_rule.py` | L47 |

Rule metadata values are grammar names today and remain grammar-name strings
in Phase 1 (D1/D2) — the value mapping is deferred to Phase 2 tasks.

**Verify**
```bash
uv run pytest -q
uv run ruff check paxman/ tests/
uv run pyright
```
Also confirm the sweep is complete (zero hits inside `paxman/` and `tests/`):
```bash
grep -rn "target_grammars" paxman/ tests/
```
(No `|| echo "CLEAN"` fallback — zero matches prints nothing and exits 1; a
grep error exits ≥ 2 and stays visible.)

**Commit**
```
refactor: rename target_grammars to target_semantics
```

---

### Task 3 — `feat(core): enforce Grammar.semantics at class-definition time`

The enforcement mirror (D3), landing together with the test-double sweep
(D4) — import-time failure otherwise.

**Step 1 RED — extend `tests/unit/test_grammar_semantics_metadata.py`**
- Add `test_bare_grammar_subclass_raises_type_error`: a local
  `class _BareGrammar(Grammar[Any])` with only `name` and `recognize()`
  raises `TypeError` matching `"must define Grammar metadata"` (or the
  exact message chosen in Step 2 — write the test to match it).
- Add `test_missing_semantics_raises`: parametrized — grammar with
  everything but `semantics` → `TypeError` naming `semantics`.
- Add `test_empty_semantics_raises`: `semantics = ""` → `TypeError`
  matching `"non-empty"`.
- Add `test_semantics_must_be_str`: `semantics = 42` / `semantics =
  frozenset()` → `TypeError` matching `"semantics must be str"`.
- Add `test_inherited_semantics_satisfies_enforcement`: a subclass of a
  compliant grammar (no own `semantics`) is accepted — locks the
  `vars(cls).get` fallback (D3), covering `_CountingLongGrammar`.
- Run: `uv run pytest tests/unit/test_grammar_semantics_metadata.py -q` →
  RED (no `__init_subclass__` yet).

**Step 2 GREEN — one commit containing all three:**
1. `paxman/core/domain.py` — add to `Grammar` (L228-240):
   - `semantics: ClassVar[str]` annotation (next to `name: str`).
   - `__init_subclass__` mirroring `Rule`'s (L194-219): require `semantics`
     via `hasattr`; type-check `vars(cls).get("semantics",
     getattr(cls, "semantics"))` is `type(...) is str`; non-empty guard.
     Error messages: `f"{cls.__name__} must define Grammar metadata:
     semantics"`, `f"{cls.__name__}.semantics must be str"`,
     `f"{cls.__name__}.semantics must be non-empty"`.
   - `ClassVar` is already imported (`Rule` uses it at L191).
2. All 18 test-defined `Grammar` subclasses in 8 files get
   `semantics = "<their name>"` (Phase-1 identity, D4):
   `tests/unit/test_capability.py` L14 `StubGrammar`; `tests/unit/
   test_extensions.py` L42/51/60/69 (`_DotDateGrammar`, `_SecondGrammar`,
   `_NamelessGrammar`, `_MixedCaseGrammar`); `tests/unit/test_discovery.py`
   L61 `DotDateGrammar`; `tests/integration/test_feature_gating.py` L54
   `_NameRecognitionGrammar`; `tests/integration/test_grammar_extensions.py`
   L35/54/73 (`DotDateGrammar`, `SecondDateGrammar`, `ClashingDateGrammar`);
   `tests/integration/test_format_value_seam.py` L47/143 (`_TokenGrammar`,
   `_DualTokenGrammar`); `tests/integration/test_pipeline.py` L127/136/357
   (`CrashGrammar`, `SimpleGrammar`, `_PhantomGrammar`);
   `tests/integration/test_recognition_seam.py` L44/69/376
   (`_ProbeLongGrammar`, `_ProbeShortGrammar`, `_CommunityGrammar`).
   Do NOT touch `_CountingLongGrammar` (L324 — inherits, D3) or the
   lookalike test classes (`TestGrammarRule`, `TestGrammarDedup`,
   `TestExtraGrammars` — not Grammar subclasses).
3. Ship the enforcement tests from Step 1.

**Verify**
```bash
uv run pytest tests/unit/test_grammar_semantics_metadata.py -q
uv run pytest -q
uv run ruff check paxman/ tests/
uv run pyright
```

**Commit**
```
feat(core): enforce Grammar.semantics at class-definition time
```

---

### Task 4 — `refactor(engine): route on semantics, not grammar name`

The three engine sites switch from name keys to semantics keys (D5). With
`semantics == name` (D1) the routing keys are set-equal, so this is
byte-identical — **no RED test is writable**; the full suite is the
regression net (a behavior change would surface as test failures). Do not
rename `GrammarRule.grammar_name`, `Candidate.recognition_rule`, or the
`_dedup_candidates` key — provenance stays name-based (ADR §4).

**Step 1 GREEN — `paxman/engine/orchestrator.py`**
- `run_capability` (L54-89): after `all_grammars` is composed (L60-63),
  build `semantics_by_name = {g.name: g.semantics for g in all_grammars}`
  and pass it to `_validate_affinity`, `_collect_candidates`, and
  `_activated_rules` (update signatures; `_activated_rules` currently takes
  `(capability, contract)` at L385, `_collect_candidates` takes
  `(capability, recognitions, rules)` at L295).
- `_validate_affinity` (L276-292): `known_grammars = {g.name ...}` →
  `known_semantics = {g.semantics for g in all_grammars}`; iterate
  `rule.target_semantics`; error message: "declares unknown semantics"
  (keep the sorted-listing shape).
- `_collect_candidates` (L295-338): at L310-312, resolve the producing
  grammar's semantics via the map — `semantics_by_name[grammar_name] not in
  rule.target_semantics: continue`. Update the docstring (L302) to describe
  semantic routing.
- `_activated_rules` (L385-400): replace `extra_grammars &
  rule.target_grammars` with a semantics-keyed activation:
  `extra_semantics = {semantics_by_name[n] for n in extra_grammars if n in
  semantics_by_name}`; activate iff `extra_semantics &
  rule.target_semantics`. Unknown extra names are silently skipped (existing
  behavior preserved).
- Check no test asserts the OLD `_validate_affinity` error text verbatim
  (grep `unknown grammar` in `tests/`); if one does, update it in this
  commit to "unknown semantics".

**Step 2 VERIFY (byte-identity proof)**
```bash
uv run pytest -q
uv run ruff check paxman/ tests/
uv run pyright
```
All green = routing keyed on semantics is behavior-identical (D1).

**Commit**
```
refactor(engine): route on semantics, not grammar name
```

---

### Task 5 — `refactor(capabilities): coalesce Date grammars to calendar-date semantics`

First Phase 2 coalescing (ADR Migration #2, the ADR's own worked example).
Two RED drivers: the consistency-guard test's group lookup, and
`CommunityISO8601Rule`'s dangling semantics.

**Step 1 RED**
- Create `tests/unit/test_grammar_semantics_consistency.py` (D8): a generic
  guard that enumerates all shipped grammar classes, groups them by
  `semantics`, and for each multi-member group runs shared probe rows
  through each member's `recognize()` asserting identical notation fields +
  canonicalization expectations. Seed it with the Date group's probe row:
  `iso8601` input `"2026-01-15"` and `slash_iso` input `"2026/01/15"` both
  produce `DateNotation(N1="2026", N2="01", N3="15")`, both canonicalize to
  `"2026-01-15"` through the ISO rule. (Verify the exact `DateNotation`
  field names from `paxman/capabilities/Date/notation.py` while writing.)
- In `tests/integration/test_grammar_extensions.py`, update
  `CommunityISO8601Rule.target_semantics` (L135) from
  `frozenset({"iso8601_recognition"})` to
  `frozenset({"iso8601_calendar_date"})`.
- Run: `uv run pytest tests/unit/test_grammar_semantics_consistency.py
  tests/integration/test_grammar_extensions.py -q` → RED: the guard test
  cannot find a `"iso8601_calendar_date"` group (grammars still claim
  identity ids) and `test_grammar_extensions.py` fails fast with
  `ContractError` (dangling semantics — the coalesced id is not yet known).

**Step 2 GREEN**
- Date grammars (4): `iso8601_recognition.py` and `slash_iso_recognition.py`
  → `semantics = "iso8601_calendar_date"`; `us_recognition.py` →
  `"us_calendar_date"`; `european_recognition.py` → `"european_calendar_date"`.
- Date rules (3): `iso_8601_ed2019.py` L36 →
  `frozenset({"iso8601_calendar_date"})`; `en_50160_ed2010.py` L33 and
  `us_federal_rules_ed2023.py` L33 →
  `frozenset({"us_calendar_date", "european_calendar_date"})` (no widening,
  D6).
- No other rule file changes (D7).
- **Plan deviation (approved 2026-08-11)**: `test_shipped_grammars_declare_semantics_identity`
  (`tests/unit/test_grammar_semantics_metadata.py` L25-32) asserts `semantics == name` for
  every shipped grammar; coalescing breaks it. Update it in this commit: keep the str /
  non-empty assertions for all grammars, add a module-level `_COALESCED_SEMANTICS` frozenset
  (seeded `{"iso8601_calendar_date", "us_calendar_date", "european_calendar_date"}`), and
  assert `semantics == name or semantics in _COALESCED_SEMANTICS`. Tasks 6-7 extend the set
  with the Email/Phone ids. Keeps every commit green — Task 8's `pytest tests/unit` verify
  passes as written.

**Verify**
```bash
uv run pytest tests/capabilities/date tests/integration/test_grammar_extensions.py \
  tests/unit/test_grammar_semantics_consistency.py -q
uv run pytest tests/integration -q
uv run pytest tests/unit/test_grammar_semantics_metadata.py -q
uv run ruff check paxman/capabilities/Date/ tests/
uv run pyright
```

**Commit**
```
refactor(capabilities): coalesce Date grammars to calendar-date semantics
```

---

### Task 6 — `refactor(capabilities): coalesce Email grammars to addr-spec semantics`

Second coalescing (D6). The guard test is extended in the same commit —
its group lookup is the RED driver.

**Step 1 RED — extend `tests/unit/test_grammar_semantics_consistency.py`**
- Add the `"rfc5322_addr_spec"` group's probe rows: `standard` input (e.g.
  `"user@example.com"`) and `obfuscated` input (e.g.
  `"user at example dot com"`) produce identical `EmailNotation` fields and
  both canonicalize to `"user@example.com"` through the RFC 5322 rule.
  (Verify exact `EmailNotation` fields from
  `paxman/capabilities/Email/notation.py` while writing.)
- Run: `uv run pytest tests/unit/test_grammar_semantics_consistency.py -q`
  → RED (no `"rfc5322_addr_spec"` group exists yet).

**Step 2 GREEN**
- Email grammars (2): `standard_recognition.py` and
  `obfuscated_recognition.py` → `semantics = "rfc5322_addr_spec"`.
- Email rule (1): `rfc_5322_ed2008.py` L36 →
  `frozenset({"rfc5322_addr_spec"})`.
- Unchanged: `localhost_recognition.py` (identity), `rfc_6761_ed2012.py` L36
  `{"localhost_recognition"}`.

**Verify**
```bash
uv run pytest tests/capabilities/email tests/unit/test_grammar_semantics_consistency.py -q
uv run pytest tests/integration -q
uv run ruff check paxman/capabilities/Email/ tests/
uv run pyright
```

**Commit**
```
refactor(capabilities): coalesce Email grammars to addr-spec semantics
```

---

### Task 7 — `refactor(capabilities): coalesce Phone grammars to E.164 semantics`

Third coalescing (D6). Same pattern as Task 6.

**Step 1 RED — extend `tests/unit/test_grammar_semantics_consistency.py`**
- Add the `"e164_international"` group's probe rows: `e164` input (e.g.
  `"+15551234567"`) and `international_00` input (e.g. `"0015551234567"`)
  produce identical `PhoneNotation` fields and both canonicalize to
  `"+15551234567"` through the E.164 rule. (Verify exact `PhoneNotation`
  fields from `paxman/capabilities/Phone/notation.py` while writing.)
- Run: `uv run pytest tests/unit/test_grammar_semantics_consistency.py -q`
  → RED (no `"e164_international"` group yet).

**Step 2 GREEN**
- Phone grammars (2): `e164_recognition.py` and
  `international_00_recognition.py` → `semantics = "e164_international"`.
- Phone rules (2 classes, 1 file): `e164_ed2010.py` L69 and L111 →
  `frozenset({"e164_international"})`.
- Unchanged: `tel_uri_recognition.py` + `rfc_3966_ed2004.py` L34
  (`{"tel_uri_recognition"}`), `national_recognition.py` + `nanp_ed2024.py`
  L93/L148 (`{"national_recognition"}`).

**Verify**
```bash
uv run pytest tests/capabilities/phone tests/unit/test_grammar_semantics_consistency.py -q
uv run pytest tests/integration -q
uv run ruff check paxman/capabilities/Phone/ tests/
uv run pyright
```

**Commit**
```
refactor(capabilities): coalesce Phone grammars to E.164 semantics
```

---

### Task 8 — `test: lock same-semantics field-mapping consistency`

The guard's structural half: assert the no-coalesce and non-coalesced groups
stay singleton (D6/D7) and that every multi-member group is covered by probe
rows. This makes the guard a complete F1-style test-time guarantee (ADR
Migration #3).

**Step 1 GREEN (test-only — the groups already exist after Tasks 5-7)**
- Extend `tests/unit/test_grammar_semantics_consistency.py`:
  - A structural enumeration: every shipped grammar belongs to a semantics
    group; every multi-member group MUST have probe rows defined in the
    test's table (fails if a future coalescing adds a group without rows).
  - Explicit singleton assertions for the no-coalesce set (D7): exactly one
    grammar claims each of `"us_calendar_date"`, `"european_calendar_date"`,
    `"name_recognition"`, `"alpha2_recognition"`, `"alpha3_recognition"`,
    `"numeric_recognition"`, `"isbn13_recognition"`, `"isbn10_recognition"`.
- Run: `uv run pytest tests/unit/test_grammar_semantics_consistency.py -q`
  → GREEN (all groups consistent after Tasks 5-7). If RED, a coalescing
  drifted — investigate, do not weaken the test.

**Verify**
```bash
uv run pytest tests/unit/test_grammar_semantics_consistency.py -q
uv run pytest tests/unit -q
```

**Commit**
```
test: lock same-semantics field-mapping consistency
```

---

### Task 9 — `docs: sweep target_grammars and document semantic affinity`

> **Follow-up items folded in here (M1-M2: Task 4 review; M3: Task 5 execution):**
> - **M1 (source docstring):** in `paxman/engine/orchestrator.py` `_collect_candidates`, add one sentence to the docstring stating the KeyError invariant for `semantics_by_name[grammar_name]`: recognitions are produced only by grammars in the composed `all_grammars` (`_recognize` filters against `supported_names`), the same list the map is built from.
> - **M2 (dead citation):** the `(ARCHITECTURE.md:201)` reference in that same docstring is stale (ARCHITECTURE.md has no routing/affinity content; L201 is "Quality Enforcement") — drop the dead line-number reference while updating the docstring.
> - **M3 (README fail-fast mechanism, verified against the engine 2026-08-11):** the "Rules of the seam" fail-fast bullet must state the real mechanism — `_activated_rules` resolves `extra_grammars` names via `semantics_by_name.get(n, n)`, so an unknown extra name keeps its own string and can activate a community rule targeting that (dangling) id, which `_validate_affinity` then rejects with `ContractError`. A rule that is NOT opted in is silently inert regardless of dangling targets. (Task 5's RED driver exercised the inert path, not the fail-fast path, hence the plan's original ContractError prediction did not match.)

Docs sweep (ADR Migration #4, D9). **No RED step** — pure documentation.

**Step 1 GREEN — rewrite the 6 in-scope repo-root files + 2 nested AGENTS.md**

| File | References to update |
|------|----------------------|
| `README.md` | L458 (Community Extensions sample: `DotDateGrammar` gains `semantics = "dot_date_recognition"`, `DotDateRule` `target_grammars` → `target_semantics`), L485 + L488 ("Rules of the seam" bullets — opt-in and fail-fast now keyed on semantics) |
| `ARCHITECTURE.md` | L100 (composition guard), L174 (community opt-in), L176 (fail-fast `ContractError`) — reword to semantics vocabulary |
| `CONTEXT.md` | L140, L155 (six-metadata-attrs sentence → `target_semantics` + grammar `semantics` claim), L182, L207 |
| `HOW_TO_ADD_NEW_CAPABILITY.md` | L292 (Step 5 directive), L441, L449, L453 (rule template `target_semantics: ClassVar[frozenset[str]]`), L572 (orthogonality note), L1035, L1056, L1069 (checklist) |
| `HOW_TO_ADD_NEW_GRAMMAR.md` | L21, L23, L33, L174, L178, L192 (extended example), L200, L202, L287 (validation table) — **Step 4 is rewritten per ADR**: a grammar whose meaning is already shipped declares a shipped `semantics` id and stops (no rule edit); a genuinely new meaning requires a new rule |
| `capability_homogeneity_audit.md` | L63, L65 (proposed orchestrator line → semantics keyed), L233, L296, L307 (F1 addenda) |
| `paxman/core/AGENTS.md` | L25 (Rule six-attr list → `target_semantics`) + add the Grammar `semantics` convention |
| `paxman/capabilities/AGENTS.md` | L43 (rule-file conventions → `target_semantics`) + grammar `semantics` requirement |

Note: `HOW_TO_ADD_NEW_GRAMMAR.md` and `HOW_TO_ADD_NEW_CAPABILITY.md` live at
the **repo root**, not under `docs/`.

Do NOT touch (historical records, ADR-0002 precedent): `docs/superpowers/
plans/*`, `docs/report/*`, `docs/research/*`, `docs/adr/*`.

**Verify** (zero hits outside the excluded paths — the historical records and
generated dirs are excluded; `paxman/` and `tests/` are searched, because the
sweep covers the nested AGENTS.md there):
```bash
grep -rnE 'target_grammars' . \
  --exclude-dir=.git --exclude-dir=plans --exclude-dir=report \
  --exclude-dir=research --exclude-dir=adr \
  --exclude-dir=htmlcov --exclude-dir=.hypothesis \
  --exclude-dir=.pytest_cache --exclude-dir=.venv
```
No `|| echo "CLEAN"` fallback: zero matches is the expected result (grep
prints nothing, exits 1); any grep error (exit ≥ 2) stays visible instead of
being reported as "CLEAN".

**Commit**
```
docs: sweep target_grammars and document semantic affinity
```

---

### Task 10 — Final gate (no commit)

**Verify — full pre-PR gate** (authoritative per `.github/workflows/ci.yml`;
ruff lint and format are CI-scoped to `paxman/ tests/`):
```bash
uv run ruff check paxman/ tests/ && uv run ruff format --check paxman/ tests/ \
  && uv run pyright && uv run import-linter lint && uv run pytest
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
Zero-grep proof (Task 9 Verify) shows no matches outside the excluded
paths; `target_grammars` appears nowhere in `paxman/` or `tests/`; `semantics`
is present on all 26 shipped grammars (Task 1 test still green).

If any gate fails, fix it in a follow-up commit — never by weakening a test,
never by restoring `target_grammars`, never by editing the excluded
historical docs.

---

## §3 Traps

1. **Ordering is load-bearing.** Task 2 must include `domain.py` AND all 21
   rule files AND the 12 test files in one commit — any split is an
   import-time `TypeError` (D2). Task 3 must include `domain.py` AND the 18
   test doubles in one commit — enforcement import-fails every grammar
   subclass lacking `semantics` (D4). Task 5 must include the
   `CommunityISO8601Rule` fixture update in the same commit as the Date
   coalescing, or `tests/integration/test_grammar_extensions.py` fails fast
   with `ContractError` (dangling `"iso8601_calendar_date"`).
2. **Never widen a rule's meaning set.** `target_semantics` coalescing is
   set-collapse only: `{"iso8601_recognition","slash_iso_recognition"}` →
   `{"iso8601_calendar_date"}` is fine; `{"us_recognition",
   "european_recognition"}` → `{"us_calendar_date","european_calendar_date"}`
   keeps two ids. ISBN is deliberately NOT coalesced (D7) — collapsing
   isbn13/isbn10 would widen `iso_2108_ed2017.py` to ISBN-10 input. If a
   coalescing looks like it needs a set to grow, it is wrong.
3. **Error-message coupling.** `tests/unit/test_rule_metadata.py` matches
   `TypeError` text that embeds the attribute name (`match=missing`, L111
   `"non-empty"`, L152 `"must be frozenset[str]"`) and `domain.py` L219 bakes
   `target_grammars` into the message — the Task 2 sweep must rename source
   and test in the same commit. Same coupling applies to the new
   `Grammar.__init_subclass__` messages (Task 3) — write the tests to the
   exact messages you ship.
4. **ADR's "55 files" is stale.** Verified ground truth is 44 files
   (D10). Use this plan's tables; the ADR's counts are for reference only.
5. **Generated artifacts trip the zero-grep proof.** `htmlcov/` (11 files),
   `.hypothesis/`, `.pytest_cache/` contain stale `target_grammars` matches
   and are gitignored — the Task 9/10 proof command excludes them (D9).
6. **`HOW_TO_ADD_*` guides are at the repo root**, not under `docs/` — path
   mistakes in the sweep are silent no-ops.
7. **The three engine routing sites have no direct unit coverage** —
   `_validate_affinity`, `_collect_candidates`, `_activated_rules` are
   covered through integration fixtures (recognition seam, feature gating,
   grammar extensions, pipeline). Do not "add coverage" by weakening those
   fixtures; Task 4's byte-identity proof IS the integration suite.
8. **Provenance stays name-based.** Do not "helpfully" rename
   `GrammarRule.grammar_name`, `Candidate.recognition_rule`, or the
   `_dedup_candidates` key in Task 4 — ADR §4 pins them; changing them is
   an output change outside this ADR.
9. **Property and e2e suites have zero `target_grammars` hits** — no edits
   needed, but they instantiate shipped grammars, so Task 3's enforcement
   applies to them at import. They are exercised at the Task 10 gate.
10. **`_CountingLongGrammar` needs no edit** (D3 — inheritance satisfies
    the `vars(cls).get` fallback), and the lookalike classes
    (`TestGrammarRule`, `TestGrammarDedup`, `TestExtraGrammars`) are test
    classes, not Grammar subclasses — do not touch them.

---

## §4 Definition of Done

- [x] All 26 shipped grammars declare `semantics` (identity in Phase 1;
      coalesced ids for Date/Email/Phone after Phase 2), enforced by
      `Grammar.__init_subclass__` at class-definition time with tests.
- [x] Zero `target_grammars` anywhere in `paxman/` or `tests/`; the Task 9
      zero-grep proof shows no matches outside the excluded historical paths.
- [x] Engine routes on semantics at all three sites; provenance and
      candidate dedup remain name-based (`GrammarRule.grammar_name`,
      `Candidate.recognition_rule` unchanged).
- [x] Phase 2 coalescing landed for Date/Email/Phone exactly as D6/D7
      scope; no rule's `target_semantics` set grew.
- [x] `tests/unit/test_grammar_semantics_consistency.py` covers every
      multi-member semantics group with probe rows and locks the singleton
      no-coalesce set.
- [x] Docs swept (Task 9 files); README's community example shows
      `semantics` on the grammar and `target_semantics` on the rule.
- [x] Full pre-PR gate green: `ruff check . && ruff format --check . &&
      pyright && import-linter lint && pytest` and 95% coverage per package.
      (Gate as written is green under CI scope; `ruff format --check .`
      additionally flags 8 pre-existing historical docs — see progress
      table note.)

