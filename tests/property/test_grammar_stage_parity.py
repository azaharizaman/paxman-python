"""Migration Proof Harness — byte-identical RecognitionMatch parity.

Every migration PR must prove the new PipelineGrammar declaration produces
the same list[RecognitionMatch] as the old bespoke recognize() for a
curated corpus plus property-generated inputs.

Corpus must cover:
- Country/name_recognition: normalized-key vs original-case value
- Phone/e164: E164Trim (end = start + len(trimmed)) vs match.end()
- URL: paren-balance (end = start + len(trimmed))
- Money: either-order SYMBOL ? AMOUNT span-merge
- SIUnit: split-prefix classifier
- ISBN: hyphen/space tolerance
"""

from __future__ import annotations

from typing import Any

import pytest

from paxman.capabilities.Currency.grammar.code_recognition import CodeRecognition
from paxman.capabilities.Currency.grammar.symbol_recognition import SymbolRecognition
from paxman.capabilities.Currency.grammar.word_recognition import WordRecognition
from paxman.core.domain import Grammar
from tests.property._legacy_currency_grammars import (
    LegacyCodeRecognition,
    LegacySymbolRecognition,
    LegacyWordRecognition,
)

# Import harness helper — implemented in this task.
from tests.property.grammar_stage_parity import assert_grammar_parity

CURATED_CORPUS: list[str] = [
    "United States",  # Country name — original case preservation
    "  united states  ",  # Country name — whitespace + case fold
    "+1 555 123 4567",  # Phone e164 — normal
    "+15551234567 5551234567",  # Phone e164 — runaway trim at 15 digits
    "https://example.com/path_(with_parens)",  # URL paren-balance
    "USD500",  # Money code+amount
    "$500",  # Money bare symbol + amount (shared symbol)
    "500 EUR",  # Money amount + code (either order)
    "kilo gram",  # SIUnit split_word_prefix
    "m/s",  # SIUnit compound
    "9780306406157",  # ISBN13 bare
    "978-0-11-000222-4",  # ISBN13 hyphenated (range message)
    "2026-01-15",  # Date S1
    "user@example.com",  # Email S1
    "192.168.1.1",  # IP S1
]


@pytest.mark.property
def test_curated_corpus_parity_placeholder() -> None:
    """Placeholder — will be parametrized over (grammar, text) pairs.

    RED: assert_grammar_parity does not yet prove any migration; the harness
    itself is GREEN-skipped until Task 5+ wires the first real parity case.
    """
    # Each parametrized case will call:
    #   assert_grammar_parity(old_grammar, new_grammar, text)
    # where equality is (start, end, raw_text, notation).
    assert callable(assert_grammar_parity), (
        "harness helper must be importable for Task 5+ wiring"
    )
    pytest.skip("Harness not yet implemented — wire in Task 5+")


# Currency migration (Task 5): old bespoke recognize() vs new PipelineGrammar
# declaration. Each tuple is (legacy_grammar, new_grammar, text). The corpus
# covers qualified/bare symbols, case-folded codes, case-insensitive words,
# amount/sign-glued rejections, and inside-token rejections — every branch the
# migration must preserve byte-identically.
CURRENCY_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    # Symbol — qualified vs bare, longest/qualified-first precedence.
    (LegacySymbolRecognition(), SymbolRecognition(), "US$"),
    (LegacySymbolRecognition(), SymbolRecognition(), "€"),
    (LegacySymbolRecognition(), SymbolRecognition(), "A$"),
    (LegacySymbolRecognition(), SymbolRecognition(), "CA$"),
    (LegacySymbolRecognition(), SymbolRecognition(), "US$ is the dollar"),
    (LegacySymbolRecognition(), SymbolRecognition(), "A$ is the Australian dollar"),
    (LegacySymbolRecognition(), SymbolRecognition(), "US$5"),  # amount-glued reject
    (LegacySymbolRecognition(), SymbolRecognition(), "$500"),  # amount-glued reject
    (LegacySymbolRecognition(), SymbolRecognition(), "x€"),  # inside-token reject
    (LegacySymbolRecognition(), SymbolRecognition(), "€5"),  # amount-glued reject
    (LegacySymbolRecognition(), SymbolRecognition(), ""),  # empty
    # Code — case folding, whitespace, multi-match, glued rejections.
    (LegacyCodeRecognition(), CodeRecognition(), "USD"),
    (LegacyCodeRecognition(), CodeRecognition(), " usd "),
    (LegacyCodeRecognition(), CodeRecognition(), "GBP, EUR"),
    (LegacyCodeRecognition(), CodeRecognition(), "US$"),  # not 3 letters
    (LegacyCodeRecognition(), CodeRecognition(), "xUSD"),  # inside-token reject
    (LegacyCodeRecognition(), CodeRecognition(), "USD-500"),  # sign-glued reject
    (LegacyCodeRecognition(), CodeRecognition(), "USD500"),  # amount-glued reject
    (LegacyCodeRecognition(), CodeRecognition(), "123"),  # digits
    (LegacyCodeRecognition(), CodeRecognition(), ""),  # empty
    # Word — case-insensitive fold, multi-word, plural/amount rejections.
    (LegacyWordRecognition(), WordRecognition(), "euro"),
    (LegacyWordRecognition(), WordRecognition(), "Euro"),
    (LegacyWordRecognition(), WordRecognition(), "EURO"),
    (LegacyWordRecognition(), WordRecognition(), "US Dollar"),
    (LegacyWordRecognition(), WordRecognition(), "Euro and Dollar"),
    (LegacyWordRecognition(), WordRecognition(), "Dollars"),  # plural reject
    (LegacyWordRecognition(), WordRecognition(), "euro500"),  # amount-glued reject
    (LegacyWordRecognition(), WordRecognition(), "the"),  # non-token reject
    (LegacyWordRecognition(), WordRecognition(), ""),  # empty
]


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), CURRENCY_PARITY_CASES)
def test_currency_grammar_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Currency grammars.

    Proves the PipelineGrammar declarations emit the same spans and notations
    as the old bespoke recognize() bodies (ADR-0008 §4.1 migration gate).
    """
    assert_grammar_parity(legacy, new, text)
