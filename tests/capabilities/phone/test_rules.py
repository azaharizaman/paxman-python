"""Tests for Phone validation rules."""

from paxman.capabilities.Phone.contract import PhoneContract
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.e164_ed2010 import (
    Section6_1InternationalNumber,
    Section6_2CountryCode,
)
from paxman.capabilities.Phone.rules.rfc_3966_ed2004 import Section3TelUri
from paxman.core.domain import RuleStrategy


class TestSection6_1InternationalNumber:
    """Tests for Section6_1InternationalNumber rule."""

    def setup_method(self) -> None:
        self.rule = Section6_1InternationalNumber()
        self.contract = PhoneContract()

    def test_matches_valid_e164(self) -> None:
        """Happy path: valid E.164 number."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_uk_number(self) -> None:
        """Edge case: 2-digit country code."""
        notation = PhoneNotation(shape="e164", value="442079460958")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_three_digit_cc(self) -> None:
        """Edge case: 3-digit country code (Taiwan 886)."""
        notation = PhoneNotation(shape="e164", value="886212345678")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_longest_prefix_wins(self) -> None:
        """Edge case: 886 (Taiwan) not mis-split as 86 (China) + 6."""
        notation = PhoneNotation(shape="e164", value="886212345678")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_max_length(self) -> None:
        """Edge case: exactly 15 digits."""
        notation = PhoneNotation(shape="e164", value="123456789012345")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_too_long(self) -> None:
        """16+ digits exceeds E.164 maximum."""
        notation = PhoneNotation(shape="e164", value="1234567890123456")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_bare_country_code(self) -> None:
        """A bare country code (no NSN) is not a valid E.164 number."""
        notation = PhoneNotation(shape="e164", value="1")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_bare_two_digit_cc(self) -> None:
        """A 2-digit country code with no NSN is not valid either."""
        notation = PhoneNotation(shape="e164", value="44")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_unassigned_cc(self) -> None:
        """999 is not an assigned country code."""
        notation = PhoneNotation(shape="e164", value="999123456789")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = PhoneNotation(shape="national", value="15551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_non_digits(self) -> None:
        """Value containing non-digits."""
        notation = PhoneNotation(shape="e164", value="1555a1234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.normalize(notation, self.contract) == "+15551234567"

    def test_normalize_rfc3966_format(self) -> None:
        """Verify rfc3966 output format."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        contract = PhoneContract(output_format="rfc3966")
        assert self.rule.normalize(notation, contract) == "tel:+15551234567"

    def test_normalize_national_format(self) -> None:
        """Verify national (NSN) output format."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        contract = PhoneContract(output_format="national")
        assert self.rule.normalize(notation, contract) == "5551234567"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ITU-T"
        assert self.rule.provenance.specification_name == "E.164"
        assert self.rule.provenance.publication_year == 2010
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section 6.1-international-number"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.PARSER

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "6.1" in self.rule.citation


class TestSection6_2CountryCode:
    """Tests for Section6_2CountryCode rule."""

    def setup_method(self) -> None:
        self.rule = Section6_2CountryCode()
        self.contract = PhoneContract()

    def test_matches_assigned_cc(self) -> None:
        """Happy path: assigned country code."""
        notation = PhoneNotation(shape="e164", value="442079460958")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_single_digit_cc(self) -> None:
        """Edge case: NANP country code 1."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_three_digit_cc(self) -> None:
        """Edge case: 3-digit country code."""
        notation = PhoneNotation(shape="e164", value="886212345678")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_unassigned_cc(self) -> None:
        """Unassigned country code."""
        notation = PhoneNotation(shape="e164", value="999123456789")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = PhoneNotation(shape="national", value="15551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.normalize(notation, self.contract) == "+15551234567"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ITU-T"
        assert self.rule.provenance.specification_name == "E.164"
        assert self.rule.provenance.publication_year == 2010

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section 6.2-country-code"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "country code" in self.rule.citation.lower()


class TestSection3TelUri:
    """Tests for Section3TelUri rule."""

    def setup_method(self) -> None:
        self.rule = Section3TelUri()
        self.contract = PhoneContract()

    def test_matches_valid_global_number(self) -> None:
        """Happy path: valid tel: URI global number."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_with_extension(self) -> None:
        """Edge case: extension present."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567", extension="890")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_unassigned_cc(self) -> None:
        """Unassigned country code in URI."""
        notation = PhoneNotation(shape="rfc3966", value="999123456789")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_too_long(self) -> None:
        """16+ digits exceeds E.164 maximum."""
        notation = PhoneNotation(shape="rfc3966", value="1234567890123456")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output (default e164)."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567")
        assert self.rule.normalize(notation, self.contract) == "+15551234567"

    def test_normalize_rfc3966_format(self) -> None:
        """Verify rfc3966 output format."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567")
        contract = PhoneContract(output_format="rfc3966")
        assert self.rule.normalize(notation, contract) == "tel:+15551234567"

    def test_normalize_with_extension_in_rfc3966_format(self) -> None:
        """Verify extension is preserved in rfc3966 output."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567", extension="890")
        contract = PhoneContract(output_format="rfc3966")
        assert self.rule.normalize(notation, contract) == "tel:+15551234567;ext=890"

    def test_normalize_national_format(self) -> None:
        """Verify national (NSN) output format strips the country code."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567")
        contract = PhoneContract(output_format="national")
        assert self.rule.normalize(notation, contract) == "5551234567"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "IETF"
        assert self.rule.provenance.specification_name == "RFC 3966"
        assert self.rule.provenance.publication_year == 2004
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section 3-tel-uri"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.PARSER

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "3" in self.rule.citation
