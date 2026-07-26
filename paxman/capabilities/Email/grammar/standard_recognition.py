"""Standard email recognition grammar."""

from __future__ import annotations

import re

from paxman.core.domain import Grammar, Notation

_STANDARD_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


class StandardEmailGrammar(Grammar):
    """Standard email recognition: user@domain.tld."""

    name = "standard_recognition"

    def recognize(self, text: str) -> list[Notation]:
        matches = _STANDARD_PATTERN.findall(text)
        return [match.split("@") for match in matches]
