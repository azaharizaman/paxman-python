"""RFC 3966 tel-URI recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Phone.grammar.common import strip_separators
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar, RecognitionMatch

# tel: URI with a GLOBAL number (optional separators) and optional ";ext="
# parameter. Per RFC 3966 §3.1 global numbers REQUIRE a leading "+" —
# no-plus URIs are local numbers (out of scope), so this grammar does not
# match them. The scheme is matched case-insensitively; the (?<![\w])
# lookbehind keeps "xtel:"/"hotel:" from matching the scheme.
_TEL_URI_PATTERN = re.compile(
    r"(?<![\w])tel:\+(\d[\d\s().\-]*)(?:;ext=(\d+))?", re.IGNORECASE
)


class TelUriGrammar(Grammar[PhoneNotation]):
    """Recognizes RFC 3966 tel: URIs.

    Examples: "tel:+15551234567", "tel:+1-201-555-0123;ext=890"
    Non-examples: "+15551234567" (no tel: scheme)
    """

    name = "tel_uri_recognition"
    semantics = "tel_uri_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[PhoneNotation]]:
        """Extract tel: URI patterns from text.

        Returns:
            List of RecognitionMatches; notation.value is the digit-only
            number (leading "+" and separators removed); notation.extension
            is the ";ext=" parameter value if present.
        """
        return [
            RecognitionMatch(
                notation=PhoneNotation(
                    shape="rfc3966",
                    value=strip_separators(match.group(1), plus=True),
                    extension=match.group(2) or "",
                ),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _TEL_URI_PATTERN.finditer(text)
        ]
