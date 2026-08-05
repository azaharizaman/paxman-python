"""Tests for ISBN capability validation rules."""

from __future__ import annotations

import pytest

from paxman.capabilities.ISBN.contract import ISBNContract
from paxman.capabilities.ISBN.notation import ISBNNotation
from paxman.capabilities.ISBN.rules.isbn_range_message_ed2026 import (
    Section4RegistrantRange,
)
from paxman.capabilities.ISBN.rules.isbn_users_manual_ed2012 import (
    Section6Isbn10CheckDigit,
)
from paxman.capabilities.ISBN.rules.iso_2108_ed2017 import (
    Section42Gs1Prefix,
    Section53Isbn13CheckDigit,
)
from paxman.core.domain import RuleStrategy

pytestmark = [pytest.mark.capability]


class TestSection53Isbn13CheckDigit:
    """Tests for Section53Isbn13CheckDigit rule."""

    def setup_method(self) -> None:
        self.rule = Section53Isbn13CheckDigit()
        self.contract = ISBNContract()

    def test_isbn13_check_digit_valid(self) -> None:
        """Happy path: valid ISBN-13 check digit matches."""
        notation = ISBNNotation(shape="isbn13", digits="9780110002224")
        assert self.rule.matches(notation, self.contract) is True
        assert self.rule.normalize(notation, self.contract) == "9780110002224"

    def test_isbn13_check_digit_invalid(self) -> None:
        """Wrong check digit fails; correct check digit matches."""
        assert (
            self.rule.matches(
                ISBNNotation(shape="isbn13", digits="9780306406158"), self.contract
            )
            is False
        )
        assert (
            self.rule.matches(
                ISBNNotation(shape="isbn13", digits="9780306406157"), self.contract
            )
            is True
        )

    def test_check_digit_rejects_non_gs1_prefix(self) -> None:
        """Non-GS1 EAN-13 is rejected even when it would otherwise pass.

        The check-digit rule enforces prefix in {978, 979} (ISO 2108 §4.2
        structure), so non-GS1 EAN-13s resolve INVALID, not SUCCESS.
        """
        notation = ISBNNotation(shape="isbn13", digits="1234567890123")
        assert self.rule.matches(notation, self.contract) is False


class TestSection42Gs1Prefix:
    """Tests for Section42Gs1Prefix rule."""

    def setup_method(self) -> None:
        self.rule = Section42Gs1Prefix()
        self.contract = ISBNContract()

    def test_gs1_prefix_rule(self) -> None:
        """978/979 prefixes match only with a valid check digit; other
        prefixes rejected; normalize passthrough."""
        assert (
            self.rule.matches(
                ISBNNotation(shape="isbn13", digits="9780306406157"), self.contract
            )
            is True
        )
        assert (
            self.rule.matches(
                ISBNNotation(shape="isbn13", digits="9780306406158"), self.contract
            )
            is False
        )
        assert (
            self.rule.matches(
                ISBNNotation(shape="isbn13", digits="9789990000009"), self.contract
            )
            is True
        )
        assert (
            self.rule.matches(
                ISBNNotation(shape="isbn13", digits="1234567890123"), self.contract
            )
            is False
        )
        notation = ISBNNotation(shape="isbn13", digits="9780306406157")
        assert self.rule.normalize(notation, self.contract) == "9780306406157"


class TestSection6Isbn10CheckDigit:
    """Tests for Section6Isbn10CheckDigit rule."""

    def setup_method(self) -> None:
        self.rule = Section6Isbn10CheckDigit()
        self.contract = ISBNContract()

    def test_isbn10_check_digit(self) -> None:
        """Valid ISBN-10s (including X check) match; invalid check digit fails."""
        for digits in ("0306406152", "0849396409", "080442957X", "080442957x"):
            notation = ISBNNotation(shape="isbn10", digits=digits)
            assert self.rule.matches(notation, self.contract) is True
        assert (
            self.rule.matches(
                ISBNNotation(shape="isbn10", digits="0306406153"), self.contract
            )
            is False
        )

    def test_isbn10_normalize_conversion(self) -> None:
        """normalize converts ISBN-10 to ISBN-13 with a recomputed check digit."""
        conversions = {
            "0306406152": "9780306406157",
            "0849396409": "9780849396403",
            "080442957X": "9780804429573",
        }
        for digits, isbn13 in conversions.items():
            notation = ISBNNotation(shape="isbn10", digits=digits)
            assert self.rule.normalize(notation, self.contract) == isbn13


