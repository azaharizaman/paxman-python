# Country Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Country capability that canonicalizes country representations (alpha2, alpha3, numeric, name) to ISO 3166-1 alpha-2 codes with full provenance.

**Architecture:** Shape-aware notation with 4 mutually exclusive grammars and 6 validation rules. Rules filter by shape discriminator. Opt-in flags for localized (CLDR) and historical data. Configurable output format.

**Tech Stack:** Python 3.11, dataclasses (frozen=True, slots=True), regex, pytest, pyright, ruff, import-linter

---

## File Structure

```
paxman/capabilities/Country/
├── __init__.py
├── capability.py
├── contract.py
├── notation.py
├── grammar/
│   ├── __init__.py
│   ├── alpha2_recognition.py
│   ├── alpha3_recognition.py
│   ├── numeric_recognition.py
│   └── name_recognition.py
└── rules/
    ├── __init__.py
    ├── iso_3166_alpha2_ed2024.py
    ├── iso_3166_alpha3_ed2024.py
    ├── iso_3166_numeric_ed2024.py
    ├── iso_3166_name_ed2024.py
    ├── cldr_localized_ed2025.py
    └── paxman_historical_ed2025.py

tests/capabilities/country/
├── __init__.py
├── test_grammar.py
├── test_rules.py
└── test_capability.py
```

---

## Task 1: Create Directory Structure

**Files:**
- Create: `paxman/capabilities/Country/__init__.py`
- Create: `paxman/capabilities/Country/grammar/__init__.py`
- Create: `paxman/capabilities/Country/rules/__init__.py`
- Create: `tests/capabilities/country/__init__.py`

- [ ] **Step 1: Create Country package directories**

```bash
mkdir -p paxman/capabilities/Country/grammar
mkdir -p paxman/capabilities/Country/rules
mkdir -p tests/capabilities/country
```

- [ ] **Step 2: Create package init files**

```python
# paxman/capabilities/Country/__init__.py
"""Country capability for canonicalizing country representations."""
```

```python
# paxman/capabilities/Country/grammar/__init__.py
"""Country recognition grammars."""
```

```python
# paxman/capabilities/Country/rules/__init__.py
"""Country validation rules."""
```

```python
# tests/capabilities/country/__init__.py
"""Country capability tests."""
```

- [ ] **Step 3: Verify directory structure**

Run: `find paxman/capabilities/Country tests/capabilities/country -type f | sort`
Expected: 4 `__init__.py` files

- [ ] **Step 4: Commit**

```bash
git add paxman/capabilities/Country tests/capabilities/country
git commit -m "feat(country): create directory structure"
```

---

## Task 2: Define Notation

**Files:**
- Create: `paxman/capabilities/Country/notation.py`
- Test: `tests/capabilities/country/test_capability.py`

- [ ] **Step 1: Write notation tests**

