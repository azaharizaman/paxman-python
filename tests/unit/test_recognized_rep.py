"""Tests for RecognizedRep dataclass."""

from __future__ import annotations

from typing import Any

import pytest

from paxman.core.domain import GrammarRule, RecognizedRep


class FakeContract:
    """Minimal Contract stub for unit tests."""

    @property
    def capability_name(self) -> str:
        return "email"

    @property
    def active_grammars(self) -> list[str]:
        return []

    @property
    def excluded_rules(self) -> list[str]:
        return []

    @property
    def pinned_rules(self) -> tuple[str, ...] | None:
        return None

    @property
    def year(self) -> int | None:
        return None

    @property
    def output_format(self) -> str | None:
        return None

    def as_dict(self) -> dict[str, Any]:
        return {"capability_name": "email"}


class TestRecognizedRep:
    @pytest.mark.unit
    def test_immutable(self) -> None:
        gr = GrammarRule(capability_name="email", grammar_name="standard")
        contract = FakeContract()
        rr = RecognizedRep(
            notation=["user", "example.com"], contract=contract, grammar=gr
        )
        with pytest.raises(AttributeError):
            rr.notation = ["other", "domain.com"]

    @pytest.mark.unit
    def test_equality(self) -> None:
        gr = GrammarRule(capability_name="email", grammar_name="standard")
        contract = FakeContract()
        a = RecognizedRep(
            notation=["user", "example.com"], contract=contract, grammar=gr
        )
        b = RecognizedRep(
            notation=["user", "example.com"], contract=contract, grammar=gr
        )
        assert a == b

    @pytest.mark.unit
    def test_inequality_notation(self) -> None:
        gr = GrammarRule(capability_name="email", grammar_name="standard")
        contract = FakeContract()
        a = RecognizedRep(
            notation=["user", "example.com"], contract=contract, grammar=gr
        )
        b = RecognizedRep(
            notation=["other", "example.com"], contract=contract, grammar=gr
        )
        assert a != b

    @pytest.mark.unit
    def test_inequality_grammar(self) -> None:
        gr1 = GrammarRule(capability_name="email", grammar_name="standard")
        gr2 = GrammarRule(capability_name="email", grammar_name="obfuscated")
        contract = FakeContract()
        a = RecognizedRep(
            notation=["user", "example.com"], contract=contract, grammar=gr1
        )
        b = RecognizedRep(
            notation=["user", "example.com"], contract=contract, grammar=gr2
        )
        assert a != b

    @pytest.mark.unit
    def test_hashable(self) -> None:
        gr = GrammarRule(capability_name="email", grammar_name="standard")
        contract = FakeContract()
        rr = RecognizedRep(
            notation=["user", "example.com"], contract=contract, grammar=gr
        )
        assert hash(rr) is not None
        assert hash(rr) == hash(rr)
