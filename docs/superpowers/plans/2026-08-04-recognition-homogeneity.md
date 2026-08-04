# 2026-08-04 — Recognition Homogeneity: one span-bearing pipeline for all capabilities

> **For agentic workers: REQUIRED SUB-SKILL: `superpowers:writing-plans` workflow.** This is an implementation plan, not a design doc. Execute it task-by-task with `superpowers:executing-plans` or `superpowers:subagent-driven-development`, TDD-first (Red-Green-Refactor), with a commit after every task. Assume the engineer executing this plan has zero codebase context; every file change below is self-contained. Do NOT skip the interim-state warning in Task 2 — it is intentional and bounded.

## Goal

Make recognition **homogeneous across all capabilities** — and set the template for future capabilities — by giving every grammar exactly one contract with the engine:

1. **Every grammar emits span-bearing `RecognitionMatch` objects** (`notation`, `start`, `end`, `raw_text`) instead of bare notations. Positions are produced by the grammar (only it can see its own regex matches) and consumed by the engine (only it can order/dedup globally).
2. **The engine owns ALL cross-match policy**: within-grammar overlap dedup ("longer wins") and a total document order `(start, end, active_grammars index, grammar name)`.
3. **Candidate set is byte-identical** — the five baseline replay hashes MUST NOT change (this is the migration's correctness gate, and it is why every existing grammar's *values* stay exactly as they are today).
4. **`HOW_TO_ADD_NEW_CAPABILITY.md` and `ARCHITECTURE.md` are updated** so future capabilities inherit this contract from the first grammar they write.

This deletes the four divergent mechanisms found in the research memo (`docs/report/recognition-handling-library-research.md`) — Email's part-keyed `seen` set + two-pass batching, Phone's value-keyed `dedup()` helper, Date's span-containment re-checks, and the per-capability ordering leftovers — and replaces them with one engine-enforced mechanism.

## Architecture

```
Grammar.recognize(text) -> list[RecognitionMatch]   # ONE contract, 16 grammars
                                     │
        engine._recognize(): per-grammar _dedup_spans()  (contained spans dropped, longer wins)
                                     │
        engine sort: (start, end, active_grammars index, grammar name)   # document order
                                     │
        RecognizedRep(notation, contract, grammar, start, end, raw_text)
                                     │
        engine._collect_candidates() → _dedup_candidates()   # UNCHANGED (value-keyed safety net)
                                     │
        ExecutionResult / VersionStamp.replay_hash   # byte-identical to today
```

**Responsibility split (the invariant):**
| Concern | Owner |
|---|---|
| Produce notations + their spans | Grammar (per-match position) |
| Syntax-only normalization (strip separators, uppercase) | Grammar |
| Containment dedup within one grammar | Engine (`_dedup_spans`, never cross-grammar) |
| Total ordering of recognitions | Engine (`(start, end, index, name)`) |
| Semantic validation, canonical value, provenance | Rules (untouched) |
| Candidate-value dedup safety net | Engine `_dedup_candidates` (untouched) |

**Why never cross-grammar dedup:** `01/02/2026` is recognized by BOTH the US and European grammars at the SAME span with different meanings. Cross-grammar dedup would silently destroy that ambiguity. Per-grammar dedup keeps both recognitions, the rules produce two distinct canonical values, and status is correctly `AMBIGUOUS`.

## Tech Stack

- Python 3.11, `uv` (run everything through `uv run`)
- `pytest` (782-test suite), markers: `unit`, `capability`, `integration`, `e2e`, `property`
- `pyright` strict, `ruff` (E/W/F/I/N/UP/B/SIM), `import-linter`, `hypothesis`
- Test-only probe capabilities follow the house pattern in `tests/integration/test_format_value_seam.py` (in-file classes, `_clean_registry` fixture, `run_capability()`).

## Behavioral Contract

- `Grammar.recognize(text) -> list[RecognitionMatch[NotationT]]` is THE grammar interface. No grammar returns bare notations anymore.
- `RecognitionMatch` invariants (enforced in `__post_init__`): `0 <= start <= end`; `len(raw_text) == end - start`.
- Engine dedups matches ONLY within a single grammar's output: a match fully contained in another match's `[start, end)` from the same grammar is dropped; the longer match wins; exact ties keep first-seen.
- Engine orders recognitions by `(start, end, active_grammars index, grammar name)` — a total order, so "document order" is unanimous across capabilities.
- The candidate set is unchanged: the five default replay hashes in Task 1 are a snapshot gate that must stay green through Task 9.
- Grammars do syntax only (extraction + separator/case normalization). No grammar imports from `rules`; no rule imports from `grammar` (purity gate, Task 8). Semantic decisions stay in rules with provenance.
- `_dedup_candidates` (value, recognition_rule, validation_rule) is untouched — it is the candidate-level safety net that makes grammar-level value dedup removable.
- Candidate ORDER within `ExecutionResult.candidates` may change (it follows recognition order). The replay hash sorts candidates, so hashes are unaffected; no test pins multi-candidate order (verified 2026-08-04).
- NOT in scope (deferred, recorded in `capability_homogeneity_audit.md` Task 8): a shared stdnum-style `clean()` syntax seam, moving Country `.upper()` into it, and adopting Lark. The `.upper()` stays in the alpha-2/alpha-3 grammars — it is syntax normalization and must remain to preserve notation values and hashes.

## Files And Responsibilities

