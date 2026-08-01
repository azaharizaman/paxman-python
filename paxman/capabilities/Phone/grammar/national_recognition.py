"""NANP national number recognition grammar.

Recognizes domestic (NANP-style) dialing formats: optional trunk "1",
optional parenthesized NPA, then 3-3-4 digit groups with any of space,
dash, or dot separators. This grammar is deliberately NANP-shaped for
Milestone 1; future milestones add country-specific national grammars.
"""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# Optional trunk 1, optional (NPA), NXX, XXXX. The NPA first digit 2-9 is a
# recognition heuristic — strict validation happens in the rules. The NXX is
# left loose (`\d{3}`) so common spellings like "555-123-4567" are captured.
# The negative lookbehind excludes digits and "+" so this grammar does NOT
# match inside E.164 numbers ("+1-555-123-4567" belongs to the e164 grammar)
# or inside tel: URIs.
_NATIONAL_PATTERN = re.compile(
    r"(?<![\d+])(?:1[\s.\-]?)?\(?([2-9]\d{2})\)?[\s.\-]?"
    r"(\d{3})[\s.\-]?(\d{4})(?!\d)"
)

_ALLOWED_SEPARATORS = str.maketrans("", "", " ().-")


class NationalGrammar(Grammar[PhoneNotation]):
    """Recognizes NANP national dialing formats.

    Examples: "(555) 123-4567", "555-123-4567", "1-555-123-4567"
    Non-examples: "+15551234567" (international), "555-1234" (7-digit local)
    """

    name = "national_recognition"

    def recognize(self, text: str) -> list[PhoneNotation]:
        """Extract national patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of PhoneNotations with shape="national". value is the
            digit-only number; a leading trunk "1" is preserved when present.
        """
        results: list[PhoneNotation] = []
        seen: set[tuple[str, ...]] = set()
        for match in _NATIONAL_PATTERN.finditer(text):
            digits = match.group(0).translate(_ALLOWED_SEPARATORS)
            notation = PhoneNotation(shape="national", value=digits)
            key = tuple(notation.as_list())
            if key not in seen:
                seen.add(key)
                results.append(notation)
        return results
