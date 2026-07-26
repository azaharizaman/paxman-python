"""Email canonicalization capability."""

from __future__ import annotations

from dataclasses import dataclass

from paxman.capabilities.Email.grammar.standard_recognition import (
    StandardEmailGrammar,
)
from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule


@dataclass(frozen=True)
class EmailNotation:
    """Email notation: local_part and domain_part."""

    local_part: str
    domain_part: str

    def as_list(self) -> list[str]:
        """Convert to list[str] for generic Rule interface."""
        return [self.local_part, self.domain_part]


class EmailCapability(Capability):
    """Email canonicalization capability."""

    name = "email"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar]:
        return [StandardEmailGrammar()]

    def get_rules(self) -> list[Rule]:
        return [Section341AddrSpec()]
