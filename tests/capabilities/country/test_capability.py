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


from paxman.capabilities.Country.contract import CountryContract


class TestCountryContract:
    """Tests for CountryContract dataclass."""

    def test_default_capability_name(self) -> None:
        """Verify capability_name is fixed to 'country'."""
        contract = CountryContract()
        assert contract.capability_name == "country"

    def test_capability_name_not_settable(self) -> None:
        """Verify capability_name is not user-settable."""
        with pytest.raises(TypeError):
            CountryContract(capability_name="other")  # type: ignore[call-arg]

    def test_default_excluded_rules(self) -> None:
        """Verify excluded_rules defaults to empty tuple."""
        contract = CountryContract()
        assert contract.excluded_rules == ()

    def test_default_pinned_rules(self) -> None:
        """Verify pinned_rules defaults to None."""
        contract = CountryContract()
        assert contract.pinned_rules is None

    def test_default_year(self) -> None:
        """Verify year defaults to None."""
        contract = CountryContract()
        assert contract.year is None

    def test_default_output_format(self) -> None:
        """Verify output_format defaults to None."""
        contract = CountryContract()
        assert contract.output_format is None

    def test_default_include_localized(self) -> None:
        """Verify include_localized defaults to False."""
        contract = CountryContract()
        assert contract.include_localized is False

    def test_default_include_historical(self) -> None:
        """Verify include_historical defaults to False."""
        contract = CountryContract()
        assert contract.include_historical is False

    def test_default_extra_synonyms(self) -> None:
        """Verify extra_synonyms defaults to empty dict."""
        contract = CountryContract()
        assert contract.extra_synonyms == {}

    def test_active_grammars_returns_all(self) -> None:
        """Verify all 4 grammars are active by default."""
        contract = CountryContract()
        grammars = contract.active_grammars
        assert len(grammars) == 4
        assert "alpha2_recognition" in grammars
        assert "alpha3_recognition" in grammars
        assert "numeric_recognition" in grammars
        assert "name_recognition" in grammars

    def test_as_dict_contains_all_fields(self) -> None:
        """Verify as_dict serializes all fields."""
        contract = CountryContract()
        d = contract.as_dict()
        assert "capability_name" in d
        assert "excluded_rules" in d
        assert "pinned_rules" in d
        assert "year" in d
        assert "output_format" in d
        assert "include_localized" in d
        assert "include_historical" in d
        assert "extra_synonyms" in d

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        contract = CountryContract()
        with pytest.raises(AttributeError):
            contract.year = 2024  # type: ignore[misc]

    def test_custom_fields(self) -> None:
        """Verify custom fields can be set."""
        contract = CountryContract(
            include_localized=True,
            include_historical=True,
            extra_synonyms={"my_alias": "MY"},
            output_format="alpha3",
        )
        assert contract.include_localized is True
        assert contract.include_historical is True
        assert contract.extra_synonyms == {"my_alias": "MY"}
        assert contract.output_format == "alpha3"
