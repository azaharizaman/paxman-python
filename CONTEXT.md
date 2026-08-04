# Paxman Domain Glossary

## Core Concepts

### Paxman
A **canonicalization authority resolver** — a library that takes ambiguous human input and returns what authoritative specifications say that input means, with full provenance. Paxman is both a **syntactic recognizer** (finds values in text) and a **semantic interpreter** (validates against authoritative specifications).

**Invariants:**
- **Deterministic:** Never guess, never infer, never suggest
- **Provenance-first:** Always cite authority-defined specifications, registries, policies
- **Replay-safe:** Same input + same contract = byte-identical output

### Capability
A domain module (e.g., Email) that:
- Defines a **Notation** (intermediate representation)
- Registers **Grammars** (recognition rules)
- Registers **Validation Rules** (semantic rules with provenance)
- Lives in `capabilities/<CapabilityName>/`

### Contract
User-facing configuration object that:
- **Toggles grammars ON/OFF** (e.g., `include_obfuscated=True`)
- **Pins rules** to run only specific validation rules (e.g., `pinned_rules=["Section 3.4.1-addr-spec"]`)
- **Excludes rules** to skip specific validation rules (e.g., `excluded_rules=["Section 6.3-localhost"]`)
- **Pins year** to filter validation rules by `publication_year`
- **Passes parameters** to validation rules (e.g., `output_format=ISO`)
  - Note: `two_digit_base_year` is a Date-specific parameter, not part of the base Contract
