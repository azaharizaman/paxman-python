# Capability Homogeneity Audit — `paxman/capabilities/`

**Scope:** Abstraction-level audit. Identifies behaviors that *must* be unanimous
across all capabilities (Email, Date, Country, IP, Phone) but are implemented
differently. Concrete per-capability differences are marked **ACCEPTED**;
divergences that violate the contract mandate are marked **DEFECT**.

**Method:** 5 parallel `explore` agents compared contracts, grammars, rules,
notations, and package exports across all 5 capabilities; `codegraph` verified
the orchestrator and base classes; an `oracle` agent produced the authoritative
design verdict (FACT 1–6 below).

---

## Executive Summary

The contract *surface* is now largely unanimous — base `CapabilityContract` plus
`resolve_output_format` in `paxman/core/contract.py` unify `output_format`
resolution and `as_dict()` serialization. But the *behavioral* contract diverges
at four layers where a unanimous implementation must still be built:

1. **Orchestrator routing** (F1) — full cartesian product, no grammar→rule affinity.
2. **Feature gating** (F2) — `include_*` toggles grammars in one cap, rules in another.
3. **Format application** (F4) — `output_format` honored inconsistently within multi-format caps.
4. **Recognition/validation boundary** (F3) — Country canonicalizes at recognition, duplicating authority tables.

Oracle's bottom line: **3 genuine architecture-level defects (F1, F2, F4)**, 1
defect-lite (F3), 1 accepted (F5), plus lower-severity items (F6).

---

## Tier 1 — Architectural findings (Oracle verdicts)

### F1. Orchestrator cartesian product / no grammar→rule routing — `DEFECT`

`paxman/engine/orchestrator.py` `_collect_candidates` (lines 126–152) does:

```python
for recognition in recognitions:
    for rule in rules:
        if rule.matches(recognition.notation, recognition.contract):
            ...
```

There is **no** concept of "grammar X produced this notation → only rules Y may
validate it." Each capability invented its own self-filter:

- **Country** — `shape` discriminator (`if notation.shape != "X": return False`)
- **Phone** — `scheme` discriminator
- **Email** — field-name semantics + regex never matching the wrong shape
- **Date** — positional `N1/N2/N3` convention (no discriminant at all)
- **IP** — `try: ipaddress... except: return False`

