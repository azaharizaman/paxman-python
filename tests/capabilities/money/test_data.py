"""Tests for Money currency data table integrity."""

from __future__ import annotations

import pytest

from paxman.capabilities.Money.grammar.data.currency_symbols import SYMBOL_TOKENS
from paxman.capabilities.Money.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Money.rules.data.cldr_currencies import (
    NAME_TO_CODES,
    SYMBOL_TO_CODES,
)
from paxman.capabilities.Money.rules.data.iso4217_list_one import (
    CURRENCY_CODES,
    MINOR_UNITS,
)

pytestmark = [pytest.mark.capability]


def _is_qualified(token: str) -> bool:
    """A symbol token is qualified when it contains an ASCII letter."""
    return any(ch.isascii() and ch.isalpha() for ch in token)


class TestIso4217ListOne:
    """Tests for the ISO 4217 List One code and minor-unit tables."""

    def test_verified_count(self) -> None:
        """The code set is locked to the verified in-scope count of 165.

        The 2026-01-01 snapshot lists 178 codes; the 13 codes whose
        CcyMnrUnts is "N.A." (XAG XAU XBA XBB XBC XBD XDR XPD XPT XSU
        XTS XUA XXX) are excluded: they have no usable minor units.
        """
        assert len(CURRENCY_CODES) == 165

    def test_minor_units_cover_exactly_the_codes(self) -> None:
        """MINOR_UNITS has exactly one entry per code and no extras."""
        assert len(MINOR_UNITS) == len(CURRENCY_CODES)
        assert set(MINOR_UNITS) == CURRENCY_CODES

    def test_all_codes_uppercase_alpha3(self) -> None:
        """Every code is an uppercase 3-letter ASCII code."""
        for code in CURRENCY_CODES:
            assert len(code) == 3
            assert code.isascii()
            assert code.isalpha()
            assert code.isupper()

    def test_minor_unit_spot_checks(self) -> None:
        """Spot-check the exponent buckets: 0, 2, 3, and 4 minor units."""
        assert MINOR_UNITS["USD"] == 2
        assert MINOR_UNITS["EUR"] == 2
        assert MINOR_UNITS["JPY"] == 0
        assert MINOR_UNITS["KRW"] == 0
        assert MINOR_UNITS["BHD"] == 3
        assert MINOR_UNITS["KWD"] == 3
        assert MINOR_UNITS["CLF"] == 4
        assert MINOR_UNITS["UYW"] == 4

    def test_no_minor_unit_exceeds_four(self) -> None:
        """No code has more than 4 minor units (CLF/UYW are the max)."""
        assert max(MINOR_UNITS.values()) == 4

    def test_na_minor_units_codes_excluded(self) -> None:
        """Codes with a N.A. minor-unit exponent are not in the table."""
        for code in (
            "XAG",
            "XAU",
            "XBA",
            "XBB",
            "XBC",
            "XBD",
            "XDR",
            "XPD",
            "XPT",
            "XSU",
            "XTS",
            "XUA",
            "XXX",
        ):
            assert code not in CURRENCY_CODES

    def test_new_and_fund_codes_present(self) -> None:
        """Spot-check recently added and fund codes present in the table."""
        for code in (
            "XAD",
            "XCG",
            "VED",
            "CHE",
            "CHW",
            "COU",
            "MXV",
            "BOV",
            "UYI",
            "USN",
        ):
            assert code in CURRENCY_CODES


