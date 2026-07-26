"""Hypothesis property-based tests for grammars."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.Email.grammar.standard_recognition import (
    StandardEmailGrammar,
)
from paxman.capabilities.Email.notation import EmailNotation


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
def test_standard_email_grammar_returns_email_notation(
    local_part: str,
    domain_label: str,
    tld: str,
) -> None:
    """StandardEmailGrammar.recognize() returns EmailNotation objects."""
    grammar = StandardEmailGrammar()
    domain_part = f"{domain_label}.{tld}"
    result = grammar.recognize(f"{local_part}@{domain_part}")
    for item in result:
        assert isinstance(item, EmailNotation)


def test_standard_email_grammar_no_match_returns_empty() -> None:
    """StandardEmailGrammar.recognize() returns empty list for no-match input."""
    grammar = StandardEmailGrammar()
    result = grammar.recognize("no email here")
    assert result == []
