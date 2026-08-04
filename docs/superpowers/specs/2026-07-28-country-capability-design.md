# Country Capability Design

**Date:** 2026-07-28
**Status:** Draft
**Author:** Sisyphus (AI Agent)

---

## Overview

The Country capability canonicalizes country representations to ISO 3166-1 alpha-2 codes with full provenance. It recognizes four mutually exclusive input shapes (alpha2, alpha3, numeric, name) and validates against multiple authoritative sources (ISO 3166-1, CLDR, Paxman policy).

**Canonical output:** Alpha-2 code by default (e.g., "US"), configurable via `output_format`.

---

## Design Decisions

### Decision 1: Shape-Aware Notation

**Choice:** Notation includes a `shape` discriminator field.

**Rationale:**
- Rules can efficiently filter by shape (e.g., alpha3 rule skips non-alpha3 inputs)
- Each rule file maps to one authority + one shape
- Enables shape-specific error messages and validation logic
- Follows existing patterns (Date capability's position-sensitive notation)

**Alternatives considered:**
- Single grammar with internal dispatch (rejected: violates "one grammar per pattern")
- No shape in notation (rejected: loses type information, inefficient validation)

### Decision 2: Four Mutually Exclusive Grammars

**Choice:** Separate grammar file per shape (alpha2, alpha3, numeric, name).

**Rationale:**
- Follows "one grammar per pattern variant" principle
- Each grammar is simple and focused
- Grammars can be toggled individually if needed
- Matches Email/Date capability patterns

**Shape detection logic:**
- `alpha2_recognition`: Exactly 2 ASCII letters (e.g., "US", "GB")
- `alpha3_recognition`: Exactly 3 ASCII letters (e.g., "USA", "GBR")
- `numeric_recognition`: 1-3 digits (e.g., "840", "4")
- `name_recognition`: Anything else (non-empty, not matching above)

### Decision 3: Opt-in for Localized and Historical Data

**Choice:** Localized and historical lookups controlled by contract flags.

**Rationale:**
- Localized data (CLDR) adds Unicode tables — opt-in reduces memory footprint
- Historical names (e.g., "BURMA" → "MM") may not be needed by all users
- Follows Email capability's `include_obfuscated` pattern
- Users who need these features explicitly enable them

**Contract flags:**
- `include_localized: bool = False` — enables CLDR multilingual names
- `include_historical: bool = False` — enables deprecated country names

### Decision 4: Configurable Output Format

**Choice:** Default alpha-2, configurable via `output_format`.

**Rationale:**
- Alpha-2 is the most common canonical form (249 codes)
- Alpha-3, numeric, and full name are useful for specific use cases
- Follows Date capability's `output_format` pattern
- Rules check `contract.output_format` during normalization

**Output format values:**
- `"alpha2"` → "US" (default)
- `"alpha3"` → "USA"
- `"numeric"` → "840"
- `"name"` → "United States of America"

---

## Notation

```python
@dataclass(frozen=True, slots=True)
class CountryNotation:
    """Intermediate representation for country recognition."""

    shape: str  # "alpha2" | "alpha3" | "numeric" | "name"
    value: str  # Raw input value (e.g., "US", "USA", "840", "United States")

    def as_list(self) -> list[str]:
        """Bridge to generic list[str] interface."""
        return [self.shape, self.value]
```

**Fields:**
- `shape`: Discriminator set by grammar — rules use it to select lookup tables
- `value`: Raw input, normalized only by grammar (e.g., uppercased for alpha2/alpha3)

**Ordering:** `[shape, value]` — shape first for consistent hashing and comparison.

---

## Grammars

### Grammar 1: `alpha2_recognition`

**File:** `paxman/capabilities/Country/grammar/alpha2_recognition.py`

**Pattern:** Exactly 2 ASCII letters, case-insensitive match, output uppercased.

**Examples:**
- "US" → `CountryNotation(shape="alpha2", value="US")`
- "gb" → `CountryNotation(shape="alpha2", value="GB")`
- "USA" → no match (3 letters, not 2)
- "12" → no match (digits, not letters)

**Regex:** `r'^[A-Za-z]{2}$'` applied to trimmed input.

### Grammar 2: `alpha3_recognition`

**File:** `paxman/capabilities/Country/grammar/alpha3_recognition.py`

**Pattern:** Exactly 3 ASCII letters, case-insensitive match, output uppercased.

**Examples:**
- "USA" → `CountryNotation(shape="alpha3", value="USA")`
- "gbr" → `CountryNotation(shape="alpha3", value="GBR")`
- "US" → no match (2 letters, not 3)
- "MAL" → `CountryNotation(shape="alpha3", value="MAL")` (valid shape, may not be assigned code)

**Regex:** `r'^[A-Za-z]{3}$'` applied to trimmed input.

### Grammar 3: `numeric_recognition`

**File:** `paxman/capabilities/Country/grammar/numeric_recognition.py`

**Pattern:** 1-3 digits, preserved as-is (no zero-padding).

**Examples:**
- "840" → `CountryNotation(shape="numeric", value="840")`
- "4" → `CountryNotation(shape="numeric", value="4")`
- "004" → `CountryNotation(shape="numeric", value="004")`
- "US" → no match (letters, not digits)
- "1234" → no match (4 digits, not 1-3)

**Regex:** `r'^\d{1,3}$'` applied to trimmed input.

### Grammar 4: `name_recognition`

**File:** `paxman/capabilities/Country/grammar/name_recognition.py`

**Pattern:** Any non-empty string. Matches independently of other grammars.

**Examples:**
- "United States" → `CountryNotation(shape="name", value="United States")`
- "马来西亚" → `CountryNotation(shape="name", value="马来西亚")`
- "Burma" → `CountryNotation(shape="name", value="Burma")`
- "US" → `CountryNotation(shape="name", value="US")` (also matched by alpha2)
- "" → no match (empty)

**Design note:** This grammar matches any non-empty input, including values that might also match alpha2/alpha3/numeric grammars. This is intentional — multiple grammars matching the same input is fine because:
- Each grammar produces a separate notation with the appropriate shape
- Rules validate based on shape (e.g., `SectionAlpha2Codes` only accepts shape="alpha2")
- Multiple candidates with the same canonical value produce SUCCESS, not AMBIGUOUS

**Logic:** Preserves original case. Returns `[]` for empty input.

---

## Validation Rules

### Rule 1: `iso_3166_alpha2_ed2024.py`

**Provenance:**
```python
PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 3166-1:2024",
    kind="registry",
    reference_url="https://www.iso.org/guest/en/ISO3166-1/RegistrationTable/Active%20country%20list.html",
    version="2024",
    lifecycle="active",
    publication_year=2024,
)
```

**Rule:** `SectionAlpha2Codes`
- **Strategy:** `LOOKUP_TABLE`
- **Matches:** `notation.shape == "alpha2"` AND `notation.value.upper() in _ALPHA2_CODES`
- **Normalizes:** Returns alpha-2 code (or configured output format)

**Lookup table:** `_ALPHA2_CODES` — frozenset of 249 assigned alpha-2 codes.

### Rule 2: `iso_3166_alpha3_ed2024.py`

**Provenance:** Same as Rule 1 (ISO 3166-1:2024).

**Rule:** `SectionAlpha3Codes`
- **Strategy:** `LOOKUP_TABLE`
- **Matches:** `notation.shape == "alpha3"` AND `notation.value.upper() in _ALPHA3_TO_ALPHA2`
- **Normalizes:** Maps alpha-3 → alpha-2, then to configured output format

**Lookup table:** `_ALPHA3_TO_ALPHA2` — Mapping[str, str] (e.g., "USA" → "US").

### Rule 3: `iso_3166_numeric_ed2024.py`

**Provenance:** Same as Rule 1 (ISO 3166-1:2024).

**Rule:** `SectionNumericCodes`
- **Strategy:** `LOOKUP_TABLE`
- **Matches:** `notation.shape == "numeric"` AND normalized numeric in `_NUMERIC_TO_ALPHA2`
- **Normalizes:** Maps numeric → alpha-2, then to configured output format

**Lookup table:** `_NUMERIC_TO_ALPHA2` — Mapping[str, str] (e.g., "840" → "US").

**Normalization:** Strips leading zeros before lookup (e.g., "0840" → "840").

### Rule 4: `iso_3166_name_ed2024.py`

**Provenance:** Same as Rule 1 (ISO 3166-1:2024).

**Rule:** `SectionNameCodes`
- **Strategy:** `LOOKUP_TABLE`
- **Matches:** `notation.shape == "name"` AND (name in `_NAME_TO_ALPHA2` OR name in `_SYNONYM_TO_ALPHA2` OR name in `contract.extra_synonyms`)
- **Normalizes:** Maps name → alpha-2, then to configured output format

**Lookup tables:**
- `_NAME_TO_ALPHA2` — Mapping[str, str] — uppercased official English short names (e.g., "UNITED STATES OF AMERICA" → "US")
- `_SYNONYM_TO_ALPHA2` — Mapping[str, str] — common aliases (e.g., "UK" → "GB", "USA" → "US")

**Extra synonyms:** The rule also checks `contract.extra_synonyms` (caller-supplied aliases). This allows users to add custom mappings at contract construction time. The lookup order is:
1. `_NAME_TO_ALPHA2` (official names)
2. `_SYNONYM_TO_ALPHA2` (common aliases)
3. `contract.extra_synonyms` (caller-supplied)

**Normalization:** Case-insensitive lookup (uppercases input before matching).

### Rule 5: `cldr_localized_ed2025.py` (opt-in)

**Provenance:**
```python
PUBLICATION = Provenance(
    authority="Unicode",
    specification_name="CLDR v45",
    kind="registry",
    reference_url="https://cldr.unicode.org/",
    version="45",
    lifecycle="active",
    publication_year=2025,
)
```

**Rule:** `SectionLocalizedNames`
- **Strategy:** `LOOKUP_TABLE`
- **Matches:** `notation.shape == "name"` AND `contract.include_localized == True` AND name in `_LOCALIZED_TO_ALPHA2`
- **Normalizes:** Maps localized name → alpha-2, then to configured output format

**Lookup table:** `_LOCALIZED_TO_ALPHA2` — Mapping[str, str] — curated multilingual names (e.g., "马来西亚" → "MY", "Estados Unidos" → "US").

**Languages (v1.0):**
- Chinese (zh): ~249 entries
- Spanish (es): ~249 entries
- French (fr): ~249 entries

### Rule 6: `paxman_historical_ed2025.py` (opt-in)

**Provenance:**
```python
PUBLICATION = Provenance(
    authority="Paxman",
    specification_name="Historical Country Names",
    kind="policy",
    reference_url="https://github.com/paxman-dev/paxman/blob/main/docs/historical-countries.md",
    version=None,
    lifecycle="active",
    publication_year=2025,
)
```

**Rule:** `SectionHistoricalNames`
- **Strategy:** `LOOKUP_TABLE`
- **Matches:** `notation.shape == "name"` AND `contract.include_historical == True` AND name in `_HISTORICAL_TO_ALPHA2`
- **Normalizes:** Maps historical name → current alpha-2, then to configured output format

**Lookup table:** `_HISTORICAL_TO_ALPHA2` — Mapping[str, str] — deprecated names (e.g., "BURMA" → "MM", "CEYLON" → "LK").

---

## Contract

```python
@dataclass(frozen=True, slots=True)
class CountryContract:
    """User-facing configuration for Country capability."""
    
    capability_name: str = field(default="country", init=False)
    
    # Standard contract fields
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None
    output_format: str | None = None  # "alpha2" | "alpha3" | "numeric" | "name"
    
    # Capability-specific fields
    include_localized: bool = False
    include_historical: bool = False
    extra_synonyms: dict[str, str] = field(default_factory=dict)
    
    @property
    def active_grammars(self) -> list[str]:
        """All grammars active by default."""
        return [
            "alpha2_recognition",
            "alpha3_recognition",
            "numeric_recognition",
            "name_recognition",
        ]
    
    def as_dict(self) -> dict[str, object]:
        """Serialize for replay hash computation."""
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

**Fields:**
- `capability_name`: Fixed to "country" (not user-settable)
- `excluded_rules`: Tuple of rule names to exclude (standard)
- `pinned_rules`: Pin to specific rules (standard, takes precedence over excluded_rules)
- `year`: Temporal filtering (standard)
- `output_format`: Canonical output format ("alpha2", "alpha3", "numeric", "name")
- `include_localized`: Enable CLDR multilingual names
- `include_historical`: Enable deprecated country names
- `extra_synonyms`: Caller-supplied aliases (validated at construction)

**Validation:**
- `extra_synonyms` validated at construction: keys must be strings, values must be valid alpha-2 codes
- `output_format` validated: must be one of None, "alpha2", "alpha3", "numeric", "name"

---

## Capability Wiring

```python
class CountryCapability(Capability[CountryNotation]):
    """Country canonicalization capability."""
    
    name = "country"
    version = "1.0.0"
    
    def get_grammars(self) -> list[Grammar[CountryNotation]]:
        """Return all grammar instances."""
        return [
            Alpha2Grammar(),
            Alpha3Grammar(),
            NumericGrammar(),
            NameGrammar(),
        ]
    
    def get_rules(self) -> list[Rule[CountryNotation]]:
        """Return all validation rule instances."""
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
        """Factory method for creating contracts with proper defaults."""
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
```

**Test structure:**
```
tests/capabilities/country/
├── __init__.py
├── test_grammar.py
├── test_rules.py
└── test_capability.py
```

---

## Data Tables

### ISO 3166-1 Data (v1.0)

**Source:** ISO 3166-1:2024 (https://www.iso.org/standard/396855.html)

| Table | Shape | Count | Description |
|-------|-------|-------|-------------|
| `_ALPHA2_CODES` | alpha2 | 249 | Frozenset of assigned alpha-2 codes |
| `_ALPHA3_TO_ALPHA2` | alpha3 | 249 | Mapping: alpha-3 → alpha-2 |
| `_NUMERIC_TO_ALPHA2` | numeric | 249 | Mapping: zero-padded M49 → alpha-2 |
| `_NAME_TO_ALPHA2` | name | 249 | Mapping: uppercased English short name → alpha-2 |
| `_SYNONYM_TO_ALPHA2` | name | ~50 | Mapping: common aliases → alpha-2 |

### CLDR Data (v1.0, opt-in)

**Source:** CLDR v45 (https://cldr.unicode.org/)

| Table | Shape | Count | Description |
|-------|-------|-------|-------------|
| `_LOCALIZED_TO_ALPHA2` | name | ~747 | Mapping: multilingual name → alpha-2 (zh, es, fr) |

### Historical Data (v1.0, opt-in)

**Source:** Paxman policy

| Table | Shape | Count | Description |
|-------|-------|-------|-------------|
| `_HISTORICAL_TO_ALPHA2` | name | ~30 | Mapping: deprecated name → current alpha-2 |

---

## Examples

### Example 1: Alpha-2 Input

```python
import paxman
from paxman.capabilities import Country

paxman.register_capability(Country())

contract = Country.create_contract()
result = paxman.canonicalize("US", contract)

# result.status == Resolution.SUCCESS
# result.canonicalized_value == "US"
# result.candidates[0].provenance[0].authority == "ISO"
```

### Example 2: Alpha-3 Input

```python
contract = Country.create_contract()
result = paxman.canonicalize("USA", contract)

# result.status == Resolution.SUCCESS
# result.canonicalized_value == "US"
# result.candidates[0].validation_rule == "Section-alpha3-codes"
```

### Example 3: Numeric Input

```python
contract = Country.create_contract()
result = paxman.canonicalize("840", contract)

# result.status == Resolution.SUCCESS
# result.canonicalized_value == "US"
# result.candidates[0].validation_rule == "Section-numeric-codes"
```

### Example 4: Full Name Input

```python
contract = Country.create_contract()
result = paxman.canonicalize("United States of America", contract)

# result.status == Resolution.SUCCESS
# result.canonicalized_value == "US"
# result.candidates[0].validation_rule == "Section-name-codes"
```

### Example 5: Localized Input (opt-in)

```python
contract = Country.create_contract(include_localized=True)
result = paxman.canonicalize("马来西亚", contract)

# result.status == Resolution.SUCCESS
# result.canonicalized_value == "MY"
# result.candidates[0].validation_rule == "Section-localized-names"
```

### Example 6: Historical Name (opt-in)

```python
contract = Country.create_contract(include_historical=True)
result = paxman.canonicalize("Burma", contract)

# result.status == Resolution.SUCCESS
# result.canonicalized_value == "MM"
# result.candidates[0].validation_rule == "Section-historical-names"
```

### Example 7: Custom Synonyms

```python
contract = Country.create_contract(extra_synonyms={"my_alias": "MY"})
result = paxman.canonicalize("my_alias", contract)

# result.status == Resolution.SUCCESS
# result.canonicalized_value == "MY"
```

### Example 8: Configurable Output Format

```python
contract = Country.create_contract(output_format="alpha3")
result = paxman.canonicalize("US", contract)

# result.status == Resolution.SUCCESS
# result.canonicalized_value == "USA"
```

### Example 9: Ambiguity Detection

```python
# Input "UK" matches both synonym table and name table
# Both resolve to "GB" — no ambiguity
contract = Country.create_contract()
result = paxman.canonicalize("UK", contract)

# result.status == Resolution.SUCCESS
# result.canonicalized_value == "GB"
# Multiple candidates, but all agree on "GB"
```

---

## Testing Strategy

### Grammar Tests

For each grammar:
1. `test_recognizes_valid_input` — happy path
2. `test_recognizes_variant_input` — edge cases (whitespace, case)
3. `test_recognizes_multiple` — input contains multiple matches
4. `test_ignores_incompatible_format` — grammar does not match other shapes
5. `test_returns_empty_for_empty_input` — empty string returns empty list

### Rule Tests

For each rule:
1. `test_matches_valid_input` — happy path
2. `test_matches_variant_valid` — edge cases
3. `test_rejects_invalid_input` — notation that should not match
4. `test_normalize_produces_canonical` — verify exact canonical output
5. `test_provenance_attributes` — verify authority, spec name, year, lifecycle
6. `test_rule_name` — verify name follows convention
7. `test_strategy` — verify the rule strategy enum

### Capability Tests

1. `test_notation_creates_with_fields` — verify field access
2. `test_notation_is_frozen` — verify immutability
3. `test_notation_as_list_returns_correct` — verify list conversion
4. `test_notation_as_list_preserves_order` — verify field order
5. `test_notation_equality` — verify value equality
6. `test_notation_hashable` — verify it can be used in sets or as dict keys
7. `test_is_capability_subclass` — verify isinstance check
8. `test_name` — verify name matches expected value
9. `test_version` — verify version matches expected value
10. `test_get_grammars_returns_all` — verify grammar count (4)
11. `test_get_rules_returns_all` — verify rule count (6)
12. `test_grammar_name` — verify grammar names follow convention
13. `test_rule_name` — verify rule names follow convention

### Integration Tests

1. `test_success` — recognized and validated, single canonical value
2. `test_missing` — nothing recognized
3. `test_invalid` — recognized but not validated
4. `test_ambiguity` — multiple conflicting canonical values
5. `test_version_stamp` — verify replay hash is present and deterministic

### End-to-End Tests

1. `test_canonicalize_success` — full happy path
2. `test_canonicalize_missing` — no match
3. `test_canonicalize_with_options` — contract configuration

---

## Quality Gates

All standard quality gates apply:

- [ ] `pyright --strict` passes with zero errors
- [ ] `ruff check` passes with zero errors
- [ ] `ruff format --check` passes with zero errors
- [ ] `import-linter` passes (no capability-to-capability imports)
- [ ] All tests pass with `uv run pytest`
- [ ] No `# type: ignore` or `# noqa` comments

---

## Future Work

### v1.1 (Community Contributions)
- Add more languages to CLDR localized data (German, Japanese, Korean, etc.)
- Expand historical names database
- Add support for country subdivisions (ISO 3166-2)

### v2.0 (Advanced Features)
- Fuzzy matching for misspelled country names
- Confidence scores for ambiguous inputs
- Integration with postal address parsing

---

## References

- ISO 3166-1:2024 — https://www.iso.org/standard/396855.html
- CLDR v45 — https://cldr.unicode.org/
- Paxman Architecture — `ARCHITECTURE.md`
- How to Add a New Capability — `HOW_TO_ADD_NEW_CAPABILITY.md`
