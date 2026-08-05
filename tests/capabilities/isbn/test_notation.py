"""Tests for ISBN notation."""

import dataclasses

import pytest

from paxman.capabilities.ISBN.notation import ISBNNotation

pytestmark = [pytest.mark.capability]


def test_notation_frozen_and_slots() -> None:
    """Notation must be a frozen, slots-based dataclass."""
    assert dataclasses.is_dataclass(ISBNNotation)
    assert "__slots__" in ISBNNotation.__dict__


def test_notation_fields() -> None:
    """Notation fields are exactly shape and digits."""
    assert [f.name for f in dataclasses.fields(ISBNNotation)] == ["shape", "digits"]


def test_as_list() -> None:
    """as_list bridges to the generic list[str] interface."""
    notation = ISBNNotation(shape="isbn13", digits="9780306406157")
    assert notation.as_list() == ["isbn13", "9780306406157"]


def test_notation_hashable() -> None:
    """Equal instances hash equal."""
    a = ISBNNotation(shape="isbn10", digits="0306406152")
    b = ISBNNotation(shape="isbn10", digits="0306406152")
    assert hash(a) == hash(b)
    assert a == b


def test_notation_immutable() -> None:
    """Assigning a field raises FrozenInstanceError."""
    notation = ISBNNotation(shape="isbn13", digits="9780306406157")
    with pytest.raises(dataclasses.FrozenInstanceError):
        notation.digits = "x"  # type: ignore[misc]
