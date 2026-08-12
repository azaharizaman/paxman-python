"""ISBN-13 recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.ISBN.notation import ISBNNotation
from paxman.core.domain import Grammar, RecognitionMatch

_ISBN13_PATTERN = re.compile(
    r"\b(?:ISBN(?:-13)?[\s:-]+)?(?=((?:\d[ -]?){12}\d)(?![\d]))\1(?<![\s:-])\b",
    re.IGNORECASE,
)


class ISBN13RecognitionGrammar(Grammar[ISBNNotation]):
    """ISBN-13 recognition: 13-digit ISBN with optional label and separators."""

    name = "isbn13_recognition"
    semantics = "isbn13_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[ISBNNotation]]:
        matches: list[RecognitionMatch[ISBNNotation]] = []
        for m in _ISBN13_PATTERN.finditer(text):
            digits = "".join(ch for ch in m.group(1) if ch in "0123456789")
            if len(digits) != 13:
                continue
            matches.append(
                RecognitionMatch(
                    notation=ISBNNotation(
                        shape="isbn13",
                        digits=digits,
                    ),
                    start=m.start(),
                    end=m.end(),
                    raw_text=m.group(0),
                )
            )
        return matches