| File | Responsibility |
|---|---|
| `paxman/core/domain.py` | Add `RecognitionMatch`; change `Grammar.recognize` signature; add span fields to `RecognizedRep` |
| `paxman/core/__init__.py` | Export `RecognitionMatch` from `paxman.core` alongside `Grammar`, `RecognizedRep`, etc. |
| `paxman/engine/orchestrator.py` | Rewrite `_recognize`; add `_dedup_spans`; engine owns dedup + total order |
| `paxman/capabilities/*/grammar/*.py` (16 files) | Migrate `recognize()` to emit `RecognitionMatch` |
| `paxman/capabilities/Phone/grammar/common.py` | Delete `dedup()` (dead code); keep `strip_separators` |
| `tests/integration/test_default_replay_hashes.py` | NEW: literal baseline hashes (Task 1) |
| `tests/integration/test_recognition_seam.py` | NEW: probe-capability seam tests (Task 2) |
| `tests/unit/test_recognized_rep.py` | Span fields on 9 constructors + new span tests (Task 2) |
| `tests/capabilities/{date,email,country,ip,phone}/test_grammar.py` | `.notation` accessor + span tests (Tasks 3–7) |
| `tests/property/test_grammar_properties.py` | Add `RecognitionMatch` type assertion (Task 8) |
| `tests/unit/test_grammar_semantic_purity.py` | NEW: AST import-boundary guard (Task 8) |
| `HOW_TO_ADD_NEW_CAPABILITY.md` | Rewrite Step 4 "Create a Grammar" to the span contract (Task 8) |
| `ARCHITECTURE.md` | Add recognition-pipeline contract (spans/dedup/order) (Task 8) |
| `capability_homogeneity_audit.md` | Mark Tier 2 resolved; record deferred syntax seam (Task 8) |

---

## Task 1 — Lock the baseline: literal replay-hash snapshot

**Why:** the migration must be hash-transparent. Snapshot the five hashes BEFORE any change so Task 9 can prove the candidate set is byte-identical.

### Step 1 — Create `tests/integration/test_default_replay_hashes.py`

```python
"""Baseline replay-hash snapshot.

The replay_hash is the engine's behavioral contract: any pipeline change
that alters the candidate set, provenance set, or serialized contract
shifts a hash and fails here. Literals captured 2026-08-04 on main
(verified byte-identical to the 2026-08-04-centralize-output-format
migration).

The recognition-homogeneity migration MUST land with zero hash changes:
the candidate set it produces is identical to today's. Update these
literals only as an intentional, reviewed consequence of a pipeline change.
"""

import pytest

import paxman
from paxman.capabilities.Country.capability import CountryCapability
from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.IP.capability import IPCapability
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution

# NOTE: IP is NOT auto-registered in paxman/capabilities/__init__.py
# (which exports only Country, Date, Email, Phone) — each case registers
# its capability explicitly.

BASELINE_HASHES = {
    "date": "cb2e67023a8c74e5eb76913a00eb1756a7ed76c3a3c8bb553a588ac5d03c65b4",
    "country": "3489ca17221e11f98068a4c5e9306a0ebfb06b857bcbaa137fdd3f14a761a70b",
    "email": "dccb1dec8fbd851c360ecb5feb0ed321a00a2ee6931ed2ba6505c0f92f9ffa31",
    "ip": "6709b8b4ca35a7fec0ddc80bf13325af0dfbcf79d17577955a2a8ae41ad8c71a",
    "phone": "c5aec207bcfb3d061585b789ccb3d6cd98d394bffbe0f81c4fcd481132647f3d",
}

CASES = [
    ("date", DateCapability, "2026-07-26"),
    ("country", CountryCapability, "United States"),
    ("email", EmailCapability, "user@example.com"),
    ("ip", IPCapability, "192.168.1.1"),
    ("phone", PhoneCapability, "+1 555 123 4567"),
]


@pytest.fixture(autouse=True)
def _fresh_registry():
    """Reset the registry before each case (mirrors test_format_value_seam)."""
    reset_registry()
    yield


@pytest.mark.integration
@pytest.mark.parametrize(
    ("key", "capability_cls", "input_text"),
    CASES,
    ids=[key for key, _, _ in CASES],
)
def test_default_replay_hash_matches_baseline(key, capability_cls, input_text):
    register_capability(capability_cls())
    contract = capability_cls.create_contract()
    result = paxman.canonicalize(input_text, contract)
    assert result.status == Resolution.SUCCESS
    assert result.version_stamp.replay_hash == BASELINE_HASHES[key]
```

### Step 2 — Verify

```bash
uv run pytest tests/integration/test_default_replay_hashes.py -q
```

All 5 pass (green pre-change). Then:

```bash
git add tests/integration/test_default_replay_hashes.py
git commit -m "test: lock default replay-hash baseline before recognition homogeneity"
```

---

## Task 2 — Domain + engine: the span-bearing contract (TDD)

**⚠️ Interim-state warning (READ FIRST):** this task changes the `Grammar` ABC signature and the engine. After it lands, every test that runs a REAL capability through `run_capability()`/`canonicalize()` fails (the un-migrated grammars still return bare notations, and the new engine reads `.start`/`.end`/`.raw_text`). This is EXPECTED and bounded: Tasks 3–7 migrate the grammars one capability at a time, and the suite returns fully green at Task 9. Do NOT "fix" the failures in this task. The seam tests and unit tests below are the only things that must be green here.

### Step 1 (RED) — Create `tests/integration/test_recognition_seam.py`

Probe capability with two overlapping grammars (modeled exactly on `test_format_value_seam.py`). Two rules tag each recognition's value with its producing grammar (`L:`/`S:`), so the tests observe — via `ExecutionResult.candidates` — exactly which recognitions survived engine dedup and ordering.

