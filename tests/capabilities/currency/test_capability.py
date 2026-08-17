"""Tests for CurrencyCapability wiring."""

import pytest

from paxman.capabilities.Currency.capability import CurrencyCapability
from paxman.capabilities.Currency.contract import CurrencyContract
from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.core.capability import Capability


@pytest.mark.capability
@pytest.mark.currency
class TestCurrencyCapability:
    """Tests for CurrencyCapability wiring."""

    def test_is_capability_subclass(self) -> None:
        """Verify inheritance from the base Capability."""
        assert issubclass(CurrencyCapability, Capability)

    def test_name(self) -> None:
        """Verify the capability name."""
        assert CurrencyCapability.name == "currency"

    def test_get_grammars(self) -> None:
        """Verify the three grammar instances and their names."""
        cap = CurrencyCapability()
        grammars = cap.get_grammars()
        assert len(grammars) == 3
        assert [g.name for g in grammars] == [
            "code_recognition",
            "symbol_recognition",
            "word_recognition",
        ]

    def test_get_rules(self) -> None:
        """Verify the three rule instances and their names."""
        cap = CurrencyCapability()
        rules = cap.get_rules()
        assert len(rules) == 3
        assert [r.name for r in rules] == [
            "Section-code",
            "Section-symbols",
            "Section-names",
        ]

    def test_rule_classes(self) -> None:
        """Verify the exact rule classes wired by get_rules()."""
        cap = CurrencyCapability()
        assert [type(r).__name__ for r in cap.get_rules()] == [
            "SectionCode",
            "SectionSymbols",
            "SectionNames",
        ]

    def test_create_contract_defaults(self) -> None:
        """create_contract() with no args produces the correct defaults."""
        c = CurrencyCapability.create_contract()
        assert c.capability_name == "currency"
        assert c.default_currency is None
        assert c.output_format == "code"

    def test_create_contract_default_currency(self) -> None:
        """default_currency passes through to the contract."""
        c = CurrencyCapability.create_contract(default_currency="USD")
        assert c.default_currency == "USD"

    def test_create_contract_excluded_rules(self) -> None:
        """excluded_rules passes through to the contract."""
        c = CurrencyCapability.create_contract(excluded_rules=["Section-code"])
        assert c.excluded_rules == ("Section-code",)

    def test_create_contract_common_block(self) -> None:
        """The unanimous common block passes through to the contract."""
        c = CurrencyCapability.create_contract(
            excluded_rules=["Section-names"],
            pinned_rules=["Section-code"],
            year=2020,
            output_format="code",
        )
        assert c.excluded_rules == ("Section-names",)
        assert c.pinned_rules == ("Section-code",)
        assert c.year == 2020
        assert c.output_format == "code"

    def test_contract_format_surface(self) -> None:
        """The formatter's formats match the contract class variables."""
        assert CurrencyContract.DEFAULT_OUTPUT_FORMAT == "code"
        assert frozenset() == CurrencyContract.OFFERED_OUTPUT_FORMATS


@pytest.mark.capability
@pytest.mark.currency
class TestCurrencyCapabilityFormatValue:
    """Tests for CurrencyCapability.format_value()."""

    NOTATION = CurrencyNotation(text="USD", shape="code")

    def test_code_is_identity(self) -> None:
        """The default code path returns the canonical value unchanged.

        Currency does NOT override format_value: the canonical value IS
        the "code" format (uppercase alpha-3) and there are no offered
        alternatives, so the Capability base identity formatter applies.
        """
        cap = CurrencyCapability()
        assert cap.format_value("USD", "code", self.NOTATION) == "USD"


# --- Package import tests ---


class TestCurrencyPackageImports:
    @pytest.mark.capability
    @pytest.mark.currency
    def test_package_exports_currency_capability(self) -> None:
        """Currency package exports CurrencyCapability."""
        from paxman.capabilities.Currency import (
            CurrencyCapability as CurrencyCapabilityExport,
        )

        assert CurrencyCapabilityExport is CurrencyCapability

    @pytest.mark.capability
    @pytest.mark.currency
    def test_package_exports_currency_contract(self) -> None:
        """Currency package exports CurrencyContract."""
        from paxman.capabilities.Currency import (
            CurrencyContract as CurrencyContractExport,
        )

        assert CurrencyContractExport is CurrencyContract

    @pytest.mark.capability
    @pytest.mark.currency
    def test_package_exports_currency_notation(self) -> None:
        """Currency package exports CurrencyNotation."""
        from paxman.capabilities.Currency import (
            CurrencyNotation as CurrencyNotationExport,
        )

        assert CurrencyNotationExport is CurrencyNotation

    @pytest.mark.capability
    @pytest.mark.currency
    def test_capability_module_all(self) -> None:
        """The capability module __all__ lists the three public names."""
        from paxman.capabilities.Currency.capability import __all__ as cap_all

        assert cap_all == ["CurrencyCapability", "CurrencyContract", "CurrencyNotation"]
