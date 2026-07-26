"""Tests for Email recognition grammars."""

from __future__ import annotations

import pytest

from paxman.capabilities.Email.grammar.localhost_recognition import (
    LocalhostEmailGrammar,
)
from paxman.capabilities.Email.grammar.obfuscated_recognition import (
    ObfuscatedEmailGrammar,
)
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


class TestObfuscatedEmailGrammar:
    """Tests for ObfuscatedEmailGrammar."""

    @pytest.mark.capability
    def test_recognizes_at_dot_format(self) -> None:
        grammar = ObfuscatedEmailGrammar()
        results = grammar.recognize("Contact user at example dot com")
        assert len(results) == 1
        assert results[0] == ["user", "example.com"]

    @pytest.mark.capability
    def test_recognizes_at_symbol_format(self) -> None:
        grammar = ObfuscatedEmailGrammar()
        results = grammar.recognize("Email user at gmail.com")
        assert len(results) == 1
        assert results[0] == ["user", "gmail.com"]

    @pytest.mark.capability
    def test_ignores_standard_email(self) -> None:
        grammar = ObfuscatedEmailGrammar()
        results = grammar.recognize("user@example.com")
        assert len(results) == 0

    @pytest.mark.capability
    def test_returns_empty_for_no_email(self) -> None:
        grammar = ObfuscatedEmailGrammar()
        results = grammar.recognize("no email here")
        assert len(results) == 0


class TestLocalhostEmailGrammar:
    """Tests for LocalhostEmailGrammar."""

    @pytest.mark.capability
    def test_recognizes_localhost_email(self) -> None:
        grammar = LocalhostEmailGrammar()
        results = grammar.recognize("Send to admin@localhost")
        assert len(results) == 1
        assert results[0] == ["admin", "localhost"]

    @pytest.mark.capability
    def test_recognizes_localhost_with_port(self) -> None:
        grammar = LocalhostEmailGrammar()
        results = grammar.recognize("user@localhost:8080")
        assert len(results) == 1
        assert results[0] == ["user", "localhost"]

    @pytest.mark.capability
    def test_ignores_standard_email(self) -> None:
        grammar = LocalhostEmailGrammar()
        results = grammar.recognize("user@example.com")
        assert len(results) == 0

    @pytest.mark.capability
    def test_returns_empty_for_no_email(self) -> None:
        grammar = LocalhostEmailGrammar()
        results = grammar.recognize("no email here")
        assert len(results) == 0
