"""ISO 80000-1 compound unit rule (edition 2022).

ISO 80000-1 §6.5 defines how unit symbols combine into product and
quotient compounds: "N·m", "m/s", "kg·m/s²". This rule validates the
compound shape against the full SI symbol lexicon (official + prefixed)
and renders the canonical ASCII-exponent form: superscripts translate
to ASCII digits, "⋅"/"·" normalize to "·", "/" stays "/", "l" -> "L".
The split patterns are kept local (not imported from grammar/data) so
rules never import from the grammar tree (grammar↔rules purity scan).
"""

from __future__ import annotations

import re

from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.capabilities.SIUnit.rules.data.prefixed_units import PREFIXED_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_base_units import BASE_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_derived_units import DERIVED_UNIT_SYMBOLS
from paxman.capabilities.SIUnit.rules.data.si_nonsi_units import NONSI_UNIT_SYMBOLS
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 80000-1:2022 Quantities and units — Part 1: General",
    kind="specification",
    reference_url="https://www.iso.org/standard/76921.html",
    version="2022",
    lifecycle="active",
    publication_year=2022,
)

_FULL_SYMBOL_LEXICON = (
    BASE_UNIT_SYMBOLS
    | DERIVED_UNIT_SYMBOLS
    | NONSI_UNIT_SYMBOLS
    | PREFIXED_UNIT_SYMBOLS
)
_EXPONENT_SUFFIX = re.compile(r"[0-9⁻⁰¹²³⁴⁵⁶⁷⁸⁹\-]*$")
_SUPERSCRIPT_TRANSLATE = str.maketrans(
    {
        "⁰": "0",
        "¹": "1",
        "²": "2",
        "³": "3",
        "⁴": "4",
        "⁵": "5",
        "⁶": "6",
        "⁷": "7",
        "⁸": "8",
        "⁹": "9",
        "⁻": "-",
    }
)
_SEPARATOR_TRANSLATE = str.maketrans({"⋅": "·"})  # D3: U+22C5 dot → U+00B7


class SectionCompounds(Rule[SIUnitNotation]):
    """ISO 80000-1 §6.5 — product and quotient unit compounds.

    Accepts compounds of the shape UNIT (separator UNIT){1,3} where each
    UNIT is a known symbol plus an optional exponent ("m/s²", "N·m",
    "kg·m/s²", "g/cm³"). "l" canonicalizes to "L" inside compounds.
    """

    name = "Section 6.5-compounds"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "ISO 80000-1:2022, §6.5 (unit symbols in products and quotients)"
    target_semantics = frozenset({"compound_recognition"})
    requires_features = frozenset()

    def matches(self, notation: SIUnitNotation, contract: Contract) -> bool:
        """Check if the notation is a valid SI compound."""
        if (
            contract.year is not None
            and contract.year < self.provenance.publication_year
        ):
            return False
        if notation.shape != "compound":
            return False
        return all(
            self._symbol_part(group) in _FULL_SYMBOL_LEXICON
            for group in re.split(r"[/·⋅]", notation.text)
        )

    def normalize(self, notation: SIUnitNotation, contract: Contract) -> str:
        """Normalize to the canonical compound: ASCII exponents, "·" separators."""
        return "".join(
            part if part in ("/", "·", "⋅") else self._canonical_group(part)
            for part in re.split(r"([/·⋅])", notation.text)
        ).translate(_SEPARATOR_TRANSLATE)

    @staticmethod
    def _symbol_part(group: str) -> str:
        """The symbol without its trailing exponent ("m/s2" -> "m/s2" group "m")."""
        return _EXPONENT_SUFFIX.sub("", group)

    @classmethod
    def _canonical_group(cls, group: str) -> str:
        """Canonical group: ASCII exponent, "l" -> "L", symbol unchanged."""
        match = _EXPONENT_SUFFIX.search(group)
        if match is None:
            return group
        symbol = group[: match.start()]
        exponent = group[match.start() :].translate(_SUPERSCRIPT_TRANSLATE)
        canonical_symbol = "L" if symbol == "l" else symbol
        return canonical_symbol + exponent
