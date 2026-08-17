"""Slash-ISO date grammar — recognizes YYYY/MM/DD format.

Notation mapping: N1=year, N2=month, N3=day
"""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar, RecognitionMatch

_SLASH_ISO_PATTERN = re.compile(r"(?<!\d)(\d{4})/(\d{1,2})/(\d{1,2})(?!\d)")


class SlashISODateGrammar(Grammar[DateNotation]):
    """Slash-delimited ISO date recognition: YYYY/MM/DD.

    Shares the ISO 8601 position mapping (N1=year, N2=month, N3=day) with a
    ``/`` delimiter instead of ``-``; single-digit month/day components are
    accepted and zero-padded by the validating rule. The leading 4-digit year
    keeps the pattern disjoint from the US and European grammars, which both
    require a leading month/day. Digit lookarounds keep the match disjoint
    from surrounding digits, mirroring the other shipped date grammars, so a
    longer digit run (e.g. an ID like ``12026/01/15``) is never partially
    matched as a date.

    Notation mapping: N1=year, N2=month, N3=day
    """

    name = "slash_iso_recognition"
    semantics = "iso8601_calendar_date"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        """Extract YYYY/MM/DD date patterns from text."""
        return [
            RecognitionMatch(
                notation=DateNotation(N1=year, N2=month, N3=day),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _SLASH_ISO_PATTERN.finditer(text)
            for year, month, day in [match.groups()]
        ]
