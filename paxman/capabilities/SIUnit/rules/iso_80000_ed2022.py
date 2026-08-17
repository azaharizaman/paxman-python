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

from paxman.capabilities.SIUnit.contract import SIUnitContract
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
# Split patterns are kept local (not imported from grammar/data) so rules
# never import from the grammar tree (grammar↔rules purity scan).
_SEPARATORS = "/·⋅"


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
        # ISO 80000-1 §6.6.2: a solidus shall not be followed by a
        # multiplication/division sign on the same line unless parentheses
        # disambiguate. More than one TOP-LEVEL "/" (outside parentheses) is
        # rejected unless the contract opts into the legacy behavior.
        allow_multi = (
            contract.allow_multi_solidus
            if isinstance(contract, SIUnitContract)
            else False
        )
        if _count_top_level_slash(notation.text) > 1 and not allow_multi:
            return False
        # Every top-level factor (a bare unit or a parenthesized group) must
        # validate against the full symbol lexicon.
        return all(_valid_factor(f) for f in _top_level_factors(notation.text))

    def normalize(self, notation: SIUnitNotation, contract: Contract) -> str:
        """Normalize to the canonical compound: ASCII exponents, "·" separators.

        Parentheses are preserved and their inner content is canonicalized
        recursively; "·"/"⋅" stay as separators, "/" stays, superscripts fold
        to ASCII, "l" -> "L".
        """
        return _canonical_compound(notation.text).translate(_SEPARATOR_TRANSLATE)


def _symbol_part(group: str) -> str:
    """The symbol without its trailing exponent ("m/s2" -> "m/s2" group "m")."""
    return _EXPONENT_SUFFIX.sub("", group)


def _canonical_group(group: str) -> str:
    """Canonical group: ASCII exponent, "l" -> "L", symbol unchanged."""
    match = _EXPONENT_SUFFIX.search(group)
    if match is None:
        return group
    symbol = group[: match.start()]
    exponent = group[match.start() :].translate(_SUPERSCRIPT_TRANSLATE)
    canonical_symbol = "L" if symbol == "l" else symbol
    return canonical_symbol + exponent


def _count_top_level_slash(text: str) -> int:
    """Count "/" characters that appear outside any parentheses.

    A "/" inside a parenthesized factor does not count toward the
    multi-solidus guard (ISO 80000-1 §6.6.2 allows one solidus per line,
    with parentheses as the disambiguation).
    """
    count = 0
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and ch == "/":
            count += 1
    return count


def _top_level_factors(text: str) -> list[str]:
    """Split a compound into its top-level factors (outside parentheses).

    Separators ("/", "·", "⋅") at depth 0 break the compound into factors;
    a parenthesized group is kept intact as a single factor.
    """
    factors: list[str] = []
    depth = 0
    current = ""
    for ch in text:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth -= 1
            current += ch
        elif depth == 0 and ch in _SEPARATORS:
            factors.append(current)
            current = ""
        else:
            current += ch
    factors.append(current)
    return factors


def _valid_factor(factor: str) -> bool:
    """Validate one compound factor against the full symbol lexicon.

    A parenthesized factor's inner content must itself be a valid compound
    (each inner part in the lexicon); a bare factor must be a known symbol.
    """
    if factor.startswith("(") and factor.endswith(")"):
        inner = factor[1:-1]
        return all(
            _symbol_part(part) in _FULL_SYMBOL_LEXICON
            for part in re.split(r"[/·⋅]", inner)
        )
    return _symbol_part(factor) in _FULL_SYMBOL_LEXICON


def _canonical_compound(text: str) -> str:
    """Render the canonical form of a compound, preserving parentheses.

    Walks the text tracking parenthesis depth: top-level separators are
    emitted verbatim, each top-level factor is canonicalized (recursively
    when parenthesized), and inner content is canonicalized the same way.
    """
    out: list[str] = []
    depth = 0
    current = ""
    for ch in text:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth -= 1
            current += ch
        elif depth == 0 and ch in _SEPARATORS:
            out.append(_canonical_factor(current))
            out.append(ch)
            current = ""
        else:
            current += ch
    out.append(_canonical_factor(current))
    return "".join(out)


def _canonical_factor(factor: str) -> str:
    """Canonicalize one factor: recurse into a parenthesized group, else a unit."""
    if factor.startswith("(") and factor.endswith(")"):
        return "(" + _canonical_compound(factor[1:-1]) + ")"
    return _canonical_group(factor)
