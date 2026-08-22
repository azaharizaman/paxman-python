"""Hypothesis property tests for the ISSN capability.

Each property locks a mathematical invariant of recognition, validation,
or presentation using an independently derived expectation:

- a valid ISSN built from 7 random digits plus the independently derived
  mod-11 check digit always round-trips to SUCCESS with the hyphenated
  canonical form;
- a random 8-digit string that is not a valid ISSN is INVALID with high
  probability (only 1/11 random strings pass the mod-11 check);
- hyphenated and bare inputs for the same valid ISSN canonicalize to the
  identical hyphenated value;
- output_format only changes rendering: hyphenated is identity, compact
  strips the hyphen, urn wraps the hyphenated form;
- lower-case ``x`` as check digit folds to upper-case ``X`` and both
  canonicalize identically.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

import paxman
from paxman.capabilities import ISSN
from paxman.capabilities.ISSN.capability import ISSNCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution

_ISSN_CAP = ISSNCapability
_ = ISSN  # keep required import used


@pytest.fixture(autouse=True)
def _fresh_registry() -> None:
    """Reset the registry and register ISSN before and after each test.

    Registration happens once per test before hypothesis examples run;
    ``paxman.canonicalize`` freezes the registry on the first example,
    which is fine because ISSN is already present.
    """

    reset_registry()
    register_capability(_ISSN_CAP())
    yield
    reset_registry()


def _issn_check_char(digits7: list[int]) -> str:
    # Check digit derived independently of the capability's rule implementation:
    # total = sum(int(d) * (8 - i) for i, d in enumerate(digits[:7]))
    # check = (11 - total % 11) % 11
    # "X" if check == 10 else str(check)
    total = sum(int(d) * (8 - i) for i, d in enumerate(digits7))
    check = (11 - total % 11) % 11
    return "X" if check == 10 else str(check)


def _build_digits(digits7: list[int]) -> str:
    return "".join(str(d) for d in digits7) + _issn_check_char(digits7)


@pytest.mark.property
@given(digits7=st.lists(st.integers(0, 9), min_size=7, max_size=7))
def test_generate_valid_issn_round_trip(digits7: list[int]) -> None:
    """A valid ISSN built from mod-11 always round-trips to SUCCESS hyphenated."""

    digits = _build_digits(digits7)
    hyphenated = f"{digits[:4]}-{digits[4:]}"
    contract = _ISSN_CAP.create_contract()
    result = paxman.canonicalize(digits, contract)
    assert result.status == Resolution.SUCCESS
    assert result.canonicalized_value == hyphenated
    # Hyphenated input must yield the same canonical value.
    result_h = paxman.canonicalize(hyphenated, contract)
    assert result_h.status == Resolution.SUCCESS
    assert result_h.canonicalized_value == hyphenated


@pytest.mark.property
@given(text=st.text(alphabet="0123456789", min_size=8, max_size=8))
def test_random_8char_is_invalid_high_prob(text: str) -> None:
    """Random 8-digit strings are INVALID with high probability.

    Only strings whose final char equals the independently derived mod-11
    check are valid; the rest are INVALID. Valid cases are skipped via
    assume so the INVALID assertion stays deterministic.
    """

    digits7 = [int(c) for c in text[:7]]
    total = sum(int(d) * (8 - i) for i, d in enumerate(digits7))
    check = (11 - total % 11) % 11
    expected = "X" if check == 10 else str(check)
    if text[7].upper() == expected:
        assume(False)
    contract = _ISSN_CAP.create_contract()
    result = paxman.canonicalize(text, contract)
    assert result.status == Resolution.INVALID


@pytest.mark.property
@given(digits7=st.lists(st.integers(0, 9), min_size=7, max_size=7))
def test_hyphenated_vs_bare_same_value(digits7: list[int]) -> None:
    """Hyphenated and bare inputs for the same valid ISSN yield identical value."""

    digits = _build_digits(digits7)
    hyphenated = f"{digits[:4]}-{digits[4:]}"
    contract = _ISSN_CAP.create_contract()
    r_bare = paxman.canonicalize(digits, contract)
    r_hyph = paxman.canonicalize(hyphenated, contract)
    assert r_bare.status == Resolution.SUCCESS
    assert r_hyph.status == Resolution.SUCCESS
    assert r_bare.canonicalized_value == r_hyph.canonicalized_value
    assert r_bare.canonicalized_value == hyphenated


@pytest.mark.property
@given(digits7=st.lists(st.integers(0, 9), min_size=7, max_size=7))
def test_compact_vs_hyphenated_same_identity(digits7: list[int]) -> None:
    """output_format only changes rendering; identity is hyphenated."""

    digits = _build_digits(digits7)
    hyphenated = f"{digits[:4]}-{digits[4:]}"
    c_default = _ISSN_CAP.create_contract()
    c_compact = _ISSN_CAP.create_contract(output_format="compact")
    c_urn = _ISSN_CAP.create_contract(output_format="urn")
    r_default = paxman.canonicalize(digits, c_default)
    r_compact = paxman.canonicalize(digits, c_compact)
    r_urn = paxman.canonicalize(digits, c_urn)
    assert r_default.status == Resolution.SUCCESS
    assert r_compact.status == Resolution.SUCCESS
    assert r_urn.status == Resolution.SUCCESS
    assert r_default.canonicalized_value == hyphenated
    assert r_compact.canonicalized_value == digits
    assert r_urn.canonicalized_value == f"urn:issn:{hyphenated}"
    assert r_compact.canonicalized_value == r_default.canonicalized_value.replace(
        "-", ""
    )


@pytest.mark.property
@given(digits7=st.lists(st.integers(0, 9), min_size=7, max_size=7))
def test_x_uppercase_invariant(digits7: list[int]) -> None:
    """Lower-case x check digit folds to upper-case X."""

    digits = _build_digits(digits7)
    hyphenated = f"{digits[:4]}-{digits[4:]}"
    lower_hyphenated = hyphenated.lower()
    contract = _ISSN_CAP.create_contract()
    r_upper = paxman.canonicalize(hyphenated, contract)
    r_lower = paxman.canonicalize(lower_hyphenated, contract)
    assert r_upper.status == Resolution.SUCCESS
    assert r_lower.status == Resolution.SUCCESS
    assert r_upper.canonicalized_value == r_lower.canonicalized_value
    assert r_upper.canonicalized_value == r_upper.canonicalized_value.upper()
    assert r_lower.canonicalized_value == r_lower.canonicalized_value.upper()
    if digits.endswith("X"):
        assert r_lower.canonicalized_value.endswith("X")
        assert lower_hyphenated.endswith("x")
