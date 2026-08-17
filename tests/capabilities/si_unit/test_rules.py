"""Tests for the SI Unit rule sections (BIPM SI Brochure + ISO 80000-1)."""

import pytest

from paxman.capabilities.SIUnit.contract import SIUnitContract
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.capabilities.SIUnit.rules.bipm_si_brochure_ed2019 import (
    SectionBaseUnits,
    SectionDerivedUnits,
    SectionNames,
    SectionNonSiUnits,
    SectionPrefixes,
)
from paxman.capabilities.SIUnit.rules.iso_80000_ed2022 import SectionCompounds
from paxman.core.domain import RuleStrategy

CONTRACT = SIUnitContract()
# Opt-in contract that preserves the legacy accept-multi-solidus behavior.
CONTRACT_MULTI_SOLIDUS = SIUnitContract(allow_multi_solidus=True)


@pytest.mark.capability
@pytest.mark.si_unit
class TestSectionBaseUnits:
    """BIPM Table 1 — base unit symbols."""

    def setup_method(self) -> None:
        self.rule = SectionBaseUnits()

    def test_rule_metadata(self) -> None:
        assert self.rule.name == "Section 2.3.1-base-units"
        assert self.rule.strategy is RuleStrategy.LOOKUP_TABLE
        assert frozenset({"symbol_recognition"}) == self.rule.target_semantics
        assert frozenset() == self.rule.requires_features
        assert self.rule.provenance.publication_year == 2019

    @pytest.mark.parametrize("symbol", ["m", "kg", "s", "A", "K", "mol", "cd"])
    def test_matches(self, symbol: str) -> None:
        assert self.rule.matches(SIUnitNotation(text=symbol, shape="symbol"), CONTRACT)

    @pytest.mark.parametrize("text", ["Pa", "km", "pa", "m/s", "da"])
    def test_rejects(self, text: str) -> None:
        assert not self.rule.matches(
            SIUnitNotation(text=text, shape="symbol"), CONTRACT
        )

    def test_rejects_non_symbol_shape(self) -> None:
        assert not self.rule.matches(SIUnitNotation(text="kg", shape="name"), CONTRACT)

    def test_normalize_is_identity(self) -> None:
        assert (
            self.rule.normalize(SIUnitNotation(text="kg", shape="symbol"), CONTRACT)
            == "kg"
        )

    def test_temporal_gate(self) -> None:
        old = SIUnitContract(year=2018)
        assert not self.rule.matches(SIUnitNotation(text="kg", shape="symbol"), old)
        assert self.rule.matches(SIUnitNotation(text="kg", shape="symbol"), CONTRACT)


@pytest.mark.capability
@pytest.mark.si_unit
class TestSectionDerivedUnits:
    """BIPM Tables 3–4 — derived units with special names."""

    def setup_method(self) -> None:
        self.rule = SectionDerivedUnits()

    @pytest.mark.parametrize("text", ["rad", "Hz", "Pa", "Ω", "°C", "kat"])
    def test_matches(self, text: str) -> None:
        assert self.rule.matches(SIUnitNotation(text=text, shape="symbol"), CONTRACT)

    @pytest.mark.parametrize("text", ["m", "km", "pa", "Hzs"])
    def test_rejects(self, text: str) -> None:
        assert not self.rule.matches(
            SIUnitNotation(text=text, shape="symbol"), CONTRACT
        )

    def test_normalize_is_identity(self) -> None:
        assert (
            self.rule.normalize(SIUnitNotation(text="Pa", shape="symbol"), CONTRACT)
            == "Pa"
        )


