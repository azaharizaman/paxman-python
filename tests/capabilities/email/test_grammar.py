"""Tests for Email recognition grammars."""

import pytest

from paxman.capabilities.Email.grammar.standard_recognition import (
    StandardEmailGrammar,
)


class TestStandardEmailGrammar:
    """Tests for StandardEmailGrammar."""

    @pytest.mark.capability
    def test_recognizes_standard_email(self) -> None:
        grammar = StandardEmailGrammar()
        results = grammar.recognize("Contact us at user@example.com")
        assert len(results) == 1
        assert results[0] == ["user", "example.com"]

    @pytest.mark.capability
    def test_recognizes_email_with_dots(self) -> None:
        grammar = StandardEmailGrammar()
        results = grammar.recognize("Send to first.last@domain.co.uk")
        assert len(results) == 1
        assert results[0] == ["first.last", "domain.co.uk"]

    @pytest.mark.capability
    def test_recognizes_email_with_plus(self) -> None:
        grammar = StandardEmailGrammar()
        results = grammar.recognize("user+tag@gmail.com")
        assert len(results) == 1
        assert results[0] == ["user+tag", "gmail.com"]

    @pytest.mark.capability
    def test_recognizes_multiple_emails(self) -> None:
        grammar = StandardEmailGrammar()
        results = grammar.recognize("Email a@b.com or c@d.org")
        assert len(results) == 2
        assert results[0] == ["a", "b.com"]
        assert results[1] == ["c", "d.org"]

    @pytest.mark.capability
    def test_ignores_invalid_email(self) -> None:
        grammar = StandardEmailGrammar()
        results = grammar.recognize("not an email")
        assert len(results) == 0

    @pytest.mark.capability
    def test_ignores_obfuscated_email(self) -> None:
        grammar = StandardEmailGrammar()
        results = grammar.recognize("user at example dot com")
        assert len(results) == 0

    @pytest.mark.capability
    def test_returns_empty_for_empty_input(self) -> None:
        grammar = StandardEmailGrammar()
        results = grammar.recognize("")
        assert len(results) == 0
