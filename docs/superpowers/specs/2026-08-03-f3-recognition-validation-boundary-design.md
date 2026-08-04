# F3 Recognition/Validation Boundary Design

**Status:** Design approved by the requested behavior decision

## Goal

Restore the homogeneous Paxman pipeline for Country name recognition:

```text
raw input -> grammar recognition -> meaning-neutral notation
          -> provenance-backed rule validation -> candidate
```

The grammar may recognize known representations, but it must not decide which
canonical country value a representation means. Validation rules make that
decision and provide the provenance for it.

## Current Defect

`Country/grammar/name_recognition.py` currently uses dictionaries whose values
are canonical names. Inputs such as `USA`, `中国`, and `Burma` are converted to
`United States`, `China`, and `BURMA` before rules run. This duplicates semantic
tables outside the rule layer and can cause a value to receive the wrong
authority provenance. In particular, localized names can currently resolve via
the ISO name rule instead of the CLDR rule.

## Chosen Design

### Recognition

Country name grammar data becomes normalized representation key sets, not
token-to-canonical mappings. `NameGrammar` uses the key sets only to decide
whether an input is a known name representation. It returns a
`CountryNotation(shape="name", value=<recognized input>)` without replacing the
input with an English name or country code.

Syntax-only normalization remains allowed: case folding, Unicode decomposition,
punctuation removal, and whitespace normalization are not semantic decisions.
A single Country normalizer is shared by the grammar and rules so both layers
agree on lookup keys.

### Validation

Existing rule data remains authoritative:

- ISO 3166-1 owns official names, codes, and ISO synonyms.
- ISO 3166-3 owns historical names and former codes.
- CLDR owns localized names.

Rules normalize the notation value for lookup, then return the canonical value
in the requested output format. Every candidate continues to carry the
validating rule's provenance.

Recognition key sets and rule mappings remain separate files so recognition and
authority data can evolve independently. A consistency test ensures the
shipped recognition catalog does not contain a name representation that no
active rule data can validate.

### Feature Semantics

Localized names remain recognized independently of `include_localized`. Because
localized authority rules are gated by F2 metadata, a localized input with the
flag disabled is recognized but returns `INVALID`. With the flag enabled, the
CLDR rule produces the candidate and Unicode provenance. This deliberately
replaces the current false ISO-backed success for Chinese names.

Historical names retain the same rule-gated behavior: recognized input with
`include_historical=False` returns `INVALID`; enabling the feature runs the ISO
3166-3 rule.

## Alternatives Rejected

1. Deriving grammar keys directly from rule maps would eliminate drift but
   couple fast-changing recognition data to slow-changing authority data.
2. Recognizing every non-empty name would make ordinary unknown text `INVALID`
   instead of `MISSING` and would make recognition noisy.
3. Preserving grammar-side canonicalization would leave the provenance and
   duplicated-table defect unresolved.

## Scope

In scope:

- Country name grammar data, normalization, and notation behavior.
- Country ISO, CLDR, and historical rule lookup normalization and missing
  representation mappings exposed by the current grammar catalog.
- Country grammar/rule/integration tests and data-consistency coverage.
- Contributor guidance, README examples, and the F3 audit addendum.

Out of scope:

- Orchestrator changes; F1 affinity and F2 feature metadata are already in
  place.
- New public APIs or new capabilities.
- Phone separator stripping, which is syntax/presentation normalization and is
  accepted by the audit.
- Adding unproven aliases such as `M'sia` or `Malaise` without a corresponding
  provenance-backed rule.

## Verification Invariants

1. `NameGrammar` never returns a canonical country name or code in place of the
   recognized input token.
2. Each successful Country name candidate is produced by a validation rule and
   carries that rule's provenance.
3. `中国` and `马来西亚` are `INVALID` without `include_localized` and resolve
   with Unicode provenance when it is enabled.
4. Existing ISO and historical outputs remain unchanged when their rules are
   active.
5. Every shipped grammar name key is covered by at least one Country rule data
   table.
6. Same input plus same contract remains deterministic; replay hashes are not
   promised to remain byte-identical for inputs whose candidate provenance or
   route changes.