```python
"""Engine seam tests for the span-bearing recognition contract.

These tests pin the NEW recognition pipeline:
1. The engine dedups overlapping matches WITHIN one grammar (longer wins);
2. The engine NEVER dedups across grammars (two grammars agreeing on the
   same span are both preserved — this is what keeps AMBIGUOUS observable);
3. The engine emits recognitions in the total order
   (start, end, active_grammars index, grammar name) — document order.

The probe capability is deliberately minimal. Its long grammar scans with
TWO patterns ('AAAA' and 'AA') so its own matches can overlap — the same
shape as the US/European date grammars — and the short grammar scans with
one. Two rules tag each recognition's value with its producing grammar
('L:'/'S:'), making the surviving recognitions observable via candidates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pytest

from paxman.core.capability import Capability
from paxman.core.contract import Contract
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import (
    Grammar,
    Provenance,
    RecognitionMatch,
    Resolution,
    Rule,
    RuleStrategy,
)
from paxman.engine.orchestrator import run_capability


@dataclass(frozen=True)
class _ProbeNotation:
    value: str


class _ProbeLongGrammar(Grammar[_ProbeNotation]):
    """Scans with two patterns, so its own matches can overlap.

    On 'AAAA' this emits the AAAA match PLUS two contained AA matches —
    the engine's within-grammar containment dedup is what collapses them.
    """

    name = "probe_long"
    _patterns = (re.compile(r"AAAA"), re.compile(r"AA"))

    def recognize(self, text: str) -> list[RecognitionMatch[_ProbeNotation]]:
        matches = []
        for pattern in self._patterns:
            for m in pattern.finditer(text):
                matches.append(
                    RecognitionMatch(
                        notation=_ProbeNotation(m.group(0)),
                        start=m.start(),
                        end=m.end(),
                        raw_text=m.group(0),
                    )
                )
        return matches


class _ProbeShortGrammar(Grammar[_ProbeNotation]):
    """Recognizes 'AA' only."""

    name = "probe_short"

    def recognize(self, text: str) -> list[RecognitionMatch[_ProbeNotation]]:
        return [
            RecognitionMatch(
                notation=_ProbeNotation(m.group(0)),
                start=m.start(),
                end=m.end(),
                raw_text=m.group(0),
            )
            for m in re.finditer(r"AA", text)
        ]


class _LongRule(Rule[_ProbeNotation]):
    """Tag values produced from probe_long recognitions as 'L:...'."""

    name = "long_rule"
    strategy = RuleStrategy.REGEX
    provenance = Provenance(
        authority="test",
        specification_name="test",
        kind="test",
        reference_url="https://test",
        version=None,
        lifecycle="active",
        publication_year=2024,
    )
    citation = "test"
    target_grammars = frozenset({"probe_long"})
    requires_features = frozenset()

    def matches(self, notation: _ProbeNotation, contract: Contract) -> bool:
        return True

    def normalize(self, notation: _ProbeNotation, contract: Contract) -> str:
        return f"L:{notation.value}"


class _ShortRule(Rule[_ProbeNotation]):
    """Tag values produced from probe_short recognitions as 'S:...'."""

    name = "short_rule"
    strategy = RuleStrategy.REGEX
    provenance = Provenance(
        authority="test",
        specification_name="test",
        kind="test",
        reference_url="https://test",
        version=None,
        lifecycle="active",
        publication_year=2024,
    )
    citation = "test"
    target_grammars = frozenset({"probe_short"})
    requires_features = frozenset()

    def matches(self, notation: _ProbeNotation, contract: Contract) -> bool:
        return True

    def normalize(self, notation: _ProbeNotation, contract: Contract) -> str:
        return f"S:{notation.value}"


class _ProbeCapability(Capability[_ProbeNotation]):
    name = "probe"
    version = "0.1.0"

    def get_grammars(self) -> list[Grammar[_ProbeNotation]]:
        return [_ProbeLongGrammar(), _ProbeShortGrammar()]

    def get_rules(self) -> list[Rule[_ProbeNotation]]:
        return [_LongRule(), _ShortRule()]


class _ProbeContract:
    """Minimal contract; default active_grammars order is long=0, short=1."""

    def __init__(self, active_grammars: list[str] | None = None) -> None:
        self._active_grammars = active_grammars or ["probe_long", "probe_short"]

    @property
    def capability_name(self) -> str:
        return "probe"

    @property
    def active_grammars(self) -> list[str]:
        return self._active_grammars

    @property
    def excluded_rules(self) -> list[str]:
        return []

    @property
    def pinned_rules(self) -> list[str] | None:
        return None

    @property
    def year(self) -> int | None:
        return None

    @property
    def output_format(self) -> str | None:
        return None

    def as_dict(self) -> dict[str, object]:
        return {"capability_name": "probe"}


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


class TestRecognitionSeam:
    @pytest.mark.integration
    def test_engine_dedups_contained_spans_within_grammar(self) -> None:
        """'AA' runs inside 'AAAA' are dropped; the longer match wins.

        Only probe_long is active. It emits AAAA(0,4), AA(0,2), AA(2,4);
        the engine's per-grammar containment dedup keeps just the longest.
        """
        register_capability(_ProbeCapability())
        result = run_capability("AAAA", _ProbeContract(["probe_long"]))

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "L:AAAA"
        assert [c.value for c in result.candidates] == ["L:AAAA"]

    @pytest.mark.integration
    def test_engine_keeps_cross_grammar_matches_at_same_span(self) -> None:
        """Two grammars matching the same span are BOTH preserved.

        This is the ambiguity-preserving invariant: '01/02/2026' (US vs
        European) must produce two recognitions, not one. Both grammars
        match AA at (0,2); per-grammar dedup keeps both, the two rules
        yield distinct tagged values, and status is AMBIGUOUS.
        """
        register_capability(_ProbeCapability())
        result = run_capability("AA", _ProbeContract())

        assert result.status == Resolution.AMBIGUOUS
        assert {c.value for c in result.candidates} == {"L:AA", "S:AA"}

    @pytest.mark.integration
    def test_engine_orders_by_document_order_with_grammar_index_tiebreak(
        self,
    ) -> None:
        """Recognitions are sorted by (start, end, grammar index, name).

        For 'AA AAAA' (both grammars active):
        - probe_long emits AAAA(3,7), AA(0,2), AA(3,5), AA(5,7); its own
          contained AA runs are dropped, leaving (0,2) and (3,7).
        - probe_short emits AA(0,2), AA(3,5), AA(5,7); none of its matches
          contains another, so all three survive — per-grammar dedup never
          touches another grammar's matches, even inside AAAA's span.
        Sorted: (0,2,0,probe_long) < (0,2,1,probe_short) < (3,5,1,probe_short)
        < (3,7,0,probe_long) < (5,7,1,probe_short).
        """
        register_capability(_ProbeCapability())
        result = run_capability("AA AAAA", _ProbeContract())

        assert [c.value for c in result.candidates] == [
            "L:AA",
            "S:AA",
            "S:AA",
            "L:AAAA",
            "S:AA",
        ]

    @pytest.mark.integration
    def test_grammar_emits_span_bearing_matches(self) -> None:
        """The ABC contract: recognize() returns matches with real spans."""
        grammar = _ProbeLongGrammar()
        matches = grammar.recognize("x AAAA y")
        # The grammar emits every match with its span: AAAA(2,6) plus the
        # two contained AA runs (2,4) and (4,6) from its second pattern.
        # Engine dedup of these is covered by the first test above.
        assert len(matches) == 3
        assert matches[0] == RecognitionMatch(
            notation=_ProbeNotation("AAAA"),
            start=2,
            end=6,
            raw_text="AAAA",
        )
```

