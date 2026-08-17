# ADR-0005: SI Unit Multi-Solidus Rejection and Parenthesized-Denominator Resolution

## Status

Accepted

## Context

The SI Unit capability recognizes product/quotient compounds (`UNIT (SEP UNIT){1,3}`)
and validates them against the full SI symbol lexicon (ISO 80000-1 §6.5). Two gaps
against ISO 80000-1 §6.6.2 were identified:

1. **Multi-solidus ambiguity.** The grammar accepted `kg/m/s` (more than one
   solidus at the top level, outside any parentheses) and resolved it to
   `kg/m/s`. ISO 80000-1 §6.6.2 states: *"a solidus shall not be followed by a
   multiplication sign or a division sign on the same line unless parentheses
   are inserted to avoid any ambiguity."* The legacy accept-multi-solidus
   behavior is useful for best-effort resolution but must not be the default
   for a canonicalization authority.

2. **Silent token dropping in parenthesized denominators.** `kg/(m·s²)` was
   recognized only as the inner compound `m·s²` (the symbol grammar's
   separator-aware boundaries block `kg`/`m`/`s`, and the compound grammar did
   not treat a parenthesized group as a single factor), so the pipeline returned
   `m·s2` — dropping the `kg/`. ISO 80000-1 §6.6.2 prescribes parentheses as
   *the* disambiguation, so `kg/(m·s²)` MUST resolve (not reject), capturing the
   whole expression as one compound span and preserving the parentheses.

## Decision

### Multi-solidus guard (default reject, opt-out)

- Add a contract field `allow_multi_solidus: bool = False` to `SIUnitContract`,
  plumbed through `SIUnitCapability.create_contract(allow_multi_solidus=...)`.
- `SectionCompounds.matches()` counts top-level `/` characters (outside
  parentheses). When the count exceeds 1 **and** `contract.allow_multi_solidus`
  is `False`, the compound is rejected (→ `INVALID`). When `True`, the legacy
  accept-multi-solidus behavior is preserved.
- This is a contract configuration flag, not a grammar/rule feature gate: it is
  read inside `matches()` via an `isinstance(contract, SIUnitContract)` narrowing
  (rules never read `output_format` or `include_*` flags, and never import from
  the grammar tree).

### Parenthesized-denominator resolution

- Extend the compound grammar's `_COMPOUND_RE` with a `FACTOR` that is either a
  bare `_UNIT` or `\(` + `_UNIT` + (`_SEP` + `_UNIT`)* + `\)`. A parenthesized
  factor is a single compound factor, so `kg/(m·s²)` is recognized as one span
  `[0, 9]`. Unbalanced parentheses (`kg/(m·s²`) do not match as a compound
  (the regex requires a closing `)`) and fall back to the symbol grammar — an
  acceptable, documented degradation.
- `SectionCompounds.matches()` validates each top-level factor against the full
  symbol lexicon; a parenthesized factor's inner content must itself be a valid
  compound (each inner part in the lexicon). Any invalid factor (including inside
  parentheses) rejects the compound.
- `SectionCompounds.normalize()` renders the canonical form preserving structure
  and parentheses: it walks the text tracking parenthesis depth, emits top-level
  separators verbatim, and recursively canonicalizes each factor (ASCII
  exponents via `_SUPERSCRIPT_TRANSLATE`/`_EXPONENT_SUFFIX`, `·`/`/` preserved,
  `l` → `L`). Thus `kg/(m·s²)` → `kg/(m·s2)`.

### Purity preserved

- Split patterns (`_SEPARATORS = "/·⋅"`) are kept **local** to the rule file; the
  rule does not import from `paxman/capabilities/SIUnit/grammar/...` (the
  grammar↔rules purity scan still passes). The rule imports its own
  `SIUnitContract` (same capability package, allowed by the import-linter layer
  contract) only for the `isinstance` narrowing.

## Consequences

- `kg/m/s` is now `INVALID` under the default contract (was `SUCCESS kg/m/s`).
- `kg/m/s` with `allow_multi_solidus=True` remains `SUCCESS kg/m/s`.
- `kg/(m·s²)` is now `SUCCESS kg/(m·s2)` (was `SUCCESS m·s2`, dropping `kg/`).
- Valid single units and valid non-parenthesized compounds (`kg·m/s²` →
  `kg·m/s2`, `m/s`, `N·m`, `g/cm³`, names) are unchanged.
- No other capability is affected.

## Changed files

- `paxman/capabilities/SIUnit/grammar/compound_recognition.py` — `_FACTOR` +
  extended `_COMPOUND_RE`.
- `paxman/capabilities/SIUnit/rules/iso_80000_ed2022.py` — multi-solidus guard,
  parenthesized-factor validation, recursive `normalize()`; local `_SEPARATORS`
  and helpers `_count_top_level_slash`, `_top_level_factors`, `_valid_factor`,
  `_canonical_compound`, `_canonical_factor`, `_symbol_part`, `_canonical_group`.
- `paxman/capabilities/SIUnit/contract.py` — `allow_multi_solidus` field.
- `paxman/capabilities/SIUnit/capability.py` — `create_contract` plumbing.
- `tests/capabilities/si_unit/test_rules.py`,
  `tests/capabilities/si_unit/test_capability.py` — RED→GREEN coverage.
