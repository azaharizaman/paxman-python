# ADR-0003: Semantic Affinity — Route Rules by Meaning, Not Grammar Name

## Status

Accepted

## Context

Paxman separates Recognition from Validation: grammars produce span-bearing
`RecognitionMatch`es carrying a notation; rules validate that notation against
an authoritative specification and emit the canonical value with provenance.
The two layers are joined by **grammar-name affinity**: `Rule.target_grammars`
declares the grammar names whose output the rule understands, and the engine
routes a recognition only to rules that name its producing grammar.

This affinity is enforced at three engine sites and one domain site:

- `Rule.__init_subclass__` requires a non-empty `target_grammars`
  `frozenset[str]` at class-definition time (`paxman/core/domain.py`).
- `_validate_affinity` fails fast with `ContractError` when a rule names a
  grammar absent from the composed set (`paxman/engine/orchestrator.py`).
- `_collect_candidates` routes each recognition to rules via
  `grammar_name not in rule.target_grammars`.
- `_activated_rules` opts a community rule in only when the contract names one
  of its `target_grammars` in `extra_grammars`.

The affinity exists to prevent the F1 defect (the cartesian product: every rule
validating every grammar's matches regardless of whether the rule's authority
covers that representation), which the homogeneity audit ranked as defect #1
and which PR #19 fixed via `target_grammars` + the one-line orchestrator
filter.

The name-based binding has a structural cost: **a new grammar is effective
only when a rule file is edited.** The shipped proof is the slash-ISO grammar
(`SlashISODateGrammar`, `YYYY/MM/DD`): it shares ISO 8601's position mapping
and canonical form, but activating it required extending the ISO rule's
`target_grammars` frozenset by hand. The grammar author's work was complete at
`RecognitionMatch`; the rule edit exists only to declare what the grammar
cannot declare today — *what its notation means*.

This violates the responsibility boundary the grammar is otherwise held to.
Grammars are prohibited from importing rule-layer data and from assigning
canonical meaning; they are required to end at the span-bearing match. But the
one thing that would let a grammar stand alone — a statement of its own
semantics — has no home in the `Grammar` ABC, which carries only `name`.

The same-notation-type hazard that motivates affinity is real and must
survive any redesign: `DateNotation(N1, N2, N3)` means `(year, month, day)`
from `iso8601_recognition` but `(month, day, year)` from `us_recognition`.
Affinity must remain *explicit*, it must remain fail-fast on dangling
declarations, and it must remain deterministic per contract.

## Decision

Replace grammar-name affinity with **semantic affinity**: a rule targets the
*meaning* of the notations it validates, and each grammar declares that
meaning. `Rule.target_grammars` is **replaced** by
`Rule.target_semantics`; `Grammar` gains a required `semantics` identifier.

### 1. `Grammar.semantics` — the meaning claim

`Grammar` (in `paxman/core/domain.py`) gains a required class attribute:

```python
class Grammar(ABC, Generic[NotationT]):
    """Base class for recognition grammars."""

    name: str
    semantics: ClassVar[str]
```

- `semantics` is a stable identifier for the *meaning* the grammar's notation
  carries — what the notation says, not how it is written.
- It is enforced by a new `Grammar.__init_subclass__` mirroring `Rule`'s
  metadata enforcement: non-empty `str`, required at class-definition time.
- It is a **claim**, not an interpretation: the grammar still never imports
  rule-layer data, never validates, and never maps tokens to canonical values.
  The semantic purity boundary is unchanged; `semantics` only names the
  meaning the grammar already produces.
- Example: `iso8601_recognition` and `slash_iso_recognition` both declare
  `semantics = "iso8601_calendar_date"`; `us_recognition` declares
  `semantics = "us_calendar_date"`.

### 2. `Rule.target_semantics` — replace `target_grammars`

`Rule.target_grammars: ClassVar[frozenset[str]]` becomes
`Rule.target_semantics: ClassVar[frozenset[str]]` with identical enforcement
(non-empty `frozenset[str]`, checked by `Rule.__init_subclass__`). The ISO
rule's declaration collapses from two grammar names to one meaning:

```python
# before
target_grammars = frozenset({"iso8601_recognition", "slash_iso_recognition"})
# after
target_semantics = frozenset({"iso8601_calendar_date"})
```

### 3. Engine routing — three one-line sites

