"""International 00-prefix recognition grammar.

The international prefix "00" is the ITU-T E.164 recommended prefix used
when dialing from within most countries. The digits AFTER the prefix form
the E.164 number, so this grammar produces shape="e164" with the prefix
stripped.
"""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# "00" followed by the international number digits (optional separators).
# The leading digit of the number must be 1-9 (country codes never start
# with 0), and a single "0" alone is not the international prefix.
# Separators between "00" and the first digit are allowed ("00 44 ...").
_INTERNATIONAL_00_PATTERN = re.compile(r"(?<!\d)00[\s.\-]*(?=[1-9])\d[\d\s().\-]*")

_ALLOWED_SEPARATORS = str.maketrans("", "", " ().-")


class International00Grammar(Grammar[PhoneNotation]):
    """Recognizes international numbers written with the 00 prefix.

    Examples: "00 44 20 7946 0958", "00442079460958"
    Non-examples: "+442079460958" (has +), "0 44 20 7946 0958" (single 0)
    """

    name = "international_00_recognition"

    def recognize(self, text: str) -> list[PhoneNotation]:
        """Extract 00-prefixed international patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of PhoneNotations with shape="e164". value is the digit-only
            number with the "00" prefix stripped (the E.164 number itself).
        """
        results: list[PhoneNotation] = []
        seen: set[tuple[str, ...]] = set()
        for match in _INTERNATIONAL_00_PATTERN.finditer(text):
            raw = match.group(0)
            # Strip the leading "00" before removing separators.
            digits = raw[2:].translate(_ALLOWED_SEPARATORS)
            notation = PhoneNotation(shape="e164", value=digits)
            key = tuple(notation.as_list())
            if key not in seen:
                seen.add(key)
                results.append(notation)
        return results
