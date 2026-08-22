"""IBAN recognition — CCDD+BBAN with optional IBAN label and paper spacing."""

from __future__ import annotations

import re

from paxman.capabilities.IBAN.notation import IBANNotation
from paxman.core.grammar.boundary import BoundaryGuard
from paxman.core.grammar.pipeline import PipelineGrammar
from paxman.core.grammar.stages import RegexStage, StandardPre

# Label separator is [\s:-]+ (one-or-more), never zero-width: a glued
# "IBANDE89..." must not fuse into a mention (ISBN-13 precedent).
_IBAN_BODY = r"(?:IBAN[\s:-]+)?(?P<compact>[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30})"
# word_only guards: the lookbehind blocks left glue (XDE89...); the trailing
# lookahead plus the 30-char loop cap blocks >34-char runs (every interior
# end is followed by a word char). A <=30-char alnum tail is absorbed by
# design — mod-97 rejects it downstream (INVALID); see
# test_alnum_tail_absorbed_documented in the grammar tests.
_IBAN_PATTERN = (
    BoundaryGuard.word_only().lookbehind
    + _IBAN_BODY
    + BoundaryGuard.word_only().lookahead
)


def _iban_notation(match: re.Match[str]) -> IBANNotation:
    raw_compact = match.group("compact")
    compact = "".join(ch for ch in raw_compact if ch.isalnum()).upper()
    country_code = compact[0:2]
    check_digits = compact[2:4]
    bban = compact[4:]
    return IBANNotation(
        country_code=country_code, check_digits=check_digits, bban=bban, compact=compact
    )


class IBANRecognitionGrammar(PipelineGrammar[IBANNotation]):
    """IBAN recognition — CCDD+BBAN with optional IBAN label and paper spacing."""

    name = "iban_recognition"
    semantics = "iban_recognition"
    single_value = True
    pre = StandardPre[IBANNotation](empty_guard=True)
    regex = RegexStage[IBANNotation](
        pattern=_IBAN_PATTERN, notation_fn=_iban_notation, flags=re.IGNORECASE
    )
