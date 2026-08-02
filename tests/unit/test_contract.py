from __future__ import annotations

from typing import Any

import pytest

from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.Email.contract import EmailContract
from paxman.core.contract import Contract
from paxman.core.errors import ContractError


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
    def pinned_rules(self) -> list[str] | None:
        return None

    @property
    def year(self) -> int | None:
        return 2024

    @property
    def output_format(self) -> str | None:
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_name": self.capability_name,
            "active_grammars": self.active_grammars,
            "excluded_rules": self.excluded_rules,
            "pinned_rules": self.pinned_rules,
            "year": self.year,
            "output_format": self.output_format,
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
    def pinned_rules(self) -> list[str] | None:
        return None

    @property
    def year(self) -> int | None:
        return None

    @property
    def output_format(self) -> str | None:
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
    def pinned_rules(self) -> list[str] | None:
        return None

    @property
    def year(self) -> int | None:
        return None

    @property
    def output_format(self) -> str | None:
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
            "pinned_rules",
            "year",
            "output_format",
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
            def pinned_rules(self) -> list[str] | None:
                return None

            @property
            def year(self) -> int | None:
                return None

            @property
            def output_format(self) -> str | None:
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


class TestEmailContractNewParameters:
    """Tests for EmailContract output_format."""

    @pytest.mark.unit
    def test_email_contract_output_format_defaults_to_email(self) -> None:
        """EmailContract.output_format resolves to the concrete default 'email'."""
        contract = EmailContract()
        assert contract.output_format == "email"

    @pytest.mark.unit
    def test_email_contract_output_format_default(self) -> None:
        """'default' resolves to 'email' — Email's single canonical form."""
        contract = EmailContract(output_format="default")
        assert contract.output_format == "email"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "fmt", ["ISO", "US", "e164", "rfc3966", "alpha2", "none", ""]
    )
    def test_email_contract_invalid_output_format_raises(self, fmt: str) -> None:
        """Unoffered output_format values raise ContractError."""
        with pytest.raises(ContractError):
            EmailContract(output_format=fmt)

    @pytest.mark.unit
    def test_email_contract_accepts_default_format_string(self) -> None:
        """The default format string 'email' is accepted and equivalent to default."""
        contract = EmailContract(output_format="email")
        assert contract.output_format == "email"

    @pytest.mark.unit
    def test_email_capability_create_contract_with_output_format_default(
        self,
    ) -> None:
        """EmailCapability.create_contract('default') resolves to 'email'."""
        contract = EmailCapability.create_contract(output_format="default")
        assert contract.output_format == "email"

    @pytest.mark.unit
    def test_email_capability_create_contract_invalid_output_format_raises(
        self,
    ) -> None:
        """EmailCapability.create_contract rejects unoffered output_format."""
        with pytest.raises(ContractError):
            EmailCapability.create_contract(output_format="ISO")