class TestSection4RegistrantRange:
    """Tests for Section4RegistrantRange rule."""

    def setup_method(self) -> None:
        self.rule = Section4RegistrantRange()
        self.contract = ISBNContract()

    def test_range_rule_allocated(self) -> None:
        """Allocated 978-0 ISBN-13 and its ISBN-10 equivalent match.

        "9780110002224": group "0", registrant "11" (first 978-0 range
        0000000-1999999, length 2). ISBN-10 "0110002229" has mod-11 check over
        0,1,1,0,0,0,2,2,2 with weights 10..2 summing to 35 -> check 9, and
        _to_isbn13 converts it back to "9780110002224".
        """
        isbn13 = ISBNNotation(shape="isbn13", digits="9780110002224")
        assert self.rule.matches(isbn13, self.contract) is True
        assert self.rule.normalize(isbn13, self.contract) == "9780110002224"
        isbn10 = ISBNNotation(shape="isbn10", digits="0110002229")
        assert self.rule.matches(isbn10, self.contract) is True
        assert self.rule.normalize(isbn10, self.contract) == "9780110002224"

    def test_range_rule_unallocated(self) -> None:
        """No match when the derived group key is absent from GROUP_RULES.

        "9789990000000" derives group 978-99900, which has no GROUP_RULES
        entry -> no match. The invariant under test is "missing group key ->
        no match".
        """
        notation = ISBNNotation(shape="isbn13", digits="9789990000000")
        assert self.rule.matches(notation, self.contract) is False

    def test_range_rule_requires_feature(self) -> None:
        """The range rule is gated on include_range_validation."""
        assert self.rule.requires_features == frozenset({"include_range_validation"})


class TestRuleConventions:
    """Verify names, strategies, citations, and provenance per rule."""

    def setup_method(self) -> None:
        self.isbn13 = Section53Isbn13CheckDigit()
        self.gs1 = Section42Gs1Prefix()
        self.isbn10 = Section6Isbn10CheckDigit()
        self.range = Section4RegistrantRange()

    def test_rule_conventions(self) -> None:
        """Names, strategies, and citations follow the plan exactly."""
        assert self.isbn13.name == "Section 5.3-isbn13-check-digit"
        assert self.isbn13.strategy == RuleStrategy.PARSER
        assert self.isbn13.citation == "Section 5.3 (ISBN-13 check digit)"
        assert self.isbn13.target_grammars == frozenset({"isbn13_recognition"})
        assert self.isbn13.requires_features == frozenset()

        assert self.gs1.name == "Section 4.2-gs1-prefix"
        assert self.gs1.strategy == RuleStrategy.LOOKUP_TABLE
        assert self.gs1.citation == "Section 4.2 (GS1 prefix)"
        assert self.gs1.target_grammars == frozenset({"isbn13_recognition"})
        assert self.gs1.requires_features == frozenset()

        assert self.isbn10.name == "Section 6-isbn10-check-digit"
        assert self.isbn10.strategy == RuleStrategy.PARSER
        assert self.isbn10.citation == "Section 6 (ISBN-10 check digit)"
        assert self.isbn10.target_grammars == frozenset({"isbn10_recognition"})
        assert self.isbn10.requires_features == frozenset()

        assert self.range.name == "Section 4-registrant-range"
        assert self.range.strategy == RuleStrategy.LOOKUP_TABLE
        assert self.range.citation == "Section 4 (registrant range)"
        assert self.range.target_grammars == frozenset(
            {"isbn13_recognition", "isbn10_recognition"}
        )

    def test_provenance_attributes(self) -> None:
        """Provenance per publication: authority, lifecycle, year, kind."""
        iso = self.isbn13.provenance
        assert iso.authority == "ISO"
        assert iso.specification_name == "ISO 2108:2017"
        assert iso.kind == "specification"
        assert iso.version == "2017"
        assert iso.lifecycle == "active"
        assert iso.publication_year == 2017

        manual = self.isbn10.provenance
        assert manual.authority == "International ISBN Agency"
        assert manual.specification_name == "ISBN Users' Manual"
        assert manual.kind == "specification"
        assert manual.version == "2012"
        assert manual.lifecycle == "superseded"
        assert manual.publication_year == 2012

        registry = self.range.provenance
        assert registry.authority == "International ISBN Agency"
        assert registry.specification_name == "ISBN Range Message"
        assert registry.kind == "registry"
        assert registry.version == "2026-08-05"
        assert registry.lifecycle == "active"
        assert registry.publication_year == 2026