@pytest.mark.capability
@pytest.mark.si_unit
class TestSectionNonSiUnits:
    """BIPM Tables 8–9 — non-SI units accepted for use with the SI."""

    def setup_method(self) -> None:
        self.rule = SectionNonSiUnits()

    @pytest.mark.parametrize(
        "text", ["min", "h", "d", "°", "ha", "L", "l", "t", "Da", "eV"]
    )
    def test_matches(self, text: str) -> None:
        assert self.rule.matches(SIUnitNotation(text=text, shape="symbol"), CONTRACT)

    def test_litre_canonicalization(self) -> None:
        assert (
            self.rule.normalize(SIUnitNotation(text="l", shape="symbol"), CONTRACT)
            == "L"
        )
        assert (
            self.rule.normalize(SIUnitNotation(text="L", shape="symbol"), CONTRACT)
            == "L"
        )

    def test_rejects(self) -> None:
        assert not self.rule.matches(SIUnitNotation(text="m", shape="symbol"), CONTRACT)
        assert not self.rule.matches(
            SIUnitNotation(text="kelvin", shape="name"), CONTRACT
        )


@pytest.mark.capability
@pytest.mark.si_unit
class TestSectionPrefixes:
    """BIPM Table 5 + §3.2 — prefixed unit symbols."""

    def setup_method(self) -> None:
        self.rule = SectionPrefixes()

    @pytest.mark.parametrize(
        "text", ["km", "MHz", "µg", "mg", "hPa", "keV", "kDa", "dam"]
    )
    def test_matches(self, text: str) -> None:
        assert self.rule.matches(SIUnitNotation(text=text, shape="symbol"), CONTRACT)

    @pytest.mark.parametrize("text", ["k", "da", "M", "µ", "m", "cd", "kg"])
    def test_bare_prefixes_and_official_do_not_match(self, text: str) -> None:
        assert not self.rule.matches(
            SIUnitNotation(text=text, shape="symbol"), CONTRACT
        )

    def test_normalize_is_identity(self) -> None:
        assert (
            self.rule.normalize(SIUnitNotation(text="MHz", shape="symbol"), CONTRACT)
            == "MHz"
        )


@pytest.mark.capability
@pytest.mark.si_unit
class TestSectionNames:
    """BIPM Tables 1, 3–4, 8–9 — unit names resolve to canonical symbols."""

    def setup_method(self) -> None:
        self.rule = SectionNames()

    def test_rule_metadata(self) -> None:
        assert self.rule.name == "Section-names"
        assert self.rule.strategy is RuleStrategy.LOOKUP_TABLE
        assert frozenset({"name_recognition"}) == self.rule.target_semantics
        assert frozenset() == self.rule.requires_features
        assert self.rule.provenance.publication_year == 2019

    @pytest.mark.parametrize(
        ("name", "symbol"),
        [
            ("kilogram", "kg"),
            ("kelvin", "K"),
            ("megahertz", "MHz"),  # generated prefixed name
            ("kilometre", "km"),  # generated prefixed name
            ("microgram", "µg"),  # generated prefixed name
            ("degree celsius", "°C"),
            ("litre", "L"),
        ],
    )
    def test_matches_and_normalize(self, name: str, symbol: str) -> None:
        notation = SIUnitNotation(text=name, shape="name")
        assert self.rule.matches(notation, CONTRACT)
        assert self.rule.normalize(notation, CONTRACT) == symbol

    @pytest.mark.parametrize("text", ["quark", "kg", "megahert", "meter"])
    def test_rejects_unknown_names(self, text: str) -> None:
        assert not self.rule.matches(SIUnitNotation(text=text, shape="name"), CONTRACT)

    def test_rejects_non_name_shape(self) -> None:
        assert not self.rule.matches(
            SIUnitNotation(text="kg", shape="symbol"), CONTRACT
        )
        assert not self.rule.matches(
            SIUnitNotation(text="m/s", shape="compound"), CONTRACT
        )

    def test_temporal_gate(self) -> None:
        old = SIUnitContract(year=2018)
        assert not self.rule.matches(SIUnitNotation(text="kelvin", shape="name"), old)
        assert self.rule.matches(SIUnitNotation(text="kelvin", shape="name"), CONTRACT)


