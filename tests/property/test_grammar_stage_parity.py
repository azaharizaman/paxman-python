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

import pytest

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
