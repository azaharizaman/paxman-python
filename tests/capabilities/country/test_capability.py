"""Tests for Country capability."""

import pytest

from paxman.capabilities.Country.capability import CountryCapability
from paxman.capabilities.Country.contract import VALID_OUTPUT_FORMATS, CountryContract
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.capability import Capability
from paxman.core.errors import ContractError


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

    def test_default_include_localized(self) -> None:
        """Verify include_localized defaults to False."""
        contract = CountryContract()
        assert contract.include_localized is False

    def test_default_include_historical(self) -> None:
        """Verify include_historical defaults to False."""
        contract = CountryContract()
        assert contract.include_historical is False

    def test_active_grammars_defaults_to_all_shipped(self) -> None:
        """No override: the engine runs every shipped grammar (fallback).

        The contract declares no active_grammars (None — the base default),
        and the capability ships exactly the four recognition grammars.
        """
        contract = CountryContract()
        assert contract.active_grammars is None
        assert [g.name for g in CountryCapability().get_grammars()] == [
            "alpha2_recognition",
            "alpha3_recognition",
            "numeric_recognition",
            "name_recognition",
        ]

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
        )
        assert contract.include_localized is True
        assert contract.include_historical is True

    def test_default_output_format(self) -> None:
        """Verify output_format defaults to alpha2."""
        contract = CountryContract()
        assert contract.output_format == "alpha2"

    def test_valid_output_formats_compatibility_surface(self) -> None:
        """The legacy module constant retains the complete format set."""
        assert frozenset({"alpha2", "alpha3", "numeric", "name"}) == (
            VALID_OUTPUT_FORMATS
        )
        assert {
            CountryContract.DEFAULT_OUTPUT_FORMAT,
            *CountryContract.OFFERED_OUTPUT_FORMATS,
        } == VALID_OUTPUT_FORMATS

    def test_custom_output_format_alpha3(self) -> None:
        """Verify output_format can be set to alpha3."""
        contract = CountryContract(output_format="alpha3")
        assert contract.output_format == "alpha3"

    def test_custom_output_format_numeric(self) -> None:
        """Verify output_format can be set to numeric."""
        contract = CountryContract(output_format="numeric")
        assert contract.output_format == "numeric"

    def test_custom_output_format_name(self) -> None:
        """Verify output_format can be set to name."""
        contract = CountryContract(output_format="name")
        assert contract.output_format == "name"

    def test_invalid_output_format_raises_contract_error(self) -> None:
        """Verify invalid output_format raises ContractError."""
        with pytest.raises(ContractError):
            CountryContract(output_format="invalid")

    def test_output_format_default_resolves_to_alpha2(self) -> None:
        """'default' reverts to the default alpha2 output."""
        contract = CountryContract(output_format="default")
        assert contract.output_format == "alpha2"

    @pytest.mark.parametrize("fmt", ["none", "", "ISO"])
    def test_invalid_output_format_variants_raise_contract_error(
        self, fmt: str
    ) -> None:
        """'none', '', and other unoffered values are contract violations."""
        with pytest.raises(ContractError):
            CountryContract(output_format=fmt)


