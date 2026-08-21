"""LexiconAlternation unit tests."""

from __future__ import annotations

import pytest

from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.core.grammar.boundary import BoundaryGuard
from paxman.core.grammar.lexicon import LexiconAlternation
from paxman.core.grammar.stages import LexiconStage, PipelineState, WholeInputLookup

pytestmark = pytest.mark.unit


def test_longest_first_ordering() -> None:
    alt = LexiconAlternation(tokens=["$", "US$", "A$"], longest_first=True)
    # US$ (3) before A$ (2) before $ (1); qualified-first tie-break is secondary
    assert alt.ordered_tokens[0] == "US$"
    assert alt.alternation.startswith("US\\$")


def test_qualified_first_within_same_length() -> None:
    alt = LexiconAlternation(tokens=["A$", "$$"], longest_first=True)
    # Same length (2), so qualified-first tie-break determines order: "A$" before "$$"
    assert alt.ordered_tokens[0] == "A$"
    assert alt.ordered_tokens[1] == "$$"


def test_alternation_is_escaped() -> None:
    alt = LexiconAlternation(tokens=["$", "("], longest_first=True)
    assert r"\$" in alt.alternation
    assert r"\(" in alt.alternation


def test_lexicon_stage_emits_matches_with_boundary() -> None:
    stage = LexiconStage[CurrencyNotation](
        tokens=["$", "US$"],
        boundary=BoundaryGuard.word_sign(),
        longest_first=True,
        notation_fn=lambda token: CurrencyNotation(text=token, shape="symbol"),
    )
    state = PipelineState(text="Pay US$ and $", matches=[], scratch={})
    out = stage.run(state)
    assert len(out.matches) == 2
    assert out.matches[0].raw_text == "US$"
    assert out.matches[1].raw_text == "$"


def test_whole_input_lookup_emits_original_trimmed_case() -> None:
    stage: WholeInputLookup[CurrencyNotation] = WholeInputLookup(
        keys={"us", "eur"},  # normalized keys
        notation_fn=lambda trimmed: CurrencyNotation(text=trimmed, shape="code"),
        normalizer=lambda s: s.lower(),
    )
    state = PipelineState(text="  Us  ", matches=[], scratch={})
    out = stage.run(state)
    assert len(out.matches) == 1
    assert out.matches[0].raw_text == "Us"  # original trimmed, not "us"
    assert out.matches[0].start == 2
    assert out.matches[0].end == 4