Run the file: it fails (RED — `RecognitionMatch` does not exist yet).

### Step 2 (GREEN) — `paxman/core/domain.py`

Add, next to `RecognizedRep` (currently ~line 74):

```python
@dataclass(frozen=True)
class RecognitionMatch(Generic[NotationT]):
    """A span-bearing recognition produced by a grammar.

    Grammars emit these instead of bare notations so the engine can
    deduplicate overlapping matches and order recognitions deterministically
    without losing positional information.

    ``start`` and ``end`` are half-open character offsets into the input
    text passed to ``Grammar.recognize()``; ``raw_text`` is the matched
    substring, so ``len(raw_text) == end - start`` always holds.
    """

    notation: NotationT
    start: int
    end: int
    raw_text: str

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError(
                f"Invalid span start={self.start}, end={self.end}: "
                "expected 0 <= start <= end"
            )
        if len(self.raw_text) != self.end - self.start:
            raise ValueError(
                f"raw_text {self.raw_text!r} length {len(self.raw_text)} "
                f"does not match span [{self.start}, {self.end})"
            )
```

Change the `Grammar` ABC (`recognize` currently returns `list[NotationT]`):

```python
    @abstractmethod
    def recognize(self, text: str) -> list[RecognitionMatch[NotationT]]:
        """Extract span-bearing recognition matches from raw text.

        Grammars MUST return their matches with positional spans; the engine
        owns deduplication and ordering. See RecognitionMatch.
        """
        ...
```

Add span fields to `RecognizedRep` (field order matters for the frozen dataclass equality tests):

```python
@dataclass(frozen=True)
class RecognizedRep(Generic[NotationT]):
    notation: NotationT
    contract: Contract
    grammar: GrammarRule
    start: int
    end: int
    raw_text: str
```

### Step 3 (GREEN) — `paxman/engine/orchestrator.py`

Add `RecognitionMatch` to the domain imports, then replace `_recognize` (currently lines 75–100) and add `_dedup_spans`:

```python
def _recognize(
    text: str, capability: Capability[Any], contract: Contract
) -> list[RecognizedRep[Any]]:
    """Run active grammars, dedup contained matches per grammar, and order.

    The engine owns all cross-match policy: containment dedup runs strictly
    within a single grammar's output (never across grammars, so cross-grammar
    ambiguity stays observable), and recognitions are emitted in the total
    order (start, end, active_grammars index, grammar name).
    """
    active_grammar_names = set(contract.active_grammars)
    all_grammars = capability.get_grammars()
    active_grammars = [g for g in all_grammars if g.name in active_grammar_names]
    grammar_index = {g.name: i for i, g in enumerate(active_grammars)}

    ordered: list[tuple[int, int, int, str, RecognitionMatch[Any]]] = []
    for grammar in active_grammars:
        try:
            matches = grammar.recognize(text)
        except Exception as exc:
            raise RecognitionError(
                rule=grammar.name,
                message=f"Grammar failed: {exc}",
                original_error=exc,
            ) from exc
        for match in _dedup_spans(matches):
            ordered.append(
                (
                    match.start,
                    match.end,
                    grammar_index[grammar.name],
                    grammar.name,
                    match,
                )
            )

    ordered.sort(key=lambda item: (item[0], item[1], item[2], item[3]))

    recognitions: list[RecognizedRep[Any]] = []
    for start, end, _index, grammar_name, match in ordered:
        grammar_ref = GrammarRule(
            capability_name=capability.name, grammar_name=grammar_name
        )
        recognitions.append(
            RecognizedRep(
                notation=match.notation,
                contract=contract,
                grammar=grammar_ref,
                start=start,
                end=end,
                raw_text=match.raw_text,
            )
        )
    return recognitions


def _dedup_spans(
    matches: list[RecognitionMatch[Any]],
) -> list[RecognitionMatch[Any]]:
    """Drop matches fully contained in a longer match from the SAME grammar.

    ``longer wins``: when two matches from one grammar overlap, the match
    covering more of the input survives; an exact tie keeps the first.
    Runs strictly within one grammar's output — overlapping matches from
    different grammars are preserved so cross-grammar ambiguity stays
    observable.
    """
    ordered = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))
    kept: list[RecognitionMatch[Any]] = []
    for match in ordered:
        if any(other.start <= match.start and match.end <= other.end for other in kept):
            continue
        kept.append(match)
    return kept
```

`_collect_candidates`, `_dedup_candidates`, `_determine_status`, and `_compute_replay_hash` are UNCHANGED.

### Step 4 (GREEN) — `paxman/core/__init__.py`

Add `RecognitionMatch` to the domain import and `__all__` list so that `from paxman.core import RecognitionMatch` works alongside the existing `Grammar`, `RecognizedRep`, etc.:

```python
from paxman.core.domain import (
    Candidate,
    Grammar,
    GrammarRule,
    Notation,
    Provenance,
    RecognitionMatch,
    RecognizedRep,
    Resolution,
    Rule,
    RuleStrategy,
    VersionStamp,
)
```

And add `"RecognitionMatch"` to the `__all__` list (alphabetical order, between `"RecognizedRep"` and `"Resolution"`).

### Step 5 — `tests/unit/test_recognized_rep.py`

Update all 9 constructor call sites to pass the new required fields. For span-neutral cases (tests that construct reps without real span data), use `start=0, end=0, raw_text=""`. For tests that build a span, use realistic values. Keep the existing equality semantics: two reps constructed with identical `start/end/raw_text` are equal; differing span fields make them unequal. Add:

```python
def test_span_fields_participate_in_equality(self) -> None:
    """Two reps with identical fields are equal; span differences break it."""
    base = dict(notation=..., contract=..., grammar=...)
    a = RecognizedRep(**base, start=0, end=4, raw_text="AAAA")
    b = RecognizedRep(**base, start=0, end=4, raw_text="AAAA")
    c = RecognizedRep(**base, start=2, end=6, raw_text="AAAA")
    assert a == b
    assert a != c


def test_recognized_rep_hash_stable_with_span_fields(self) -> None:
    """RecognitionMatch and RecognizedRep with identical fields hash the same."""
    # RecognitionMatch is used transiently; RecognizedRep is stored.
    # Both must be hashable for use in sets/dicts if needed.
    match = RecognitionMatch(notation=..., start=0, end=4, raw_text="AAAA")
    rep = RecognizedRep(
        notation=..., contract=..., grammar=..., start=0, end=4, raw_text="AAAA"
    )
    assert hash(match) == hash(rep)
```

