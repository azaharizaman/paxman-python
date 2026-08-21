"""Tests for ISSN check-digit rule (ISO 3297:2022)."""

from __future__ import annotations

import pathlib

import pytest

from paxman.capabilities.ISSN.contract import ISSNContract
from paxman.capabilities.ISSN.notation import ISSNNotation
from paxman.capabilities.ISSN.rules.iso_3297_ed2022 import Section4CheckDigit
from paxman.core.domain import RuleStrategy

pytestmark = [pytest.mark.capability]


class TestSection4CheckDigit:
    """ISO 3297:2022 Section 4 — ISSN check digit."""

    def setup_method(self) -> None:
        self.rule = Section4CheckDigit()
        self.contract = ISSNContract()

    def test_check_digit_valid_hyphenated(self) -> None:
        """Valid ISSNs with correct mod-11 check digit match."""
        valid = ["03178471", "03785955", "00280836", "00000019", "1050124X"]
        for digits in valid:
            notation = ISSNNotation(digits=digits)
            assert self.rule.matches(notation, self.contract) is True, digits

    def test_check_digit_lowercase_x_valid(self) -> None:
        """Lowercase x folded to X is still valid when check is 10."""
        # 1050-124X is valid; grammar folds x->X but rule must accept X
        notation = ISSNNotation(digits="1050124X")
        assert self.rule.matches(notation, self.contract) is True
        lowercase_notation = ISSNNotation(digits="1050124x")
        assert self.rule.matches(lowercase_notation, self.contract) is True

    def test_check_digit_invalid(self) -> None:
        """Invalid check digit or charset fails."""
        for digits in ["03785954", "12345678", "0378595Y"]:
            assert (
                self.rule.matches(ISSNNotation(digits=digits), self.contract) is False
            )

    def test_check_mid_x_rejects(self) -> None:
        """X not in final position is rejected."""
        for digits in ["12X45679", "X2345679", "12X4567X"]:
            assert (
                self.rule.matches(ISSNNotation(digits=digits), self.contract) is False
            )

    def test_normalize_hyphenated(self) -> None:
        """normalize returns hyphenated XXXX-XXXX uppercased."""
        assert (
            self.rule.normalize(ISSNNotation(digits="03178471"), self.contract)
            == "0317-8471"
        )
        assert (
            self.rule.normalize(ISSNNotation(digits="1050124X"), self.contract)
            == "1050-124X"
        )
        # lower x in digits should be uppercased by normalize
        assert (
            self.rule.normalize(ISSNNotation(digits="1050124x"), self.contract)
            == "1050-124X"
        )

    def test_provenance(self) -> None:
        """Provenance fields match ISSN International Centre ISO 3297:2022."""
        prov = self.rule.provenance
        assert "ISSN" in prov.authority
        assert "ISO 3297:2022" in prov.specification_name
        assert prov.kind == "specification"
        assert prov.reference_url == "https://www.iso.org/standard/84536.html"
        assert prov.version == "2022"
        assert prov.lifecycle == "active"
        assert prov.publication_year == 2022

    def test_rule_conventions(self) -> None:
        """Name, strategy, citation, semantics, requires_features."""
        assert self.rule.name == "Section 4-issn-check-digit"
        assert self.rule.strategy == RuleStrategy.PARSER
        assert "Section 4" in self.rule.citation
        assert self.rule.target_semantics == frozenset({"issn_recognition"})
        assert self.rule.requires_features == frozenset()

    def test_no_output_format_token(self) -> None:
        """Source of rule module must not contain output_format token."""
        path = (
            pathlib.Path(__file__).resolve().parents[3]
            / "paxman"
            / "capabilities"
            / "ISSN"
            / "rules"
            / "iso_3297_ed2022.py"
        )
        text = path.read_text(encoding="utf-8")
        assert "output_format" not in text
