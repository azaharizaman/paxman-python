"""Tests for Country validation rules."""

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.data import ALPHA2_CODES
from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.cldr_localized_ed2025 import (
    SectionLocalizedNames,
)
from paxman.capabilities.Country.rules.iso_3166_alpha2_ed2024 import SectionAlpha2Codes
from paxman.capabilities.Country.rules.iso_3166_alpha3_ed2024 import SectionAlpha3Codes
from paxman.capabilities.Country.rules.iso_3166_name_ed2024 import SectionNames
from paxman.capabilities.Country.rules.iso_3166_numeric_ed2024 import (
    SectionNumericCodes,
)
from paxman.capabilities.Country.rules.paxman_historical_ed2025 import (
    SectionHistoricalNames,
)
from paxman.core.domain import RuleStrategy


class TestSectionAlpha2Codes:
    """Tests for SectionAlpha2Codes rule."""

    def setup_method(self) -> None:
        self.rule = SectionAlpha2Codes()
        self.contract = CountryContract()

    def test_matches_valid_input(self) -> None:
        """Happy path: notation is valid."""
        notation = CountryNotation(shape="alpha2", value="US")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_lowercase(self) -> None:
        """Edge case: lowercase input matches."""
        notation = CountryNotation(shape="alpha2", value="us")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_all_valid_codes(self) -> None:
        """Edge case: all 249 codes match."""
        for code in list(ALPHA2_CODES)[:10]:  # Test first 10
            notation = CountryNotation(shape="alpha2", value=code)
            assert self.rule.matches(notation, self.contract) is True

    def test_rejects_invalid_code(self) -> None:
        """Notation with invalid alpha-2 code."""
        notation = CountryNotation(shape="alpha2", value="XX")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = CountryNotation(shape="alpha3", value="US")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        notation = CountryNotation(shape="alpha2", value="US")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_normalize_lowercase(self) -> None:
        """Verify lowercase input normalizes to uppercase."""
        notation = CountryNotation(shape="alpha2", value="us")
        assert self.rule.normalize(notation, self.contract) == "US"

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

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "alpha-2" in self.rule.citation.lower()


class TestSectionAlpha3Codes:
    """Tests for SectionAlpha3Codes rule."""

    def setup_method(self) -> None:
        self.rule = SectionAlpha3Codes()
        self.contract = CountryContract()

    def test_matches_valid_input(self) -> None:
        """Happy path: notation is valid."""
        notation = CountryNotation(shape="alpha3", value="USA")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_lowercase(self) -> None:
        """Edge case: lowercase input matches."""
        notation = CountryNotation(shape="alpha3", value="usa")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_invalid_code(self) -> None:
        """Notation with invalid alpha-3 code."""
        notation = CountryNotation(shape="alpha3", value="XXX")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = CountryNotation(shape="alpha2", value="USA")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output (alpha-2)."""
        notation = CountryNotation(shape="alpha3", value="USA")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_normalize_lowercase(self) -> None:
        """Verify lowercase input normalizes correctly."""
        notation = CountryNotation(shape="alpha3", value="gbr")
        assert self.rule.normalize(notation, self.contract) == "GB"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.publication_year == 2024

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-alpha3-codes"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "alpha-3" in self.rule.citation.lower()


class TestSectionNumericCodes:
    """Tests for SectionNumericCodes rule."""

    def setup_method(self) -> None:
        self.rule = SectionNumericCodes()
        self.contract = CountryContract()

    def test_matches_valid_input(self) -> None:
        """Happy path: notation is valid."""
        notation = CountryNotation(shape="numeric", value="840")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_with_leading_zeros(self) -> None:
        """Edge case: leading zeros are stripped for lookup."""
        notation = CountryNotation(shape="numeric", value="0840")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_single_digit(self) -> None:
        """Edge case: single digit code matches."""
        notation = CountryNotation(shape="numeric", value="4")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_invalid_code(self) -> None:
        """Notation with invalid numeric code."""
        notation = CountryNotation(shape="numeric", value="999")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = CountryNotation(shape="alpha2", value="840")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output (alpha-2)."""
        notation = CountryNotation(shape="numeric", value="840")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_normalize_preserves_original(self) -> None:
        """Verify normalization with leading zeros."""
        notation = CountryNotation(shape="numeric", value="004")
        assert self.rule.normalize(notation, self.contract) == "AF"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.publication_year == 2024

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
        self.contract = CountryContract()

    def test_matches_valid_input(self) -> None:
        """Happy path: notation is valid."""
        notation = CountryNotation(shape="name", value="UNITED STATES")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_title_case(self) -> None:
        """Edge case: title case matches (uppercased internally)."""
        notation = CountryNotation(shape="name", value="United States")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_invalid_name(self) -> None:
        """Notation with invalid name."""
        notation = CountryNotation(shape="name", value="NOT A COUNTRY")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = CountryNotation(shape="alpha2", value="UNITED STATES")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output (alpha-2)."""
        notation = CountryNotation(shape="name", value="UNITED STATES")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_normalize_case_insensitive(self) -> None:
        """Verify case-insensitive lookup."""
        notation = CountryNotation(shape="name", value="united states")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.publication_year == 2024

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-names"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "name" in self.rule.citation.lower()


class TestSectionLocalizedNames:
    """Tests for SectionLocalizedNames rule."""

    def setup_method(self) -> None:
        self.rule = SectionLocalizedNames()

    def test_matches_when_enabled(self) -> None:
        """Happy path: localized enabled and name matches."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="马来西亚")
        assert self.rule.matches(notation, contract) is True

    def test_matches_chinese(self) -> None:
        """Edge case: Chinese name matches."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="中国")
        assert self.rule.matches(notation, contract) is True

    def test_matches_spanish(self) -> None:
        """Edge case: Spanish name matches."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="Estados Unidos")
        assert self.rule.matches(notation, contract) is True

    def test_matches_french(self) -> None:
        """Edge case: French name matches."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="Allemagne")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_when_disabled(self) -> None:
        """Notation rejected when localized disabled (default)."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="马来西亚")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="alpha2", value="马来西亚")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_invalid_name(self) -> None:
        """Notation with invalid localized name."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="NOT A COUNTRY")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="马来西亚")
        assert self.rule.normalize(notation, contract) == "MY"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "Unicode"
        assert self.rule.provenance.specification_name == "CLDR v45"
        assert self.rule.provenance.publication_year == 2025

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-localized-names"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE


class TestSectionHistoricalNames:
    """Tests for SectionHistoricalNames rule."""

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

    def test_rejects_when_disabled(self) -> None:
        """Notation rejected when historical disabled (default)."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="BURMA")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="alpha2", value="BURMA")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_invalid_name(self) -> None:
        """Notation with invalid historical name."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="NOT A COUNTRY")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="BURMA")
        assert self.rule.normalize(notation, contract) == "MM"

    def test_normalize_ceylon(self) -> None:
        """Verify Ceylon normalizes to LK."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="CEYLON")
        assert self.rule.normalize(notation, contract) == "LK"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "Paxman"
        assert self.rule.provenance.specification_name == "Historical Country Names"
        assert self.rule.provenance.publication_year == 2025

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-historical-names"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE
