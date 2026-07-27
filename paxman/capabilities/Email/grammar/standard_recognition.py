"""Standard email recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Email.notation import EmailNotation
from paxman.core.domain import Grammar

_STANDARD_PATTERN = re.compile(
    r"\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


class StandardEmailGrammar(Grammar[EmailNotation]):
    """Standard email recognition: user@domain.tld."""

    name = "standard_recognition"

    def recognize(self, text: str) -> list[EmailNotation]:
        matches = _STANDARD_PATTERN.findall(text)
        return [
            EmailNotation(
                local_part=match.split("@")[0],
                domain_part=match.split("@")[1],
            )
            for match in matches
        ]
