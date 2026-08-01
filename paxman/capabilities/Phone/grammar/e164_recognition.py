"""E.164 international number recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# A "+" followed by digits with optional separators (space, dash, dot, parens).
# The grammar is intentionally loose — validation happens in rules. The
# negative lookbehind excludes both digits and ":" so tel: URIs are NOT
# double-matched by this grammar (RFC 3966 handles those).
_E164_PATTERN = re.compile(r"(?<![\d:])\+\d[\d\s().\-]*")

_ALLOWED_SEPARATORS = str.maketrans("", "", "+ ().-")


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
        results: list[PhoneNotation] = []
        seen: set[tuple[str, ...]] = set()
        for match in _E164_PATTERN.finditer(text):
            digits = match.group(0).translate(_ALLOWED_SEPARATORS)
            notation = PhoneNotation(shape="e164", value=digits)
            key = tuple(notation.as_list())
            if key not in seen:
                seen.add(key)
                results.append(notation)
        return results
