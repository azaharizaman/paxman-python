"""Hypothesis property tests for the SI Unit capability.

Each property locks a mathematical invariant of recognition using an
independently derived expectation:

- any symbol token from SYMBOL_TOKENS is recognized case-exactly as
  itself with shape "symbol" (D6 — the symbol grammar never folds
  case);
- any lowercase official unit name folds back from its Title-Case
  spelling to exactly one lowercase "name" match (D4 grammar-owned
  case folding);
- any prefixed unit name is recognized and passes the BIPM Section
  names rule (name → symbol resolution);
- any compound built from two compoundable symbol tokens — SYMBOL_TOKENS
  minus the glyph-only factors °, ′, ″ — joined by "/" yields exactly
  one "compound" match;
- every recognized match spans exactly its raw text (half-open
  [start, end) offsets, raw_text slicing back to the source).
"""

from __future__ import annotations

import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.SIUnit.contract import SIUnitContract
from paxman.capabilities.SIUnit.grammar.compound_recognition import CompoundRecognition
from paxman.capabilities.SIUnit.grammar.data.unit_symbol_tokens import SYMBOL_TOKENS
from paxman.capabilities.SIUnit.grammar.name_recognition import NameRecognition
from paxman.capabilities.SIUnit.grammar.symbol_recognition import SymbolRecognition
from paxman.capabilities.SIUnit.rules.bipm_si_brochure_ed2019 import SectionNames
from paxman.capabilities.SIUnit.rules.data.prefixed_unit_names import (
    PREFIXED_NAME_TO_SYMBOL,
)
from paxman.capabilities.SIUnit.rules.data.unit_names import NAME_TO_SYMBOL

# Alphabet for the span-invariant fuzz: ASCII letters and digits (symbol
# and name token characters), punctuation (boundary/glue rejection), plus
# the non-ASCII glyphs the grammars match or treat as boundaries — the
# degree sign, micro sign, middle dot, superscript digits, superscript
# minus, prime/double-prime (arcminute/arcsecond), Å, Ω, and the dot
# operator separator.
_SI_ALPHABET = (
    string.ascii_letters
    + string.digits
    + string.punctuation
    + "\u00b0\u00b5\u00b7\u00b2\u00b3\u2070\u2074\u2075\u2076\u2077\u2078\u2079\u207b"
    + "\u2032\u2033\u00c5\u03a9\u22c5"
)

# Glyph-only plane-angle units (BIPM Table 8) are present in SYMBOL_TOKENS
# but are NOT compound factors: the compound grammar's _UNIT class is
# letter-based ([A-Za-zµΩÅ]) with a "°" prefix only to compose "°C" — a
# bare °/′/″ factor is never a unit. No §1 locked row requires a
# bare-glyph compound (e.g. "m/°C" composes via the "°C" token itself),
# so excluding them keeps the compound invariant deterministic over the
# lexicon the grammar actually composes.
_NON_COMPOUND_FACTORS: frozenset[str] = frozenset({"\u00b0", "\u2032", "\u2033"})
_COMPOUNDABLE_TOKENS: tuple[str, ...] = tuple(
    t for t in sorted(SYMBOL_TOKENS) if t not in _NON_COMPOUND_FACTORS
)


@pytest.mark.property
@given(t=st.sampled_from(sorted(SYMBOL_TOKENS)))
def test_symbol_token_recognized_case_exact(t: str) -> None:
    """D6: every symbol token is recognized case-exactly as itself."""
    matches = SymbolRecognition().recognize(t)
    assert len(matches) == 1
    assert matches[0].notation.text == t
    assert matches[0].notation.shape == "symbol"


@pytest.mark.property
@given(n=st.sampled_from(sorted(NAME_TO_SYMBOL)))
def test_lowercase_name_folds_from_title_case(n: str) -> None:
    """D4: a lowercase name folds back from its Title-Case spelling."""
    matches = NameRecognition().recognize(n.title())
    assert len(matches) == 1
    assert matches[0].notation.text == n
    assert matches[0].notation.shape == "name"


@pytest.mark.property
@given(pn=st.sampled_from(sorted(PREFIXED_NAME_TO_SYMBOL)))
def test_prefixed_name_recognized_and_validated(pn: str) -> None:
    """Every prefixed name is recognized and passes the BIPM names rule."""
    matches = NameRecognition().recognize(pn)
    assert len(matches) == 1
    assert matches[0].notation.text == pn
    assert SectionNames().matches(matches[0].notation, SIUnitContract()) is True


@pytest.mark.property
@given(
    a=st.sampled_from(_COMPOUNDABLE_TOKENS),
    b=st.sampled_from(_COMPOUNDABLE_TOKENS),
)
def test_compound_shape_recognized(a: str, b: str) -> None:
    """Any two compoundable symbols joined by "/" form exactly one compound."""
    ct = f"{a}/{b}"
    matches = CompoundRecognition().recognize(ct)
    assert len(matches) == 1
    assert matches[0].notation.shape == "compound"


@pytest.mark.property
@given(text=st.text(alphabet=_SI_ALPHABET, max_size=40))
def test_recognized_matches_have_consistent_spans(text: str) -> None:
    """Every match spans exactly its raw_text (half-open [start, end))."""
    grammars = [SymbolRecognition(), NameRecognition(), CompoundRecognition()]
    for grammar in grammars:
        for match in grammar.recognize(text):
            assert 0 <= match.start <= match.end
            assert match.end - match.start == len(match.raw_text)
            assert match.raw_text == text[match.start : match.end]
