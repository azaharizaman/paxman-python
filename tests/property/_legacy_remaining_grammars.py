"""Verbatim legacy Date/Email/IP/ISBN/Country grammars (pre-PipelineGrammar migration).

Snapshot of the bespoke ``recognize()`` logic at the start of Task 9, used by
the Migration Proof Harness (ADR-0008 §4.1) to assert byte-identical
``RecognitionMatch`` output after the staged-pipeline migration. Classes are
renamed ``Legacy*`` to avoid colliding with the migrated grammar classes.

Do NOT edit by hand — this is a frozen reference. The live grammar files are
the source of truth post-migration; this module exists only so the parity
test can compare old vs new behavior.
"""

from __future__ import annotations

import re

from paxman.capabilities.Country.grammar.data.chinese_names import (
    CHINESE_NAME_KEYS,
)
from paxman.capabilities.Country.grammar.data.english_names import (
    ENGLISH_NAME_KEYS,
)
from paxman.capabilities.Country.grammar.data.historical_names import (
    HISTORICAL_NAME_KEYS,
)
from paxman.capabilities.Country.grammar.data.localized_names import (
    LOCALIZED_NAME_KEYS,
)
from paxman.capabilities.Country.notation import CountryNotation, normalize_name
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Email.notation import EmailNotation
from paxman.capabilities.IP.notation import IPNotation
from paxman.capabilities.ISBN.notation import ISBNNotation
from paxman.core.domain import Grammar, RecognitionMatch

# ---------------------------------------------------------------------------
# Date
# ---------------------------------------------------------------------------

_ISO8601_PATTERN = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")

_US_DATE_PATTERN_4DIGIT = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)")
_US_DATE_PATTERN_2DIGIT = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2})(?!\d)")

_EUROPEAN_DATE_PATTERN_4DIGIT = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)")
_EUROPEAN_DATE_PATTERN_2DIGIT = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2})(?!\d)")

_SLASH_ISO_PATTERN = re.compile(r"(?<!\d)(\d{4})/(\d{1,2})/(\d{1,2})(?!\d)")


class LegacyISO8601DateGrammar(Grammar[DateNotation]):
    """Legacy ISO 8601 date recognition (verbatim)."""

    name = "iso8601_recognition"
    semantics = "iso8601_calendar_date"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        return [
            RecognitionMatch(
                notation=DateNotation(N1=year, N2=month, N3=day),
                start=match.start(),
                end=match.end(),
                raw_text=match.group(0),
            )
            for match in _ISO8601_PATTERN.finditer(text)
            for year, month, day in [match.groups()]
        ]


