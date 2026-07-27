"""IPv4 recognition grammar — extracts dotted-decimal IPv4 addresses."""

from __future__ import annotations

import re

from paxman.capabilities.IP.notation import IPNotation
from paxman.core.domain import Grammar

_IPV4_PATTERN = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b")


class IPv4Grammar(Grammar[IPNotation]):
    """IPv4 recognition: dotted-decimal format (e.g., 192.168.1.1)."""

    name = "ipv4_recognition"

    def recognize(self, text: str) -> list[IPNotation]:
        """Extract IPv4 dotted-decimal patterns from text."""
        return [
            IPNotation(address=f"{a}.{b}.{c}.{d}")
            for a, b, c, d in _IPV4_PATTERN.findall(text)
        ]
