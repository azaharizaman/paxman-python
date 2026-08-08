"""Hypothesis property tests for the Currency capability.

Each property locks a mathematical invariant of recognition using an
independently derived expectation:

- any standalone 3-letter ASCII token folds to exactly one uppercase
  "code" match (D3 grammar-owned case folding);
- every code in CURRENCY_CODES is recognized and validated by the ISO
  4217 Section-code rule;
- any lowercase CLDR display-name word folds back from its Title-Case
  spelling to exactly one lowercase "word" match (D4 grammar-owned
  case folding);
- every recognized match spans exactly its raw text (half-open
  [start, end) offsets, raw_text slicing back to the source).
"""

from __future__ import annotations

import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.Currency.contract import CurrencyContract
from paxman.capabilities.Currency.grammar.code_recognition import CodeRecognition
from paxman.capabilities.Currency.grammar.symbol_recognition import SymbolRecognition
from paxman.capabilities.Currency.grammar.word_recognition import WordRecognition
from paxman.capabilities.Currency.rules.data.cldr_currencies import NAME_TO_CODES
from paxman.capabilities.Currency.rules.data.iso4217_list_one import CURRENCY_CODES
from paxman.capabilities.Currency.rules.iso_4217_ed2015 import SectionCode

# Alphabet for the span-invariant fuzz: ASCII letters (code/word grammars),
# digits and punctuation (boundary/glue rejection), plus the non-ASCII
# symbol glyphs only the symbol grammar matches (EUR, GBP, won signs).
_CURRENCY_ALPHABET = (
    string.ascii_letters + string.digits + string.punctuation + "\u20ac\u00a3\u20a9"
)


@pytest.mark.property
@given(t=st.text(alphabet=string.ascii_letters, min_size=3, max_size=3))
def test_standalone_code_folds_to_uppercase(t: str) -> None:
    """D3: any standalone 3-letter ASCII token folds to one uppercase code."""
    matches = CodeRecognition().recognize(t)
    assert len(matches) == 1
    assert matches[0].notation.text == t.upper()
    assert matches[0].notation.shape == "code"


@pytest.mark.property
@given(c=st.sampled_from(sorted(CURRENCY_CODES)))
def test_known_code_recognized_and_validated(c: str) -> None:
    """Every CURRENCY_CODES code is recognized and passes Section-code."""
    matches = CodeRecognition().recognize(c)
    assert len(matches) == 1
    assert matches[0].notation.text == c
    assert SectionCode().matches(matches[0].notation, CurrencyContract()) is True


@pytest.mark.property
@given(w=st.sampled_from(sorted(NAME_TO_CODES)))
def test_title_case_word_folds_to_lowercase(w: str) -> None:
    """D4: a lowercase CLDR word folds back from its Title-Case spelling."""
    matches = WordRecognition().recognize(w.title())
    assert len(matches) == 1
    assert matches[0].notation.text == w
    assert matches[0].notation.shape == "word"


@pytest.mark.property
@given(text=st.text(alphabet=_CURRENCY_ALPHABET, max_size=40))
def test_recognized_matches_have_consistent_spans(text: str) -> None:
    """Every match spans exactly its raw_text (half-open [start, end))."""
    grammars = [CodeRecognition(), SymbolRecognition(), WordRecognition()]
    for grammar in grammars:
        for match in grammar.recognize(text):
            assert 0 <= match.start <= match.end
            assert match.end - match.start == len(match.raw_text)
            assert match.raw_text == text[match.start : match.end]
