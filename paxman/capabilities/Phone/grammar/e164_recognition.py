"""E.164 international number recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Phone.grammar.common import strip_separators
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar, RecognitionMatch

# A "+" followed by digits with optional separators (space, dash, dot, parens).
# The grammar is intentionally loose — validation happens in rules. The
# negative lookbehind excludes word characters (letters, digits, underscore),
# ":" and "." — so email plus-tags ("user+123@"), algebra ("x+11"), decimals
# (".+1.5"), and "tel:+..." (which the tel-URI grammar handles) are NOT
# double-matched. The trailing (?<=\d) lookbehind forces the match to end on
# a digit, so the trailing character class cannot swallow separators,
# whitespace, or sentence punctuation after the number.
_E164_PATTERN = re.compile(r"(?<![\w:.])\+\d[\d\s().\-]*(?<=\d)")

# Maximum E.164 number length in digits (spec limit; the grammar trims
# runaway matches at this boundary). Duplicated from the rule module on
# purpose: the semantic-purity gate forbids grammar -> rules imports, so
# each side keeps its own copy. Keep in sync with
# rules/e164_ed2010.py:_MAX_E164_DIGITS.
_MAX_E164_DIGITS = 15


def _trim_to_e164_boundary(raw: str) -> str:
    """Trim a runaway raw match at the last digit-run group within the limit.

    ``_E164_PATTERN``'s trailing character class consumes separators AND
    following digit runs, so "+15551234567 5551234567" is captured as one raw
    span. The raw match is trimmed back to the last complete digit-run group
    whose inclusion keeps the total digit count at or below
    ``_MAX_E164_DIGITS`` (15), so a legitimate following number is not
    swallowed into the match. If the first run alone exceeds the limit, the
    raw match is kept whole: validation then rejects the oversized value
    instead of silently recognizing a truncated 15-digit prefix.
    """
    runs = list(re.finditer(r"\d+", raw))
    total = 0
    for index, run in enumerate(runs):
        total += len(run.group(0))
        if total > _MAX_E164_DIGITS:
            if index == 0:
                return raw
            return raw[: runs[index - 1].end()]
    return raw


class E164Grammar(Grammar[PhoneNotation]):
    """Recognizes E.164-style international numbers (leading +).

    Examples: "+15551234567", "+1 555 123 4567", "+44-20-7946-0958"
    Non-examples: "15551234567" (no +), "(555) 123-4567" (national format)
    """

    name = "e164_recognition"
    semantics = "e164_international"

    def recognize(self, text: str) -> list[RecognitionMatch[PhoneNotation]]:
        """Extract e164 patterns from text.

        Returns:
            List of RecognitionMatches; notation.value is the digit-only
            number (leading "+" and separators removed).
        """
        matches: list[RecognitionMatch[PhoneNotation]] = []
        for match in _E164_PATTERN.finditer(text):
            raw_text = _trim_to_e164_boundary(match.group(0))
            matches.append(
                RecognitionMatch(
                    notation=PhoneNotation(
                        shape="e164",
                        value=strip_separators(raw_text, plus=True),
                    ),
                    start=match.start(),
                    end=match.start() + len(raw_text),
                    raw_text=raw_text,
                )
            )
        return matches
