"""SI prefix-spacing rule (BIPM SI Brochure 9th ed., 2019, §3.2).

SI prefixes are part of the unit name/symbol and are written attached
("kilogram", "kg"); a space between a prefix and its unit is not standard
SI. This rule rescues the common spoken form "kilo gram" behind an opt-in
contract flag: it merges the word prefix to the prefixed symbol ("kg") only
when ``allow_split_word_prefixes`` is set, and is otherwise dropped by the
engine's feature gate (→ INVALID). Symbol-prefix spacing ("k g") is handled
by the grammar (the trailing unit is subsumed into one span) and rejected
implicitly — a prefix symbol must bind tightly with no space, and collapsing
it would corrupt dimensionality (e.g. "m m" ≠ "mm").
"""

from __future__ import annotations

import re

from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.capabilities.SIUnit.rules.data.prefixed_unit_names import (
    PREFIXED_NAME_TO_SYMBOL,
)
from paxman.capabilities.SIUnit.rules.data.unit_names import NAME_TO_SYMBOL
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

# Full name→symbol resolution (maintained official names + generated prefixed
# names). "kilogram" -> "kg", "megahertz" -> "MHz".
FULL_NAME_TO_SYMBOL = NAME_TO_SYMBOL | PREFIXED_NAME_TO_SYMBOL

PUBLICATION = Provenance(
    authority="BIPM",
    specification_name="SI Brochure: The International System of Units (SI)",
    kind="specification",
    reference_url="https://www.bipm.org/en/publications/si-brochure",
    version="9th edition",
    lifecycle="active",
    publication_year=2019,
)

_WHITESPACE = re.compile(r"\s+")


class SectionSplitWordPrefixes(Rule[SIUnitNotation]):
    """BIPM SI Brochure §3.2 — a word prefix split from its unit by whitespace.

    When the contract opts in via ``allow_split_word_prefixes``, a
    ``split_word_prefix`` notation ("kilo gram") merges to its attached
    prefixed symbol ("kg"). The rule declares ``requires_features`` so the
    engine drops it entirely when the flag is off, leaving the recognition
    unvalidated (→ INVALID) by Paxman's standard idiom.
    """

    name = "Section 3.2-split-word-prefixes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = (
        "BIPM SI Brochure (9th ed., 2019), §3.2 (prefixes attached to unit names)"
    )
    target_semantics = frozenset({"name_recognition"})
    requires_features = frozenset({"allow_split_word_prefixes"})

    def matches(self, notation: SIUnitNotation, contract: Contract) -> bool:
        """Accept a merged word-prefix notation when the flag is on."""
        if notation.shape != "split_word_prefix":
            return False
        merged = _WHITESPACE.sub("", notation.text)
        return merged in FULL_NAME_TO_SYMBOL

    def normalize(self, notation: SIUnitNotation, contract: Contract) -> str:
        """Render the attached prefixed symbol ("kilo gram" -> "kg")."""
        return FULL_NAME_TO_SYMBOL[_WHITESPACE.sub("", notation.text)]
