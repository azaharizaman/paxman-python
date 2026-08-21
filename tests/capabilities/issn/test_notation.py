"""Tests for ISSNNotation."""

import dataclasses

import pytest

from paxman.capabilities.ISSN.notation import ISSNNotation


@pytest.mark.capability
class TestISSNNotation:
    """Tests for ISSNNotation."""

    def test_notation_frozen_and_slots(self) -> None:
        assert dataclasses.is_dataclass(ISSNNotation)
        assert "__slots__" in ISSNNotation.__dict__
        n = ISSNNotation(digits="03178471")
        assert n.digits == "03178471"

    def test_notation_fields(self) -> None:
        field_names = [f.name for f in dataclasses.fields(ISSNNotation)]
        assert field_names == ["digits"]

    def test_notation_hashable(self) -> None:
        a = ISSNNotation(digits="03178471")
        b = ISSNNotation(digits="03178471")
        assert a == b
        assert hash(a) == hash(b)
        s = {a, b}
        assert len(s) == 1

    def test_notation_immutable(self) -> None:
        n = ISSNNotation(digits="03178471")
        with pytest.raises(dataclasses.FrozenInstanceError):
            n.digits = "00000000"  # type: ignore[misc]

    def test_notation_digits_length(self) -> None:
        n = ISSNNotation(digits="03178471")
        assert n.digits == "03178471"
        assert len(n.digits) == 8
        # Uppercase X handled by grammar; notation stores whatever given
        m = ISSNNotation(digits="1050124X")
        assert m.digits == "1050124X"