(Replace the ellipses with the existing fixtures from that file.)

### Step 6 — Verify

```bash
uv run pytest tests/integration/test_recognition_seam.py tests/unit/test_recognized_rep.py -q
```

Green. Then confirm the expected interim failures:

```bash
uv run pytest tests/integration -q -x --ignore=tests/integration/test_recognition_seam.py
```

Fails (real grammars not yet migrated) — this is the bounded red state documented above; proceed to Tasks 3–7. Commit:

```bash
git add -A
git commit -m "feat(core): span-bearing recognition contract (RecognitionMatch, engine dedup + order)"
```

---

## Task 3 — Migrate Date grammars (iso8601, us, european) + tests

**Why Date first:** cheapest, and its US/European overlap is the canonical AMBIGUOUS case the contract must preserve.

### Step 1 (RED) — `tests/capabilities/date/test_grammar.py`

Mechanical transform for every assertion in the file (10 `recognize` calls):

| Current | New |
|---|---|
| `result[0].as_list() == ["2026", "07", "26"]` | `result[0].notation.as_list() == ["2026", "07", "26"]` |
| `result[1].as_list() == ...` | `result[1].notation.as_list() == ...` |

Also add one span test to `TestISO8601DateGrammar`, `TestUSDateGrammar`, and `TestEuropeanDateGrammar`:

```python
    def test_emits_spans(self) -> None:
        result = self.grammar.recognize("x 2026-07-26 y")
        assert len(result) == 1
        assert result[0].start == 2
        assert result[0].end == 12
        assert result[0].raw_text == "2026-07-26"
        assert result[0].notation.as_list() == ["2026", "07", "26"]
```

(For US/European use `"07/26/2026"` with span `(0, 10)` instead.)

### Step 2 (GREEN) — grammar files

`paxman/capabilities/Date/grammar/iso8601_recognition.py` — import `RecognitionMatch`, replace `recognize`:

```python
    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        """Extract ISO 8601 date patterns from text."""
        matches = []
        for match in _ISO8601_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=DateNotation(
                        N1=match.group(1), N2=match.group(2), N3=match.group(3)
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
```

`paxman/capabilities/Date/grammar/us_recognition.py` — replace `recognize` (the `four_digit_ranges` containment check is REMOVED — the engine's span dedup owns containment; structurally the 2-digit pattern never matches inside a 4-digit match's span, but the engine guarantees it regardless):

```python
    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        """Extract US date patterns from text.

        Both patterns emit span-bearing matches; containment dedup between
        them is the engine's responsibility.
        """
        matches = []
        for pattern in (_US_DATE_PATTERN_4DIGIT, _US_DATE_PATTERN_2DIGIT):
            for match in pattern.finditer(text):
                matches.append(
                    RecognitionMatch(
                        notation=DateNotation(
                            N1=match.group(1),
                            N2=match.group(2),
                            N3=match.group(3),
                        ),
                        start=match.start(),
                        end=match.end(),
                        raw_text=match.group(0),
                    )
                )
        return matches
```

`paxman/capabilities/Date/grammar/european_recognition.py` — same replacement (drop the manual re-sort and `four_digit_ranges`; engine orders by span):

```python
    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        """Extract European date patterns from text.

        Matches from both patterns are returned with spans; the engine
        orders them (document order) and dedups contained matches.
        """
        matches = []
        for pattern in (_EUROPEAN_DATE_PATTERN_4DIGIT, _EUROPEAN_DATE_PATTERN_2DIGIT):
            for match in pattern.finditer(text):
                matches.append(
                    RecognitionMatch(
                        notation=DateNotation(
                            N1=match.group(1),
                            N2=match.group(2),
                            N3=match.group(3),
                        ),
                        start=match.start(),
                        end=match.end(),
                        raw_text=match.group(0),
                    )
                )
        return matches
```

### Step 3 — Verify

```bash
uv run pytest tests/capabilities/date tests/integration/test_date_capability.py tests/integration/test_temporal.py -q
```

Also run the full integration suite to catch regressions:

```bash
uv run pytest tests/integration/test_pipeline.py tests/integration/test_ambiguity.py -q
```

Green. Commit.

---

## Task 4 — Migrate Email grammars (standard, localhost, obfuscated) + tests

### Step 1 (RED) — `tests/capabilities/email/test_grammar.py`

Transform every assertion (14 `recognize` calls):

| Current | New |
|---|---|
| `assert results[0] == EmailNotation(local_part="user", domain_part="example.com")` | `assert results[0].notation == EmailNotation(local_part="user", domain_part="example.com")` |
| `assert results[0].local_part == ...` (if present) | `assert results[0].notation.local_part == ...` |

Add one span test to `TestStandardEmailGrammar`, `TestLocalhostEmailGrammar`, and `TestObfuscatedEmailGrammar`:

```python
    def test_emits_spans(self) -> None:
        results = self.grammar.recognize("Contact us at user@example.com")
        assert len(results) == 1
        assert results[0].start == 14
        assert results[0].end == 31
        assert results[0].raw_text == "user@example.com"
```

(Localhost: `"Send to admin@localhost"` → span `(8, 23)`. Obfuscated: `"Contact user at example dot com"` → span `(8, 31)`.)

### Step 2 (GREEN) — grammar files

`standard_recognition.py` (import `RecognitionMatch`):

```python
    def recognize(self, text: str) -> list[RecognitionMatch[EmailNotation]]:
        matches = []
        for match in _STANDARD_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(0).split("@")[0],
                        domain_part=match.group(0).split("@")[1],
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
```

`localhost_recognition.py`:

```python
    def recognize(self, text: str) -> list[RecognitionMatch[EmailNotation]]:
        matches = []
        for match in _LOCALHOST_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(1), domain_part="localhost"
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
```

`obfuscated_recognition.py` — remove the `seen` set and the two-pass ordering; both patterns emit matches and the engine merges + orders them (document order) while candidate-stage dedup collapses duplicate values:

```python
    def recognize(self, text: str) -> list[RecognitionMatch[EmailNotation]]:
        """Extract obfuscated email patterns from text.

        Both patterns emit span-bearing matches; the engine merges, orders
        (document order), and dedups contained matches, and identical
        candidate values collapse at the candidate stage. The grammar does
        not de-duplicate.
        """
        matches = []
        for match in _OBFUSCATED_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(1),
                        domain_part=f"{match.group(2)}.{match.group(3)}",
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        for match in _AT_ONLY_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(1),
                        domain_part=match.group(2),
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
```

### Step 3 — Verify

```bash
uv run pytest tests/capabilities/email -q
uv run pytest tests/integration/test_pipeline.py tests/integration/test_ambiguity.py -q
```

Green. Commit.

---

## Task 5 — Migrate Country grammars (alpha2, alpha3, numeric, name) + tests

### Step 1 (RED) — `tests/capabilities/country/test_grammar.py`

Transform every assertion (26 `recognize` calls):

| Current | New |
|---|---|
| `assert results[0].shape == "alpha2"` | `assert results[0].notation.shape == "alpha2"` |
| `assert results[0].value == "US"` | `assert results[0].notation.value == "US"` |
| `assert results == [CountryNotation(shape="name", value="United States")]` | `assert len(results) == 1` + `assert results[0].notation == CountryNotation(shape="name", value="United States")` |
| `assert results[1].value == "GB"` | `assert results[1].notation.value == "GB"` |

Add one span test per grammar class. Alpha-2:

```python
    def test_emits_spans(self) -> None:
        results = self.grammar.recognize("  US  ")
        assert len(results) == 1
        assert results[0].start == 2
        assert results[0].end == 4
        assert results[0].raw_text == "US"
        assert results[0].notation == CountryNotation(shape="alpha2", value="US")
```

(Alpha-3: `"  USA  "` → span `(2, 5)`. Numeric: `"  840  "` → span `(2, 5)`. Name: `"  United States  "` → span `(2, 15)`, `raw_text == "United States"`, `notation.value == "United States"`.)

### Step 2 (GREEN) — grammar files

All four follow the same shape; syntax normalization (`.upper()`) STAYS in the grammars (see Behavioral Contract — deferred syntax seam). `alpha2_recognition.py`:

```python
def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
    """Extract alpha-2 patterns from text."""
    if not text.strip():
        return []
    matches = []
    for match in _ALPHA2_PATTERN.finditer(text):
        matches.append(
            RecognitionMatch(
                notation=CountryNotation(shape="alpha2", value=match.group(0).upper()),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
        )
    return matches
```

`alpha3_recognition.py`: identical with `shape="alpha3"`.

`numeric_recognition.py`:

```python
    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        """Extract numeric patterns from text."""
        if not text.strip():
            return []
        matches = []
        for match in _NUMERIC_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CountryNotation(shape="numeric", value=match.group(0)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
```

`name_recognition.py` (span derived from leading whitespace since there is no regex):

```python
    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        """Extract a country name representation from text."""
        trimmed = text.strip()
        if not trimmed:
            return []
        normalized = normalize_name(trimmed)
        if normalized in _KNOWN_NAME_KEYS:
            start = len(text) - len(text.lstrip())
            return [
                RecognitionMatch(
                    notation=CountryNotation(shape="name", value=trimmed),
                    start=start,
                    end=start + len(trimmed),
                    raw_text=trimmed,
                )
            ]
        return []
```

### Step 3 — Verify

```bash
uv run pytest tests/capabilities/country tests/integration/test_country_pipeline.py -q
uv run pytest tests/integration/test_pipeline.py tests/integration/test_ambiguity.py -q
```

Green. Commit.

---

## Task 6 — Migrate IP grammars (ipv4, ipv6) + tests

### Step 1 (RED) — `tests/capabilities/ip/test_grammar.py`

Transform assertions (both files use `results[0] == IPNotation(...)` and `[r.address for r in results]`):

| Current | New |
|---|---|
| `assert results[0] == IPNotation(address="192.168.1.1")` | `assert results[0].notation == IPNotation(address="192.168.1.1")` |
| `addresses = [r.address for r in results]` | `addresses = [r.notation.address for r in results]` |
| `assert len(results) == 2` (multiple) | unchanged |

Rewrite `test_no_duplicates` (behavior change: grammar-level value dedup is removed; the engine collapses identical candidates):

```python
    @pytest.mark.capability
    def test_no_duplicates(self) -> None:
        """Same address at distinct positions yields two span-bearing matches.

        The grammar returns every occurrence with its span; the engine
        collapses identical candidates at the candidate stage.
        """
        grammar = IPv6Grammar()
        results = grammar.recognize("::1 and ::1")
        assert len(results) == 2
        assert [(r.start, r.end) for r in results] == [(0, 3), (8, 11)]
        assert [r.notation.address for r in results] == ["::1", "::1"]
```

Add a span test per grammar:

```python
    @pytest.mark.capability
    def test_emits_spans(self) -> None:
        grammar = IPv4Grammar()
        results = grammar.recognize("Server at 192.168.1.1")
        assert len(results) == 1
        assert results[0].start == 10
        assert results[0].end == 21
        assert results[0].raw_text == "192.168.1.1"
```

(IPv6: `"Address: 2001:db8::1"` → span `(9, 20)`, `raw_text == "2001:db8::1"`.)

### Step 2 (GREEN) — grammar files

`ipv4_recognition.py`:

```python
    def recognize(self, text: str) -> list[RecognitionMatch[IPNotation]]:
        """Extract IPv4 dotted-decimal patterns from text."""
        matches = []
        for match in _IPV4_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=IPNotation(address=match.group(0)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
```

`ipv6_recognition.py` — replace the `seen`-set dedup with span-bearing emission (the full and compressed patterns are structurally disjoint, so no containment issues; the engine dedups anyway):

```python
    def recognize(self, text: str) -> list[RecognitionMatch[IPNotation]]:
        """Extract IPv6 address patterns from text."""
        matches: list[RecognitionMatch[IPNotation]] = []
        for match in _IPV6_FULL.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=IPNotation(address=match.group(1)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(1),
                )
            )
        for match in _IPV6_COMPRESSED.finditer(text):
            for group in match.groups():
                if group is not None:
                    matches.append(
                        RecognitionMatch(
                            notation=IPNotation(address=group),
                            start=match.start(),
                            end=match.end(),
                            raw_text=group,
                        )
                    )
        return matches
```

### Step 3 — Verify

```bash
uv run pytest tests/capabilities/ip -q
uv run pytest tests/integration/test_pipeline.py tests/integration/test_ambiguity.py -q
```

Green. Commit.

---

## Task 7 — Migrate Phone grammars (e164, international_00, national, tel_uri) + delete `dedup` + tests

**Why last:** it touches the only helper module (`common.py`) and the only behavior test that changes (`test_e164_dedups_same_value_different_formats`).

### Step 1 (RED) — `tests/capabilities/phone/test_grammar.py`

Transform every assertion (the file uses `results[0].shape`, `results[0].value`, `results[0].extension` across all four test classes):

| Current | New |
|---|---|
| `assert results[0].shape == "e164"` | `assert results[0].notation.shape == "e164"` |
| `assert results[0].value == "15551234567"` | `assert results[0].notation.value == "15551234567"` |
| `assert results[0].extension == "890"` | `assert results[0].notation.extension == "890"` |

Rewrite `test_e164_dedups_same_value_different_formats` (dedup moved to the engine; the grammar now returns both occurrences with spans):

```python
    def test_e164_returns_same_value_at_distinct_spans(self) -> None:
        """The same number in two formats yields two span-bearing matches.

        Grammar-level value dedup is removed; the engine collapses identical
        candidates at the candidate stage.
        """
        results = self.e164.recognize("Call +1 555 123 4567 or +15551234567")
        assert len(results) == 2
        assert [r.notation.value for r in results] == [
            "15551234567",
            "15551234567",
        ]
        assert [(r.start, r.end) for r in results] == [(5, 20), (24, 36)]
```

(`test_e164_merges_space_separated_following_number` keeps its assertion semantics — `len == 1` and the concatenated value — only the accessor becomes `results[0].notation.value`. Add a docstring line noting the regex, not the dedup, produces the single match.)

Add one span test per grammar class:

```python
    def test_emits_spans(self) -> None:
        results = self.grammar.recognize("Call +1 555 123 4567 now")
        assert len(results) == 1
        assert results[0].start == 5
        assert results[0].end == 19
        assert results[0].raw_text == "+1 555 123 4567"
```

(International00: `"00 44 20 7946 0958"` → span `(0, 17)`, raw `"00 44 20 7946 0958"`. National: `"(555) 123-4567"` → span `(0, 14)`. TelUri: `"tel:+15551234567"` → span `(0, 16)`, and also assert `results[0].notation.extension == ""`.)

### Step 2 (GREEN) — `paxman/capabilities/Phone/grammar/common.py`

Delete `dedup` and the now-unused `Iterable` import; keep `strip_separators`; update the module docstring:

```python
"""Shared helpers for Phone recognition grammars.

Space, dash, dot, and parentheses are the separators every Phone grammar
tolerates inside a number. ``strip_separators`` normalizes a raw match to
digit-only text. Grammar-level value dedup was removed in the recognition-
homogeneity migration: the engine dedups contained matches by span and
identical candidates by value.
"""
```

### Step 3 (GREEN) — the four grammar files

Each drops the `dedup` import and emits `RecognitionMatch` (values unchanged):

`e164_recognition.py`:

```python
from paxman.capabilities.Phone.grammar.common import strip_separators

    def recognize(self, text: str) -> list[RecognitionMatch[PhoneNotation]]:
        """Extract e164 patterns from text.

        Returns:
            List of RecognitionMatches; notation.value is the digit-only
            number (leading "+" and separators removed).
        """
        return [
            RecognitionMatch(
                notation=PhoneNotation(
                    shape="e164", value=strip_separators(match.group(0), plus=True)
                ),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _E164_PATTERN.finditer(text)
        ]
```

`international_00_recognition.py`:

```python
        return [
            RecognitionMatch(
                notation=PhoneNotation(
                    shape="e164",
                    # Strip the leading "00" before removing separators.
                    value=strip_separators(match.group(0)[2:]),
                ),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _INTERNATIONAL_00_PATTERN.finditer(text)
        ]
```

`national_recognition.py`:

```python
        return [
            RecognitionMatch(
                notation=PhoneNotation(
                    shape="national", value=strip_separators(match.group(0))
                ),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _NATIONAL_PATTERN.finditer(text)
        ]
```

`tel_uri_recognition.py`:

```python
        return [
            RecognitionMatch(
                notation=PhoneNotation(
                    shape="rfc3966",
                    value=strip_separators(match.group(1), plus=True),
                    extension=match.group(2) or "",
                ),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _TEL_URI_PATTERN.finditer(text)
        ]
```

All four files: add `RecognitionMatch` to the `paxman.core.domain` import.

### Step 4 — Verify

```bash
uv run pytest tests/capabilities/phone -q
uv run pytest tests/integration -q
uv run pytest tests/integration/test_pipeline.py tests/integration/test_ambiguity.py -q
```

Both green — the full integration suite recovers here because all 16 grammars are now migrated. Commit.

---

## Task 8 — Purity gate, property contract lock, and the future-capability template

### Step 1 — Create `tests/unit/test_grammar_semantic_purity.py`

```python
"""Grammars and rules must not import from each other.

Recognition grammars perform syntax-level extraction and normalization;
validation rules own every semantic decision with provenance. A grammar that
imports a rule (or vice versa) would let semantics leak across the
pipeline's separation boundary, so it is forbidden structurally.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PAXMAN = Path(__file__).resolve().parents[2] / "paxman"
GRAMMAR_FILES = sorted((PAXMAN / "capabilities").glob("*/grammar/*.py"))
RULE_FILES = sorted((PAXMAN / "capabilities").glob("*/rules/*.py"))


def _forbidden_imports(path: Path, forbidden: str) -> list[str]:
    """Return import-from statements referencing the forbidden package."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if forbidden in parts and "paxman" in parts:
                violations.append(f"{path.name}: {ast.unparse(node)}")
    return violations


@pytest.mark.unit
@pytest.mark.parametrize("grammar_file", GRAMMAR_FILES, ids=lambda p: p.name)
def test_grammars_do_not_import_rules(grammar_file):
    assert _forbidden_imports(grammar_file, "rules") == []


@pytest.mark.unit
@pytest.mark.parametrize("rule_file", RULE_FILES, ids=lambda p: p.name)
def test_rules_do_not_import_grammars(rule_file):
    assert _forbidden_imports(rule_file, "grammar") == []
```

