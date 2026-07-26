"""Localhost email recognition grammar."""

from __future__ import annotations

import re

from paxman.core.domain import Grammar, Notation

_LOCALHOST_PATTERN = re.compile(r"\b([A-Za-z0-9._%+-]+)@localhost(?::\d+)?\b")


class LocalhostEmailGrammar(Grammar):
    """Localhost email recognition: user@localhost."""

    name = "localhost_recognition"

    def recognize(self, text: str) -> list[Notation]:
        matches = _LOCALHOST_PATTERN.findall(text)
        return [[match, "localhost"] for match in matches]
