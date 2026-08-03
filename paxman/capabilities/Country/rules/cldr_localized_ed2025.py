"""CLDR v45 localized country name validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.data.cldr_ed2025 import LOCALIZED_TO_ALPHA2
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="Unicode",
    specification_name="CLDR v45",
    kind="registry",
    reference_url="https://cldr.unicode.org/",
    version="45",
    lifecycle="active",
    publication_year=2025,
)


class SectionLocalizedNames(Rule[CountryNotation]):
    """CLDR v45 Section: localized country names.

    Validates name shape against curated multilingual names (zh, es, fr).
    Activation is engine-owned: the engine runs this rule only when the
    contract enables ``include_localized``, via ``Rule.requires_features``.
    """

    name = "Section-localized-names"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "CLDR v45 localized country names"
    target_grammars = frozenset({"name_recognition"})
    requires_features = frozenset({"include_localized"})

    def matches(self, notation: CountryNotation, contract: Contract) -> bool:
        """Check if notation is a valid localized name.

        Validates notation/table membership only. Whether the rule runs at
        all is decided by the engine from ``requires_features``.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "name" AND name is in
            LOCALIZED_TO_ALPHA2.
        """
        if notation.shape != "name":
            return False
        return notation.value in LOCALIZED_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: Contract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code.
        """
        return LOCALIZED_TO_ALPHA2[notation.value]
