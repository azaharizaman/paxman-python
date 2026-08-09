"""Tests for Currency data table integrity."""

from __future__ import annotations

import pytest

from paxman.capabilities.Currency.grammar.data.currency_symbols import SYMBOL_TOKENS
from paxman.capabilities.Currency.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Currency.rules.data.cldr_currencies import (
    NAME_TO_CODES,
    SYMBOL_TO_CODES,
)
from paxman.capabilities.Currency.rules.data.iso4217_list_one import CURRENCY_CODES

pytestmark = [pytest.mark.capability, pytest.mark.currency]


def _is_qualified(token: str) -> bool:
    """A symbol token is qualified when it contains an ASCII letter."""
    return any(ch.isascii() and ch.isalpha() for ch in token)


class TestIso4217ListOne:
    """Tests for the ISO 4217 List One code table."""

    def test_verified_count(self) -> None:
        """The code set is locked to the verified full count of 178.

        The 2026-01-01 snapshot lists 178 codes; Currency ships the full
        set, including the 13 codes whose CcyMnrUnts is "N.A." (XAG XAU
        XBA XBB XBC XBD XDR XPD XPT XSU XTS XUA XXX) that Money excludes
        for lack of usable minor units (D2).
        """
        assert len(CURRENCY_CODES) == 178

    def test_all_codes_uppercase_alpha3(self) -> None:
        """Every code is an uppercase 3-letter ASCII code."""
        for code in CURRENCY_CODES:
            assert len(code) == 3
            assert code.isascii()
            assert code.isalpha()
            assert code.isupper()

    def test_full_set_superset(self) -> None:
        """Common codes are present in the table."""
        assert {"USD", "EUR", "GBP", "JPY", "MYR"} <= CURRENCY_CODES

    def test_na_minor_units_codes_included(self) -> None:
        """Codes with a N.A. minor-unit exponent are in the table (D2).

        Currency canonicalizes identifiers, so a bare "XAU" resolving to
        "XAU" is correct; Money excludes these 13 codes because amounts
        need minor units.
        """
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
            assert code in CURRENCY_CODES

    def test_post_amendment_entries_present(self) -> None:
        """Spot-check recently amended codes present in the table."""
        assert {"ZWG", "VES", "VED", "SLE", "XAD", "XCG"} <= CURRENCY_CODES

    def test_historic_entries_absent(self) -> None:
        """Historic (List Three) codes are absent from the table."""
        assert CURRENCY_CODES.isdisjoint(
            {"ZWL", "SLL", "BGN", "ANG", "HRK", "VEF", "BYR", "MRO", "STD"}
        )