class TestCountryCapability:
    """Tests for CountryCapability wiring."""

    def test_is_capability_subclass(self) -> None:
        """Verify isinstance check."""
        cap = CountryCapability()
        assert isinstance(cap, Capability)

    def test_name(self) -> None:
        """Verify name matches expected value."""
        assert CountryCapability.name == "country"

    def test_get_grammars_returns_all(self) -> None:
        """Verify grammar count (4)."""
        cap = CountryCapability()
        grammars = cap.get_grammars()
        assert len(grammars) == 4

    def test_get_rules_returns_all(self) -> None:
        """Verify rule count (6)."""
        cap = CountryCapability()
        rules = cap.get_rules()
        assert len(rules) == 6

    def test_grammar_names(self) -> None:
        """Verify grammar names follow convention."""
        cap = CountryCapability()
        names = [g.name for g in cap.get_grammars()]
        assert "alpha2_recognition" in names
        assert "alpha3_recognition" in names
        assert "numeric_recognition" in names
        assert "name_recognition" in names

    def test_rule_names(self) -> None:
        """Verify rule names follow convention."""
        cap = CountryCapability()
        names = [r.name for r in cap.get_rules()]
        assert "Section-alpha2-codes" in names
        assert "Section-alpha3-codes" in names
        assert "Section-numeric-codes" in names
        assert "Section-names" in names
        assert "Section-localized-names" in names
        assert "Section-historical-names" in names

    def test_create_contract(self) -> None:
        """Verify create_contract factory method."""
        contract = CountryCapability.create_contract()
        assert contract.capability_name == "country"
        assert contract.include_localized is False
        assert contract.include_historical is False

    def test_create_contract_with_options(self) -> None:
        """Verify create_contract passes through all options."""
        contract = CountryCapability.create_contract(
            include_localized=True,
            include_historical=True,
            year=2024,
        )
        assert contract.include_localized is True
        assert contract.include_historical is True
        assert contract.year == 2024

    def test_create_contract_default_output_format(self) -> None:
        """Verify create_contract defaults to alpha2."""
        contract = CountryCapability.create_contract()
        assert contract.output_format == "alpha2"

    def test_create_contract_with_output_format(self) -> None:
        """Verify create_contract passes through output_format."""
        contract = CountryCapability.create_contract(output_format="numeric")
        assert contract.output_format == "numeric"

    def test_create_contract_all_formats(self) -> None:
        """Verify all valid output_format values pass through create_contract."""
        for fmt in ("alpha2", "alpha3", "numeric", "name"):
            contract = CountryCapability.create_contract(output_format=fmt)
            assert contract.output_format == fmt


@pytest.mark.capability
class TestCountryCapabilityFormatValue:
    """Tests for CountryCapability.format_value()."""

    NOTATION = CountryNotation(shape="alpha2", value="DE")

    def test_alpha2_format_is_identity(self) -> None:
        """The default alpha-2 path returns the canonical value unchanged."""
        cap = CountryCapability()
        assert cap.format_value("DE", "alpha2", self.NOTATION) == "DE"

    def test_default_format_is_identity(self) -> None:
        """An unset output format returns the canonical value unchanged."""
        cap = CountryCapability()
        assert cap.format_value("DE", None, self.NOTATION) == "DE"

    def test_alpha3_format_maps_current_alpha2(self) -> None:
        """Alpha-3 rendering maps the canonical alpha-2 code."""
        cap = CountryCapability()
        assert cap.format_value("DE", "alpha3", self.NOTATION) == "DEU"

    def test_numeric_format_maps_current_alpha2(self) -> None:
        """Numeric rendering maps the canonical alpha-2 code."""
        cap = CountryCapability()
        assert cap.format_value("DE", "numeric", self.NOTATION) == "276"

    def test_name_format_maps_current_alpha2(self) -> None:
        """Name rendering maps the canonical alpha-2 code."""
        cap = CountryCapability()
        assert cap.format_value("DE", "name", self.NOTATION) == "GERMANY"

    @pytest.mark.parametrize("fmt", ["alpha3", "numeric", "name"])
    def test_former_code_without_current_mapping_passes_through(self, fmt: str) -> None:
        """Former codes absent from the current tables pass through unchanged.

        ``SU`` (USSR) has no entry in the current ISO 3166-1 conversion
        tables, so alpha-3/numeric/name requests return it unchanged rather
        than fabricating a current-code mapping.
        """
        cap = CountryCapability()
        assert cap.format_value("SU", fmt, self.NOTATION) == "SU"

    def test_former_name_with_name_shape_preserves_historical_code(self) -> None:
        """A former name (name shape) preserves its historical alpha-2 code.

        A name-shaped notation for a former name resolves to the historical
        entity's own code (``USSR`` → ``SU``); requesting an alternative
        format must return that code unchanged rather than fabricating a
        current-code conversion.
        """
        cap = CountryCapability()
        notation = CountryNotation(shape="name", value="USSR")
        assert cap.format_value("SU", "alpha3", notation) == "SU"
