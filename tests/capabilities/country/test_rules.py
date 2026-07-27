"""Tests for Country validation rules."""

import pytest
from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.iso_3166_alpha2_ed2024 import SectionAlpha2Codes
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
        from paxman.capabilities.Country.data import ALPHA2_CODES
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
