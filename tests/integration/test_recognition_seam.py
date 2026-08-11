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
from paxman.core.extensions import register_grammar, register_rule
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
    target_semantics = frozenset({"probe_long"})
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
    target_semantics = frozenset({"probe_short"})
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
    """Minimal contract.

    ``active_grammars=None`` (the default) exercises the engine fallback:
    the capability's shipped ``get_grammars()`` names run in declaration
    order. Passing an explicit list overrides the fallback.
    """

    def __init__(
        self,
        active_grammars: list[str] | None = None,
        extra_grammars: tuple[str, ...] = (),
    ) -> None:
        self._active_grammars = active_grammars
        self._extra_grammars = extra_grammars

    @property
    def capability_name(self) -> str:
        return "probe"

    @property
    def active_grammars(self) -> list[str] | None:
        return self._active_grammars

    @property
    def extra_grammars(self) -> tuple[str, ...]:
        return self._extra_grammars

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
        Recognition order: (0,2,0,probe_long) < (0,2,1,probe_short) <
        (3,5,1,probe_short) < (3,7,0,probe_long) < (5,7,1,probe_short).

        The three probe_short recognitions all produce the identical
        candidate tuple (S:AA, probe_short, short_rule), so the unchanged
        candidate-level dedup safety net collapses them to the first-seen.
        The observable candidates still prove the contract: the same-span
        index tiebreak (L:AA before S:AA), and the longer L:AAAA surviving
        its contained runs.
        """
        register_capability(_ProbeCapability())
        result = run_capability("AA AAAA", _ProbeContract())

        assert [c.value for c in result.candidates] == [
            "L:AA",
            "S:AA",
            "L:AAAA",
        ]

    @pytest.mark.integration
    def test_engine_grammar_index_follows_contract_order(self) -> None:
        """The same-span tiebreak uses contract.active_grammars order.

        Reversing the contract's active grammar order flips the
        (start, end, index, name) tiebreak at the shared (0,2) span: with
        contract order [probe_short, probe_long], short's index is 0, so
        S:AA precedes L:AA — the index follows the CONTRACT's order, not
        the capability's internal get_grammars() order.
        """
        register_capability(_ProbeCapability())
        result = run_capability(
            "AA AAAA", _ProbeContract(["probe_short", "probe_long"])
        )

        assert [c.value for c in result.candidates] == [
            "S:AA",
            "L:AA",
            "L:AAAA",
        ]

    @pytest.mark.integration
    def test_grammar_emits_span_bearing_matches(self) -> None:
        """The ABC contract: recognize() returns matches with real spans."""
        grammar = _ProbeLongGrammar()
        matches = grammar.recognize("x AAAA y")
        # The grammar emits every match with its span: AAAA(2,6) plus the
        # two contained AA runs (2,4) and (4,6) from its second pattern.
        # Engine dedup of these is covered by the first test above.
        assert matches == [
            RecognitionMatch(
                notation=_ProbeNotation("AAAA"),
                start=2,
                end=6,
                raw_text="AAAA",
            ),
            RecognitionMatch(
                notation=_ProbeNotation("AA"),
                start=2,
                end=4,
                raw_text="AA",
            ),
            RecognitionMatch(
                notation=_ProbeNotation("AA"),
                start=4,
                end=6,
                raw_text="AA",
            ),
        ]

    @pytest.mark.integration
    def test_engine_runs_each_grammar_once_despite_duplicate_contract_names(
        self,
    ) -> None:
        """Duplicate names in contract.active_grammars must not double-run.

        The engine dedupes the contract's active grammar list (keeping the
        first occurrence) before building grammar_index and the run list,
        so each supported grammar runs at most once and the two structures
        stay aligned.
        """
        calls: list[str] = []

        class _CountingLongGrammar(_ProbeLongGrammar):
            def recognize(self, text: str) -> list[RecognitionMatch[_ProbeNotation]]:
                calls.append(self.name)
                return super().recognize(text)

        class _CountingCapability(_ProbeCapability):
            def get_grammars(self) -> list[Grammar[_ProbeNotation]]:
                return [_CountingLongGrammar(), _ProbeShortGrammar()]

        register_capability(_CountingCapability())
        result = run_capability("AAAA", _ProbeContract(["probe_long", "probe_long"]))

        assert calls == ["probe_long"]
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "L:AAAA"


class TestDefaultGrammarSurface:
    """The engine fallback when a contract omits ``active_grammars``.

    Option B: ``active_grammars`` becomes optional. A contract returning
    ``None`` (the base-class default) activates every **shipped** grammar in
    ``get_grammars()`` declaration order — so adding a new shipped grammar
    activates it with no contract edit. Community grammars stay opt-in via
    ``extra_grammars``.
    """

    @pytest.mark.integration
    def test_contract_without_active_grammars_runs_all_shipped(self) -> None:
        """The None fallback activates every shipped grammar, in order."""
        register_capability(_ProbeCapability())
        result = run_capability("AA AAAA", _ProbeContract())

        # Both shipped grammars ran via the fallback; same-span tiebreak
        # follows get_grammars() order (long=0, short=1).
        assert [c.value for c in result.candidates] == [
            "L:AA",
            "S:AA",
            "L:AAAA",
        ]

    @pytest.mark.integration
    def test_fallback_never_activates_community_grammars(self) -> None:
        """The fallback covers shipped grammars only; community stays opt-in.

        This distinguishes "fallback to shipped get_grammars()" from a naive
        "fallback to every supported grammar": a registered community grammar
        must NOT run under the None fallback — only ``extra_grammars`` opts
        it in (D4).
        """
        calls: list[str] = []

        class _CommunityGrammar(Grammar[_ProbeNotation]):
            name = "probe_community"

            def recognize(self, text: str) -> list[RecognitionMatch[_ProbeNotation]]:
                calls.append(self.name)
                return [
                    RecognitionMatch(
                        notation=_ProbeNotation("COMMUNITY"),
                        start=0,
                        end=len(text),
                        raw_text=text,
                    )
                ]

        class _CommunityRule(Rule[_ProbeNotation]):
            name = "community_rule"
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
            target_semantics = frozenset({"probe_community"})
            requires_features = frozenset()

            def matches(self, notation: _ProbeNotation, contract: Contract) -> bool:
                return True

            def normalize(self, notation: _ProbeNotation, contract: Contract) -> str:
                return "COMMUNITY"

        register_grammar("probe", _CommunityGrammar)
        register_rule("probe", _CommunityRule)
        register_capability(_ProbeCapability())

        # "XXXX" matches no shipped grammar, so any recognition here could
        # only come from the community grammar — the fallback must not run it.
        result = run_capability("XXXX", _ProbeContract())
        assert calls == []
        assert result.status == Resolution.MISSING
        assert result.candidates == ()

        # Same contract opted in via extra_grammars: community grammar runs.
        result = run_capability(
            "XXXX", _ProbeContract(extra_grammars=("probe_community",))
        )
        assert calls == ["probe_community"]
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "COMMUNITY"