### Step 2 — `tests/property/test_grammar_properties.py`

The four "returns a list" property tests survive unchanged; add the contract-type assertion to each (in the body of the existing `returns...list` tests):

```python
    assert all(isinstance(m, RecognitionMatch) for m in result)
```

(import `RecognitionMatch` from `paxman.core.domain`).

### Step 3 — `HOW_TO_ADD_NEW_CAPABILITY.md` (future-capability template)

In `HOW_TO_ADD_NEW_CAPABILITY.md`, replace Step 4 "Create a Grammar" (lines 134–198) with the span contract version. The new Step 4 must teach:

- Grammar returns `list[RecognitionMatch[YourDomainNotation]]`, NOT bare notations.
- Every match carries `start`, `end`, `raw_text` (the matched substring), so `len(raw_text) == end - start`.
- The grammar does syntax only (extraction + separator/case normalization). It does NOT de-duplicate, sort, or validate — the engine owns dedup/order, rules own meaning.
- Never import from `rules/` (purity gate).

Replace the current Step 4 example with:

```python
import re

from paxman.core.domain import Grammar, RecognitionMatch
from paxman.capabilities.MyDomain.notation import MyDomainNotation


class StandardMyDomainGrammar(Grammar[MyDomainNotation]):
    """Standard recognition for the MyDomain capability."""

    name = "standard_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[MyDomainNotation]]:
        """Extract span-bearing matches from raw text.

        The engine dedups contained matches and orders recognitions; the
        grammar only extracts and emits spans.
        """
        pattern = re.compile(r"...")  # your pattern
        matches = []
        for match in pattern.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=MyDomainNotation(...),  # parsed from groups
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
```

### Step 4 — `ARCHITECTURE.md`

In `ARCHITECTURE.md`, after the "Separation of Recognition and Validation" section (lines 17–25) and before the "### Capability Isolation" heading (line 28), insert a new subsection:

```markdown
### Recognition Pipeline Contract

Every grammar implements `recognize(text) -> list[RecognitionMatch]`, where
`RecognitionMatch` carries the notation plus a half-open `[start, end)` span
and the matched `raw_text`. The grammar produces positions; the engine owns
all cross-match policy:

- **Containment dedup (per grammar):** a match fully contained in a longer
  match from the SAME grammar is dropped ("longer wins"). Dedup never runs
  across grammars, so two grammars agreeing on the same span (e.g. US vs
  European date reading of `01/02/2026`) are both preserved and ambiguity
  stays observable.
- **Ordering:** recognitions are emitted in the total order
  `(start, end, active_grammars index, grammar name)`, i.e. document order.
- **Candidate dedup** (`value, recognition_rule, validation_rule`) runs
  after validation as a stability net.

Grammars perform syntax-level extraction and normalization only; rules own
semantic validation with provenance. This contract applies identically to
every capability, built-in or future.
```

### Step 5 — `capability_homogeneity_audit.md`

Append a resolution note to the Tier 2 section:

```markdown
**Resolved 2026-08-04 (recognition-homogeneity migration):** grammar
recognition is now homogeneous across capabilities — every grammar emits
span-bearing `RecognitionMatch` objects, the engine owns within-grammar
containment dedup ("longer wins") and the total document order
`(start, end, active_grammars index, grammar name)`, and grammars are
restricted to syntax extraction/normalization (enforced by the semantic
purity gate). Value-keyed dedup was removed from Phone (`common.dedup`),
Email (`seen` set), and IP (`seen` set); Date's manual span-containment
checks and per-grammar ordering were removed. Deferred: a shared
stdnum-style `clean()` syntax seam and moving Country `.upper()` into it.
```

### Step 6 — Verify

```bash
uv run pytest tests/unit/test_grammar_semantic_purity.py tests/property -q
```

Green. Commit.

---

## Task 9 — Final verification gate

**This is the ULTRAWORK verification step. Every check below must pass with the evidence in hand.**

```bash
uv run ruff format . && uv run ruff check .          # no violations
uv run pyright                                        # strict, no errors
uv run lint-imports                                   # import boundaries clean
uv run pytest -q                                      # FULL 782-test suite, 0 failures
uv run pytest tests/integration/test_default_replay_hashes.py -q   # 5/5 — hashes byte-identical
```

If `test_default_replay_hashes.py` FAILS at this point, STOP: the migration changed the candidate set. Do not update the literals — find and fix the regression (compare `result.candidates` against pre-migration output). If any rule/grammar file needed a stray `# type: ignore` or `# noqa`, fix the underlying issue instead — none are permitted in `paxman/` source.

Versioning: NO version bump is required — the replay hashes are byte-identical, which is the migration's correctness contract (semantic versioning reflects observable behavior, and there is none). If the release process requires a bump, bump patch only.

### Acceptance checklist (from the Behavioral Contract)

- [ ] All 16 grammars return `list[RecognitionMatch]`; zero bare-notation returns
- [ ] `RecognitionMatch` invariants enforced (`0 <= start <= end`, `len(raw_text) == end - start`)
- [ ] Engine dedups within a grammar only; `01/02/2026` still AMBIGUOUS (US vs European)
- [ ] Recognitions in total order `(start, end, active index, grammar name)`
- [ ] Five baseline replay hashes byte-identical
- [ ] `_dedup_candidates` untouched
- [ ] Purity gate green (no grammar↔rule imports)
- [ ] `HOW_TO_ADD_NEW_CAPABILITY.md` teaches the span contract
- [ ] `ARCHITECTURE.md` documents the recognition pipeline contract
- [ ] Audit Tier 2 marked resolved, syntax seam deferred
- [ ] Full suite green: `pytest`, `pyright`, `ruff`, `lint-imports`
