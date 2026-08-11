"""Tests for grammar ``semantics`` metadata on shipped grammars."""

from __future__ import annotations

import pytest

from paxman.capabilities import (
    IP,
    ISBN,
    URL,
    Country,
    Currency,
    Date,
    Email,
    Money,
    Phone,
)


class TestGrammarSemanticsMetadata:
    @pytest.mark.unit
    def test_shipped_grammars_declare_semantics_identity(self) -> None:
        """Every shipped grammar declares ``semantics`` equal to its name."""
        capabilities = [Country, Currency, Date, Email, IP, ISBN, Money, Phone, URL]
        for capability in capabilities:
            for grammar in capability().get_grammars():
                assert isinstance(grammar.semantics, str)
                assert grammar.semantics != ""
                assert grammar.semantics == grammar.name
