"""Capability base class — interface for domain modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, Protocol, runtime_checkable

from paxman.core.capability_contract import CapabilityContract
from paxman.core.domain import Grammar, NotationT, Rule


class Capability(ABC, Generic[NotationT]):
    """Base class for all capabilities.

    Each capability defines a domain module (e.g., Email, Date, Country)
    that registers grammars for recognition and rules for validation.

    The generic parameter ``NotationT`` is the capability's notation type
    (e.g., ``EmailNotation``, ``DateNotation``).  Subclasses declare it
    explicitly::

        class EmailCapability(Capability[EmailNotation]): ...

    This ensures that ``get_grammars()`` and ``get_rules()`` return
    correctly-typed collections, giving compile-time safety that every
    grammar and rule operates on the same notation shape.
    """

    name: str
    version: str

    @abstractmethod
    def get_grammars(self) -> list[Grammar[NotationT]]:
        """Return default grammars for this capability."""
        ...

    @abstractmethod
    def get_rules(self) -> list[Rule[NotationT]]:
        """Return default validation rules for this capability."""
        ...


@runtime_checkable
class ContractFactory(Protocol):
    """Factory protocol for capability contract creation.

    Every capability exposes a ``create_contract`` staticmethod with the
    unanimous common parameter block — ``excluded_rules``, ``pinned_rules``,
    ``year``, ``output_format``, all keyword-only — followed by capability-
    specific parameters.  This protocol makes that common block structural:
    the five capability classes satisfy it by declaring ``create_contract``
    with those parameters (plus their own extras).
    """

    @staticmethod
    def create_contract(
        *,
        excluded_rules: Sequence[str] | None = None,
        pinned_rules: Sequence[str] | None = None,
        year: int | None = None,
        output_format: str | None = None,
    ) -> CapabilityContract:
        """Create a configured contract with the unanimous common block."""
        ...
