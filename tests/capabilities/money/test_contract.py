# tests/capabilities/money/test_contract.py
"""Tests for Money contract."""

import dataclasses

import pytest

from paxman.capabilities.Money.contract import MoneyContract
from paxman.core.errors import ContractError

_STANDARD_KEYS = frozenset(
    {"capability_name", "excluded_rules", "pinned_rules", "year", "output_format"}
)


@pytest.mark.capability
class TestMoneyContractDefaults:
    """Default field values."""

    def test_default_output_format(self) -> None:
        """output_format resolves to code_amount by default."""
        assert MoneyContract().output_format == "code_amount"

    def test_offered_output_formats(self) -> None:
        """Only compact is offered beyond the default."""
        assert frozenset({"compact"}) == MoneyContract.OFFERED_OUTPUT_FORMATS

    def test_capability_name(self) -> None:
        """capability_name is fixed to money."""
        assert MoneyContract().capability_name == "money"

    def test_precision_default(self) -> None:
        """precision defaults to strict."""
        assert MoneyContract().precision == "strict"

    def test_dollar_sign_currency_default(self) -> None:
        """dollar_sign_currency defaults to None (bare $ stays INVALID)."""
        assert MoneyContract().dollar_sign_currency is None

    def test_active_grammars(self) -> None:
        """All three recognition grammars are active by default."""
        assert MoneyContract().active_grammars == (
            "code_recognition",
            "symbol_recognition",
            "word_recognition",
        )

    def test_frozen(self) -> None:
        """Assigning a field raises FrozenInstanceError."""
        contract = MoneyContract()
        with pytest.raises(dataclasses.FrozenInstanceError):
            contract.precision = "round"  # type: ignore[misc]


@pytest.mark.capability
class TestMoneyContractPrecision:
    """precision validation."""

    @pytest.mark.parametrize("precision", ["strict", "truncate", "round"])
    def test_valid_precision_accepted(self, precision: str) -> None:
        """Each of the three precision values is accepted."""
        assert MoneyContract(precision=precision).precision == precision

    @pytest.mark.parametrize("precision", ["bogus", "", "STRICT", 42, None])
    def test_invalid_precision_raises_contract_error(self, precision: object) -> None:
        """Anything outside the three raises ContractError at construction."""
        with pytest.raises(ContractError):
            MoneyContract(precision=precision)


@pytest.mark.capability
class TestMoneyContractDollarSignCurrency:
    """dollar_sign_currency validation."""

    def test_none_allowed(self) -> None:
        """None (the default) means bare $ symbols stay unresolved."""
        assert MoneyContract(dollar_sign_currency=None).dollar_sign_currency is None

    def test_uppercase_alpha3_accepted(self) -> None:
        """An uppercase ISO 4217 alpha-3 code is accepted (opt-in)."""
        assert MoneyContract(dollar_sign_currency="EUR").dollar_sign_currency == "EUR"

    @pytest.mark.parametrize("currency", ["usd", "US", "US1", "USDD", "U$D", 123])
    def test_invalid_dollar_sign_currency_raises_contract_error(
        self, currency: object
    ) -> None:
        """Non-alpha-3 dollar_sign_currency values raise ContractError."""
        with pytest.raises(ContractError):
            MoneyContract(dollar_sign_currency=currency)


@pytest.mark.capability
class TestMoneyContractOutputFormat:
    """output_format resolution (base-class rules)."""

    @pytest.mark.parametrize("value", [None, "default", "code_amount"])
    def test_default_paths_resolve_to_code_amount(self, value: str | None) -> None:
        """None/default/code_amount all resolve to code_amount."""
        assert MoneyContract(output_format=value).output_format == "code_amount"

    def test_compact_resolves_to_compact(self) -> None:
        """The offered compact format resolves to itself."""
        assert MoneyContract(output_format="compact").output_format == "compact"

    @pytest.mark.parametrize("fmt", ["", "none", "None", "hyphenated", "compact "])
    def test_unknown_format_raises_contract_error(self, fmt: str) -> None:
        """Unoffered output_format values raise ContractError at construction."""
        with pytest.raises(ContractError):
            MoneyContract(output_format=fmt)


@pytest.mark.capability
class TestMoneyContractSerialization:
    """as_dict surface."""

    def test_as_dict_deterministic_key_set(self) -> None:
        """as_dict() emits the standard keys plus precision and dollar_sign_currency."""
        assert set(MoneyContract().as_dict().keys()) == _STANDARD_KEYS | {
            "precision",
            "dollar_sign_currency",
        }

    def test_as_dict_values(self) -> None:
        """as_dict() serializes precision and dollar_sign_currency with their values."""
        d = MoneyContract(precision="round", dollar_sign_currency="JPY").as_dict()
        assert d["precision"] == "round"
        assert d["dollar_sign_currency"] == "JPY"

    def test_as_dict_includes_resolved_output_format(self) -> None:
        """as_dict() emits the resolved (non-None) output_format."""
        assert MoneyContract().as_dict()["output_format"] == "code_amount"

    def test_extra_dict_fields_do_not_collide_with_standard_keys(self) -> None:
        """Capability-specific as_dict() keys never shadow the standard keys."""
        assert not (set(MoneyContract()._extra_dict_fields()) & _STANDARD_KEYS)
