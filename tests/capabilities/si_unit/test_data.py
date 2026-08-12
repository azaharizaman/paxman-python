"""Tests for the SI Unit maintained authority tables."""

import pytest

from paxman.capabilities.SIUnit.rules.data.si_base_units import BASE_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_derived_units import DERIVED_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_nonsi_units import NONSI_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_prefixes import (
    PREFIX_NAMES,
    PREFIX_SYMBOLS,
)
from paxman.capabilities.SIUnit.rules.data.unit_names import NAME_TO_SYMBOL


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
        assert {"rad", "Hz", "Pa", "Ω", "°C", "kat"} <= DERIVED_UNIT_SYMBOLS

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
        assert {
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
        } <= NONSI_UNIT_SYMBOLS

    def test_name_to_symbol_locked_rows(self) -> None:
        assert NAME_TO_SYMBOL["kilogram"] == "kg"
        assert NAME_TO_SYMBOL["kelvin"] == "K"
        assert NAME_TO_SYMBOL["degree celsius"] == "°C"
        assert NAME_TO_SYMBOL["litre"] == "L"
        assert NAME_TO_SYMBOL["metre"] == "m"
        assert NAME_TO_SYMBOL["hertz"] == "Hz"
