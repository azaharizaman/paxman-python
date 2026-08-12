"""RFC 791 IPv4 address rule — validates and normalizes dotted-decimal IPv4."""

from __future__ import annotations

import ipaddress

from paxman.capabilities.IP.notation import IPNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="IETF",
    specification_name="RFC 791",
    kind="specification",
    reference_url="https://tools.ietf.org/html/rfc791",
    version="1981",
    lifecycle="active",
    publication_year=1981,
)


class Section3Dot2IPv4Address(Rule[IPNotation]):
    """RFC 791 Section 3.2 — Internet Addressing.

    Validates IPv4 addresses and normalizes to canonical dotted-decimal
    form without leading zeros.
    """

    name = "Section 3.2-ipv4-address"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 3.2 (internet addressing)"
    target_semantics = frozenset({"ipv4_recognition"})
    requires_features = frozenset()

    @staticmethod
    def _strip_leading_zeros(address: str) -> str:
        """Strip leading zeros from each octet."""
        octets = address.split(".")
        return ".".join(str(int(o)) for o in octets)

    def matches(self, notation: IPNotation, contract: Contract) -> bool:
        """Check if the address is a valid IPv4 address."""
        try:
            normalized = self._strip_leading_zeros(notation.address)
            addr = ipaddress.IPv4Address(normalized)
            return addr.version == 4
        except (ValueError, IndexError):
            return False

    def normalize(self, notation: IPNotation, contract: Contract) -> str:
        """Normalize to canonical dotted-decimal without leading zeros."""
        normalized = self._strip_leading_zeros(notation.address)
        addr = ipaddress.IPv4Address(normalized)
        return str(addr)
