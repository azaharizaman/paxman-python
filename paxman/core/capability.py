"""Capability base class — interface for domain modules."""

from __future__ import annotations

from abc import ABC, abstractmethod

from paxman.core.domain import Grammar, Rule


class Capability(ABC):
    """Base class for all capabilities.

    Each capability defines a domain module (e.g., Email, Date, Country)
    that registers grammars for recognition and rules for validation.
    """

    name: str
    version: str

    @abstractmethod
    def get_grammars(self) -> list[Grammar]:
        """Return default grammars for this capability."""
        ...

    @abstractmethod
    def get_rules(self) -> list[Rule]:
        """Return default validation rules for this capability."""
        ...
