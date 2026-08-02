"""NANP national number recognition grammar.

Recognizes domestic (NANP-style) dialing formats: optional trunk "1",
optional parenthesized NPA, then 3-3-4 digit groups with any of space,
dash, or dot separators. This grammar is deliberately NANP-shaped for
Milestone 1; future milestones add country-specific national grammars.
"""

from __future__ import annotations

import re

from paxman.capabilities.Phone.grammar.common import dedup, strip_separators
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# Optional trunk 1, optional (NPA), NXX, XXXX. NPA first digit 2-9 is a
# recognition heuristic — strict validation (including NXX first digit 2-9)
# happens in the rules. NXX is deliberately loose here so the grammar
# recognizes the NANP *shape* even for unassignable exchanges (e.g.,
# "555-123-4567"), which the NANP rule then rejects as INVALID.
#
# Four fixed-width negative lookbehinds ensure this grammar does NOT match
# inside E.164 numbers or tel: URIs (those belong to the e164 / tel-URI
# grammars). They reject a match when the characters immediately before it
# belong to an international number:
#   1. digit or "+"          -> "+15551234567" (compact)
#   2. separator after d/+   -> "+1-555-123-4567", "+1 555 123 4567", "+1.555..."
#   3. "( " after sep after d/+ -> "+1 (555) 123-4567" (parens w/ separator)
#   4. "(" directly after d/+ -> "+1(555)123-4567"  (parens, no separator)
#
# No-plus local tel: URIs ("tel:212-555-6789") are NOT global numbers
# (RFC 3966 §3.1) and are not recognized by the tel-URI grammar; their
# NANP-shaped number content may be recognized here as a national number.
_NATIONAL_PATTERN = re.compile(
    r"(?<![\d+])(?<![\d+][\s.\-])(?<![\d+][\s.\-]\()(?<![\d+]\()"
    r"(?:1[\s.\-]?)?\(?([2-9]\d{2})\)?[\s.\-]?"
    r"(\d{3})[\s.\-]?(\d{4})(?!\d)"
)


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
        return dedup(
            PhoneNotation(shape="national", value=strip_separators(match.group(0)))
            for match in _NATIONAL_PATTERN.finditer(text)
        )
