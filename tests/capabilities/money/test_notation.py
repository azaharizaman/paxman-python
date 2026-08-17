"""Tests for Money notation."""

import dataclasses

import pytest

from paxman.capabilities.Money.notation import MoneyNotation

pytestmark = [pytest.mark.capability]


def test_notation_frozen_and_slots() -> None:
    """Notation must be a frozen, slots-based dataclass."""
    assert dataclasses.is_dataclass(MoneyNotation)
    assert "__slots__" in MoneyNotation.__dict__


def test_notation_fields() -> None:
    """Notation fields are exactly the four component fields."""
    assert [f.name for f in dataclasses.fields(MoneyNotation)] == [
        "currency_part",
        "amount_part",
        "currency_shape",
        "amount_shape",
    ]


def test_field_defaults() -> None:
    """Shape fields default to the empty unset sentinel."""
    notation = MoneyNotation(currency_part="USD", amount_part="500")
    assert notation.currency_shape == ""
    assert notation.amount_shape == ""


def test_shape_value_validation() -> None:
    """Invalid shape values raise ValueError at construction."""
    with pytest.raises(ValueError):
        MoneyNotation(currency_part="USD", amount_part="500", currency_shape="bogus")
    with pytest.raises(ValueError):
        MoneyNotation(currency_part="USD", amount_part="500", amount_shape="bogus")


def test_valid_shapes_accepted() -> None:
    """Every enumerated shape value is accepted; the empty sentinel is too."""
    for shape in ("code", "symbol", "qualified_symbol", "word"):
        MoneyNotation(currency_part="USD", amount_part="500", currency_shape=shape)
    for shape in (
        "integer",
        "dot_decimal",
        "comma_decimal",
        "space_decimal",
        "accounting",
    ):
        MoneyNotation(currency_part="USD", amount_part="500", amount_shape=shape)
    MoneyNotation(currency_part="USD", amount_part="500")


def test_notation_hashable() -> None:
    """Equal instances hash equal."""
    a = MoneyNotation(currency_part="USD", amount_part="500")
    b = MoneyNotation(currency_part="USD", amount_part="500")
    assert hash(a) == hash(b)
    assert a == b


def test_notation_equality_inequality() -> None:
    """Equal instances compare equal; differing fields do not."""
    a = MoneyNotation(currency_part="USD", amount_part="500")
    b = MoneyNotation(currency_part="USD", amount_part="500")
    c = MoneyNotation(currency_part="EUR", amount_part="500")
    assert a == b
    assert a != c


def test_notation_immutable() -> None:
    """Assigning a field raises FrozenInstanceError."""
    notation = MoneyNotation(currency_part="USD", amount_part="500")
    with pytest.raises(dataclasses.FrozenInstanceError):
        notation.amount_part = "600"  # type: ignore[misc]
