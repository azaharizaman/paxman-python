"""Tests for IBANNotation (scaffold)."""

import dataclasses

import pytest

from paxman.capabilities.IBAN.notation import IBANNotation


@pytest.mark.capability
class TestIBANNotation:
    """Tests for IBANNotation."""

    def test_value_attribute(self) -> None:
        n = IBANNotation(value="example")
        assert n.value == "example"

    def test_frozen(self) -> None:
        n = IBANNotation(value="example")
        with pytest.raises(dataclasses.FrozenInstanceError):
            n.value = "other"  # type: ignore[misc]
