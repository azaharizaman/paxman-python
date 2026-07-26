"""Tests for DateNotation and DateCapability."""

from __future__ import annotations

import pytest

from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.grammar.iso8601_recognition import (
    ISO8601DateGrammar,
)
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Date.rules.iso_8601_ed2019 import Section431CalendarDate
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule

# --- DateNotation tests ---


class TestDateNotation:
    """Tests for DateNotation."""

    @pytest.mark.capability
    def test_creates_with_fields(self) -> None:
        notation = DateNotation(day="26", month="07", year="2026")
        assert notation.day == "26"
        assert notation.month == "07"
        assert notation.year == "2026"

    @pytest.mark.capability
    def test_is_frozen(self) -> None:
        notation = DateNotation(day="26", month="07", year="2026")
        with pytest.raises(AttributeError):
            notation.day = "01"  # type: ignore[misc]

    @pytest.mark.capability
    def test_as_list_returns_correct(self) -> None:
        notation = DateNotation(day="26", month="07", year="2026")
        result = notation.as_list()
        assert result == ["26", "07", "2026"]
        assert isinstance(result, list)

    @pytest.mark.capability
    def test_as_list_preserves_order(self) -> None:
        notation = DateNotation(day="15", month="03", year="2024")
        assert notation.as_list()[0] == "15"
        assert notation.as_list()[1] == "03"
        assert notation.as_list()[2] == "2024"

    @pytest.mark.capability
    def test_equality(self) -> None:
        n1 = DateNotation(day="26", month="07", year="2026")
        n2 = DateNotation(day="26", month="07", year="2026")
        assert n1 == n2

    @pytest.mark.capability
    def test_inequality(self) -> None:
        n1 = DateNotation(day="26", month="07", year="2026")
        n2 = DateNotation(day="01", month="01", year="2025")
        assert n1 != n2

    @pytest.mark.capability
    def test_hashable(self) -> None:
        n1 = DateNotation(day="26", month="07", year="2026")
        n2 = DateNotation(day="26", month="07", year="2026")
        s = {n1, n2}
        assert len(s) == 1


# --- DateCapability tests ---


class TestDateCapability:
    """Tests for DateCapability."""

    @pytest.mark.capability
    def test_is_capability_subclass(self) -> None:
        cap = DateCapability()
        assert isinstance(cap, Capability)

    @pytest.mark.capability
    def test_name(self) -> None:
        cap = DateCapability()
        assert cap.name == "date"

    @pytest.mark.capability
    def test_version(self) -> None:
        cap = DateCapability()
        assert cap.version == "1.0.0"

    @pytest.mark.capability
    def test_get_grammars_returns_all(self) -> None:
        cap = DateCapability()
        grammars = cap.get_grammars()
        assert len(grammars) == 3
        assert isinstance(grammars[0], ISO8601DateGrammar)
        assert isinstance(grammars[0], Grammar)

    @pytest.mark.capability
    def test_get_rules_returns_all(self) -> None:
        cap = DateCapability()
        rules = cap.get_rules()
        assert len(rules) == 2
        assert isinstance(rules[0], Section431CalendarDate)
        assert isinstance(rules[0], Rule)

    @pytest.mark.capability
    def test_create_contract_defaults(self) -> None:
        contract = DateCapability.create_contract()
        assert contract.capability_name == "date"
        assert contract.output_format is None
        assert contract.two_digit_base_year is None

    @pytest.mark.capability
    def test_create_contract_with_params(self) -> None:
        contract = DateCapability.create_contract(
            output_format="ISO",
            two_digit_base_year=2000,
        )
        assert contract.output_format == "ISO"
        assert contract.two_digit_base_year == 2000


# --- DateContract tests ---


class TestDateContract:
    """Tests for DateContract."""

    @pytest.mark.capability
    def test_defaults(self) -> None:
        contract = DateContract()
        assert contract.capability_name == "date"
        assert contract.output_format is None
        assert contract.two_digit_base_year is None
        assert contract.excluded_rules == ()

    @pytest.mark.capability
    def test_with_parameters(self) -> None:
        contract = DateContract(output_format="ISO", two_digit_base_year=2000)
        assert contract.output_format == "ISO"
        assert contract.two_digit_base_year == 2000

    @pytest.mark.capability
    def test_active_grammars(self) -> None:
        contract = DateContract()
        assert contract.active_grammars == [
            "iso8601_recognition",
            "us_recognition",
            "european_recognition",
        ]

    @pytest.mark.capability
    def test_as_dict(self) -> None:
        contract = DateContract()
        d = contract.as_dict()
        assert d["capability_name"] == "date"
        assert d["output_format"] is None
        assert d["two_digit_base_year"] is None


# --- Package import tests ---


class TestDatePackageImports:
    """Tests for Date package imports."""

    @pytest.mark.capability
    def test_package_exports_date_capability(self) -> None:
        from paxman.capabilities.Date import DateCapability as DateCapabilityExport

        assert DateCapabilityExport is DateCapability

    @pytest.mark.capability
    def test_package_exports_date_notation(self) -> None:
        from paxman.capabilities.Date import DateNotation as DateNotationExport

        assert DateNotationExport is DateNotation
