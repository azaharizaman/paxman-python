from __future__ import annotations

from typing import Any

import pytest

from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.Email.contract import EmailContract
from paxman.core.contract import Contract


class _FullyCompliantContract:
    """A class that fully satisfies the Contract protocol."""

    @property
    def capability_name(self) -> str:
        return "email"

    @property
    def active_grammars(self) -> list[str]:
        return ["standard_recognition"]

    @property
    def excluded_rules(self) -> list[str]:
        return []

    @property
    def year(self) -> int | None:
        return 2024

    @property
    def output_format(self) -> str | None:
        return None

    @property
    def two_digit_base_year(self) -> int | None:
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_name": self.capability_name,
            "active_grammars": self.active_grammars,
            "excluded_rules": self.excluded_rules,
            "year": self.year,
            "output_format": self.output_format,
            "two_digit_base_year": self.two_digit_base_year,
        }


class _MissingAsDict:
    """Missing the as_dict method."""

    @property
    def capability_name(self) -> str:
        return "email"

    @property
    def active_grammars(self) -> list[str]:
        return ["standard_recognition"]

    @property
    def excluded_rules(self) -> list[str]:
        return []

    @property
    def year(self) -> int | None:
        return None

    @property
    def output_format(self) -> str | None:
        return None

    @property
    def two_digit_base_year(self) -> int | None:
        return None


class _MissingCapabilityName:
    """Missing the capability_name property."""

    @property
    def active_grammars(self) -> list[str]:
        return []

    @property
    def excluded_rules(self) -> list[str]:
        return []

    @property
    def year(self) -> int | None:
        return None

    @property
    def output_format(self) -> str | None:
        return None

    @property
    def two_digit_base_year(self) -> int | None:
        return None

    def as_dict(self) -> dict[str, Any]:
        return {}


class TestContractProtocol:
    @pytest.mark.unit
    def test_compliant_class_passes_isinstance(self) -> None:
        assert isinstance(_FullyCompliantContract(), Contract)

    @pytest.mark.unit
    def test_missing_as_dict_fails_isinstance(self) -> None:
        assert not isinstance(_MissingAsDict(), Contract)

    @pytest.mark.unit
    def test_missing_capability_name_fails_isinstance(self) -> None:
        assert not isinstance(_MissingCapabilityName(), Contract)

    @pytest.mark.unit
    def test_protocol_is_runtime_checkable(self) -> None:
        # The @runtime_checkable decorator should be present;
        # the isinstance checks above already verify this, but
        # we make it explicit here.
        contract = _FullyCompliantContract()
        assert isinstance(contract, Contract)

    @pytest.mark.unit
    def test_as_dict_returns_correct_keys(self) -> None:
        contract = _FullyCompliantContract()
        result = contract.as_dict()
        assert set(result.keys()) == {
            "capability_name",
            "active_grammars",
            "excluded_rules",
            "year",
            "output_format",
            "two_digit_base_year",
        }

    @pytest.mark.unit
    def test_year_can_be_none(self) -> None:
        """Contract.year is int | None — verify None is valid."""

        class _NoneYear:
            @property
            def capability_name(self) -> str:
                return "date"

            @property
            def active_grammars(self) -> list[str]:
                return []

            @property
            def excluded_rules(self) -> list[str]:
                return []

            @property
            def year(self) -> int | None:
                return None

            @property
            def output_format(self) -> str | None:
                return None

            @property
            def two_digit_base_year(self) -> int | None:
                return None

            def as_dict(self) -> dict[str, Any]:
                return {"year": self.year}

        contract = _NoneYear()
        assert isinstance(contract, Contract)
        assert contract.year is None

    @pytest.mark.unit
    def test_contract_has_output_format_property(self) -> None:
        """Contract protocol defines output_format property."""
        assert hasattr(Contract, "output_format")

    @pytest.mark.unit
    def test_contract_has_two_digit_base_year_property(self) -> None:
        """Contract protocol defines two_digit_base_year property."""
        assert hasattr(Contract, "two_digit_base_year")


class TestEmailContractNewParameters:
    """Tests for EmailContract output_format and two_digit_base_year."""

    @pytest.mark.unit
    def test_email_contract_output_format_defaults_to_none(self) -> None:
        """EmailContract.output_format defaults to None."""
        contract = EmailContract()
        assert contract.output_format is None

    @pytest.mark.unit
    def test_email_contract_two_digit_base_year_defaults_to_none(self) -> None:
        """EmailContract.two_digit_base_year defaults to None."""
        contract = EmailContract()
        assert contract.two_digit_base_year is None

    @pytest.mark.unit
    def test_email_contract_with_output_format(self) -> None:
        """EmailContract accepts output_format parameter."""
        contract = EmailContract(output_format="ISO")
        assert contract.output_format == "ISO"

    @pytest.mark.unit
    def test_email_contract_with_two_digit_base_year(self) -> None:
        """EmailContract accepts two_digit_base_year parameter."""
        contract = EmailContract(two_digit_base_year=2000)
        assert contract.two_digit_base_year == 2000

    @pytest.mark.unit
    def test_email_capability_create_contract_with_output_format(self) -> None:
        """EmailCapability.create_contract passes output_format to contract."""
        contract = EmailCapability.create_contract(output_format="ISO")
        assert contract.output_format == "ISO"

    @pytest.mark.unit
    def test_email_capability_create_contract_with_two_digit_base_year(self) -> None:
        """EmailCapability.create_contract passes two_digit_base_year to contract."""
        contract = EmailCapability.create_contract(two_digit_base_year=2000)
        assert contract.two_digit_base_year == 2000
