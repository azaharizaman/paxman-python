"""RFC 5322 addr-spec rule — standard email validation."""

from __future__ import annotations

import re

from paxman.capabilities.Email.notation import EmailNotation
from paxman.core.contract import Contract
from paxman.core.domain import (
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

_LOCAL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+$")
_DOMAIN_PATTERN = re.compile(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class Section341AddrSpec(Rule[EmailNotation]):
    """RFC 5322 Section 3.4.1 — addr-spec."""

    name = "Section 3.4.1-addr-spec"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "Section 3.4.1 (addr-spec)"

    def matches(self, notation: EmailNotation, contract: Contract) -> bool:
        return bool(
            _LOCAL_PATTERN.match(notation.local_part)
            and _DOMAIN_PATTERN.match(notation.domain_part)
        )

    def normalize(self, notation: EmailNotation, contract: Contract) -> str:
        return f"{notation.local_part.lower()}@{notation.domain_part.lower()}"