- `_validate_affinity`: validate `rule.target_semantics` against the composed
  **semantics set** `{g.semantics for g in all_grammars}` instead of the
  grammar-name set. Dangling semantics still fail fast with `ContractError`.
- `_collect_candidates`: route via
  `recognition.grammar.semantics not in rule.target_semantics`. The engine
  builds a `semantics_by_name` map at composition time so the producing
  grammar's semantics is resolvable from the `RecognizedRep`'s
  `GrammarRule.grammar_name`.
- `_activated_rules`: a community rule activates when the contract names, in
  `extra_grammars`, any grammar whose `semantics` is in the rule's
  `target_semantics` — the opt-in discipline is unchanged, keyed on meaning.

### 4. Provenance and dedup stay name-based

`Candidate.recognition_rule` continues to record the **grammar name**
(`grammar_name`), and `_dedup_candidates` continues to collapse on
`(value, recognition_rule, validation_rule)`. `semantics` is routing metadata;
the grammar name remains the audit identity of the recognition. Provenance
output is byte-identical to today for every existing input.

### 5. What a grammar-only addition now means

Adding a grammar whose meaning is already shipped becomes a single-file
change: the grammar file itself. It declares `semantics = "<existing id>"`
and is validated by the existing rule automatically — no rule edit, no
`target_*` change. This is the property that makes the grammar's
responsibility end at the `RecognitionMatch` (plus its one-word meaning
claim). A genuinely new meaning still requires a new rule: the canonical
value and provenance must come from an authoritative specification, and that
is rule territory by design.

## Migration

1. **Phase 1 — behavior-preserving rename.** Every shipped grammar declares
   `semantics = "<its own name>"`; every rule's `target_grammars` is renamed
   `target_semantics` with the identical set. Routing keyed on semantics with
   `semantics == name` is byte-identical to name routing; the full pre-PR gate
   (ruff, pyright, import-linter, pytest) stays green with no test edits.
   Community rule metadata (`target_grammars` → `target_semantics`) is a
   breaking rename at 0.x, acceptable under the same policy as ADR-0002.
   *Post-ADR correction:* during Migration #4 the four date grammars'
   digit-lookaround bounds (`(?<!\d)...(?!\d)`) were tightened so digit-glued
   ids like `12026-01-15` no longer partially match at offset 1. Deliberate
   and post-ADR; Phase 1 is byte-identical for every other input class.
2. **Phase 2 — coalescing.** Grammars that share meaning declare a common
   `semantics` id (e.g. both Date ISO grammars → `"iso8601_calendar_date"`),
   and the affected rules' `target_semantics` coalesce to the single id. Same
   behavior, simpler declarations; each coalescing step is verified by the
   per-capability pipeline tests.
3. **Consistency guard.** A new test asserts that every grammar declaring the
   same `semantics` emits notations with identical field mapping and
   canonicalization expectations — the F1-style protection against
   same-semantics/different-meaning collisions. This is a test-time
   guarantee, like the existing homogeneity tests; the engine does not
   introspect notation semantics at runtime.
4. **Docs sweep.** `HOW_TO_ADD_NEW_GRAMMAR.md` (Step 4 becomes: declare a
   shipped `semantics` and stop, or add a rule for a new meaning),
   `HOW_TO_ADD_NEW_CAPABILITY.md`, `ARCHITECTURE.md`, `README.md` (Community
   Extensions section), `CONTEXT.md`, the capability `AGENTS.md` conventions,
   and `capability_homogeneity_audit.md`. Historical capability plans and
   research docs are left as historical records (ADR-0002 precedent).

## Consequences

### Positive

- **Grammar-only additions become effective for existing meanings.** The
  slash-ISO case collapses from a two-file change (grammar + rule edit) to a
  one-file change (grammar only). The grammar's responsibility now ends at
  the `RecognitionMatch` plus its meaning claim.
- **Rules declare intent, not implementation.** `target_semantics =
  {"us_calendar_date"}` says what the rule understands; recognition
  implementations can be refined or added without rule churn.
- **The community seam widens.** A downstream user registers a grammar
  (via `register_grammar` + `extra_grammars` opt-in) whose meaning is already
  validated, and shipped rules validate it — no `register_rule` needed.
  Recognition becomes the pluggable half of the seam.
- **F1 protection preserved.** Affinity stays explicit, deterministic, and
  fail-fast on dangling declarations — the cartesian-product defect cannot
  return via routing.
