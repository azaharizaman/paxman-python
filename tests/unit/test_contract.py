from __future__ import annotations

from typing import Any

import pytest

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

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_name": self.capability_name,
            "active_grammars": self.active_grammars,
            "excluded_rules": self.excluded_rules,
            "year": self.year,
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

            def as_dict(self) -> dict[str, Any]:
                return {"year": self.year}

        contract = _NoneYear()
        assert isinstance(contract, Contract)
        assert contract.year is None