class TestCldrCurrencies:
    """Tests for the CLDR symbol and display-name tables."""

    def test_symbol_values_are_sorted_tuples_of_known_codes(self) -> None:
        """Every symbol value is a non-empty sorted tuple of in-scope codes."""
        for codes in SYMBOL_TO_CODES.values():
            assert isinstance(codes, tuple)
            assert codes
            assert codes == tuple(sorted(codes))
            assert set(codes) <= CURRENCY_CODES

    def test_dollar_family(self) -> None:
        """The bare $ maps to the 29 dollar-family codes, including USD."""
        assert len(SYMBOL_TO_CODES["$"]) == 29
        assert "USD" in SYMBOL_TO_CODES["$"]

    def test_qualified_symbols_definitive(self) -> None:
        """Qualified symbols map to exactly one code (D4/D6)."""
        assert SYMBOL_TO_CODES["US$"] == ("USD",)
        assert SYMBOL_TO_CODES["CA$"] == ("CAD",)
        assert SYMBOL_TO_CODES["RM"] == ("MYR",)
        assert SYMBOL_TO_CODES["C$"] == ("NIO",)

    def test_bare_multi_candidate_symbols(self) -> None:
        """Bare symbols shared by several currencies list every code."""
        assert SYMBOL_TO_CODES["¥"] == ("CNY", "JPY")
        assert SYMBOL_TO_CODES["£"] == ("FKP", "GBP", "GIP", "SHP", "SSP", "SYP")
        assert SYMBOL_TO_CODES["₩"] == ("KPW", "KRW")

    def test_definitive_bare_symbols(self) -> None:
        """Bare single-candidate symbols are definitive (D3)."""
        assert SYMBOL_TO_CODES["€"] == ("EUR",)
        assert SYMBOL_TO_CODES["₽"] == ("RUB",)

    def test_no_symbol_equals_its_code(self) -> None:
        """CLDR code-fallback symbols (e.g. AED -> "AED") are omitted."""
        for symbol, codes in SYMBOL_TO_CODES.items():
            assert symbol not in codes
            assert not (
                len(symbol) == 3
                and symbol.isascii()
                and symbol.isalpha()
                and symbol.isupper()
            )

    def test_no_symbol_contains_whitespace(self) -> None:
        """Symbols containing (narrow no-break) spaces are omitted."""
        for symbol in SYMBOL_TO_CODES:
            assert not any(ch.isspace() for ch in symbol)

    def test_code_fallback_symbols_absent(self) -> None:
        """Codes whose CLDR symbol is the code itself have no symbol row."""
        assert "BHD" not in SYMBOL_TO_CODES
        assert "AED" not in SYMBOL_TO_CODES

    def test_name_values_are_sorted_tuples_of_known_codes(self) -> None:
        """Every name value is a non-empty sorted tuple of in-scope codes."""
        for codes in NAME_TO_CODES.values():
            assert isinstance(codes, tuple)
            assert codes
            assert codes == tuple(sorted(codes))
            assert set(codes) <= CURRENCY_CODES

    def test_brief_anchored_names_definitive(self) -> None:
        """The brief-anchored display names are definitive mappings."""
        assert NAME_TO_CODES["Dollar"] == ("USD",)
        assert NAME_TO_CODES["Euro"] == ("EUR",)
        assert NAME_TO_CODES["Ringgit"] == ("MYR",)

    def test_every_name_is_definitive(self) -> None:
        """Each curated name maps to exactly one canonical code."""
        assert all(len(codes) == 1 for codes in NAME_TO_CODES.values())


class TestCurrencySymbolTokens:
    """Tests for the grammar symbol-token ordering (D4)."""

    def test_tokens_are_exactly_the_symbol_table_keys(self) -> None:
        """Every shipped symbol token must resolve through SYMBOL_TO_CODES."""
        assert set(SYMBOL_TOKENS) == set(SYMBOL_TO_CODES)

    def test_qualified_tokens_before_bare(self) -> None:
        """All qualified tokens precede all bare tokens (D4)."""
        tokens = list(SYMBOL_TOKENS)
        first_bare = next(
            i for i, token in enumerate(tokens) if not _is_qualified(token)
        )
        assert all(_is_qualified(token) for token in tokens[:first_bare])
        assert all(not _is_qualified(token) for token in tokens[first_bare:])

    def test_longest_first_within_each_class(self) -> None:
        """Within each class, tokens are ordered longest first (D4)."""
        for cls in ("qualified", "bare"):
            tokens = [
                token
                for token in SYMBOL_TOKENS
                if _is_qualified(token) == (cls == "qualified")
            ]
            lengths = [len(token) for token in tokens]
            assert lengths == sorted(lengths, reverse=True)


class TestCurrencyWordTokens:
    """Tests for the grammar word-token ordering."""

    def test_tokens_are_exactly_the_name_table_keys(self) -> None:
        """Every shipped word token must resolve through NAME_TO_CODES."""
        assert set(WORD_TOKENS) == set(NAME_TO_CODES)

    def test_longest_first(self) -> None:
        """Word tokens are ordered longest first for alternation."""
        lengths = [len(token) for token in WORD_TOKENS]
        assert lengths == sorted(lengths, reverse=True)
