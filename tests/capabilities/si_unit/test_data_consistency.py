"""Cross-layer data-consistency tests for the SI Unit capability.

House mandate (Currency precedent): every recognition key shipped by the
grammar/data token tables must resolve through the rules/data authority
tables, and every authority symbol must be reachable from the token
tables. Grammar<->rule key agreement is asserted here, not per-file.
"""

from __future__ import annotations

import pytest

from paxman.capabilities.SIUnit.grammar.data.unit_name_tokens import NAME_TOKENS
from paxman.capabilities.SIUnit.grammar.data.unit_symbol_tokens import SYMBOL_TOKENS
from paxman.capabilities.SIUnit.rules.data.prefixed_unit_names import (
    PREFIXED_NAME_TO_SYMBOL,
)
from paxman.capabilities.SIUnit.rules.data.prefixed_units import PREFIXED_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_base_units import BASE_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_derived_units import DERIVED_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_nonsi_units import NONSI_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_prefixes import (
    PREFIX_NAMES,
    PREFIX_SYMBOLS,
)
from paxman.capabilities.SIUnit.rules.data.unit_names import NAME_TO_SYMBOL

pytestmark = [pytest.mark.capability, pytest.mark.si_unit]

OFFICIAL_SYMBOLS = BASE_UNIT_SYMBOLS | DERIVED_UNIT_SYMBOLS | NONSI_UNIT_SYMBOLS
FULL_NAME_TO_SYMBOL = NAME_TO_SYMBOL | PREFIXED_NAME_TO_SYMBOL


class TestSymbolCoverage:
    """Every grammar symbol token is an authority symbol, and vice versa."""

    def test_token_set_equals_authority_symbols(self) -> None:
        assert set(SYMBOL_TOKENS) == (
            OFFICIAL_SYMBOLS | PREFIX_SYMBOLS | PREFIXED_UNIT_SYMBOLS
        )

    def test_generated_symbols_disjoint_from_official(self) -> None:
        assert PREFIXED_UNIT_SYMBOLS.isdisjoint(OFFICIAL_SYMBOLS)

    def test_kg_not_prefixable(self) -> None:
        # D9: prefixes attach to the gram, never to the kilogram.
        assert "kg" not in PREFIXED_UNIT_SYMBOLS
        assert "g" in OFFICIAL_SYMBOLS


class TestNameCoverage:
    """Every grammar name token resolves; every resolvable name is a token."""

    def test_name_tokens_equal_full_name_map(self) -> None:
        assert set(NAME_TOKENS) == set(FULL_NAME_TO_SYMBOL)

    def test_names_resolve_to_known_symbols(self) -> None:
        assert set(FULL_NAME_TO_SYMBOL.values()) <= (
            OFFICIAL_SYMBOLS | PREFIXED_UNIT_SYMBOLS
        )

    def test_prefixed_names_disjoint_from_official_names(self) -> None:
        assert set(PREFIXED_NAME_TO_SYMBOL).isdisjoint(NAME_TO_SYMBOL)

    def test_no_kilogram_stacking(self) -> None:
        assert not any(n.endswith("kilogram") for n in PREFIXED_NAME_TO_SYMBOL)


class TestDecompositionInvariants:
    """Generated prefixed symbols/names decompose into known parts."""

    def test_gram_is_the_prefix_attachment_point(self) -> None:
        # D9: "microgram" -> "µg" is reachable only via name "gram" -> "g".
        assert NAME_TO_SYMBOL["gram"] == "g"

    def test_prefixed_symbols_decompose(self) -> None:
        prefixes = sorted(PREFIX_SYMBOLS, key=lambda p: (-len(p), p))
        for symbol in PREFIXED_UNIT_SYMBOLS:
            for prefix in prefixes:
                if symbol.startswith(prefix):
                    unit = symbol[len(prefix) :]
                    assert unit in OFFICIAL_SYMBOLS
                    assert unit != "kg"  # D9
                    break
            else:
                pytest.fail(f"{symbol!r} does not start with any prefix symbol")

    def test_prefixed_names_decompose(self) -> None:
        prefix_names = sorted(set(PREFIX_NAMES.values()), key=lambda n: (-len(n), n))
        for name, symbol in PREFIXED_NAME_TO_SYMBOL.items():
            for prefix_name in prefix_names:
                if name.startswith(prefix_name):
                    unit_name = name[len(prefix_name) :]
                    assert unit_name in NAME_TO_SYMBOL
                    assert NAME_TO_SYMBOL[unit_name] in OFFICIAL_SYMBOLS
                    break
            else:
                pytest.fail(f"{name!r} does not start with any prefix name")
            assert symbol in PREFIXED_UNIT_SYMBOLS


class TestTokenShapeInvariants:
    """Symbol tokens are bare; name tokens are lowercase (grammar folds)."""

    def test_no_whitespace_in_symbol_tokens(self) -> None:
        assert all(" " not in t for t in SYMBOL_TOKENS)

    def test_name_tokens_lowercase(self) -> None:
        assert all(t == t.lower() for t in NAME_TOKENS)

    def test_no_empty_tokens(self) -> None:
        assert all(SYMBOL_TOKENS)
        assert all(NAME_TOKENS)
