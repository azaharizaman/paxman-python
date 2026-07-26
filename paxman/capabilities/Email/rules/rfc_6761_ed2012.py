"""RFC 6761 localhost rule — localhost email validation."""

from __future__ import annotations

from paxman.core.domain import (
    Notation,
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


class Section63localhost(Rule):
    """RFC 6761 Section 6.3 — localhost.

    Validates email addresses with localhost as the domain.
    Per RFC 6761, "localhost" is a special-use domain name that
    resolves to the loopback interface.
    """

    name = "Section 6.3-localhost"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "Section 6.3 (localhost)"

    def matches(self, notation: Notation) -> bool:
        domain_part = notation[1]
        return domain_part == "localhost"

    def normalize(self, notation: Notation) -> str:
        local_part = notation[0]
        return f"{local_part}@localhost"
