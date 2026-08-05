"""Tests for Money recognition grammars."""

from __future__ import annotations

import pytest

from paxman.capabilities.Money.grammar import classify_amount_shape
from paxman.capabilities.Money.grammar.code_recognition import CodeRecognition
from paxman.capabilities.Money.grammar.symbol_recognition import SymbolRecognition
from paxman.capabilities.Money.grammar.word_recognition import WordRecognition
from paxman.core.domain import RecognitionMatch

pytestmark = [pytest.mark.capability]


def _assert_span_invariants(text: str, match: RecognitionMatch[object]) -> None:
    """Verify the RecognitionMatch span contract (half-open [start, end))."""
    assert 0 <= match.start <= match.end
    assert len(match.raw_text) == match.end - match.start
    assert match.raw_text == text[match.start : match.end]


class TestCodeRecognition:
    """Tests for CodeRecognition."""

    def setup_method(self) -> None:
        self.grammar = CodeRecognition()

    def test_recognizes_prefix_adjacent(self) -> None:
        """Happy path: uppercase code directly adjacent to the amount."""
        results = self.grammar.recognize("USD500")
        assert len(results) == 1
        assert results[0].notation.currency_part == "USD"
        assert results[0].notation.amount_part == "500"
        assert results[0].notation.currency_shape == "code"
        assert results[0].notation.amount_shape == "integer"

    def test_recognizes_prefix_with_space(self) -> None:
        """A single ASCII space between code and amount is allowed."""
        results = self.grammar.recognize("USD 500")
        assert len(results) == 1
        assert results[0].notation.currency_part == "USD"
        assert results[0].notation.amount_part == "500"
        assert results[0].raw_text == "USD 500"

    def test_recognizes_suffix(self) -> None:
        """Amount-first order: '500 USD'."""
        results = self.grammar.recognize("500 USD")
        assert len(results) == 1
        assert results[0].notation.currency_part == "USD"
        assert results[0].notation.amount_part == "500"

    def test_recognizes_suffix_adjacent(self) -> None:
        """Amount-first, no space: '100MYR'."""
        results = self.grammar.recognize("100MYR")
        assert len(results) == 1
        assert results[0].notation.currency_part == "MYR"
        assert results[0].notation.amount_part == "100"

    def test_recognizes_comma_decimal_suffix(self) -> None:
        """'1.000,50 EUR' keeps the raw amount and comma_decimal shape."""
        results = self.grammar.recognize("1.000,50 EUR")
        assert len(results) == 1
        assert results[0].notation.currency_part == "EUR"
        assert results[0].notation.amount_part == "1.000,50"
        assert results[0].notation.amount_shape == "comma_decimal"

    def test_recognizes_dot_decimal_suffix(self) -> None:
        """'1,00.50 USD' keeps the raw amount and dot_decimal shape."""
        results = self.grammar.recognize("1,00.50 USD")
        assert len(results) == 1
        assert results[0].notation.currency_part == "USD"
        assert results[0].notation.amount_part == "1,00.50"
        assert results[0].notation.amount_shape == "dot_decimal"

    def test_recognizes_multiple(self) -> None:
        """Two independent code+amount tokens both match."""
        results = self.grammar.recognize("USD 500 and EUR 200")
        assert len(results) == 2

    def test_recognizes_unknown_code(self) -> None:
        """Unknown codes ARE matched — validity is the rule's job."""
        results = self.grammar.recognize("ZZZ 500")
        assert len(results) == 1
        assert results[0].notation.currency_part == "ZZZ"

    def test_recognizes_accounting_form(self) -> None:
        """Parenthesized amounts match as one token with accounting shape."""
        results = self.grammar.recognize("(500) USD")
        assert len(results) == 1
        assert results[0].notation.amount_part == "(500)"
        assert results[0].notation.amount_shape == "accounting"

    def test_rejects_bare_code(self) -> None:
        """A code with no amount is not a money token."""
        assert self.grammar.recognize("USD") == []

    def test_rejects_bare_amount(self) -> None:
        """An amount with no code is not a money token."""
        assert self.grammar.recognize("500") == []

    def test_rejects_lowercase_code(self) -> None:
        """Only uppercase alpha-3 codes match."""
        assert self.grammar.recognize("usd 500") == []

    def test_rejects_two_letter_code(self) -> None:
        """A 2-letter code is not alpha-3."""
        assert self.grammar.recognize("US 500") == []

    def test_rejects_preceded_by_word_char(self) -> None:
        """No match inside a longer token: xUSD500."""
        assert self.grammar.recognize("xUSD500") == []

    def test_rejects_followed_by_word_char(self) -> None:
        """No match inside a longer token: USD500x."""
        assert self.grammar.recognize("USD500x") == []

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty/whitespace-only input returns an empty list."""
        assert self.grammar.recognize("") == []
        assert self.grammar.recognize("   ") == []

    def test_name(self) -> None:
        """Verify the grammar name."""
        assert self.grammar.name == "code_recognition"

    def test_emits_spans(self) -> None:
        """The whole token is one span: raw_text == text[start:end]."""
        results = self.grammar.recognize("USD 500")
        assert len(results) == 1
        _assert_span_invariants("USD 500", results[0])


class TestSymbolRecognition:
    """Tests for SymbolRecognition."""

    def setup_method(self) -> None:
        self.grammar = SymbolRecognition()

    def test_bare_symbol_prefix(self) -> None:
        """'$500' matches as a bare symbol, shape 'symbol'."""
        results = self.grammar.recognize("$500")
        assert len(results) == 1
        assert results[0].notation.currency_part == "$"
        assert results[0].notation.currency_shape == "symbol"
        assert results[0].notation.amount_part == "500"
        assert results[0].notation.amount_shape == "integer"

    def test_qualified_symbol_ordering(self) -> None:
        """'US$50.79' matches as the qualified form, not bare '$' (D4)."""
        results = self.grammar.recognize("US$50.79")
        assert len(results) == 1
        assert results[0].notation.currency_part == "US$"
        assert results[0].notation.currency_shape == "qualified_symbol"
        assert results[0].notation.amount_part == "50.79"
        assert results[0].notation.amount_shape == "dot_decimal"

    def test_euro_prefix(self) -> None:
        """'€5' matches at string start (lookbehind boundary)."""
        results = self.grammar.recognize("\u20ac5")
        assert len(results) == 1
        assert results[0].notation.currency_part == "\u20ac"
        assert results[0].notation.currency_shape == "symbol"

    def test_qualified_rm(self) -> None:
        """'RM100' — a letter-containing symbol is qualified."""
        results = self.grammar.recognize("RM100")
        assert len(results) == 1
        assert results[0].notation.currency_part == "RM"
        assert results[0].notation.currency_shape == "qualified_symbol"

    def test_symbol_suffix(self) -> None:
        """'500 €' — amount-first order."""
        results = self.grammar.recognize("500 \u20ac")
        assert len(results) == 1
        assert results[0].notation.currency_part == "\u20ac"
        assert results[0].notation.amount_part == "500"

    def test_comma_decimal_suffix(self) -> None:
        """'1.000,00 €' keeps the raw amount and comma_decimal shape."""
        results = self.grammar.recognize("1.000,00 \u20ac")
        assert len(results) == 1
        assert results[0].notation.amount_part == "1.000,00"
        assert results[0].notation.amount_shape == "comma_decimal"

    def test_rejects_bare_symbol(self) -> None:
        """A symbol with no amount is not a money token."""
        assert self.grammar.recognize("$") == []

    def test_rejects_code_shape(self) -> None:
        """Codes are not symbols: 'USD 500' does not match."""
        assert self.grammar.recognize("USD 500") == []

    def test_rejects_mid_word(self) -> None:
        """No match inside a longer token: $500x."""
        assert self.grammar.recognize("$500x") == []

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty input returns an empty list."""
        assert self.grammar.recognize("") == []

    def test_name(self) -> None:
        """Verify the grammar name."""
        assert self.grammar.name == "symbol_recognition"

    def test_emits_spans(self) -> None:
        """The whole token is one span: raw_text == text[start:end]."""
        text = "  $500  "
        results = self.grammar.recognize(text)
        assert len(results) == 1
        assert results[0].start == 2
        assert results[0].end == 6
        _assert_span_invariants(text, results[0])