This contradicts `ARCHITECTURE.md:201` ("Each grammar's notation flows to its
corresponding validation rule").

**Unanimous ideal:** declare affinity on the rule — `Rule.target_grammars:
frozenset[str]` (ClassVar, enforced by the existing `__init_subclass__` metadata
check); orchestrator adds one line `if grammar_name not in rule.target_grammars:
continue`. Engine stays capability-agnostic (reads declared names, no shape
knowledge). Replay-safe *if* `_collect_candidates` also dedups identical
`(value, recognition_rule, validation_rule)` tuples — otherwise Date candidate
multiplicity changes the hash (semantics/status unchanged). Preserves Date
ambiguity (each rule sees only its grammar's notation → 2 candidates →
AMBIGUOUS). Effort: Medium.

### F2. `include_*` gates grammars (Email) vs rules (Country) — `DEFECT` (ad-hoc form)

Email `include_obfuscated=True` adds `obfuscated_recognition` to `active_grammars`
(→ MISSING when off). Country `include_localized`/`include_historical` are static
`active_grammars`; the gate lives *inside the rule* as
`cast(CountryContract, contract); if not contract.include_historical: return False`.

The subclass cast inside `matches()` silently narrows the `Contract` protocol and
is latent-fragile.

**Oracle's answer to "one unanimous mechanism?":** **No — one single mechanism is
wrong**, because the two feature kinds are semantically distinct (grammar-gate →
MISSING; rule-gate → INVALID). The defect is the *ad-hoc, per-rule implementation*,
not the existence of two loci.

**Unanimous ideal:** one *declaration pattern* with engine enforcement for both
loci — input-shape features → `active_grammars`; authority features → declared
`Rule.requires_features` metadata checked by the engine in `_filter_rules`. Never
via casts in `matches()`. Document in `HOW_TO_ADD_NEW_CAPABILITY.md`.

### F3. Grammar canonicalization (Country/Phone) — `DEFECT-lite` / partial

- **Phone `strip_separators`** = presentation normalization, not canonicalization →
  **ACCEPTED**.
- **Country `name_recognition`** resolves "USA"/"中国" → canonical "United States"
  at recognition. Justified pragmatic divergence with documented intent, BUT:
  (a) violates the stated recognition/validation separation; (b) duplicates
  authority tables across grammar-data and rule-data layers (drift hazard — e.g.
  `HISTORICAL_NAME_TO_CANONICAL` vs `FORMER_NAME_TO_ALPHA2`; "BURMA"→"BURMA" vs
  "BU"); (c) can yield INVALID-from-accepted-input when tables diverge.

**Unanimous ideal:** grammars emit raw recognized tokens; rules own
synonym→canonical tables; grammar recognition-gating derives from rule-table keys
(single source of truth). Minimal compliant alternative: grammar tables reduced to
recognition keys + automated consistency test.

### F4. `output_format` consumption fragmented — `DEFECT` (within multi-format caps)

Contract layer is unanimous (`resolve_output_format` in `__post_init__`). But **no
rule calls it**; each branches on raw strings. Within multi-format caps the format
is honored inconsistently: Date `iso_8601` ignores `output_format`, so
`output_format="US"` on ISO input silently yields ISO.

**Unanimous ideal:** capability-level `format_value(value, output_format)` hook
invoked by the engine after candidate collection; rules always emit the default
canonical form. Fixes Date's silent-ignore and kills the Phone `_canonical`
triplication (see Tier 3 #5).

### F5. `active_grammars` toggleable (Email/IP) vs static (Date/Country/Phone) — `ACCEPTED`

Already adjudicated in plan `2026-08-02-capability-surface-homogeneity.md` and
legitimized by `HOW_TO_ADD_NEW_CAPABILITY.md`. The property *shape* (`Sequence[str]`,
consumed by `_recognize`) is unanimous. Low severity — not a defect.

---

## Tier 2 — Grammar layer divergences

Three cross-cutting non-homogeneities (from the grammar-comparison agent):

1. **Canonicalization-at-recognition spectrum** — raw (Email/Date/IP) vs cleaned
   (Phone, Country codes) vs fully-resolved (Country name). The single most
   consequential divergence; the notation is *not* a consistent abstraction.
2. **Dedup policy** — 7 dedup / 8 don't / 1 N/A via 3 distinct mechanisms
   (part-keyed set, address-keyed set, span-overlap). No shared contract for
   `recognize()` uniqueness.
3. **Ordering semantics** — 12 document-order vs 3 two-pass-batch (us, obfuscated,
   ipv6) vs european explicit re-sort. Deterministic everywhere (no replay hazard)
   but the "document order" promise is inconsistent.

**Minor:** Email's 3/3 grammars lack `recognize()` docstrings; 2 Phone
regex-embedded semantic constraints (`[2-9]`, `(?=[1-9])`); redundant `text.strip()`
in Country; Country name recognition-time resolution (documented layering deviation).

---

## Tier 3 — Rule layer divergences

**Homogeneous (good):** signature shapes, no-raise/return-False policy, module-level
`_`-prefixed constant naming, singular `PUBLICATION`.

Ranked defects (from the rule-comparison agent):

| # | Divergence | Class |
|---|---|---|
| 1 | `Section63localhost` declares REGEX, runs zero regex | Defect |
| 2 | E.164 §6.1 (PARSER) & §6.2 (LOOKUP_TABLE) have byte-identical `matches()` | Defect |
| 3 | NANP §1.2 declares LOOKUP_TABLE but regex-gates; §1.1 declares REGEX but does frozenset lookups | Defect |
| 4 | Email/IP expose `output_format` but rules never read it | Defect |
| 5 | `_canonical` triplicated across Phone rules, already drifted (RFC3966 copy adds `;ext=`) | Defect |
| 6 | Email case self-contradictory (local part never lowercased; `localhost` case-sensitive vs lowercase output) | Defect |
| 7 | `_normalize_key` vs `_normalize_numeric_key` twins with different failure fallbacks | Defect |
| 8 | Country rule names drop "Section X.Y" prefix | Justified-ish |
| 9 | `specification_name` embeds version in 2/13; `version` = year vs edition | Minor |
| 10 | 11 mutable module-level dicts, no `MappingProxyType` | Latent defect |
| 11 | Full double-parse in IP/NANP `normalize()` vs none in Email | Perf smell |
| 12 | `iso_3166_ed2024` URL is a geographic-names board for a date standard | Factual flag |
| 13 | Dead mixed-case key `"EQUatorial GUINEA"` in `SYNONYM_TO_ALPHA2` | Data defect |

---

## Consolidated severity-ranked defect list

| Rank | Finding | Class |
|---|---|---|
| 1 | F1 cartesian product / no grammar→rule affinity | Defect |
| 2 | F2 ad-hoc `include_*` gating via subclass cast | Defect |
| 3 | F4 `output_format` honored inconsistently + Phone `_canonical` triplication | Defect |
| 4 | F3 Country recognition-time canonicalization + duplicated authority tables | Defect-lite |
| 5 | Rule `RuleStrategy` decorative (Section63localhost; E.164 6.1/6.2; NANP 1.2) | Defect |
| 6 | Email case self-contradiction | Defect |
| 7 | `_normalize_key` vs `_normalize_numeric_key` twins drift | Defect |
| 8 | 11 unprotected mutable authority dicts | Latent defect |
| 9 | Grammar canonicalization-at-recognition spectrum | Defect-lite |
| 10 | Grammar dedup / ordering inconsistent | Smell |
| 11 | Dead/mislabeled data (`"EQUatorial GUINEA"`; wrong `reference_url`) | Data defect |
| 12 | F5 static vs toggleable `active_grammars` | Accepted |
| 13 | Phone `strip_separators`; Country rule-name prefix | Accepted |

---

## Unanimous ideals — recommended build order

1. **`Rule.target_grammars`** + one-line orchestrator filter (fixes F1; makes
   `ARCHITECTURE.md:201` true; replay-safe with candidate dedup).
2. **Move `include_*` feature-gating** to engine-enforced declared metadata, split
   by feature kind (fixes F2).
3. **Capability-level `format_value` hook**; rules emit default canonical only
   (fixes F4; kills Phone `_canonical` triplication).
4. **Make `RuleStrategy` checked** (assert implementation matches declared) or drop
   it — a decorative enum is worse than none (fixes Tier 3 #1–3).
5. **Single-source authority tables**; grammars emit raw tokens (fixes F3 + #10 + #13).
6. **Freeze authority dicts** with `MappingProxyType` (fixes #8).

---

## Watch out for

- **Replay-hash change** when moving to grammar→rule affinity: candidate
  multiplicity changes for Date inputs unless `_collect_candidates` dedups identical
  `(value, recognition_rule, validation_rule)` tuples. Decide: dedup at engine, or
  accept hash bump on version release.
- **MISSING vs INVALID** semantic: any unification of `include_*` to rule-gating
  flips Email from MISSING→INVALID (regression vs documented fails-fast). Keep
  grammar-gating for input-shape features.
- **Do not enforce `RuleStrategy` blindly** — either make it *checked* or drop it.

## Addendum — Corrections from the F1 implementation (2026-08-03)

F1 was implemented and verified (plan: `docs/superpowers/plans/2026-08-03-f1-grammar-rule-affinity.md`; `pyright` / `ruff` / `import-linter` / `pytest` 782 all green). Two findings surfaced that correct this audit's premises:

### A. Date honors `output_format` — the F4 premise for Date is wrong

The audit (F4, lines 103–113) states *"Date `iso_8601` ignores `output_format`, so `output_format="US"` on ISO input silently yields ISO."* This is **not** borne out by the code. Observed behavior for `01/02/2026`:

| `output_format` | canonical candidate values |
|---|---|
| `None` (resolves to default `"ISO"`) | `{"2026-01-02", "2026-02-01"}` |
| `"US"` | `{"01/02/2026", "02/01/2026"}` |

Date already routes `output_format` into formatting. The reformat is a per-format
bijection, so the count of distinct canonical values (and therefore the `AMBIGUOUS`
status) is preserved under any `output_format` (see F1 plan, `TestGrammarRuleAffinity`).

**Consequence:** the F4 remediation (capability-level `format_value` hook) is **not
required for Date**. F4 should be re-scoped to whichever capabilities *genuinely*
ignore `output_format` (if any remain) — not Date. The audit's F4 severity for Date
is overstated.

### B. F1 replay-hash is byte-identical — the "watch out" risk did not materialize

The audit's *Watch out for* warns that moving to grammar→rule affinity could change
the replay hash via candidate multiplicity. In practice `target_grammars` was set equal
to each rule's *effective acceptance domain* (the affinity map in F1), so the candidate
multiset is identical to the cartesian product for every capability (Email / Date /
Country / IP / Phone). The hash is therefore byte-identical by construction. The
`_dedup_candidates` step is a pure safety net for future over-declaration, not a
behavior change. The plan's Step 6.7 hash-snapshot gate was satisfied *structurally*
(target_grammars == effective domain ⇒ identical hash) rather than by captured
pre-change constants; the full 782-test suite passing is the empirical confirmation.

## Addendum — F3 completion: Country recognition/validation boundary restored (2026-08-03)

F3 (lines 87–101) was implemented and verified (plan:
`docs/superpowers/plans/2026-08-03-f3-recognition-validation-boundary.md`). The
defect described there is resolved; the finding's premise is now historical, and the
lines above are left intact as the record of what was found.

### A. Old behavior — grammar-side canonicalization and duplicated tables

`Country/grammar/name_recognition.py` previously held dictionaries whose values were
canonical names (`USA`/`中国`/`Burma` → "United States"/"China"/"BURMA" at
recognition), duplicating authority tables in the grammar layer
(`HISTORICAL_NAME_TO_CANONICAL` vs `FORMER_NAME_TO_ALPHA2`; "BURMA"→"BURMA" vs "BU")
and letting localized names resolve through the ISO name rule with the wrong
provenance.

### B. New behavior — raw tokens, key-only catalogs, shared normalizer

- Grammar data files are now key-only recognition sets (`ENGLISH_NAME_KEYS`,
  `HISTORICAL_NAME_KEYS`, `CHINESE_NAME_KEYS`, `LOCALIZED_NAME_KEYS`) with no
  token-to-country mapping.
- `NameGrammar` returns the trimmed input token as the notation value
  (`CountryNotation(shape="name", value=<input>)`); it never substitutes a canonical
  name or code.
- `paxman/capabilities/Country/name_normalization.py` provides `normalize_name()`,
  shared by grammar membership checks and rule lookups — syntax-only (case folding,
  NFKD decomposition, punctuation/whitespace cleanup), no transliteration or synonym
  resolution.
- Rules own meaning: ISO 3166-1 owns official names and synonyms (`NAME_TO_ALPHA2`,
  `SYNONYM_TO_ALPHA2`), ISO 3166-3 owns former names (`FORMER_NAME_TO_ALPHA2`), CLDR
  owns localized names (`LOCALIZED_TO_ALPHA2`). Grammar-rescued aliases (`USA`,
  `HOLLAND`, `VIET CONG` → `VD`, and the rest) were moved into the owning rule tables.

### C. Localized status/provenance matrix

| Input | Contract | Status | Candidates | Provenance |
|---|---|---|---|---|
| `Alemania` / `中国` / `马来西亚` | default | `INVALID` | `()` | — (recognized, no authority rule runs) |
| `Alemania` / `中国` / `马来西亚` | `include_localized=True` | `SUCCESS` | `≥1` (`DE`/`CN`/`MY`) | `Unicode` (CLDR v45) |
| `Burma` | `include_historical=True` | `SUCCESS` | `1` (`BU`) | ISO (ISO 3166-3) |
| `Malaysia` | default | `SUCCESS` | `1` (`MY`) | ISO (ISO 3166-1:2024) |

Recognition of localized input is not ISO validation: disabled localized input is
recognized (not `MISSING`) and yields `INVALID` with no candidates, matching the F2
rule-gating semantics (recognized-but-unvalidated, not fails-fast at recognition).

### D. Consistency guard and coverage

`tests/capabilities/country/test_data_consistency.py` asserts every shipped
recognition key is covered by at least one rule-data mapping, plus per-locale
ownership assertions (English → ISO 3166-1, historical → ISO 3166-3, Chinese and
localized → CLDR). The `LOCALIZED_NAME_KEYS` catalog is the single source of truth
for which CLDR spellings are recognized, independent of `include_localized`
(recognition is not gated; validation is).

### E. What remains accepted

Phone `strip_separators` remains presentation/syntax normalization and is unchanged
by F3, as the original finding accepted.

### F. Replay/provenance note

For inputs whose candidate provenance or route changed (localized names that
previously resolved through ISO), replay hashes are intentionally not byte-identical
to pre-F3 behavior. Same input + same contract remains deterministic; the change is
intentional and attributable to the corrected authority routing, not to ordering.
