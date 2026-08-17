"""Tests for SIUnit recognition grammars.

Grammars are exercised directly (no rules): each test drives
Grammar.recognize() against raw text and asserts the emitted spans —
half-open [start, end) offsets, raw_text, and the SIUnitNotation
text/shape — mirroring Currency's grammar test structure.
"""

from __future__ import annotations

import pytest

from paxman.capabilities.SIUnit.grammar.compound_recognition import CompoundRecognition
from paxman.capabilities.SIUnit.grammar.name_recognition import NameRecognition
from paxman.capabilities.SIUnit.grammar.symbol_recognition import SymbolRecognition
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.core.domain import Grammar, RecognitionMatch

pytestmark = [pytest.mark.capability, pytest.mark.si_unit]

# Expected-span tuple: (raw_text, start, end, notation_text, shape).
Span = tuple[str, int, int, str, str]


def _assert_span_invariants(text: str, match: RecognitionMatch[SIUnitNotation]) -> None:
    """Verify the RecognitionMatch span contract (half-open [start, end))."""
    assert 0 <= match.start <= match.end
    assert len(match.raw_text) == match.end - match.start
    assert match.raw_text == text[match.start : match.end]


def _assert_spans(
    text: str,
    expected: list[Span],
    results: list[RecognitionMatch[SIUnitNotation]],
) -> None:
    """Compare results against (raw_text, start, end, text, shape) tuples."""
    assert len(results) == len(expected)
    for match, (raw_text, start, end, notation_text, shape) in zip(
        results, expected, strict=True
    ):
        _assert_span_invariants(text, match)
        assert match.start == start
        assert match.end == end
        assert match.raw_text == raw_text
        assert match.notation.text == notation_text
        assert match.notation.shape == shape


class TestSymbolRecognition:
    """Grammar: symbol_recognition — case-exact unit symbol tokens."""

    def setup_method(self) -> None:
        self.grammar: Grammar[SIUnitNotation] = SymbolRecognition()

    def test_semantics_identity(self) -> None:
        # SEAM (ADR-0003): every shipped grammar declares `semantics`;
        # SIUnit grammars use identity ids (no coalesced groups).
        assert self.grammar.semantics == "symbol_recognition"

    @pytest.mark.parametrize(
        ("text", "token"),
        [
            ("m", "m"),
            ("kg", "kg"),
            ("MHz", "MHz"),
            ("Pa", "Pa"),
            ("cd", "cd"),
            ("°C", "°C"),
            ("µg", "µg"),
            ("min", "min"),
            ("da", "da"),  # bare prefix is recognized (the rule rejects -> INVALID)
            ("k", "k"),
        ],
    )
    def test_recognizes(self, text: str, token: str) -> None:
        results = self.grammar.recognize(text)
        assert len(results) == 1
        match = results[0]
        assert match.notation.text == token
        assert match.notation.shape == "symbol"
        assert match.start == 0
        assert match.end == len(text)
        assert match.raw_text == text

    @pytest.mark.parametrize(
        "text",
        ["pa", "Kg", "KHz", "metre", "m/s²", "N·m", "xkg", "kg5", "2m", "25°C", "5kg"],
    )
    def test_rejects(self, text: str) -> None:
        assert self.grammar.recognize(text) == []

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            # "m s" is the valid SI expression "metre second": two units, not a
            # broken spaced prefix (m is also the metre unit, not prefix-only).
            ("m s", [("m", 0, 1, "m", "symbol"), ("s", 2, 3, "s", "symbol")]),
            # Separated by a non-space keeps the two units distinct.
            ("m; s", [("m", 0, 1, "m", "symbol"), ("s", 3, 4, "s", "symbol")]),
        ],
    )
    def test_multiple_spans(self, text: str, expected: list[Span]) -> None:
        _assert_spans(text, expected, self.grammar.recognize(text))

    @pytest.mark.parametrize(
        ("text", "notation_text", "shape"),
        [
            # Prefix-ONLY symbols split across whitespace are rejectable spans.
            ("k g", "k g", "split_symbol_prefix"),
            ("µ g", "µ g", "split_symbol_prefix"),
            ("da m", "da m", "split_symbol_prefix"),
        ],
    )
    def test_split_prefix_shape(
        self, text: str, notation_text: str, shape: str
    ) -> None:
        results = self.grammar.recognize(text)
        assert results
        first = results[0]
        assert first.notation.text == notation_text
        assert first.notation.shape == shape

    @pytest.mark.parametrize(
        ("text", "notation_text", "shape"),
        [
            # Dual-role prefix symbols stay two distinct units when spaced.
            ("m s", "m", "symbol"),
            ("N m", "N", "symbol"),
        ],
    )
    def test_spaced_units_not_split(
        self, text: str, notation_text: str, shape: str
    ) -> None:
        results = self.grammar.recognize(text)
        assert results
        first = results[0]
        assert first.notation.text == notation_text
        assert first.notation.shape == shape


