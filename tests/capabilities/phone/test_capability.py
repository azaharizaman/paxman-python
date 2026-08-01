"""Tests for Phone capability."""

import pytest

from paxman.capabilities.Phone.contract import PhoneContract
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


class TestPhoneContract:
    """Tests for PhoneContract dataclass."""

    def test_default_capability_name(self) -> None:
        """Verify capability_name is fixed to 'phone'."""
        contract = PhoneContract()
        assert contract.capability_name == "phone"

    def test_capability_name_not_settable(self) -> None:
        """Verify capability_name is not user-settable."""
        with pytest.raises(TypeError):
            PhoneContract(capability_name="other")  # type: ignore[call-arg]

    def test_default_excluded_rules(self) -> None:
        """Verify excluded_rules defaults to empty tuple."""
        contract = PhoneContract()
        assert contract.excluded_rules == ()

    def test_default_pinned_rules(self) -> None:
        """Verify pinned_rules defaults to None."""
        contract = PhoneContract()
        assert contract.pinned_rules is None

    def test_default_year(self) -> None:
        """Verify year defaults to None."""
        contract = PhoneContract()
        assert contract.year is None

    def test_default_output_format(self) -> None:
        """Verify output_format defaults to 'e164'."""
        contract = PhoneContract()
        assert contract.output_format == "e164"

    def test_default_country_none(self) -> None:
        """Verify default_country defaults to None."""
        contract = PhoneContract()
        assert contract.default_country is None

    def test_custom_default_country(self) -> None:
        """Verify default_country can be set."""
        contract = PhoneContract(default_country="US")
        assert contract.default_country == "US"

    def test_custom_output_format(self) -> None:
        """Verify output_format can be set."""
        contract = PhoneContract(output_format="rfc3966")
        assert contract.output_format == "rfc3966"

    def test_active_grammars_returns_all(self) -> None:
        """Verify all 4 grammars are active by default."""
        contract = PhoneContract()
        grammars = contract.active_grammars
        assert len(grammars) == 4
        assert "e164_recognition" in grammars
        assert "tel_uri_recognition" in grammars
        assert "international_00_recognition" in grammars
        assert "national_recognition" in grammars

    def test_as_dict_contains_all_fields(self) -> None:
        """Verify as_dict serializes all fields."""
        contract = PhoneContract()
        d = contract.as_dict()
        assert "capability_name" in d
        assert "default_country" in d
        assert "output_format" in d
        assert "excluded_rules" in d
        assert "pinned_rules" in d
        assert "year" in d

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        contract = PhoneContract()
        with pytest.raises(AttributeError):
            contract.year = 2024  # type: ignore[misc]
