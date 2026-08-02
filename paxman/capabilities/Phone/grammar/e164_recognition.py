"""E.164 international number recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Phone.grammar.common import dedup, strip_separators
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# A "+" followed by digits with optional separators (space, dash, dot, parens).
# The grammar is intentionally loose — validation happens in rules. The
# negative lookbehind excludes word characters (letters, digits, underscore),
# ":" and "." — so email plus-tags ("user+123@"), algebra ("x+11"), decimals
# (".+1.5"), and "tel:+..." (which the tel-URI grammar handles) are NOT
# double-matched. The trailing (?<=\d) lookbehind forces the match to end on
# a digit, so the trailing character class cannot swallow separators,
# whitespace, or sentence punctuation after the number.
_E164_PATTERN = re.compile(r"(?<![\w:.])\+\d[\d\s().\-]*(?<=\d)")


class E164Grammar(Grammar[PhoneNotation]):
    """Recognizes E.164-style international numbers (leading +).

    Examples: "+15551234567", "+1 555 123 4567", "+44-20-7946-0958"
    Non-examples: "15551234567" (no +), "(555) 123-4567" (national format)
    """

    name = "e164_recognition"

    def recognize(self, text: str) -> list[PhoneNotation]:
        """Extract e164 patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of PhoneNotations with shape="e164" and value set to the
            digit-only number (leading "+" and separators removed).
        """
        return dedup(
            PhoneNotation(
                shape="e164", value=strip_separators(match.group(0), plus=True)
            )
            for match in _E164_PATTERN.finditer(text)
        )
