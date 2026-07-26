"""Hypothesis property-based tests for rules."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Date.rules.iso_8601_ed2019 import Section431CalendarDate


@given(
    day=st.integers(min_value=1, max_value=31),
    month=st.integers(min_value=1, max_value=12),
    year=st.integers(min_value=1900, max_value=2100),
)
def test_iso8601_rule_matches_returns_bool(
    day: int,
    month: int,
    year: int,
) -> None:
    """ISO 8601 rule matches() always returns a bool."""
    rule = Section431CalendarDate()
    notation = DateNotation(
        day=str(day),
        month=str(month),
        year=str(year),
    )
    contract = DateContract()
    result = rule.matches(notation, contract)
    assert isinstance(result, bool)


def test_iso8601_rule_normalize_always_returns_string() -> None:
    """ISO 8601 rule normalize() always returns a string."""
    rule = Section431CalendarDate()
    notation = DateNotation(day="26", month="07", year="2026")
    contract = DateContract()
    result = rule.normalize(notation, contract)
    assert isinstance(result, str)


def test_iso8601_rule_valid_date_normalizes_correctly() -> None:
    """ISO 8601 rule normalizes valid date to expected format."""
    rule = Section431CalendarDate()
    notation = DateNotation(day="15", month="03", year="2024")
    contract = DateContract()
    assert rule.matches(notation, contract) is True
    assert rule.normalize(notation, contract) == "2024-03-15"


def test_iso8601_rule_invalid_date_does_not_match() -> None:
    """ISO 8601 rule rejects invalid dates."""
    rule = Section431CalendarDate()
    notation = DateNotation(day="31", month="02", year="2024")
    contract = DateContract()
    assert rule.matches(notation, contract) is False


def test_iso8601_rule_handles_non_numeric_notation() -> None:
    """ISO 8601 rule handles non-numeric notation gracefully."""
    rule = Section431CalendarDate()
    notation = DateNotation(day="abc", month="def", year="ghi")
    contract = DateContract()
    assert rule.matches(notation, contract) is False