class TestCldrCurrencies:
    """Tests for the CLDR symbol and display-name tables."""

    def test_symbol_values_are_sorted_tuples_of_known_codes(self) -> None:
        """Every symbol value is a non-empty sorted tuple of in-scope codes."""
        for codes in SYMBOL_TO_CODES.values():
            assert isinstance(codes, tuple)
            assert codes
            assert codes == tuple(sorted(codes))
            assert set(codes) <= CURRENCY_CODES

    def test_qualified_symbols_definitive(self) -> None:
        """Qualified symbols map to exactly one code."""
        assert SYMBOL_TO_CODES["US$"] == ("USD",)
        assert SYMBOL_TO_CODES["CA$"] == ("CAD",)
        assert SYMBOL_TO_CODES["RM"] == ("MYR",)

    def test_definitive_bare_symbols(self) -> None:
        """Bare single-candidate symbols are definitive."""
        assert SYMBOL_TO_CODES["€"] == ("EUR",)
        assert SYMBOL_TO_CODES["₽"] == ("RUB",)

    def test_bare_multi_candidate_symbols(self) -> None:
        """Bare symbols shared by several currencies list every code."""
        assert SYMBOL_TO_CODES["¥"] == ("CNY", "JPY")
        assert SYMBOL_TO_CODES["£"] == ("FKP", "GBP", "GIP", "SHP", "SSP", "SYP")
        assert SYMBOL_TO_CODES["₩"] == ("KPW", "KRW")

    def test_dollar_family(self) -> None:
        """The bare $ maps to the dollar-family codes, including USD."""
        assert len(SYMBOL_TO_CODES["$"]) >= 25
        assert "USD" in SYMBOL_TO_CODES["$"]

    def test_no_symbol_equals_its_code(self) -> None:
        """No symbol appears in its own value tuple."""
        for symbol, codes in SYMBOL_TO_CODES.items():
            assert symbol not in codes

    def test_no_symbol_looks_like_a_code(self) -> None:
        """No symbol is a code lookalike, contains whitespace, or is empty."""
        for symbol in SYMBOL_TO_CODES:
            assert not (
                len(symbol) == 3
                and symbol.isascii()
                and symbol.isalpha()
                and symbol.isupper()
            )
            assert not any(ch.isspace() for ch in symbol)
            assert symbol

    def test_name_keys_are_lowercase(self) -> None:
        """Every name key is lowercase (D4 — divergence from Money).

        Money's NAME_TO_CODES uses Title-Case keys; Currency's word
        grammar folds input to lowercase, so the keys are lowercase.
        """
        assert all(k == k.lower() for k in NAME_TO_CODES)

    def test_brief_anchored_names_definitive(self) -> None:
        """The brief-anchored display names are definitive mappings."""
        assert NAME_TO_CODES["dollar"] == ("USD",)
        assert NAME_TO_CODES["euro"] == ("EUR",)
        assert NAME_TO_CODES["ringgit"] == ("MYR",)

    def test_name_values_are_sorted_tuples_of_known_codes(self) -> None:
        """Every name value is a non-empty sorted tuple of in-scope codes."""
        for codes in NAME_TO_CODES.values():
            assert isinstance(codes, tuple)
            assert codes
            assert codes == tuple(sorted(codes))
            assert set(codes) <= CURRENCY_CODES


class TestCurrencySymbolTokens:
    """Tests for the grammar symbol-token ordering."""

    def test_tokens_are_exactly_the_symbol_table_keys(self) -> None:
        """Every shipped symbol token must resolve through SYMBOL_TO_CODES."""
        assert set(SYMBOL_TOKENS) == set(SYMBOL_TO_CODES)

    def test_qualified_tokens_before_bare(self) -> None:
        """All qualified tokens precede all bare tokens."""
        tokens = list(SYMBOL_TOKENS)
        first_bare = next(
            i for i, token in enumerate(tokens) if not _is_qualified(token)
        )
        assert all(_is_qualified(token) for token in tokens[:first_bare])
        assert all(not _is_qualified(token) for token in tokens[first_bare:])

    def test_longest_first_within_each_class(self) -> None:
        """Within each class, tokens are ordered longest first."""
        for cls in ("qualified", "bare"):
            tokens = [
                token
                for token in SYMBOL_TOKENS
                if _is_qualified(token) == (cls == "qualified")
            ]
            lengths = [len(token) for token in tokens]
            assert lengths == sorted(lengths, reverse=True)

    def test_no_token_is_prefix_of_a_later_token(self) -> None:
        """No token is a prefix of any token ordered after it.

        Longest-first ordering guarantees longest-match alternation: a
        longer token placed before its shorter prefix form always wins,
        so a shorter token must never shadow a longer token later in the
        order (e.g. "CFPF" precedes "CF", never the reverse).
        """
        tokens = list(SYMBOL_TOKENS)
        for i, token in enumerate(tokens):
            for later in tokens[i + 1 :]:
                assert not later.startswith(token)


class TestCurrencyWordTokens:
    """Tests for the grammar word-token ordering."""

    def test_tokens_are_exactly_the_name_table_keys(self) -> None:
        """Every shipped word token must resolve through NAME_TO_CODES."""
        assert set(WORD_TOKENS) == set(NAME_TO_CODES)

    def test_longest_first(self) -> None:
        """Word tokens are ordered longest first for alternation."""
        lengths = [len(token) for token in WORD_TOKENS]
        assert lengths == sorted(lengths, reverse=True)
