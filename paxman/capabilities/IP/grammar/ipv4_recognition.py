"""IPv4 recognition grammar — extracts dotted-decimal IPv4 addresses."""

from __future__ import annotations

import re

from paxman.capabilities.IP.notation import IPNotation
from paxman.core.domain import Grammar, RecognitionMatch

_IPV4_PATTERN = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b")


class IPv4Grammar(Grammar[IPNotation]):
    """IPv4 recognition: dotted-decimal format (e.g., 192.168.1.1)."""

    name = "ipv4_recognition"
    semantics = "ipv4_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[IPNotation]]:
        """Extract IPv4 dotted-decimal patterns from text."""
        matches: list[RecognitionMatch[IPNotation]] = []
        for match in _IPV4_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=IPNotation(address=match.group(0)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
