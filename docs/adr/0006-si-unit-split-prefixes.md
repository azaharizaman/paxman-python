# ADR-0006: SI Unit Split-Prefix Handling (Word Merge + Symbol Reject)

## Status

Accepted

## Context

SI prefixes are written attached to their unit ("kilogram", "kg"); a space
between a prefix and its unit is not standard SI (BIPM SI Brochure 9th ed.
§3.2). Natural/spoken input inserts whitespace in two distinct shapes, and a
naive "reject all spaced prefixes" rule is wrong because it also rejects valid
SI expressions:

1. **Word prefix split** ("kilo gram") — the prefix is a full word. A common
   natural-language form. Best-effort resolution can merge it to the canonical
   attached prefixed symbol ("kg").
2. **Symbol prefix split** ("k g") — the prefix is a symbol. ISO is unambiguous
   that a prefix symbol must bind tightly with no space, and collapsing it would
   corrupt dimensionality (e.g. "m m" → "mm" = 10⁻³ m, catastrophic). So
   symbol-prefix spacing must be rejected.

A blanket "any prefix + space = split" rule wrongly rejected `m s` (the valid
SI expression "metre second") and `m m` (which would collapse to "mm"). The
design must reject broken spaced prefixes *without* breaking valid SI
space-separated expressions.

## Decision

### Word prefix: opt-in merge (`allow_split_word_prefixes`)

- Add `allow_split_word_prefixes: bool = False` to `SIUnitContract`, plumbed
  through `SIUnitCapability.create_contract(allow_split_word_prefixes=...)`.
- The **name grammar** captures `"kilo gram"` as ONE span with shape
  `split_word_prefix`, subsuming the trailing unit so it is never emitted as a
  competing candidate.
- `SectionSplitWordPrefixes` (`rules/split_prefixes.py`) declares
  `requires_features = frozenset({"allow_split_word_prefixes"})`, so when the
  flag is off the engine drops the rule (recognition stays unvalidated →
  `INVALID`). When on, it merges ("kilo gram" → "kg") via the maintained
  `FULL_NAME_TO_SYMBOL` lookup (`NAME_TO_SYMBOL | PREFIXED_NAME_TO_SYMBOL`).
- `target_semantics = frozenset({"name_recognition"})`.

### Symbol prefix: prefix-ONLY rejected, dual-role stays units

- The **symbol grammar** captures a **prefix-ONLY** symbol split
  (`"k g"`, `"da m"`, `"µ g"`) as ONE span, shape `split_symbol_prefix`,
  subsuming the trailing unit → `INVALID` (the inner unit can never resolve to a
  wrong candidate).
- Four SI prefix symbols are also unit symbols — `m` (metre/milli), `h`
  (hour/hecto), `a` (annum/atto), `d` (day/deci). A spaced pair led by one of
  these is ambiguous between a broken prefix and a valid two-unit expression, so
  it stays two units:
  - `"m s"` → valid SI "metre second" → `AMBIGUOUS`.
  - `"m m"` → resolves to `"m"` (metre), **never** "mm" (10⁻³ m).
- The set `DUAL_ROLE_PREFIX_SYMBOLS = {"a", "d", "h", "m"}` is subtracted from
  the prefix set; the generated `SYMBOL_TOKENS` table leaks every prefix symbol
  as a standalone token, so prefix-only cannot be derived by set difference
  against it (the four dual-role symbols are subtracted explicitly instead).

### Purity preserved

- Grammars emit the split shapes; rules never import grammar token tables. The
  word-merge rule reads only the maintained name→symbol authority tables.
- `split_symbol_prefix` is handled entirely by grammar subsumption (no rule);
  the inner unit is consumed, so symbol-prefix spacing is rejected implicitly.

## Consequences

- `"kilo gram"` → `INVALID` by default; `"kg"` when
  `allow_split_word_prefixes=True`.
- `"mega hertz"` → `"MHz"` when allowed.
- `"k g"` → `INVALID` always (no flag; symbol prefixes must bind tightly).
- `"m s"` → `AMBIGUOUS` (valid SI metre second — not rejected).
- `"m m"` → `SUCCESS "m"` (metre), never "mm" (dimensionality preserved).
- No other capability is affected.

## Changed files

- `paxman/capabilities/SIUnit/notation.py` — `split_word_prefix` /
  `split_symbol_prefix` shapes.
- `paxman/capabilities/SIUnit/grammar/data/prefix_tokens.py` — 24 SI prefix
  words + symbols (longest-first).
- `paxman/capabilities/SIUnit/grammar/name_recognition.py` — `split_word_prefix`
  capture via prefix+space alternative.
- `paxman/capabilities/SIUnit/grammar/symbol_recognition.py` —
  `split_symbol_prefix` capture (prefix-only).
- `paxman/capabilities/SIUnit/contract.py` — `allow_split_word_prefixes` field.
- `paxman/capabilities/SIUnit/capability.py` — `create_contract` plumbing + rule
  registration.
- `paxman/capabilities/SIUnit/rules/split_prefixes.py` —
  `SectionSplitWordPrefixes`.
- `tests/capabilities/si_unit/test_grammar.py`,
  `tests/capabilities/si_unit/test_capability.py` — RED→GREEN coverage.