- **Provenance output unchanged.** `recognition_rule`/`validation_rule`
  attribution and candidate dedup are untouched; existing consumers see no
  behavioral difference in Phase 1.

### Negative

- **Breaking community API change.** Community rules must rename
  `target_grammars` → `target_semantics`. Acceptable at 0.x; semver-major at
  >= 1.0.
- **New required metadata on every grammar.** `semantics` is a contributor
  touch point in `HOW_TO_ADD_NEW_GRAMMAR.md`; a grammar without it fails at
  class-definition time rather than at runtime.
- **Wrong `semantics` declarations are silent until a test catches them.** A
  grammar claiming a shipped `semantics` id with divergent field mapping
  would route to the wrong rule and produce a wrong-but-plausible canonical
  value. The consistency guard is the mitigation; it is test-time, not
  runtime.

### Risks

- **Same-semantics, different-meaning collisions.** Two grammars declaring the
  same `semantics` with divergent field mapping silently mis-canonicalize.
  Mitigation: the consistency-guard test per `semantics` id (Migration #3),
  and a documented convention that `semantics` is a *semantic contract*: all
  grammars claiming it must agree on notation field order and canonical form.
- **Coalescing drift during Phase 2.** Coalescing `target_semantics` sets must
  never widen the set of meanings a rule validates. Mitigation: each
  coalescing step runs the per-capability pipeline tests; the migration lands
  one capability at a time.
- **Incomplete docs sweep.** 55 files referenced `target_grammars` at plan
  time (pre-migration inventory; the plan's D10 re-count is authoritative —
  superseded by the completed Migration #4 sweep). Mitigation: this ADR lands
  before code; the sweep is enumerated in Migration #4.

## Alternatives Considered

1. **Keep `target_grammars` (status quo).** Rejected — a new grammar is
   effective only when a rule file is edited, even when the grammar's meaning
   is already validated. The slash-ISO one-line rule extension is the proof;
   the coupling is name-based, not meaning-based, so it forces rule churn for
   pure recognition additions.
2. **Additive `target_semantics` alongside `target_grammars` (OR routing).**
   Rejected — two routing dimensions, ambiguous precedence, and a rule could
   silently widen its authority by naming a semantics id without removing
   stale grammar names. Replacement keeps a single, auditable affinity
   declaration.
3. **Type-only routing.** Rules accept any notation of their declared type.
   Rejected — the same `DateNotation` type carries different meanings per
   grammar (US vs ISO field mapping); this is the F1 defect's failure mode,
   not a fix for it.
4. **`same_semantics_as` pointer on the grammar.** A grammar references an
   existing grammar whose meaning it shares. Rejected — requires equivalence
   classes with canonical representatives, and validation of a reference
   graph (acyclicity, consistency); a self-contained `semantics` id names the
   meaning directly and avoids the representative problem.
5. **Infer meaning from the notation type.** Rejected — impossible in the
   general case; meaning is not recoverable from `DateNotation(N1, N2, N3)`
   without knowing the producing grammar's field mapping. `semantics` is the
   minimal explicit claim that makes the inference sound.

## References

- ADR-0001 — Key Design Decisions #1 (Separate Recognition from Validation),
  #2 (Notation as Internal Contract) — reaffirmed; the grammar purity
  boundary this ADR extends
- ADR-0002 — breaking-change-at-0.x policy precedent
- `docs/superpowers/plans/2026-08-03-f1-grammar-rule-affinity.md` — the F1
  defect and the `target_grammars` fix this ADR generalizes to semantics
- `capability_homogeneity_audit.md` — F1 cartesian-product defect (#1), the
  audit this ADR builds on
- `paxman/core/domain.py` — `Rule.__init_subclass__` (`target_grammars`
  enforcement, replaced), `Grammar` (gains `semantics`), `GrammarRule`
- `paxman/engine/orchestrator.py` — `_validate_affinity`,
  `_collect_candidates`, `_activated_rules` (routing sites, changed)
- `paxman/core/extensions.py` — `register_grammar` / `register_rule`
  community seam (activation keyed on semantics)
- `HOW_TO_ADD_NEW_GRAMMAR.md` — Step 4 (rule-affinity requirement, replaced
  by the semantics declaration)
- `README.md` — Community Extensions section (activation rule reworded)
