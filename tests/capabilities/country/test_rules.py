"""Tests for Country capability validation rules."""

from __future__ import annotations

import pytest

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.iso_3166_ed2024 import (
    SectionAlpha2Codes,
    SectionAlpha3Codes,
    SectionNames,
    SectionNumericCodes,
)
from paxman.capabilities.Country.rules.iso_3166_historical_ed2020 import (
    SectionHistoricalNames,
)
from paxman.core.domain import RuleStrategy

pytestmark = [pytest.mark.capability, pytest.mark.country]


class TestSectionAlpha2Codes:
    """Tests for SectionAlpha2Codes rule."""

    def setup_method(self) -> None:
        self.rule = SectionAlpha2Codes()

    def test_matches_valid_alpha2(self) -> None:
        """Happy path: valid alpha-2 code matches."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha2", value="US")
        assert self.rule.matches(notation, contract) is True

    def test_matches_lowercase(self) -> None:
        """Edge case: lowercase alpha-2 matches."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha2", value="us")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="US")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_invalid_code(self) -> None:
        """Notation with invalid alpha-2 code."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha2", value="ZZ")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_historical_code(self) -> None:
        """Historical alpha-2 code (SU) is not in active set."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha2", value="SU")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha2", value="US")
        assert self.rule.normalize(notation, contract) == "US"

    def test_normalize_alpha3_output(self) -> None:
        """Alpha-2 input with alpha3 output format."""
        contract = CountryContract(output_format="alpha3")
        notation = CountryNotation(shape="alpha2", value="DE")
        assert self.rule.normalize(notation, contract) == "DEU"

    def test_normalize_numeric_output(self) -> None:
        """Alpha-2 input with numeric output format."""
        contract = CountryContract(output_format="numeric")
        notation = CountryNotation(shape="alpha2", value="DE")
        assert self.rule.normalize(notation, contract) == "276"

    def test_normalize_name_output(self) -> None:
        """Alpha-2 input with name output format."""
        contract = CountryContract(output_format="name")
        notation = CountryNotation(shape="alpha2", value="DE")
        assert self.rule.normalize(notation, contract) == "GERMANY"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.specification_name == "ISO 3166-1:2024"
        assert self.rule.provenance.publication_year == 2024
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-alpha2-codes"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE


