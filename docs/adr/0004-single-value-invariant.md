# ADR-0004: Single-Value Invariant — One Entity Per Call

## Status

Accepted

## Context

Paxman is a canonicalization *authority resolver*: it takes one ambiguous
human input and returns what the authoritative specification says that input
means, with provenance. From the outset the intended contract was that a single
`canonicalize()` call processes **one input that is expected to contain exactly
one presumed canonical value (or none at all)**.

Segmentation of free text into individual entities — "split this sentence into
the phone numbers / emails / dates it contains" — is the **caller's**
responsibility, not paxman's. Paxman operates at the *mention* level (it
normalizes a single recognized mention); it is not a document-level extractor.
When a caller passes input containing more than one entity, the honest outcome
is to **fail fast** rather than to spend recognition and validation work and
return a misleading aggregate status.

The pre-invariant behavior conflated two distinct situations under the single
`AMBIGUOUS` status:

1. **Genuine single-mention ambiguity** — one recognized span, but two or more
   authoritative specifications disagree on its canonical value (e.g.
   `01/02/2026`, which is `2026-01-02` under US order and `2026-02-01` under
   European order). This is a *correct* and useful result: paxman surfaced the
   conflict and declined to pick a winner.
2. **Segmentation violation** — the input actually contained *more than one*
   entity (e.g. `"+60164041945 and +60164041946"`), and the multiple distinct
   canonical values that surfaced are an artifact of un-split input, not a
   genuine spec conflict.

Returning `AMBIGUOUS` for case 2 wastes the caller's processing and obscures a
usage error behind a status that looks like a real domain decision. The
invariant makes the distinction explicit and enforces it.

## Decision

**The Single-Value Invariant:** A single `canonicalize()` call must resolve at
most one canonical value. The caller is responsible for ensuring the input holds
one presumed entity (or none); paxman neither segments multi-entity input nor
aggregates multiple entities into one result.

**Enforcement — fail fast, opt-in.** The invariant is enforced only for
grammars that opt in by declaring `single_value = True` on their `Grammar`
subclass (the default is `False`). Opting in asserts that the grammar resolves
one mention per `canonicalize()` call; a grammar that deliberately emits
multiple spans for a *single* logical mention — e.g. a test probe exercising the
span-bearing seam — leaves the flag `False` and is exempt from the check.

For opted-in grammars, the engine treats **overlapping or contained spans as one
mention**: candidate spans are clustered, and any two spans that share a
character position fall into the same cluster. The check then inspects the
resulting mention clusters:

- **One mention** (any number of overlapping spans), even with multiple distinct
  values → not a violation. This is genuine single-mention ambiguity (e.g.
  `01/02/2026` under US vs European order, or cross-grammar reads of one span
  such as `"€ 18 Dollar"`) and stays `AMBIGUOUS`.
- **Multiple separate mentions that all resolve to the same value** → not a
  violation: coincidentally identical mentions (e.g. two copies of the same phone
  number at different positions) still resolve to that one value via `SUCCESS`.
- **Two or more separate mentions resolving to more than one distinct value** →
  **raise `MultipleMentionsError`**, a `PaxmanError` subclass, instead of
  returning `AMBIGUOUS`.

Clustering by span overlap (rather than by grammar or by bare span count) is what
lets the invariant spare the cases it must not touch: a single mention read
several ways lands in one cluster and stays `AMBIGUOUS`, while two genuinely
separate entities — whether matched by one grammar (two phone numbers) or by
several (one via E.164, another via national) — form two non-overlapping clusters
and fail fast.

`MultipleMentionsError` is a *usage/contract* signal: it tells the caller "your
input contained more than one entity; split it and call `canonicalize()` once
per entity." It is distinct from `ContractError` (malformed contract
configuration) and from the `AMBIGUOUS` *status* (a legitimate domain result).

The error is raised at pipeline time, after recognition and before status
determination, so no partial `ExecutionResult` is produced for violating input.

**No known limitation on the dominant pattern.** Because clustering is performed
over the spans of *all* opted-in grammars, multi-entity input is caught whether its
separate instances are matched by one grammar (two phone numbers) or by several
(one via E.164, another via national). The only inputs that escape the check are
those whose grammars have not opted in (`single_value = False`), which is the
intended exemption for seam probes and any capability that elects not to assert
the invariant.

## Consequences

### Positive

- **Honest contract.** Multi-entity input fails fast instead of masquerading as
  a domain ambiguity, saving caller processing and preventing silent
  mis-aggregation.
- **`AMBIGUOUS` regains a single, precise meaning** — genuine single-mention
  spec conflict only. This removes the previous overload and makes
  status-based branching in callers reliable.
- **Caller-owned segmentation is now a hard, documented invariant** rather than
  a soft convention, so future capabilities cannot accidentally reintroduce
  multi-entity aggregation.
- **New public surface.** One new exception, ``MultipleMentionsError``, plus two
  new optional span fields: ``Candidate.span`` and ``ExecutionResult.span`` carry
  the half-open ``[start, end)`` recognition range. The ``Resolution`` enum and
  capability contracts are unchanged.

### Negative

- **Breaking change for callers** that passed multi-entity inputs and inspected
  the resulting `AMBIGUOUS` status. Those callers must now pre-split input (the
  originally intended usage) and will observe `MultipleMentionsError` instead.
  This is the desired correction, documented here so it is not treated as a
  regression.
- **Tests that asserted multi-entity → `AMBIGUOUS`** must be rewritten to either
  expect `MultipleMentionsError` (specifying the invariant) or to use
  single-entity inputs.

### Risks

- **Over-strict on coincidentally identical multi-mention input.** Two copies of
  the same value at different spans currently still resolve to `SUCCESS`. If the
  project later wants strict single-*span* enforcement (fail fast even when
  values coincide), the grouping predicate in `_enforce_single_value_invariant`
  narrows from "spans disagree on value" to "more than one span exists." This ADR
  deliberately chooses the value-based predicate to avoid surprising/pedantic
  failures on duplicated input, and records the stricter option as a known
  future lever.
- **Cross-grammar same-entity recognition must share a span.** If a future
  grammar returns a *different* span for the same logical entity, it would be
  misclassified as a second mention. The span contract (half-open,
  `raw_text == text[start:end]`, bounds-checked in `_recognize`) keeps
  same-entity matches aligned today; this invariant depends on that holding.

## Alternatives Considered

1. **Keep returning `AMBIGUOUS` for multi-entity input (status quo).** Rejected —
   it overloads `AMBIGUOUS`, hides a caller usage error, and wastes processing,
   directly contradicting the stated one-entity-per-call intent.
2. **Soft convention, no enforcement.** Rejected — without a hard signal the
   invariant is unenforceable across nine capabilities and any future extension;
   drift is inevitable.
3. **Strict single-span enforcement (fail fast on any >1 span, even identical
   values).** Rejected for now as too pedantic: duplicated identical input still
   has exactly one canonical value, which is what the invariant literally
   guarantees. Recorded as a future lever if the project prefers span-strictness.
4. **Return a multi-value aggregate result type.** Rejected — contradicts the
   single-value contract and the provenance-per-value model; segmentation
   belongs to the caller.

## References

- ADR-0001 (Clean Architecture Pipeline) — pipeline layers and `Resolution`
  status definitions this invariant refines.
- `paxman/engine/orchestrator.py` — `_collect_candidates`,
  `_enforce_single_value_invariant`, `_dedup_candidates`, `_determine_status`.
- `paxman/core/errors.py` — `MultipleMentionsError`.
- `paxman/core/domain.py` — `RecognizedRep` (carries `start`/`end` spans used for
  grouping).
