"""RFC 5952 IPv6 text representation rule — validates and normalizes IPv6."""

from __future__ import annotations

import ipaddress

from paxman.capabilities.IP.notation import IPNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="IETF",
    specification_name="RFC 5952",
    kind="specification",
    reference_url="https://tools.ietf.org/html/rfc5952",
    version="2010",
    lifecycle="active",
    publication_year=2010,
)


class Section4IPv6TextRepresentation(Rule[IPNotation]):
    """RFC 5952 Section 4 — A Recommendation for IPv6 Text Representation.

    Validates IPv6 addresses and normalizes to the recommended compressed
    form: lowercase hex, :: for the longest zero run, no leading zeros
    except for the :: itself.
    """

    name = "Section 4-ipv6-text-representation"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 4 (IPv6 text representation)"

    def matches(self, notation: IPNotation, contract: Contract) -> bool:
        """Check if the address is a valid IPv6 address."""
        try:
            addr = ipaddress.IPv6Address(notation.address)
            return addr.version == 6
        except ValueError:
            return False

    def normalize(self, notation: IPNotation, contract: Contract) -> str:
        """Normalize to RFC 5952 recommended compressed form.

        The ipaddress module's str() output follows RFC 5952:
        - Lowercase hex digits
        - :: for the longest run of consecutive zeros
        - No leading zeros in groups
        """
        addr = ipaddress.IPv6Address(notation.address)
        return str(addr)
