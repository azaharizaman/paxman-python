"""Obfuscated email recognition grammar."""

from __future__ import annotations

import re

from paxman.core.domain import Grammar, Notation

# Matches: "user at domain dot tld"
_OBFUSCATED_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)\s+at\s+([A-Za-z0-9.-]+)\s+dot\s+([A-Za-z]{2,})\b"
)
# Matches: "user at domain.tld"
_AT_ONLY_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)\s+at\s+([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)


class ObfuscatedEmailGrammar(Grammar):
    """Obfuscated email recognition: 'user at domain dot tld' or 'user at domain.tld'."""

    name = "obfuscated_recognition"

    def recognize(self, text: str) -> list[Notation]:
        results: list[Notation] = []

        # Try "at ... dot ..." format first
        for match in _OBFUSCATED_PATTERN.finditer(text):
            local_part = match.group(1)
            domain = f"{match.group(2)}.{match.group(3)}"
            results.append([local_part, domain])

        # Try "at domain.tld" format (no "dot")
        for match in _AT_ONLY_PATTERN.finditer(text):
            local_part = match.group(1)
            domain = match.group(2)
            notation: Notation = [local_part, domain]
            # Avoid duplicates from the dot pattern
            if notation not in results:
                results.append(notation)

        return results