class TestSectionAlpha3Codes:
    """Tests for SectionAlpha3Codes rule."""

    def setup_method(self) -> None:
        self.rule = SectionAlpha3Codes()

    def test_matches_valid_alpha3(self) -> None:
        """Happy path: valid alpha-3 code matches."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha3", value="USA")
        assert self.rule.matches(notation, contract) is True

    def test_matches_lowercase(self) -> None:
        """Edge case: lowercase alpha-3 matches."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha3", value="usa")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="USA")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_invalid_code(self) -> None:
        """Notation with invalid alpha-3 code."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha3", value="ZZZ")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha3", value="USA")
        assert self.rule.normalize(notation, contract) == "US"

    def test_normalize_alpha3_output(self) -> None:
        """Alpha-3 input with alpha3 output format returns canonical alpha-3."""
        contract = CountryContract(output_format="alpha3")
        notation = CountryNotation(shape="alpha3", value="DEU")
        assert self.rule.normalize(notation, contract) == "DEU"

    def test_normalize_numeric_output(self) -> None:
        """Alpha-3 input with numeric output format."""
        contract = CountryContract(output_format="numeric")
        notation = CountryNotation(shape="alpha3", value="DEU")
        assert self.rule.normalize(notation, contract) == "276"

    def test_normalize_name_output(self) -> None:
        """Alpha-3 input with name output format."""
        contract = CountryContract(output_format="name")
        notation = CountryNotation(shape="alpha3", value="DEU")
        assert self.rule.normalize(notation, contract) == "GERMANY"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.specification_name == "ISO 3166-1:2024"
        assert self.rule.provenance.publication_year == 2024
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-alpha3-codes"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE


class TestSectionNumericCodes:
    """Tests for SectionNumericCodes rule."""

    def setup_method(self) -> None:
        self.rule = SectionNumericCodes()

    def test_matches_valid_numeric(self) -> None:
        """Happy path: valid numeric code matches."""
        contract = CountryContract()
        notation = CountryNotation(shape="numeric", value="840")
        assert self.rule.matches(notation, contract) is True

    def test_matches_with_leading_zeros(self) -> None:
        """Edge case: numeric code with leading zeros."""
        contract = CountryContract()
        notation = CountryNotation(shape="numeric", value="004")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="840")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_invalid_code(self) -> None:
        """Notation with invalid numeric code."""
        contract = CountryContract()
        notation = CountryNotation(shape="numeric", value="000")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        contract = CountryContract()
        notation = CountryNotation(shape="numeric", value="840")
        assert self.rule.normalize(notation, contract) == "US"

    def test_normalize_leading_zeros(self) -> None:
        """Verify normalization with leading zeros."""
        contract = CountryContract()
        notation = CountryNotation(shape="numeric", value="004")
        assert self.rule.normalize(notation, contract) == "AF"

    def test_normalize_alpha3_output(self) -> None:
        """Numeric input with alpha3 output format."""
        contract = CountryContract(output_format="alpha3")
        notation = CountryNotation(shape="numeric", value="276")
        assert self.rule.normalize(notation, contract) == "DEU"

    def test_normalize_numeric_output(self) -> None:
        """Numeric input with numeric output format returns canonical M49."""
        contract = CountryContract(output_format="numeric")
        notation = CountryNotation(shape="numeric", value="276")
        assert self.rule.normalize(notation, contract) == "276"

    def test_normalize_name_output(self) -> None:
        """Numeric input with name output format."""
        contract = CountryContract(output_format="name")
        notation = CountryNotation(shape="numeric", value="276")
        assert self.rule.normalize(notation, contract) == "GERMANY"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.specification_name == "ISO 3166-1:2024"
        assert self.rule.provenance.publication_year == 2024
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-numeric-codes"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE


class TestSectionNames:
    """Tests for SectionNames rule."""

    def setup_method(self) -> None:
        self.rule = SectionNames()

    def test_matches_valid_name(self) -> None:
        """Happy path: valid country name matches."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="UNITED STATES")
        assert self.rule.matches(notation, contract) is True

    def test_matches_lowercase(self) -> None:
        """Edge case: lowercase name matches."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="united states")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        contract = CountryContract()
        notation = CountryNotation(shape="alpha2", value="UNITED STATES")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_invalid_name(self) -> None:
        """Notation with invalid name."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="NOT A COUNTRY")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="UNITED STATES")
        assert self.rule.normalize(notation, contract) == "US"

    def test_normalize_synonym_usa(self) -> None:
        """Verify USA synonym normalizes to US."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="USA")
        assert self.rule.normalize(notation, contract) == "US"

    def test_normalize_alpha3_output(self) -> None:
        """Name input with alpha3 output format."""
        contract = CountryContract(output_format="alpha3")
        notation = CountryNotation(shape="name", value="GERMANY")
        assert self.rule.normalize(notation, contract) == "DEU"

    def test_normalize_numeric_output(self) -> None:
        """Name input with numeric output format."""
        contract = CountryContract(output_format="numeric")
        notation = CountryNotation(shape="name", value="GERMANY")
        assert self.rule.normalize(notation, contract) == "276"

    def test_normalize_name_output(self) -> None:
        """Name input with name output format returns canonical official name."""
        contract = CountryContract(output_format="name")
        notation = CountryNotation(shape="name", value="USA")
        # "USA" is a synonym, so normalize should resolve to "US" alpha-2,
        # then look up canonical name "UNITED STATES" from ALPHA2_TO_NAME.
        assert self.rule.normalize(notation, contract) == "UNITED STATES"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.specification_name == "ISO 3166-1:2024"
        assert self.rule.provenance.publication_year == 2024
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-names"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE


class TestSectionHistoricalNames:
    """Tests for SectionHistoricalNames rule.

    Historical entities map to their own former alpha-2 codes:
      BURMA → BU (not MM)
      USSR  → SU (not RU)
    """

    def setup_method(self) -> None:
        self.rule = SectionHistoricalNames()

    def test_matches_when_enabled(self) -> None:
        """Happy path: historical enabled and name matches."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="BURMA")
        assert self.rule.matches(notation, contract) is True

    def test_matches_lowercase(self) -> None:
        """Edge case: lowercase historical name matches."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="burma")
        assert self.rule.matches(notation, contract) is True

    def test_matches_soviet_union(self) -> None:
        """Soviet Union alternate name matches."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="SOVIET UNION")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_when_disabled(self) -> None:
        """Notation rejected when historical disabled (default)."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="BURMA")
        assert self.rule.matches(notation, contract) is False

    def test_accepts_historical_alpha2(self) -> None:
        """Now accepts alpha2 shape for historical codes (round-trip)."""
        contract = CountryContract(include_historical=True)
        # SU is a formerly used alpha-2 code (USSR)
        notation = CountryNotation(shape="alpha2", value="SU")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_active_alpha2_as_historical(self) -> None:
        """Active alpha-2 codes rejected by historical rule."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="alpha2", value="US")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_invalid_name(self) -> None:
        """Notation with invalid historical name."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="NOT A COUNTRY")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_burma(self) -> None:
        """Burma normalizes to its own former code BU (not MM)."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="BURMA")
        assert self.rule.normalize(notation, contract) == "BU"

    def test_normalize_ussr(self) -> None:
        """USSR normalizes to its own former code SU (not RU)."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="USSR")
        assert self.rule.normalize(notation, contract) == "SU"

    def test_normalize_soviet_union(self) -> None:
        """Soviet Union normalizes to SU."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="SOVIET UNION")
        assert self.rule.normalize(notation, contract) == "SU"

    def test_normalize_historical_alpha2(self) -> None:
        """Historical alpha-2 code normalizes to itself (round-trip)."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="alpha2", value="SU")
        assert self.rule.normalize(notation, contract) == "SU"

    def test_normalize_czechoslovakia(self) -> None:
        """Czechoslovakia normalizes to CS."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="CZECHOSLOVAKIA")
        assert self.rule.normalize(notation, contract) == "CS"

    def test_normalize_east_germany(self) -> None:
        """East Germany normalizes to DD."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="EAST GERMANY")
        assert self.rule.normalize(notation, contract) == "DD"

    def test_matches_historical_numeric(self) -> None:
        """Historical numeric code matches when enabled."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="numeric", value="200")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_historical_numeric_when_disabled(self) -> None:
        """Historical numeric code rejected when historical disabled."""
        contract = CountryContract()
        notation = CountryNotation(shape="numeric", value="200")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_historical_numeric(self) -> None:
        """Historical numeric code normalizes to former alpha-2 (always alpha2)."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="numeric", value="200")
        assert self.rule.normalize(notation, contract) == "CS"

    def test_normalize_historical_numeric_antilles(self) -> None:
        """Netherlands Antilles numeric code normalizes to AN."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="numeric", value="530")
        assert self.rule.normalize(notation, contract) == "AN"

    def test_historical_normalize_ignores_output_format(self) -> None:
        """Historical normalize always returns alpha-2 regardless of output_format."""
        contract = CountryContract(include_historical=True, output_format="alpha3")
        notation = CountryNotation(shape="name", value="USSR")
        # Historical always returns former alpha-2 code (SU), not converted to alpha-3
        assert self.rule.normalize(notation, contract) == "SU"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.specification_name == "ISO 3166-3"
        assert self.rule.provenance.publication_year == 2020
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-historical-names"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE
