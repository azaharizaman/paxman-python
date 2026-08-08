# tests/capabilities/currency/test_notation.py
"""CurrencyNotation structural tests."""

from __future__ import annotations

import pytest

from paxman.capabilities.Currency.notation import CurrencyNotation

pytestmark = [pytest.mark.capability, pytest.mark.currency]


def test_frozen() -> None:
    notation = CurrencyNotation(text="USD", shape="code")
    with pytest.raises(AttributeError):
        notation.text = "EUR"  # type: ignore[misc]


def test_as_list() -> None:
    assert CurrencyNotation(text="US$", shape="qualified_symbol").as_list() == [
        "US$",
        "qualified_symbol",
    ]


@pytest.mark.parametrize(
    ("text", "shape"),
    [
        ("USD", "code"),
        ("usd", "code"),  # grammar folds; the notation may hold any casing pre-fold
        ("US$", "qualified_symbol"),
        ("€", "symbol"),
        ("euro", "word"),
    ],
)
def test_valid_shapes(text: str, shape: str) -> None:
    assert CurrencyNotation(text=text, shape=shape).shape == shape


@pytest.mark.parametrize(
    ("text", "shape"),
    [
        ("", "code"),
        ("USD", "amount"),      # not an identifier shape
        ("USD", "code+amount"),  # Money's shape vocabulary is out of scope
    ],
)
def test_invalid(text: str, shape: str) -> None:
    with pytest.raises(ValueError):
        CurrencyNotation(text=text, shape=shape)
