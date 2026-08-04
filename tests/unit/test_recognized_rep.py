"""Tests for RecognizedRep dataclass."""

from __future__ import annotations

from typing import Any

import pytest

from paxman.core.domain import GrammarRule, RecognitionMatch, RecognizedRep


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


def _grammar_rule(name: str = "standard") -> GrammarRule:
    return GrammarRule(capability_name="email", grammar_name=name)


def _contract() -> FakeContract:
    return FakeContract()


# Shared defaults so two default-constructed reps compare equal: FakeContract
# and GrammarRule are compared by identity/value in dataclass equality, so
# fresh instances per call would break `a == b` for identical field values.
_DEFAULT_CONTRACT = _contract()
_DEFAULT_GRAMMAR = _grammar_rule()


def _rep(
    *,
    notation: Any = ["user", "example.com"],
    contract: FakeContract | None = None,
    grammar: GrammarRule | None = None,
    start: int = 0,
    end: int = 0,
    raw_text: str = "",
) -> RecognizedRep[Any]:
    """Build a RecognizedRep with span-neutral defaults for unit tests."""
    return RecognizedRep(
        notation=notation,
        contract=contract or _DEFAULT_CONTRACT,
        grammar=grammar or _DEFAULT_GRAMMAR,
        start=start,
        end=end,
        raw_text=raw_text,
    )


class TestGrammarRule:
    @pytest.mark.unit
    def test_requires_lowercase_capability_name(self) -> None:
        with pytest.raises(ValueError, match="capability_name must be lowercase"):
            GrammarRule(capability_name="Email", grammar_name="standard")

    @pytest.mark.unit
    def test_requires_lowercase_grammar_name(self) -> None:
        with pytest.raises(ValueError, match="grammar_name must be lowercase"):
            GrammarRule(capability_name="email", grammar_name="Standard")


class TestRecognizedRep:
    @pytest.mark.unit
    def test_immutable(self) -> None:
        rr = _rep()
        with pytest.raises(AttributeError):
            rr.notation = ["other", "domain.com"]

    @pytest.mark.unit
    def test_equality(self) -> None:
        assert _rep() == _rep()

    @pytest.mark.unit
    def test_inequality_notation(self) -> None:
        a = _rep(notation=["user", "example.com"])
        b = _rep(notation=["other", "example.com"])
        assert a != b

    @pytest.mark.unit
    def test_inequality_grammar(self) -> None:
        a = _rep(grammar=_grammar_rule("standard"))
        b = _rep(grammar=_grammar_rule("obfuscated"))
        assert a != b

    @pytest.mark.unit
    def test_hashable(self) -> None:
        rr = _rep()
        assert hash(rr) is not None
        assert hash(rr) == hash(rr)

    @pytest.mark.unit
    def test_hashable_with_hashable_notation(self) -> None:
        rr = _rep(notation=("user", "example.com"))
        assert hash(rr) is not None
        assert hash(rr) == hash(rr)

    @pytest.mark.unit
    def test_span_fields_participate_in_equality(self) -> None:
        """Two reps with identical fields are equal; span differences break it."""
        a = _rep(start=0, end=4, raw_text="AAAA")
        b = _rep(start=0, end=4, raw_text="AAAA")
        c = _rep(start=2, end=6, raw_text="AAAA")
        assert a == b
        assert a != c

    @pytest.mark.unit
    def test_recognized_rep_hash_stable_with_span_fields(self) -> None:
        """Adding span fields keeps both types hashable and reps stable.

        RecognitionMatch is used transiently; RecognizedRep is stored. Both
        must be hashable for use in sets/dicts if needed. Hash stability is
        asserted on RecognizedRep (identical reps hash identically), since
        the two classes intentionally hash over different field subsets.
        """
        match = RecognitionMatch(
            notation=("user", "example.com"), start=0, end=4, raw_text="AAAA"
        )
        rep = _rep(
            notation=("user", "example.com"), start=0, end=4, raw_text="AAAA"
        )
        assert hash(match) is not None
        assert hash(rep) == hash(rep)
        assert hash(_rep(notation=("user", "example.com"), start=0, end=4, raw_text="AAAA")) == hash(rep)
