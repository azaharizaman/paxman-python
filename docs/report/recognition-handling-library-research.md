# Recognition Handling Library Research - paxman-alternative

**Date:** 2026-08-04
**Scope:** Primary-source survey of established Python libraries for strategies to
regularize Paxman's grammar recognition handling. No source code, tests, or
configuration were modified.
**Evidence basis:** Repository source at pinned commits (permalinks below) plus
official documentation in those repositories. No secondary blog posts are used
as support.

---

## Executive Summary

Paxman's recognition layer is divergent in three cross-cutting ways, documented
as Tier 2 of `capability_homogeneity_audit.md`: (1) the canonicalization-at-
recognition spectrum (raw vs. cleaned vs. fully-resolved notation), (2) three
distinct dedup mechanisms (part-keyed set, address-keyed set, span-overlap),
and (3) inconsistent ordering semantics (document order vs. two-pass-batch vs.
explicit re-sort). `Grammar.recognize()` returns `list[NotationT]` with no
source span, and `RecognizedRep` carries no span either, so nothing downstream
can implement uniform span-based dedup or ordering.

Three libraries offer directly borrowable strategies:

| Library | Borrowable strategy | Solves | Does not solve |
|---------|--------------------|--------|----------------|
| python-stdnum | `compact()` -> `validate()` -> `format()` pipeline; shared `clean()` syntax normalization | Recognition-level normalization spectrum (Tier 2 #1); validation/formatting separation (F4-style) | Text scanning, match spans, dedup, ordering, ambiguity (single-number input) |
| phonenumbers / libphonenumber | `PhoneNumberMatcher` yielding `(start, end, raw_string)` matches; `is_possible` vs `is_valid` tiers | Match spans; non-overlapping scan; dedup-adjacent advance; two-tier validation | Ambiguity (picks one best match per span); provenance (authority is implicit in metadata) |
| Lark | Deterministic terminal precedence tuple; explicit ambiguity retention | Overlap/precedence; deterministic ordering; preserving multiple derivations | Free-text scanning (whole-input grammar model); regex opacity; performance |

**Bottom line:** adopt the phonenumbers span model and the Lark precedence-table
convention into Paxman's existing architecture; do **not** adopt stdnum's
exception-based validation, phonenumbers' single-best-match semantics, or Lark
as a replacement parser. Details and a concrete recommendation follow.

---

## 1. Current Paxman recognition state (grounding)

`Grammar.recognize(self, text: str) -> list[NotationT]` returns bare notation
values with no span information (`paxman/core/domain.py`, [domain.py](https://github.com/azaharizaman/paxman-python/blob/7c960797b7846c1052a7412b643a7d1976140e2d/paxman/core/domain.py#L180-L186)
-- commit-specific link below). `RecognizedRep` stores `notation`, `contract`,
and `grammar` but no source location, and its `__hash__` is deliberately
defensive about unhashable notation types rather than about position
([domain.py](https://github.com/azaharizaman/paxman-python/blob/7c960797b7846c1052a7412b643a7d1976140e2d/paxman/core/domain.py#L74-L94)).

Consequences visible today:

- **Per-grammar ad-hoc dedup.** The US Date grammar keeps a 4-digit match when a
  2-digit match falls inside its span, by tracking `four_digit_ranges` and
  skipping contained matches
  (`paxman/capabilities/Date/grammar/us_recognition.py`). This is one of the
  three divergent mechanisms Tier 2 #2 reports; span tracking is re-implemented
  inside every grammar that needs it, with no shared contract.
- **Engine-level value-keyed dedup only.** `_dedup_candidates` collapses on
  `(value, recognition_rule, validation_rule)` after validation
  (`paxman/engine/orchestrator.py`, lines 211-229) -- a semantic dedup, not a
  recognition-level one, and invisible to ordering.
- **Ordering is whatever each grammar returns.** The orchestrator consumes
  `recognitions` in grammar-emission order; there is no position sort
  (`_recognize` / `_collect_candidates`, lines 75-208).
- **Recognition levels vary.** Email/Date/IP emit raw tokens, Phone strips
  separators, Country name resolution previously canonicalized at recognition
  (Tier 2 #1; F3 has since moved semantic tables into rules).

These are the divergences the survey below addresses.

---

## 2. python-stdnum - clean -> validate -> format pipeline

**Primary sources:** repo `arthurdejong/python-stdnum` at commit
`7662137d48daddf3e6f0e79a69d24197c9761d1c`.

python-stdnum's entire design is a per-number pipeline with a common interface
that every module implements. The package docstring states the contract
explicitly:

```python
"""Parse, validate and reformat standard numbers and codes.

All modules implement a common interface:
>>> from stdnum import isbn
>>> isbn.validate('978-9024538270')
'9789024538270'
>>> isbn.validate('978-9024538271')
Traceback (most recent call last):
    ...
InvalidChecksum: ...
"""
```

([stdnum/__init__.py](https://github.com/arthurdejong/python-stdnum/blob/7662137d48daddf3e6f0e79a69d24197c9761d1c/stdnum/__init__.py#L19-L39))

The interface is declared as a Protocol for tooling:

```python
class NumberValidationModule(Protocol):
    """Minimal interface for a number validation module."""
    def compact(self, number: str) -> str: ...
    def validate(self, number: str) -> str: ...
    def is_valid(self, number: str) -> bool: ...
```

([stdnum/util.py](https://github.com/arthurdejong/python-stdnum/blob/7662137d48daddf3e6f0e79a69d24197c9761d1c/stdnum/util.py#L44-L55))

A representative module (IMEI) shows the four-layer split:

```python
def compact(number: str) -> str:
    """Convert the IMEI number to the minimal representation. This strips the
    number of any valid separators and removes surrounding whitespace."""
    return clean(number, ' -').strip().upper()

def validate(number: str) -> str:
    """Check if the number provided is a valid IMEI (or IMEISV) number."""
    number = compact(number)
    if not isdigits(number):
        raise InvalidFormat()
    if len(number) == 15:
        luhn.validate(number)
    elif len(number) not in (14, 16):
        raise InvalidLength()
    return number

def is_valid(number: str) -> bool:
    try:
        return bool(validate(number))
    except ValidationError:
        return False

def format(number: str, separator: str = '-', add_check_digit: bool = False) -> str:
    """Reformat the number to the standard presentation format."""
    number = compact(number)
    ...
```

([stdnum/imei.py](https://github.com/arthurdejong/python-stdnum/blob/7662137d48daddf3e6f0e79a69d24197c9761d1c/stdnum/imei.py#L54-L115))

The syntax-normalization layer is a shared utility: `clean()` strips declared
separator characters (and, in the full source, folds Unicode punctuation
variants such as dash forms into their ASCII counterparts):

```python
def clean(number: str, deletechars: str = '') -> str:
    """Remove the specified characters from the supplied number.
    >>> clean('123-456:78 9', ' -:')
    '123456789'
    """
    number = _clean_chars(number)
    return ''.join(x for x in number if x not in deletechars)
```

([stdnum/util.py](https://github.com/arthurdejong/python-stdnum/blob/7662137d48daddf3e6f0e79a69d24197c9761d1c/stdnum/util.py#L177-L197))

Validation failure is expressed as a typed exception hierarchy, all deriving
from `ValidationError` (itself a `ValueError`): `InvalidFormat`, `InvalidChecksum`,
`InvalidLength`, `InvalidComponent`
([stdnum/exceptions.py](https://github.com/arthurdejong/python-stdnum/blob/7662137d48daddf3e6f0e79a69d24197c9761d1c/stdnum/exceptions.py#L32-L64)).

### What it solves

- **Recognition-level normalization spectrum (Tier 2 #1).** The mandatory
  `compact()`/`clean()` step gives every module one place where syntax-only
  normalization happens (separator stripping, Unicode folding, case folding).
  This is exactly the "grammars emit raw tokens; one shared syntax seam" shape
  Paxman's F3 resolution already gestured at with
  `paxman/capabilities/Country/name_normalization.py`.
- **Validation/formatting separation (F4).** `validate()` returns the canonical
  minimal representation; `format()` is purely presentation and is per-module
  parameterized (`separator`, `add_check_digit`). This matches the
  already-shipped `Capability.format_value()` seam: rules emit a default
  canonical form, formatting is a separate seam.

### What it does not solve

- **Text scanning.** stdnum validates one number given as an argument; it never
  scans free text for embedded values, so it has no multi-match concept, no
  spans, no dedup, and no ordering. Paxman's `recognize(text)` is inherently a
  scanner problem, which is where the divergence lives.
- **No-raise policy compatibility.** stdnum raises on invalid input. Paxman's
  rule policy is no-raise/return-False (documented as homogeneous in the audit,
  Tier 3). Borrow the *pipeline shape*, not the exception behavior.
- **Ambiguity.** stdnum has no notion of two authorities disagreeing; a number
  is valid or it raises. It models nothing like Paxman's `AMBIGUOUS`.

---

## 3. phonenumbers / libphonenumber - matcher spans + validation tiers

**Primary sources:** repo `daviddrysdale/python-phonenumbers` (the pip
`phonenumbers` package, a direct port of `google/libphonenumber`) at commit
`5fc931803851ba2bab06701a55ece3a698cf44a7`.

### 3.1 Match spans: the `PhoneNumberMatcher` / `PhoneNumberMatch` pair

`PhoneNumberMatcher` scans free text and yields matches carrying the source
span and the raw substring:

```python
class PhoneNumberMatch(UnicodeMixin):
    """...
    A match consists of the phone number (in .number) as well as the .start
    and .end offsets of the corresponding subsequence of the searched
    text. Use .raw_string to obtain a copy of the matched subsequence.
    >>> m.raw_string
    '+1 425 882-8080'
    >>> (m.start, m.end)
    (11, 26)
    >>> text[m.start:m.end]
    '+1 425 882-8080'
    """
    def __init__(self, start, raw_string, numobj):
        self.start = start
        self.raw_string = raw_string
        self.end = self.start + len(raw_string)
        self.number = numobj
```

([python/phonenumbers/phonenumbermatcher.py](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumbermatcher.py#L730-L770))

The matcher scans with a regex, then runs a verification pass on each candidate
via `_extract_match` before accepting it:

```python
def _find(self, index):
    """Attempts to find the next subsequence ... that represents a phone number."""
    match = _PATTERN.search(self.text, index)
    while self._max_tries > 0 and match is not None:
        start = match.start()
        candidate = self.text[start:match.end()]
        candidate = self._trim_after_first_match(_SECOND_NUMBER_START_PATTERN, candidate)
        candidate_len = len(candidate)
        if candidate_len >= self._min_candidate_length:
            match = self._extract_match(candidate, start)
            if match is not None:
                return match
            self._max_tries -= 1
        # Move along
        index = start + candidate_len
        match = _PATTERN.search(self.text, index)
    return None
```

([python/phonenumbers/phonenumbermatcher.py](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumbermatcher.py#L503-L537))

After a successful match the search index is advanced past its end, so matches
are non-overlapping and in document order by construction:

```python
def has_next(self):
    if self._state == PhoneNumberMatcher._NOT_READY:
        self._last_match = self._find(self._search_index)
        if self._last_match is None:
            self._state = PhoneNumberMatcher._DONE
        else:
            self._search_index = self._last_match.end
            self._state = PhoneNumberMatcher._READY
    return (self._state == PhoneNumberMatcher._READY)
```

([python/phonenumbers/phonenumbermatcher.py](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumbermatcher.py#L701-L711))

### 3.2 Two-tier validation: `is_possible_number` vs `is_valid_number`

libphonenumber separates a cheap length/shape check from the authoritative
pattern check. The reason ladder is explicit:

```python
class ValidationResult(object):
    """Possible outcomes when testing if a PhoneNumber is a possible number."""
    IS_POSSIBLE = 0
    INVALID_COUNTRY_CODE = 1
    TOO_SHORT = 2
    TOO_LONG = 3
    IS_POSSIBLE_LOCAL_ONLY = 4
    INVALID_LENGTH = 5
```

([python/phonenumbers/phonenumberutil.py](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumberutil.py#L570-L610))

`is_possible_number_with_reason` is documented as *more lenient than
is_valid_number*: it checks only length, not starting digits, and returns a
reason code rather than a boolean
([python/phonenumbers/phonenumberutil.py](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumberutil.py#L2452-L2475)).
`is_valid_number` then verifies the parsed number against the region's actual
patterns and explicitly does *not* claim the number is in use:

```python
def is_valid_number(numobj):
    """Tests whether a phone number matches a valid pattern.

    Note this doesn't verify the number is actually in use, which is
    impossible to tell by just looking at a number itself.  It only verifies
    whether the parsed, canonicalised number is valid: ...
    """
    region_code = region_code_for_number(numobj)
    return is_valid_number_for_region(numobj, region_code)
```

([python/phonenumbers/phonenumberutil.py](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumberutil.py#L2103-L2125))

The raw -> syntax-normalized -> semantic pipeline lives in
`parse()`/`_normalize()`/`normalize_digits_only()`
([python/phonenumbers/phonenumberutil.py](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumberutil.py#L2882),
[`_normalize` L705](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumberutil.py#L705),
[`normalize_digits_only` L733](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumberutil.py#L733)),
and presentation is a separate `format_number` surface
([L1082](https://github.com/daviddrysdale/python-phonenumbers/blob/5fc931803851ba2bab06701a55ece3a698cf44a7/python/phonenumbers/phonenumberutil.py#L1082)).

### What it solves

- **Match spans (directly missing from Paxman).** `PhoneNumberMatch.start` /
  `.end` / `.raw_string` is the exact shape `RecognizedRep` lacks. With spans,
  span-overlap dedup and document-order sorting become engine responsibilities
  instead of per-grammar ad-hoc code (Tier 2 #2 and #3).
- **Dedup-by-advance / non-overlap.** Advancing `_search_index` past the last
  match's end is a simple, deterministic way to ensure one recognition per
  span within a grammar -- the same intent as the US Date grammar's manual
  `four_digit_ranges` containment check, but centralized.
- **Two-tier validation.** `is_possible` (shape) vs `is_valid` (authority
  pattern) maps onto Paxman's recognize vs validate phases: recognition is
  intentionally lenient, validation is authoritative. The `ValidationResult`
  reason codes (TOO_SHORT, INVALID_LENGTH, ...) are an idea for richer INVALID
  diagnostics without changing semantics.
- **Deterministic document order.** Matches are produced in scan order; Paxman
  could adopt "recognition output is document-ordered" as a unanimous contract.

### What it does not solve

- **Ambiguity.** The matcher is single-best per span: `_extract_match` accepts
  the first verified candidate and the search moves on. libphonenumber has no
  concept of "two authorities disagree about this span" -- the exact
  situation Paxman encodes as `AMBIGUOUS`. If Paxman naively copied the matcher,
  Date's US-vs-European ambiguity would silently collapse to one answer. Span
  dedup must therefore be **per-grammar**, never cross-grammar.
- **Provenance.** libphonenumber's metadata is a private data set; the "authority"
  is implicit and not surfaced per candidate. Paxman's provenance-first contract
  needs the per-candidate `Provenance` tuple, which the matcher model does not
  provide (and Paxman already does).
- **Overlap policy is hard-coded, not configurable.** The matcher always skips
  past the last match; there is no notion of contract-driven overlap tolerance.

---

## 4. Lark - deterministic precedence + explicit ambiguity

**Primary sources:** repo `lark-parser/lark` at commit
`240d4bcd3e207c7ed1cebd9908be41150c3ea1ab` (official docs live in the repo:
`docs/grammar.md`, `docs/parsers.md`).

### 4.1 Deterministic terminal precedence

Lark defines a strict, documented tie-break order for tokens, and implements it
as a single deterministic sort:

```python
terminals.sort(key=lambda x: (-x.priority, -x.pattern.max_width, -len(x.pattern.value), x.name))
```

([lark/lexer.py](https://github.com/lark-parser/lark/blob/240d4bcd3e207c7ed1cebd9908be41150c3ea1ab/lark/lexer.py#L629))

The documented precedence, for colliding literals, is: (1) highest terminal
priority first, (2) longest match, (3) length of the literal/pattern
definition, (4) name as final tie-break
([docs/grammar.md](https://github.com/lark-parser/lark/blob/240d4bcd3e207c7ed1cebd9908be41150c3ea1ab/docs/grammar.md#L100-L133)).
`priority` is a per-terminal signed integer with a default value of 0
([lark/lexer.py](https://github.com/lark-parser/lark/blob/240d4bcd3e207c7ed1cebd9908be41150c3ea1ab/lark/lexer.py#L119-L130)).

Rule-level priorities play the same role at parse time: with LALR they resolve
collision errors; with Earley they resolve ambiguity
([docs/grammar.md](https://github.com/lark-parser/lark/blob/240d4bcd3e207c7ed1cebd9908be41150c3ea1ab/docs/grammar.md#L255-L262)).

### 4.2 Explicit ambiguity retention vs. best-derivation

Lark's default is to pick a best derivation for you, but it also offers
`ambiguity="explicit"`, which returns every derivation under an `_ambig` node,
and a `dynamic_complete` lexer that considers every possible regexp match so
ambiguity *inside* terminals can surface:

```python
>>> p = Lark(g, ambiguity="explicit", lexer="dynamic_complete")
>>> rich.print(p.parse("ab"))
_ambig
  start
    ab
  start
    a
    b
```

([docs/grammar.md](https://github.com/lark-parser/lark/blob/240d4bcd3e207c7ed1cebd9908be41150c3ea1ab/docs/grammar.md#L158-L215))

The trade-offs are documented: Lark stores all ambiguities in a Shared Packed
Parse Forest for Earley, and offers three strategies -- (1) choose the best
derivation (default, tunable by rule priority), (2) `ambiguity='explicit'`
return all trees, (3) visit the SPPF yourself
([docs/parsers.md](https://github.com/lark-parser/lark/blob/240d4bcd3e207c7ed1cebd9908be41150c3ea1ab/docs/parsers.md#L14-L36)).

### What it solves

- **Overlap/precedence (Tier 2 #2).** A declared, engine-enforced precedence
  tuple replaces per-grammar hand-rolled overlap logic. Paxman already has the
  seed of this: `contract.active_grammars` is an ordered `Sequence[str]` (F5),
  which can serve as the deterministic grammar-precedence axis.
- **Deterministic ordering (Tier 2 #3).** Lark's sort is total -- no two tokens
  tie because name breaks every tie. Paxman's ordering contract could adopt the
  same shape: order recognitions by `(start, end, active_grammars index,
  grammar name)`, making "document order" precise and replay-safe.
- **Explicit multi-derivation retention.** `ambiguity='explicit'` is philosophically
  aligned with Paxman's no-guessing rule: rather than picking a winner, surface
  all derivations and let the caller (or the authority set) adjudicate. Paxman's
  `AMBIGUOUS` is the semantic analogue of Lark's `_ambig` node.

### What it does not solve

- **Free-text scanning.** Lark parses a *whole input* against a start rule; it
  is not built to skip arbitrary surrounding text and extract embedded values.
  Paxman grammars scan sentences like "Contact user at example dot com" for a
  substring. Forcing Paxman onto a whole-input grammar would be a re-architecture,
  not a regularization.
- **Regex opacity.** Lark explicitly cannot resolve ambiguity *inside* a
  terminal regex -- Python's regex engine silently picks one match
  ([docs/grammar.md L158](https://github.com/lark-parser/lark/blob/240d4bcd3e207c7ed1cebd9908be41150c3ea1ab/docs/grammar.md#L158-L165)).
  Paxman's grammars *are* regexes (Email, Date, IP, Phone all compile regexes),
  so Lark's in-terminal limitation is exactly where Paxman's span-overlap
  problems live. This is the strongest evidence that a parser framework alone
  does not solve the dedup problem: the ambiguity to manage is at the regex
  scan layer, which Lark delegates to `re`.
- **Performance.** `dynamic_complete` is documented as potentially much slower
  and unsuitable for open-ended terminals; not a fit for Paxman's replay-every-
  byte cost model.
- **Ambiguity is syntactic, not semantic.** Lark's `_ambig` collects different
  *parses* of the same text; Paxman's `AMBIGUOUS` collects different *authoritative
  meanings* (ISO says day-first, EN 50160 says month-first). Lark shows how to
  *keep* all derivations; it does not adjudicate authorities.

---

## 5. Compatibility with Paxman invariants

| Paxman invariant | stdnum | phonenumbers | Lark |
|------------------|--------|--------------|------|
| Deterministic / replay-safe | Yes (pure functions) | Yes (pure functions) | Yes, but `dynamic_complete` cost is input-dependent |
| No guessing | Yes (`validate` is all-or-nothing) | **No** -- matcher picks best match per span | Default is best-derivation (**no**); `ambiguity='explicit'` is **yes** |
| AMBIGUOUS preserved | N/A (no ambiguity model) | **No** -- collapses to one match | **Yes** -- retains all derivations (but syntactic) |
| Provenance-first | No provenance concept | Implicit metadata only | No provenance concept |
| No-raise rule policy | **No** -- raises typed exceptions | Returns bools | N/A |

The only library that *models* multiple valid interpretations is Lark, and only
with the non-default `ambiguity='explicit'` option. That is the single most
important compatibility finding: **any borrowed strategy that collapses multiple
recognitions of one span to a single winner is incompatible with Paxman's
AMBIGUOUS semantics.** Dedup and precedence must operate within one grammar's
output, never across grammars, so Date's US/European pair still yields two
candidates for `01/02/2026`.

---

## 6. Recommendation

Adopt a **span-first recognition contract** and a **shared syntax-normalization
seam**, regularized by an engine-enforced precedence order. Concretely:

1. **Carry source spans in `RecognizedRep`** (add `start: int`, `end: int`,
   `raw_text: str`, mirroring `PhoneNumberMatch`). Keep `Grammar.recognize()`
   returning `list[NotationT]` but make the span available at the seam the
   engine already owns (`RecognizedRep` construction). Addresses Tier 2 #2 and
   #3; without spans neither uniform dedup nor uniform ordering is possible.
2. **Unify dedup as per-grammar span-overlap, engine-enforced.** Replace the
   three divergent mechanisms (part-keyed, address-keyed, span-overlap) with one
   rule: within a single grammar's output, drop a recognition whose span is
   contained in an earlier, longer recognition of the same grammar (the US Date
   containment check, generalized); never dedup across grammars. Keep
   `_dedup_candidates` value-keyed dedup as the replay-hash safety net. The
   phonenumbers "advance past last match" scan and Lark's precedence tuple are
   the models; the cross-grammar carve-out is what preserves AMBIGUOUS.
3. **Declare deterministic ordering as a total order.** Engine sorts
   recognitions by `(start, end, active_grammars index, grammar name)` -- the
   Lark terminal-sort pattern with a total tie-break. This makes "document
   order" a real, unanimous contract (Tier 2 #3) and is replay-safe by
   construction.
4. **Standardize the recognition level at "raw tokens + shared syntax seam".**
   Grammars emit raw recognized tokens; a capability-level syntax-normalization
   helper (the stdnum `clean()`/`compact()` idea, already partially realized as
   `Country/name_normalization.py`) does case folding, Unicode cleanup, and
   separator stripping; semantic mapping stays in rules (Tier 2 #1; reinforces
   the F3 resolution). Optionally expose a phonenumbers-style lenient/authoritative
   two-tier validation as a *diagnostic* (reason codes), not a behavior change.
5. **Keep the existing `format_value` seam and the no-raise rule policy.**
   Validation/formatting separation is already shipped (F4, 2026-08-04) and
   matches stdnum's `validate`/`format` split; do not adopt stdnum's exception
   model or phonenumbers' single-best-match semantics. Do **not** adopt Lark as
   a parser engine: Paxman's grammars are regex scanners over free text, Lark's
   whole-input grammar model and in-terminal regex opacity do not apply, and the
   audit's RuleStrategy findings already flag that a decorative parser layer is
   worse than none.

**Recommended next step** (no code yet): a design ADR specifying the
`RecognizedRep` span fields, the per-grammar span-overlap dedup rule, and the
`(start, end, active_grammars index, name)` ordering contract, validated against
the 782-test suite's replay-hash snapshot gate before any implementation.

---

## 7. Source register

| Library | Repository | Commit | Key files |
|---------|-----------|--------|-----------|
| python-stdnum | https://github.com/arthurdejong/python-stdnum | 7662137d | `stdnum/__init__.py`, `stdnum/util.py`, `stdnum/imei.py`, `stdnum/exceptions.py` |
| phonenumbers | https://github.com/daviddrysdale/python-phonenumbers | 5fc93180 | `python/phonenumbers/phonenumbermatcher.py`, `python/phonenumbers/phonenumberutil.py` |
| Lark | https://github.com/lark-parser/lark | 240d4bcd | `docs/grammar.md`, `docs/parsers.md`, `lark/lexer.py` |
| Paxman (local) | https://github.com/azaharizaman/paxman-python | 7c960797 | `paxman/core/domain.py`, `paxman/engine/orchestrator.py`, `capability_homogeneity_audit.md` |
