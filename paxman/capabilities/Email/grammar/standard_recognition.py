"""Standard email recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Email.notation import EmailNotation
from paxman.core.domain import Grammar, RecognitionMatch

_STANDARD_PATTERN = re.compile(
    r"\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


class StandardEmailGrammar(Grammar[EmailNotation]):
    """Standard email recognition: user@domain.tld."""

    name = "standard_recognition"
    semantics = "rfc5322_addr_spec"

    def recognize(self, text: str) -> list[RecognitionMatch[EmailNotation]]:
        matches: list[RecognitionMatch[EmailNotation]] = []
        for match in _STANDARD_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(0).split("@")[0],
                        domain_part=match.group(0).split("@")[1],
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
