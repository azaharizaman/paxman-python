# Phone Number (E.164) Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Phone capability that canonicalizes phone numbers (E.164 international, NANP national, RFC 3966 tel-URI) to E.164 format (`+CCNSN`) with full provenance.

**Architecture:** Shape-aware notation with 4 mutually exclusive grammars (e164, tel-URI, international-00, national) and 5 validation rules. Rules filter by shape discriminator. National rules gate on `default_country` contract parameter. Configurable output format (`e164`, `rfc3966`, `national`).

**Tech Stack:** Python 3.11, dataclasses (frozen=True, slots=True), regex, pytest, pyright, ruff, import-linter

---

## Multi-Recognition Types (Design Requirement)

This capability showcases **all three** `RuleStrategy` types Paxman supports, which no existing capability does:

| Rule | Strategy | Why |
|------|----------|-----|
| `Section 6.1-international-number` | `PARSER` | Structure validation + longest-prefix country-code split (like IP's RFC 5952 PARSER rule) |
| `Section 6.2-country-code` | `LOOKUP_TABLE` | Assigned country code membership (like Country's alpha-2 table) |
| `Section 3-tel-uri` | `PARSER` | RFC 3966 URI grammar parsing |
| `Section 1.1-nanp-structure` | `REGEX` | NANP structure is a regex recognition problem (national rules with regex recognition) |
| `Section 1.2-service-npa` | `LOOKUP_TABLE` | Toll-free/premium NPA table |

National-level validity rules **also** use regex recognition (Section 1.1), demonstrating multi-recognition types at the national layer.

---

## Milestone Roadmap — All Countries with Bounded Validation Sets

**Scope rule for this branch:** implement ONLY Milestone 1 (US / NANP national set). All other milestones are intentionally NOT implemented in this branch — they are enumerated here so reviewers understand the roadmap is deliberate and bounded, not aspirational.

| Milestone | Countries / Plan | CC | Bounded validation set (in scope) | Explicitly OUT of scope |
|-----------|-----------------|----|-----------------------------------|------------------------|
| **M1 (THIS BRANCH)** | United States (NANP) | +1 | NANP structure regex (NPA `[2-9]XX`, NXX `[2-9]XX`, N11 exclusions, 555-01XX reserved); service NPA lookup table (800/833/844/855/866/877/888/900); RFC 3966 tel-URI | Geographic NPA assignment table; 7-digit local dialing; carrier/portability lookups; extensions in canonical output |
| M2 | Canada (NANP) | +1 | Same NANP structure rules; add `default_country="CA"` gate; Canadian-specific NPA reservations | Province-level area code tables |
| M3 | United Kingdom | +44 | 2–5 digit area code prefix table (01, 02, 03, 07, 08, 09); mobile `07xxx` structure; 10-digit NSN | Full geographic number range tables; subscriber number ranges |
| M4 | Germany | +49 | Area code structure (0-prefix, 2–5 digits); mobile `015x/016x/017x`; NSN 10–11 digits | Geographic area code table (3,000+ entries) |
| M5 | France | +33 | 9-digit NSN; `01`–`05` geographic, `06/07` mobile; zero-trunk structure | Subscriber range tables |
| M6 | Japan | +81 | City code ranges (`010`–`099`); mobile `090/080/070`; zero-trunk structure | Geographic area code table |
| M7 | India | +91 | 10-digit NSN; mobile prefix `6/7/8/9`; STD code structure | STD code table (2,000+ entries) |
| M8 | China | +86 | 11-digit mobile `1xx`; landline 10–12 digit structure | Geographic area code table |
| M9 | Australia | +61 | 9-digit NSN; mobile `04`; geographic `02/03/07/08`; toll-free `1800/13xx` | Subscriber range tables |
| M10 | Brazil | +55 | 10–11 digit NSN; 2-digit DDD area codes; mobile `9` prefix | DDD area code table |
| M11 | Russia / Kazakhstan | +7 | 10-digit NSN; 3-digit area code structure | Geographic ABC code table |
| M12 | Shared-cost / satellite | 800, 808, 870, 881–883, 888, 991 | ITU-T special service code membership | — |

**Architecture note for M3+ (deliberate, not implemented here):** each non-NANP milestone (UK, DE, FR, JP, IN, CN, AU, BR, RU) requires a *country-specific national grammar* (e.g., `national_uk_recognition` recognizing `020 7946 0958`, which the NANP-shaped grammar cannot match) plus a dispatch mechanism that selects the national grammar from `default_country`. Milestone 1 ships a single NANP-shaped `national_recognition` grammar with a static `active_grammars` list; the per-country grammar registry/dispatch is a future architectural decision enumerated here so M3+ is understood to be bounded but not yet designed. The rule sets per country (area-code prefix tables, mobile ranges) are fully specified in the table above; only the grammar-dispatch mechanism is deferred.

**Future (non-milestone) work:** RFC 3966 `phone-context` local numbers; extension (`;ext=`) in canonical output; 7-digit NANP local dialing; geographic NPA/NXX assignment tables.

---

## File Structure

```
paxman/capabilities/Phone/
├── __init__.py
├── capability.py
├── contract.py
├── notation.py
├── grammar/
│   ├── __init__.py
│   ├── e164_recognition.py
│   ├── tel_uri_recognition.py
│   ├── international_00_recognition.py
│   └── national_recognition.py
└── rules/
    ├── __init__.py
    ├── e164_ed2010.py
    ├── rfc_3966_ed2004.py
    ├── nanp_ed2024.py
    └── data/
        ├── __init__.py
        ├── e164_country_codes.py
        └── nanp_tables.py

tests/capabilities/phone/
├── __init__.py
├── test_grammar.py
├── test_rules.py
└── test_capability.py

tests/integration/test_phone_pipeline.py   # NEW file (mirrors test_country_pipeline.py)
tests/e2e/test_canonicalize.py             # EXTEND with Phone cases
```

---

## Task 1: Create Directory Structure

**Files:**
- Create: `paxman/capabilities/Phone/__init__.py`
- Create: `paxman/capabilities/Phone/grammar/__init__.py`
- Create: `paxman/capabilities/Phone/rules/__init__.py`
- Create: `paxman/capabilities/Phone/rules/data/__init__.py`
- Create: `tests/capabilities/phone/__init__.py`

- [ ] **Step 1: Create Phone package directories**

```bash
mkdir -p paxman/capabilities/Phone/grammar
mkdir -p paxman/capabilities/Phone/rules/data
mkdir -p tests/capabilities/phone
```

- [ ] **Step 2: Create package init files**

```python
# paxman/capabilities/Phone/__init__.py
"""Phone capability for canonicalizing telephone numbers."""
```

```python
# paxman/capabilities/Phone/grammar/__init__.py
"""Phone recognition grammars."""
```

```python
# paxman/capabilities/Phone/rules/__init__.py
"""Phone validation rules."""
```

```python
# paxman/capabilities/Phone/rules/data/__init__.py
"""Phone lookup table data."""
```

```python
# tests/capabilities/phone/__init__.py
"""Phone capability tests."""
```

- [ ] **Step 3: Verify directory structure**

Run: `find paxman/capabilities/Phone tests/capabilities/phone -type f | sort`
Expected: 5 `__init__.py` files

- [ ] **Step 4: Commit**

```bash
git add paxman/capabilities/Phone tests/capabilities/phone
git commit -m "feat(phone): create directory structure"
```

---

## Task 2: Define Notation

**Files:**
- Create: `paxman/capabilities/Phone/notation.py`
- Test: `tests/capabilities/phone/test_capability.py`

- [ ] **Step 1: Write notation tests**

```python
# tests/capabilities/phone/test_capability.py
"""Tests for Phone capability."""

import pytest
from paxman.capabilities.Phone.notation import PhoneNotation


class TestPhoneNotation:
    """Tests for PhoneNotation dataclass."""

    def test_creates_with_fields(self) -> None:
        """Verify field access."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert notation.shape == "e164"
        assert notation.value == "15551234567"
        assert notation.extension == ""

    def test_creates_with_extension(self) -> None:
        """Verify extension field."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567", extension="890")
        assert notation.extension == "890"

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        with pytest.raises(AttributeError):
            notation.shape = "national"  # type: ignore[misc]

    def test_as_list_returns_correct(self) -> None:
        """Verify list conversion."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert notation.as_list() == ["e164", "15551234567", ""]

    def test_as_list_with_extension(self) -> None:
        """Verify list conversion includes extension."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567", extension="890")
        assert notation.as_list() == ["rfc3966", "15551234567", "890"]

    def test_equality(self) -> None:
        """Verify value equality."""
        n1 = PhoneNotation(shape="e164", value="15551234567")
        n2 = PhoneNotation(shape="e164", value="15551234567")
        assert n1 == n2

    def test_inequality(self) -> None:
        """Verify different values are not equal."""
        n1 = PhoneNotation(shape="e164", value="15551234567")
        n2 = PhoneNotation(shape="e164", value="15551234568")
        assert n1 != n2

    def test_hashable(self) -> None:
        """Verify it can be used in sets or as dict keys."""
        n1 = PhoneNotation(shape="e164", value="15551234567")
        n2 = PhoneNotation(shape="e164", value="15551234567")
        s = {n1, n2}
        assert len(s) == 1
        d = {n1: "value"}
        assert d[n2] == "value"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_capability.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'paxman.capabilities.Phone.notation'"

- [ ] **Step 3: Implement Notation**

```python
# paxman/capabilities/Phone/notation.py
"""Phone notation — intermediate representation for phone number recognition."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PhoneNotation:
    """Intermediate representation for phone number recognition.

    Attributes:
        shape: Discriminator set by grammar ("e164", "national", "rfc3966").
            - "e164": value is the E.164 number digits WITHOUT the leading "+"
              or the international prefix "00" (e.g., "15551234567").
            - "national": value is the domestic dialing digits, optional
              leading trunk "1" preserved (e.g., "15551234567" or "5551234567").
            - "rfc3966": value is the tel-URI number digits WITHOUT "tel:"
              prefix or "+" (e.g., "15551234567").
        value: Digit-only string (no "+", no separators, no "tel:" prefix).
        extension: Digits of the ";ext=" parameter (RFC 3966 only); "" when
            no extension is present.
    """

    shape: str
    value: str
    extension: str = ""

    def as_list(self) -> list[str]:
        """Bridge to generic list[str] interface.

        Returns:
            [shape, value, extension] — shape first for consistent ordering.
        """
        return [self.shape, self.value, self.extension]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_capability.py::TestPhoneNotation -v`
Expected: 8 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/notation.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Phone/notation.py tests/capabilities/phone/test_capability.py
git commit -m "feat(phone): add PhoneNotation dataclass"
```

---

## Task 3: Define Contract

**Files:**
- Create: `paxman/capabilities/Phone/contract.py`
- Test: `tests/capabilities/phone/test_capability.py`

- [ ] **Step 1: Write contract tests**

```python
# Append to tests/capabilities/phone/test_capability.py

from paxman.capabilities.Phone.contract import PhoneContract


class TestPhoneContract:
    """Tests for PhoneContract dataclass."""

    def test_default_capability_name(self) -> None:
        """Verify capability_name is fixed to 'phone'."""
        contract = PhoneContract()
        assert contract.capability_name == "phone"

    def test_capability_name_not_settable(self) -> None:
        """Verify capability_name is not user-settable."""
        with pytest.raises(TypeError):
            PhoneContract(capability_name="other")  # type: ignore[call-arg]

    def test_default_excluded_rules(self) -> None:
        """Verify excluded_rules defaults to empty tuple."""
        contract = PhoneContract()
        assert contract.excluded_rules == ()

    def test_default_pinned_rules(self) -> None:
        """Verify pinned_rules defaults to None."""
        contract = PhoneContract()
        assert contract.pinned_rules is None

    def test_default_year(self) -> None:
        """Verify year defaults to None."""
        contract = PhoneContract()
        assert contract.year is None

    def test_default_output_format(self) -> None:
        """Verify output_format defaults to 'e164'."""
        contract = PhoneContract()
        assert contract.output_format == "e164"

    def test_default_country_none(self) -> None:
        """Verify default_country defaults to None."""
        contract = PhoneContract()
        assert contract.default_country is None

    def test_custom_default_country(self) -> None:
        """Verify default_country can be set."""
        contract = PhoneContract(default_country="US")
        assert contract.default_country == "US"

    def test_custom_output_format(self) -> None:
        """Verify output_format can be set."""
        contract = PhoneContract(output_format="rfc3966")
        assert contract.output_format == "rfc3966"

    def test_active_grammars_returns_all(self) -> None:
        """Verify all 4 grammars are active by default."""
        contract = PhoneContract()
        grammars = contract.active_grammars
        assert len(grammars) == 4
        assert "e164_recognition" in grammars
        assert "tel_uri_recognition" in grammars
        assert "international_00_recognition" in grammars
        assert "national_recognition" in grammars

    def test_as_dict_contains_all_fields(self) -> None:
        """Verify as_dict serializes all fields."""
        contract = PhoneContract()
        d = contract.as_dict()
        assert "capability_name" in d
        assert "default_country" in d
        assert "output_format" in d
        assert "excluded_rules" in d
        assert "pinned_rules" in d
        assert "year" in d

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        contract = PhoneContract()
        with pytest.raises(AttributeError):
            contract.year = 2024  # type: ignore[misc]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_capability.py::TestPhoneContract -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'paxman.capabilities.Phone.contract'"

- [ ] **Step 3: Implement Contract**

```python
# paxman/capabilities/Phone/contract.py
"""Phone contract — user-facing configuration for Phone capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PhoneContract:
    """User-facing configuration for Phone capability.

    Attributes:
        capability_name: Fixed to "phone" (not user-settable).
        default_country: ISO 3166-1 alpha-2 country code used to resolve
            national numbers (e.g., "US"). When None, national-shaped input
            is recognized but never validated (status INVALID).
        output_format: Canonical output format ("e164" default, "rfc3966",
            or "national" for the national significant number).
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
        year: Year for temporal filtering.
    """

    capability_name: str = field(default="phone", init=False)

    # Capability-specific fields
    default_country: str | None = None
    output_format: str = "e164"

    # Standard contract fields
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None

    @property
    def active_grammars(self) -> list[str]:
        """All grammars active by default.

        All grammars are cheap regex scans; rules filter by shape and by
        contract parameters (e.g., national rules gate on default_country).

        Returns:
            List of grammar names to activate.
        """
        return [
            "e164_recognition",
            "tel_uri_recognition",
            "international_00_recognition",
            "national_recognition",
        ]

    def as_dict(self) -> dict[str, Any]:
        """Serialize for replay hash computation.

        Returns:
            Dictionary representation of all fields.
        """
        return {
            "capability_name": self.capability_name,
            "default_country": self.default_country,
            "output_format": self.output_format,
            "excluded_rules": self.excluded_rules,
            "pinned_rules": self.pinned_rules,
            "year": self.year,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_capability.py::TestPhoneContract -v`
Expected: 12 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/contract.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Phone/contract.py
git commit -m "feat(phone): add PhoneContract dataclass"
```

---

## Task 4: Create Lookup Tables

**Files:**
- Create: `paxman/capabilities/Phone/rules/data/e164_country_codes.py`
- Create: `paxman/capabilities/Phone/rules/data/nanp_tables.py`

- [ ] **Step 1: Create E.164 country code table**

```python
# paxman/capabilities/Phone/rules/data/e164_country_codes.py
"""ITU-T E.164 assigned country code lookup table and longest-prefix splitter.

All codes derived from ITU-T E.164 (11/2010), Annex A — Table of assigned
country codes.
Source: https://www.itu.int/rec/T-REC-E.164/

The table is a data artifact; ``split_country_code`` is the single helper
that both E.164 and RFC 3966 rules share to resolve country-code prefixes.
"""

from __future__ import annotations

# Country code -> country/territory/plan name (all assigned E.164 codes)
ASSIGNED_COUNTRY_CODES: dict[str, str] = {
    # Zone 1
    "1": "North American Numbering Plan (US, CA, Caribbean)",
    # Zone 2 (Africa)
    "20": "Egypt",
    "211": "South Sudan",
    "212": "Morocco",
    "213": "Algeria",
    "216": "Tunisia",
    "218": "Libya",
    "220": "Gambia",
    "221": "Senegal",
    "222": "Mauritania",
    "223": "Mali",
    "224": "Guinea",
    "225": "Cote d'Ivoire",
    "226": "Burkina Faso",
    "227": "Niger",
    "228": "Togo",
    "229": "Benin",
    "230": "Mauritius",
    "231": "Liberia",
    "232": "Sierra Leone",
    "233": "Ghana",
    "234": "Nigeria",
    "235": "Chad",
    "236": "Central African Republic",
    "237": "Cameroon",
    "238": "Cape Verde",
    "239": "Sao Tome and Principe",
    "240": "Equatorial Guinea",
    "241": "Gabon",
    "242": "Republic of the Congo",
    "243": "Democratic Republic of the Congo",
    "244": "Angola",
    "245": "Guinea-Bissau",
    "246": "British Indian Ocean Territory (Diego Garcia)",
    "247": "Ascension Island",
    "248": "Seychelles",
    "249": "Sudan",
    "250": "Rwanda",
    "251": "Ethiopia",
    "252": "Somalia",
    "253": "Djibouti",
    "254": "Kenya",
    "255": "Tanzania",
    "256": "Uganda",
    "257": "Burundi",
    "258": "Mozambique",
    "260": "Zambia",
    "261": "Madagascar",
    "262": "Reunion",
    "263": "Zimbabwe",
    "264": "Namibia",
    "265": "Malawi",
    "266": "Lesotho",
    "267": "Botswana",
    "268": "Eswatini",
    "269": "Comoros",
    "27": "South Africa",
    "290": "Saint Helena",
    "291": "Eritrea",
    "297": "Aruba",
    "298": "Faroe Islands",
    "299": "Greenland",
    # Zones 3/4 (Europe)
    "30": "Greece",
    "31": "Netherlands",
    "32": "Belgium",
    "33": "France",
    "34": "Spain",
    "350": "Gibraltar",
    "351": "Portugal",
    "352": "Luxembourg",
    "353": "Ireland",
    "354": "Iceland",
    "355": "Albania",
    "356": "Malta",
    "357": "Cyprus",
    "358": "Finland",
    "359": "Bulgaria",
    "36": "Hungary",
    "370": "Lithuania",
    "371": "Latvia",
    "372": "Estonia",
    "373": "Moldova",
    "374": "Armenia",
    "375": "Belarus",
    "376": "Andorra",
    "377": "Monaco",
    "378": "San Marino",
    "379": "Vatican City",
    "380": "Ukraine",
    "381": "Serbia",
    "382": "Montenegro",
    "383": "Kosovo",
    "385": "Croatia",
    "386": "Slovenia",
    "387": "Bosnia and Herzegovina",
    "389": "North Macedonia",
    "39": "Italy",
    "40": "Romania",
    "41": "Switzerland",
    "420": "Czech Republic",
    "421": "Slovakia",
    "423": "Liechtenstein",
    "43": "Austria",
    "44": "United Kingdom",
    "45": "Denmark",
    "46": "Sweden",
    "47": "Norway",
    "48": "Poland",
    "49": "Germany",
    # Zone 5 (Americas)
    "500": "Falkland Islands",
    "501": "Belize",
    "502": "Guatemala",
    "503": "El Salvador",
    "504": "Honduras",
    "505": "Nicaragua",
    "506": "Costa Rica",
    "507": "Panama",
    "508": "Saint Pierre and Miquelon",
    "509": "Haiti",
    "51": "Peru",
    "52": "Mexico",
    "53": "Cuba",
    "54": "Argentina",
    "55": "Brazil",
    "56": "Chile",
    "57": "Colombia",
    "58": "Venezuela",
    "590": "Guadeloupe",
    "591": "Bolivia",
    "592": "Guyana",
    "593": "Ecuador",
    "594": "French Guiana",
    "595": "Paraguay",
    "596": "Martinique",
    "597": "Suriname",
    "598": "Uruguay",
    "599": "Caribbean Netherlands / Curacao",
    # Zone 6 (Oceania)
    "60": "Malaysia",
    "61": "Australia",
    "62": "Indonesia",
    "63": "Philippines",
    "64": "New Zealand",
    "65": "Singapore",
    "66": "Thailand",
    "670": "Timor-Leste",
    "672": "Antarctica / Australian external territories",
    "673": "Brunei",
    "674": "Nauru",
    "675": "Papua New Guinea",
    "676": "Tonga",
    "677": "Solomon Islands",
    "678": "Vanuatu",
    "679": "Fiji",
    "680": "Palau",
    "681": "Wallis and Futuna",
    "682": "Cook Islands",
    "683": "Niue",
    "684": "American Samoa",
    "685": "Samoa",
    "686": "Kiribati",
    "687": "New Caledonia",
    "688": "Tuvalu",
    "689": "French Polynesia",
    "690": "Tokelau",
    "691": "Micronesia",
    "692": "Marshall Islands",
    # Zone 7 (Russia / Kazakhstan)
    "7": "Russia / Kazakhstan",
    # Zone 8 (East Asia + special services)
    "800": "International Freephone",
    "808": "International Shared Cost",
    "81": "Japan",
    "82": "South Korea",
    "84": "Vietnam",
    "850": "North Korea",
    "852": "Hong Kong",
    "853": "Macau",
    "855": "Cambodia",
    "856": "Laos",
    "86": "China",
    "870": "Inmarsat",
    "878": "Universal Personal Telecommunications",
    "880": "Bangladesh",
    "881": "Global Mobile Satellite System",
    "882": "International Networks",
    "883": "International Networks",
    "886": "Taiwan",
    "888": "Telecommunications for Disaster Relief",
    # Zone 9 (Middle East / Central-South Asia)
    "90": "Turkey",
    "91": "India",
    "92": "Pakistan",
    "93": "Afghanistan",
    "94": "Sri Lanka",
    "95": "Myanmar",
    "960": "Maldives",
    "961": "Lebanon",
    "962": "Jordan",
    "963": "Syria",
    "964": "Iraq",
    "965": "Kuwait",
    "966": "Saudi Arabia",
    "967": "Yemen",
    "968": "Oman",
    "970": "Palestine",
    "971": "United Arab Emirates",
    "972": "Israel",
    "973": "Bahrain",
    "974": "Qatar",
    "975": "Bhutan",
    "976": "Mongolia",
    "977": "Nepal",
    "98": "Iran",
    "991": "International Telecommunications Public Correspondence Service",
    "992": "Tajikistan",
    "993": "Turkmenistan",
    "994": "Azerbaijan",
    "995": "Georgia",
    "996": "Kyrgyzstan",
    "998": "Uzbekistan",
}


def split_country_code(value: str) -> str | None:
    """Split the longest matching country code prefix off a digit string.

    Args:
        value: Digit-only E.164 number (no leading +).

    Returns:
        The country code string if an assigned prefix matches, else None.
        Longest-prefix matching ensures e.g. "886..." resolves to Taiwan
        (886), not China (86) with a stray leading 6. A bare country code
        with no NSN (e.g. "1" or "44") returns None.
    """
    for length in (3, 2, 1):
        if len(value) > length and value[:length] in ASSIGNED_COUNTRY_CODES:
            return value[:length]
    return None
```

- [ ] **Step 2: Create NANP tables**

```python
# paxman/capabilities/Phone/rules/data/nanp_tables.py
"""North American Numbering Plan (NANP) lookup tables.

Structure rules derived from the NANP (administered by NANPA).
Source: https://www.nanpa.com/
"""

from __future__ import annotations

# N11 service codes — NOT assignable as NPA or NXX (911, 411, etc.)
N11_CODES: frozenset[str] = frozenset(
    {"211", "311", "411", "511", "611", "711", "811", "911"}
)

# Service NPAs assigned by NANPA: toll-free + premium rate
SERVICE_NPAS: frozenset[str] = frozenset(
    {"800", "833", "844", "855", "866", "877", "888", "900"}
)
```

Note: The fictional-number reservation (555-0100 through 555-0199, i.e. NXX `555` with a line number starting `01`) is a *predicate*, not a table — it is implemented inline in `nanp_ed2024.py` (see Task 11).

- [ ] **Step 3: Verify data modules load**

Run: `uv run python -c "from paxman.capabilities.Phone.rules.data.e164_country_codes import ASSIGNED_COUNTRY_CODES; print(len(ASSIGNED_COUNTRY_CODES))"`
Expected: `217` (verified count — pin this in test_data.py, see Step 4)

Run: `uv run python -c "from paxman.capabilities.Phone.rules.data.nanp_tables import N11_CODES, SERVICE_NPAS; print(len(N11_CODES), len(SERVICE_NPAS))"`
Expected: `8 8`

- [ ] **Step 4: Write data-integrity tests**

```python
# tests/capabilities/phone/test_data.py
"""Tests for Phone lookup table data integrity."""

from paxman.capabilities.Phone.rules.data.e164_country_codes import (
    ASSIGNED_COUNTRY_CODES,
)
from paxman.capabilities.Phone.rules.data.nanp_tables import N11_CODES, SERVICE_NPAS


class TestE164CountryCodes:
    """Tests for the E.164 country code table."""

    def test_verified_count(self) -> None:
        """The table is locked to the verified count of assigned codes."""
        assert len(ASSIGNED_COUNTRY_CODES) == 217

    def test_all_keys_are_1_to_3_digits(self) -> None:
        """Every country code is 1-3 digits long."""
        for code in ASSIGNED_COUNTRY_CODES:
            assert code.isdigit()
            assert 1 <= len(code) <= 3

    def test_no_code_is_prefix_of_another(self) -> None:
        """Longest-prefix matching must be deterministic.

        No assigned country code may be a prefix of another assigned code;
        otherwise split_country_code's longest-prefix search would be
        ambiguous (e.g., 1 vs 12, 80 vs 800).
        """
        codes = sorted(ASSIGNED_COUNTRY_CODES)
        for i, short in enumerate(codes):
            for long in codes[i + 1:]:
                assert not long.startswith(short), (
                    f"{long} starts with {short} — ambiguous country code"
                )

    def test_known_codes_present(self) -> None:
        """Spot-check a handful of assigned codes across zones."""
        assert "1" in ASSIGNED_COUNTRY_CODES  # NANP
        assert "44" in ASSIGNED_COUNTRY_CODES  # UK
        assert "886" in ASSIGNED_COUNTRY_CODES  # Taiwan
        assert "800" in ASSIGNED_COUNTRY_CODES  # International Freephone

    def test_unassigned_codes_absent(self) -> None:
        """Codes known to be unassigned are not in the table."""
        assert "999" not in ASSIGNED_COUNTRY_CODES
        assert "0" not in ASSIGNED_COUNTRY_CODES
        assert "15" not in ASSIGNED_COUNTRY_CODES


class TestNanpTables:
    """Tests for NANP lookup tables."""

    def test_n11_codes_exact(self) -> None:
        """N11 service codes are exactly the 8 reserved codes."""
        assert N11_CODES == {
            "211", "311", "411", "511", "611", "711", "811", "911"
        }

    def test_service_npas_exact(self) -> None:
        """Service NPAs are exactly the toll-free and premium codes."""
        assert SERVICE_NPAS == {
            "800", "833", "844", "855", "866", "877", "888", "900"
        }
```

- [ ] **Step 5: Run data tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_data.py -v`
Expected: 7 passed

- [ ] **Step 6: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/rules/data/`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add paxman/capabilities/Phone/rules/data/ tests/capabilities/phone/test_data.py
git commit -m "feat(phone): add E.164 country code and NANP lookup tables"
```

---

## Task 5: Create E.164 Grammar

**Files:**
- Create: `paxman/capabilities/Phone/grammar/e164_recognition.py`
- Test: `tests/capabilities/phone/test_grammar.py`

- [ ] **Step 1: Write e164 grammar tests**

```python
# tests/capabilities/phone/test_grammar.py
"""Tests for Phone recognition grammars."""

import pytest
from paxman.capabilities.Phone.grammar.e164_recognition import E164Grammar


class TestE164Grammar:
    """Tests for E164Grammar."""

    def setup_method(self) -> None:
        self.grammar = E164Grammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: grammar finds e164 pattern."""
        results = self.grammar.recognize("+15551234567")
        assert len(results) == 1
        assert results[0].shape == "e164"
        assert results[0].value == "15551234567"

    def test_recognizes_with_spaces(self) -> None:
        """Edge case: spaces between digit groups."""
        results = self.grammar.recognize("+1 555 123 4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_with_dashes(self) -> None:
        """Edge case: dashes between digit groups."""
        results = self.grammar.recognize("+44-20-7946-0958")
        assert len(results) == 1
        assert results[0].value == "442079460958"

    def test_recognizes_with_dots(self) -> None:
        """Edge case: dots between digit groups."""
        results = self.grammar.recognize("+1.555.123.4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_with_parens(self) -> None:
        """Edge case: parentheses around area code."""
        results = self.grammar.recognize("+1 (555) 123-4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_in_text(self) -> None:
        """Input contains e164 number within surrounding text."""
        results = self.grammar.recognize("Call me at +15551234567 today")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_multiple(self) -> None:
        """Input contains multiple e164 matches."""
        results = self.grammar.recognize("+15551234567 or +442079460958")
        assert len(results) == 2

    def test_ignores_number_without_plus(self) -> None:
        """Grammar does not match numbers without the + prefix."""
        results = self.grammar.recognize("15551234567")
        assert len(results) == 0

    def test_ignores_national_format(self) -> None:
        """Grammar does not match national (no +) formatting."""
        results = self.grammar.recognize("(555) 123-4567")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "e164_recognition"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_grammar.py::TestE164Grammar -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement E164Grammar**

```python
# paxman/capabilities/Phone/grammar/e164_recognition.py
"""E.164 international number recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# A "+" followed by digits with optional separators (space, dash, dot, parens).
# The grammar is intentionally loose — validation happens in rules. The
# negative lookbehind excludes both digits and ":" so tel: URIs are NOT
# double-matched by this grammar (RFC 3966 handles those). The "+" itself is
# stripped from the value (digit-only), so "+" is in the separator map.
_E164_PATTERN = re.compile(r"(?<![\d:])\+\d[\d\s().\-]*")

_ALLOWED_SEPARATORS = str.maketrans("", "", "+ ().-")


class E164Grammar(Grammar[PhoneNotation]):
    """Recognizes E.164-style international numbers (leading +).

    Examples: "+15551234567", "+1 555 123 4567", "+44-20-7946-0958"
    Non-examples: "15551234567" (no +), "(555) 123-4567" (national format)
    """

    name = "e164_recognition"

    def recognize(self, text: str) -> list[PhoneNotation]:
        """Extract e164 patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of PhoneNotations with shape="e164" and value set to the
            digit-only number (leading "+" and separators removed).
        """
        results: list[PhoneNotation] = []
        seen: set[tuple[str, ...]] = set()
        for match in _E164_PATTERN.finditer(text):
            digits = match.group(0).translate(_ALLOWED_SEPARATORS)
            notation = PhoneNotation(shape="e164", value=digits)
            key = tuple(notation.as_list())
            if key not in seen:
                seen.add(key)
                results.append(notation)
        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_grammar.py::TestE164Grammar -v`
Expected: 11 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/grammar/e164_recognition.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Phone/grammar/e164_recognition.py tests/capabilities/phone/test_grammar.py
git commit -m "feat(phone): add E.164 grammar"
```

---

## Task 6: Create tel-URI Grammar

**Files:**
- Create: `paxman/capabilities/Phone/grammar/tel_uri_recognition.py`
- Test: `tests/capabilities/phone/test_grammar.py`

- [ ] **Step 1: Write tel-URI grammar tests**

```python
# Append to tests/capabilities/phone/test_grammar.py

from paxman.capabilities.Phone.grammar.tel_uri_recognition import TelUriGrammar


class TestTelUriGrammar:
    """Tests for TelUriGrammar."""

    def setup_method(self) -> None:
        self.grammar = TelUriGrammar()

    def test_recognizes_global_number(self) -> None:
        """Happy path: tel: URI with global number."""
        results = self.grammar.recognize("tel:+15551234567")
        assert len(results) == 1
        assert results[0].shape == "rfc3966"
        assert results[0].value == "15551234567"

    def test_recognizes_with_dashes(self) -> None:
        """Edge case: dashes in URI number."""
        results = self.grammar.recognize("tel:+1-201-555-0123")
        assert len(results) == 1
        assert results[0].value == "12015550123"

    def test_recognizes_with_extension(self) -> None:
        """Edge case: ;ext= parameter."""
        results = self.grammar.recognize("tel:+15551234567;ext=890")
        assert len(results) == 1
        assert results[0].value == "15551234567"
        assert results[0].extension == "890"

    def test_recognizes_in_text(self) -> None:
        """Input contains tel: URI within surrounding text."""
        results = self.grammar.recognize("Reach me at tel:+15551234567 now")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_uppercase_scheme(self) -> None:
        """Edge case: uppercase TEL: scheme."""
        results = self.grammar.recognize("TEL:+15551234567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_ignores_plain_number(self) -> None:
        """Grammar does not match numbers without tel: scheme."""
        results = self.grammar.recognize("+15551234567")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "tel_uri_recognition"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_grammar.py::TestTelUriGrammar -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement TelUriGrammar**

```python
# paxman/capabilities/Phone/grammar/tel_uri_recognition.py
"""RFC 3966 tel-URI recognition grammar."""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# tel: URI with global number digits (optional separators) and optional
# ";ext=" parameter. The scheme is matched case-insensitively. The "+" in
# the global number is stripped from the value (digit-only), so "+" is in
# the separator map.
_TEL_URI_PATTERN = re.compile(
    r"tel:([+\d][\d\s().\-]*)(?:;ext=(\d+))?", re.IGNORECASE
)

_ALLOWED_SEPARATORS = str.maketrans("", "", "+ ().-")


class TelUriGrammar(Grammar[PhoneNotation]):
    """Recognizes RFC 3966 tel: URIs.

    Examples: "tel:+15551234567", "tel:+1-201-555-0123;ext=890"
    Non-examples: "+15551234567" (no tel: scheme)
    """

    name = "tel_uri_recognition"

    def recognize(self, text: str) -> list[PhoneNotation]:
        """Extract tel: URI patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of PhoneNotations with shape="rfc3966". value is the
            digit-only number (leading "+" and separators removed);
            extension is the ";ext=" parameter value if present.
        """
        results: list[PhoneNotation] = []
        seen: set[tuple[str, ...]] = set()
        for match in _TEL_URI_PATTERN.finditer(text):
            digits = match.group(1).translate(_ALLOWED_SEPARATORS)
            extension = match.group(2) or ""
            notation = PhoneNotation(shape="rfc3966", value=digits, extension=extension)
            key = tuple(notation.as_list())
            if key not in seen:
                seen.add(key)
                results.append(notation)
        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_grammar.py::TestTelUriGrammar -v`
Expected: 8 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/grammar/tel_uri_recognition.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Phone/grammar/tel_uri_recognition.py tests/capabilities/phone/test_grammar.py
git commit -m "feat(phone): add tel-URI grammar"
```

---

## Task 7: Create International 00 Grammar

**Files:**
- Create: `paxman/capabilities/Phone/grammar/international_00_recognition.py`
- Test: `tests/capabilities/phone/test_grammar.py`

- [ ] **Step 1: Write international 00 grammar tests**

```python
# Append to tests/capabilities/phone/test_grammar.py

from paxman.capabilities.Phone.grammar.international_00_recognition import (
    International00Grammar,
)


class TestInternational00Grammar:
    """Tests for International00Grammar."""

    def setup_method(self) -> None:
        self.grammar = International00Grammar()

    def test_recognizes_valid_input(self) -> None:
        """Happy path: 00-prefixed international number."""
        results = self.grammar.recognize("00 44 20 7946 0958")
        assert len(results) == 1
        assert results[0].shape == "e164"
        assert results[0].value == "442079460958"

    def test_recognizes_compact(self) -> None:
        """Edge case: compact digits."""
        results = self.grammar.recognize("00442079460958")
        assert len(results) == 1
        assert results[0].value == "442079460958"

    def test_recognizes_in_text(self) -> None:
        """Input contains 00 number within surrounding text."""
        results = self.grammar.recognize("Dial 00 44 20 7946 0958 from abroad")
        assert len(results) == 1
        assert results[0].value == "442079460958"

    def test_ignores_number_with_plus(self) -> None:
        """Grammar does not match +-prefixed numbers."""
        results = self.grammar.recognize("+442079460958")
        assert len(results) == 0

    def test_ignores_single_zero(self) -> None:
        """Grammar does not match a single leading zero."""
        results = self.grammar.recognize("0 44 20 7946 0958")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "international_00_recognition"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_grammar.py::TestInternational00Grammar -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement International00Grammar**

```python
# paxman/capabilities/Phone/grammar/international_00_recognition.py
"""International 00-prefix recognition grammar.

The international prefix "00" is the ITU-T E.164 recommended prefix used
when dialing from within most countries. The digits AFTER the prefix form
the E.164 number, so this grammar produces shape="e164" with the prefix
stripped.
"""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# "00" followed by the international number digits (optional separators).
# The leading digit of the number must be 1-9 (country codes never start
# with 0), and a single "0" alone is not the international prefix.
# Separators between "00" and the first digit are allowed ("00 44 ...").
_INTERNATIONAL_00_PATTERN = re.compile(r"(?<!\d)00[\s.\-]*(?=[1-9])\d[\d\s().\-]*")

_ALLOWED_SEPARATORS = str.maketrans("", "", " ().-")


class International00Grammar(Grammar[PhoneNotation]):
    """Recognizes international numbers written with the 00 prefix.

    Examples: "00 44 20 7946 0958", "00442079460958"
    Non-examples: "+442079460958" (has +), "0 44 20 7946 0958" (single 0)
    """

    name = "international_00_recognition"

    def recognize(self, text: str) -> list[PhoneNotation]:
        """Extract 00-prefixed international patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of PhoneNotations with shape="e164". value is the digit-only
            number with the "00" prefix stripped (the E.164 number itself).
        """
        results: list[PhoneNotation] = []
        seen: set[tuple[str, ...]] = set()
        for match in _INTERNATIONAL_00_PATTERN.finditer(text):
            raw = match.group(0)
            # Strip the leading "00" before removing separators.
            digits = raw[2:].translate(_ALLOWED_SEPARATORS)
            notation = PhoneNotation(shape="e164", value=digits)
            key = tuple(notation.as_list())
            if key not in seen:
                seen.add(key)
                results.append(notation)
        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_grammar.py::TestInternational00Grammar -v`
Expected: 7 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/grammar/international_00_recognition.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Phone/grammar/international_00_recognition.py tests/capabilities/phone/test_grammar.py
git commit -m "feat(phone): add international 00 grammar"
```

---

## Task 8: Create National Grammar

**Files:**
- Create: `paxman/capabilities/Phone/grammar/national_recognition.py`
- Test: `tests/capabilities/phone/test_grammar.py`

- [ ] **Step 1: Write national grammar tests**

```python
# Append to tests/capabilities/phone/test_grammar.py

from paxman.capabilities.Phone.grammar.national_recognition import NationalGrammar


class TestNationalGrammar:
    """Tests for NationalGrammar."""

    def setup_method(self) -> None:
        self.grammar = NationalGrammar()

    def test_recognizes_parenthesized(self) -> None:
        """Happy path: (NPA) NXX-XXXX format."""
        results = self.grammar.recognize("(555) 123-4567")
        assert len(results) == 1
        assert results[0].shape == "national"
        assert results[0].value == "5551234567"

    def test_recognizes_dashes(self) -> None:
        """Edge case: NPA-NXX-XXXX format."""
        results = self.grammar.recognize("555-123-4567")
        assert len(results) == 1
        assert results[0].value == "5551234567"

    def test_recognizes_dots(self) -> None:
        """Edge case: NPA.NXX.XXXX format."""
        results = self.grammar.recognize("555.123.4567")
        assert len(results) == 1
        assert results[0].value == "5551234567"

    def test_recognizes_spaces(self) -> None:
        """Edge case: space-separated format."""
        results = self.grammar.recognize("555 123 4567")
        assert len(results) == 1
        assert results[0].value == "5551234567"

    def test_recognizes_with_trunk(self) -> None:
        """Edge case: leading trunk 1 preserved."""
        results = self.grammar.recognize("1-555-123-4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_trunk_with_parens(self) -> None:
        """Edge case: trunk with parenthesized NPA."""
        results = self.grammar.recognize("1 (555) 123-4567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_recognizes_in_text(self) -> None:
        """Input contains national number within surrounding text."""
        results = self.grammar.recognize("Call (555) 123-4567 today")
        assert len(results) == 1
        assert results[0].value == "5551234567"

    def test_ignores_international(self) -> None:
        """Grammar does not match +-prefixed numbers (compact)."""
        results = self.grammar.recognize("+15551234567")
        assert len(results) == 0

    def test_ignores_international_with_separators(self) -> None:
        """Grammar does not match inside separated E.164 numbers.

        Regression for spec review: the lookbehind must reject matches whose
        preceding characters belong to an E.164 number ("+1-555-123-4567"
        belongs to the e164 grammar), not just compact "+15551234567".
        """
        for text in ("+1-555-123-4567", "+1 555 123 4567", "+1.555.123.4567"):
            results = self.grammar.recognize(text)
            assert len(results) == 0

    def test_ignores_international_with_parens(self) -> None:
        """Grammar does not match inside parenthesized E.164 numbers."""
        results = self.grammar.recognize("+1 (555) 123-4567")
        assert len(results) == 0

    def test_ignores_tel_uri(self) -> None:
        """Grammar does not match inside tel: URIs."""
        for text in ("tel:+1-201-555-0123", "tel:+15551234567", "tel:+1 (555) 123-4567"):
            results = self.grammar.recognize(text)
            assert len(results) == 0

    def test_ignores_short_number(self) -> None:
        """Grammar does not match 7-digit local-only numbers."""
        results = self.grammar.recognize("555-1234")
        assert len(results) == 0

    def test_returns_empty_for_empty_input(self) -> None:
        """Empty string returns empty list."""
        results = self.grammar.recognize("")
        assert results == []

    def test_name(self) -> None:
        """Verify grammar name."""
        assert self.grammar.name == "national_recognition"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_grammar.py::TestNationalGrammar -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement NationalGrammar**

```python
# paxman/capabilities/Phone/grammar/national_recognition.py
"""NANP national number recognition grammar.

Recognizes domestic (NANP-style) dialing formats: optional trunk "1",
optional parenthesized NPA, then 3-3-4 digit groups with any of space,
dash, or dot separators. This grammar is deliberately NANP-shaped for
Milestone 1; future milestones add country-specific national grammars.
"""

from __future__ import annotations

import re

from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.domain import Grammar

# Optional trunk 1, optional (NPA), NXX, XXXX. NPA first digit 2-9 is a
# recognition heuristic — strict validation (including NXX first digit 2-9)
# happens in the rules. NXX is deliberately loose here so the grammar
# recognizes the NANP *shape* even for unassignable exchanges (e.g.,
# "555-123-4567"), which the NANP rule then rejects as INVALID.
#
# Four fixed-width negative lookbehinds ensure this grammar does NOT match
# inside E.164 numbers or tel: URIs (those belong to the e164 / tel-URI
# grammars). They reject a match when the characters immediately before it
# belong to an international number:
#   1. digit or "+"          -> "+15551234567" (compact)
#   2. separator after d/+   -> "+1-555-123-4567", "+1 555 123 4567", "+1.555..."
#   3. "( " after sep after d/+ -> "+1 (555) 123-4567" (parens w/ separator)
#   4. "(" directly after d/+ -> "+1(555)123-4567"  (parens, no separator)
_NATIONAL_PATTERN = re.compile(
    r"(?<![\d+])(?<![\d+][\s.\-])(?<![\d+][\s.\-]\()(?<![\d+]\()"
    r"(?:1[\s.\-]?)?\(?([2-9]\d{2})\)?[\s.\-]?"
    r"(\d{3})[\s.\-]?(\d{4})(?!\d)"
)

_ALLOWED_SEPARATORS = str.maketrans("", "", " ().-")


class NationalGrammar(Grammar[PhoneNotation]):
    """Recognizes NANP national dialing formats.

    Examples: "(555) 123-4567", "555-123-4567", "1-555-123-4567"
    Non-examples: "+15551234567" (international), "555-1234" (7-digit local)
    """

    name = "national_recognition"

    def recognize(self, text: str) -> list[PhoneNotation]:
        """Extract national patterns from text.

        Args:
            text: Raw input text.

        Returns:
            List of PhoneNotations with shape="national". value is the
            digit-only number; a leading trunk "1" is preserved when present.
        """
        results: list[PhoneNotation] = []
        seen: set[tuple[str, ...]] = set()
        for match in _NATIONAL_PATTERN.finditer(text):
            digits = match.group(0).translate(_ALLOWED_SEPARATORS)
            notation = PhoneNotation(shape="national", value=digits)
            key = tuple(notation.as_list())
            if key not in seen:
                seen.add(key)
                results.append(notation)
        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_grammar.py::TestNationalGrammar -v`
Expected: 14 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/grammar/national_recognition.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Phone/grammar/national_recognition.py tests/capabilities/phone/test_grammar.py
git commit -m "feat(phone): add national (NANP) grammar"
```

---

## Task 8b: Grammar Test Hygiene (code-review fold-in)

**Files:**
- Update: `tests/capabilities/phone/test_grammar.py`
- Update: `paxman/capabilities/Phone/grammar/international_00_recognition.py` (comment only)

The code-quality review of Tasks 4-8 approved the wave with 4 minor hygiene items. Address them:

- [ ] **Step 1: Add dedup + multi-match + boundary tests**

Append to `tests/capabilities/phone/test_grammar.py`:

```python
# Append to tests/capabilities/phone/test_grammar.py


class TestGrammarDedup:
    """Dedup behavior across grammars (same value via different formats)."""

    def setup_method(self) -> None:
        self.e164 = E164Grammar()
        self.tel_uri = TelUriGrammar()
        self.i00 = International00Grammar()
        self.national = NationalGrammar()

    def test_e164_dedups_same_value_different_formats(self) -> None:
        """The same number in two formats yields one notation (seen-set)."""
        results = self.e164.recognize("Call +1 555 123 4567 or +15551234567")
        assert len(results) == 1
        assert results[0].value == "15551234567"

    def test_tel_uri_multiple_matches(self) -> None:
        """Multiple distinct tel: URIs are all returned."""
        results = self.tel_uri.recognize("tel:+15551234567 and tel:+442079460958")
        assert len(results) == 2

    def test_i00_multiple_matches(self) -> None:
        """Multiple distinct 00-prefixed numbers are all returned."""
        results = self.i00.recognize("00 44 20 7946 0958 or 00 1 555 234 5678")
        assert len(results) == 2

    def test_national_multiple_matches(self) -> None:
        """Multiple distinct national numbers are all returned."""
        results = self.national.recognize(
            "Call (555) 123-4567 today or (212) 234-5678"
        )
        assert len(results) == 2

    def test_e164_trailing_period_still_digit_correct(self) -> None:
        """A trailing sentence period is stripped, value stays digit-only."""
        results = self.e164.recognize("End of +15551234567.")
        assert len(results) == 1
        assert results[0].value == "15551234567"


class TestInternational00Boundary:
    """Boundary cases for the 00-prefix lookbehind."""

    def setup_method(self) -> None:
        self.grammar = International00Grammar()

    def test_ignores_00_embedded_in_digits(self) -> None:
        """'100442079460958' must NOT match (00 preceded by digit)."""
        results = self.grammar.recognize("100442079460958")
        assert len(results) == 0

    def test_ignores_00_after_plus(self) -> None:
        """'+00442079460958' is contradictory input; 00 grammar skips it."""
        # The e164 grammar may match it; the 00 grammar must not treat
        # '+00...' as a 00-prefixed number.
        results = self.grammar.recognize("+00442079460958")
        assert len(results) == 0
```

- [ ] **Step 2: Update International00Grammar comment**

In `paxman/capabilities/Phone/grammar/international_00_recognition.py`, extend the comment above `_INTERNATIONAL_00_PATTERN` to note the boundary explicitly:

```python
# "00" followed by the international number digits (optional separators).
# The leading digit of the number must be 1-9 (country codes never start
# with 0), and a single "0" alone is not the international prefix.
# Separators between "00" and the first digit are allowed ("00 44 ...").
# The (?<!\d) lookbehind excludes "00" preceded by a digit ("10044..." is
# not an international prefix) but deliberately does NOT exclude "+":
# "+0044..." is contradictory input handled by the e164 grammar instead.
_INTERNATIONAL_00_PATTERN = re.compile(r"(?<!\d)00[\s.\-]*(?=[1-9])\d[\d\s().\-]*")
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_grammar.py -v`
Expected: 40 + 7 = 47 passed

- [ ] **Step 4: Run type checker and linters**

Run: `uv run pyright paxman/capabilities/Phone/grammar/`
Expected: No errors

Run: `uv run ruff check paxman/capabilities/Phone/ tests/capabilities/phone/`
Expected: Zero errors

- [ ] **Step 5: Commit**

```bash
git add tests/capabilities/phone/test_grammar.py paxman/capabilities/Phone/grammar/international_00_recognition.py
git commit -m "test(phone): grammar dedup, multi-match, and boundary tests
docs(phone): document 00-prefix lookbehind boundary"
```

---

## Task 9: Create E.164 International Number Rule (PARSER)

**Files:**
- Create: `paxman/capabilities/Phone/rules/e164_ed2010.py`
- Test: `tests/capabilities/phone/test_rules.py`

- [ ] **Step 1: Write rule tests**

```python
# tests/capabilities/phone/test_rules.py
"""Tests for Phone validation rules."""

import pytest
from paxman.capabilities.Phone.contract import PhoneContract
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.e164_ed2010 import (
    Section6_1InternationalNumber,
    Section6_2CountryCode,
)
from paxman.core.domain import RuleStrategy


class TestSection6_1InternationalNumber:
    """Tests for Section6_1InternationalNumber rule."""

    def setup_method(self) -> None:
        self.rule = Section6_1InternationalNumber()
        self.contract = PhoneContract()

    def test_matches_valid_e164(self) -> None:
        """Happy path: valid E.164 number."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_uk_number(self) -> None:
        """Edge case: 2-digit country code."""
        notation = PhoneNotation(shape="e164", value="442079460958")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_three_digit_cc(self) -> None:
        """Edge case: 3-digit country code (Taiwan 886)."""
        notation = PhoneNotation(shape="e164", value="886212345678")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_longest_prefix_wins(self) -> None:
        """Edge case: 886 (Taiwan) not mis-split as 86 (China) + 6."""
        notation = PhoneNotation(shape="e164", value="886212345678")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_max_length(self) -> None:
        """Edge case: exactly 15 digits."""
        notation = PhoneNotation(shape="e164", value="123456789012345")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_too_long(self) -> None:
        """16+ digits exceeds E.164 maximum."""
        notation = PhoneNotation(shape="e164", value="1234567890123456")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_bare_country_code(self) -> None:
        """A bare country code (no NSN) is not a valid E.164 number."""
        notation = PhoneNotation(shape="e164", value="1")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_bare_two_digit_cc(self) -> None:
        """A 2-digit country code with no NSN is not valid either."""
        notation = PhoneNotation(shape="e164", value="44")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_unassigned_cc(self) -> None:
        """999 is not an assigned country code."""
        notation = PhoneNotation(shape="e164", value="999123456789")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = PhoneNotation(shape="national", value="15551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_non_digits(self) -> None:
        """Value containing non-digits."""
        notation = PhoneNotation(shape="e164", value="1555a1234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.normalize(notation, self.contract) == "+15551234567"

    def test_normalize_rfc3966_format(self) -> None:
        """Verify rfc3966 output format."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        contract = PhoneContract(output_format="rfc3966")
        assert self.rule.normalize(notation, contract) == "tel:+15551234567"

    def test_normalize_national_format(self) -> None:
        """Verify national (NSN) output format."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        contract = PhoneContract(output_format="national")
        assert self.rule.normalize(notation, contract) == "5551234567"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ITU-T"
        assert self.rule.provenance.specification_name == "E.164"
        assert self.rule.provenance.publication_year == 2010
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section 6.1-international-number"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.PARSER

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "6.1" in self.rule.citation


class TestSection6_2CountryCode:
    """Tests for Section6_2CountryCode rule."""

    def setup_method(self) -> None:
        self.rule = Section6_2CountryCode()
        self.contract = PhoneContract()

    def test_matches_assigned_cc(self) -> None:
        """Happy path: assigned country code."""
        notation = PhoneNotation(shape="e164", value="442079460958")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_single_digit_cc(self) -> None:
        """Edge case: NANP country code 1."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_three_digit_cc(self) -> None:
        """Edge case: 3-digit country code."""
        notation = PhoneNotation(shape="e164", value="886212345678")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_unassigned_cc(self) -> None:
        """Unassigned country code."""
        notation = PhoneNotation(shape="e164", value="999123456789")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = PhoneNotation(shape="national", value="15551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.normalize(notation, self.contract) == "+15551234567"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "ITU-T"
        assert self.rule.provenance.specification_name == "E.164"
        assert self.rule.provenance.publication_year == 2010

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section 6.2-country-code"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "country code" in self.rule.citation.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_rules.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement E.164 rules**

```python
# paxman/capabilities/Phone/rules/e164_ed2010.py
"""ITU-T E.164 validation rules — international number structure and country codes."""

from __future__ import annotations

import re

from paxman.capabilities.Phone.contract import PhoneContract
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.data.e164_country_codes import (
    split_country_code,
)
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ITU-T",
    specification_name="E.164",
    kind="specification",
    reference_url="https://www.itu.int/rec/T-REC-E.164",
    version="2010",
    lifecycle="active",
    publication_year=2010,
)

_MAX_E164_DIGITS = 15

_DIGITS_ONLY = re.compile(r"^\d+$")


def _canonical(value: str, contract: Contract) -> str:
    """Render the canonical form per contract.output_format.

    Args:
        value: Digit-only E.164 number (no leading +).
        contract: Contract configuration.

    Returns:
        Canonical string: "+CCNSN" (e164), "tel:+CCNSN" (rfc3966), or the
        national significant number (national).
    """
    if contract.output_format == "rfc3966":
        return f"tel:+{value}"
    if contract.output_format == "national":
        country_code = split_country_code(value)
        assert country_code is not None  # matches() ran first
        return value[len(country_code):]
    return f"+{value}"


class Section6_1InternationalNumber(Rule[PhoneNotation]):
    """ITU-T E.164 Section 6.1 — Number structure.

    Validates the E.164 number structure: 1-15 digits, first digit 1-9,
    and a country code (1-3 digits, longest prefix) assigned by ITU-T.
    """

    name = "Section 6.1-international-number"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 6.1 (number structure)"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation is a structurally valid E.164 number.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "e164", value is 1-15 digits, and the country
            code prefix is assigned.
        """
        if notation.shape != "e164":
            return False
        if not _DIGITS_ONLY.match(notation.value):
            return False
        if not 1 <= len(notation.value) <= _MAX_E164_DIGITS:
            return False
        return split_country_code(notation.value) is not None

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical E.164 form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+" + value, or the formatted variant per contract.output_format.
        """
        return _canonical(notation.value, contract)


class Section6_2CountryCode(Rule[PhoneNotation]):
    """ITU-T E.164 Annex A — Country code assignment.

    Validates that the country code prefix of an E.164 number is in the
    ITU-T assigned country code table.
    """

    name = "Section 6.2-country-code"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "Annex A (table of assigned country codes)"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation carries an assigned country code.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "e164" and the country code prefix is assigned.
        """
        if notation.shape != "e164":
            return False
        if not _DIGITS_ONLY.match(notation.value):
            return False
        return split_country_code(notation.value) is not None

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical E.164 form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+" + value, or the formatted variant per contract.output_format.
        """
        return _canonical(notation.value, contract)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_rules.py::TestSection6_1InternationalNumber tests/capabilities/phone/test_rules.py::TestSection6_2CountryCode -v`
Expected: 18 + 10 = 28 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/rules/e164_ed2010.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Phone/rules/e164_ed2010.py tests/capabilities/phone/test_rules.py
git commit -m "feat(phone): add E.164 international number and country code rules"
```

---

## Task 10: Create RFC 3966 tel-URI Rule (PARSER)

**Files:**
- Create: `paxman/capabilities/Phone/rules/rfc_3966_ed2004.py`
- Test: `tests/capabilities/phone/test_rules.py`

- [ ] **Step 1: Write rule tests**

```python
# Append to tests/capabilities/phone/test_rules.py

from paxman.capabilities.Phone.rules.rfc_3966_ed2004 import Section3TelUri


class TestSection3TelUri:
    """Tests for Section3TelUri rule."""

    def setup_method(self) -> None:
        self.rule = Section3TelUri()
        self.contract = PhoneContract()

    def test_matches_valid_global_number(self) -> None:
        """Happy path: valid tel: URI global number."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_with_extension(self) -> None:
        """Edge case: extension present."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567", extension="890")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_unassigned_cc(self) -> None:
        """Unassigned country code in URI."""
        notation = PhoneNotation(shape="rfc3966", value="999123456789")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_too_long(self) -> None:
        """16+ digits exceeds E.164 maximum."""
        notation = PhoneNotation(shape="rfc3966", value="1234567890123456")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output (default e164)."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567")
        assert self.rule.normalize(notation, self.contract) == "+15551234567"

    def test_normalize_rfc3966_format(self) -> None:
        """Verify rfc3966 output format."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567")
        contract = PhoneContract(output_format="rfc3966")
        assert self.rule.normalize(notation, contract) == "tel:+15551234567"

    def test_normalize_with_extension_in_rfc3966_format(self) -> None:
        """Verify extension is preserved in rfc3966 output."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567", extension="890")
        contract = PhoneContract(output_format="rfc3966")
        assert self.rule.normalize(notation, contract) == "tel:+15551234567;ext=890"

    def test_normalize_national_format(self) -> None:
        """Verify national (NSN) output format strips the country code."""
        notation = PhoneNotation(shape="rfc3966", value="15551234567")
        contract = PhoneContract(output_format="national")
        assert self.rule.normalize(notation, contract) == "5551234567"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "IETF"
        assert self.rule.provenance.specification_name == "RFC 3966"
        assert self.rule.provenance.publication_year == 2004
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section 3-tel-uri"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.PARSER

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "3" in self.rule.citation
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_rules.py::TestSection3TelUri -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement RFC 3966 rule**

```python
# paxman/capabilities/Phone/rules/rfc_3966_ed2004.py
"""IETF RFC 3966 validation rule — the tel URI for telephone numbers."""

from __future__ import annotations

from paxman.capabilities.Phone.contract import PhoneContract
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.data.e164_country_codes import (
    split_country_code,
)
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="IETF",
    specification_name="RFC 3966",
    kind="specification",
    reference_url="https://tools.ietf.org/html/rfc3966",
    version="2004",
    lifecycle="active",
    publication_year=2004,
)

_MAX_E164_DIGITS = 15


class Section3TelUri(Rule[PhoneNotation]):
    """RFC 3966 Section 3 — The tel URI for telephone numbers.

    Validates tel: URIs carrying global numbers (per RFC 3966 Section 3.1).
    Local numbers with phone-context are Milestone-12+ scope and rejected
    here (they carry no E.164 country code).
    """

    name = "Section 3-tel-uri"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 3 (tel URI) / Section 3.1 (global numbers)"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation is a valid tel-URI global number.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "rfc3966", value is 1-15 digits with an
            assigned country code prefix.
        """
        if notation.shape != "rfc3966":
            return False
        if not notation.value.isdigit():
            return False
        if not 1 <= len(notation.value) <= _MAX_E164_DIGITS:
            return False
        return split_country_code(notation.value) is not None

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+" + value (default), "tel:+value[;ext=extension]" (rfc3966),
            or the national significant number (national).
        """
        if contract.output_format == "rfc3966":
            base = f"tel:+{notation.value}"
            return f"{base};ext={notation.extension}" if notation.extension else base
        if contract.output_format == "national":
            country_code = split_country_code(notation.value)
            assert country_code is not None  # matches() ran first
            return notation.value[len(country_code):]
        return f"+{notation.value}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_rules.py::TestSection3TelUri -v`
Expected: 13 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/rules/rfc_3966_ed2004.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Phone/rules/rfc_3966_ed2004.py
git commit -m "feat(phone): add RFC 3966 tel-URI rule"
```

---

## Task 11: Create NANP National Rules (REGEX + LOOKUP_TABLE)

**Files:**
- Create: `paxman/capabilities/Phone/rules/nanp_ed2024.py`
- Test: `tests/capabilities/phone/test_rules.py`

- [ ] **Step 1: Write rule tests**

```python
# Append to tests/capabilities/phone/test_rules.py

from paxman.capabilities.Phone.rules.nanp_ed2024 import (
    Section1_1NANPStructure,
    Section1_2ServiceNPA,
)


class TestSection1_1NANPStructure:
    """Tests for Section1_1NANPStructure rule."""

    def setup_method(self) -> None:
        self.rule = Section1_1NANPStructure()
        self.contract = PhoneContract(default_country="US")

    def test_matches_valid_national(self) -> None:
        """Happy path: valid NANP number (NXX first digit 2-9)."""
        notation = PhoneNotation(shape="national", value="5552345678")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_with_trunk(self) -> None:
        """Edge case: leading trunk 1."""
        notation = PhoneNotation(shape="national", value="15552345678")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_toll_free(self) -> None:
        """Edge case: toll-free NPA."""
        notation = PhoneNotation(shape="national", value="8005551234")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_n11_npa(self) -> None:
        """911 is not an assignable NPA."""
        notation = PhoneNotation(shape="national", value="9115551234")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_n11_nxx(self) -> None:
        """411 is not an assignable NXX."""
        notation = PhoneNotation(shape="national", value="5554111234")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_fictional_555_range(self) -> None:
        """555-0100..555-0199 (NXX=555, line 01xx) is reserved for fiction."""
        notation = PhoneNotation(shape="national", value="5555550100")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_fictional_555_upper_bound(self) -> None:
        """Upper edge of the fictional range is still reserved."""
        notation = PhoneNotation(shape="national", value="15555550199")
        assert self.rule.matches(notation, self.contract) is False

    def test_accepts_555_outside_fictional_range(self) -> None:
        """555 NXX with a line number outside 0100-0199 is structurally valid."""
        notation = PhoneNotation(shape="national", value="5555550200")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_npa_starting_with_0(self) -> None:
        """NPA first digit must be 2-9."""
        notation = PhoneNotation(shape="national", value="05551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_nxx_starting_with_1(self) -> None:
        """NXX first digit must be 2-9 (123 is not an assignable exchange)."""
        notation = PhoneNotation(shape="national", value="5551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_too_short(self) -> None:
        """9 digits is not a full NANP number."""
        notation = PhoneNotation(shape="national", value="555123456")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_too_long(self) -> None:
        """12 digits is not a full NANP number."""
        notation = PhoneNotation(shape="national", value="155551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = PhoneNotation(shape="e164", value="15551234567")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_without_default_country(self) -> None:
        """National numbers need default_country."""
        notation = PhoneNotation(shape="national", value="5552345678")
        contract = PhoneContract()
        assert self.rule.matches(notation, contract) is False

    def test_rejects_non_us_default_country(self) -> None:
        """default_country outside NANP does not match (Milestone 1: US only)."""
        notation = PhoneNotation(shape="national", value="5552345678")
        contract = PhoneContract(default_country="GB")
        assert self.rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        notation = PhoneNotation(shape="national", value="5552345678")
        assert self.rule.normalize(notation, self.contract) == "+15552345678"

    def test_normalize_strips_trunk(self) -> None:
        """Trunk 1 is not duplicated in canonical output."""
        notation = PhoneNotation(shape="national", value="15552345678")
        assert self.rule.normalize(notation, self.contract) == "+15552345678"

    def test_normalize_national_format(self) -> None:
        """Verify national output format (NSN)."""
        notation = PhoneNotation(shape="national", value="5552345678")
        contract = PhoneContract(default_country="US", output_format="national")
        assert self.rule.normalize(notation, contract) == "5552345678"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "NANPA"
        assert self.rule.provenance.publication_year == 2024
        assert self.rule.provenance.lifecycle == "active"

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section 1.1-nanp-structure"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.REGEX

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "structure" in self.rule.citation.lower()


class TestSection1_2ServiceNPA:
    """Tests for Section1_2ServiceNPA rule."""

    def setup_method(self) -> None:
        self.rule = Section1_2ServiceNPA()
        self.contract = PhoneContract(default_country="US")

    def test_matches_toll_free(self) -> None:
        """Happy path: toll-free NPA."""
        notation = PhoneNotation(shape="national", value="8005551234")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_premium(self) -> None:
        """Edge case: premium rate 900."""
        notation = PhoneNotation(shape="national", value="9005551234")
        assert self.rule.matches(notation, self.contract) is True

    def test_matches_833(self) -> None:
        """Edge case: newer toll-free NPA."""
        notation = PhoneNotation(shape="national", value="8335551234")
        assert self.rule.matches(notation, self.contract) is True

    def test_rejects_geographic_npa(self) -> None:
        """Geographic NPA (212) is not a service code."""
        notation = PhoneNotation(shape="national", value="2125551234")
        assert self.rule.matches(notation, self.contract) is False

    def test_rejects_without_default_country(self) -> None:
        """Service NPAs still need default_country."""
        notation = PhoneNotation(shape="national", value="8005551234")
        contract = PhoneContract()
        assert self.rule.matches(notation, contract) is False

    def test_rejects_wrong_shape(self) -> None:
        """Notation with wrong shape."""
        notation = PhoneNotation(shape="e164", value="8005551234")
        assert self.rule.matches(notation, self.contract) is False

    def test_normalize_produces_canonical(self) -> None:
        """Verify exact canonical output."""
        notation = PhoneNotation(shape="national", value="8005551234")
        assert self.rule.normalize(notation, self.contract) == "+18005551234"

    def test_normalize_strips_trunk(self) -> None:
        """Trunk 1 is not duplicated in canonical output."""
        notation = PhoneNotation(shape="national", value="18005551234")
        assert self.rule.normalize(notation, self.contract) == "+18005551234"

    def test_provenance_attributes(self) -> None:
        """Verify authority, spec name, year, lifecycle."""
        assert self.rule.provenance.authority == "NANPA"
        assert self.rule.provenance.publication_year == 2024

    def test_rule_name(self) -> None:
        """Verify name follows convention."""
        assert self.rule.name == "Section 1.2-service-npa"

    def test_strategy(self) -> None:
        """Verify the rule strategy enum."""
        assert self.rule.strategy == RuleStrategy.LOOKUP_TABLE

    def test_citation(self) -> None:
        """Verify citation is set."""
        assert "service" in self.rule.citation.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_rules.py::TestSection1_1NANPStructure tests/capabilities/phone/test_rules.py::TestSection1_2ServiceNPA -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement NANP rules**

```python
# paxman/capabilities/Phone/rules/nanp_ed2024.py
"""North American Numbering Plan (NANP) validation rules.

NANP structure: NPA-NXX-XXXX where NPA and NXX each begin with 2-9.
N11 codes (211/311/411/511/611/711/811/911) are not assignable as NPA
or NXX. 555-01XX exchanges are reserved for fictional numbers.
"""

from __future__ import annotations

import re
from typing import cast

from paxman.capabilities.Phone.contract import PhoneContract
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.data.nanp_tables import (
    N11_CODES,
    SERVICE_NPAS,
)
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="NANPA",
    specification_name="North American Numbering Plan (NANP)",
    kind="registry",
    reference_url="https://www.nanpa.com/",
    version="2024",
    lifecycle="active",
    publication_year=2024,
)

# NANP countries for Milestone 1: United States only.
# Future milestones add "CA" and other NANP members.
_NANP_COUNTRIES: frozenset[str] = frozenset({"US"})

# Optional trunk 1, then NPA NXX XXXX. Group 1 = NPA, group 2 = NXX,
# group 3 = line number.
_NANP_PATTERN = re.compile(r"^(1)?([2-9]\d{2})([2-9]\d{2})(\d{4})$")


def _is_fictional_range(nxx: str, line: str) -> bool:
    """Check if the number falls in the 555-0100..555-0199 fictional range.

    Per NANPA, numbers of the form NXX=555 with a line number 0100-0199
    are reserved for fictional use (e.g., in movies and TV). They are not
    assignable real numbers.

    Args:
        nxx: The 3-digit central office code.
        line: The 4-digit line number.

    Returns:
        True if the number is in the reserved fictional range.
    """
    return nxx == "555" and line.startswith("01")


def _nanp_digits(value: str) -> str | None:
    """Return the 10 NANP digits after stripping an optional trunk 1.

    Args:
        value: Digit-only national number (10 or 11 digits).

    Returns:
        The 10-digit NANP number (trunk stripped), or None if the value
        is not 10/11 digits or fails structural constraints.
    """
    match = _NANP_PATTERN.match(value)
    if match is None:
        return None
    npa, nxx, line = match.group(2), match.group(3), match.group(4)
    if npa in N11_CODES:
        return None
    if nxx in N11_CODES:
        return None
    if _is_fictional_range(nxx, line):
        return None
    return f"{npa}{nxx}{line}"


def _canonical(digits: str, contract: Contract) -> str:
    """Render the canonical form per contract.output_format.

    Args:
        digits: 10-digit NANP number (trunk already stripped).
        contract: Contract configuration.

    Returns:
        "+1" + digits (e164/rfc3966-with-plus), "tel:+1" + digits
        (rfc3966), or the NSN (national).
    """
    if contract.output_format == "rfc3966":
        return f"tel:+1{digits}"
    if contract.output_format == "national":
        return digits
    return f"+1{digits}"


class Section1_1NANPStructure(Rule[PhoneNotation]):
    """NANP — numbering plan structure.

    Validates NANP structure: 10-digit NPA-NXX-XXXX (optionally with
    leading trunk 1), NPA/NXX first digit 2-9, N11 codes not assignable,
    and 555-01XX reserved for fictional numbers.
    """

    name = "Section 1.1-nanp-structure"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "NANP numbering plan structure (NPA NXX-XXXX)"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation is a structurally valid NANP number.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "national", default_country is a NANP country
            (Milestone 1: "US"), and the value passes the NANP structure
            regex and exclusions.
        """
        if notation.shape != "national":
            return False
        typed_contract = cast(PhoneContract, contract)
        if typed_contract.default_country not in _NANP_COUNTRIES:
            return False
        return _nanp_digits(notation.value) is not None

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical E.164 form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+1" + 10-digit NANP number, or the formatted variant per
            contract.output_format.
        """
        digits = _nanp_digits(notation.value)
        assert digits is not None  # matches() ran first
        return _canonical(digits, contract)


class Section1_2ServiceNPA(Rule[PhoneNotation]):
    """NANP — service NPAs (toll-free and premium rate).

    Validates that the NPA is a NANPA-assigned service code (toll-free
    800/833/844/855/866/877/888 or premium 900).
    """

    name = "Section 1.2-service-npa"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    citation = "NANPA service NPA assignment table"

    def matches(self, notation: PhoneNotation, contract: Contract) -> bool:
        """Check if the notation carries a service NPA.

        Args:
            notation: Phone notation to validate.
            contract: Contract configuration.

        Returns:
            True if shape == "national", default_country is a NANP country
            (Milestone 1: "US"), and the NPA is in the service table.
        """
        if notation.shape != "national":
            return False
        typed_contract = cast(PhoneContract, contract)
        if typed_contract.default_country not in _NANP_COUNTRIES:
            return False
        digits = _nanp_digits(notation.value)
        if digits is None:
            return False
        return digits[:3] in SERVICE_NPAS

    def normalize(self, notation: PhoneNotation, contract: Contract) -> str:
        """Normalize to canonical E.164 form.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            "+1" + 10-digit NANP number, or the formatted variant per
            contract.output_format.
        """
        digits = _nanp_digits(notation.value)
        assert digits is not None  # matches() ran first
        return _canonical(digits, contract)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_rules.py::TestSection1_1NANPStructure tests/capabilities/phone/test_rules.py::TestSection1_2ServiceNPA -v`
Expected: 22 + 12 = 34 passed

- [ ] **Step 5: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/rules/nanp_ed2024.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add paxman/capabilities/Phone/rules/nanp_ed2024.py
git commit -m "feat(phone): add NANP structure and service NPA rules"
```

---

## Task 12: Create Capability Class

**Files:**
- Create: `paxman/capabilities/Phone/capability.py`
- Update: `paxman/capabilities/Phone/__init__.py`
- Test: `tests/capabilities/phone/test_capability.py`

- [ ] **Step 1: Write capability wiring tests**

```python
# Append to tests/capabilities/phone/test_capability.py

from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.core.capability import Capability


class TestPhoneCapability:
    """Tests for PhoneCapability wiring."""

    def test_is_capability_subclass(self) -> None:
        """Verify inheritance from base Capability."""
        assert issubclass(PhoneCapability, Capability)

    def test_name(self) -> None:
        """Verify capability name."""
        assert PhoneCapability.name == "phone"

    def test_version(self) -> None:
        """Verify capability version."""
        assert PhoneCapability.version == "1.0.0"

    def test_get_grammars_returns_all(self) -> None:
        """Verify grammar count."""
        capability = PhoneCapability()
        grammars = capability.get_grammars()
        assert len(grammars) == 4

    def test_get_rules_returns_all(self) -> None:
        """Verify rule count."""
        capability = PhoneCapability()
        rules = capability.get_rules()
        assert len(rules) == 5

    def test_grammar_name(self) -> None:
        """Verify grammar names follow convention."""
        capability = PhoneCapability()
        names = {g.name for g in capability.get_grammars()}
        assert names == {
            "e164_recognition",
            "tel_uri_recognition",
            "international_00_recognition",
            "national_recognition",
        }

    def test_rule_name(self) -> None:
        """Verify rule names follow convention."""
        capability = PhoneCapability()
        names = {r.name for r in capability.get_rules()}
        assert names == {
            "Section 6.1-international-number",
            "Section 6.2-country-code",
            "Section 3-tel-uri",
            "Section 1.1-nanp-structure",
            "Section 1.2-service-npa",
        }

    def test_create_contract_default(self) -> None:
        """Verify create_contract factory defaults."""
        contract = PhoneCapability.create_contract()
        assert contract.capability_name == "phone"
        assert contract.default_country is None
        assert contract.output_format == "e164"

    def test_create_contract_with_params(self) -> None:
        """Verify create_contract factory passes parameters."""
        contract = PhoneCapability.create_contract(
            default_country="US",
            output_format="rfc3966",
            excluded_rules=["Section 1.2-service-npa"],
        )
        assert contract.default_country == "US"
        assert contract.output_format == "rfc3966"
        assert contract.excluded_rules == ("Section 1.2-service-npa",)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/capabilities/phone/test_capability.py::TestPhoneCapability -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement Capability class**

```python
# paxman/capabilities/Phone/capability.py
"""Phone capability — wires grammars and rules together."""

from __future__ import annotations

from collections.abc import Sequence

from paxman.capabilities.Phone.contract import PhoneContract
from paxman.capabilities.Phone.grammar.e164_recognition import E164Grammar
from paxman.capabilities.Phone.grammar.international_00_recognition import (
    International00Grammar,
)
from paxman.capabilities.Phone.grammar.national_recognition import NationalGrammar
from paxman.capabilities.Phone.grammar.tel_uri_recognition import TelUriGrammar
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.e164_ed2010 import (
    Section6_1InternationalNumber,
    Section6_2CountryCode,
)
from paxman.capabilities.Phone.rules.nanp_ed2024 import (
    Section1_1NANPStructure,
    Section1_2ServiceNPA,
)
from paxman.capabilities.Phone.rules.rfc_3966_ed2004 import Section3TelUri
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule

__all__ = ["PhoneCapability", "PhoneContract", "PhoneNotation"]


class PhoneCapability(Capability[PhoneNotation]):
    """Phone canonicalization capability.

    Canonicalizes phone numbers (E.164 international, NANP national,
    RFC 3966 tel-URI) to E.164 format with full provenance.
    """

    name = "phone"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar[PhoneNotation]]:
        """Return all grammar instances.

        Returns:
            List of 4 grammars: e164, tel-URI, international-00, national.
        """
        return [
            E164Grammar(),
            TelUriGrammar(),
            International00Grammar(),
            NationalGrammar(),
        ]

    def get_rules(self) -> list[Rule[PhoneNotation]]:
        """Return all validation rule instances.

        Returns:
            List of 5 rules: E.164 structure, E.164 country code,
            RFC 3966 tel-URI, NANP structure, NANP service NPA.
        """
        return [
            Section6_1InternationalNumber(),
            Section6_2CountryCode(),
            Section3TelUri(),
            Section1_1NANPStructure(),
            Section1_2ServiceNPA(),
        ]

    @staticmethod
    def create_contract(
        *,
        default_country: str | None = None,
        output_format: str = "e164",
        excluded_rules: Sequence[str] | None = None,
        pinned_rules: Sequence[str] | None = None,
        year: int | None = None,
    ) -> PhoneContract:
        """Factory method for creating contracts with proper defaults.

        Args:
            default_country: ISO 3166-1 alpha-2 country code used to resolve
                national numbers (e.g., "US").
            output_format: Output format for canonical values ("e164",
                "rfc3966", "national"). Default "e164".
            excluded_rules: Rule names to exclude.
            pinned_rules: Pin to specific rules (takes precedence over
                excluded_rules).
            year: Year for temporal filtering.

        Returns:
            Configured PhoneContract instance.
        """
        return PhoneContract(
            default_country=default_country,
            output_format=output_format,
            excluded_rules=tuple(excluded_rules) if excluded_rules else (),
            pinned_rules=tuple(pinned_rules) if pinned_rules is not None else None,
            year=year,
        )
```

- [ ] **Step 4: Add contract validation (code-review fold-in)**

The code-quality review of Task 3 flagged that `PhoneContract` accepts any `output_format`/`default_country` string without validation (Country validates in `__post_init__`; Email/Date do not). Now that rules will consume these fields, add validation. Append tests to `tests/capabilities/phone/test_capability.py`:

```python
# Append to tests/capabilities/phone/test_capability.py

from paxman.core.errors import ContractError


class TestPhoneContractValidation:
    """Tests for PhoneContract __post_init__ validation."""

    def test_rejects_unknown_output_format(self) -> None:
        """Unsupported output_format raises ContractError."""
        with pytest.raises(ContractError):
            PhoneContract(output_format="uppercase")

    def test_rejects_lowercase_output_format(self) -> None:
        """output_format is case-sensitive and must be one of the enum values."""
        with pytest.raises(ContractError):
            PhoneContract(output_format="E164")

    def test_accepts_all_valid_output_formats(self) -> None:
        """All documented output formats construct successfully."""
        for fmt in ("e164", "rfc3966", "national"):
            contract = PhoneContract(output_format=fmt)
            assert contract.output_format == fmt

    def test_rejects_non_alpha2_default_country(self) -> None:
        """default_country must be an uppercase ISO 3166-1 alpha-2 code."""
        with pytest.raises(ContractError):
            PhoneContract(default_country="us")

    def test_rejects_invalid_length_default_country(self) -> None:
        """default_country must be exactly 2 letters."""
        with pytest.raises(ContractError):
            PhoneContract(default_country="USA")
```

Implement `__post_init__` in `paxman/capabilities/Phone/contract.py`:

```python
# Add to paxman/capabilities/Phone/contract.py

from paxman.core.errors import ContractError

_VALID_OUTPUT_FORMATS: frozenset[str] = frozenset({"e164", "rfc3966", "national"})


def _validate_alpha2(value: str | None) -> None:
    """Validate an ISO 3166-1 alpha-2 country code.

    Args:
        value: Country code to validate (None is allowed — means "no default").

    Raises:
        ContractError: If the value is present but not an uppercase
            2-letter ISO 3166-1 alpha-2 code.
    """
    if value is not None and (len(value) != 2 or not value.isalpha() or not value.isupper()):
        raise ContractError(
            f"default_country must be an uppercase ISO 3166-1 alpha-2 code, got {value!r}"
        )
```

Then add `__post_init__` to the `PhoneContract` class body:

```python
    def __post_init__(self) -> None:
        """Validate contract configuration.

        Raises:
            ContractError: If output_format is unsupported or default_country
                is present but not an uppercase alpha-2 code.
        """
        if self.output_format not in _VALID_OUTPUT_FORMATS:
            raise ContractError(
                f"output_format must be one of {sorted(_VALID_OUTPUT_FORMATS)}, "
                f"got {self.output_format!r}"
            )
        _validate_alpha2(self.default_country)
```

Run: `uv run pytest tests/capabilities/phone/test_capability.py::TestPhoneContractValidation -v`
Expected: 5 passed

Run: `uv run pytest tests/capabilities/phone/test_capability.py -v`
Expected: 8 + 12 + 9 + 5 = 34 passed

- [ ] **Step 5: Update Phone package init**

```python
# paxman/capabilities/Phone/__init__.py
"""Phone capability for canonicalizing telephone numbers."""

from paxman.capabilities.Phone.capability import (
    PhoneCapability,
    PhoneContract,
)
from paxman.capabilities.Phone.notation import PhoneNotation

__all__ = ["PhoneCapability", "PhoneContract", "PhoneNotation"]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/capabilities/phone/test_capability.py -v`
Expected: 34 passed

- [ ] **Step 7: Run type checker**

Run: `uv run pyright paxman/capabilities/Phone/`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add paxman/capabilities/Phone/capability.py paxman/capabilities/Phone/__init__.py paxman/capabilities/Phone/contract.py tests/capabilities/phone/test_capability.py
git commit -m "feat(phone): add PhoneCapability class, package exports, and contract validation"
```

---

## Task 13: Register the Capability

**Files:**
- Update: `paxman/capabilities/__init__.py`
- Test: `tests/unit/test_capability_exports.py`

- [ ] **Step 1: Register Phone in capabilities init**

```python
# paxman/capabilities/__init__.py
"""Paxman capabilities."""

from paxman.capabilities.Country.capability import CountryCapability as Country
from paxman.capabilities.Date.capability import DateCapability as Date
from paxman.capabilities.Email.capability import EmailCapability as Email
from paxman.capabilities.Phone.capability import PhoneCapability as Phone

__all__ = ["Country", "Date", "Email", "Phone"]
```

Note: The IP capability is intentionally NOT registered here (pre-existing state — do not touch).

- [ ] **Step 2: Add export test**

```python
# Append to tests/unit/test_capability_exports.py

from paxman.capabilities import Phone


class TestPhoneCapabilityExports:
    @pytest.mark.unit
    def test_phone_capability_importable(self) -> None:
        """Phone capability is importable from paxman.capabilities."""
        assert Phone is not None

    @pytest.mark.unit
    def test_phone_capability_name(self) -> None:
        """Phone capability has correct name."""
        assert Phone.name == "phone"
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_capability_exports.py -v`
Expected: All export tests pass (existing + new)

- [ ] **Step 4: Run type checker**

Run: `uv run pyright paxman/capabilities/`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add paxman/capabilities/__init__.py tests/unit/test_capability_exports.py
git commit -m "feat(phone): register Phone capability"
```

---

## Task 14: Integration Tests

**Files:**
- Create: `tests/integration/test_phone_pipeline.py`

Reference the existing pattern in `tests/integration/test_country_pipeline.py` (uses `run_capability`, `_clean_registry` autouse fixture, inline `register_capability`).

- [ ] **Step 1: Write integration tests**

```python
# tests/integration/test_phone_pipeline.py
"""Integration tests for the Phone capability pipeline."""

import pytest
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.engine.orchestrator import run_capability


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Reset the capability registry before and after each test."""
    reset_registry()
    yield
    reset_registry()


class TestPhonePipeline:
    """Full-pipeline tests for the Phone capability.

    Note on AMBIGUOUS: after the grammar-overlap fixes (e164/national
    grammars no longer match inside tel: URIs), AMBIGUOUS is unreachable
    by design — each input maps to exactly one grammar/shape, and the two
    E.164 rules (Section 6.1 / 6.2) always agree on the canonical value.
    The tel-URI test below asserts single-candidate output, which is the
    observable consequence of that design invariant.
    """

    @pytest.mark.integration
    def test_success_e164(self) -> None:
        """International number resolves to E.164."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = run_capability("+1 555 123 4567", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+15551234567"

    @pytest.mark.integration
    def test_success_national_with_default_country(self) -> None:
        """National number resolves when default_country is set."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(default_country="US")
        result = run_capability("(555) 234-5678", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+15552345678"

    @pytest.mark.integration
    def test_success_tel_uri(self) -> None:
        """tel: URI resolves to E.164."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = run_capability("tel:+1-201-555-0123", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+12015550123"

    @pytest.mark.integration
    def test_tel_uri_single_candidate(self) -> None:
        """tel: URIs yield exactly one candidate (no grammar overlap)."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = run_capability("tel:+1-201-555-0123", contract)
        assert result.status == Resolution.SUCCESS
        assert len(result.candidates) == 1

    @pytest.mark.integration
    def test_ambiguity_unreachable_by_design(self) -> None:
        """e164 and tel-URI inputs never produce conflicting candidates."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(output_format="rfc3966")
        result = run_capability("tel:+15551234567;ext=890", contract)
        # Extension is preserved; no conflicting candidate drops it.
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "tel:+15551234567;ext=890"
        assert len(result.candidates) == 1

    @pytest.mark.integration
    def test_success_international_00(self) -> None:
        """00-prefixed international number resolves to E.164."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = run_capability("00 44 20 7946 0958", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+442079460958"

    @pytest.mark.integration
    def test_missing(self) -> None:
        """Nothing recognized."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = run_capability("hello world", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.integration
    def test_invalid_unassigned_cc(self) -> None:
        """Recognized but no rule validates (unassigned country code)."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = run_capability("+999123456789", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.integration
    def test_invalid_national_without_default_country(self) -> None:
        """National input without default_country is invalid, not missing."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = run_capability("(555) 234-5678", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.integration
    def test_invalid_nanp_structure(self) -> None:
        """N11 NPA is recognized but fails NANP validation."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(default_country="US")
        result = run_capability("(911) 555-1234", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.integration
    def test_output_format_rfc3966(self) -> None:
        """output_format=rfc3966 renders tel: URI."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(output_format="rfc3966")
        result = run_capability("+15551234567", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "tel:+15551234567"

    @pytest.mark.integration
    def test_version_stamp(self) -> None:
        """Replay hash is present and deterministic."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result1 = run_capability("+15551234567", contract)
        result2 = run_capability("+15551234567", contract)
        assert result1.version_stamp.replay_hash == result2.version_stamp.replay_hash
        assert len(result1.version_stamp.replay_hash) == 64  # SHA-256 hex
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_phone_pipeline.py -v`
Expected: 12 passed

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_phone_pipeline.py
git commit -m "test(phone): add integration pipeline tests"
```

---

## Task 15: End-to-End Tests

**Files:**
- Update: `tests/e2e/test_canonicalize.py`

- [ ] **Step 1: Write e2e tests**

```python
# Append to tests/e2e/test_canonicalize.py

import pytest
from paxman.api import canonicalize
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution

# Use the same autouse _clean_registry fixture pattern as the existing e2e file.


class TestCanonicalizePhone:
    """End-to-end tests for the Phone capability through paxman.canonicalize."""

    @pytest.mark.e2e
    def test_canonicalize_phone_success(self) -> None:
        """Full happy path through the public API."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("+44 20 7946 0958", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+442079460958"

    @pytest.mark.e2e
    def test_canonicalize_phone_national(self) -> None:
        """National number with default_country through the public API."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(default_country="US")
        result = canonicalize("(555) 234-5678", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "+15552345678"

    @pytest.mark.e2e
    def test_canonicalize_phone_missing(self) -> None:
        """No phone pattern recognized."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("no phone number here", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.e2e
    def test_canonicalize_phone_invalid(self) -> None:
        """Unassigned country code is invalid."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract()
        result = canonicalize("+999123456789", contract)
        assert result.status == Resolution.INVALID

    @pytest.mark.e2e
    def test_canonicalize_phone_with_options(self) -> None:
        """output_format option through the public API."""
        register_capability(PhoneCapability())
        contract = PhoneCapability.create_contract(output_format="rfc3966")
        result = canonicalize("+15551234567", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "tel:+15551234567"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/e2e/test_canonicalize.py -v`
Expected: All e2e tests pass (existing + 5 new Phone tests)

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_canonicalize.py
git commit -m "test(phone): add end-to-end canonicalize tests"
```

---

## Task 16: Update README

**Files:**
- Update: `README.md`

- [ ] **Step 1: Add Phone to the capabilities table**

Add a row to the capabilities table:

```markdown
| **Phone** | Phone numbers | 4 (E.164, tel-URI, 00-prefix, national) | 5 | ITU-T E.164, RFC 3966, NANP |
```

Note: The README currently lists **IP** as a registered built-in capability, but `paxman/capabilities/__init__.py` does not export IP (only Country/Date/Email). This is a pre-existing inconsistency — do NOT "fix" it in this task; it is out of scope. Only add the Phone row.

- [ ] **Step 2: Add a Phone Capability section**

Add a section following the existing capability sections (mirroring the Email/Date/Country/IP sections):

```markdown
### Phone Capability

Recognizes international (E.164, 00-prefix), tel-URI, and NANP national phone numbers.

```python
from paxman.capabilities import Phone

register_capability(Phone())

# International number
contract = Phone.create_contract()
result = paxman.canonicalize("+1 555 123 4567", contract)
# → "+15551234567"

# National number (requires default_country)
contract = Phone.create_contract(default_country="US")
result = paxman.canonicalize("(555) 234-5678", contract)
# → "+15552345678"

# Output as RFC 3966 tel-URI
contract = Phone.create_contract(output_format="rfc3966")
result = paxman.canonicalize("+15551234567", contract)
# → "tel:+15551234567"
```
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(phone): document Phone capability in README"
```

---

## Task 17: Final Quality Gates

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests pass (existing + Phone tests)

- [ ] **Step 2: Run coverage check**

Run: `uv run pytest --cov=paxman --cov-report=term-missing --cov-report=html --tb=short -q`
Expected: Coverage ≥ 95% for `paxman/capabilities/*` (CI enforces per-package 95% gate)

- [ ] **Step 3: Run ruff lint and format check**

Run: `uv run ruff check paxman/ tests/`
Expected: No errors

Run: `uv run ruff format --check paxman/ tests/`
Expected: No errors

- [ ] **Step 4: Run pyright**

Run: `uv run pyright`
Expected: No errors

- [ ] **Step 5: Run import-linter**

Run: `uv run importlinter`
Expected: No errors (Phone imports only from `paxman.core` and its own package)

- [ ] **Step 6: Verify commit history**

Run: `git log --oneline -15`
Expected: All `feat(phone)`/`test(phone)`/`docs(phone)` commits present, no push performed

---

## Final State

After all tasks are complete:

- `paxman.canonicalize("+1 555 123 4567", Phone.create_contract())` → `SUCCESS` `+15551234567`
- `paxman.canonicalize("(555) 234-5678", Phone.create_contract(default_country="US"))` → `SUCCESS` `+15552345678`
- `paxman.canonicalize("+999123456789", Phone.create_contract())` → `INVALID`
- `paxman.canonicalize("hello", Phone.create_contract())` → `MISSING`
- All 3 `RuleStrategy` types demonstrated across 5 rules with full provenance
- Milestones M2-M12 documented as bounded future work, NOT implemented in this branch
