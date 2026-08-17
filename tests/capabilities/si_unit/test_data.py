"""Tests for the SI Unit maintained authority tables and generated data modules."""

import subprocess
import sys
from pathlib import Path

import pytest

from paxman.capabilities.SIUnit.grammar.data.unit_name_tokens import NAME_TOKENS
from paxman.capabilities.SIUnit.grammar.data.unit_symbol_tokens import SYMBOL_TOKENS
from paxman.capabilities.SIUnit.rules.data.prefixed_unit_names import (
    PREFIXED_NAME_TO_SYMBOL,
)
from paxman.capabilities.SIUnit.rules.data.prefixed_units import PREFIXED_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_base_units import BASE_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_derived_units import DERIVED_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_nonsi_units import (
    LITRE_WRITTEN_FORMS,
    NONSI_UNIT_SYMBOLS,
)
from paxman.capabilities.SIUnit.rules.data.si_prefixes import (
    PREFIX_NAMES,
    PREFIX_SYMBOLS,
)
from paxman.capabilities.SIUnit.rules.data.unit_names import NAME_TO_SYMBOL

TOOLS_DIR = Path(__file__).resolve().parents[3] / "tools"
GENERATOR = TOOLS_DIR / "regenerate_si_prefix_data.py"


@pytest.mark.capability
@pytest.mark.si_unit
class TestAuthorityTables:
    """Locked counts and rows for the maintained authority tables."""

    def test_base_unit_symbols(self) -> None:
        assert frozenset({"m", "kg", "s", "A", "K", "mol", "cd"}) == BASE_UNIT_SYMBOLS

    def test_derived_unit_symbols(self) -> None:
        # 22 BIPM Table 3 special-name units + "g" (the gram — the
        # prefix attachment point for mass, per BIPM SI Brochure §3.2).
        assert len(DERIVED_UNIT_SYMBOLS) == 23
        assert (
            frozenset(
                {
                    "rad",
                    "sr",
                    "Hz",
                    "N",
                    "Pa",
                    "J",
                    "W",
                    "C",
                    "V",
                    "F",
                    "Ω",
                    "S",
                    "Wb",
                    "T",
                    "H",
                    "°C",
                    "lm",
                    "lx",
                    "Bq",
                    "Gy",
                    "Sv",
                    "kat",
                    "g",
                }
            )
            == DERIVED_UNIT_SYMBOLS
        )

    def test_prefix_symbols(self) -> None:
        assert len(PREFIX_SYMBOLS) == 24
        assert (
            frozenset(
                {
                    "da",
                    "h",
                    "k",
                    "M",
                    "G",
                    "T",
                    "P",
                    "E",
                    "Z",
                    "Y",
                    "R",
                    "Q",
                    "d",
                    "c",
                    "m",
                    "µ",
                    "n",
                    "p",
                    "f",
                    "a",
                    "z",
                    "y",
                    "r",
                    "q",
                }
            )
            == PREFIX_SYMBOLS
        )

    def test_prefix_names(self) -> None:
        assert len(PREFIX_NAMES) == 24
        assert PREFIX_NAMES["k"] == "kilo"
        assert PREFIX_NAMES["µ"] == "micro"
        assert PREFIX_NAMES["da"] == "deca"

    def test_non_si_units(self) -> None:
        assert (
            frozenset(
                {
                    "min",
                    "h",
                    "d",
                    "°",
                    "′",
                    "″",
                    "ha",
                    "L",
                    "l",
                    "t",
                    "Da",
                    "eV",
                    "u",
                    "Å",
                    "b",
                    "bar",
                    "mmHg",
                }
            )
            == NONSI_UNIT_SYMBOLS
        )
        assert frozenset({"L", "l"}) == LITRE_WRITTEN_FORMS

    def test_name_to_symbol_locked_rows(self) -> None:
        assert NAME_TO_SYMBOL["kilogram"] == "kg"
        assert NAME_TO_SYMBOL["kelvin"] == "K"
        assert NAME_TO_SYMBOL["degree celsius"] == "°C"
        assert NAME_TO_SYMBOL["litre"] == "L"
        assert NAME_TO_SYMBOL["metre"] == "m"
        assert NAME_TO_SYMBOL["hertz"] == "Hz"
        assert NAME_TO_SYMBOL["gram"] == "g"


@pytest.mark.capability
@pytest.mark.si_unit
class TestGeneratedData:
    """Invariants and locked rows for the generated tables."""

    def test_prefixed_units_disjoint_from_official(self) -> None:
        official = BASE_UNIT_SYMBOLS | DERIVED_UNIT_SYMBOLS | NONSI_UNIT_SYMBOLS
        assert PREFIXED_UNIT_SYMBOLS.isdisjoint(official)

    def test_locked_prefixed_rows(self) -> None:
        for token in ("km", "MHz", "µg", "mg", "cm", "hPa", "keV", "kDa", "dam"):
            assert token in PREFIXED_UNIT_SYMBOLS
        assert "kg" not in PREFIXED_UNIT_SYMBOLS  # official base symbol wins
        assert "cd" not in PREFIXED_UNIT_SYMBOLS  # candela wins over centi-day

    def test_prefixed_name_to_symbol_locked_rows(self) -> None:
        assert PREFIXED_NAME_TO_SYMBOL["megahertz"] == "MHz"
        assert PREFIXED_NAME_TO_SYMBOL["kilometre"] == "km"
        assert PREFIXED_NAME_TO_SYMBOL["microgram"] == "µg"
        assert "kilogram" not in PREFIXED_NAME_TO_SYMBOL  # official name wins
        assert "kg" not in PREFIXED_NAME_TO_SYMBOL

    def test_no_kg_prefix_stacking(self) -> None:
        # BIPM §3.2 (D9): prefixes attach to the gram, so "kg" is never a
        # prefixable unit — no "kilokilogram"/"megakilogram" junk.
        assert not any(name.endswith("kilogram") for name in PREFIXED_NAME_TO_SYMBOL)
        assert set(PREFIXED_NAME_TO_SYMBOL).isdisjoint(NAME_TO_SYMBOL)

    def test_symbol_tokens_cover_and_order(self) -> None:
        official = BASE_UNIT_SYMBOLS | DERIVED_UNIT_SYMBOLS | NONSI_UNIT_SYMBOLS
        assert set(SYMBOL_TOKENS) == official | PREFIX_SYMBOLS | PREFIXED_UNIT_SYMBOLS
        lengths = [len(t) for t in SYMBOL_TOKENS]
        assert lengths == sorted(lengths, reverse=True)

    def test_name_tokens_longest_first(self) -> None:
        lengths = [len(t) for t in NAME_TOKENS]
        assert lengths == sorted(lengths, reverse=True)
        assert "degree celsius" in NAME_TOKENS
        assert "kilometre" in NAME_TOKENS
        assert "megahertz" in NAME_TOKENS

    def test_generator_is_idempotent(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            capture_output=True,
            text=True,
            cwd=TOOLS_DIR.parent,
        )
        assert result.returncode == 0, result.stderr
