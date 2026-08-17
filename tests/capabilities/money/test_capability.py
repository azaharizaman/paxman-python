"""Tests for MoneyCapability wiring."""

import pytest

from paxman.capabilities.Money.capability import MoneyCapability
from paxman.capabilities.Money.contract import MoneyContract
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.core.capability import Capability


@pytest.mark.capability
class TestMoneyCapability:
    """Tests for MoneyCapability wiring."""

    def test_is_capability_subclass(self) -> None:
        """Verify inheritance from the base Capability."""
        assert issubclass(MoneyCapability, Capability)

    def test_name(self) -> None:
        """Verify the capability name."""
        assert MoneyCapability.name == "money"

    def test_get_grammars(self) -> None:
        """Verify the three grammar instances and their names."""
        cap = MoneyCapability()
        grammars = cap.get_grammars()
        assert len(grammars) == 3
        assert [g.name for g in grammars] == [
            "code_recognition",
            "symbol_recognition",
            "word_recognition",
        ]

    def test_get_rules(self) -> None:
        """Verify the three rule instances and their names."""
        cap = MoneyCapability()
        rules = cap.get_rules()
        assert len(rules) == 3
        assert [r.name for r in rules] == [
            "Section-codes",
            "Section-symbols",
            "Section-names",
        ]

    def test_rule_classes(self) -> None:
        """Verify the exact rule classes wired by get_rules()."""
        cap = MoneyCapability()
        assert [type(r).__name__ for r in cap.get_rules()] == [
            "SectionCode",
            "SectionSymbols",
            "SectionNames",
        ]

    def test_create_contract_defaults(self) -> None:
        """create_contract() with no args produces the correct defaults."""
        c = MoneyCapability.create_contract()
        assert c.capability_name == "money"
        assert c.precision == "strict"
        assert c.dollar_sign_currency is None
        assert c.output_format == "code_amount"

    def test_create_contract_precision(self) -> None:
        """precision passes through to the contract."""
        c = MoneyCapability.create_contract(precision="round")
        assert c.precision == "round"

    def test_create_contract_dollar_sign_currency(self) -> None:
        """dollar_sign_currency passes through to the contract."""
        c = MoneyCapability.create_contract(dollar_sign_currency="MYR")
        assert c.dollar_sign_currency == "MYR"

    def test_create_contract_dollar_sign_currency_none(self) -> None:
        """dollar_sign_currency=None passes through (bare $ becomes INVALID)."""
        c = MoneyCapability.create_contract(dollar_sign_currency=None)
        assert c.dollar_sign_currency is None

    def test_create_contract_common_block(self) -> None:
        """The unanimous common block passes through to the contract."""
        c = MoneyCapability.create_contract(
            excluded_rules=["Section-names"],
            pinned_rules=["Section-codes"],
            year=2020,
            output_format="compact",
        )
        assert c.excluded_rules == ("Section-names",)
        assert c.pinned_rules == ("Section-codes",)
        assert c.year == 2020
        assert c.output_format == "compact"

    def test_create_contract_output_format_default(self) -> None:
        """An unset output_format resolves to code_amount."""
        c = MoneyCapability.create_contract()
        assert c.output_format == "code_amount"

    def test_create_contract_output_format_compact(self) -> None:
        """output_format="compact" resolves to compact."""
        c = MoneyCapability.create_contract(output_format="compact")
        assert c.output_format == "compact"

    def test_contract_format_surface(self) -> None:
        """The formatter's formats match the contract class variables."""
        assert MoneyContract.DEFAULT_OUTPUT_FORMAT == "code_amount"
        assert frozenset({"compact"}) == MoneyContract.OFFERED_OUTPUT_FORMATS


@pytest.mark.capability
class TestMoneyCapabilityFormatValue:
    """Tests for MoneyCapability.format_value()."""

    NOTATION = MoneyNotation(currency_part="USD", amount_part="500.00")

    def test_code_amount_is_identity(self) -> None:
        """The default code_amount path returns the canonical value unchanged."""
        cap = MoneyCapability()
        assert (
            cap.format_value("USD 500.00", "code_amount", self.NOTATION) == "USD 500.00"
        )

    def test_default_format_is_identity(self) -> None:
        """An unset output format returns the canonical value unchanged."""
        cap = MoneyCapability()
        assert cap.format_value("USD 500.00", None, self.NOTATION) == "USD 500.00"

    def test_compact_removes_separator_space(self) -> None:
        """Compact rendering removes the single ASCII space between code and amount."""
        cap = MoneyCapability()
        assert cap.format_value("USD 500.00", "compact", self.NOTATION) == "USD500.00"

    def test_compact_zero_decimal_currency(self) -> None:
        """Compact rendering works for 0-decimal amounts (no fraction)."""
        cap = MoneyCapability()
        notation = MoneyNotation(currency_part="JPY", amount_part="1000")
        assert cap.format_value("JPY 1000", "compact", notation) == "JPY1000"

    def test_compact_three_decimal_currency(self) -> None:
        """Compact rendering works for 3-decimal amounts."""
        cap = MoneyCapability()
        notation = MoneyNotation(currency_part="BHD", amount_part="500.000")
        assert cap.format_value("BHD 500.000", "compact", notation) == "BHD500.000"

    def test_compact_preserves_amount_with_narrow_no_break_space(self) -> None:
        """Only the code/amount ASCII space is removed.

        The space_decimal amount shape carries a NARROW NO-BREAK SPACE
        (U+202F) in its token, never an ASCII space, so the sole ASCII space
        in the canonical value is always the code/amount separator.
        """
        cap = MoneyCapability()
        notation = MoneyNotation(currency_part="EUR", amount_part="1\u202f234,50")
        assert (
            cap.format_value("EUR 1\u202f234,50", "compact", notation)
            == "EUR1\u202f234,50"
        )


# --- Package import tests ---


class TestMoneyPackageImports:
    @pytest.mark.capability
    def test_package_exports_money_capability(self) -> None:
        """Money package exports MoneyCapability."""
        from paxman.capabilities.Money import MoneyCapability as MoneyCapabilityExport

        assert MoneyCapabilityExport is MoneyCapability

    @pytest.mark.capability
    def test_package_exports_money_contract(self) -> None:
        """Money package exports MoneyContract."""
        from paxman.capabilities.Money import MoneyContract as MoneyContractExport

        assert MoneyContractExport is MoneyContract

    @pytest.mark.capability
    def test_package_exports_money_notation(self) -> None:
        """Money package exports MoneyNotation."""
        from paxman.capabilities.Money import MoneyNotation as MoneyNotationExport

        assert MoneyNotationExport is MoneyNotation
