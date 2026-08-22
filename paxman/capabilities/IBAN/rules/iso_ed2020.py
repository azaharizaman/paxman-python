"""IBAN rule — scaffolded placeholder (publication: ISO).

TODO(scaffold): implement matches()/normalize() against your authority.
"""

from __future__ import annotations

from paxman.capabilities.IBAN.notation import IBANNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 13616-1:2020",
    kind="specification",
    reference_url="https://www.iso.org/standard/81090.html",
    version=None,  # TODO(scaffold): set when --spec-version is provided
    lifecycle="active",
    publication_year=2020,
)


class IBANRule(Rule[IBANNotation]):
    """Placeholder validation rule for IBAN.

    TODO(scaffold): rename to the real Section {X.Y.Z}-{description}; implement
    matches()/normalize() against your authority.
    """

    name = "Section 1-overview"  # TODO(scaffold): Section {X.Y.Z}-{description}
    strategy = RuleStrategy.REGEX  # TODO(scaffold): match strategy to representation
    provenance = PUBLICATION
    citation = "Section TODO"  # TODO(scaffold): real citation
    target_semantics = frozenset({"iban_recognition"})
    requires_features = frozenset()

    def matches(self, notation: IBANNotation, contract: Contract) -> bool:
        """TODO(scaffold): return True when notation is valid per authority."""
        return True

    def normalize(self, notation: IBANNotation, contract: Contract) -> str:
        """TODO(scaffold): return the canonical form of notation.value."""
        return notation.value
