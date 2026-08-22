"""Tests for IBAN rule (scaffold)."""

import pytest

from paxman.capabilities.IBAN.rules.iso_ed2020 import IBANRule
from paxman.core.domain import RuleStrategy


@pytest.mark.capability
class TestIBANRule:
    """Rule: Section 1-overview (scaffold)."""

    def setup_method(self) -> None:
        self.rule = IBANRule()

    def test_rule_metadata(self) -> None:
        assert self.rule.name == "Section 1-overview"
        assert self.rule.strategy is RuleStrategy.REGEX
        assert self.rule.target_semantics == frozenset({"iban_recognition"})
        assert self.rule.requires_features == frozenset()
        assert self.rule.provenance.publication_year == 2020

    def test_matches(self) -> None:
        from paxman.capabilities.IBAN.contract import IBANContract
        from paxman.capabilities.IBAN.notation import IBANNotation

        contract = IBANContract()
        assert self.rule.matches(IBANNotation(value="example"), contract) is True

    def test_normalize_returns_canonical_string(self) -> None:
        from paxman.capabilities.IBAN.contract import IBANContract
        from paxman.capabilities.IBAN.notation import IBANNotation

        contract = IBANContract()
        result = self.rule.normalize(IBANNotation(value="example"), contract)
        assert isinstance(result, str)
        assert result == "example"
