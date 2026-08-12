"""ISBN-10 recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.ISBN.notation import ISBNNotation
from paxman.core.domain import Grammar, RecognitionMatch

_ISBN10_PATTERN = re.compile(
    r"(?<!\d)(?<!\d[ -])(?:ISBN(?:-10)?[\s:-]+)?"
    r"(?=((?:\d[ -]?){9}[0-9Xx])(?![\d]))\1(?<![\s:-])\b",
    re.IGNORECASE,
)


class ISBN10RecognitionGrammar(Grammar[ISBNNotation]):
    """ISBN-10 recognition: 10-digit ISBN with optional label and separators."""

    name = "isbn10_recognition"
    semantics = "isbn10_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[ISBNNotation]]:
        matches: list[RecognitionMatch[ISBNNotation]] = []
        for m in _ISBN10_PATTERN.finditer(text):
            digits = "".join(ch for ch in m.group(1) if ch in "0123456789Xx").upper()
            if len(digits) != 10:
                continue
            matches.append(
                RecognitionMatch(
                    notation=ISBNNotation(
                        shape="isbn10",
                        digits=digits,
                    ),
                    start=m.start(),
                    end=m.end(),
                    raw_text=m.group(0),
                )
            )
        return matches
