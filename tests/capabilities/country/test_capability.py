"""Tests for Country capability."""

import pytest
from paxman.capabilities.Country.notation import CountryNotation


class TestCountryNotation:
    """Tests for CountryNotation dataclass."""

    def test_creates_with_fields(self) -> None:
        """Verify field access."""
        notation = CountryNotation(shape="alpha2", value="US")
        assert notation.shape == "alpha2"
        assert notation.value == "US"

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        notation = CountryNotation(shape="alpha2", value="US")
        with pytest.raises(AttributeError):
            notation.shape = "alpha3"  # type: ignore[misc]

    def test_as_list_returns_correct(self) -> None:
        """Verify list conversion."""
        notation = CountryNotation(shape="alpha2", value="US")
        assert notation.as_list() == ["alpha2", "US"]

    def test_as_list_preserves_order(self) -> None:
        """Verify field order matches list order."""
        notation = CountryNotation(shape="name", value="United States")
        result = notation.as_list()
        assert result[0] == notation.shape
        assert result[1] == notation.value

    def test_equality(self) -> None:
        """Verify value equality."""
        n1 = CountryNotation(shape="alpha2", value="US")
        n2 = CountryNotation(shape="alpha2", value="US")
        assert n1 == n2

    def test_inequality(self) -> None:
        """Verify different values are not equal."""
        n1 = CountryNotation(shape="alpha2", value="US")
        n2 = CountryNotation(shape="alpha2", value="GB")
        assert n1 != n2

    def test_hashable(self) -> None:
        """Verify it can be used in sets or as dict keys."""
        n1 = CountryNotation(shape="alpha2", value="US")
        n2 = CountryNotation(shape="alpha2", value="US")
        s = {n1, n2}
        assert len(s) == 1
        d = {n1: "value"}
        assert d[n2] == "value"