class LegacyUSDateGrammar(Grammar[DateNotation]):
    """Legacy US date recognition (verbatim)."""

    name = "us_recognition"
    semantics = "us_calendar_date"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        results: list[RecognitionMatch[DateNotation]] = []
        for match in _US_DATE_PATTERN_4DIGIT.finditer(text):
            month, day, year = match.group(1), match.group(2), match.group(3)
            results.append(
                RecognitionMatch(
                    notation=DateNotation(N1=month, N2=day, N3=year),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        for match in _US_DATE_PATTERN_2DIGIT.finditer(text):
            month, day, year = match.group(1), match.group(2), match.group(3)
            results.append(
                RecognitionMatch(
                    notation=DateNotation(N1=month, N2=day, N3=year),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return results


class LegacyEuropeanDateGrammar(Grammar[DateNotation]):
    """Legacy European date recognition (verbatim)."""

    name = "european_recognition"
    semantics = "european_calendar_date"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
        results: list[RecognitionMatch[DateNotation]] = []
        for match in _EUROPEAN_DATE_PATTERN_4DIGIT.finditer(text):
            day, month, year = match.group(1), match.group(2), match.group(3)
            results.append(
                RecognitionMatch(
                    notation=DateNotation(N1=day, N2=month, N3=year),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        for match in _EUROPEAN_DATE_PATTERN_2DIGIT.finditer(text):
            day, month, year = match.group(1), match.group(2), match.group(3)
            results.append(
                RecognitionMatch(
                    notation=DateNotation(N1=day, N2=month, N3=year),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return results


class LegacySlashISODateGrammar(Grammar[DateNotation]):
    """Legacy slash-ISO date recognition (verbatim)."""

    name = "slash_iso_recognition"
    semantics = "iso8601_calendar_date"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[DateNotation]]:
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


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

_STANDARD_PATTERN = re.compile(
    r"\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

_OBFUSCATED_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)\s+at\s+([A-Za-z0-9.-]+)\s+dot\s+([A-Za-z]{2,})\b"
)
_AT_ONLY_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)\s+at\s+([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)

_LOCALHOST_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)@localhost(?::\d+)?(?:(?=[\s,;()]|$)|\.(?=\s|$))",
    re.IGNORECASE,
)


class LegacyStandardEmailGrammar(Grammar[EmailNotation]):
    """Legacy standard email recognition (verbatim)."""

    name = "standard_recognition"
    semantics = "rfc5322_addr_spec"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[EmailNotation]]:
        matches: list[RecognitionMatch[EmailNotation]] = []
        for match in _STANDARD_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(0).split("@")[0],
                        domain_part=match.group(0).split("@")[1],
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


class LegacyObfuscatedEmailGrammar(Grammar[EmailNotation]):
    """Legacy obfuscated email recognition (verbatim)."""

    name = "obfuscated_recognition"
    semantics = "rfc5322_addr_spec"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[EmailNotation]]:
        matches: list[RecognitionMatch[EmailNotation]] = []
        for match in _OBFUSCATED_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(1),
                        domain_part=f"{match.group(2)}.{match.group(3)}",
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        for match in _AT_ONLY_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(1),
                        domain_part=match.group(2),
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


class LegacyLocalhostEmailGrammar(Grammar[EmailNotation]):
    """Legacy localhost email recognition (verbatim)."""

    name = "localhost_recognition"
    semantics = "localhost_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[EmailNotation]]:
        matches: list[RecognitionMatch[EmailNotation]] = []
        for match in _LOCALHOST_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=EmailNotation(
                        local_part=match.group(1), domain_part="localhost"
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


# ---------------------------------------------------------------------------
# IP
# ---------------------------------------------------------------------------

_IPV4_PATTERN = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b")

_IPV6_BOUNDARY = r"(?:^|(?<=[\s,;([ ]))"
_IPV6_END = r"(?:$|(?=[\s,;().\]]))"

_IPV6_FULL = re.compile(
    _IPV6_BOUNDARY + r"([0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){7})" + _IPV6_END
)
_IPV6_COMPRESSED = re.compile(
    _IPV6_BOUNDARY
    + r"((?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{0,4}::"
    + r"(?:[0-9a-fA-F]{0,4}:){0,6}[0-9a-fA-F]{1,4})"
    + _IPV6_END
    + "|"
    + _IPV6_BOUNDARY
    + r"(::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4})"
    + _IPV6_END
    + "|"
    + _IPV6_BOUNDARY
    + r"((?:[0-9a-fA-F]{1,4}:){1,6}[0-9a-fA-F]{0,4}::)"
    + _IPV6_END
    + "|"
    + _IPV6_BOUNDARY
    + r"(::)"
    + _IPV6_END
)


class LegacyIPv4Grammar(Grammar[IPNotation]):
    """Legacy IPv4 recognition (verbatim)."""

    name = "ipv4_recognition"
    semantics = "ipv4_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[IPNotation]]:
        matches: list[RecognitionMatch[IPNotation]] = []
        for match in _IPV4_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=IPNotation(address=match.group(0)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


class LegacyIPv6Grammar(Grammar[IPNotation]):
    """Legacy IPv6 recognition (verbatim)."""

    name = "ipv6_recognition"
    semantics = "ipv6_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[IPNotation]]:
        matches: list[RecognitionMatch[IPNotation]] = []
        for match in _IPV6_FULL.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=IPNotation(address=match.group(1)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(1),
                )
            )
        for match in _IPV6_COMPRESSED.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=IPNotation(address=match.group(0)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


# ---------------------------------------------------------------------------
# ISBN
# ---------------------------------------------------------------------------

_ISBN13_PATTERN = re.compile(
    r"\b(?:ISBN(?:-13)?[\s:-]+)?(?=((?:\d[ -]?){12}\d)(?![\d]))\1(?<![\s:-])\b",
    re.IGNORECASE,
)

_ISBN10_PATTERN = re.compile(
    r"(?<!\d)(?<!\d[ -])(?:ISBN(?:-10)?[\s:-]+)?"
    r"(?=((?:\d[ -]?){9}[0-9Xx])(?![\d]))\1(?<![\s:-])\b",
    re.IGNORECASE,
)


class LegacyISBN13RecognitionGrammar(Grammar[ISBNNotation]):
    """Legacy ISBN-13 recognition (verbatim)."""

    name = "isbn13_recognition"
    semantics = "isbn13_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[ISBNNotation]]:
        matches: list[RecognitionMatch[ISBNNotation]] = []
        for m in _ISBN13_PATTERN.finditer(text):
            digits = "".join(ch for ch in m.group(1) if ch in "0123456789")
            if len(digits) != 13:
                continue
            matches.append(
                RecognitionMatch(
                    notation=ISBNNotation(
                        shape="isbn13",
                        digits=digits,
                    ),
                    start=m.start(),
                    end=m.end(),
                    raw_text=m.group(0),
                )
            )
        return matches


class LegacyISBN10RecognitionGrammar(Grammar[ISBNNotation]):
    """Legacy ISBN-10 recognition (verbatim)."""

    name = "isbn10_recognition"
    semantics = "isbn10_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[ISBNNotation]]:
        matches: list[RecognitionMatch[ISBNNotation]] = []
        for m in _ISBN10_PATTERN.finditer(text):
            digits = "".join(ch for ch in m.group(1) if ch in "0123456789Xx").upper()
            if len(digits) != 10:
                continue
            matches.append(
                RecognitionMatch(
                    notation=ISBNNotation(
                        shape="isbn10",
                        digits=digits,
                    ),
                    start=m.start(),
                    end=m.end(),
                    raw_text=m.group(0),
                )
            )
        return matches


# ---------------------------------------------------------------------------
# Country
# ---------------------------------------------------------------------------

_KNOWN_NAME_KEYS = (
    ENGLISH_NAME_KEYS | HISTORICAL_NAME_KEYS | CHINESE_NAME_KEYS | LOCALIZED_NAME_KEYS
)

_ALPHA2_PATTERN = re.compile(r"\b[A-Za-z]{2}\b")
_ALPHA3_PATTERN = re.compile(r"\b[A-Za-z]{3}\b")
_NUMERIC_PATTERN = re.compile(r"\b\d{1,3}\b")


class LegacyAlpha2Grammar(Grammar[CountryNotation]):
    """Legacy alpha-2 country code recognition (verbatim)."""

    name = "alpha2_recognition"
    semantics = "alpha2_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CountryNotation]] = []
        for match in _ALPHA2_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CountryNotation(
                        shape="alpha2", value=match.group(0).upper()
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


class LegacyAlpha3Grammar(Grammar[CountryNotation]):
    """Legacy alpha-3 country code recognition (verbatim)."""

    name = "alpha3_recognition"
    semantics = "alpha3_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CountryNotation]] = []
        for match in _ALPHA3_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CountryNotation(
                        shape="alpha3", value=match.group(0).upper()
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


class LegacyNumericGrammar(Grammar[CountryNotation]):
    """Legacy numeric country code recognition (verbatim)."""

    name = "numeric_recognition"
    semantics = "numeric_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CountryNotation]] = []
        for match in _NUMERIC_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CountryNotation(shape="numeric", value=match.group(0)),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


class LegacyNameGrammar(Grammar[CountryNotation]):
    """Legacy country name recognition (verbatim)."""

    name = "name_recognition"
    semantics = "name_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[CountryNotation]]:
        trimmed = text.strip()
        if not trimmed:
            return []

        normalized = normalize_name(trimmed)

        if normalized in _KNOWN_NAME_KEYS:
            start = len(text) - len(text.lstrip())
            return [
                RecognitionMatch(
                    notation=CountryNotation(shape="name", value=trimmed),
                    start=start,
                    end=start + len(trimmed),
                    raw_text=trimmed,
                )
            ]

        return []
