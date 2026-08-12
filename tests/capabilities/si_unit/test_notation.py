"""Tests for SIUnitNotation."""

import dataclasses

import pytest

from paxman.capabilities.SIUnit.notation import SIUnitNotation


@pytest.mark.capability
@pytest.mark.si_unit
class TestSIUnitNotation:
    """Tests for SIUnitNotation."""

    def test_text_and_shape(self) -> None:
        n = SIUnitNotation(text="kg", shape="symbol")
        assert n.text == "kg"
        assert n.shape == "symbol"

    def test_rejects_empty_text(self) -> None:
        with pytest.raises(ValueError):
            SIUnitNotation(text="", shape="symbol")

    def test_rejects_unknown_shape(self) -> None:
        with pytest.raises(ValueError):
            SIUnitNotation(text="kg", shape="quantity")

    def test_as_list(self) -> None:
        n = SIUnitNotation(text="kg", shape="symbol")
        assert n.as_list() == ["kg", "symbol"]

    def test_frozen(self) -> None:
        n = SIUnitNotation(text="kg", shape="symbol")
        with pytest.raises(dataclasses.FrozenInstanceError):
            n.text = "m"  # type: ignore[misc]
