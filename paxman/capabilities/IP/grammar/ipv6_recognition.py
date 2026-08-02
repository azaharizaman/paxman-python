"""IPv6 recognition grammar — extracts IPv6 addresses in various formats."""

from __future__ import annotations

import re

from paxman.capabilities.IP.notation import IPNotation
from paxman.core.domain import Grammar

# Boundary: start/end of string, whitespace, or common punctuation
_IPV6_BOUNDARY = r"(?:^|(?<=[\s,;([ ]))"
_IPV6_END = r"(?:$|(?=[\s,;().\]]))"

# Full form: 8 groups of 1-4 hex digits separated by single colons
_IPV6_FULL = re.compile(
    _IPV6_BOUNDARY + r"([0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){7})" + _IPV6_END
)

# Compressed form: handles :: with groups on either side
_IPV6_COMPRESSED = re.compile(
    _IPV6_BOUNDARY
    + r"((?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{0,4}::"
    + r"(?:[0-9a-fA-F]{0,4}:){0,6}[0-9a-fA-F]{1,4})"
    + _IPV6_END
    + "|"
    + _IPV6_BOUNDARY
    + r"(::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4})"
    + _IPV6_END
    + "|"
    + _IPV6_BOUNDARY
    + r"((?:[0-9a-fA-F]{1,4}:){1,6}[0-9a-fA-F]{0,4}::)"
    + _IPV6_END
    + "|"
    + _IPV6_BOUNDARY
    + r"(::)"
    + _IPV6_END
)


class IPv6Grammar(Grammar[IPNotation]):
    """IPv6 recognition: full and compressed formats.

    Handles:
    - Full form: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
    - Compressed: 2001:db8:85a3::8a2e:370:7334
    - Loopback: ::1
    - Link-local: fe80::1
    - All-zeros: ::
    """

    name = "ipv6_recognition"

    def recognize(self, text: str) -> list[IPNotation]:
        """Extract IPv6 address patterns from text."""
        seen: set[str] = set()
        results: list[IPNotation] = []

        # Try full form first (8 groups)
        for match in _IPV6_FULL.finditer(text):
            addr = match.group(1)
            if addr not in seen:
                seen.add(addr)
                results.append(IPNotation(address=addr))

        # Try compressed forms
        for match in _IPV6_COMPRESSED.finditer(text):
            for group in match.groups():
                if group is not None and group not in seen:
                    seen.add(group)
                    results.append(IPNotation(address=group))

        return results
