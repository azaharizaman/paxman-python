"""IBAN recognition — CCDD+BBAN with optional IBAN label and paper spacing."""

from __future__ import annotations

import re

from paxman.capabilities.IBAN.notation import IBANNotation
from paxman.core.grammar.boundary import BoundaryGuard
from paxman.core.grammar.pipeline import PipelineGrammar
from paxman.core.grammar.stages import RegexStage, StandardPre

# Label separator is [\s:-]+ (one-or-more), never zero-width: a glued
# "IBANDE89..." must not fuse into a mention (ISBN-13 precedent).
# Two alternatives: electronic (contiguous 15-34) and paper (groups-of-four
# with single spaces). Paper uses groups-of-four to prevent greedy absorption
# of trailing English words (e.g. "DE89 ... 00 now" should not include "now");
# the word_only lookahead plus the 30-char cap still blocks >34-char runs,
# while a glued alnum tail <=30 chars (e.g. DE89...Y) is absorbed by design
# and rejected downstream via mod-97 (INVALID).
# Body uses inline (?ai:...) to restrict case-folding and character classes
# to ASCII (reject K and Unicode digits) while BoundaryGuard.word_only()
# remains Unicode-aware (no global re.ASCII).
_IBAN_BODY = (
    r"(?:(?ai:IBAN)[\s:-]+)?"
    r"(?P<compact>(?ai:(?:[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}"
    r"|[A-Z]{2}[0-9]{2}(?: [A-Z0-9]{4}){2,7}(?: [A-Z0-9]{1,4})?)))"
)
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
    regex = RegexStage[IBANNotation](pattern=_IBAN_PATTERN, notation_fn=_iban_notation)
