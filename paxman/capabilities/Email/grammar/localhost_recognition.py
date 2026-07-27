"""Localhost email recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Email.notation import EmailNotation
from paxman.core.domain import Grammar

_LOCALHOST_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)@localhost(?::\d+)?(?![\w:.])",
    re.IGNORECASE,
)


class LocalhostEmailGrammar(Grammar[EmailNotation]):
    """Localhost email recognition: user@localhost."""

    name = "localhost_recognition"

    def recognize(self, text: str) -> list[EmailNotation]:
        matches = _LOCALHOST_PATTERN.findall(text)
        return [
            EmailNotation(local_part=match, domain_part="localhost")
            for match in matches
        ]
