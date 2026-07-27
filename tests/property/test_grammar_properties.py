"""Hypothesis property-based tests for grammars."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.Date.grammar.iso8601_recognition import (
    ISO8601DateGrammar,
)
from paxman.capabilities.Date.grammar.us_recognition import USDateGrammar
from paxman.capabilities.Email.grammar.standard_recognition import (
    StandardEmailGrammar,
)


@pytest.mark.property
@given(
    local_part=st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="._%+-",
        ),
        min_size=1,
        max_size=64,
    ),
    domain_label=st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-",
        ),
        min_size=1,
        max_size=63,
    ),
    tld=st.text(
        alphabet=st.characters(
            whitelist_categories=("L",),
        ),
        min_size=2,
        max_size=10,
    ),
)
def test_standard_email_grammar_returns_list(
    local_part: str,
    domain_label: str,
    tld: str,
) -> None:
    """StandardEmailGrammar.recognize() always returns a list."""
    grammar = StandardEmailGrammar()
    domain_part = f"{domain_label}.{tld}"
    result = grammar.recognize(f"{local_part}@{domain_part}")
    assert isinstance(result, list)


@pytest.mark.property
@given(
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
)
def test_iso8601_grammar_returns_list(
    year: int,
    month: int,
    day: int,
) -> None:
    """ISO8601DateGrammar.recognize() always returns a list."""
    grammar = ISO8601DateGrammar()
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    result = grammar.recognize(date_str)
    assert isinstance(result, list)
    if result:
        assert len(result) == 1


@pytest.mark.property
@given(
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
    year=st.integers(min_value=1900, max_value=2100),
)
def test_us_grammar_returns_list(
    month: int,
    day: int,
    year: int,
) -> None:
    """USDateGrammar.recognize() always returns a list."""
    grammar = USDateGrammar()
    date_str = f"{month}/{day}/{year}"
    result = grammar.recognize(date_str)
    assert isinstance(result, list)
    if result:
        assert len(result) == 1


@pytest.mark.property
@given(
    text=st.text(min_size=0, max_size=100),
)
def test_grammar_never_returns_none(text: str) -> None:
    """All grammars never return None from recognize()."""
    grammars = [
        StandardEmailGrammar(),
        ISO8601DateGrammar(),
        USDateGrammar(),
    ]
    for grammar in grammars:
        result = grammar.recognize(text)
        assert result is not None
        assert isinstance(result, list)
