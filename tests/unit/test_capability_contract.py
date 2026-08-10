"""Tests for the CapabilityContract base class and ContractFactory protocol.

``CapabilityContract`` is the unanimous base that every capability contract
must inherit from, and ``ContractFactory`` is the protocol that every
capability's ``create_contract`` staticmethod must satisfy.  Together they
make the homogeneous contract surface structural rather than documentary.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import FrozenInstanceError, dataclass, field
from typing import ClassVar

import pytest

import paxman.core.contract as contract_module
from paxman.capabilities.Email.capability import EmailCapability
from paxman.core.capability import ContractFactory
from paxman.core.capability_contract import CapabilityContract
from paxman.core.contract import Contract
from paxman.core.errors import ContractError


@dataclass(frozen=True)
class _TestContract(CapabilityContract):
    """Minimal concrete CapabilityContract subclass for tests.

    Decorated like the real capability contracts (which are frozen dataclasses
    that inherit ``CapabilityContract``).
    """

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "test"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset({"alt"})

    capability_name: str = field(default="test", init=False)

    @property
    def active_grammars(self) -> Sequence[str]:
        return []


@dataclass(frozen=True)
class _MissingActiveGrammars(CapabilityContract):
    """Subclass that forgets the abstract ``active_grammars`` property."""

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "test"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset({"alt"})

    capability_name: str = field(default="test", init=False)


class _Factory:
    """A class satisfying the ContractFactory protocol."""

    @staticmethod
    def create_contract(
        *,
        excluded_rules: Sequence[str] | None = None,
        pinned_rules: Sequence[str] | None = None,
        year: int | None = None,
        output_format: str | None = None,
    ) -> _TestContract:
        return _TestContract(
            excluded_rules=tuple(excluded_rules) if excluded_rules else (),
            pinned_rules=tuple(pinned_rules) if pinned_rules is not None else None,
            year=year,
            output_format=output_format,
        )


class TestCapabilityContract:
    @pytest.mark.unit
    def test_output_format_none_resolves_to_default(self) -> None:
        """None is equivalent to the capability's DEFAULT_OUTPUT_FORMAT."""
        contract = _TestContract()
        assert contract.output_format == "test"

    @pytest.mark.unit
    def test_output_format_default_keyword_resolves_to_default(self) -> None:
        """'default' reverts to the capability's DEFAULT_OUTPUT_FORMAT."""
        contract = _TestContract(output_format="default")
        assert contract.output_format == "test"

    @pytest.mark.unit
    def test_output_format_default_format_string_resolves_to_default(self) -> None:
        """The DEFAULT_OUTPUT_FORMAT string itself is accepted."""
        contract = _TestContract(output_format="test")
        assert contract.output_format == "test"

    @pytest.mark.unit
    def test_output_format_offered_alternative_is_kept(self) -> None:
        """An offered alternative resolves to itself."""
        contract = _TestContract(output_format="alt")
        assert contract.output_format == "alt"

    @pytest.mark.unit
    @pytest.mark.parametrize("fmt", ["", "none", "None", "nope", "TEST", "alt "])
    def test_output_format_invalid_raises_contract_error(self, fmt: str) -> None:
        """Unoffered output_format values raise ContractError at construction."""
        with pytest.raises(ContractError):
            _TestContract(output_format=fmt)

    @pytest.mark.unit
    def test_output_format_non_string_raises_contract_error(self) -> None:
        """Non-string output_format values raise ContractError."""
        with pytest.raises(ContractError):
            _TestContract(output_format=123)

    @pytest.mark.unit
    def test_base_class_exposes_no_as_dict_method(self) -> None:
        """The base class no longer exposes the as_dict() serialization method."""
        assert not hasattr(_TestContract(), "as_dict")

    @pytest.mark.unit
    def test_active_grammars_is_abstract(self) -> None:
        """CapabilityContract cannot be instantiated without active_grammars."""
        with pytest.raises(TypeError):
            _MissingActiveGrammars()

    @pytest.mark.unit
    def test_instance_satisfies_contract_protocol(self) -> None:
        """CapabilityContract instances satisfy the Contract protocol."""
        assert isinstance(_TestContract(), Contract)

    @pytest.mark.unit
    def test_capability_contract_reexported_from_contract_module(self) -> None:
        """paxman.core.contract re-exports CapabilityContract."""
        assert contract_module.CapabilityContract is CapabilityContract

    @pytest.mark.unit
    def test_frozen_dataclass_rejects_assignment(self) -> None:
        """CapabilityContract is a frozen dataclass."""
        contract = _TestContract()
        with pytest.raises(FrozenInstanceError):
            contract.excluded_rules = ("x",)


class TestContractFactory:
    @pytest.mark.unit
    def test_class_with_staticmethod_create_contract_passes(self) -> None:
        """A class with a matching create_contract staticmethod satisfies it."""
        assert isinstance(_Factory, ContractFactory)

    @pytest.mark.unit
    def test_class_without_create_contract_fails(self) -> None:
        """A class without create_contract does not satisfy it."""

        class _NoFactory:
            pass

        assert not isinstance(_NoFactory, ContractFactory)

    @pytest.mark.unit
    def test_contract_class_without_create_contract_fails(self) -> None:
        """A contract class (no create_contract) does not satisfy it."""
        assert not isinstance(_TestContract, ContractFactory)

    @pytest.mark.unit
    def test_email_capability_satisfies_contract_factory(self) -> None:
        """EmailCapability's create_contract staticmethod satisfies the protocol."""
        assert isinstance(EmailCapability, ContractFactory)
