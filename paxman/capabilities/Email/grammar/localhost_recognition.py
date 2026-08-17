"""Localhost email recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Email.notation import EmailNotation
from paxman.core.domain import Grammar, RecognitionMatch

_LOCALHOST_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)@localhost(?::\d+)?(?:(?=[\s,;()]|$)|\.(?=\s|$))",
    re.IGNORECASE,
)


class LocalhostEmailGrammar(Grammar[EmailNotation]):
    """Localhost email recognition: user@localhost."""

    name = "localhost_recognition"
    semantics = "localhost_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[EmailNotation]]:
        matches: list[RecognitionMatch[EmailNotation]] = []
        for match in _LOCALHOST_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(1), domain_part="localhost"
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
