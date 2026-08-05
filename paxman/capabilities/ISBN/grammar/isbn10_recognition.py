"""ISBN-10 recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.ISBN.notation import ISBNNotation
from paxman.core.domain import Grammar, RecognitionMatch

_ISBN10_PATTERN = re.compile(
    r"\b(?:ISBN(?:-10)?[\s:-]+)?(?=((?:\d[ -]?){9}[0-9Xx])(?![\d]))\1(?<![\s:-])\b",
    re.IGNORECASE,
)


class ISBN10RecognitionGrammar(Grammar[ISBNNotation]):
    """ISBN-10 recognition: 10-digit ISBN with optional label and separators."""

    name = "isbn10_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[ISBNNotation]]:
        matches: list[RecognitionMatch[ISBNNotation]] = []
        for m in _ISBN10_PATTERN.finditer(text):
            cleaned = "".join(
                ch for ch in m.group(1) if ch.isdigit() or ch in "xX"
            ).upper()
            if len(cleaned) != 10:
                continue
            matches.append(
                RecognitionMatch(
                    notation=ISBNNotation(
                        shape="isbn10",
                        digits=cleaned,
                    ),
                    start=m.start(),
                    end=m.end(),
                    raw_text=m.group(0),
                )
            )
        return matches