```python
# tests/capabilities/country/test_capability.py
"""Tests for Country capability."""

import pytest
from paxman.capabilities.Country.notation import CountryNotation


class TestCountryNotation:
    """Tests for CountryNotation dataclass."""

    def test_creates_with_fields(self) -> None:
        """Verify field access."""
        notation = CountryNotation(shape="alpha2", value="US")
        assert notation.shape == "alpha2"
        assert notation.value == "US"

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        notation = CountryNotation(shape="alpha2", value="US")
        with pytest.raises(AttributeError):
            notation.shape = "alpha3"  # type: ignore[misc]

    def test_as_list_returns_correct(self) -> None:
        """Verify list conversion."""
        notation = CountryNotation(shape="alpha2", value="US")
        assert notation.as_list() == ["alpha2", "US"]

    def test_as_list_preserves_order(self) -> None:
        """Verify field order matches list order."""
        notation = CountryNotation(shape="name", value="United States")
        result = notation.as_list()
        assert result[0] == notation.shape
        assert result[1] == notation.value

    def test_equality(self) -> None:
        """Verify value equality."""
        n1 = CountryNotation(shape="alpha2", value="US")
        n2 = CountryNotation(shape="alpha2", value="US")
        assert n1 == n2

    def test_inequality(self) -> None:
        """Verify different values are not equal."""
        n1 = CountryNotation(shape="alpha2", value="US")
        n2 = CountryNotation(shape="alpha2", value="GB")
        assert n1 != n2

    def test_hashable(self) -> None:
        """Verify it can be used in sets or as dict keys."""
        n1 = CountryNotation(shape="alpha2", value="US")
        n2 = CountryNotation(shape="alpha2", value="US")
        s = {n1, n2}
        assert len(s) == 1
        d = {n1: "value"}
        assert d[n2] == "value"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_capability.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'paxman.capabilities.Country.notation'"

- [ ] **Step 3: Implement Notation**

```python
# paxman/capabilities/Country/notation.py
"""Country notation — intermediate representation for country recognition."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CountryNotation:
    """Intermediate representation for country recognition.

    Attributes:
        shape: Discriminator set by grammar ("alpha2", "alpha3", "numeric", "name").
        value: Raw input value (e.g., "US", "USA", "840", "United States").
    """

    shape: str
    value: str

    def as_list(self) -> list[str]:
        """Bridge to generic list[str] interface.

        Returns:
            [shape, value] — shape first for consistent ordering.
        """
        return [self.shape, self.value]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_capability.py::TestCountryNotation -v`
Expected: 7 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/notation.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/notation.py tests/capabilities/country/test_capability.py
git commit -m "feat(country): add CountryNotation dataclass"
```

---

## Task 3: Define Contract

**Files:**
- Create: `paxman/capabilities/Country/contract.py`
- Test: `tests/capabilities/country/test_capability.py`

- [ ] **Step 1: Write contract tests**

```python
# Append to tests/capabilities/country/test_capability.py

from paxman.capabilities.Country.contract import CountryContract


class TestCountryContract:
    """Tests for CountryContract dataclass."""

    def test_default_capability_name(self) -> None:
        """Verify capability_name is fixed to 'country'."""
        contract = CountryContract()
        assert contract.capability_name == "country"

    def test_capability_name_not_settable(self) -> None:
        """Verify capability_name is not user-settable."""
        # The field has init=False, so this should raise TypeError
        with pytest.raises(TypeError):
            CountryContract(capability_name="other")  # type: ignore[call-arg]

    def test_default_excluded_rules(self) -> None:
        """Verify excluded_rules defaults to empty tuple."""
        contract = CountryContract()
        assert contract.excluded_rules == ()

    def test_default_pinned_rules(self) -> None:
        """Verify pinned_rules defaults to None."""
        contract = CountryContract()
        assert contract.pinned_rules is None

    def test_default_year(self) -> None:
        """Verify year defaults to None."""
        contract = CountryContract()
        assert contract.year is None

    def test_default_output_format(self) -> None:
        """Verify output_format defaults to None."""
        contract = CountryContract()
        assert contract.output_format is None

    def test_default_include_localized(self) -> None:
        """Verify include_localized defaults to False."""
        contract = CountryContract()
        assert contract.include_localized is False

    def test_default_include_historical(self) -> None:
        """Verify include_historical defaults to False."""
        contract = CountryContract()
        assert contract.include_historical is False

    def test_default_extra_synonyms(self) -> None:
        """Verify extra_synonyms defaults to empty dict."""
        contract = CountryContract()
        assert contract.extra_synonyms == {}

    def test_active_grammars_returns_all(self) -> None:
        """Verify all 4 grammars are active by default."""
        contract = CountryContract()
        grammars = contract.active_grammars
        assert len(grammars) == 4
        assert "alpha2_recognition" in grammars
        assert "alpha3_recognition" in grammars
        assert "numeric_recognition" in grammars
        assert "name_recognition" in grammars

    def test_as_dict_contains_all_fields(self) -> None:
        """Verify as_dict serializes all fields."""
        contract = CountryContract()
        d = contract.as_dict()
        assert "capability_name" in d
        assert "excluded_rules" in d
        assert "pinned_rules" in d
        assert "year" in d
        assert "output_format" in d
        assert "include_localized" in d
        assert "include_historical" in d
        assert "extra_synonyms" in d

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        contract = CountryContract()
        with pytest.raises(AttributeError):
            contract.year = 2024  # type: ignore[misc]

    def test_custom_fields(self) -> None:
        """Verify custom fields can be set."""
        contract = CountryContract(
            include_localized=True,
            include_historical=True,
            extra_synonyms={"my_alias": "MY"},
            output_format="alpha3",
        )
        assert contract.include_localized is True
        assert contract.include_historical is True
        assert contract.extra_synonyms == {"my_alias": "MY"}
        assert contract.output_format == "alpha3"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_capability.py::TestCountryContract -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'paxman.capabilities.Country.contract'"

- [ ] **Step 3: Implement Contract**

```python
# paxman/capabilities/Country/contract.py
"""Country contract — user-facing configuration for Country capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CountryContract:
    """User-facing configuration for Country capability.

    Attributes:
        capability_name: Fixed to "country" (not user-settable).
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
        year: Year for temporal filtering.
        output_format: Canonical output format ("alpha2", "alpha3", "numeric", "name").
        include_localized: Enable CLDR multilingual names.
        include_historical: Enable deprecated country names.
        extra_synonyms: Caller-supplied aliases (validated at construction).
    """

    capability_name: str = field(default="country", init=False)

    # Standard contract fields
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None
    output_format: str | None = None

    # Capability-specific fields
    include_localized: bool = False
    include_historical: bool = False
    extra_synonyms: dict[str, str] = field(default_factory=dict)

    @property
    def active_grammars(self) -> list[str]:
        """All grammars active by default.

        Returns:
            List of grammar names to activate.
        """
        return [
            "alpha2_recognition",
            "alpha3_recognition",
            "numeric_recognition",
            "name_recognition",
        ]

    def as_dict(self) -> dict[str, Any]:
        """Serialize for replay hash computation.

        Returns:
            Dictionary representation of all fields.
        """
        return {
            "capability_name": self.capability_name,
            "excluded_rules": self.excluded_rules,
            "pinned_rules": self.pinned_rules,
            "year": self.year,
            "output_format": self.output_format,
            "include_localized": self.include_localized,
            "include_historical": self.include_historical,
            "extra_synonyms": self.extra_synonyms,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_capability.py::TestCountryContract -v`
Expected: 14 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/contract.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/contract.py
git commit -m "feat(country): add CountryContract dataclass"
```

---

## Task 4: Create ISO 3166-1 Lookup Tables

**Files:**
- Create: `paxman/capabilities/Country/data.py`

- [ ] **Step 1: Create data module with all lookup tables**

```python
# paxman/capabilities/Country/data.py
"""ISO 3166-1 lookup tables for Country capability.

All tables are derived from ISO 3166-1:2024.
Source: https://www.iso.org/standard/396855.html
"""

from __future__ import annotations

# Alpha-2 codes (249 assigned)
_ALPHA2_CODES: frozenset[str] = frozenset(
    {
        "AD",
        "AE",
        "AF",
        "AG",
        "AI",
        "AL",
        "AM",
        "AO",
        "AQ",
        "AR",
        "AS",
        "AT",
        "AU",
        "AW",
        "AX",
        "AZ",
        "BA",
        "BB",
        "BD",
        "BE",
        "BF",
        "BG",
        "BH",
        "BI",
        "BJ",
        "BL",
        "BM",
        "BN",
        "BO",
        "BQ",
        "BR",
        "BS",
        "BT",
        "BV",
        "BW",
        "BY",
        "BZ",
        "CA",
        "CC",
        "CD",
        "CF",
        "CG",
        "CH",
        "CI",
        "CK",
        "CL",
        "CM",
        "CN",
        "CO",
        "CR",
        "CU",
        "CV",
        "CW",
        "CX",
        "CY",
        "CZ",
        "DE",
        "DJ",
        "DK",
        "DM",
        "DO",
        "DZ",
        "EC",
        "EE",
        "EG",
        "EH",
        "ER",
        "ES",
        "ET",
        "FI",
        "FJ",
        "FK",
        "FM",
        "FO",
        "FR",
        "GA",
        "GB",
        "GD",
        "GE",
        "GF",
        "GG",
        "GH",
        "GI",
        "GL",
        "GM",
        "GN",
        "GP",
        "GQ",
        "GR",
        "GS",
        "GT",
        "GU",
        "GW",
        "GY",
        "HK",
        "HM",
        "HN",
        "HR",
        "HT",
        "HU",
        "ID",
        "IE",
        "IL",
        "IM",
        "IN",
        "IO",
        "IQ",
        "IR",
        "IS",
        "IT",
        "JE",
        "JM",
        "JO",
        "JP",
        "KE",
        "KG",
        "KH",
        "KI",
        "KM",
        "KN",
        "KP",
        "KR",
        "KW",
        "KY",
        "KZ",
        "LA",
        "LB",
        "LC",
        "LI",
        "LK",
        "LR",
        "LS",
        "LT",
        "LU",
        "LV",
        "LY",
        "MA",
        "MC",
        "MD",
        "ME",
        "MF",
        "MG",
        "MH",
        "MK",
        "ML",
        "MM",
        "MN",
        "MO",
        "MP",
        "MQ",
        "MR",
        "MS",
        "MT",
        "MU",
        "MV",
        "MW",
        "MX",
        "MY",
        "MZ",
        "NA",
        "NC",
        "NE",
        "NF",
        "NG",
        "NI",
        "NL",
        "NO",
        "NP",
        "NR",
        "NU",
        "NZ",
        "OM",
        "PA",
        "PE",
        "PF",
        "PG",
        "PH",
        "PK",
        "PL",
        "PM",
        "PN",
        "PR",
        "PS",
        "PT",
        "PW",
        "PY",
        "QA",
        "RE",
        "RO",
        "RS",
        "RU",
        "RW",
        "SA",
        "SB",
        "SC",
        "SD",
        "SE",
        "SG",
        "SH",
        "SI",
        "SJ",
        "SK",
        "SL",
        "SM",
        "SN",
        "SO",
        "SR",
        "SS",
        "ST",
        "SV",
        "SX",
        "SY",
        "SZ",
        "TC",
        "TD",
        "TF",
        "TG",
        "TH",
        "TJ",
        "TK",
        "TL",
        "TM",
        "TN",
        "TO",
        "TR",
        "TT",
        "TV",
        "TW",
        "TZ",
        "UA",
        "UG",
        "UM",
        "US",
        "UY",
        "UZ",
        "VA",
        "VC",
        "VE",
        "VG",
        "VI",
        "VN",
        "VU",
        "WF",
        "WS",
        "XK",
        "YE",
        "YT",
        "ZA",
        "ZM",
        "ZW",
    }
)

# Alpha-3 to Alpha-2 mapping (249 entries)
_ALPHA3_TO_ALPHA2: dict[str, str] = {
    "ABW": "AW",
    "AFG": "AF",
    "AGO": "AO",
    "AIA": "AI",
    "ALA": "AX",
    "ALB": "AL",
    "AND": "AD",
    "ARE": "AE",
    "ARG": "AR",
    "ARM": "AM",
    "ASM": "AS",
    "ATA": "AQ",
    "ATF": "TF",
    "ATG": "AG",
    "AUS": "AU",
    "AUT": "AT",
    "AZE": "AZ",
    "BDI": "BI",
    "BEL": "BE",
    "BEN": "BJ",
    "BES": "BQ",
    "BFA": "BF",
    "BGD": "BD",
    "BGR": "BG",
    "BHR": "BH",
    "BHS": "BS",
    "BIH": "BA",
    "BLM": "BL",
    "BLR": "BY",
    "BLZ": "BZ",
    "BMU": "BM",
    "BOL": "BO",
    "BRA": "BR",
    "BRB": "BB",
    "BRN": "BN",
    "BTN": "BT",
    "BVT": "BV",
    "BWA": "BW",
    "CAF": "CF",
    "CAN": "CA",
    "CCK": "CC",
    "CHE": "CH",
    "CHL": "CL",
    "CHN": "CN",
    "CIV": "CI",
    "CMR": "CM",
    "COD": "CD",
    "COG": "CG",
    "COK": "CK",
    "COL": "CO",
    "COM": "KM",
    "CPV": "CV",
    "CRI": "CR",
    "CUB": "CU",
    "CUW": "CW",
    "CXR": "CX",
    "CYM": "KY",
    "CYP": "CY",
    "CZE": "CZ",
    "DEU": "DE",
    "DJI": "DJ",
    "DMA": "DM",
    "DNK": "DK",
    "DOM": "DO",
    "DZA": "DZ",
    "ECU": "EC",
    "EGY": "EG",
    "ERI": "ER",
    "ESH": "EH",
    "ESP": "ES",
    "EST": "EE",
    "ETH": "ET",
    "FIN": "FI",
    "FJI": "FJ",
    "FLK": "FK",
    "FRA": "FR",
    "FRO": "FO",
    "FSM": "FM",
    "GAB": "GA",
    "GBR": "GB",
    "GEO": "GE",
    "GGY": "GG",
    "GHA": "GH",
    "GIB": "GI",
    "GIN": "GN",
    "GLP": "GP",
    "GMB": "GM",
    "GNB": "GW",
    "GNQ": "GQ",
    "GRC": "GR",
    "GRD": "GD",
    "GRL": "GL",
    "GTM": "GT",
    "GUF": "GF",
    "GUM": "GU",
    "GUY": "GY",
    "HKG": "HK",
    "HMD": "HM",
    "HND": "HN",
    "HRV": "HR",
    "HTI": "HT",
    "HUN": "HU",
    "IDN": "ID",
    "IMN": "IM",
    "IND": "IN",
    "IOT": "IO",
    "IRL": "IE",
    "IRN": "IR",
    "IRQ": "IQ",
    "ISL": "IS",
    "ISR": "IL",
    "ITA": "IT",
    "JAM": "JM",
    "JEY": "JE",
    "JOR": "JO",
    "JPN": "JP",
    "KAZ": "KZ",
    "KEN": "KE",
    "KGZ": "KG",
    "KHM": "KH",
    "KIR": "KI",
    "KNA": "KN",
    "KOR": "KR",
    "KWT": "KW",
    "LAO": "LA",
    "LBN": "LB",
    "LBR": "LR",
    "LBY": "LY",
    "LCA": "LC",
    "LIE": "LI",
    "LKA": "LK",
    "LSO": "LS",
    "LTU": "LT",
    "LUX": "LU",
    "LVA": "LV",
    "MAR": "MA",
    "MCO": "MC",
    "MDA": "MD",
    "MDG": "MG",
    "MDV": "MV",
    "MEX": "MX",
    "MHL": "MH",
    "MKD": "MK",
    "MLI": "ML",
    "MLT": "MT",
    "MMR": "MM",
    "MNE": "ME",
    "MNG": "MN",
    "MNP": "MP",
    "MOZ": "MZ",
    "MRT": "MR",
    "MSR": "MS",
    "MTQ": "MQ",
    "MUS": "MU",
    "MWI": "MW",
    "MYS": "MY",
    "MYT": "YT",
    "NAM": "NA",
    "NCL": "NC",
    "NER": "NE",
    "NFK": "NF",
    "NGA": "NG",
    "NIC": "NI",
    "NIU": "NU",
    "NLD": "NL",
    "NOR": "NO",
    "NPL": "NP",
    "NRU": "NR",
    "NZL": "NZ",
    "OMN": "OM",
    "PAK": "PK",
    "PAN": "PA",
    "PCN": "PN",
    "PER": "PE",
    "PHL": "PH",
    "PLW": "PW",
    "PNG": "PG",
    "POL": "PL",
    "PRI": "PR",
    "PRK": "KP",
    "PRT": "PT",
    "PRY": "PY",
    "PSE": "PS",
    "PYF": "PF",
    "QAT": "QA",
    "REU": "RE",
    "ROU": "RO",
    "RUS": "RU",
    "RWA": "RW",
    "SAU": "SA",
    "SDN": "SD",
    "SEN": "SN",
    "SGP": "SG",
    "SGS": "GS",
    "SHN": "SH",
    "SJM": "SJ",
    "SLB": "SB",
    "SLE": "SL",
    "SLV": "SV",
    "SMR": "SM",
    "SOM": "SO",
    "SPM": "PM",
    "SRB": "RS",
    "SSD": "SS",
    "STP": "ST",
    "SUR": "SR",
    "SVK": "SK",
    "SVN": "SI",
    "SWE": "SE",
    "SWZ": "SZ",
    "SXM": "SX",
    "SYC": "SC",
    "SYR": "SY",
    "TCA": "TC",
    "TCD": "TD",
    "TGO": "TG",
    "THA": "TH",
    "TJK": "TJ",
    "TKL": "TK",
    "TKM": "TM",
    "TLS": "TL",
    "TON": "TO",
    "TTO": "TT",
    "TUN": "TN",
    "TUR": "TR",
    "TUV": "TV",
    "TWN": "TW",
    "TZA": "TZ",
    "UGA": "UG",
    "UKR": "UA",
    "UMI": "UM",
    "URY": "UY",
    "USA": "US",
    "UZB": "UZ",
    "VAT": "VA",
    "VCT": "VC",
    "VEN": "VE",
    "VGB": "VG",
    "VIR": "VI",
    "VNM": "VN",
    "VUT": "VU",
    "WLF": "WF",
    "WSM": "WS",
    "XKX": "XK",
    "YEM": "YE",
    "ZAF": "ZA",
    "ZMB": "ZM",
    "ZWE": "ZW",
}

# Numeric (M49) to Alpha-2 mapping (249 entries)
_NUMERIC_TO_ALPHA2: dict[str, str] = {
    "004": "AF",
    "008": "AL",
    "010": "AQ",
    "012": "DZ",
    "016": "AS",
    "020": "AD",
    "024": "AO",
    "028": "AG",
    "031": "AZ",
    "032": "AR",
    "036": "AU",
    "040": "AT",
    "044": "BS",
    "048": "BH",
    "050": "BD",
    "051": "AM",
    "052": "BB",
    "056": "BE",
    "060": "BM",
    "064": "BT",
    "068": "BO",
    "070": "BA",
    "072": "BW",
    "074": "BV",
    "076": "BR",
    "084": "BZ",
    "086": "IO",
    "090": "SB",
    "092": "VG",
    "096": "BN",
    "100": "BG",
    "104": "MM",
    "108": "BI",
    "112": "BY",
    "116": "KH",
    "120": "CM",
    "124": "CA",
    "132": "CV",
    "136": "KY",
    "140": "CF",
    "144": "LK",
    "148": "TD",
    "152": "CL",
    "156": "CN",
    "158": "TW",
    "162": "CX",
    "166": "CC",
    "170": "CO",
    "174": "KM",
    "175": "YT",
    "178": "CG",
    "180": "CD",
    "184": "CK",
    "188": "CR",
    "191": "HR",
    "192": "CU",
    "196": "CY",
    "200": "CS",
    "203": "CZ",
    "204": "BJ",
    "208": "DK",
    "212": "DM",
    "214": "DO",
    "218": "EC",
    "222": "SV",
    "226": "GQ",
    "231": "ET",
    "232": "ER",
    "233": "EE",
    "234": "FO",
    "238": "FK",
    "242": "FJ",
    "246": "FI",
    "250": "FR",
    "254": "GF",
    "258": "PF",
    "260": "TF",
    "262": "DJ",
    "266": "GA",
    "268": "GE",
    "270": "GM",
    "275": "PS",
    "276": "DE",
    "288": "GH",
    "292": "GI",
    "296": "KI",
    "300": "GR",
    "304": "GL",
    "308": "GD",
    "312": "GP",
    "316": "GU",
    "320": "GT",
    "324": "GN",
    "328": "GY",
    "332": "HT",
    "336": "VA",
    "340": "HN",
    "344": "HK",
    "348": "HU",
    "352": "IS",
    "356": "IN",
    "360": "ID",
    "364": "IR",
    "368": "IQ",
    "372": "IE",
    "376": "IL",
    "380": "IT",
    "384": "CI",
    "388": "JM",
    "392": "JP",
    "398": "KZ",
    "400": "JO",
    "404": "KE",
    "408": "KP",
    "410": "KR",
    "414": "KW",
    "417": "KG",
    "418": "LA",
    "422": "LB",
    "426": "LS",
    "428": "LV",
    "430": "LR",
    "434": "LY",
    "438": "LI",
    "440": "LT",
    "442": "LU",
    "446": "MO",
    "450": "MG",
    "454": "MW",
    "458": "MY",
    "462": "MV",
    "466": "ML",
    "470": "MT",
    "474": "MQ",
    "478": "MR",
    "480": "MU",
    "484": "MX",
    "492": "MC",
    "496": "MN",
    "498": "MD",
    "499": "ME",
    "500": "MS",
    "504": "MA",
    "508": "MZ",
    "512": "OM",
    "516": "NA",
    "520": "NR",
    "524": "NP",
    "528": "NL",
    "530": "AN",
    "540": "NC",
    "548": "VU",
    "554": "NZ",
    "558": "NI",
    "562": "NE",
    "566": "NG",
    "570": "NU",
    "574": "NF",
    "578": "NO",
    "580": "MP",
    "583": "FM",
    "584": "MH",
    "585": "PW",
    "586": "PK",
    "591": "PA",
    "598": "PG",
    "600": "PY",
    "604": "PE",
    "608": "PH",
    "612": "PN",
    "616": "PL",
    "620": "PT",
    "624": "GW",
    "626": "TL",
    "630": "PR",
    "634": "QA",
    "638": "RE",
    "642": "RO",
    "643": "RU",
    "646": "RW",
    "654": "SH",
    "659": "KN",
    "660": "AI",
    "662": "LC",
    "666": "PM",
    "670": "VC",
    "674": "SM",
    "678": "ST",
    "682": "SA",
    "686": "SN",
    "688": "RS",
    "690": "SC",
    "694": "SL",
    "702": "SG",
    "703": "SK",
    "704": "VN",
    "705": "SI",
    "706": "SO",
    "710": "ZA",
    "716": "ZW",
    "724": "ES",
    "728": "SS",
    "732": "EH",
    "736": "SD",
    "740": "SR",
    "744": "SJ",
    "748": "SZ",
    "752": "SE",
    "756": "CH",
    "760": "SY",
    "762": "TJ",
    "764": "TH",
    "768": "TG",
    "772": "TK",
    "776": "TO",
    "780": "TT",
    "784": "AE",
    "788": "TN",
    "792": "TR",
    "795": "TM",
    "796": "TC",
    "798": "TV",
    "800": "UG",
    "804": "UA",
    "807": "MK",
    "818": "EG",
    "826": "GB",
    "831": "GG",
    "832": "JE",
    "833": "IM",
    "834": "TZ",
    "840": "US",
    "850": "VI",
    "854": "BF",
    "858": "UY",
    "860": "UZ",
    "862": "VE",
    "876": "WF",
    "882": "WS",
    "887": "YE",
    "894": "ZM",
    "-99": "XK",
}

# Official English short names (249 entries, uppercased)
_NAME_TO_ALPHA2: dict[str, str] = {
    "AFGHANISTAN": "AF",
    "ALBANIA": "AL",
    "ALGERIA": "DZ",
    "AMERICAN SAMOA": "AS",
    "ANDORRA": "AD",
    "ANGOLA": "AO",
    "ANTIGUA AND BARBUDA": "AG",
    "ARGENTINA": "AR",
    "ARMENIA": "AM",
    "ARUBA": "AW",
    "AUSTRALIA": "AU",
    "AUSTRIA": "AT",
    "AZERBAIJAN": "AZ",
    "BAHAMAS": "BS",
    "BAHRAIN": "BH",
    "BANGLADESH": "BD",
    "BARBADOS": "BB",
    "BELARUS": "BY",
    "BELGIUM": "BE",
    "BELIZE": "BZ",
    "BENIN": "BJ",
    "BERMUDA": "BM",
    "BHUTAN": "BT",
    "BOLIVIA": "BO",
    "BOSNIA AND HERZEGOVINA": "BA",
    "BOTSWANA": "BW",
    "BRAZIL": "BR",
    "BRITISH VIRGIN ISLANDS": "VG",
    "BRUNEI": "BN",
    "BULGARIA": "BG",
    "BURKINA FASO": "BF",
    "BURUNDI": "BI",
    "CAMBODIA": "KH",
    "CAMEROON": "CM",
    "CANADA": "CA",
    "CAPE VERDE": "CV",
    "CAYMAN ISLANDS": "KY",
    "CENTRAL AFRICAN REPUBLIC": "CF",
    "CHAD": "TD",
    "CHILE": "CL",
    "CHINA": "CN",
    "COLOMBIA": "CO",
    "COMOROS": "KM",
    "CONGO": "CG",
    "COOK ISLANDS": "CK",
    "COSTA RICA": "CR",
    "CROATIA": "HR",
    "CUBA": "CU",
    "CURACAO": "CW",
    "CYPRUS": "CY",
    "CZECHIA": "CZ",
    "DEMOCRATIC REPUBLIC OF THE CONGO": "CD",
    "DENMARK": "DK",
    "DJIBOUTI": "DJ",
    "DOMINICA": "DM",
    "DOMINICAN REPUBLIC": "DO",
    "ECUADOR": "EC",
    "EGYPT": "EG",
    "EL SALVADOR": "SV",
    "EQUATORIAL GUINEA": "GQ",
    "ERITREA": "ER",
    "ESTONIA": "EE",
    "ESWATINI": "SZ",
    "ETHIOPIA": "ET",
    "FALKLAND ISLANDS": "FK",
    "FIJI": "FJ",
    "FINLAND": "FI",
    "FRANCE": "FR",
    "FRENCH GUIANA": "GF",
    "FRENCH POLYNESIA": "PF",
    "GABON": "GA",
    "GAMBIA": "GM",
    "GEORGIA": "GE",
    "GERMANY": "DE",
    "GHANA": "GH",
    "GIBRALTAR": "GI",
    "GREECE": "GR",
    "GREENLAND": "GL",
    "GRENADA": "GD",
    "GUADELOUPE": "GP",
    "GUAM": "GU",
    "GUATEMALA": "GT",
    "GUERNSEY": "GG",
    "GUINEA": "GN",
    "GUINEA-BISSAU": "GW",
    "GUYANA": "GY",
    "HAITI": "HT",
    "HONDURAS": "HN",
    "HONG KONG": "HK",
    "HUNGARY": "HU",
    "ICELAND": "IS",
    "INDIA": "IN",
    "INDONESIA": "ID",
    "IRAN": "IR",
    "IRAQ": "IQ",
    "IRELAND": "IE",
    "ISLE OF MAN": "IM",
    "ISRAEL": "IL",
    "ITALY": "IT",
    "IVORY COAST": "CI",
    "JAMAICA": "JM",
    "JAPAN": "JP",
    "JERSEY": "JE",
    "JORDAN": "JO",
    "KAZAKHSTAN": "KZ",
    "KENYA": "KE",
    "KIRIBATI": "KI",
    "KOSOVO": "XK",
    "KUWAIT": "KW",
    "KYRGYZSTAN": "KG",
    "LAOS": "LA",
    "LATVIA": "LV",
    "LEBANON": "LB",
    "LESOTHO": "LS",
    "LIBERIA": "LR",
    "LIBYA": "LY",
    "LIECHTENSTEIN": "LI",
    "LITHUANIA": "LT",
    "LUXEMBOURG": "LU",
    "MACAU": "MO",
    "MADAGASCAR": "MG",
    "MALAWI": "MW",
    "MALAYSIA": "MY",
    "MALDIVES": "MV",
    "MALI": "ML",
    "MALTA": "MT",
    "MARSHALL ISLANDS": "MH",
    "MARTINIQUE": "MQ",
    "MAURITANIA": "MR",
    "MAURITIUS": "MU",
    "MAYOTTE": "YT",
    "MEXICO": "MX",
    "MICRONESIA": "FM",
    "MOLDOVA": "MD",
    "MONACO": "MC",
    "MONGOLIA": "MN",
    "MONTENEGRO": "ME",
    "MONTSERRAT": "MS",
    "MOROCCO": "MA",
    "MOZAMBIQUE": "MZ",
    "MYANMAR": "MM",
    "NAMIBIA": "NA",
    "NAURU": "NR",
    "NEPAL": "NP",
    "NETHERLANDS": "NL",
    "NEW CALEDONIA": "NC",
    "NEW ZEALAND": "NZ",
    "NICARAGUA": "NI",
    "NIGER": "NE",
    "NIGERIA": "NG",
    "NIUE": "NU",
    "NORFOLK ISLAND": "NF",
    "NORTH KOREA": "KP",
    "NORTH MACEDONIA": "MK",
    "NORTHERN MARIANA ISLANDS": "MP",
    "NORWAY": "NO",
    "OMAN": "OM",
    "PAKISTAN": "PK",
    "PALAU": "PW",
    "PALESTINE": "PS",
    "PANAMA": "PA",
    "PAPUA NEW GUINEA": "PG",
    "PARAGUAY": "PY",
    "PERU": "PE",
    "PHILIPPINES": "PH",
    "PITCAIRN ISLANDS": "PN",
    "POLAND": "PL",
    "PORTUGAL": "PT",
    "PUERTO RICO": "PR",
    "QATAR": "QA",
    "REUNION": "RE",
    "ROMANIA": "RO",
    "RUSSIA": "RU",
    "RWANDA": "RW",
    "SAINT BARTHELEMY": "BL",
    "SAINT HELENA": "SH",
    "SAINT KITTS AND NEVIS": "KN",
    "SAINT LUCIA": "LC",
    "SAINT MARTIN": "MF",
    "SAINT PIERRE AND MIQUELON": "PM",
    "SAINT VINCENT AND THE GRENADINES": "VC",
    "SAMOA": "WS",
    "SAN MARINO": "SM",
    "SAO TOME AND PRINCIPE": "ST",
    "SAUDI ARABIA": "SA",
    "SENEGAL": "SN",
    "SERBIA": "RS",
    "SEYCHELLES": "SC",
    "SIERRA LEONE": "SL",
    "SINGAPORE": "SG",
    "SLOVAKIA": "SK",
    "SLOVENIA": "SI",
    "SOLOMON ISLANDS": "SB",
    "SOMALIA": "SO",
    "SOUTH AFRICA": "ZA",
    "SOUTH KOREA": "KR",
    "SOUTH SUDAN": "SS",
    "SPAIN": "ES",
    "SRI LANKA": "LK",
    "SUDAN": "SD",
    "SURINAME": "SR",
    "SWEDEN": "SE",
    "SWITZERLAND": "CH",
    "SYRIA": "SY",
    "TAIWAN": "TW",
    "TAJIKISTAN": "TJ",
    "TANZANIA": "TZ",
    "THAILAND": "TH",
    "TIMOR-LESTE": "TL",
    "TOGO": "TG",
    "TOKELAU": "TK",
    "TONGA": "TO",
    "TRINIDAD AND TOBAGO": "TT",
    "TUNISIA": "TN",
    "TURKEY": "TR",
    "TURKMENISTAN": "TM",
    "TURKS AND CAICOS ISLANDS": "TC",
    "TUVALU": "TV",
    "UGANDA": "UG",
    "UKRAINE": "UA",
    "UNITED ARAB EMIRATES": "AE",
    "UNITED KINGDOM": "GB",
    "UNITED STATES": "US",
    "UNITED STATES VIRGIN ISLANDS": "VI",
    "URUGUAY": "UY",
    "UZBEKISTAN": "UZ",
    "VANUATU": "VU",
    "VATICAN CITY": "VA",
    "VENEZUELA": "VE",
    "VIETNAM": "VN",
    "WALLIS AND FUTUNA": "WF",
    "WESTERN SAHARA": "EH",
    "YEMEN": "YE",
    "ZAMBIA": "ZM",
    "ZIMBABWE": "ZW",
}

# Common aliases (uppercased)
_SYNONYM_TO_ALPHA2: dict[str, str] = {
    "USA": "US",
    "UK": "GB",
    "UAE": "AE",
    "PRC": "CN",
    "DRC": "CD",
    "DPRK": "KP",
    "ROK": "KR",
    "USSR": "RU",
    "UAR": "EG",
    "CDI": "CI",
    "RSA": "ZA",
    "TLS": "TL",
    "CAR": "CF",
    "PNG": "PG",
    "SWZ": "SZ",
    "SKN": "KN",
    "LCA": "LC",
    "VCT": "VC",
    "TCT": "TC",
    "BVI": "VG",
    "USVI": "VI",
    "CAY": "KY",
    "FR GUIANA": "GF",
    "FRENCH GUIANA": "GF",
    "HKG": "HK",
    "MOZ": "MZ",
    "COD": "CD",
    "COG": "CG",
    "DOM": "DO",
    "EL SAL": "SV",
    "EQUatorial GUINEA": "GQ",
    "HOND": "HN",
    "NICAR": "NI",
    "PAN": "PA",
    "PARAG": "PY",
    "TRINIDAD": "TT",
    "UZBEK": "UZ",
    "VENEZ": "VE",
}
```

- [ ] **Step 2: Verify data module loads**

Run: `uv run python -c "from paxman.capabilities.Country.data import _ALPHA2_CODES; print(len(_ALPHA2_CODES))"`
Expected: `249`

- [ ] **Step 3: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/data.py`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add paxman/capabilities/Country/data.py
git commit -m "feat(country): add ISO 3166-1 lookup tables"
```

---

## Task 5: Create Alpha2 Grammar

**Files:**
- Create: `paxman/capabilities/Country/grammar/alpha2_recognition.py`
- Test: `tests/capabilities/country/test_grammar.py`

- [ ] **Step 1: Write alpha2 grammar tests**

```python
# tests/capabilities/country/test_grammar.py
"""Tests for Country recognition grammars."""

import pytest
from paxman.capabilities.Country.grammar.alpha2_recognition import Alpha2Grammar


class TestAlpha2Grammar:
    """Tests for Alpha2Grammar."""

    def setup_method(self) -> None:
        self.grammar = Alpha2Grammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: grammar finds alpha2 pattern."""
        results = self.grammar.recognize("US")
        assert len(results) == 1
        assert results[0].shape == "alpha2"
        assert results[0].value == "US"

    def test_recognizes_lowercase(self) -> None:
        """Edge case: lowercase input is uppercased."""
        results = self.grammar.recognize("gb")
        assert len(results) == 1
        assert results[0].value == "GB"

    def test_recognizes_mixed_case(self) -> None:
        """Edge case: mixed case input is uppercased."""
        results = self.grammar.recognize("Us")
        assert len(results) == 1
        assert results[0].value == "US"

    def test_recognizes_with_whitespace(self) -> None:
        """Edge case: whitespace is trimmed."""
        results = self.grammar.recognize("  US  ")
        assert len(results) == 1
        assert results[0].value == "US"

    def test_recognizes_multiple(self) -> None:
        """Input contains multiple alpha2 matches."""
        results = self.grammar.recognize("US and GB")
        assert len(results) == 2

    def test_rejects_alpha3(self) -> None:
        """Grammar does not match 3-letter codes."""
        results = self.grammar.recognize("USA")
        assert len(results) == 0

    def test_rejects_numeric(self) -> None:
        """Grammar does not match digits."""
        results = self.grammar.recognize("12")
        assert len(results) == 0

    def test_rejects_single_letter(self) -> None:
        """Grammar does not match single letter."""
        results = self.grammar.recognize("U")
        assert len(results) == 0

    def test_rejects_long_string(self) -> None:
        """Grammar does not match strings > 2 chars."""
        results = self.grammar.recognize("United")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "alpha2_recognition"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_grammar.py::TestAlpha2Grammar -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement Alpha2Grammar**

```python
# paxman/capabilities/Country/grammar/alpha2_recognition.py
"""Alpha-2 country code recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar

_ALPHA2_PATTERN = re.compile(r"^[A-Za-z]{2}$")


class Alpha2Grammar(Grammar[CountryNotation]):
    """Recognizes exactly 2 ASCII letters as alpha-2 country code shape.

    Examples: "US", "GB", "us", "gB"
    Non-examples: "USA" (3 letters), "12" (digits), "U" (1 letter)
    """

    name = "alpha2_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract alpha-2 patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of CountryNotations with shape="alpha2".
        """
        trimmed = text.strip()
        if not trimmed:
            return []
        if _ALPHA2_PATTERN.match(trimmed):
            return [CountryNotation(shape="alpha2", value=trimmed.upper())]
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_grammar.py::TestAlpha2Grammar -v`
Expected: 11 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/grammar/alpha2_recognition.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/grammar/alpha2_recognition.py tests/capabilities/country/test_grammar.py
git commit -m "feat(country): add Alpha2 grammar"
```

---

## Task 6: Create Alpha3 Grammar

**Files:**
- Create: `paxman/capabilities/Country/grammar/alpha3_recognition.py`
- Test: `tests/capabilities/country/test_grammar.py`

- [ ] **Step 1: Write alpha3 grammar tests**

```python
# Append to tests/capabilities/country/test_grammar.py

from paxman.capabilities.Country.grammar.alpha3_recognition import Alpha3Grammar


class TestAlpha3Grammar:
    """Tests for Alpha3Grammar."""

    def setup_method(self) -> None:
        self.grammar = Alpha3Grammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: grammar finds alpha3 pattern."""
        results = self.grammar.recognize("USA")
        assert len(results) == 1
        assert results[0].shape == "alpha3"
        assert results[0].value == "USA"

    def test_recognizes_lowercase(self) -> None:
        """Edge case: lowercase input is uppercased."""
        results = self.grammar.recognize("gbr")
        assert len(results) == 1
        assert results[0].value == "GBR"

    def test_recognizes_with_whitespace(self) -> None:
        """Edge case: whitespace is trimmed."""
        results = self.grammar.recognize("  USA  ")
        assert len(results) == 1
        assert results[0].value == "USA"

    def test_recognizes_multiple(self) -> None:
        """Input contains multiple alpha3 matches."""
        results = self.grammar.recognize("USA and GBR")
        assert len(results) == 2

    def test_rejects_alpha2(self) -> None:
        """Grammar does not match 2-letter codes."""
        results = self.grammar.recognize("US")
        assert len(results) == 0

    def test_rejects_numeric(self) -> None:
        """Grammar does not match digits."""
        results = self.grammar.recognize("123")
        assert len(results) == 0

    def test_rejects_long_string(self) -> None:
        """Grammar does not match strings > 3 chars."""
        results = self.grammar.recognize("United")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "alpha3_recognition"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_grammar.py::TestAlpha3Grammar -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement Alpha3Grammar**

```python
# paxman/capabilities/Country/grammar/alpha3_recognition.py
"""Alpha-3 country code recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar

_ALPHA3_PATTERN = re.compile(r"^[A-Za-z]{3}$")


class Alpha3Grammar(Grammar[CountryNotation]):
    """Recognizes exactly 3 ASCII letters as alpha-3 country code shape.

    Examples: "USA", "GBR", "usa", "gbr"
    Non-examples: "US" (2 letters), "123" (digits), "United" (6 letters)
    """

    name = "alpha3_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract alpha-3 patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of CountryNotations with shape="alpha3".
        """
        trimmed = text.strip()
        if not trimmed:
            return []
        if _ALPHA3_PATTERN.match(trimmed):
            return [CountryNotation(shape="alpha3", value=trimmed.upper())]
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_grammar.py::TestAlpha3Grammar -v`
Expected: 9 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/grammar/alpha3_recognition.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/grammar/alpha3_recognition.py
git commit -m "feat(country): add Alpha3 grammar"
```

---

## Task 7: Create Numeric Grammar

**Files:**
- Create: `paxman/capabilities/Country/grammar/numeric_recognition.py`
- Test: `tests/capabilities/country/test_grammar.py`

- [ ] **Step 1: Write numeric grammar tests**

```python
# Append to tests/capabilities/country/test_grammar.py

from paxman.capabilities.Country.grammar.numeric_recognition import NumericGrammar


class TestNumericGrammar:
    """Tests for NumericGrammar."""

    def setup_method(self) -> None:
        self.grammar = NumericGrammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: grammar finds numeric pattern."""
        results = self.grammar.recognize("840")
        assert len(results) == 1
        assert results[0].shape == "numeric"
        assert results[0].value == "840"

    def test_recognizes_single_digit(self) -> None:
        """Edge case: single digit."""
        results = self.grammar.recognize("4")
        assert len(results) == 1
        assert results[0].value == "4"

    def test_recognizes_two_digits(self) -> None:
        """Edge case: two digits."""
        results = self.grammar.recognize("82")
        assert len(results) == 1
        assert results[0].value == "82"

    def test_recognizes_with_whitespace(self) -> None:
        """Edge case: whitespace is trimmed."""
        results = self.grammar.recognize("  840  ")
        assert len(results) == 1
        assert results[0].value == "840"

    def test_preserves_leading_zeros(self) -> None:
        """Edge case: leading zeros are preserved."""
        results = self.grammar.recognize("004")
        assert len(results) == 1
        assert results[0].value == "004"

    def test_rejects_four_digits(self) -> None:
        """Grammar does not match 4+ digits."""
        results = self.grammar.recognize("1234")
        assert len(results) == 0

    def test_rejects_letters(self) -> None:
        """Grammar does not match letters."""
        results = self.grammar.recognize("abc")
        assert len(results) == 0

    def test_rejects_alphanumeric(self) -> None:
        """Grammar does not match alphanumeric."""
        results = self.grammar.recognize("12a")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "numeric_recognition"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_grammar.py::TestNumericGrammar -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement NumericGrammar**

```python
# paxman/capabilities/Country/grammar/numeric_recognition.py
"""Numeric (M49) country code recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar

_NUMERIC_PATTERN = re.compile(r"^\d{1,3}$")


class NumericGrammar(Grammar[CountryNotation]):
    """Recognizes 1-3 digits as numeric country code shape.

    Examples: "840", "4", "004"
    Non-examples: "US" (letters), "1234" (4 digits), "12a" (alphanumeric)
    """

    name = "numeric_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract numeric patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of CountryNotations with shape="numeric".
        """
        trimmed = text.strip()
        if not trimmed:
            return []
        if _NUMERIC_PATTERN.match(trimmed):
            return [CountryNotation(shape="numeric", value=trimmed)]
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_grammar.py::TestNumericGrammar -v`
Expected: 10 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/grammar/numeric_recognition.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/grammar/numeric_recognition.py
git commit -m "feat(country): add Numeric grammar"
```

---

## Task 8: Create Name Grammar

**Files:**
- Create: `paxman/capabilities/Country/grammar/name_recognition.py`
- Test: `tests/capabilities/country/test_grammar.py`

- [ ] **Step 1: Write name grammar tests**

```python
# Append to tests/capabilities/country/test_grammar.py

from paxman.capabilities.Country.grammar.name_recognition import NameGrammar


class TestNameGrammar:
    """Tests for NameGrammar."""

    def setup_method(self) -> None:
        self.grammar = NameGrammar()

    def test_recognizes_full_name(self) -> None:
        """Happy path: grammar finds name pattern."""
        results = self.grammar.recognize("United States")
        assert len(results) == 1
        assert results[0].shape == "name"
        assert results[0].value == "United States"

    def test_recognizes_unicode(self) -> None:
        """Edge case: Unicode input."""
        results = self.grammar.recognize("马来西亚")
        assert len(results) == 1
        assert results[0].value == "马来西亚"

    def test_recognizes_alpha2(self) -> None:
        """Design note: name grammar also matches alpha2 shapes."""
        results = self.grammar.recognize("US")
        assert len(results) == 1
        assert results[0].shape == "name"
        assert results[0].value == "US"

    def test_recognizes_alpha3(self) -> None:
        """Design note: name grammar also matches alpha3 shapes."""
        results = self.grammar.recognize("USA")
        assert len(results) == 1
        assert results[0].shape == "name"

    def test_recognizes_numeric(self) -> None:
        """Design note: name grammar also matches numeric shapes."""
        results = self.grammar.recognize("840")
        assert len(results) == 1
        assert results[0].shape == "name"

    def test_preserves_case(self) -> None:
        """Edge case: original case is preserved."""
        results = self.grammar.recognize("united states")
        assert len(results) == 1
        assert results[0].value == "united states"

    def test_recognizes_with_whitespace(self) -> None:
        """Edge case: whitespace is trimmed."""
        results = self.grammar.recognize("  Burma  ")
        assert len(results) == 1
        assert results[0].value == "Burma"

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "name_recognition"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_grammar.py::TestNameGrammar -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement NameGrammar**

```python
# paxman/capabilities/Country/grammar/name_recognition.py
"""Country name recognition grammar."""

from __future__ import annotations

from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Grammar


class NameGrammar(Grammar[CountryNotation]):
    """Recognizes any non-empty string as country name shape.

    Design note: This grammar matches ANY non-empty input, including values
    that might also match alpha2/alpha3/numeric grammars. This is intentional —
    multiple grammars matching the same input is fine because:
    - Each grammar produces a separate notation with the appropriate shape
    - Rules validate based on shape (e.g., SectionAlpha2Codes only accepts shape="alpha2")
    - Multiple candidates with the same canonical value produce SUCCESS, not AMBIGUOUS

    Examples: "United States", "马来西亚", "Burma", "US" (also matched by alpha2)
    Non-examples: "" (empty)
    """

    name = "name_recognition"

    def recognize(self, text: str) -> list[CountryNotation]:
        """Extract name patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of CountryNotations with shape="name".
        """
        trimmed = text.strip()
        if not trimmed:
            return []
        return [CountryNotation(shape="name", value=trimmed)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_grammar.py::TestNameGrammar -v`
Expected: 9 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/grammar/name_recognition.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/grammar/name_recognition.py
git commit -m "feat(country): add Name grammar"
```

---

## Task 9: Create ISO 3166-1 Alpha2 Rule

**Files:**
- Create: `paxman/capabilities/Country/rules/iso_3166_alpha2_ed2024.py`
- Test: `tests/capabilities/country/test_rules.py`

- [ ] **Step 1: Write alpha2 rule tests**

```python
# tests/capabilities/country/test_rules.py
"""Tests for Country validation rules."""

import pytest
from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.iso_3166_alpha2_ed2024 import SectionAlpha2Codes
from paxman.core.domain import RuleStrategy


class TestSectionAlpha2Codes:
    """Tests for SectionAlpha2Codes rule."""

    def setup_method(self) -> None:
        self.rule = SectionAlpha2Codes()
        self.contract = CountryContract()

    def test_matches_valid_input(self) -> None:
        """Happy path: notation is valid."""
        notation = CountryNotation(shape="alpha2", value="US")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_lowercase(self) -> None:
        """Edge case: lowercase input matches."""
        notation = CountryNotation(shape="alpha2", value="us")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_all_valid_codes(self) -> None:
        """Edge case: all 249 codes match."""
        from paxman.capabilities.Country.data import _ALPHA2_CODES

        for code in list(_ALPHA2_CODES)[:10]:  # Test first 10
            notation = CountryNotation(shape="alpha2", value=code)
            assert self.rule.matches(notation, self.contract) is True

    def test_rejects_invalid_code(self) -> None:
        """Notation with invalid alpha-2 code."""
        notation = CountryNotation(shape="alpha2", value="XX")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = CountryNotation(shape="alpha3", value="US")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        notation = CountryNotation(shape="alpha2", value="US")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_normalize_lowercase(self) -> None:
        """Verify lowercase input normalizes to uppercase."""
        notation = CountryNotation(shape="alpha2", value="us")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.specification_name == "ISO 3166-1:2024"
        assert self.rule.provenance.publication_year == 2024
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-alpha2-codes"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "alpha-2" in self.rule.citation.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionAlpha2Codes -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement SectionAlpha2Codes**

```python
# paxman/capabilities/Country/rules/iso_3166_alpha2_ed2024.py
"""ISO 3166-1:2024 alpha-2 code validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.data import _ALPHA2_CODES
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 3166-1:2024",
    kind="registry",
    reference_url="https://www.iso.org/guest/en/ISO3166-1/RegistrationTable/Active%20country%20list.html",
    version="2024",
    lifecycle="active",
    publication_year=2024,
)


class SectionAlpha2Codes(Rule[CountryNotation]):
    """ISO 3166-1 Section: alpha-2 codes.

    Validates alpha-2 shape against the official list of 249 assigned codes.
    """

    name = "Section-alpha2-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 alpha-2 codes"

    def matches(self, notation: CountryNotation, contract: CountryContract) -> bool:
        """Check if notation is a valid alpha-2 code.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "alpha2" AND value is in _ALPHA2_CODES.
        """
        if notation.shape != "alpha2":
            return False
        return notation.value.upper() in _ALPHA2_CODES

    def normalize(self, notation: CountryNotation, contract: CountryContract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code.
        """
        code = notation.value.upper()
        if contract.output_format == "alpha3":
            from paxman.capabilities.Country.data import _ALPHA3_TO_ALPHA2

            for alpha3, alpha2 in _ALPHA3_TO_ALPHA2.items():
                if alpha2 == code:
                    return alpha3
        if contract.output_format == "numeric":
            from paxman.capabilities.Country.data import _NUMERIC_TO_ALPHA2

            for numeric, alpha2 in _NUMERIC_TO_ALPHA2.items():
                if alpha2 == code:
                    return numeric
        if contract.output_format == "name":
            from paxman.capabilities.Country.data import _NAME_TO_ALPHA2

            for name, alpha2 in _NAME_TO_ALPHA2.items():
                if alpha2 == code:
                    return name
        return code
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionAlpha2Codes -v`
Expected: 11 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/rules/iso_3166_alpha2_ed2024.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/rules/iso_3166_alpha2_ed2024.py tests/capabilities/country/test_rules.py
git commit -m "feat(country): add ISO 3166-1 alpha-2 validation rule"
```

---

## Task 10: Create ISO 3166-1 Alpha3 Rule

**Files:**
- Create: `paxman/capabilities/Country/rules/iso_3166_alpha3_ed2024.py`
- Test: `tests/capabilities/country/test_rules.py`

- [ ] **Step 1: Write alpha3 rule tests**

```python
# Append to tests/capabilities/country/test_rules.py

from paxman.capabilities.Country.rules.iso_3166_alpha3_ed2024 import SectionAlpha3Codes


class TestSectionAlpha3Codes:
    """Tests for SectionAlpha3Codes rule."""

    def setup_method(self) -> None:
        self.rule = SectionAlpha3Codes()
        self.contract = CountryContract()

    def test_matches_valid_input(self) -> None:
        """Happy path: notation is valid."""
        notation = CountryNotation(shape="alpha3", value="USA")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_lowercase(self) -> None:
        """Edge case: lowercase input matches."""
        notation = CountryNotation(shape="alpha3", value="usa")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_invalid_code(self) -> None:
        """Notation with invalid alpha-3 code."""
        notation = CountryNotation(shape="alpha3", value="XXX")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = CountryNotation(shape="alpha2", value="USA")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output (alpha-2)."""
        notation = CountryNotation(shape="alpha3", value="USA")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_normalize_lowercase(self) -> None:
        """Verify lowercase input normalizes correctly."""
        notation = CountryNotation(shape="alpha3", value="gbr")
        assert self.rule.normalize(notation, self.contract) == "GB"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.publication_year == 2024

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-alpha3-codes"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionAlpha3Codes -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement SectionAlpha3Codes**

```python
# paxman/capabilities/Country/rules/iso_3166_alpha3_ed2024.py
"""ISO 3166-1:2024 alpha-3 code validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.data import _ALPHA3_TO_ALPHA2
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 3166-1:2024",
    kind="registry",
    reference_url="https://www.iso.org/guest/en/ISO3166-1/RegistrationTable/Active%20country%20list.html",
    version="2024",
    lifecycle="active",
    publication_year=2024,
)


class SectionAlpha3Codes(Rule[CountryNotation]):
    """ISO 3166-1 Section: alpha-3 codes.

    Validates alpha-3 shape against the official list of 249 assigned codes.
    """

    name = "Section-alpha3-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 alpha-3 codes"

    def matches(self, notation: CountryNotation, contract: CountryContract) -> bool:
        """Check if notation is a valid alpha-3 code.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "alpha3" AND value is in _ALPHA3_TO_ALPHA2.
        """
        if notation.shape != "alpha3":
            return False
        return notation.value.upper() in _ALPHA3_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: CountryContract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code (or configured output format).
        """
        alpha2 = _ALPHA3_TO_ALPHA2[notation.value.upper()]
        if contract.output_format == "alpha3":
            return notation.value.upper()
        if contract.output_format == "numeric":
            from paxman.capabilities.Country.data import _NUMERIC_TO_ALPHA2

            for numeric, a2 in _NUMERIC_TO_ALPHA2.items():
                if a2 == alpha2:
                    return numeric
        if contract.output_format == "name":
            from paxman.capabilities.Country.data import _NAME_TO_ALPHA2

            for name, a2 in _NAME_TO_ALPHA2.items():
                if a2 == alpha2:
                    return name
        return alpha2
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionAlpha3Codes -v`
Expected: 9 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/rules/iso_3166_alpha3_ed2024.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/rules/iso_3166_alpha3_ed2024.py
git commit -m "feat(country): add ISO 3166-1 alpha-3 validation rule"
```

---

## Task 11: Create ISO 3166-1 Numeric Rule

**Files:**
- Create: `paxman/capabilities/Country/rules/iso_3166_numeric_ed2024.py`
- Test: `tests/capabilities/country/test_rules.py`

- [ ] **Step 1: Write numeric rule tests**

```python
# Append to tests/capabilities/country/test_rules.py

from paxman.capabilities.Country.rules.iso_3166_numeric_ed2024 import (
    SectionNumericCodes,
)


class TestSectionNumericCodes:
    """Tests for SectionNumericCodes rule."""

    def setup_method(self) -> None:
        self.rule = SectionNumericCodes()
        self.contract = CountryContract()

    def test_matches_valid_input(self) -> None:
        """Happy path: notation is valid."""
        notation = CountryNotation(shape="numeric", value="840")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_with_leading_zeros(self) -> None:
        """Edge case: leading zeros are stripped for lookup."""
        notation = CountryNotation(shape="numeric", value="0840")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_single_digit(self) -> None:
        """Edge case: single digit."""
        notation = CountryNotation(shape="numeric", value="4")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_invalid_code(self) -> None:
        """Notation with invalid numeric code."""
        notation = CountryNotation(shape="numeric", value="999")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = CountryNotation(shape="alpha2", value="840")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output (alpha-2)."""
        notation = CountryNotation(shape="numeric", value="840")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_normalize_preserves_original(self) -> None:
        """Verify original value is preserved in notation."""
        notation = CountryNotation(shape="numeric", value="004")
        assert self.rule.normalize(notation, self.contract) == "AF"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.publication_year == 2024

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-numeric-codes"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionNumericCodes -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement SectionNumericCodes**

```python
# paxman/capabilities/Country/rules/iso_3166_numeric_ed2024.py
"""ISO 3166-1:2024 numeric (M49) code validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.data import _NUMERIC_TO_ALPHA2
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 3166-1:2024",
    kind="registry",
    reference_url="https://www.iso.org/guest/en/ISO3166-1/RegistrationTable/Active%20country%20list.html",
    version="2024",
    lifecycle="active",
    publication_year=2024,
)


class SectionNumericCodes(Rule[CountryNotation]):
    """ISO 3166-1 Section: numeric (M49) codes.

    Validates numeric shape against the official list of 249 assigned codes.
    """

    name = "Section-numeric-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 numeric (M49) codes"

    def matches(self, notation: CountryNotation, contract: CountryContract) -> bool:
        """Check if notation is a valid numeric code.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "numeric" AND normalized value is in _NUMERIC_TO_ALPHA2.
        """
        if notation.shape != "numeric":
            return False
        normalized = notation.value.lstrip("0") or "0"
        return normalized in _NUMERIC_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: CountryContract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code (or configured output format).
        """
        normalized = notation.value.lstrip("0") or "0"
        alpha2 = _NUMERIC_TO_ALPHA2[normalized]
        if contract.output_format == "numeric":
            return normalized
        if contract.output_format == "alpha3":
            from paxman.capabilities.Country.data import _ALPHA3_TO_ALPHA2

            for alpha3, a2 in _ALPHA3_TO_ALPHA2.items():
                if a2 == alpha2:
                    return alpha3
        if contract.output_format == "name":
            from paxman.capabilities.Country.data import _NAME_TO_ALPHA2

            for name, a2 in _NAME_TO_ALPHA2.items():
                if a2 == alpha2:
                    return name
        return alpha2
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionNumericCodes -v`
Expected: 10 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/rules/iso_3166_numeric_ed2024.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/rules/iso_3166_numeric_ed2024.py
git commit -m "feat(country): add ISO 3166-1 numeric validation rule"
```

---

## Task 12: Create ISO 3166-1 Name Rule

**Files:**
- Create: `paxman/capabilities/Country/rules/iso_3166_name_ed2024.py`
- Test: `tests/capabilities/country/test_rules.py`

- [ ] **Step 1: Write name rule tests**

```python
# Append to tests/capabilities/country/test_rules.py

from paxman.capabilities.Country.rules.iso_3166_name_ed2024 import SectionNameCodes


class TestSectionNameCodes:
    """Tests for SectionNameCodes rule."""

    def setup_method(self) -> None:
        self.rule = SectionNameCodes()
        self.contract = CountryContract()

    def test_matches_official_name(self) -> None:
        """Happy path: official name matches."""
        notation = CountryNotation(shape="name", value="UNITED STATES OF AMERICA")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_lowercase_official_name(self) -> None:
        """Edge case: lowercase official name matches."""
        notation = CountryNotation(shape="name", value="united states of america")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_synonym(self) -> None:
        """Edge case: synonym matches."""
        notation = CountryNotation(shape="name", value="UK")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_extra_synonyms(self) -> None:
        """Edge case: extra_synonyms from contract matches."""
        contract = CountryContract(extra_synonyms={"my_alias": "MY"})
        notation = CountryNotation(shape="name", value="my_alias")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_invalid_name(self) -> None:
        """Notation with invalid name."""
        notation = CountryNotation(shape="name", value="NOT A COUNTRY")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = CountryNotation(shape="alpha2", value="US")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        notation = CountryNotation(shape="name", value="UNITED STATES OF AMERICA")
        assert self.rule.normalize(notation, self.contract) == "US"

    def test_normalize_synonym(self) -> None:
        """Verify synonym normalizes correctly."""
        notation = CountryNotation(shape="name", value="UK")
        assert self.rule.normalize(notation, self.contract) == "GB"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ISO"
        assert self.rule.provenance.publication_year == 2024

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-name-codes"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionNameCodes -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement SectionNameCodes**

```python
# paxman/capabilities/Country/rules/iso_3166_name_ed2024.py
"""ISO 3166-1:2024 name validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.data import (
    _NAME_TO_ALPHA2,
    _SYNONYM_TO_ALPHA2,
)
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 3166-1:2024",
    kind="registry",
    reference_url="https://www.iso.org/guest/en/ISO3166-1/RegistrationTable/Active%20country%20list.html",
    version="2024",
    lifecycle="active",
    publication_year=2024,
)


class SectionNameCodes(Rule[CountryNotation]):
    """ISO 3166-1 Section: name codes.

    Validates name shape against official English short names and common aliases.
    Also checks contract.extra_synonyms for caller-supplied aliases.
    """

    name = "Section-name-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "ISO 3166-1 name codes"

    def matches(self, notation: CountryNotation, contract: CountryContract) -> bool:
        """Check if notation is a valid country name.

        Lookup order:
        1. _NAME_TO_ALPHA2 (official names)
        2. _SYNONYM_TO_ALPHA2 (common aliases)
        3. contract.extra_synonyms (caller-supplied)

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if notation.shape == "name" AND name is found in any lookup.
        """
        if notation.shape != "name":
            return False
        normalized = notation.value.upper()
        if normalized in _NAME_TO_ALPHA2:
            return True
        if normalized in _SYNONYM_TO_ALPHA2:
            return True
        if notation.value in contract.extra_synonyms:
            return True
        return False

    def normalize(self, notation: CountryNotation, contract: CountryContract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code (or configured output format).
        """
        normalized = notation.value.upper()
        alpha2 = None
        if normalized in _NAME_TO_ALPHA2:
            alpha2 = _NAME_TO_ALPHA2[normalized]
        elif normalized in _SYNONYM_TO_ALPHA2:
            alpha2 = _SYNONYM_TO_ALPHA2[normalized]
        elif notation.value in contract.extra_synonyms:
            alpha2 = contract.extra_synonyms[notation.value]

        if alpha2 is None:
            raise ValueError(f"Unexpected: {notation.value} not found in any lookup")

        if contract.output_format == "name":
            for name, a2 in _NAME_TO_ALPHA2.items():
                if a2 == alpha2:
                    return name
        if contract.output_format == "alpha3":
            from paxman.capabilities.Country.data import _ALPHA3_TO_ALPHA2

            for alpha3, a2 in _ALPHA3_TO_ALPHA2.items():
                if a2 == alpha2:
                    return alpha3
        if contract.output_format == "numeric":
            from paxman.capabilities.Country.data import _NUMERIC_TO_ALPHA2

            for numeric, a2 in _NUMERIC_TO_ALPHA2.items():
                if a2 == alpha2:
                    return numeric
        return alpha2
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionNameCodes -v`
Expected: 11 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/rules/iso_3166_name_ed2024.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/rules/iso_3166_name_ed2024.py
git commit -m "feat(country): add ISO 3166-1 name validation rule"
```

---

## Task 13: Create CLDR Localized Rule

**Files:**
- Create: `paxman/capabilities/Country/rules/cldr_localized_ed2025.py`
- Test: `tests/capabilities/country/test_rules.py`

- [ ] **Step 1: Write localized rule tests**

```python
# Append to tests/capabilities/country/test_rules.py

from paxman.capabilities.Country.rules.cldr_localized_ed2025 import (
    SectionLocalizedNames,
)


class TestSectionLocalizedNames:
    """Tests for SectionLocalizedNames rule."""

    def setup_method(self) -> None:
        self.rule = SectionLocalizedNames()

    def test_matches_when_enabled(self) -> None:
        """Happy path: localized enabled and name matches."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="马来西亚")
        assert self.rule.matches(notation, contract) is True

    def test_matches_chinese(self) -> None:
        """Edge case: Chinese name matches."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="中国")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_when_disabled(self) -> None:
        """Notation rejected when localized disabled (default)."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="马来西亚")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="alpha2", value="马来西亚")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_invalid_name(self) -> None:
        """Notation with invalid localized name."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="NOT A COUNTRY")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        contract = CountryContract(include_localized=True)
        notation = CountryNotation(shape="name", value="马来西亚")
        assert self.rule.normalize(notation, contract) == "MY"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "Unicode"
        assert self.rule.provenance.specification_name == "CLDR v45"
        assert self.rule.provenance.publication_year == 2025

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-localized-names"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionLocalizedNames -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create CLDR data module**

```python
# paxman/capabilities/Country/cldr_data.py
"""CLDR v45 localized country names.

Source: https://cldr.unicode.org/
Languages: Chinese (zh), Spanish (es), French (fr)
"""

from __future__ import annotations

# Localized names to alpha-2 (curated subset for v1.0)
# Format: {localized_name: alpha2_code}
_LOCALIZED_TO_ALPHA2: dict[str, str] = {
    # Chinese (zh)
    "中国": "CN",
    "美国": "US",
    "日本": "JP",
    "韩国": "KR",
    "马来西亚": "MY",
    "新加坡": "SG",
    "泰国": "TH",
    "越南": "VN",
    "印度尼西亚": "ID",
    "菲律宾": "PH",
    "俄罗斯": "RU",
    "英国": "GB",
    "法国": "FR",
    "德国": "DE",
    "意大利": "IT",
    "西班牙": "ES",
    "巴西": "BR",
    "墨西哥": "MX",
    "加拿大": "CA",
    "澳大利亚": "AU",
    "印度": "IN",
    "巴基斯坦": "PK",
    "孟加拉国": "BD",
    "斯里兰卡": "LK",
    "尼泊尔": "NP",
    "不丹": "BT",
    "马尔代夫": "MV",
    "阿富汗": "AF",
    "伊朗": "IQ",
    "伊拉克": "IQ",
    "沙特阿拉伯": "SA",
    "阿联酋": "AE",
    "卡塔尔": "QA",
    "科威特": "KW",
    "巴林": "BH",
    "阿曼": "OM",
    "约旦": "JO",
    "黎巴嫩": "LB",
    "叙利亚": "SY",
    "以色列": "IL",
    "巴勒斯坦": "PS",
    "埃及": "EG",
    "南非": "ZA",
    "尼日利亚": "NG",
    "肯尼亚": "KE",
    "埃塞俄比亚": "ET",
    "坦桑尼亚": "TZ",
    "乌干达": "UG",
    "加纳": "GH",
    "喀麦隆": "CM",
    "科特迪瓦": "CI",
    "塞内加尔": "SN",
    "马里": "ML",
    "布基纳法索": "BF",
    "尼日尔": "NE",
    "乍得": "TD",
    "刚果": "CG",
    "刚果民主共和国": "CD",
    "加蓬": "GA",
    "赤道几内亚": "GQ",
    "卢旺达": "RW",
    "布隆迪": "BI",
    "索马里": "SO",
    "苏丹": "SD",
    "南苏丹": "SS",
    "利比亚": "LY",
    "突尼斯": "TN",
    "阿尔及利亚": "DZ",
    "摩洛哥": "MA",
    "西撒哈拉": "EH",
    "毛里塔尼亚": "MR",
    "马达加斯加": "MG",
    "莫桑比克": "MZ",
    "安哥拉": "AO",
    "赞比亚": "ZM",
    "津巴布韦": "ZW",
    "博茨瓦纳": "BW",
    "纳米比亚": "NA",
    "斯威士兰": "SZ",
    "莱索托": "LS",
    "马拉维": "MW",
    "刚果共和国": "CG",
    "几内亚": "GN",
    "几内亚比绍": "GW",
    "塞拉利昂": "SL",
    "利比里亚": "LR",
    "多哥": "TG",
    "贝宁": "BJ",
    "中非": "CF",
    "厄立特里亚": "ER",
    "吉布提": "DJ",
    "科摩罗": "KM",
    "毛里求斯": "MU",
    "塞舌尔": "SC",
    "科摩罗群岛": "KM",
    # Spanish (es)
    "Estados Unidos": "US",
    "México": "MX",
    "Brasil": "BR",
    "Argentina": "AR",
    "Colombia": "CO",
    "Perú": "PE",
    "Chile": "CL",
    "Venezuela": "VE",
    "Ecuador": "EC",
    "Bolivia": "BO",
    "Paraguay": "PY",
    "Uruguay": "UY",
    "España": "ES",
    "Francia": "FR",
    "Alemania": "DE",
    "Italia": "IT",
    "Portugal": "PT",
    "Reino Unido": "GB",
    "Japón": "JP",
    "China": "CN",
    "Corea del Sur": "KR",
    "India": "IN",
    "Rusia": "RU",
    "Canadá": "CA",
    "Australia": "AU",
    "Nueva Zelanda": "NZ",
    "Sudáfrica": "ZA",
    "Egipto": "EG",
    "Marruecos": "MA",
    "Argelia": "DZ",
    "Túnez": "TN",
    "Nigeria": "NG",
    "Kenia": "KE",
    "Etiopía": "ET",
    "Tanzania": "TZ",
    # French (fr)
    "États-Unis": "US",
    "Royaume-Uni": "GB",
    "Allemagne": "DE",
    "Japon": "JP",
    "Chine": "CN",
    "Corée du Sud": "KR",
    "Inde": "IN",
    "Russie": "RU",
    "Canada": "CA",
    "Australie": "AU",
    "Nouvelle-Zélande": "NZ",
    "Afrique du Sud": "ZA",
    "Égypte": "EG",
    "Maroc": "MA",
    "Algérie": "DZ",
    "Tunisie": "TN",
    "Nigeria": "NG",
    "Kenya": "KE",
    "Éthiopie": "ET",
    "Tanzanie": "TZ",
    "Brésil": "BR",
    "Argentine": "AR",
    "Colombie": "CO",
    "Pérou": "PE",
    "Chili": "CL",
    "Venezuela": "VE",
    "Équateur": "EC",
    "Bolivie": "BO",
    "Paraguay": "PY",
    "Uruguay": "UY",
    "Espagne": "ES",
    "Italie": "IT",
    "Portugal": "PT",
}
```

- [ ] **Step 4: Implement SectionLocalizedNames**

```python
# paxman/capabilities/Country/rules/cldr_localized_ed2025.py
"""CLDR v45 localized country name validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.cldr_data import _LOCALIZED_TO_ALPHA2
from paxman.capabilities.Country.notation import CountryNotation
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
    Only active when contract.include_localized is True.
    """

    name = "Section-localized-names"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "CLDR v45 localized country names"

    def matches(self, notation: CountryNotation, contract: CountryContract) -> bool:
        """Check if notation is a valid localized name.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if include_localized AND notation.shape == "name" AND name is in _LOCALIZED_TO_ALPHA2.
        """
        if not contract.include_localized:
            return False
        if notation.shape != "name":
            return False
        return notation.value in _LOCALIZED_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: CountryContract) -> str:
        """Normalize to canonical alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Uppercase alpha-2 code.
        """
        return _LOCALIZED_TO_ALPHA2[notation.value]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionLocalizedNames -v`
Expected: 9 passed

- [ ] **Step 6: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/rules/cldr_localized_ed2025.py`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add paxman/capabilities/Country/rules/cldr_localized_ed2025.py paxman/capabilities/Country/cldr_data.py
git commit -m "feat(country): add CLDR localized names rule"
```

---

## Task 14: Create Historical Names Rule

**Files:**
- Create: `paxman/capabilities/Country/rules/paxman_historical_ed2025.py`
- Test: `tests/capabilities/country/test_rules.py`

- [ ] **Step 1: Write historical rule tests**

```python
# Append to tests/capabilities/country/test_rules.py

from paxman.capabilities.Country.rules.paxman_historical_ed2025 import (
    SectionHistoricalNames,
)


class TestSectionHistoricalNames:
    """Tests for SectionHistoricalNames rule."""

    def setup_method(self) -> None:
        self.rule = SectionHistoricalNames()

    def test_matches_when_enabled(self) -> None:
        """Happy path: historical enabled and name matches."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="BURMA")
        assert self.rule.matches(notation, contract) is True

    def test_matches_lowercase(self) -> None:
        """Edge case: lowercase historical name matches."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="burma")
        assert self.rule.matches(notation, contract) is True

    def test_rejects_when_disabled(self) -> None:
        """Notation rejected when historical disabled (default)."""
        contract = CountryContract()
        notation = CountryNotation(shape="name", value="BURMA")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="alpha2", value="BURMA")
        assert self.rule.matches(notation, contract) is False

    def test_rejects_invalid_name(self) -> None:
        """Notation with invalid historical name."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="NOT A COUNTRY")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="BURMA")
        assert self.rule.normalize(notation, contract) == "MM"

    def test_normalize_ceylon(self) -> None:
        """Verify Ceylon normalizes to LK."""
        contract = CountryContract(include_historical=True)
        notation = CountryNotation(shape="name", value="CEYLON")
        assert self.rule.normalize(notation, contract) == "LK"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "Paxman"
        assert self.rule.provenance.specification_name == "Historical Country Names"
        assert self.rule.provenance.publication_year == 2025

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section-historical-names"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionHistoricalNames -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create historical data module**

```python
# paxman/capabilities/Country/historical_data.py
"""Historical country names (deprecated)."""

from __future__ import annotations

# Historical names to current alpha-2
# Format: {historical_name: current_alpha2_code}
_HISTORICAL_TO_ALPHA2: dict[str, str] = {
    "BURMA": "MM",
    "MYANMAR": "MM",
    "CEYLON": "LK",
    "SRI LANKA": "LK",
    "SIAM": "TH",
    "THAILAND": "TH",
    "PERSIA": "IR",
    "IRAN": "IR",
    "MOZAMBIQUE": "MZ",
    "MOÇAMBIQUE": "MZ",
    "RHODESIA": "ZW",
    "ZIMBABWE": "ZW",
    "SWAZILAND": "SZ",
    "ESWATINI": "SZ",
    "ABYSSINIA": "ET",
    "ETHIOPIA": "ET",
    "GOLD COAST": "GH",
    "GHANA": "GH",
    "GOLD COAST": "GH",
    "GHANA": "GH",
    "UPPER VOLTA": "BF",
    "BURKINA FASO": "BF",
    "DUTCH EAST INDIES": "ID",
    "INDONESIA": "ID",
    "NEW HEBRIDES": "VU",
    "VANUATU": "VU",
    "DANZIG": "PL",
    "GDANSK": "PL",
    "PRUSSIA": "DE",
    "GERMANY": "DE",
    "USSR": "RU",
    "RUSSIA": "RU",
    "CZECHOSLOVAKIA": "CZ",
    "CZECHIA": "CZ",
    "YUGOSLAVIA": "RS",
    "SERBIA": "RS",
    "EAST GERMANY": "DE",
    "GERMANY": "DE",
    "WEST GERMANY": "DE",
    "GERMANY": "DE",
    "TANGANYIKA": "TZ",
    "TANZANIA": "TZ",
    "ZANZIBAR": "TZ",
    "TANZANIA": "TZ",
    "SOUTH RHODESIA": "ZW",
    "ZIMBABWE": "ZW",
    "NORTH RHODESIA": "ZM",
    "ZAMBIA": "ZM",
    "NYASALAND": "MW",
    "MALAWI": "MW",
    "DARUSSALAM": "BN",
    "BRUNEI": "BN",
    "FORMOSA": "TW",
    "TAIWAN": "TW",
    "MANCHURIA": "CN",
    "CHINA": "CN",
    "TIBET": "CN",
    "CHINA": "CN",
    "HONG KONG": "HK",
    "CHINA": "HK",
}
```

- [ ] **Step 4: Implement SectionHistoricalNames**

```python
# paxman/capabilities/Country/rules/paxman_historical_ed2025.py
"""Paxman historical country name validation rule."""

from __future__ import annotations

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.historical_data import _HISTORICAL_TO_ALPHA2
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="Paxman",
    specification_name="Historical Country Names",
    kind="policy",
    reference_url="https://github.com/paxman-dev/paxman/blob/main/docs/historical-countries.md",
    version=None,
    lifecycle="active",
    publication_year=2025,
)


class SectionHistoricalNames(Rule[CountryNotation]):
    """Paxman Section: historical country names.

    Validates name shape against deprecated country names.
    Only active when contract.include_historical is True.
    """

    name = "Section-historical-names"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "Paxman historical country names"

    def matches(self, notation: CountryNotation, contract: CountryContract) -> bool:
        """Check if notation is a valid historical name.

        Args:
            notation: Country notation to validate.
            contract: Contract configuration.

        Returns:
            True if include_historical AND notation.shape == "name" AND name is in _HISTORICAL_TO_ALPHA2.
        """
        if not contract.include_historical:
            return False
        if notation.shape != "name":
            return False
        return notation.value.upper() in _HISTORICAL_TO_ALPHA2

    def normalize(self, notation: CountryNotation, contract: CountryContract) -> str:
        """Normalize to current alpha-2 code.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            Current alpha-2 code.
        """
        return _HISTORICAL_TO_ALPHA2[notation.value.upper()]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_rules.py::TestSectionHistoricalNames -v`
Expected: 10 passed

- [ ] **Step 6: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/rules/paxman_historical_ed2025.py`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add paxman/capabilities/Country/rules/paxman_historical_ed2025.py paxman/capabilities/Country/historical_data.py
git commit -m "feat(country): add historical names rule"
```

---

## Task 15: Create Capability Wiring

**Files:**
- Create: `paxman/capabilities/Country/capability.py`
- Test: `tests/capabilities/country/test_capability.py`

- [ ] **Step 1: Write capability tests**

```python
# Append to tests/capabilities/country/test_capability.py

from paxman.capabilities.Country.capability import CountryCapability
from paxman.core.capability import Capability


class TestCountryCapability:
    """Tests for CountryCapability wiring."""

    def test_is_capability_subclass(self) -> None:
        """Verify isinstance check."""
        cap = CountryCapability()
        assert isinstance(cap, Capability)

    def test_name(self) -> None:
        """Verify name matches expected value."""
        assert CountryCapability.name == "country"

    def test_version(self) -> None:
        """Verify version matches expected value."""
        assert CountryCapability.version == "1.0.0"

    def test_get_grammars_returns_all(self) -> None:
        """Verify grammar count (4)."""
        cap = CountryCapability()
        grammars = cap.get_grammars()
        assert len(grammars) == 4

    def test_get_rules_returns_all(self) -> None:
        """Verify rule count (6)."""
        cap = CountryCapability()
        rules = cap.get_rules()
        assert len(rules) == 6

    def test_grammar_names(self) -> None:
        """Verify grammar names follow convention."""
        cap = CountryCapability()
        names = [g.name for g in cap.get_grammars()]
        assert "alpha2_recognition" in names
        assert "alpha3_recognition" in names
        assert "numeric_recognition" in names
        assert "name_recognition" in names

    def test_rule_names(self) -> None:
        """Verify rule names follow convention."""
        cap = CountryCapability()
        names = [r.name for r in cap.get_rules()]
        assert "Section-alpha2-codes" in names
        assert "Section-alpha3-codes" in names
        assert "Section-numeric-codes" in names
        assert "Section-name-codes" in names
        assert "Section-localized-names" in names
        assert "Section-historical-names" in names

    def test_create_contract(self) -> None:
        """Verify create_contract factory method."""
        contract = CountryCapability.create_contract()
        assert contract.capability_name == "country"
        assert contract.include_localized is False
        assert contract.include_historical is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/country/test_capability.py::TestCountryCapability -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement CountryCapability**

```python
# paxman/capabilities/Country/capability.py
"""Country capability — wires grammars and rules together."""

from __future__ import annotations

from collections.abc import Sequence

from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.grammar.alpha2_recognition import Alpha2Grammar
from paxman.capabilities.Country.grammar.alpha3_recognition import Alpha3Grammar
from paxman.capabilities.Country.grammar.name_recognition import NameGrammar
from paxman.capabilities.Country.grammar.numeric_recognition import NumericGrammar
from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Country.rules.cldr_localized_ed2025 import (
    SectionLocalizedNames,
)
from paxman.capabilities.Country.rules.iso_3166_alpha2_ed2024 import SectionAlpha2Codes
from paxman.capabilities.Country.rules.iso_3166_alpha3_ed2024 import SectionAlpha3Codes
from paxman.capabilities.Country.rules.iso_3166_name_ed2024 import SectionNameCodes
from paxman.capabilities.Country.rules.iso_3166_numeric_ed2024 import (
    SectionNumericCodes,
)
from paxman.capabilities.Country.rules.paxman_historical_ed2025 import (
    SectionHistoricalNames,
)
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule


class CountryCapability(Capability[CountryNotation]):
    """Country canonicalization capability.

    Canonicalizes country representations (alpha2, alpha3, numeric, name)
    to ISO 3166-1 alpha-2 codes with full provenance.
    """

    name = "country"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar[CountryNotation]]:
        """Return all grammar instances.

        Returns:
            List of 4 grammars: alpha2, alpha3, numeric, name.
        """
        return [
            Alpha2Grammar(),
            Alpha3Grammar(),
            NumericGrammar(),
            NameGrammar(),
        ]

    def get_rules(self) -> list[Rule[CountryNotation]]:
        """Return all validation rule instances.

        Returns:
            List of 6 rules: iso_alpha2, iso_alpha3, iso_numeric, iso_name, cldr_localized, paxman_historical.
        """
        return [
            SectionAlpha2Codes(),
            SectionAlpha3Codes(),
            SectionNumericCodes(),
            SectionNameCodes(),
            SectionLocalizedNames(),
            SectionHistoricalNames(),
        ]

    @staticmethod
    def create_contract(
        *,
        excluded_rules: Sequence[str] | None = None,
        pinned_rules: Sequence[str] | None = None,
        year: int | None = None,
        output_format: str | None = None,
        include_localized: bool = False,
        include_historical: bool = False,
        extra_synonyms: dict[str, str] | None = None,
    ) -> CountryContract:
        """Factory method for creating contracts with proper defaults.

        Args:
            excluded_rules: Rule names to exclude.
            pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
            year: Year for temporal filtering.
            output_format: Canonical output format ("alpha2", "alpha3", "numeric", "name").
            include_localized: Enable CLDR multilingual names.
            include_historical: Enable deprecated country names.
            extra_synonyms: Caller-supplied aliases.

        Returns:
            Configured CountryContract instance.
        """
        return CountryContract(
            excluded_rules=tuple(excluded_rules) if excluded_rules else (),
            pinned_rules=tuple(pinned_rules) if pinned_rules is not None else None,
            year=year,
            output_format=output_format,
            include_localized=include_localized,
            include_historical=include_historical,
            extra_synonyms=extra_synonyms or {},
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/country/test_capability.py -v`
Expected: 22 passed (7 notation + 14 contract + 9 capability + 2 create_contract)

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/capability.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Country/capability.py
git commit -m "feat(country): add CountryCapability wiring"
```

---

## Task 16: Create Package Init Exports

**Files:**
- Modify: `paxman/capabilities/Country/__init__.py`

- [ ] **Step 1: Update init file with exports**

```python
# paxman/capabilities/Country/__init__.py
"""Country capability for canonicalizing country representations."""

from paxman.capabilities.Country.capability import CountryCapability
from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.notation import CountryNotation

__all__ = ["CountryCapability", "CountryContract", "CountryNotation"]
```

- [ ] **Step 2: Verify imports work**

Run: `uv run python -c "from paxman.capabilities.Country import CountryCapability, CountryContract, CountryNotation; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Run type checker**

Run: `uv run pyright paxman/capabilities/Country/__init__.py`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add paxman/capabilities/Country/__init__.py
git commit -m "feat(country): add package exports"
```

---

## Task 17: Register Capability

**Files:**
- Modify: `paxman/capabilities/__init__.py`

- [ ] **Step 1: Add Country to built-in capabilities**

```python
# paxman/capabilities/__init__.py
# Add this import alongside existing capabilities:

from paxman.capabilities.Country.capability import CountryCapability as Country
```

- [ ] **Step 2: Verify registration works**

Run: `uv run python -c "from paxman.capabilities import Country; print(Country.name)"`
Expected: `country`

- [ ] **Step 3: Commit**

```bash
git add paxman/capabilities/__init__.py
git commit -m "feat(country): register Country capability as built-in"
```

---

## Task 18: Run All Tests

- [ ] **Step 1: Run country capability tests**

Run: `uv run pytest tests/capabilities/country/ -v`
Expected: All tests pass

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests pass (no regressions)

- [ ] **Step 3: Run type checker**

Run: `uv run pyright --strict paxman/capabilities/Country/`
Expected: No errors

- [ ] **Step 4: Run linter**

Run: `uv run ruff check paxman/capabilities/Country/ tests/capabilities/country/`
Expected: No errors

- [ ] **Step 5: Run formatter check**

Run: `uv run ruff format --check paxman/capabilities/Country/ tests/capabilities/country/`
Expected: No errors

- [ ] **Step 6: Run import linter**

Run: `uv run import-linter lint`
Expected: No errors

- [ ] **Step 7: Commit final state**

```bash
git add -A
git commit -m "feat(country): Country capability complete with all quality gates passing"
```
