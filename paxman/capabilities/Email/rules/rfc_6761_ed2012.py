"""RFC 6761 localhost rule — localhost email validation."""

from __future__ import annotations

from paxman.capabilities.Email.notation import EmailNotation
from paxman.core.contract import Contract
from paxman.core.domain import (
    Provenance,
    Rule,
    RuleStrategy,
)

PUBLICATION = Provenance(
    authority="IETF",
    specification_name="RFC 6761",
    kind="specification",
    reference_url="https://tools.ietf.org/html/rfc6761",
    version="2012",
    lifecycle="active",
    publication_year=2012,
)


class Section63localhost(Rule[EmailNotation]):
    """RFC 6761 Section 6.3 — localhost.

    Validates email addresses with localhost as the domain.
    Per RFC 6761, "localhost" is a special-use domain name that
    resolves to the loopback interface.
    """

    name = "Section 6.3-localhost"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "Section 6.3 (localhost)"

    def matches(self, notation: EmailNotation, contract: Contract) -> bool:
        return notation.domain_part == "localhost"

    def normalize(self, notation: EmailNotation, contract: Contract) -> str:
        return f"{notation.local_part}@localhost"
