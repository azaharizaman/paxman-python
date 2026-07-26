"""Email canonicalization capability."""

from __future__ import annotations

from dataclasses import dataclass, field

from paxman.capabilities.Email.grammar.localhost_recognition import (
    LocalhostEmailGrammar,
)
from paxman.capabilities.Email.grammar.obfuscated_recognition import (
    ObfuscatedEmailGrammar,
)
from paxman.capabilities.Email.grammar.standard_recognition import (
    StandardEmailGrammar,
)
from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec
from paxman.capabilities.Email.rules.rfc_6761_ed2012 import Section63localhost
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
        return [
            StandardEmailGrammar(),
            ObfuscatedEmailGrammar(),
            LocalhostEmailGrammar(),
        ]

    def get_rules(self) -> list[Rule]:
        return [
            Section341AddrSpec(),
            Section63localhost(),
        ]


@dataclass(frozen=True)
class EmailContract:
    """User-facing contract for Email capability."""

    capability_name: str = field(default="email", init=False)
    include_obfuscated: bool = False
    include_localhost: bool = True
    excluded_rules: list[str] = field(default_factory=lambda: [])
    year: int | None = None

    @property
    def active_grammars(self) -> list[str]:
        grammars = ["standard_recognition"]
        if self.include_obfuscated:
            grammars.append("obfuscated_recognition")
        if self.include_localhost:
            grammars.append("localhost_recognition")
        return grammars

    def as_dict(self) -> dict[str, object]:
        return {
            "capability_name": self.capability_name,
            "include_obfuscated": self.include_obfuscated,
            "include_localhost": self.include_localhost,
            "excluded_rules": self.excluded_rules,
            "year": self.year,
        }


def _create_contract(
    include_obfuscated: bool = False,
    include_localhost: bool = True,
    excluded_rules: list[str] | None = None,
    year: int | None = None,
) -> EmailContract:
    return EmailContract(
        include_obfuscated=include_obfuscated,
        include_localhost=include_localhost,
        excluded_rules=excluded_rules or [],
        year=year,
    )


EmailCapability.create_contract = staticmethod(_create_contract)  # type: ignore[attr-defined]