@pytest.mark.capability
@pytest.mark.si_unit
class TestSectionCompounds:
    """ISO 80000-1:2022 §6.5 — product and quotient unit compounds."""

    def setup_method(self) -> None:
        self.rule = SectionCompounds()

    def test_rule_metadata(self) -> None:
        assert self.rule.name == "Section 6.5-compounds"
        assert self.rule.strategy is RuleStrategy.PARSER
        assert frozenset({"compound_recognition"}) == self.rule.target_semantics
        assert frozenset() == self.rule.requires_features
        assert self.rule.provenance.publication_year == 2022

    @pytest.mark.parametrize(
        "text",
        [
            "m/s²",
            "m/s2",
            "km/h",
            "N·m",
            "N⋅m",
            "kg·m/s²",
            "g/cm³",
            "m·s⁻²",
            "µg/mL",
            "m/°C",
        ],
    )
    def test_matches(self, text: str) -> None:
        assert self.rule.matches(SIUnitNotation(text=text, shape="compound"), CONTRACT)

    @pytest.mark.parametrize("text", ["QQQ/zzz", "m/", "/s", "m s", "m/2", "/"])
    def test_rejects(self, text: str) -> None:
        assert not self.rule.matches(
            SIUnitNotation(text=text, shape="compound"), CONTRACT
        )

    def test_rejects_non_compound_shape(self) -> None:
        assert not self.rule.matches(
            SIUnitNotation(text="m/s", shape="symbol"), CONTRACT
        )

    @pytest.mark.parametrize(
        ("text", "canonical"),
        [
            ("m/s²", "m/s2"),
            ("m/s2", "m/s2"),
            ("N·m", "N·m"),
            ("N⋅m", "N·m"),
            ("kg·m/s²", "kg·m/s2"),
            ("g/cm³", "g/cm3"),
            ("m·s⁻²", "m·s-2"),
            ("l/s", "L/s"),
            ("µm/s", "µm/s"),
        ],
    )
    def test_normalize(self, text: str, canonical: str) -> None:
        result = self.rule.normalize(
            SIUnitNotation(text=text, shape="compound"), CONTRACT
        )
        assert result == canonical

    def test_temporal_gate(self) -> None:
        old = SIUnitContract(year=2021)
        assert not self.rule.matches(SIUnitNotation(text="m/s", shape="compound"), old)
        assert self.rule.matches(SIUnitNotation(text="m/s", shape="compound"), CONTRACT)

    def test_rejects_multi_solidus_by_default(self) -> None:
        # ISO 80000-1 §6.6.2: a solidus shall not be followed by a
        # multiplication/division sign unless parentheses disambiguate.
        # More than one top-level "/" is INVALID under the default contract.
        assert not self.rule.matches(
            SIUnitNotation(text="kg/m/s", shape="compound"), CONTRACT
        )

    def test_matches_multi_solidus_when_allowed(self) -> None:
        # The legacy accept-multi-solidus behavior is preserved when the
        # contract opts in via allow_multi_solidus=True.
        assert self.rule.matches(
            SIUnitNotation(text="kg/m/s", shape="compound"), CONTRACT_MULTI_SOLIDUS
        )

    def test_matches_parenthesized_denominator(self) -> None:
        # ISO 80000-1 §6.6.2 prescribes parentheses as THE disambiguation,
        # so a parenthesized denominator MUST resolve (not reject).
        assert self.rule.matches(
            SIUnitNotation(text="kg/(m·s²)", shape="compound"), CONTRACT
        )

    def test_rejects_unbalanced_parentheses(self) -> None:
        # A parenthesized factor requires a closing ")"; an unbalanced
        # expression is not a valid compound.
        assert not self.rule.matches(
            SIUnitNotation(text="kg/(m·s²", shape="compound"), CONTRACT
        )

    def test_normalize_parenthesized_denominator(self) -> None:
        # The whole expression is captured as one compound span; parens are
        # preserved, superscripts ASCII-ized, "·"/"/" preserved.
        result = self.rule.normalize(
            SIUnitNotation(text="kg/(m·s²)", shape="compound"), CONTRACT
        )
        assert result == "kg/(m·s2)"

    def test_normalize_multi_solidus_when_allowed(self) -> None:
        result = self.rule.normalize(
            SIUnitNotation(text="kg/m/s", shape="compound"), CONTRACT_MULTI_SOLIDUS
        )
        assert result == "kg/m/s"
