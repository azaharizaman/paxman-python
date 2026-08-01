"""Tests for Phone capability."""

import pytest

from paxman.capabilities.Phone.notation import PhoneNotation


class TestPhoneNotation:
    """Tests for PhoneNotation dataclass."""

    def test_creates_with_fields(self) -> None:
        """Verify field access."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert notation.shape == "e164"
        assert notation.value == "15551234567"
        assert notation.extension == ""

    def test_creates_with_extension(self) -> None:
        """Verify extension field."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567", extension="890")
        assert notation.extension == "890"

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        with pytest.raises(AttributeError):
            notation.shape = "national"  # type: ignore[misc]

    def test_as_list_returns_correct(self) -> None:
        """Verify list conversion."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert notation.as_list() == ["e164", "15551234567", ""]

    def test_as_list_with_extension(self) -> None:
        """Verify list conversion includes extension."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567", extension="890")
        assert notation.as_list() == ["rfc3966", "15551234567", "890"]

    def test_equality(self) -> None:
        """Verify value equality."""
        n1 = PhoneNotation(shape="e164", value="15551234567")
        n2 = PhoneNotation(shape="e164", value="15551234567")
        assert n1 == n2

    def test_inequality(self) -> None:
        """Verify different values are not equal."""
        n1 = PhoneNotation(shape="e164", value="15551234567")
        n2 = PhoneNotation(shape="e164", value="15551234568")
        assert n1 != n2

    def test_hashable(self) -> None:
        """Verify it can be used in sets or as dict keys."""
        n1 = PhoneNotation(shape="e164", value="15551234567")
        n2 = PhoneNotation(shape="e164", value="15551234567")
        s = {n1, n2}
        assert len(s) == 1
        d = {n1: "value"}
        assert d[n2] == "value"
