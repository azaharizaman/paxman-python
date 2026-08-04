"""Recognition-to-rule data consistency for the Country name grammar.

Every name representation the Country name grammar recognizes must be
backed by at least one authority rule-data mapping. If a recognition key
had no rule-data mapping, the grammar could emit a notation that no
validation rule can resolve — a pipeline dead end (MISSING/INVALID) for
an input the grammar explicitly claims to understand.

The assertion is deliberately one-directional: recognition keys must be a
subset of the union of rule-data keys. Rule data may contain additional
round-trip and lookup-only keys (e.g., official-name spellings whose ASCII
form is a grammar alias) that no recognition key targets.

Each locale's keys are additionally asserted against its owning authority
table, matching data ownership: ISO 3166-1 owns English names, ISO 3166-3
owns former names, and CLDR owns localized (Chinese, Spanish, French) names.
"""

from __future__ import annotations

import pytest

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
from paxman.capabilities.Country.name_normalization import normalize_name
from paxman.capabilities.Country.rules.data.cldr_ed2025 import (
    LOCALIZED_TO_ALPHA2,
)
from paxman.capabilities.Country.rules.data.iso_3166_ed2020_part3 import (
    FORMER_NAME_TO_ALPHA2,
)
from paxman.capabilities.Country.rules.data.iso_3166_ed2024 import (
    NAME_TO_ALPHA2,
    SYNONYM_TO_ALPHA2,
)

pytestmark = [pytest.mark.capability, pytest.mark.country]


def _normalized_keys(mapping: dict[str, str]) -> set[str]:
    """Normalize a rule-data mapping's keys with the shared normalizer.

    Recognition key sets are normalized at module construction; rule-data
    maps carry raw spellings, so both sides are compared in the same
    normalized key space.
    """
    return {normalize_name(key) for key in mapping}


def _uncovered_report(uncovered: list[str]) -> str:
    """Build a sorted, readable failure report for uncovered keys."""
    lines = ["Recognition keys with no backing rule-data mapping:"]
    lines.extend(f"  - {key}" for key in uncovered)
    return "\n".join(lines)


class TestRecognitionKeysAreRuleDataCovered:
    """Recognition key sets must be covered by authority rule-data maps."""

    def test_every_recognition_key_has_rule_data_mapping(self) -> None:
        """Union of recognition keys is covered by the union of rule maps."""
        recognized = (
            ENGLISH_NAME_KEYS
            | HISTORICAL_NAME_KEYS
            | CHINESE_NAME_KEYS
            | LOCALIZED_NAME_KEYS
        )
        rule_data = (
            _normalized_keys(NAME_TO_ALPHA2)
            | _normalized_keys(SYNONYM_TO_ALPHA2)
            | _normalized_keys(FORMER_NAME_TO_ALPHA2)
            | _normalized_keys(LOCALIZED_TO_ALPHA2)
        )
        uncovered = sorted(recognized - rule_data)
        assert not uncovered, _uncovered_report(uncovered)

    def test_every_english_key_has_iso_rule_data(self) -> None:
        """English recognition keys are covered by ISO 3166-1 tables."""
        iso_keys = _normalized_keys(NAME_TO_ALPHA2) | _normalized_keys(
            SYNONYM_TO_ALPHA2
        )
        uncovered = sorted(ENGLISH_NAME_KEYS - iso_keys)
        assert not uncovered, _uncovered_report(uncovered)

    def test_every_historical_key_has_iso3166_3_rule_data(self) -> None:
        """Historical recognition keys are covered by ISO 3166-3 former names."""
        uncovered = sorted(
            HISTORICAL_NAME_KEYS - _normalized_keys(FORMER_NAME_TO_ALPHA2)
        )
        assert not uncovered, _uncovered_report(uncovered)

    def test_every_chinese_key_has_cldr_rule_data(self) -> None:
        """Chinese recognition keys are covered by the CLDR localized table."""
        uncovered = sorted(CHINESE_NAME_KEYS - _normalized_keys(LOCALIZED_TO_ALPHA2))
        assert not uncovered, _uncovered_report(uncovered)

    def test_every_localized_key_has_cldr_rule_data(self) -> None:
        """Localized recognition keys are covered by the CLDR localized table."""
        uncovered = sorted(LOCALIZED_NAME_KEYS - _normalized_keys(LOCALIZED_TO_ALPHA2))
        assert not uncovered, _uncovered_report(uncovered)
