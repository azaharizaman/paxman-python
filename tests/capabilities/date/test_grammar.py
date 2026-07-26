"""Tests for Date grammars."""

from __future__ import annotations

import pytest

from paxman.capabilities.Date.grammar.european_recognition import (
    EuropeanDateGrammar,
)
from paxman.capabilities.Date.grammar.iso8601_recognition import (
    ISO8601DateGrammar,
)
from paxman.capabilities.Date.grammar.us_recognition import USDateGrammar


class TestISO8601DateGrammar:
    """Tests for ISO 8601 date grammar."""

    @pytest.mark.capability
    def test_recognizes_valid_input(self) -> None:
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("2026-07-26")
        assert len(result) == 1
        assert result[0].as_list() == ["26", "07", "2026"]

    @pytest.mark.capability
    def test_recognizes_multiple(self) -> None:
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("Dates: 2026-07-26 and 2025-12-31")
        assert len(result) == 2

    @pytest.mark.capability
    def test_returns_empty_for_no_match(self) -> None:
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("no dates here")
        assert result == []

    @pytest.mark.capability
    def test_returns_empty_for_empty_input(self) -> None:
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("")
        assert result == []

    @pytest.mark.capability
    def test_grammar_name(self) -> None:
        grammar = ISO8601DateGrammar()
        assert grammar.name == "iso8601_recognition"


class TestUSDateGrammar:
    """Tests for US date grammar."""

    @pytest.mark.capability
    def test_recognizes_valid_input(self) -> None:
        grammar = USDateGrammar()
        result = grammar.recognize("07/26/2026")
        assert len(result) == 1
        assert result[0].as_list() == ["26", "07", "2026"]

    @pytest.mark.capability
    def test_recognizes_variant_input(self) -> None:
        grammar = USDateGrammar()
        result = grammar.recognize("7/26/2026")
        assert len(result) == 1
        assert result[0].as_list() == ["26", "7", "2026"]

    @pytest.mark.capability
    def test_grammar_name(self) -> None:
        grammar = USDateGrammar()
        assert grammar.name == "us_recognition"


class TestEuropeanDateGrammar:
    """Tests for European date grammar."""

    @pytest.mark.capability
    def test_recognizes_valid_input(self) -> None:
        grammar = EuropeanDateGrammar()
        result = grammar.recognize("26.07.2026")
        assert len(result) == 1
        assert result[0].as_list() == ["26", "07", "2026"]

    @pytest.mark.capability
    def test_recognizes_multiple(self) -> None:
        grammar = EuropeanDateGrammar()
        result = grammar.recognize("From 01.01.2025 to 31.12.2026")
        assert len(result) == 2

    @pytest.mark.capability
    def test_grammar_name(self) -> None:
        grammar = EuropeanDateGrammar()
        assert grammar.name == "european_recognition"
