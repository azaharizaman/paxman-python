"""RFC 3966 tel-URI recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# tel: URI with global number digits (optional separators) and optional
# ";ext=" parameter. The scheme is matched case-insensitively.
_TEL_URI_PATTERN = re.compile(r"tel:([+\d][\d\s().\-]*)(?:;ext=(\d+))?", re.IGNORECASE)

_ALLOWED_SEPARATORS = str.maketrans("", "", "+ ().-")


class TelUriGrammar(Grammar[PhoneNotation]):
    """Recognizes RFC 3966 tel: URIs.

    Examples: "tel:+15551234567", "tel:+1-201-555-0123;ext=890"
    Non-examples: "+15551234567" (no tel: scheme)
    """

    name = "tel_uri_recognition"

    def recognize(self, text: str) -> list[PhoneNotation]:
        """Extract tel: URI patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of PhoneNotations with shape="rfc3966". value is the
            digit-only number (leading "+" and separators removed);
            extension is the ";ext=" parameter value if present.
        """
        results: list[PhoneNotation] = []
        seen: set[tuple[str, ...]] = set()
        for match in _TEL_URI_PATTERN.finditer(text):
            digits = match.group(1).translate(_ALLOWED_SEPARATORS)
            extension = match.group(2) or ""
            notation = PhoneNotation(shape="rfc3966", value=digits, extension=extension)
            key = tuple(notation.as_list())
            if key not in seen:
                seen.add(key)
                results.append(notation)
        return results
