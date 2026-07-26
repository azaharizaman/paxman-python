"""Tests for Date validation rules."""

from __future__ import annotations

import pytest

from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Date.rules.iso_8601_ed2019 import Section431CalendarDate
from paxman.capabilities.Date.rules.us_federal_rules_ed2023 import (
    Section1DateFormat,
)
from paxman.core.domain import RuleStrategy


class TestSection431CalendarDate:
    """ISO 8601 Section 4.3.1 — calendar date rule tests."""

    @pytest.mark.capability
    def test_matches_valid_input(self) -> None:
        rule = Section431CalendarDate()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract()
        assert rule.matches(notation, contract) is True

    @pytest.mark.capability
    def test_rejects_invalid_day(self) -> None:
        rule = Section431CalendarDate()
        notation = DateNotation(day="32", month="07", year="2026")
        contract = DateContract()
        assert rule.matches(notation, contract) is False

    @pytest.mark.capability
    def test_rejects_invalid_month(self) -> None:
        rule = Section431CalendarDate()
        notation = DateNotation(day="26", month="13", year="2026")
        contract = DateContract()
        assert rule.matches(notation, contract) is False

    @pytest.mark.capability
    def test_normalize_produces_canonical(self) -> None:
        rule = Section431CalendarDate()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract()
        assert rule.normalize(notation, contract) == "2026-07-26"

    @pytest.mark.capability
    def test_normalize_zero_pads(self) -> None:
        rule = Section431CalendarDate()
        notation = DateNotation(day="5", month="3", year="2026")
        contract = DateContract()
        assert rule.normalize(notation, contract) == "2026-03-05"

    @pytest.mark.capability
    def test_provenance_attributes(self) -> None:
        rule = Section431CalendarDate()
        assert rule.provenance.authority == "ISO"
        assert rule.provenance.specification_name == "ISO 8601"
        assert rule.provenance.publication_year == 2019
        assert rule.provenance.lifecycle == "active"

    @pytest.mark.capability
    def test_rule_name(self) -> None:
        rule = Section431CalendarDate()
        assert rule.name == "Section 4.3.1-calendar-date"

    @pytest.mark.capability
    def test_strategy_is_parser(self) -> None:
        rule = Section431CalendarDate()
        assert rule.strategy == RuleStrategy.PARSER


class TestSection1DateFormat:
    """US federal date format rule tests."""

    @pytest.mark.capability
    def test_matches_valid_input(self) -> None:
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract()
        assert rule.matches(notation, contract) is True

    @pytest.mark.capability
    def test_rejects_invalid_date(self) -> None:
        rule = Section1DateFormat()
        notation = DateNotation(day="31", month="02", year="2026")
        contract = DateContract()
        assert rule.matches(notation, contract) is False

    @pytest.mark.capability
    def test_two_digit_year_with_base_year(self) -> None:
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="26")
        contract = DateContract(two_digit_base_year=2000)
        assert rule.matches(notation, contract) is True

    @pytest.mark.capability
    def test_two_digit_year_normalize(self) -> None:
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="26")
        contract = DateContract(two_digit_base_year=2000)
        assert rule.normalize(notation, contract) == "2026-07-26"

    @pytest.mark.capability
    def test_output_format_iso(self) -> None:
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract(output_format="ISO")
        assert rule.normalize(notation, contract) == "2026-07-26"

    @pytest.mark.capability
    def test_output_format_us(self) -> None:
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract(output_format="US")
        assert rule.normalize(notation, contract) == "07/26/2026"

    @pytest.mark.capability
    def test_default_output_format_is_iso(self) -> None:
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract()
        assert rule.normalize(notation, contract) == "2026-07-26"

    @pytest.mark.capability
    def test_provenance_attributes(self) -> None:
        rule = Section1DateFormat()
        assert rule.provenance.authority == "US Federal Government"
        assert rule.provenance.specification_name == "Federal Rules"
        assert rule.provenance.publication_year == 2023
        assert rule.provenance.lifecycle == "active"

    @pytest.mark.capability
    def test_rule_name(self) -> None:
        rule = Section1DateFormat()
        assert rule.name == "Section 1-date-format"

    @pytest.mark.capability
    def test_strategy_is_parser(self) -> None:
        rule = Section1DateFormat()
        assert rule.strategy == RuleStrategy.PARSER
