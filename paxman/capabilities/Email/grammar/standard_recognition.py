"""Standard email recognition grammar — placeholder for Task 8."""

from __future__ import annotations

from paxman.core.domain import Grammar, Notation


class StandardEmailGrammar(Grammar):
    """Standard email recognition: user@domain.tld.

    Placeholder — real implementation in Task 8.
    """

    name = "standard_recognition"

    def recognize(self, text: str) -> list[Notation]:
        raise NotImplementedError("Task 8 will implement recognition")
