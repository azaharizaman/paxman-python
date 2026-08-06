"""Recognition-to-rule data consistency for the Money grammars.

Every currency representation the Money grammars recognize must be backed
by at least one authority rule-data mapping. If a recognition key had no
rule-data mapping, a grammar could emit a notation that no validation rule
can resolve — a pipeline dead end (MISSING/INVALID) for an input the
grammar explicitly claims to understand.

The assertion is deliberately one-directional: recognition keys must be a
subset of the rule-data keys. Rule data may contain additional round-trip
and lookup-only keys that no recognition key targets.

Data ownership matches the rule layer: symbols and words resolve through
the CLDR tables only, and every resolved code must exist in the ISO 4217
List One code set.
"""

from __future__ import annotations

import pytest

from paxman.capabilities.Money.grammar.data.currency_symbols import SYMBOL_TOKENS
from paxman.capabilities.Money.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Money.rules.data.cldr_currencies import (
    NAME_TO_CODES,
    SYMBOL_TO_CODES,
)
from paxman.capabilities.Money.rules.data.iso4217_list_one import CURRENCY_CODES

pytestmark = [pytest.mark.capability, pytest.mark.money]


def _uncovered_report(uncovered: list[str], kind: str) -> str:
    """Build a sorted, readable failure report for uncovered keys."""
    lines = [f"Recognition keys with no backing rule-data mapping ({kind}):"]
    lines.extend(f"  - {key}" for key in uncovered)
    return "\n".join(lines)


class TestRecognitionKeysAreRuleDataCovered:
    """Recognition key sets must be covered by authority rule-data maps."""

    def test_every_symbol_token_is_a_symbol_to_codes_key(self) -> None:
        """Every shipped symbol token resolves through the CLDR symbol table."""
        uncovered = sorted(set(SYMBOL_TOKENS) - set(SYMBOL_TO_CODES))
        assert not uncovered, _uncovered_report(uncovered, "symbols")

    def test_every_word_token_is_a_name_to_codes_key(self) -> None:
        """Every shipped word token resolves through the CLDR name table."""
        uncovered = sorted(set(WORD_TOKENS) - set(NAME_TO_CODES))
        assert not uncovered, _uncovered_report(uncovered, "words")

    def test_every_symbol_resolves_to_at_least_one_iso_code(self) -> None:
        """Every CLDR symbol key resolves to at least one ISO 4217 code."""
        uncovered = sorted(
            key
            for key, codes in SYMBOL_TO_CODES.items()
            if not (set(codes) & CURRENCY_CODES)
        )
        assert not uncovered, _uncovered_report(uncovered, "symbol codes")

    def test_every_word_resolves_to_at_least_one_iso_code(self) -> None:
        """Every CLDR word key resolves to at least one ISO 4217 code."""
        uncovered = sorted(
            key
            for key, codes in NAME_TO_CODES.items()
            if not (set(codes) & CURRENCY_CODES)
        )
        assert not uncovered, _uncovered_report(uncovered, "word codes")
