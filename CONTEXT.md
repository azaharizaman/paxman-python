# Paxman Domain Glossary

## Core Concepts

### Paxman
A **canonicalization authority resolver** — a library that takes ambiguous human input and returns what authoritative specifications say that input means, with full provenance. Paxman is both a **syntactic recognizer** (finds values in text) and a **semantic interpreter** (validates against authoritative specifications).

**Invariants:**
- **Deterministic:** Never guess, never infer, never suggest
- **Provenance-first:** Always cite authority-defined specifications, registries, policies
- **Replay-safe:** Same input + same contract = byte-identical output

### Capability
A domain module (e.g., Email, Date, Country) that:
- Defines a **Notation** (intermediate representation)
- Registers **Grammars** (recognition rules)
- Registers **Validation Rules** (semantic rules with provenance)
- Lives in `capabilities/<CapabilityName>/`

### Contract
User-facing configuration object that:
- **Toggles grammars ON/OFF** (e.g., `include_obfuscated=True`)
- **Pins year** to filter validation rules by `publication_year`
- **Passes parameters** to validation rules (e.g., `output_format=ISO`)
- Does NOT define Notation (that's internal to Capability)

### Notation
Capability-defined intermediate representation that Grammars must produce.
- **Email:** `EmailNotation = list[str]` → `["local_part", "domain_part"]`
- **Date:** `DateNotation = list[str]` → `["day", "month", "year"]`
- **Country:** `CountryNotation = list[str]` → `["country_name"]`

---

## Pipeline Components

### Grammar (Recognition Rule)
Syntactic extraction rules that:
- Scan raw text for patterns
- Produce **Notation** (capability-defined shape)
- Live in `capabilities/<CapabilityName>/grammar/`
- Are **contract-aware** (know which grammars are active)
- Do NOT validate — only recognize

### Validation Rule
Semantic rules that:
- Accept **Notation** (not raw input)
- Are backed by **Provenance** (authority specification)
- Use **Contract parameters** (e.g., `two_digit_base_year`)
- Produce **Candidate** with canonical value
- Live in `capabilities/<CapabilityName>/rules/`
- Are filtered by **year** (publication_year ≤ contract.year)

### Rule Structure
Each rule file pins to **ONE publication** and contains **ONE or more rules** (sections):

```python
# capabilities/Email/rules/rfc_5322_ed2008.py

from paxman.domain import Provenance, Rule, RuleStrategy, RuleSense

# Publication-level provenance (one per file)
PUBLICATION = Provenance(
    authority="IETF",
    specification_name="RFC 5322",
    kind="specification",
    reference_url="https://tools.ietf.org/html/rfc5322",
    version="2008",
    lifecycle="active",
    publication_year=2008,
)

class Section341AddrSpec(Rule):
    """RFC 5322 Section 3.4.1 - addr-spec"""
    
    name = "Section 3.4.1-addr-spec"
    strategy = RuleStrategy.REGEX
    sense = RuleSense.POSITIVE  # Match = valid
    provenance = PUBLICATION
    citation = "Section 3.4.1 (addr-spec)"  # Human-readable citation
    
    def matches(self, notation: list[str]) -> bool:
        """Check if notation matches addr-spec pattern."""
        local_part, domain_part = notation
        local_pattern = r"^[a-zA-Z0-9._%+-]+$"
        domain_pattern = r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(local_pattern, local_part) and 
                    re.match(domain_pattern, domain_part))
    
    def normalize(self, notation: list[str]) -> str:
        """Normalize to canonical email format."""
        local_part, domain_part = notation
        return f"{local_part.lower()}@{domain_part.lower()}"
```

### Notation Purpose
Notation exists for **placement-sensitive rules**:
- **Dates:** `["01", "02", "2026"]` — position matters (DD/MM/YYYY vs MM/DD/YYYY)
- **Email:** `["azahari", "@gmail.com"]` — position matters (local vs domain)
- **Countries:** `["Russia", "Federation"]` — multi-word names

The resolver **consumes notation** and outputs a canonical_value (not notation).

### Rule Strategies
| Strategy | Use Case | Example |
|----------|----------|---------|
| `REGEX` | Pattern matching | Email addr-spec validation |
| `LOOKUP_TABLE` | Table lookup | HTTP status codes, country codes |
| `PARSER` | Value parsing | Date parsing, UUID validation |

### Rule Sense
| Sense | Meaning | Example |
|-------|---------|---------|
| `POSITIVE` | Match = valid | RFC 5322 Section 3.4.1 (addr-spec) |
| `NEGATIVE` | Match = invalid (exclusion) | RFC 5322 Section 4.4 (obsolete addressing) |

### LookupTable Example
```python
# capabilities/HttpStatusCode/rules/rfc_9110_ed2022.py

class Section15StatusCodes(Rule):
    """RFC 9110 Section 15 - Status Codes"""
    
    name = "Section 15-status-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    sense = RuleSense.POSITIVE
    provenance = PUBLICATION
    
    TABLE = {
        103: "Early Hints",
        200: "OK",
        404: "Not Found",
        ...
    }
    
    def matches(self, notation: list[str]) -> bool:
        """Check if status code exists in table."""
        return int(notation[0]) in self.TABLE
    
    def normalize(self, notation: list[str]) -> str:
        """Return canonical status code."""
        code = int(notation[0])
        return str(code)
```

### Parser Example
```python
# capabilities/Date/rules/iso_8601_ed2019.py

class SectionISO8601Date(Rule):
    """ISO 8601 Section 4.3.1 - Calendar date"""
    
    name = "Section 4.3.1-calendar-date"
    strategy = RuleStrategy.PARSER
    sense = RuleSense.POSITIVE
    provenance = PUBLICATION
    
    def matches(self, notation: list[str]) -> bool:
        """Try to parse as ISO 8601 date."""
        try:
            day, month, year = notation
            datetime(int(year), int(month), int(day))
            return True
        except ValueError:
            return False
    
    def normalize(self, notation: list[str]) -> str:
        """Normalize to ISO 8601 format."""
        day, month, year = notation
        return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"
```

### Exclusion Rule Example
```python
# paxman/capabilities/Email/rules/rfc_5322_ed2008.py

class Section44ObsoleteAddressing(Rule):
    """RFC 5322 Section 4.4 - Obsolete Addressing"""
    
    name = "Section 4.4-obsolete-addressing"
    strategy = RuleStrategy.REGEX
    sense = RuleSense.NEGATIVE  # Match = INVALID (exclusion)
    provenance = PUBLICATION
    citation = "Section 4.4 (obsolete addressing)"
    
    def matches(self, notation: list[str]) -> bool:
        """Check if notation matches obsolete pattern."""
        local_part, domain_part = notation
        obsolete_pattern = r"^[^@]*@[^@]*@[^@]*$"
        return bool(re.match(obsolete_pattern, f"{local_part}@{domain_part}"))
    
    def normalize(self, notation: list[str]) -> str:
        """Return None (excluded)."""
        return None
```

### Grammar File Structure
```python
# paxman/capabilities/Email/grammar/standard_recognition.py

from paxman.domain import Grammar, Notation

class StandardEmailGrammar(Grammar):
    """Standard email recognition: user@domain.tld"""
    
    name = "standard_recognition"
    
    def recognize(self, text: str) -> list[Notation]:
        """Extract email patterns from text."""
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        matches = re.findall(pattern, text)
        return [EmailNotation(match.split("@")) for match in matches]
```

### Date Ambiguity Example
```python
# Input: "01/02/2026"
# Notation: ["01", "02", "2026"]

# Rule 1: ISO 8601 (YYYY-MM-DD)
# year=01, month=02, day=2026 → INVALID (year too small)

# Rule 2: US Date (MM/DD/YYYY)
# month=01, day=02, year=2026 → VALID → "2026-01-02"

# Rule 3: Other interpretations → INVALID

# Result: 1 canonical value → SUCCESS
```

### Contract Rule Exclusion
```python
# User knows input is US format, excludes ISO interpretation
paxman.canonicalize("01/02/2026", Date(exclude_rule=ISO))

# Or with year pinning
paxman.canonicalize("01/02/26", Date(exclude_rule=ISO, two_digits_year_base=2000))
# Result: "2026-01-02" → SUCCESS
```

### RecognizedRep
Data class carrying recognition output:
```python
@dataclass(frozen=True)
class RecognizedRep:
    notation: Notation           # capability-defined shape
    contract: Contract           # contract configuration
    grammar: GrammarRule         # which grammar produced this
```

### Candidate
Data class carrying validation output:
```python
@dataclass(frozen=True)
class Candidate:
    value: str                   # canonical value
    recognition_rule: str        # which grammar produced notation
    validation_rule: str         # which rule validated it
    provenance: list[Provenance] # authorities backing this value
```

### Provenance
Authority citation for a validated value:
```python
@dataclass(frozen=True)
class Provenance:
    authority: str               # "IETF", "ISO", "W3C"
    specification_name: str      # "RFC 5322 §3.4.1"
    kind: str                    # "specification" | "registry" | "policy"
    reference_url: str           # "https://..."
    version: str | None          # "2008" or None if not versioned
    lifecycle: str               # "active" | "deprecated" | "superseded"
    publication_year: int        # year this provenance came into effect
```

### GrammarRule
Reference to a grammar that produced a RecognizedRep:
```python
@dataclass(frozen=True)
class GrammarRule:
    """Reference to a grammar that produced a RecognizedRep."""
    capability_name: str  # "email"
    grammar_name: str     # "standard_recognition"
```

### RuleStrategy
Validation strategy for a rule:
```python
from enum import Enum

class RuleStrategy(Enum):
    """Validation strategy for a rule."""
    REGEX = "regex"
    LOOKUP_TABLE = "lookup_table"
    PARSER = "parser"
```

### RuleSense
Whether a match means valid or invalid:
```python
class RuleSense(Enum):
    """Whether a match means valid or invalid."""
    POSITIVE = "positive"   # Match = valid
    NEGATIVE = "negative"   # Match = invalid (exclusion)
```

---

## Execution Result

### Resolution (Status Enum)
```python
from enum import Enum

class Resolution(Enum):
    """Status of the canonicalization execution."""
    MISSING = "missing"       # No RecognizedReps produced (fails-fast at recognition)
    INVALID = "invalid"       # Recognized, but no provenance validates
    SUCCESS = "success"       # Single canonical value resolved
    AMBIGUOUS = "ambiguous"   # Multiple conflicting canonical values
```

### ExecutionResult
Final output from `paxman.canonicalize()`. **Engine responsibility** — not capability.

```python
@dataclass(frozen=True)
class ExecutionResult:
    status: Resolution        # Enum status (computed by engine)
    canonicalized_value: str | None  # Extracted from candidates (if SUCCESS)
    candidates: list[Candidate]  # Produced by capability validation rules
    contract: Contract  # Passed through from user
    version_stamp: VersionStamp  # Computed by engine (includes replay_hash)
```

**Responsibility Split:**
| Component | Responsibility |
|-----------|----------------|
| **Capability** | Produces candidates via validation rules |
| **Engine** | Shapes ExecutionResult, computes status, replay_hash |

### Resolution Semantics
| Resolution | Phase | Meaning | Candidates | canonicalized_value |
|------------|-------|---------|------------|---------------------|
| `MISSING` | Recognition | No RecognizedReps produced (fails-fast) | `[]` | `None` |
| `INVALID` | Validation | Recognized, but no provenance validates | `[]` | `None` |
| `SUCCESS` | Validation | Single canonical value resolved | `≥1` (all same value) | `str` |
| `AMBIGUOUS` | Validation | Multiple conflicting canonical values | `≥2` (different values) | `None` |

### VersionStamp
Replay integrity metadata:
```python
@dataclass(frozen=True)
class VersionStamp:
    paxman_version: str          # library version
    contract_version: int        # contract schema version
    replay_hash: str             # SHA-256 of canonical bytes
```

---

## Error Handling

### Exception Hierarchy
```python
class PaxmanError(Exception):
    """Base exception for all Paxman errors."""
    pass

class ContractError(PaxmanError):
    """Raised when contract is malformed or invalid."""
    pass

class CapabilityError(PaxmanError):
    """Raised when no capability can claim the process."""
    pass

class RecognitionError(PaxmanError):
    """Raised when grammar fails to parse input (malformed regex, etc.)."""
    def __init__(self, rule: str, message: str, original_error: Exception):
        self.rule = rule
        self.original_error = original_error
        super().__init__(f"[{rule}] {message}")

class ValidationError(PaxmanError):
    """Raised when validation rule encounters unexpected error."""
    def __init__(self, rule: str, message: str, original_error: Exception):
        self.rule = rule
        self.original_error = original_error
        super().__init__(f"[{rule}] {message}")
```

### Error Scenarios
| Scenario | Exception | Example |
|----------|-----------|---------|
| Contract missing required fields | `ContractError` | `Email()` with no parameters when required |
| Unknown capability name | `CapabilityError` | `paxman.canonicalize("input", "unknown_cap")` |
| Grammar regex malformed | `RecognitionError` | Invalid regex pattern in grammar file |
| Validation rule crashes | `ValidationError` | Unexpected None in provenance lookup |
| Registry frozen, register attempted | `CapabilityError` | `register_capability()` after first call |

**Note:** INVALID and AMBIGUOUS are output states (Resolution enum), not exceptions.

---

## Usage Examples

### Basic Usage
```python
import paxman
from paxman.capabilities import Email
from paxman.domain import Resolution

# Canonicalize an email
result = paxman.canonicalize("azahari at gmail dot com", Email(include_obfuscated=True))

if result.status == Resolution.SUCCESS:
    print(f"Canonical: {result.canonicalized_value}")
    print(f"Provenance: {result.candidates[0].provenance}")
else:
    print(f"Status: {result.status}")
```

### Date with Year Pinning
```python
from paxman.capabilities import Date

# Pin to US format, exclude ISO interpretation
result = paxman.canonicalize("01/02/26", Date(exclude_rule="iso_8601", two_digits_year_base=2000))

# Result: "2026-01-02" → SUCCESS
```

### Custom Capability Registration
```python
from paxman import register_capability
from mypackage import MyCapability

# Register before first canonicalize() call
register_capability(MyCapability())

# Now use it
result = paxman.canonicalize("input", MyCapability())
```

### Inspecting Provenance
```python
result = paxman.canonicalize("test@example.com", Email())

for candidate in result.candidates:
    print(f"Value: {candidate.value}")
    print(f"Grammar: {candidate.recognition_rule}")
    print(f"Rule: {candidate.validation_rule}")
    for prov in candidate.provenance:
        print(f"  Authority: {prov.authority}")
        print(f"  Specification: {prov.specification_name}")
        print(f"  URL: {prov.reference_url}")
```

---

## Capability Registration

### Capability Registry
- **Built-in capabilities:** Hard-coded in `discovery.py` via `builtin_capabilities()`
- **User-registered capabilities:** Added via `register_capability()` before first call
- **Registry freezes** after first `canonicalize()` call
- **User can override built-ins** by registering same-named capability before first call
- **Attempting to register after freeze raises `CapabilityError`**

### Capability Versioning
- Each capability has its own version in `capability.py`
- Capability version is independent of engine version
- Example:
  ```python
  # capabilities/Email/capability.py
  class EmailCapability:
      name = "email"
      version = "1.0.0"
      ...
  ```

### Engine Versioning
- Engine version lives in `pyproject.toml` or `paxman/__init__.py`
- Referenced in `VersionStamp.paxman_version`
- Independent of capability versions

### Contract Protocol
```python
# paxman/core/contract.py

from typing import Protocol, Any

class Contract(Protocol):
    """Base protocol for all capability contracts."""
    
    @property
    def capability_name(self) -> str:
        """Name of the capability this contract configures."""
        ...
    
    @property
    def active_grammars(self) -> list[str]:
        """List of grammar names to activate."""
        ...
    
    @property
    def excluded_rules(self) -> list[str]:
        """List of rule names to exclude."""
        ...
    
    def as_dict(self) -> dict[str, Any]:
        """Serialize contract for replay_hash."""
        ...
```

---

## Directory Structure

```
paxman/
├── __init__.py                    # Public API exports
├── core/
│   ├── __init__.py
│   ├── domain.py                  # Provenance, Candidate, Rule, Grammar, etc.
│   ├── contract.py                # Contract protocol
│   └── discovery.py               # Capability registry
├── capabilities/
│   ├── __init__.py
│   ├── Email/
│   │   ├── __init__.py
│   │   ├── capability.py          # Notation, default grammars, default rules
│   │   ├── grammar/
│   │   │   ├── __init__.py
│   │   │   ├── standard_recognition.py
│   │   │   ├── obfuscated_recognition.py
│   │   │   └── localhost_recognition.py
│   │   └── rules/
│   │       ├── __init__.py
│   │       ├── rfc_5322_ed2008.py
│   │       └── rfc_6761_ed2012.py
│   ├── Date/
│   │   ├── __init__.py
│   │   ├── capability.py
│   │   ├── grammar/
│   │   │   ├── __init__.py
│   │   │   ├── iso_date_recognition.py
│   │   │   └── locale_date_recognition.py
│   │   └── rules/
│   │       ├── __init__.py
│   │       ├── iso_8601_ed2019.py
│   │       └── us_date_ed2024.py
│   └── Country/
│       ├── __init__.py
│       ├── capability.py
│       ├── grammar/
│       │   ├── __init__.py
│       │   └── standard_country_recognition.py
│       └── rules/
│           ├── __init__.py
│           └── iso_3166_ed2020.py
├── engine/
│   ├── __init__.py
│   └── orchestrator.py            # Pipeline orchestrator
└── api/
    ├── __init__.py
    └── canonicalize.py            # Public canonicalize() function
```

### Package Responsibilities

| Package | Responsibility |
|---------|----------------|
| `paxman.core` | Domain objects, protocols, discovery |
| `paxman.capabilities` | Capability implementations |
| `paxman.engine` | Pipeline orchestration |
| `paxman.api` | Public API entry points |

---

## Testing Strategy

### Test Structure
```
tests/
├── unit/
│   ├── test_provenance.py        # Provenance dataclass
│   ├── test_candidate.py         # Candidate dataclass
│   ├── test_recognized_rep.py    # RecognizedRep dataclass
│   ├── test_resolution.py        # Resolution enum
│   ├── test_contract.py          # Contract validation
│   └── test_version_stamp.py     # VersionStamp + replay_hash
├── capabilities/
│   ├── email/
│   │   ├── test_grammar.py       # Recognition rules
│   │   ├── test_rules.py         # Validation rules
│   │   └── test_capability.py    # Capability registration
│   ├── date/
│   │   ├── test_grammar.py
│   │   ├── test_rules.py
│   │   └── test_capability.py
│   └── country/
│       ├── test_grammar.py
│       ├── test_rules.py
│       └── test_capability.py
├── integration/
│   ├── test_pipeline.py          # Full pipeline flow
│   ├── test_ambiguity.py         # Ambiguity detection
│   ├── test_temporal.py          # Year-based filtering
│   └── test_replay.py            # Replay hash verification
└── e2e/
    └── test_canonicalize.py      # End-to-end user scenarios
```

### Test Markers
```python
import pytest

@pytest.mark.unit
def test_provenance_immutable():
    ...

@pytest.mark.capability
def test_email_grammar_recognizes_standard():
    ...

@pytest.mark.integration
def test_ambiguity_detection():
    ...

@pytest.mark.e2e
def test_canonicalize_email_success():
    ...
```

---

## Architectural Enforcement

### Toolchain
| Tool | Purpose | Configuration |
|------|---------|---------------|
| **ruff** | Linting + formatting | `pyproject.toml` |
| **pyright** | Static type checking (strict) | `pyrightconfig.json` |
| **import-linter** | Enforce import boundaries | `pyproject.toml` |
| **pytest** | Testing | `pyproject.toml` |
| **hypothesis** | Property-based testing | `conftest.py` |

### Import Rules (import-linter)
```toml
# pyproject.toml
[tool.importlinter]
root_package = "paxman"

[[tool.importlinter.contracts]]
name = "Capability independence"
type = "layers"
layers = [
    "paxman.core",           # Domain objects (Provenance, Candidate, etc.)
    "paxman.capabilities",   # Capability implementations
    "paxman.engine",         # Pipeline orchestrator
    "paxman.api",            # Public API (canonicalize)
]
```

### Import Boundaries
| Rule | Description |
|------|-------------|
| `paxman.core` cannot import from `paxman.capabilities` | Core domain is independent |
| `paxman.capabilities` can import from `paxman.core` | Capabilities use domain objects |
| `paxman.engine` can import from `paxman.core` and `paxman.capabilities` | Engine orchestrates |
| `paxman.api` can import from everything | Public API is the entry point |

### Ruff Configuration
```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
]
```

### Pyright Configuration
```json
{
  "pythonVersion": "3.11",
  "typeCheckingMode": "strict",
  "reportMissingImports": true,
  "reportMissingTypeStubs": false,
  "include": ["src/paxman"],
  "exclude": ["tests", "docs"]
}
```
