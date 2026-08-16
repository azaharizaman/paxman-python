"""International 00-prefix recognition grammar.

The international prefix "00" is the ITU-T E.164 recommended prefix used
when dialing from within most countries. The digits AFTER the prefix form
the E.164 number, so this grammar produces shape="e164" with the prefix
stripped.
"""

from __future__ import annotations

import re

from paxman.capabilities.Phone.grammar.common import strip_separators
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar, RecognitionMatch

# "00" followed by the international number digits (optional separators).
# The leading digit of the number must be 1-9 (country codes never start
# with 0), and a single "0" alone is not the international prefix.
# Separators between "00" and the first digit are allowed ("00 44 ...").
# The (?<![\w:.+]) lookbehind excludes word characters, ":", "." and "+"
# so "10044..." / "x0044..." / "0.0044..." are not treated as prefixes
# and "+0044..." (contradictory input) is left to the e164 grammar.
# The trailing (?<=\d) lookbehind forces the match to end on a digit, so
# the trailing character class cannot swallow separators, whitespace, or
# sentence punctuation after the number (mirrors _E164_PATTERN).
_INTERNATIONAL_00_PATTERN = re.compile(
    r"(?<![\w:.+])00[\s.\-]*(?=[1-9])\d[\d\s().\-]*(?<=\d)"
)


class International00Grammar(Grammar[PhoneNotation]):
    """Recognizes international numbers written with the 00 prefix.

    Examples: "00 44 20 7946 0958", "00442079460958"
    Non-examples: "+442079460958" (has +), "0 44 20 7946 0958" (single 0)
    """

    name = "international_00_recognition"
    semantics = "e164_international"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[PhoneNotation]]:
        """Extract 00-prefixed international patterns from text.

        Returns:
            List of RecognitionMatches; notation.value is the digit-only
            number with the "00" prefix stripped (the E.164 number itself).
        """
        return [
            RecognitionMatch(
                notation=PhoneNotation(
                    shape="e164",
                    # Strip the leading "00" before removing separators.
                    value=strip_separators(match.group(0)[2:]),
                ),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _INTERNATIONAL_00_PATTERN.finditer(text)
        ]
