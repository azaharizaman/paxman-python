"""Hypothesis property tests for the Money capability.

Each property locks a mathematical invariant of parsing, formatting, or the
full pipeline using an independently derived expectation:

- repeated runs over the same input and contract are byte-identical
  (canonical determinism);
- format_amount then parse_amount round-trips the value for conforming
  precision;
- random ASCII input never raises and every status is well-formed;
- every SUCCESS canonical value matches ``CODE amount`` shape and carries
  exactly the code's ISO 4217 minor units.
"""

from __future__ import annotations

import re
import string
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.Money.capability import MoneyCapability
from paxman.capabilities.Money.parsing import ParsedAmount, format_amount, parse_amount
from paxman.capabilities.Money.rules.data.iso4217_list_one import MINOR_UNITS
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.engine.orchestrator import run_capability

_CANONICAL_SHAPE = re.compile(r"[A-Z]{3} \d+(\.\d+)?")


@pytest.fixture(autouse=True)
def _fresh_registry() -> None:
    """Reset the registry and register Money before and after each test.

    Registration happens once per test, before the hypothesis examples run;
    ``run_capability`` freezes the registry on the first example, which is
    fine because the capability is already present.
    """
    reset_registry()
    register_capability(MoneyCapability())
    yield
    reset_registry()


@pytest.mark.property
@given(text=st.text(alphabet=string.printable, max_size=120))
def test_canonical_determinism(text: str) -> None:
    """Same input + same contract -> byte-identical ExecutionResult."""
    contract = MoneyCapability.create_contract()
    result1 = run_capability(text, contract)
    result2 = run_capability(text, contract)
    assert result1 == result2
    assert result1.status == result2.status
    assert result1.canonicalized_value == result2.canonicalized_value
    assert {c.value for c in result1.candidates} == {
        c.value for c in result2.candidates
    }


@pytest.mark.property
@given(
    integer=st.text(alphabet=string.digits, min_size=1, max_size=9),
    fraction=st.text(alphabet=string.digits, min_size=0, max_size=2),
)
def test_parse_format_round_trip_preserves_value(integer: str, fraction: str) -> None:
    """format_amount then parse_amount returns the same value."""
    parsed = ParsedAmount(integer=integer.lstrip("0") or "0", fraction=fraction)
    assert parsed.decimal_digits() <= 2
    formatted = format_amount(parsed, 2, "strict")
    reparsed = parse_amount(formatted)
    assert reparsed is not None
    assert Decimal(reparsed.to_decimal_string()) == Decimal(parsed.to_decimal_string())
    assert format_amount(reparsed, 2, "strict") == formatted


@pytest.mark.property
@given(text=st.text(alphabet=string.printable, max_size=120))
def test_fuzz_random_text_never_raises(text: str) -> None:
    """Random ASCII input never raises; every status is well-formed."""
    contract = MoneyCapability.create_contract()
    result = run_capability(text, contract)
    assert result.status in {
        Resolution.MISSING,
        Resolution.INVALID,
        Resolution.SUCCESS,
        Resolution.AMBIGUOUS,
    }
    assert (result.canonicalized_value is not None) == (
        result.status == Resolution.SUCCESS
    )
    assert isinstance(result.version_stamp.paxman_version, str)
    if result.status == Resolution.SUCCESS:
        assert len(result.candidates) >= 1
        assert {c.value for c in result.candidates} == {result.canonicalized_value}
        authorities = {p.authority for c in result.candidates for p in c.provenance}
        assert authorities and all(authorities)


@pytest.mark.property
@given(text=st.text(alphabet=string.printable, max_size=120))
def test_success_canonical_shape(text: str) -> None:
    """Every SUCCESS value matches CODE amount with the code's minor units."""
    contract = MoneyCapability.create_contract()
    result = run_capability(text, contract)
    if result.status != Resolution.SUCCESS:
        return
    value = result.canonicalized_value
    assert value is not None
    assert _CANONICAL_SHAPE.fullmatch(value) is not None
    code, _, amount = value.partition(" ")
    if "." in amount:
        assert len(amount.split(".", 1)[1]) == MINOR_UNITS[code]
    else:
        assert MINOR_UNITS[code] == 0
