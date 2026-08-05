"""Hypothesis property tests for the ISBN capability.

Each property locks a mathematical invariant of recognition, hyphenation, or
check-digit conversion using an independently derived expectation:

- a grammar-recognized ISBN-13 that the ISO 2108 §5.3 rule accepts always
  carries the check digit independently recomputed from the first 12 digits,
  while a recognized ISBN-13 whose final digit was mutated is rejected by the
  rule — recognition is shape-only and never validates the check digit;
- hyphenation is presentation only: stripping separators never alters the
  digit content of a 13-digit ISBN;
- the ISBN-10 rule's 978-folded ISBN-13 conversion agrees with the
  independently derived ISBN-13 check digit, so a valid ISBN-10 and its
  converted ISBN-13 canonicalize to the same value.
"""

from __future__ import annotations

import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.ISBN.capability import ISBNCapability
from paxman.capabilities.ISBN.contract import ISBNContract
from paxman.capabilities.ISBN.grammar.isbn13_recognition import (
    ISBN13RecognitionGrammar,
)
from paxman.capabilities.ISBN.notation import ISBNNotation
from paxman.capabilities.ISBN.rules.isbn_users_manual_ed2012 import (
    Section6Isbn10CheckDigit,
)
from paxman.capabilities.ISBN.rules.iso_2108_ed2017 import (
    Section53Isbn13CheckDigit,
)


def _check_digit_isbn13(first12: str) -> str:
    """ISO 2108 §5.3 check digit: alternating 1/3 weights, mod 10."""
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(first12))
    return str((10 - total % 10) % 10)


def _check_digit_isbn10(first9: str) -> str:
    """Users' Manual §6 check digit: weights 10..2, mod 11; 10 -> 'X'."""
    total = sum(int(d) * (10 - i) for i, d in enumerate(first9))
    rem = total % 11
    if rem == 0:
        return "0"
    return str(11 - rem) if 11 - rem < 10 else "X"


@pytest.mark.property
@given(
    prefix=st.sampled_from(("978", "979")),
    core=st.text(alphabet=string.digits, min_size=9, max_size=9),
)
def test_isbn13_correct_check_digit_recognized_and_rule_accepted(
    prefix: str, core: str
) -> None:
    """Positive acceptance: a valid ISBN-13 is recognized and rule-validated.

    For every ISBN-13 built from a GS1 prefix, nine digits, and the
    independently derived check digit, the grammar must recognize it and the
    ISO 2108 §5.3 rule must accept it — recognition, validation, and the
    independent derivation can never disagree.
    """
    value = prefix + core + _check_digit_isbn13(prefix + core)
    grammar = ISBN13RecognitionGrammar()
    rule = Section53Isbn13CheckDigit()
    contract = ISBNContract()
    matches = [m for m in grammar.recognize(value) if m.notation.digits == value]
    assert matches
    notation = ISBNNotation(shape="isbn13", digits=value)
    assert rule.matches(notation, contract) is True
    assert value[-1] == _check_digit_isbn13(value[:12])


@pytest.mark.property
@given(
    prefix=st.sampled_from(("978", "979")),
    core=st.text(alphabet=string.digits, min_size=9, max_size=9),
)
def test_isbn13_mutated_check_digit_recognized_but_rule_rejected(
    prefix: str, core: str
) -> None:
    """Recognition is shape-only: a mutated check digit is still recognized.

    The grammar matches 13-digit structure regardless of check-digit validity,
    so an ISBN-13 with a wrong final digit is recognized but the ISO 2108 §5.3
    rule must reject it — recognition and validation stay decoupled.
    """
    value = prefix + core + _check_digit_isbn13(prefix + core)
    mutated = value[:-1] + str((int(value[-1]) + 1) % 10)
    grammar = ISBN13RecognitionGrammar()
    rule = Section53Isbn13CheckDigit()
    contract = ISBNContract()
    matches = [m for m in grammar.recognize(mutated) if m.notation.digits == mutated]
    assert matches
    notation = ISBNNotation(shape="isbn13", digits=mutated)
    assert rule.matches(notation, contract) is False


@pytest.mark.property
@given(value=st.text(alphabet=string.digits, min_size=13, max_size=13))
def test_hyphenate_round_trips_digits(value: str) -> None:
    """Hyphenation never alters the digit content of a 13-digit ISBN."""
    cap = ISBNCapability()
    notation = ISBNNotation(shape="isbn13", digits=value)
    hyphenated = cap.format_value(value, "hyphenated", notation)
    assert "".join(c for c in hyphenated if c.isdigit()) == value


@pytest.mark.property
@given(first9=st.text(alphabet=string.digits, min_size=9, max_size=9))
def test_isbn10_and_converted_isbn13_agree(first9: str) -> None:
    """A valid ISBN-10 converts to the same value as its 978-folded ISBN-13.

    The ISBN-10 rule's normalize() path must agree with the independent
    ISBN-13 derivation, so a valid ISBN-10 and its converted ISBN-13
    canonicalize to the same value.
    """
    isbn10 = first9 + _check_digit_isbn10(first9)
    notation10 = ISBNNotation(shape="isbn10", digits=isbn10)
    rule = Section6Isbn10CheckDigit()
    contract = ISBNContract()
    assert rule.matches(notation10, contract) is True
    expected13 = "978" + first9 + _check_digit_isbn13("978" + first9)
    assert rule.normalize(notation10, contract) == expected13
