"""Tests for Date grammars."""

from __future__ import annotations

import pytest

from paxman.capabilities.Date.grammar.european_recognition import (
    EuropeanDateGrammar,
)
from paxman.capabilities.Date.grammar.iso8601_recognition import (
    ISO8601DateGrammar,
)
from paxman.capabilities.Date.grammar.slash_iso_recognition import (
    SlashISODateGrammar,
)
from paxman.capabilities.Date.grammar.us_recognition import USDateGrammar


@pytest.mark.capability
class TestISO8601DateGrammar:
    """Tests for ISO 8601 date grammar."""

    def test_recognizes_valid_input(self) -> None:
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("2026-07-26")
        assert len(result) == 1
        assert result[0].notation.as_list() == ["2026", "07", "26"]

    def test_recognizes_multiple(self) -> None:
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("Dates: 2026-07-26 and 2025-12-31")
        assert len(result) == 2

    def test_returns_empty_for_empty_input(self) -> None:
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("")
        assert result == []

    def test_returns_empty_for_no_match(self) -> None:
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("No dates here")
        assert result == []

    def test_does_not_match_embedded_in_digits(self) -> None:
        """A date glued to surrounding digits is not recognized.

        The digit lookarounds prevent partial matches inside longer digit
        runs (e.g. IDs).
        """
        grammar = ISO8601DateGrammar()
        assert grammar.recognize("12026-07-26") == []
        assert grammar.recognize("2026-07-261") == []
        assert grammar.recognize("12026-07-261") == []

    def test_grammar_name(self) -> None:
        grammar = ISO8601DateGrammar()
        assert grammar.name == "iso8601_recognition"

    def test_emits_spans(self) -> None:
        result = self.grammar.recognize("x 2026-07-26 y")
        assert len(result) == 1
        assert result[0].start == 2
        assert result[0].end == 12
        assert result[0].raw_text == "2026-07-26"
        assert result[0].notation.as_list() == ["2026", "07", "26"]

    @property
    def grammar(self) -> ISO8601DateGrammar:
        return ISO8601DateGrammar()


@pytest.mark.capability
class TestUSDateGrammar:
    """Tests for US date grammar."""

    def test_recognizes_4digit_year(self) -> None:
        grammar = USDateGrammar()
        result = grammar.recognize("07/26/2026")
        assert len(result) == 1
        assert result[0].notation.as_list() == ["07", "26", "2026"]

    def test_recognizes_2digit_year(self) -> None:
        grammar = USDateGrammar()
        result = grammar.recognize("07/26/26")
        assert len(result) == 1
        assert result[0].notation.as_list() == ["07", "26", "26"]

    def test_recognizes_variant_input(self) -> None:
        grammar = USDateGrammar()
        result = grammar.recognize("7/26/2026")
        assert len(result) == 1

    def test_recognizes_multiple_dates(self) -> None:
        grammar = USDateGrammar()
        result = grammar.recognize("Dates: 07/26/2026 and 12/31/2025")
        assert len(result) == 2

    def test_grammar_name(self) -> None:
        grammar = USDateGrammar()
        assert grammar.name == "us_recognition"

    def test_does_not_match_embedded_in_digits(self) -> None:
        """A date glued to surrounding digits is not recognized.

        Both year-length variants carry digit lookarounds, preventing
        partial matches inside longer digit runs (e.g. IDs).
        """
        grammar = USDateGrammar()
        assert grammar.recognize("1207/26/2026") == []
        assert grammar.recognize("07/26/20261") == []
        assert grammar.recognize("1207/26/26") == []
        assert grammar.recognize("07/26/261") == []

    def test_emits_spans(self) -> None:
        result = self.grammar.recognize("x 07/26/2026 y")
        assert len(result) == 1
        assert result[0].start == 2
        assert result[0].end == 12
        assert result[0].raw_text == "07/26/2026"
        assert result[0].notation.as_list() == ["07", "26", "2026"]

    @property
    def grammar(self) -> USDateGrammar:
        return USDateGrammar()


