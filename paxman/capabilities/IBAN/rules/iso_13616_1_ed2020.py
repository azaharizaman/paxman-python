"""ISO 13616-1:2020 + ISO/IEC 7064:2003 MOD 97-10 — generic IBAN structure."""

from __future__ import annotations

from paxman.capabilities.IBAN.notation import IBANNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 13616-1:2020",
    kind="specification",
    reference_url="https://www.iso.org/standard/81090.html",
    version="2020",
    lifecycle="active",
    publication_year=2020,
)

# SWIFT IBAN Registry — Release 99 Dec 2024 (mirrors Release 100 Oct 2025);
# 90 ISO 3166 country codes with registered IBAN formats. Used to validate
# the two-letter prefix before MOD 97-10 (registry, not bare ISO 3166-1).
REGISTERED_IBAN_COUNTRY_CODES: frozenset[str] = frozenset(
    {
        "AD",
        "AE",
        "AL",
        "AT",
        "AZ",
        "BA",
        "BE",
        "BG",
        "BH",
        "BI",
        "BR",
        "BY",
        "CH",
        "CR",
        "CY",
        "CZ",
        "DE",
        "DJ",
        "DK",
        "DO",
        "EE",
        "EG",
        "ES",
        "FI",
        "FK",
        "FO",
        "FP",
        "FR",
        "GB",
        "GE",
        "GI",
        "GL",
        "GR",
        "GT",
        "HN",
        "HR",
        "HU",
        "IE",
        "IL",
        "IQ",
        "IS",
        "IT",
        "JO",
        "KW",
        "KZ",
        "LB",
        "LC",
        "LI",
        "LT",
        "LU",
        "LV",
        "LY",
        "MC",
        "MD",
        "ME",
        "MK",
        "MN",
        "MR",
        "MT",
        "MU",
        "NI",
        "NL",
        "NO",
        "OM",
        "PK",
        "PL",
        "PS",
        "PT",
        "QA",
        "RO",
        "RS",
        "RU",
        "SA",
        "SC",
        "SD",
        "SE",
        "SI",
        "SK",
        "SM",
        "SO",
        "ST",
        "SV",
        "TL",
        "TN",
        "TR",
        "UA",
        "VA",
        "VG",
        "XK",
        "YE",
    }
)

_REGISTERED_IBAN_COUNTRY_CODES = REGISTERED_IBAN_COUNTRY_CODES


def _mod97(compact: str) -> int:
    rearranged = compact[4:] + compact[:4]
    expanded_chars: list[str] = []
    for ch in rearranged:
        if "A" <= ch <= "Z":
            expanded_chars.append(str(ord(ch) - 55))
        else:
            expanded_chars.append(ch)
    expanded = "".join(expanded_chars)
    r = 0
    for d in expanded:
        r = (r * 10 + int(d)) % 97
    return r


class Section4IBANStructureMOD97(Rule[IBANNotation]):
    """ISO 13616-1 §4-5 + ISO/IEC 7064 MOD 97-10 — generic IBAN validation.

    Validates generic IBAN: total 15-34, charset [A-Z]{2}[0-9]{2}[A-Z0-9]{1,30},
    CC in SWIFT IBAN Registry (90 codes), DD in 02-98 (reject 00/01/99),
    and mod97==1. Citations: ISO 13616-1:2020 structure + MOD 97-10 normative
    reference to ISO/IEC 7064:2003; CC check against SWIFT IBAN Registry.
    """

    name = "Section 4-iban-structure-mod97"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 4-5 (structure + MOD 97-10, via ISO/IEC 7064:2003)"
    target_semantics = frozenset({"iban_recognition"})
    requires_features = frozenset()

    def matches(self, notation: IBANNotation, contract: Contract) -> bool:
        c = notation.compact
        if not (15 <= len(c) <= 34):
            return False
        if not c.isascii() or not c.isalnum() or not c.isupper():
            return False
        if not (c[0:2].isalpha() and c[2:4].isdigit()):
            return False
        if c[0:2] not in _REGISTERED_IBAN_COUNTRY_CODES:
            return False
        if c[2:4] in ("00", "01", "99"):
            return False
        return _mod97(c) == 1

    def normalize(self, notation: IBANNotation, contract: Contract) -> str:
        return notation.compact
