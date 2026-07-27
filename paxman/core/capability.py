"""Capability base class — interface for domain modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

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