@pytest.mark.capability
class TestEuropeanDateGrammar:
    """Tests for European date grammar."""

    def test_recognizes_4digit_year(self) -> None:
        grammar = EuropeanDateGrammar()
        result = grammar.recognize("26/07/2026")
        assert len(result) == 1
        assert result[0].notation.as_list() == ["26", "07", "2026"]

    def test_recognizes_2digit_year(self) -> None:
        grammar = EuropeanDateGrammar()
        result = grammar.recognize("26/07/26")
        assert len(result) == 1
        assert result[0].notation.as_list() == ["26", "07", "26"]

    def test_recognizes_variant_input(self) -> None:
        grammar = EuropeanDateGrammar()
        result = grammar.recognize("6/7/2026")
        assert len(result) == 1

    def test_grammar_name(self) -> None:
        grammar = EuropeanDateGrammar()
        assert grammar.name == "european_recognition"

    def test_does_not_match_embedded_in_digits(self) -> None:
        """A date glued to surrounding digits is not recognized.

        Both year-length variants carry digit lookarounds, preventing
        partial matches inside longer digit runs (e.g. IDs).
        """
        grammar = EuropeanDateGrammar()
        assert grammar.recognize("1226/07/2026") == []
        assert grammar.recognize("26/07/20261") == []
        assert grammar.recognize("1226/07/26") == []
        assert grammar.recognize("26/07/261") == []

    def test_emits_spans(self) -> None:
        result = self.grammar.recognize("x 26/07/2026 y")
        assert len(result) == 1
        assert result[0].start == 2
        assert result[0].end == 12
        assert result[0].raw_text == "26/07/2026"
        assert result[0].notation.as_list() == ["26", "07", "2026"]

    @property
    def grammar(self) -> EuropeanDateGrammar:
        return EuropeanDateGrammar()


@pytest.mark.capability
class TestSlashISODateGrammar:
    """Tests for slash-ISO date grammar (YYYY/MM/DD)."""

    def test_recognizes_valid_input(self) -> None:
        grammar = SlashISODateGrammar()
        result = grammar.recognize("2026/07/26")
        assert len(result) == 1
        assert result[0].notation.as_list() == ["2026", "07", "26"]

    def test_recognizes_single_digit_components(self) -> None:
        grammar = SlashISODateGrammar()
        result = grammar.recognize("2026/7/6")
        assert len(result) == 1
        assert result[0].notation.as_list() == ["2026", "7", "6"]

    def test_recognizes_multiple(self) -> None:
        grammar = SlashISODateGrammar()
        result = grammar.recognize("Dates: 2026/07/26 and 2025/12/31")
        assert len(result) == 2

    def test_returns_empty_for_empty_input(self) -> None:
        grammar = SlashISODateGrammar()
        result = grammar.recognize("")
        assert result == []

    def test_returns_empty_for_no_match(self) -> None:
        grammar = SlashISODateGrammar()
        result = grammar.recognize("No dates here")
        assert result == []

    def test_does_not_match_us_or_european_order(self) -> None:
        """A 2-digit-first slash date is not a slash-ISO date."""
        grammar = SlashISODateGrammar()
        assert grammar.recognize("07/26/2026") == []
        assert grammar.recognize("26/07/2026") == []

    def test_does_not_match_embedded_in_digits(self) -> None:
        """A date run glued to surrounding digits is not recognized.

        The digit lookarounds prevent partial matches inside longer digit
        runs (e.g. IDs), mirroring the 2-digit US/European patterns.
        """
        grammar = SlashISODateGrammar()
        assert grammar.recognize("12026/07/26") == []
        assert grammar.recognize("2026/07/261") == []
        assert grammar.recognize("12026/07/261") == []

    def test_grammar_name(self) -> None:
        grammar = SlashISODateGrammar()
        assert grammar.name == "slash_iso_recognition"

    def test_emits_spans(self) -> None:
        result = self.grammar.recognize("x 2026/07/26 y")
        assert len(result) == 1
        assert result[0].start == 2
        assert result[0].end == 12
        assert result[0].raw_text == "2026/07/26"
        assert result[0].notation.as_list() == ["2026", "07", "26"]

    @property
    def grammar(self) -> SlashISODateGrammar:
        return SlashISODateGrammar()
