"""Tests for Money amount parsing and formatting helpers."""

from __future__ import annotations

import dataclasses

import pytest

from paxman.capabilities.Money.parsing import (
    ParsedAmount,
    format_amount,
    parse_amount,
)

pytestmark = [pytest.mark.capability]


class TestParsedAmount:
    """Tests for the ParsedAmount value object."""

    def test_frozen_and_slots(self) -> None:
        """ParsedAmount is a frozen, slots-based dataclass."""
        assert dataclasses.is_dataclass(ParsedAmount)
        assert "__slots__" in ParsedAmount.__dict__

    def test_decimal_digits(self) -> None:
        """decimal_digits is the fraction length."""
        assert ParsedAmount("500", "").decimal_digits() == 0
        assert ParsedAmount("1000", "50").decimal_digits() == 2

    def test_to_decimal_string_no_fraction(self) -> None:
        """No fraction renders as the bare integer."""
        assert ParsedAmount("500", "").to_decimal_string() == "500"

    def test_to_decimal_string_with_fraction(self) -> None:
        """Fraction renders after a decimal point."""
        assert ParsedAmount("1000", "50").to_decimal_string() == "1000.50"


class TestParseAmount:
    """The locked 'last separator wins' algorithm table."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (".50", ("0", "50")),
            ("500.", ("500", "")),
            ("0,05", ("0", "05")),
            ("1,00", ("1", "")),
            ("1.234", ("1", "234")),
            ("1,00.50", ("1000", "50")),
            ("1.000,50", ("1000", "50")),
            ("1.500,50", ("1500", "50")),
            ("1,234.56", ("1234", "56")),
            ("12.345.678,90", ("12345678", "90")),
            ("500", ("500", "")),
        ],
    )
    def test_parse_amount_table(self, raw: str, expected: tuple[str, str]) -> None:
        """The full locked edge-case table (D2 'last separator wins')."""
        parsed = parse_amount(raw)
        assert parsed is not None
        assert (parsed.integer, parsed.fraction) == expected

    @pytest.mark.parametrize("raw", ["abc", "", "USD", "!?@#"])
    def test_parse_amount_none(self, raw: str) -> None:
        """A token with no digit character parses to None."""
        assert parse_amount(raw) is None

    def test_parse_amount_strips_leading_zeros(self) -> None:
        """No-separator integers strip leading zeros."""
        assert parse_amount("007") == ParsedAmount("7", "")

    def test_parse_amount_accounting_parens(self) -> None:
        """Accounting-form parentheses are ignored; the digit run is kept."""
        assert parse_amount("(500)") == ParsedAmount("500", "")


class TestFormatAmount:
    """format_amount pads, truncates, or rounds to minor_units digits."""

    @pytest.mark.parametrize(
        ("parsed", "minor_units", "precision", "expected"),
        [
            (ParsedAmount("500", ""), 2, "strict", "500.00"),
            (ParsedAmount("1000", "5"), 2, "strict", "1000.50"),
            (ParsedAmount("500", "999"), 2, "truncate", "500.99"),
            (ParsedAmount("500", "5"), 0, "round", "500"),
            (ParsedAmount("2", "5"), 0, "round", "2"),
            (ParsedAmount("3", "5"), 0, "round", "4"),
            (ParsedAmount("500", "9"), 0, "round", "501"),
        ],
    )
    def test_format_amount_table(
        self,
        parsed: ParsedAmount,
        minor_units: int,
        precision: str,
        expected: str,
    ) -> None:
        """The locked examples: strict pads, truncate drops, round half-to-even."""
        assert format_amount(parsed, minor_units, precision) == expected

    def test_zero_minor_units_never_render_decimal_point(self) -> None:
        """minor_units == 0 produces an integer string, never '500.'."""
        assert format_amount(ParsedAmount("500", ""), 0, "strict") == "500"
        assert format_amount(ParsedAmount("500", ""), 0, "round") == "500"

    def test_truncate_pads_short_fraction(self) -> None:
        """Truncate zero-pads fractions shorter than minor_units."""
        assert format_amount(ParsedAmount("500", "5"), 2, "truncate") == "500.50"

    def test_round_pads_to_minor_units(self) -> None:
        """Round quantizes to the exact minor-unit scale."""
        assert format_amount(ParsedAmount("500", "5"), 2, "round") == "500.50"

    def test_round_large_integer_does_not_raise(self) -> None:
        """A 28-digit integer rounding up to 29 digits must not raise.

        The default Decimal context (prec=28) makes arithmetic composition
        raise InvalidOperation here; Decimal string construction is
        context-independent and quantize runs under a raised local context.
        """
        assert format_amount(ParsedAmount("9" * 28, "5"), 0, "round") == "1" + "0" * 28

    def test_round_large_integer_27_digit_boundary(self) -> None:
        """The 27-digit boundary: 28 result digits fit the default context."""
        assert format_amount(ParsedAmount("9" * 27, "5"), 0, "round") == "1" + "0" * 27

    def test_round_long_fraction_keeps_full_precision(self) -> None:
        """A 30-digit fraction rounds by its exact value, not a 28-digit view.

        500.500...001 (29 zeros then a 1) is not a tie and must round up to
        501; truncating the fraction to 28 significant digits turns it into
        an exact 500.5 tie that rounds half-to-even down to 500.
        """
        assert (
            format_amount(ParsedAmount("500", "5" + "0" * 28 + "1"), 0, "round")
            == "501"
        )
