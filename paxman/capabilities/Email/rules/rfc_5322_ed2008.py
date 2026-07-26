"""RFC 5322 addr-spec rule — placeholder for Task 9."""

from __future__ import annotations

from paxman.core.domain import (
    Notation,
    Provenance,
    Rule,
    RuleStrategy,
)


PUBLICATION = Provenance(
    authority="IETF",
    specification_name="RFC 5322",
    kind="specification",
    reference_url="https://tools.ietf.org/html/rfc5322",
    version="2008",
    lifecycle="active",
    publication_year=2008,
)


class Section341AddrSpec(Rule):
    """RFC 5322 Section 3.4.1 — addr-spec.

    Placeholder — real implementation in Task 9.
    """

    name = "Section 3.4.1-addr-spec"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "Section 3.4.1 (addr-spec)"

    def matches(self, notation: Notation) -> bool:
        raise NotImplementedError("Task 9 will implement matching")

    def normalize(self, notation: Notation) -> str:
        raise NotImplementedError("Task 9 will implement normalization")
