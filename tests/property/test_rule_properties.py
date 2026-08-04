"""Hypothesis property-based tests for rules."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Date.rules.iso_8601_ed2019 import Section431CalendarDate
from paxman.capabilities.Date.rules.us_federal_rules_ed2023 import Section1DateFormat


@pytest.mark.property
@given(
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
)
def test_iso8601_rule_matches_returns_bool(
    year: int,
    month: int,
    day: int,
) -> None:
    """ISO 8601 rule.matches() always returns a bool."""
    rule = Section431CalendarDate()
    notation = DateNotation(N1=str(year), N2=str(month), N3=str(day))
    contract = DateContract()
    result = rule.matches(notation, contract)
    assert isinstance(result, bool)


@pytest.mark.property
@given(
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
)
def test_iso8601_rule_normalize_returns_str(
    year: int,
    month: int,
    day: int,
) -> None:
    """ISO 8601 rule.normalize() always returns a str when matches() is True."""
    rule = Section431CalendarDate()
    notation = DateNotation(N1=str(year), N2=str(month), N3=str(day))
    contract = DateContract()
    if rule.matches(notation, contract):
        result = rule.normalize(notation, contract)
        assert isinstance(result, str)
        # Should be in ISO format
        assert len(result) == 10
        assert result[4] == "-"
        assert result[7] == "-"


@pytest.mark.property
@given(
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
    year=st.integers(min_value=1900, max_value=2100),
)
def test_us_rule_matches_returns_bool(
    month: int,
    day: int,
    year: int,
) -> None:
    """US federal rule.matches() always returns a bool."""
    rule = Section1DateFormat()
    notation = DateNotation(N1=str(month), N2=str(day), N3=str(year))
    contract = DateContract()
    result = rule.matches(notation, contract)
    assert isinstance(result, bool)


@pytest.mark.property
@given(
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
    year=st.integers(min_value=1900, max_value=2100),
    output_format=st.sampled_from([None, "ISO", "US"]),
)
def test_us_rule_normalize_returns_iso_regardless_of_format(
    month: int,
    day: int,
    year: int,
    output_format: str | None,
) -> None:
    """US federal rule.normalize() emits ISO shape for any output_format."""
    rule = Section1DateFormat()
    notation = DateNotation(N1=str(month), N2=str(day), N3=str(year))
    contract = DateContract(output_format=output_format)
    if rule.matches(notation, contract):
        result = rule.normalize(notation, contract)
        assert isinstance(result, str)
        assert len(result) == 10
        assert result[4] == "-"
        assert result[7] == "-"


@pytest.mark.property
@given(
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
)
def test_date_format_value_iso_is_identity(
    year: int,
    month: int,
    day: int,
) -> None:
    """DateCapability.format_value() keeps the default ISO canonical value."""
    cap = DateCapability()
    iso_value = f"{year:04d}-{month:02d}-{day:02d}"
    notation = DateNotation(N1=str(year), N2=str(month), N3=str(day))
    assert cap.format_value(iso_value, "ISO", notation) == iso_value


@pytest.mark.property
@given(
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
)
def test_date_format_value_us_produces_valid_us_shape(
    year: int,
    month: int,
    day: int,
) -> None:
    """DateCapability.format_value() converts valid ISO values to MM/DD/YYYY."""
    cap = DateCapability()
    iso_value = f"{year:04d}-{month:02d}-{day:02d}"
    notation = DateNotation(N1=str(year), N2=str(month), N3=str(day))
    result = cap.format_value(iso_value, "US", notation)
    assert len(result) == 10
    assert result[2] == "/"
    assert result[5] == "/"
    assert result == f"{month:02d}/{day:02d}/{year:04d}"
