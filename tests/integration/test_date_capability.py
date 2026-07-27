"""Integration tests for Date capability."""

from __future__ import annotations

import pytest

import paxman
from paxman.capabilities import Date
from paxman.capabilities.Date.capability import DateCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset and register Date capability before each test."""
    reset_registry()
    register_capability(DateCapability())
    yield
    reset_registry()


@pytest.mark.integration
class TestDateCapabilityIntegration:
    """Integration tests for Date capability pipeline."""

    def test_iso8601_date_recognized_and_canonicalized(self) -> None:
        """ISO 8601 date is recognized and canonicalized to ISO format."""
        contract = Date.create_contract()
        result = paxman.canonicalize("2026-07-26", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "2026-07-26"

    def test_us_date_with_output_format_iso(self) -> None:
        """US date with output_format=ISO is canonicalized to ISO format."""
        contract = Date.create_contract(output_format="ISO")
        result = paxman.canonicalize("07/26/2026", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "2026-07-26"

    def test_us_date_with_output_format_us(self) -> None:
        """US date with output_format=US is canonicalized to US format."""
        contract = Date.create_contract(output_format="US")
        result = paxman.canonicalize("07/26/2026", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "07/26/2026"

    def test_european_date_with_output_format_iso(self) -> None:
        """European date with output_format=ISO is canonicalized to ISO format."""
        contract = Date.create_contract(output_format="ISO")
        result = paxman.canonicalize("26/07/2026", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "2026-07-26"

    def test_two_digit_year_with_base_year(self) -> None:
        """Two-digit year with base_year is interpreted correctly."""
        contract = Date.create_contract(two_digit_base_year=2000)
        result = paxman.canonicalize("07/26/26", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "2026-07-26"

    def test_two_digit_year_without_base_year(self) -> None:
        """Two-digit year without base_year uses default (2000)."""
        contract = Date.create_contract()
        result = paxman.canonicalize("07/26/26", contract)
        assert result.status == Resolution.SUCCESS
        # Default base year is 2000, so 26 -> 2026
        assert result.canonicalized_value == "2026-07-26"

    def test_date_in_text_recognized(self) -> None:
        """Date embedded in text is recognized."""
        contract = Date.create_contract()
        result = paxman.canonicalize("Meeting on 2026-07-26", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "2026-07-26"

    def test_multiple_dates_ambiguous(self) -> None:
        """Multiple different dates produce AMBIGUOUS status."""
        contract = Date.create_contract()
        result = paxman.canonicalize("2026-07-26 and 2025-12-31", contract)
        assert result.status == Resolution.AMBIGUOUS

    def test_no_date_missing(self) -> None:
        """No date in text produces MISSING status."""
        contract = Date.create_contract()
        result = paxman.canonicalize("No dates here", contract)
        assert result.status == Resolution.MISSING

    def test_invalid_date_invalid(self) -> None:
        """Invalid date (e.g., February 30) produces INVALID status."""
        contract = Date.create_contract()
        result = paxman.canonicalize("2026-02-30", contract)
        assert result.status == Resolution.INVALID

    def test_us_vs_european_date_ambiguity(self) -> None:
        """Input '07/02/2026' is ambiguous between US (July 2) and European (Feb 7)."""
        contract = Date.create_contract()
        result = paxman.canonicalize("07/02/2026", contract)
        assert result.status == Resolution.AMBIGUOUS
        values = {c.value for c in result.candidates}
        assert "2026-07-02" in values  # US interpretation
        assert "2026-02-07" in values  # European interpretation
