"""Recognition-to-rule data consistency for the Currency grammars.

Every currency representation the Currency grammars recognize must be
backed by at least one authority rule-data mapping. If a recognition key
had no rule-data mapping, a grammar could emit a notation that no
validation rule can resolve — a pipeline dead end (MISSING/INVALID) for
an input the grammar explicitly claims to understand.

Unlike Money (whose consistency test is one-directional), Currency locks
the sets equal: the grammar token tables are derived from exactly the
rule-data keys, and the rule-data keys are derived from exactly the
grammar token tables. Rule data may therefore not drift from the tokens
the grammars ship.

Data ownership matches the rule layer: symbols and words resolve through
the CLDR tables only, and every resolved code must exist in the ISO 4217
List One code set.
"""

from __future__ import annotations

import pytest

from paxman.capabilities.Currency.grammar.data.currency_symbols import SYMBOL_TOKENS
from paxman.capabilities.Currency.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Currency.rules.data.cldr_currencies import (
    NAME_TO_CODES,
    SYMBOL_TO_CODES,
)
from paxman.capabilities.Currency.rules.data.iso4217_list_one import CURRENCY_CODES

pytestmark = [pytest.mark.capability, pytest.mark.currency]


def _uncovered_report(uncovered: list[str], kind: str) -> str:
    """Build a sorted, readable failure report for uncovered codes."""
    lines = [f"Codes with no backing ISO 4217 code-set entry ({kind}):"]
    lines.extend(f"  - {code}" for code in uncovered)
    return "\n".join(lines)


class TestRecognitionKeysAreRuleDataCovered:
    """Recognition key sets must match the authority rule-data maps."""

    def test_symbol_token_keys_match_symbol_to_codes(self) -> None:
        """Every shipped symbol token resolves through the CLDR symbol table."""
        assert set(SYMBOL_TOKENS) == set(SYMBOL_TO_CODES)

    def test_word_token_keys_match_name_to_codes(self) -> None:
        """Every shipped word token resolves through the CLDR name table."""
        assert set(WORD_TOKENS) == set(NAME_TO_CODES)

    def test_every_resolved_symbol_code_is_in_iso_set(self) -> None:
        """Every ISO code a symbol resolves to is a member of CURRENCY_CODES."""
        uncovered = sorted(
            code
            for codes in SYMBOL_TO_CODES.values()
            for code in codes
            if code not in CURRENCY_CODES
        )
        assert not uncovered, _uncovered_report(uncovered, "symbol codes")

    def test_every_resolved_word_code_is_in_iso_set(self) -> None:
        """Every ISO code a word resolves to is a member of CURRENCY_CODES."""
        uncovered = sorted(
            code
            for codes in NAME_TO_CODES.values()
            for code in codes
            if code not in CURRENCY_CODES
        )
        assert not uncovered, _uncovered_report(uncovered, "word codes")

    def test_no_symbol_token_is_a_code_lookalike(self) -> None:
        """No symbol token is a code lookalike, whitespace, or empty."""
        for token in SYMBOL_TOKENS:
            assert not (
                len(token) == 3
                and token.isascii()
                and token.isalpha()
                and token.isupper()
            )
            assert not any(ch.isspace() for ch in token)
            assert token

    def test_name_keys_are_lowercase(self) -> None:
        """Every NAME_TO_CODES key is lowercase (D4)."""
        assert all(k == k.lower() for k in NAME_TO_CODES)
