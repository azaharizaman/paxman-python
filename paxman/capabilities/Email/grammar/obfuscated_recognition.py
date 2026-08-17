"""Obfuscated email recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Email.notation import EmailNotation
from paxman.core.domain import Grammar, RecognitionMatch

# Matches: "user at domain dot tld"
_OBFUSCATED_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)\s+at\s+([A-Za-z0-9.-]+)\s+dot\s+([A-Za-z]{2,})\b"
)
# Matches: "user at domain.tld"
_AT_ONLY_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)\s+at\s+([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)


class ObfuscatedEmailGrammar(Grammar[EmailNotation]):
    """Obfuscated email: 'user at domain dot tld' or 'user at domain.tld'."""

    name = "obfuscated_recognition"
    semantics = "rfc5322_addr_spec"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[EmailNotation]]:
        """Extract obfuscated email patterns from text.

        Both patterns emit span-bearing matches; the engine merges, orders
        (document order), and dedups contained matches, and identical
        candidate values collapse at the candidate stage. The grammar does
        not de-duplicate.
        """
        matches: list[RecognitionMatch[EmailNotation]] = []
        for match in _OBFUSCATED_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(1),
                        domain_part=f"{match.group(2)}.{match.group(3)}",
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        for match in _AT_ONLY_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(1),
                        domain_part=match.group(2),
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