- Does NOT define Notation (that's internal to Capability)

When `pinned_rules` is set, `excluded_rules` is ignored — only the pinned rules run.

### Notation
Capability-defined intermediate representation that Grammars must produce.
- **Email:** `EmailNotation` (frozen dataclass with `local_part` and `domain_part` fields) → `["local_part", "domain_part"]`
- **Date:** `DateNotation` (frozen dataclass with `N1`, `N2`, `N3` fields) → `["N1", "N2", "N3"]` (position-sensitive: grammar determines meaning)

**Note:** Capabilities define Notation using frozen dataclasses for type safety and immutability. The `as_list()` method bridges the typed notation to the generic `list[str]` interface.

### Notation Type Example
```python
from dataclasses import dataclass


# Email Notation using frozen dataclass
@dataclass(frozen=True)
class EmailNotation:
    local_part: str
    domain_part: str

    def as_list(self) -> list[str]:
        """Convert to list[str] for generic Rule interface."""
        return [self.local_part, self.domain_part]
```

---

## Pipeline Components

### Grammar (Recognition Rule)
Syntactic extraction rules that:
- Scan raw text for patterns
- Produce **Notation** (capability-defined shape)
- Live in `capabilities/<CapabilityName>/grammar/`
- Are **filtered by the orchestrator** based on the contract's `active_grammars`
- Do NOT validate — only recognize

### Validation Rule
Semantic rules that:
- Accept **Notation** (not raw input)
- Are backed by **Provenance** (authority specification)
- Use **Contract parameters** (e.g., `output_format`)
- Produce **Candidate** with canonical value
- Live in `capabilities/<CapabilityName>/rules/`
- Are filtered by **pinned_rules** (if set, only those rules run) or **excluded_rules**
- Are filtered by **year** (publication_year ≤ contract.year)

### Rule Structure
Each rule file pins to **ONE publication** and contains **ONE or more rules** (sections):

```python
# capabilities/Email/rules/rfc_5322_ed2008.py

from paxman.core.domain import Provenance, Rule, RuleStrategy

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


class Section341AddrSpec(Rule[EmailNotation]):
    """RFC 5322 Section 3.4.1 - addr-spec"""

    name = "Section 3.4.1-addr-spec"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "Section 3.4.1 (addr-spec)"  # Human-readable citation

    def matches(self, notation: EmailNotation, contract: Contract) -> bool:
        """Check if notation matches addr-spec pattern."""
        local_pattern = r"^[a-zA-Z0-9._%+-]+$"
        domain_pattern = r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(
            re.match(local_pattern, notation.local_part)
            and re.match(domain_pattern, notation.domain_part)
        )

    def normalize(self, notation: EmailNotation, contract: Contract) -> str:
        """Normalize to canonical email format."""
        return f"{notation.local_part.lower()}@{notation.domain_part.lower()}"
```

### Notation Purpose
Notation exists for **placement-sensitive rules**:
- **Dates:** `["01", "02", "2026"]` — position matters (DD/MM/YYYY vs MM/DD/YYYY)
- **Email:** `["azahari", "gmail.com"]` — position matters (local vs domain)
- **Countries:** `["Russia", "Federation"]` — multi-word names

The resolver **consumes notation** and outputs a canonical_value (not notation).

### Rule Strategies
| Strategy | Use Case | Example |
|----------|----------|---------|
| `REGEX` | Pattern matching | Email addr-spec validation |
| `LOOKUP_TABLE` | Table lookup | HTTP status codes, country codes |
| `PARSER` | Value parsing | Date parsing, UUID validation |

### LookupTable Example
```python
# capabilities/HttpStatusCode/rules/rfc_9110_ed2022.py

class Section15StatusCodes(Rule[StatusCodeNotation]):
    """RFC 9110 Section 15 - Status Codes"""
    
    name = "Section 15-status-codes"
    strategy = RuleStrategy.LOOKUP_TABLE
    provenance = PUBLICATION
    
    TABLE = {
        103: "Early Hints",
        200: "OK",
        404: "Not Found",
        ...
    }
    
    def matches(self, notation: StatusCodeNotation, contract: Contract) -> bool:
        """Check if status code exists in table."""
        return int(notation.code) in self.TABLE
    
    def normalize(self, notation: StatusCodeNotation, contract: Contract) -> str:
        """Return canonical status code."""
        code = int(notation.code)
        return str(code)
```

### Parser Example
```python
# capabilities/Date/rules/iso_8601_ed2019.py


class Section431CalendarDate(Rule[DateNotation]):
    """ISO 8601 Section 4.3.1 - Calendar date"""

    name = "Section 4.3.1-calendar-date"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION

    def matches(self, notation: DateNotation, contract: Contract) -> bool:
        """Try to parse as ISO 8601 date.

        ISO grammar maps: N1=year, N2=month, N3=day
        """
        try:
            year, month, day = int(notation.N1), int(notation.N2), int(notation.N3)
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    def normalize(self, notation: DateNotation, contract: Contract) -> str:
        """Normalize to ISO 8601 format."""
        year, month, day = int(notation.N1), int(notation.N2), int(notation.N3)
        return f"{year:04d}-{month:02d}-{day:02d}"
```

### Grammar File Structure
```python
# paxman/capabilities/Email/grammar/standard_recognition.py

import re

from paxman.core.domain import Grammar
from paxman.capabilities.Email.notation import EmailNotation


class StandardEmailGrammar(Grammar[EmailNotation]):
    """Standard email recognition: user@domain.tld"""

    name = "standard_recognition"

    def recognize(self, text: str) -> list[EmailNotation]:
        """Extract email patterns from text."""
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        matches = re.findall(pattern, text)
        return [
            EmailNotation(
                local_part=match.split("@")[0], domain_part=match.split("@")[1]
            )
            for match in matches
        ]
```

### Date Ambiguity Example
```python
# Input: "01/02/2026"
# Grammar outputs notation based on its own mapping:
#   ISO grammar:    N1="2026", N2="01", N3="02"  (N1=year, N2=month, N3=day)
#   US grammar:     N1="01",   N2="02", N3="2026" (N1=month, N2=day, N3=year)
#   European grammar: N1="01", N2="02", N3="2026" (N1=day, N2=month, N3=year)

# Rule 1: ISO 8601 — receives ISO notation
# N1=year=2026, N2=month=01, N3=day=02 → VALID → "2026-01-02"

# Rule 2: US federal — receives US notation
# N1=month=01, N2=day=02, N3=year=2026 → VALID → "2026-01-02"

# Rule 3: EN 50160 (European) — receives European notation
# N1=day=01, N2=month=02, N3=year=2026 → VALID → "2026-02-01"

# Result: 2 distinct canonical values → AMBIGUOUS
```

### Date Capability Details

The Date capability has **3 grammars** and **3 validation rules**:

#### Grammars (Recognition)

| Grammar | Delimiter | N1 (first) | N2 (second) | N3 (third) | Notes |
|---------|-----------|------------|-------------|------------|-------|
| ISO | `-` | year | month | day | 4-digit year only |
| US | `/` | month | day | year | Supports 2-digit years |
| European | `/` | day | month | year | Supports 2-digit years |

**Note:** European and US grammars both use `/` as delimiter. The ambiguity arises from different position mappings, not delimiters.

#### Validation Rules

| Rule | Standard | Canonical Output |
|------|----------|------------------|
| ISO 8601 | ISO 8601:2019 | `YYYY-MM-DD` |
| US federal | US government standard | `YYYY-MM-DD` |
| EN 50160 | European EN 50160 | `YYYY-MM-DD` |

All rules normalize to ISO 8601 format (`YYYY-MM-DD`) regardless of input grammar.

### Contract Rule Exclusion
```python
from paxman.capabilities import Email

# User knows input is localhost, excludes standard validation
contract = Email.create_contract(excluded_rules=["Section 3.4.1-addr-spec"])
paxman.canonicalize("user@localhost", contract)

# Or with year pinning
contract = Email.create_contract(excluded_rules=["Section 6.3-localhost"], year=2008)
paxman.canonicalize("user@example.com", contract)
# Result: "user@example.com" → SUCCESS
```

### Contract Rule Pinning
```python
from paxman.capabilities import Email

# Pin to specific rules — only these run, excluded_rules is ignored
contract = Email.create_contract(pinned_rules=["Section 3.4.1-addr-spec"])
paxman.canonicalize("user@example.com", contract)

# Pin + year filter — both apply
contract = Email.create_contract(
    pinned_rules=["Section 3.4.1-addr-spec", "Section 6.3-localhost"], year=2010
)
# Only rules matching both pinning and year filter are active
```

### RecognizedRep
Data class carrying recognition output:
```python
@dataclass(frozen=True)
class RecognizedRep(Generic[NotationT]):
    notation: NotationT  # capability-defined shape
    contract: Contract  # contract configuration
    grammar: GrammarRule  # which grammar produced this
```

### Candidate
Data class carrying validation output:
```python
@dataclass(frozen=True)
class Candidate:
    value: str  # canonical value
    recognition_rule: str  # which grammar produced notation
    validation_rule: str  # which rule validated it
    provenance: tuple[Provenance, ...]  # authorities backing this value
```

### Provenance
Authority citation for a validated value:
```python
@dataclass(frozen=True)
class Provenance:
    authority: str  # "IETF", "ISO", "W3C"
    specification_name: str  # "RFC 5322 §3.4.1"
    kind: str  # "specification" | "registry" | "policy"
    reference_url: str  # "https://..."
    version: str | None  # "2008" or None if not versioned
    lifecycle: str  # "active" | "deprecated" | "superseded"
    publication_year: int  # year this provenance came into effect
```

### GrammarRule
Reference to a grammar that produced a RecognizedRep:
```python
@dataclass(frozen=True)
class GrammarRule:
    """Reference to a grammar that produced a RecognizedRep."""

    capability_name: str  # "email"
    grammar_name: str  # "standard_recognition"
```

**Naming Convention:**
- `capability_name`: Lowercase capability name (e.g., "email", "date", "country")
- `grammar_name`: Lowercase, underscore-separated grammar name (e.g., "standard_recognition", "obfuscated_recognition")
- Grammar names are unique within a capability but may not be globally unique
- The `capability_name` field ensures global uniqueness

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

---

## Execution Result

### Resolution (Status Enum)
```python
from enum import Enum


class Resolution(Enum):
    """Status of the canonicalization execution."""

    MISSING = "missing"  # No RecognizedReps produced (fails-fast at recognition)
    INVALID = "invalid"  # Recognized, but no provenance validates
    SUCCESS = "success"  # Single canonical value resolved
    AMBIGUOUS = "ambiguous"  # Multiple conflicting canonical values
```

### ExecutionResult
Final output from `paxman.canonicalize()`. **Engine responsibility** — not capability.

```python
@dataclass(frozen=True)
class ExecutionResult:
    status: Resolution  # Enum status (computed by engine)
    canonicalized_value: str | None  # Extracted from candidates (if SUCCESS)
    candidates: tuple[Candidate, ...]  # Produced by capability validation rules
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
    paxman_version: str  # library version
    replay_hash: str  # SHA-256 of canonical bytes
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
| Contract missing required fields | `ContractError` | Contract with invalid field types |
| Unknown capability name | `CapabilityError` | `canonicalize("input", contract_with_unknown_name)` |
| Grammar regex malformed | `RecognitionError` | Invalid regex pattern in grammar file |
| Validation rule crashes | `ValidationError` | Unexpected None in provenance lookup |
| Registry frozen, register attempted | `CapabilityError` | `register_capability()` after first call |

**Note:** INVALID and AMBIGUOUS are output states (Resolution enum), not exceptions.

---

## Usage Examples

### Basic Usage
```python
import paxman
from paxman.capabilities.Email.capability import EmailCapability
from paxman.core.domain import Resolution
from paxman.core.discovery import register_capability

# Register capability (required before first use)
register_capability(EmailCapability())

# Canonicalize an email
result = paxman.canonicalize(
    "azahari at gmail dot com", EmailCapability.create_contract(include_obfuscated=True)
)

if result.status == Resolution.SUCCESS:
    print(f"Canonical: {result.canonicalized_value}")
    print(f"Provenance: {result.candidates[0].provenance}")
else:
    print(f"Status: {result.status}")
```

### Date with Year Pinning
```python
from paxman.capabilities.Date.capability import DateCapability

# Pin to 2019, include ISO 8601 rule (publication_year=2019)
contract = DateCapability.create_contract(year=2019)
result = paxman.canonicalize("2026-01-02", contract)

# Result: "2026-01-02" (ISO 8601 grammar + rule)
```

### Custom Capability Registration
```python
from paxman import register_capability
from mypackage import MyCapability, MyContract

# Register before first canonicalize() call
register_capability(MyCapability())

# Now use it
result = paxman.canonicalize("input", MyContract())
```

### Inspecting Provenance
```python
result = paxman.canonicalize("test@example.com", Email.create_contract())

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
- **Built-in capabilities:** Registered in `paxman/capabilities/__init__.py`
- **User-registered capabilities:** Added via `register_capability()` before first call
- **Registry freezes** at the start of each `run_capability()` call (engine responsibility)
- **Duplicate registration** raises `CapabilityError` — each capability name must be unique.
- **Attempting to register after freeze raises `CapabilityError`**

**Note:** The registry freeze happens at the start of each pipeline run, not just once. In testing, use `reset_registry()` between tests to allow re-registration. `freeze_registry()` is available for explicit control.

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
from collections.abc import Sequence


class Contract(Protocol):
    """Base protocol for all capability contracts."""

    @property
    def capability_name(self) -> str:
        """Name of the capability this contract configures."""
        ...

    @property
    def active_grammars(self) -> Sequence[str]:
        """List of grammar names to activate."""
        ...

    @property
    def excluded_rules(self) -> Sequence[str]:
        """List of rule names to exclude."""
        ...

    @property
    def pinned_rules(self) -> Sequence[str] | None:
        """Pin to specific rules. If set, ONLY these rules run.

        Mutually exclusive with excluded_rules. When pinned_rules is set,
        excluded_rules is ignored.
        """
        ...

    @property
    def year(self) -> int | None:
        """Year for temporal filtering (publication_year ≤ year)."""
        ...

    @property
    def output_format(self) -> str | None:
        """Output format for canonical values (e.g., 'ISO', 'US')."""
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
│   ├── capability.py              # Capability abstract class
│   ├── contract.py                # Contract protocol
│   ├── discovery.py               # Capability registry
│   ├── domain.py                  # Provenance, Candidate, Rule, Grammar, etc.
│   └── errors.py                  # Exception hierarchy
├── capabilities/
│   ├── __init__.py
│   ├── Email/
│   │   ├── __init__.py
│   │   ├── capability.py          # EmailCapability
│   │   ├── contract.py            # EmailContract
│   │   ├── notation.py            # EmailNotation dataclass
│   │   ├── grammar/
│   │   │   ├── __init__.py
│   │   │   ├── standard_recognition.py
│   │   │   ├── obfuscated_recognition.py
│   │   │   └── localhost_recognition.py
│   │   └── rules/
│   │       ├── __init__.py
│   │       ├── rfc_5322_ed2008.py
│   │       └── rfc_6761_ed2012.py
│   └── Date/
│       ├── __init__.py
│       ├── capability.py          # DateCapability
│       ├── contract.py            # DateContract
│       ├── notation.py            # DateNotation dataclass
│       ├── grammar/
│       │   ├── __init__.py
│       │   ├── iso8601_recognition.py
│       │   ├── us_recognition.py
│       │   └── european_recognition.py
│       └── rules/
│           ├── __init__.py
│           ├── iso_8601_ed2019.py
│           ├── us_federal_rules_ed2023.py
│           └── en_50160_ed2010.py
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
│   ├── test_version_stamp.py     # VersionStamp + replay_hash
│   ├── test_capability_exports.py # Capability exports validation
│   └── test_errors.py            # Exception hierarchy
├── capabilities/
│   ├── email/
│   │   ├── test_grammar.py       # Recognition rules
│   │   ├── test_rules.py         # Validation rules
│   │   └── test_capability.py    # Capability registration
│   └── date/
│       ├── test_grammar.py       # Recognition rules
│       ├── test_rules.py         # Validation rules
│       └── test_capability.py    # Capability registration
├── property/
│   ├── __init__.py
│   ├── test_domain_properties.py
│   ├── test_grammar_properties.py
│   └── test_rule_properties.py
├── integration/
│   ├── test_pipeline.py          # Full pipeline flow
│   ├── test_ambiguity.py         # Ambiguity detection
│   └── test_temporal.py          # Year-based filtering
└── e2e/
    └── test_canonicalize.py      # End-to-end user scenarios
```

### Test Markers
```python
import pytest


@pytest.mark.unit
def test_provenance_immutable(): ...


@pytest.mark.capability
def test_email_grammar_recognizes_standard(): ...


@pytest.mark.integration
def test_ambiguity_detection(): ...


@pytest.mark.e2e
def test_canonicalize_email_success(): ...
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
    "paxman.api",            # Public API (canonicalize)
    "paxman.engine",         # Pipeline orchestrator
    "paxman.capabilities",   # Capability implementations
    "paxman.core",           # Domain objects (Provenance, Candidate, etc.)
]
```

### Pytest Configuration
```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: unit tests",
    "capability: capability-specific tests",
    "integration: integration tests",
    "e2e: end-to-end tests",
    "property: property-based tests (Hypothesis)",
]
testpaths = ["tests"]
```

### Pyright Configuration
```json
{
  "pythonVersion": "3.11",
  "typeCheckingMode": "strict",
  "reportMissingImports": true,
  "reportMissingTypeStubs": false,
  "include": ["paxman"],
  "exclude": ["tests", "docs"]
}
```

### Hypothesis Configuration
```python
# tests/conftest.py
from hypothesis import settings, HealthCheck

# Configure hypothesis for faster tests
settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
settings.load_profile("ci")
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
  "include": ["paxman"],
  "exclude": ["tests", "docs"]
}
```