class TestNameRecognition:
    """Grammar: name_recognition — case-folded unit names."""

    def setup_method(self) -> None:
        self.grammar: Grammar[SIUnitNotation] = NameRecognition()

    def test_semantics_identity(self) -> None:
        # SEAM (ADR-0003): identity semantics id; no coalesced groups.
        assert self.grammar.semantics == "name_recognition"

    @pytest.mark.parametrize(
        ("text", "name"),
        [
            ("kilogram", "kilogram"),
            ("Kilogram", "kilogram"),
            ("KILOGRAM", "kilogram"),
            ("kelvin", "kelvin"),
            ("degree celsius", "degree celsius"),
            ("Degree Celsius", "degree celsius"),
            ("megahertz", "megahertz"),
            ("kilometre", "kilometre"),
        ],
    )
    def test_recognizes(self, text: str, name: str) -> None:
        results = self.grammar.recognize(text)
        assert len(results) == 1
        match = results[0]
        assert match.notation.text == name
        assert match.notation.shape == "name"
        assert match.start == 0
        assert match.end == len(text)

    @pytest.mark.parametrize(
        "text",
        ["kilograms", "kilogran", "kg", "kelvins", "xkelvin", "kelvinx"],
    )
    def test_rejects(self, text: str) -> None:
        assert self.grammar.recognize(text) == []

    @pytest.mark.parametrize(
        "text",
        ["5kilogram", "kilogram5", "_kilogram", "kilogram_"],
    )
    def test_rejects_quantity_adjacent_names(self, text: str) -> None:
        # The grammar boundary blocks digit/underscore-adjacent names so a
        # quantity-prefixed unit name is not recognized (identity-only: no
        # quantities). Mirrors the symbol grammar's digit boundary.
        assert self.grammar.recognize(text) == []

    def test_multiple_spans(self) -> None:
        _assert_spans(
            "kelvin pascal",
            [("kelvin", 0, 6, "kelvin", "name"), ("pascal", 7, 13, "pascal", "name")],
            self.grammar.recognize("kelvin pascal"),
        )


class TestCompoundRecognition:
    """Grammar: compound_recognition — product/quotient unit shapes."""

    def setup_method(self) -> None:
        self.grammar: Grammar[SIUnitNotation] = CompoundRecognition()

    def test_semantics_identity(self) -> None:
        # SEAM (ADR-0003): identity semantics id; no coalesced groups.
        assert self.grammar.semantics == "compound_recognition"

    @pytest.mark.parametrize(
        ("text", "body"),
        [
            ("m/s²", "m/s²"),
            ("m/s2", "m/s2"),
            ("km/h", "km/h"),
            ("N·m", "N·m"),
            ("N⋅m", "N⋅m"),
            ("kg·m/s²", "kg·m/s²"),
            ("g/cm³", "g/cm³"),
            ("m·s⁻²", "m·s⁻²"),
            ("m/°C", "m/°C"),
            ("µg/mL", "µg/mL"),
            ("QQQ/zzz", "QQQ/zzz"),  # shape-only: the rule rejects unknown groups
            ("m/sx", "m/sx"),  # shape-only: the rule rejects unknown groups
            ("xN·m", "xN·m"),  # shape-only: the rule rejects unknown groups
        ],
    )
    def test_recognizes(self, text: str, body: str) -> None:
        results = self.grammar.recognize(text)
        assert len(results) == 1
        match = results[0]
        assert match.notation.text == body
        assert match.notation.shape == "compound"
        assert match.start == 0
        assert match.end == len(text)

    @pytest.mark.parametrize("text", ["m", "m s", "m s²", "5m/s"])
    def test_rejects(self, text: str) -> None:
        assert self.grammar.recognize(text) == []
