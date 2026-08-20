"""Verbatim legacy Phone + URL grammars (pre-PipelineGrammar migration).

Snapshot of the bespoke ``recognize()`` logic from the branch
refactor/staged-recognition-pipeline (commit eeb9529 SIUnit), used by the
Migration Proof Harness (ADR-0008 §4.1) to assert byte-identical
``RecognitionMatch`` output after the staged-pipeline migration. Classes are
renamed ``Legacy*`` to avoid colliding with the migrated grammar classes.

Do NOT edit by hand — this is a frozen reference. The live grammar files are
the source of truth post-migration; this module exists only so the parity
test can compare old vs new behavior.
"""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.URL.notation import URLNotation
from paxman.core.domain import Grammar, RecognitionMatch

# Verbatim copy of Phone/grammar/common.py:strip_separators (the legacy helper
# retired in ADR-0008 Task 10) so this frozen reference stays self-contained.
_SEPARATORS = str.maketrans("", "", " ().-")
_SEPARATORS_WITH_PLUS = str.maketrans("", "", "+ ().-")


def strip_separators(value: str, *, plus: bool = False) -> str:
    """Remove phone separators from a raw match (legacy verbatim)."""
    if plus:
        return value.translate(_SEPARATORS_WITH_PLUS)
    return value.translate(_SEPARATORS)

# ---------------------------------------------------------------------------
# Phone / E.164 (verbatim)
# ---------------------------------------------------------------------------

_E164_PATTERN = re.compile(r"(?<![\w:.])\+\d[\d\s().\-]*(?<=\d)")

_MAX_E164_DIGITS = 15


def _trim_to_e164_boundary(raw: str) -> str:
    """Trim a runaway raw match at the last digit-run group within the limit."""
    runs = list(re.finditer(r"\d+", raw))
    total = 0
    for index, run in enumerate(runs):
        total += len(run.group(0))
        if total > _MAX_E164_DIGITS:
            if index == 0:
                return raw
            return raw[: runs[index - 1].end()]
    return raw


class LegacyE164Grammar(Grammar[PhoneNotation]):
    """Recognizes E.164-style international numbers (leading +)."""

    name = "e164_recognition"
    semantics = "e164_international"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[PhoneNotation]]:
        matches: list[RecognitionMatch[PhoneNotation]] = []
        for match in _E164_PATTERN.finditer(text):
            raw_text = _trim_to_e164_boundary(match.group(0))
            matches.append(
                RecognitionMatch(
                    notation=PhoneNotation(
                        shape="e164",
                        value=strip_separators(raw_text, plus=True),
                    ),
                    start=match.start(),
                    end=match.start() + len(raw_text),
                    raw_text=raw_text,
                )
            )
        return matches


# ---------------------------------------------------------------------------
# Phone / tel-URI (verbatim)
# ---------------------------------------------------------------------------

_TEL_URI_PATTERN = re.compile(
    r"(?<![\w])tel:\+(\d[\d\s().\-]*)(?:;ext=(\d+))?", re.IGNORECASE
)


class LegacyTelUriGrammar(Grammar[PhoneNotation]):
    """Recognizes RFC 3966 tel: URIs."""

    name = "tel_uri_recognition"
    semantics = "tel_uri_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[PhoneNotation]]:
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


# ---------------------------------------------------------------------------
# Phone / international 00-prefix (verbatim)
# ---------------------------------------------------------------------------

_INTERNATIONAL_00_PATTERN = re.compile(
    r"(?<![\w:.+])00[\s.\-]*(?=[1-9])\d[\d\s().\-]*(?<=\d)"
)


class LegacyInternational00Grammar(Grammar[PhoneNotation]):
    """Recognizes international numbers written with the 00 prefix."""

    name = "international_00_recognition"
    semantics = "e164_international"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[PhoneNotation]]:
        return [
            RecognitionMatch(
                notation=PhoneNotation(
                    shape="e164",
                    value=strip_separators(match.group(0)[2:]),
                ),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _INTERNATIONAL_00_PATTERN.finditer(text)
        ]


# ---------------------------------------------------------------------------
# Phone / national (NANP) (verbatim)
# ---------------------------------------------------------------------------

_NATIONAL_PATTERN = re.compile(
    r"(?<![\d+])(?<![\d+][\s.\-])(?<![\d+][\s.\-]\()(?<![\d+]\()"
    r"(?:1[\s.\-]?)?\(?([2-9]\d{2})\)?[\s.\-]?"
    r"(\d{3})[\s.\-]?(\d{4})(?!\d)"
)


class LegacyNationalGrammar(Grammar[PhoneNotation]):
    """Recognizes NANP national dialing formats."""

    name = "national_recognition"
    semantics = "national_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[PhoneNotation]]:
        return [
            RecognitionMatch(
                notation=PhoneNotation(
                    shape="national", value=strip_separators(match.group(0))
                ),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _NATIONAL_PATTERN.finditer(text)
        ]


# ---------------------------------------------------------------------------
# URL / absolute-URI (verbatim)
# ---------------------------------------------------------------------------

_ABSOLUTE_URI_PATTERN = re.compile(
    r"(?<![A-Za-z0-9+.\-])"
    r"[A-Za-z][A-Za-z0-9+.\-]*:"
    r'[^ <>"\x00-\x08\x0B\x0C\x0E-\x1F\x7F]*[^ <>"\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'
)


class LegacyAbsoluteUriRecognition(Grammar[URLNotation]):
    """Absolute-URI recognition: extracts scheme-anchored URI spans."""

    name = "absolute_uri_recognition"
    semantics = "absolute_uri_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[URLNotation]]:
        results: list[RecognitionMatch[URLNotation]] = []
        for match in _ABSOLUTE_URI_PATTERN.finditer(text):
            raw_span = match.group(0)
            excess = raw_span.count(")") - raw_span.count("(")
            trim = 0
            while trim < excess and raw_span[-(trim + 1)] == ")":
                trim += 1
            if trim:
                raw_span = raw_span[:-trim]
            scheme_end = raw_span.find(":")
            if len(raw_span) <= scheme_end + 1:
                continue
            start = match.start()
            end = start + len(raw_span)
            results.append(
                RecognitionMatch(
                    notation=URLNotation(text=raw_span),
                    start=start,
                    end=end,
                    raw_text=raw_span,
                )
            )
        return results
