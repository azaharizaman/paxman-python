"""IPv6 recognition grammar — extracts IPv6 addresses in various formats."""

from __future__ import annotations

import re

from paxman.capabilities.IP.notation import IPNotation
from paxman.core.domain import Grammar, RecognitionMatch

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

    def recognize(self, text: str) -> list[RecognitionMatch[IPNotation]]:
        """Extract IPv6 address patterns from text.

        The full and compressed patterns are structurally disjoint, so every
        match emits a span-bearing RecognitionMatch; the engine dedups
        contained spans and identical candidate values collapse at the
        candidate stage.
        """
        matches: list[RecognitionMatch[IPNotation]] = []
        for match in _IPV6_FULL.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=IPNotation(address=match.group(1)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(1),
                )
            )
        for match in _IPV6_COMPRESSED.finditer(text):
            # Boundary assertions are zero-width and each alternation branch
            # has one capture group, so the full match text IS the address.
            matches.append(
                RecognitionMatch(
                    notation=IPNotation(address=match.group(0)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