class TestWordRecognition:
    """Tests for WordRecognition."""

    def setup_method(self) -> None:
        self.grammar = WordRecognition()

    def test_recognizes_amount_first(self) -> None:
        """'18 Dollar' — amount-first order, word as written."""
        results = self.grammar.recognize("18 Dollar")
        assert len(results) == 1
        assert results[0].notation.currency_part == "Dollar"
        assert results[0].notation.currency_shape == "word"
        assert results[0].notation.amount_part == "18"
        assert results[0].notation.amount_shape == "integer"

    def test_recognizes_ringgit(self) -> None:
        """'500 Ringgit'."""
        results = self.grammar.recognize("500 Ringgit")
        assert len(results) == 1
        assert results[0].notation.currency_part == "Ringgit"

    def test_recognizes_euro(self) -> None:
        """'500 Euro'."""
        results = self.grammar.recognize("500 Euro")
        assert len(results) == 1
        assert results[0].notation.currency_part == "Euro"

    def test_recognizes_word_first(self) -> None:
        """Word-first order: 'Euro 500'."""
        results = self.grammar.recognize("Euro 500")
        assert len(results) == 1
        assert results[0].notation.currency_part == "Euro"
        assert results[0].notation.amount_part == "500"

    def test_recognizes_case_insensitive_as_written(self) -> None:
        """Matching is case-insensitive; the word is kept as written."""
        results = self.grammar.recognize("500 euro")
        assert len(results) == 1
        assert results[0].notation.currency_part == "euro"

    def test_rejects_code_shape(self) -> None:
        """Codes are not words: '500 USD' does not match."""
        assert self.grammar.recognize("500 USD") == []

    def test_rejects_bare_word(self) -> None:
        """A word with no amount is not a money token."""
        assert self.grammar.recognize("Dollar") == []

    def test_rejects_plural(self) -> None:
        """'500 Dollars' — 'Dollar' inside a longer word does not match."""
        assert self.grammar.recognize("500 Dollars") == []

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty input returns an empty list."""
        assert self.grammar.recognize("") == []

    def test_name(self) -> None:
        """Verify the grammar name."""
        assert self.grammar.name == "word_recognition"

    def test_emits_spans(self) -> None:
        """The whole token is one span: raw_text == text[start:end]."""
        text = "18 Dollar"
        results = self.grammar.recognize(text)
        assert len(results) == 1
        assert results[0].start == 0
        assert results[0].end == 9
        _assert_span_invariants(text, results[0])


class TestClassifyAmountShape:
    """The amount-shape classifier table (syntax only)."""

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            ("500", "integer"),
            ("500.50", "dot_decimal"),
            ("1,00.50", "dot_decimal"),
            ("1.000,50", "comma_decimal"),
            ("1,234.56", "dot_decimal"),
            ("12.345.678,90", "comma_decimal"),
            ("1\u202f234,50", "space_decimal"),
            ("(500)", "accounting"),
        ],
    )
    def test_classify_amount_shape(self, amount: str, expected: str) -> None:
        """The five syntactic shapes are classified from the token alone."""
        assert classify_amount_shape(amount) == expected
