"""Tests for the generated ISBN Range Message data module."""

from pathlib import Path

import pytest

from paxman.capabilities.ISBN.rules.data.range_message import (
    EAN_PREFIX_RULES,
    GROUP_RULES,
    MESSAGE_DATE,
    MESSAGE_SERIAL,
)

pytestmark = [pytest.mark.capability]

_ALL_RULES = tuple(EAN_PREFIX_RULES.values()) + tuple(GROUP_RULES.values())


def test_shipped_prefixes() -> None:
    """The two EAN.UCC prefixes shipped are 978 and 979."""
    assert set(EAN_PREFIX_RULES) == {"978", "979"}


def test_group_count() -> None:
    """The snapshot registers 287 registration groups."""
    assert len(GROUP_RULES) == 287


def test_emitted_rule_count() -> None:
    """1864 raw rules minus 182 unallocated (Length 0) leaves 1682 emitted."""
    emitted = sum(len(r) for r in EAN_PREFIX_RULES.values()) + sum(
        len(r) for r in GROUP_RULES.values()
    )
    assert emitted == 1682


def test_message_serial() -> None:
    """MessageSerialNumber matches the committed snapshot."""
    assert MESSAGE_SERIAL == "6f6063f3-6f2a-4619-8bd9-116a3addc690"


def test_message_date() -> None:
    """MessageDate matches the committed snapshot."""
    assert MESSAGE_DATE.startswith("Wed, 5 Aug 2026")


def test_known_groups() -> None:
    """Key group prefixes are present; there is no 979-9 group."""
    assert "978-0" in GROUP_RULES
    assert "979-10" in GROUP_RULES
    assert "979-11" in GROUP_RULES
    assert "979-12" in GROUP_RULES
    assert "979-13" in GROUP_RULES
    assert "979-8" in GROUP_RULES
    assert "979-9" not in GROUP_RULES


def test_ranges_seven_digit() -> None:
    """Every range endpoint is a 7-digit zero-padded numeric string."""
    for rules in _ALL_RULES:
        for start, end, _length in rules:
            assert len(start) == len(end) == 7
            assert start.isdigit()
            assert end.isdigit()


def test_no_length_zero() -> None:
    """Unallocated (Length 0) ranges are never emitted."""
    for rules in _ALL_RULES:
        for _start, _end, length in rules:
            assert length >= 1


def test_no_output_format_token() -> None:
    """The generated data module must not contain the output_format token."""
    source = (
        Path(__file__).parents[3]
        / "paxman"
        / "capabilities"
        / "ISBN"
        / "rules"
        / "data"
        / "range_message.py"
    )
    assert "output_format" not in source.read_text()
