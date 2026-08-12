# Email Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Paxman core domain infrastructure and Email capability with standard/obfuscated/localhost grammars and RFC 5322/RFC 6761 validation rules, delivering a working `paxman.canonicalize()` pipeline for email inputs.

**Architecture:** Domain-Centric Pipeline with clean separation between Recognition (syntactic grammar extraction) and Validation (semantic provenance-backed rules). Each capability defines its own Notation type, registers grammars and rules, and the engine orchestrates the full pipeline from input to `ExecutionResult` with replay-safe determinism.

**Tech Stack:** Python 3.11, uv, pytest, ruff, pyright (strict), import-linter, hypothesis

**Design Spec:** ADR-0001 (docs/adr/0001-clean-architecture-pipeline.md) + CONTEXT.md

---

## File Structure

```
paxman/
├── __init__.py                        # Public API exports (canonicalize, register_capability)
├── core/
│   ├── __init__.py                    # Core exports
│   ├── domain.py                      # Provenance, Candidate, GrammarRule, RuleStrategy, Resolution, VersionStamp, Rule, Grammar, Notation
│   ├── contract.py                    # Contract protocol
│   ├── capability.py                  # Capability base class
│   ├── errors.py                      # Exception hierarchy
│   └── discovery.py                   # Capability registry (freeze after first call)
├── capabilities/
│   ├── __init__.py                    # Capability exports
│   └── Email/
│       ├── __init__.py                # EmailCapability export
│       ├── capability.py              # EmailCapability, EmailNotation, default grammars/rules
│       ├── grammar/
│       │   ├── __init__.py
│       │   ├── standard_recognition.py    # Standard email: user@domain.tld
│       │   ├── obfuscated_recognition.py  # Obfuscated: "at"/"dot" variations
│       │   └── localhost_recognition.py   # Localhost: user@localhost
│       └── rules/
│           ├── __init__.py
│           ├── rfc_5322_ed2008.py      # RFC 5322 addr-spec validation
│           └── rfc_6761_ed2012.py      # RFC 6761 localhost validation
├── engine/
│   ├── __init__.py
│   └── orchestrator.py                # Pipeline orchestrator (run_capability)
└── api/
    ├── __init__.py
    └── canonicalize.py                # Public canonicalize() function
tests/
├── conftest.py                        # Hypothesis settings, shared fixtures
├── unit/
│   ├── test_domain.py                 # Provenance, Candidate, GrammarRule, Resolution, VersionStamp, RuleStrategy
│   └── test_errors.py                 # Exception hierarchy
├── capabilities/
│   └── email/
│       ├── test_grammar.py            # Standard, obfuscated, localhost grammar recognition
│       └── test_rules.py              # RFC 5322, RFC 6761 rule validation
├── integration/
│   ├── test_pipeline.py               # Full pipeline: input → ExecutionResult
│   ├── test_ambiguity.py              # Multiple canonical values → AMBIGUOUS
│   └── test_temporal.py               # Year-based rule filtering
└── e2e/
    └── test_canonicalize.py           # User-facing scenarios
```

---

## Task 1: Project Initialization

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `tests/conftest.py`
- Create: `paxman/__init__.py` (stub)
- Create: `paxman/core/__init__.py` (stub)
- Create: `paxman/capabilities/__init__.py` (stub)
- Create: `paxman/engine/__init__.py` (stub)
- Create: `paxman/api/__init__.py` (stub)

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "paxman"
version = "0.1.0"
description = "Canonicalization authority resolver"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "hypothesis>=6.100",
    "ruff>=0.5",
    "pyright>=1.1",
    "import-linter>=2.0",
]

[tool.pytest.ini_options]
markers = [
    "unit: unit tests",
    "capability: capability-specific tests",
    "integration: integration tests",
    "e2e: end-to-end tests",
]
testpaths = ["tests"]

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

[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "strict"
reportMissingImports = true
reportMissingTypeStubs = false
include = ["paxman"]
exclude = ["tests", "docs"]

[tool.importlinter]
root_package = "paxman"

[[tool.importlinter.contracts]]
name = "Capability independence"
type = "layers"
layers = [
    "paxman.core",
    "paxman.capabilities",
    "paxman.engine",
    "paxman.api",
]
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.venv/
venv/
ENV/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.pyright/
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover
*.py,cover
.hypothesis/
```

- [ ] **Step 3: Create test conftest.py**

```python
from hypothesis import HealthCheck, settings

settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
settings.load_profile("ci")
```

- [ ] **Step 4: Create package stubs**

```python
# paxman/__init__.py
```

```python
# paxman/core/__init__.py
```

```python
# paxman/capabilities/__init__.py
```

```python
# paxman/engine/__init__.py
```

```python
# paxman/api/__init__.py
```

- [ ] **Step 5: Install dependencies and verify**

Run: `uv sync`
Expected: Dependencies installed, `.venv/` created

- [ ] **Step 6: Verify toolchain works**

Run: `uv run ruff check paxman/`
Expected: No errors (empty package)

Run: `uv run pyright paxman/`
Expected: No errors

Run: `uv run pytest tests/ -v`
Expected: No tests collected (expected)

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore tests/conftest.py paxman/
git commit -m "feat: project initialization with uv, ruff, pyright, import-linter"
```

---

## Task 2: Core Domain Objects — Enums and Value Objects

**Files:**
- Create: `paxman/core/domain.py`
- Test: `tests/unit/test_domain.py`

- [ ] **Step 1: Write failing tests for RuleStrategy**

```python
# tests/unit/test_domain.py

import pytest
from paxman.core.domain import RuleStrategy


class TestRuleStrategy:
    @pytest.mark.unit
    def test_has_regex(self):
        assert RuleStrategy.REGEX.value == "regex"

    @pytest.mark.unit
    def test_has_lookup_table(self):
        assert RuleStrategy.LOOKUP_TABLE.value == "lookup_table"

    @pytest.mark.unit
    def test_has_parser(self):
        assert RuleStrategy.PARSER.value == "parser"

    @pytest.mark.unit
    def test_all_strategies(self):
        assert len(RuleStrategy) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_domain.py::TestRuleStrategy -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'paxman.core.domain'`

- [ ] **Step 3: Write failing tests for Resolution**

```python
# Append to tests/unit/test_domain.py

from paxman.core.domain import Resolution


class TestResolution:
    @pytest.mark.unit
    def test_has_missing(self):
        assert Resolution.MISSING.value == "missing"

    @pytest.mark.unit
    def test_has_invalid(self):
        assert Resolution.INVALID.value == "invalid"

    @pytest.mark.unit
    def test_has_success(self):
        assert Resolution.SUCCESS.value == "success"

    @pytest.mark.unit
    def test_has_ambiguous(self):
        assert Resolution.AMBIGUOUS.value == "ambiguous"

    @pytest.mark.unit
    def test_all_statuses(self):
        assert len(Resolution) == 4
```

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_domain.py::TestResolution -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 5: Write failing tests for Provenance**

```python
# Append to tests/unit/test_domain.py

from paxman.core.domain import Provenance


class TestProvenance:
    @pytest.mark.unit
    def test_immutable(self):
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        with pytest.raises(AttributeError):
            prov.authority = "ISO"

    @pytest.mark.unit
    def test_equality_by_value(self):
        kwargs = dict(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        assert Provenance(**kwargs) == Provenance(**kwargs)

    @pytest.mark.unit
    def test_inequality_by_value(self):
        a = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        b = Provenance(
            authority="ISO",
            specification_name="ISO 8601",
            kind="specification",
            reference_url="https://www.iso.org/iso-8601-date-and-time-format.html",
            version="2019",
            lifecycle="active",
            publication_year=2019,
        )
        assert a != b

    @pytest.mark.unit
    def test_hashable(self):
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        assert hash(prov) is not None
        assert hash(prov) == hash(prov)
```

- [ ] **Step 6: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_domain.py::TestProvenance -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 7: Write failing tests for GrammarRule**

```python
# Append to tests/unit/test_domain.py

from paxman.core.domain import GrammarRule


class TestGrammarRule:
    @pytest.mark.unit
    def test_immutable(self):
        gr = GrammarRule(capability_name="email", grammar_name="standard")
        with pytest.raises(AttributeError):
            gr.capability_name = "date"

    @pytest.mark.unit
    def test_equality(self):
        a = GrammarRule(capability_name="email", grammar_name="standard")
        b = GrammarRule(capability_name="email", grammar_name="standard")
        assert a == b

    @pytest.mark.unit
    def test_inequality(self):
        a = GrammarRule(capability_name="email", grammar_name="standard")
        b = GrammarRule(capability_name="email", grammar_name="obfuscated")
        assert a != b

    @pytest.mark.unit
    def test_hashable(self):
        gr = GrammarRule(capability_name="email", grammar_name="standard")
        assert hash(gr) is not None
```

- [ ] **Step 8: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_domain.py::TestGrammarRule -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 9: Write failing tests for Candidate**

```python
# Append to tests/unit/test_domain.py

from paxman.core.domain import Candidate, Provenance


class TestCandidate:
    @pytest.mark.unit
    def test_immutable(self):
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        c = Candidate(
            value="test@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        with pytest.raises(AttributeError):
            c.value = "other@example.com"

    @pytest.mark.unit
    def test_equality(self):
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        kwargs = dict(
            value="test@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        assert Candidate(**kwargs) == Candidate(**kwargs)

    @pytest.mark.unit
    def test_hashable(self):
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        c = Candidate(
            value="test@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        assert hash(c) is not None
```

- [ ] **Step 10: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_domain.py::TestCandidate -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 11: Write failing tests for VersionStamp**

```python
# Append to tests/unit/test_domain.py

from paxman.core.domain import VersionStamp


class TestVersionStamp:
    @pytest.mark.unit
    def test_immutable(self):
        vs = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        with pytest.raises(AttributeError):
            vs.paxman_version = "0.2.0"

    @pytest.mark.unit
    def test_equality(self):
        a = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        b = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        assert a == b

    @pytest.mark.unit
    def test_inequality(self):
        a = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        b = VersionStamp(paxman_version="0.1.0", replay_hash="def456")
        assert a != b

    @pytest.mark.unit
    def test_hashable(self):
        vs = VersionStamp(paxman_version="0.1.0", replay_hash="abc123")
        assert hash(vs) is not None
```

- [ ] **Step 12: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_domain.py::TestVersionStamp -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 13: Implement all domain objects**

```python
# paxman/core/domain.py

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class RuleStrategy(Enum):
    """Validation strategy for a rule."""

    REGEX = "regex"
    LOOKUP_TABLE = "lookup_table"
    PARSER = "parser"


class Resolution(Enum):
    """Status of the canonicalization execution."""

    MISSING = "missing"
    INVALID = "invalid"
    SUCCESS = "success"
    AMBIGUOUS = "ambiguous"


# Notation type — capability-defined, but list[str] is the generic contract.
# For capability-specific Notation, use a TypedDict or dataclass to capture positional semantics.
# The generic Notation alias is used by grammars/rules to interoperate across capabilities.
Notation = list[str]


class Provenance:
    """Authority citation for a validated value."""

    __slots__ = (
        "authority",
        "specification_name",
        "kind",
        "reference_url",
        "version",
        "lifecycle",
        "publication_year",
    )

    def __init__(
        self,
        authority: str,
        specification_name: str,
        kind: str,
        reference_url: str,
        version: str | None,
        lifecycle: str,
        publication_year: int,
    ) -> None:
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "specification_name", specification_name)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "reference_url", reference_url)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "lifecycle", lifecycle)
        object.__setattr__(self, "publication_year", publication_year)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Provenance is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Provenance is immutable")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Provenance):
            return NotImplemented
        return (
            self.authority == other.authority
            and self.specification_name == other.specification_name
            and self.kind == other.kind
            and self.reference_url == other.reference_url
            and self.version == other.version
            and self.lifecycle == other.lifecycle
            and self.publication_year == other.publication_year
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.authority,
                self.specification_name,
                self.kind,
                self.reference_url,
                self.version,
                self.lifecycle,
                self.publication_year,
            )
        )


class GrammarRule:
    """Reference to a grammar that produced a RecognizedRep."""

    __slots__ = ("capability_name", "grammar_name")

    def __init__(self, capability_name: str, grammar_name: str) -> None:
        object.__setattr__(self, "capability_name", capability_name)
        object.__setattr__(self, "grammar_name", grammar_name)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("GrammarRule is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("GrammarRule is immutable")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GrammarRule):
            return NotImplemented
        return (
            self.capability_name == other.capability_name
            and self.grammar_name == other.grammar_name
        )

    def __hash__(self) -> int:
        return hash((self.capability_name, self.grammar_name))


class Candidate:
    """Carries validation output: canonical value + provenance.

    recognition_rule and validation_rule are string-based rule names
    for traceability. If a future iteration requires instance references,
    update the Candidate fields and documentation accordingly.
    """

    __slots__ = ("value", "recognition_rule", "validation_rule", "provenance")

    def __init__(
        self,
        value: str,
        recognition_rule: str,
        validation_rule: str,
        provenance: list[Provenance],
    ) -> None:
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "recognition_rule", recognition_rule)
        object.__setattr__(self, "validation_rule", validation_rule)
        object.__setattr__(self, "provenance", tuple(provenance))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Candidate is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Candidate is immutable")

    @property
    def provenance(self) -> tuple[Provenance, ...]:
        return object.__getattribute__(self, "provenance")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Candidate):
            return NotImplemented
        return (
            self.value == other.value
            and self.recognition_rule == other.recognition_rule
            and self.validation_rule == other.validation_rule
            and self.provenance == other.provenance
        )

    def __hash__(self) -> int:
        return hash(
            (self.value, self.recognition_rule, self.validation_rule, self.provenance)
        )


class VersionStamp:
    """Replay integrity metadata."""

    __slots__ = ("paxman_version", "replay_hash")

    def __init__(self, paxman_version: str, replay_hash: str) -> None:
        object.__setattr__(self, "paxman_version", paxman_version)
        object.__setattr__(self, "replay_hash", replay_hash)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("VersionStamp is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("VersionStamp is immutable")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionStamp):
            return NotImplemented
        return (
            self.paxman_version == other.paxman_version
            and self.replay_hash == other.replay_hash
        )

    def __hash__(self) -> int:
        return hash((self.paxman_version, self.replay_hash))


class Rule(ABC):
    """Base class for validation rules."""

    name: str
    strategy: RuleStrategy
    provenance: Provenance
    citation: str

    @abstractmethod
    def matches(self, notation: Notation) -> bool:
        """Check if notation matches this rule's pattern."""
        ...

    @abstractmethod
    def normalize(self, notation: Notation) -> str:
        """Normalize notation to canonical value."""
        ...


class Grammar(ABC):
    """Base class for recognition grammars."""

    name: str

    @abstractmethod
    def recognize(self, text: str) -> list[Notation]:
        """Extract notation candidates from raw text."""
        ...
```

- [ ] **Step 14: Run all domain tests**

Run: `uv run pytest tests/unit/test_domain.py -v`
Expected: All PASS

- [ ] **Step 15: Commit**

```bash
git add paxman/core/domain.py tests/unit/test_domain.py
git commit -m "feat(core): add domain objects — Provenance, Candidate, GrammarRule, Resolution, VersionStamp, Rule, Grammar"
```

---

## Task 3: Core Error Hierarchy

**Files:**
- Create: `paxman/core/errors.py`
- Test: `tests/unit/test_errors.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_errors.py

import pytest
from paxman.core.errors import (
    CapabilityError,
    ContractError,
    PaxmanError,
    RecognitionError,
    ValidationError,
)


class TestExceptionHierarchy:
    @pytest.mark.unit
    def test_paxman_error_is_base(self):
        assert issubclass(ContractError, PaxmanError)
        assert issubclass(CapabilityError, PaxmanError)
        assert issubclass(RecognitionError, PaxmanError)
        assert issubclass(ValidationError, PaxmanError)

    @pytest.mark.unit
    def test_paxman_error_is_exception(self):
        assert issubclass(PaxmanError, Exception)

    @pytest.mark.unit
    def test_recognition_error_stores_rule(self):
        original = ValueError("bad regex")
        err = RecognitionError(
            rule="standard_recognition",
            message="invalid pattern",
            original_error=original,
        )
        assert err.rule == "standard_recognition"
        assert err.original_error is original
        assert "standard_recognition" in str(err)

    @pytest.mark.unit
    def test_validation_error_stores_rule(self):
        original = KeyError("missing")
        err = ValidationError(
            rule="rfc_5322", message="lookup failed", original_error=original
        )
        assert err.rule == "rfc_5322"
        assert err.original_error is original
        assert "rfc_5322" in str(err)

    @pytest.mark.unit
    def test_contract_error_message(self):
        err = ContractError("missing required field")
        assert "missing required field" in str(err)

    @pytest.mark.unit
    def test_capability_error_message(self):
        err = CapabilityError("unknown capability: foo")
        assert "unknown capability: foo" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_errors.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'paxman.core.errors'`

- [ ] **Step 3: Implement error hierarchy**

```python
# paxman/core/errors.py


class PaxmanError(Exception):
    """Base exception for all Paxman errors."""


class ContractError(PaxmanError):
    """Raised when contract is malformed or invalid."""


class CapabilityError(PaxmanError):
    """Raised when no capability can claim the process."""


class RecognitionError(PaxmanError):
    """Raised when grammar fails to parse input."""

    def __init__(self, rule: str, message: str, original_error: Exception) -> None:
        self.rule = rule
        self.original_error = original_error
        super().__init__(f"[{rule}] {message}")


class ValidationError(PaxmanError):
    """Raised when validation rule encounters unexpected error."""

    def __init__(self, rule: str, message: str, original_error: Exception) -> None:
        self.rule = rule
        self.original_error = original_error
        super().__init__(f"[{rule}] {message}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_errors.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add paxman/core/errors.py tests/unit/test_errors.py
git commit -m "feat(core): add exception hierarchy — PaxmanError, ContractError, CapabilityError, RecognitionError, ValidationError"
```

---

## Task 4: Contract Protocol

**Files:**
- Create: `paxman/core/contract.py`

- [ ] **Step 1: Implement Contract protocol**

```python
# paxman/core/contract.py

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
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

    @property
    def year(self) -> int | None:
        """Year for temporal filtering (publication_year <= year)."""
        ...

    def as_dict(self) -> dict[str, Any]:
        """Serialize contract for replay_hash."""
        ...
```

- [ ] **Step 2: Commit**

```bash
git add paxman/core/contract.py
git commit -m "feat(core): add Contract protocol"
```

---

## Task 5: Capability Base Class and Registry

**Files:**
- Create: `paxman/core/capability.py`
- Create: `paxman/core/discovery.py`

- [ ] **Step 1: Implement Capability base class**

```python
# paxman/core/capability.py

from __future__ import annotations

from abc import ABC, abstractmethod

from paxman.core.domain import Grammar, Rule


class Capability(ABC):
    """Base class for all capabilities."""

    name: str
    version: str

    @abstractmethod
    def get_grammars(self) -> list[Grammar]:
        """Return default grammars for this capability."""
        ...

    @abstractmethod
    def get_rules(self) -> list[Rule]:
        """Return default validation rules for this capability."""
        ...
```

- [ ] **Step 2: Implement capability registry**

```python
# paxman/core/discovery.py

from __future__ import annotations

from paxman.core.capability import Capability
from paxman.core.errors import CapabilityError

_registry: dict[str, Capability] = {}
_frozen: bool = False


def register_capability(capability: Capability) -> None:
    """Register a capability. Raises CapabilityError if registry is frozen."""
    global _frozen
    if _frozen:
        raise CapabilityError(
            "Registry is frozen. Cannot register after first canonicalize() call."
        )
    if not isinstance(capability, Capability):
        raise CapabilityError(
            f"Expected Capability instance, got {type(capability).__name__}"
        )
    if capability.name in _registry:
        raise CapabilityError(f"Capability '{capability.name}' already registered.")
    _registry[capability.name] = capability


def get_capability(name: str) -> Capability:
    """Look up a capability by name. Raises CapabilityError if not found."""
    if name not in _registry:
        raise CapabilityError(f"Unknown capability: '{name}'")
    return _registry[name]


def freeze_registry() -> None:
    """Freeze the registry so no more capabilities can be registered."""
    global _frozen
    _frozen = True


def is_registry_frozen() -> bool:
    """Check if the registry is frozen."""
    return _frozen


def reset_registry() -> None:
    """Reset the registry (for testing only)."""
    global _frozen
    _registry.clear()
    _frozen = False
```

- [ ] **Step 3: Commit**

```bash
git add paxman/core/capability.py paxman/core/discovery.py
git commit -m "feat(core): add Capability base class and discovery registry"
```

---

## Task 6: Core Module Exports

**Files:**
- Modify: `paxman/core/__init__.py`

- [ ] **Step 1: Update core __init__.py with exports**

```python
# paxman/core/__init__.py

from paxman.core.capability import Capability
from paxman.core.contract import Contract
from paxman.core.discovery import (
    freeze_registry,
    get_capability,
    is_registry_frozen,
    register_capability,
    reset_registry,
)
from paxman.core.domain import (
    Candidate,
    Grammar,
    GrammarRule,
    Notation,
    Provenance,
    Resolution,
    Rule,
    RuleStrategy,
    VersionStamp,
)
from paxman.core.errors import (
    CapabilityError,
    ContractError,
    PaxmanError,
    RecognitionError,
    ValidationError,
)

__all__ = [
    # Domain
    "Candidate",
    "Grammar",
    "GrammarRule",
    "Notation",
    "Provenance",
    "Resolution",
    "Rule",
    "RuleStrategy",
    "VersionStamp",
    # Contract
    "Contract",
    # Capability
    "Capability",
    # Errors
    "CapabilityError",
    "ContractError",
    "PaxmanError",
    "RecognitionError",
    "ValidationError",
    # Discovery
    "freeze_registry",
    "get_capability",
    "is_registry_frozen",
    "register_capability",
    "reset_registry",
]
```

- [ ] **Step 2: Verify imports work**

Run: `uv run python -c "from paxman.core import Provenance, Resolution, Capability; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add paxman/core/__init__.py
git commit -m "feat(core): add module exports"
```

---

## Task 7: Email Capability — Notation and Capability Class

**Files:**
- Create: `paxman/capabilities/Email/__init__.py`
- Create: `paxman/capabilities/Email/capability.py`
- Create: `paxman/capabilities/Email/grammar/__init__.py`
- Create: `paxman/capabilities/Email/rules/__init__.py`

- [ ] **Step 1: Create Email package structure**

```python
# paxman/capabilities/Email/__init__.py

from paxman.capabilities.Email.capability import EmailCapability

__all__ = ["EmailCapability"]
```

```python
# paxman/capabilities/Email/grammar/__init__.py
```

```python
# paxman/capabilities/Email/rules/__init__.py
```

- [ ] **Step 2: Implement EmailCapability with placeholder grammars/rules**

```python
# paxman/capabilities/Email/capability.py

from __future__ import annotations

from dataclasses import dataclass

from paxman.capabilities.Email.grammar.standard_recognition import (
    StandardEmailGrammar,
)
from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule


@dataclass(frozen=True)
class EmailNotation:
    """Email notation: local_part and domain_part."""

    local_part: str
    domain_part: str

    def as_list(self) -> list[str]:
        """Convert to list[str] for generic Rule interface."""
        return [self.local_part, self.domain_part]


class EmailCapability(Capability):
    """Email canonicalization capability."""

    name = "email"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar]:
        return [StandardEmailGrammar()]

    def get_rules(self) -> list[Rule]:
        return [Section341AddrSpec()]
```

- [ ] **Step 3: Commit**

```bash
git add paxman/capabilities/Email/
git commit -m "feat(email): add EmailCapability with EmailNotation and package structure"
```

---

## Task 8: Email Grammar — Standard Recognition

**Files:**
- Create: `paxman/capabilities/Email/grammar/standard_recognition.py`
- Test: `tests/capabilities/email/test_grammar.py`

- [ ] **Step 1: Write failing tests for standard grammar**

```python
# tests/capabilities/email/test_grammar.py

import pytest
from paxman.capabilities.Email.grammar.standard_recognition import StandardEmailGrammar


class TestStandardEmailGrammar:
    @pytest.mark.capability
    def test_recognizes_standard_email(self):
        grammar = StandardEmailGrammar()
        results = grammar.recognize("Contact us at user@example.com")
        assert len(results) == 1
        assert results[0].local_part == "user"
        assert results[0].domain_part == "example.com"

    @pytest.mark.capability
    def test_recognizes_email_with_dots(self):
        grammar = StandardEmailGrammar()
        results = grammar.recognize("Send to first.last@domain.co.uk")
        assert len(results) == 1
        assert results[0].local_part == "first.last"
        assert results[0].domain_part == "domain.co.uk"

    @pytest.mark.capability
    def test_recognizes_email_with_plus(self):
        grammar = StandardEmailGrammar()
        results = grammar.recognize("user+tag@gmail.com")
        assert len(results) == 1
        assert results[0].local_part == "user+tag"
        assert results[0].domain_part == "gmail.com"

    @pytest.mark.capability
    def test_recognizes_multiple_emails(self):
        grammar = StandardEmailGrammar()
        results = grammar.recognize("Email a@b.com or c@d.org")
        assert len(results) == 2

    @pytest.mark.capability
    def test_ignores_invalid_email(self):
        grammar = StandardEmailGrammar()
        results = grammar.recognize("not an email")
        assert len(results) == 0

    @pytest.mark.capability
    def test_ignores_obfuscated_email(self):
        grammar = StandardEmailGrammar()
        results = grammar.recognize("user at example dot com")
        assert len(results) == 0

    @pytest.mark.capability
    def test_returns_empty_for_empty_input(self):
        grammar = StandardEmailGrammar()
        results = grammar.recognize("")
        assert len(results) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/capabilities/email/test_grammar.py::TestStandardEmailGrammar -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement standard email grammar**

```python
# paxman/capabilities/Email/grammar/standard_recognition.py

from __future__ import annotations

import re

from paxman.capabilities.Email.capability import EmailNotation
from paxman.core.domain import Grammar, Notation

_STANDARD_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


class StandardEmailGrammar(Grammar):
    """Standard email recognition: user@domain.tld"""

    name = "standard_recognition"

    def recognize(self, text: str) -> list[Notation]:
        matches = _STANDARD_PATTERN.findall(text)
        return [
            EmailNotation(
                local_part=match.split("@")[0],
                domain_part=match.split("@")[1],
            ).as_list()
            for match in matches
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/capabilities/email/test_grammar.py::TestStandardEmailGrammar -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add paxman/capabilities/Email/grammar/standard_recognition.py tests/capabilities/email/test_grammar.py
git commit -m "feat(email): add StandardEmailGrammar with tests"
```

---

## Task 9: Email Grammar — Obfuscated and Localhost Recognition

**Files:**
- Create: `paxman/capabilities/Email/grammar/obfuscated_recognition.py`
- Create: `paxman/capabilities/Email/grammar/localhost_recognition.py`
- Test: `tests/capabilities/email/test_grammar.py` (append)

- [ ] **Step 1: Write failing tests for obfuscated grammar**

```python
# Append to tests/capabilities/email/test_grammar.py

from paxman.capabilities.Email.grammar.obfuscated_recognition import (
    ObfuscatedEmailGrammar,
)


class TestObfuscatedEmailGrammar:
    @pytest.mark.capability
    def test_recognizes_at_dot_format(self):
        grammar = ObfuscatedEmailGrammar()
        results = grammar.recognize("Contact user at example dot com")
        assert len(results) == 1
        assert results[0].local_part == "user"
        assert results[0].domain_part == "example.com"

    @pytest.mark.capability
    def test_recognizes_at_symbol_format(self):
        grammar = ObfuscatedEmailGrammar()
        results = grammar.recognize("Email user at gmail.com")
        assert len(results) == 1
        assert results[0].local_part == "user"
        assert results[0].domain_part == "gmail.com"

    @pytest.mark.capability
    def test_ignores_standard_email(self):
        grammar = ObfuscatedEmailGrammar()
        results = grammar.recognize("user@example.com")
        assert len(results) == 0

    @pytest.mark.capability
    def test_returns_empty_for_no_email(self):
        grammar = ObfuscatedEmailGrammar()
        results = grammar.recognize("no email here")
        assert len(results) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/capabilities/email/test_grammar.py::TestObfuscatedEmailGrammar -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement obfuscated email grammar**

```python
# paxman/capabilities/Email/grammar/obfuscated_recognition.py

from __future__ import annotations

import re

from paxman.capabilities.Email.capability import EmailNotation
from paxman.core.domain import Grammar, Notation

# Matches: "user at domain dot tld" or "user at domain.tld"
_OBFUSCATED_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)\s+at\s+([A-Za-z0-9.-]+)\s+dot\s+([A-Za-z]{2,})\b"
)
_AT_ONLY_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)\s+at\s+([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)


def _clean_domain(domain_parts: list[str]) -> str:
    """Join domain parts and strip trailing punctuation."""
    domain = ".".join(domain_parts)
    return domain.rstrip(".")


class ObfuscatedEmailGrammar(Grammar):
    """Obfuscated email recognition: 'user at domain dot tld'"""

    name = "obfuscated_recognition"

    def recognize(self, text: str) -> list[Notation]:
        results: list[Notation] = []

        # Try "at ... dot ..." format first
        for match in _OBFUSCATED_PATTERN.finditer(text):
            local_part = match.group(1)
            domain = _clean_domain([match.group(2), match.group(3)])
            results.append(
                EmailNotation(local_part=local_part, domain_part=domain).as_list()
            )

        # Try "at domain.tld" format (no "dot")
        for match in _AT_ONLY_PATTERN.finditer(text):
            local_part = match.group(1)
            domain = match.group(2)
            notation = EmailNotation(
                local_part=local_part, domain_part=domain
            ).as_list()
            # Avoid duplicates from the dot pattern
            if notation not in results:
                results.append(notation)

        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/capabilities/email/test_grammar.py::TestObfuscatedEmailGrammar -v`
Expected: All PASS

- [ ] **Step 5: Write failing tests for localhost grammar**

```python
# Append to tests/capabilities/email/test_grammar.py

from paxman.capabilities.Email.grammar.localhost_recognition import (
    LocalhostEmailGrammar,
)


class TestLocalhostEmailGrammar:
    @pytest.mark.capability
    def test_recognizes_localhost_email(self):
        grammar = LocalhostEmailGrammar()
        results = grammar.recognize("Send to admin@localhost")
        assert len(results) == 1
        assert results[0].local_part == "admin"
        assert results[0].domain_part == "localhost"

    @pytest.mark.capability
    def test_recognizes_localhost_with_port(self):
        grammar = LocalhostEmailGrammar()
        results = grammar.recognize("user@localhost:8080")
        assert len(results) == 1
        assert results[0].local_part == "user"
        assert results[0].domain_part == "localhost"

    @pytest.mark.capability
    def test_ignores_standard_email(self):
        grammar = LocalhostEmailGrammar()
        results = grammar.recognize("user@example.com")
        assert len(results) == 0

    @pytest.mark.capability
    def test_returns_empty_for_no_email(self):
        grammar = LocalhostEmailGrammar()
        results = grammar.recognize("no email here")
        assert len(results) == 0
```

- [ ] **Step 6: Run test to verify it fails**

Run: `uv run pytest tests/capabilities/email/test_grammar.py::TestLocalhostEmailGrammar -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 7: Implement localhost email grammar**

```python
# paxman/capabilities/Email/grammar/localhost_recognition.py

from __future__ import annotations

import re

from paxman.capabilities.Email.capability import EmailNotation
from paxman.core.domain import Grammar, Notation

_LOCALHOST_PATTERN = re.compile(r"\b([A-Za-z0-9._%+-]+)@localhost(?::\d+)?\b")


class LocalhostEmailGrammar(Grammar):
    """Localhost email recognition: user@localhost"""

    name = "localhost_recognition"

    def recognize(self, text: str) -> list[Notation]:
        matches = _LOCALHOST_PATTERN.findall(text)
        return [
            EmailNotation(local_part=match, domain_part="localhost").as_list()
            for match in matches
        ]
```

- [ ] **Step 8: Run all grammar tests**

Run: `uv run pytest tests/capabilities/email/test_grammar.py -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add paxman/capabilities/Email/grammar/ tests/capabilities/email/test_grammar.py
git commit -m "feat(email): add ObfuscatedEmailGrammar and LocalhostEmailGrammar with tests"
```

---

## Task 10: Email Rules — RFC 5322 and RFC 6761

**Files:**
- Create: `paxman/capabilities/Email/rules/rfc_5322_ed2008.py`
- Create: `paxman/capabilities/Email/rules/rfc_6761_ed2012.py`
- Test: `tests/capabilities/email/test_rules.py`

- [ ] **Step 1: Write failing tests for RFC 5322 rule**

```python
# tests/capabilities/email/test_rules.py

import pytest
from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec


class TestSection341AddrSpec:
    @pytest.mark.capability
    def test_matches_valid_email(self):
        rule = Section341AddrSpec()
        assert rule.matches(["user", "example.com"]) is True

    @pytest.mark.capability
    def test_matches_email_with_dots(self):
        rule = Section341AddrSpec()
        assert rule.matches(["first.last", "domain.co.uk"]) is True

    @pytest.mark.capability
    def test_matches_email_with_plus(self):
        rule = Section341AddrSpec()
        assert rule.matches(["user+tag", "gmail.com"]) is True

    @pytest.mark.capability
    def test_rejects_local_part_with spaces(self):
        rule = Section341AddrSpec()
        assert rule.matches(["user name", "example.com"]) is False

    @pytest.mark.capability
    def test_rejects_domain_without_tld(self):
        rule = Section341AddrSpec()
        assert rule.matches(["user", "localhost"]) is False

    @pytest.mark.capability
    def test_normalize_lowercases(self):
        rule = Section341AddrSpec()
        result = rule.normalize(["User", "Example.COM"])
        assert result == "user@example.com"

    @pytest.mark.capability
    def test_provenance_attributes(self):
        rule = Section341AddrSpec()
        assert rule.provenance.authority == "IETF"
        assert rule.provenance.specification_name == "RFC 5322"
        assert rule.provenance.publication_year == 2008
        assert rule.provenance.lifecycle == "active"

    @pytest.mark.capability
    def test_rule_name(self):
        rule = Section341AddrSpec()
        assert rule.name == "Section 3.4.1-addr-spec"

    @pytest.mark.capability
    def test_strategy_is_regex(self):
        from paxman.core.domain import RuleStrategy

        rule = Section341AddrSpec()
        assert rule.strategy == RuleStrategy.REGEX
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/capabilities/email/test_rules.py::TestSection341AddrSpec -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement RFC 5322 rule**

```python
# paxman/capabilities/Email/rules/rfc_5322_ed2008.py

from __future__ import annotations

import re

from paxman.core.domain import Notation, Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="IETF",
    specification_name="RFC 5322",
    kind="specification",
    reference_url="https://tools.ietf.org/html/rfc5322",
    version="2008",
    lifecycle="active",
    publication_year=2008,
)

_LOCAL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+$")
_DOMAIN_PATTERN = re.compile(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class Section341AddrSpec(Rule):
    """RFC 5322 Section 3.4.1 - addr-spec"""

    name = "Section 3.4.1-addr-spec"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "Section 3.4.1 (addr-spec)"

    def matches(self, notation: Notation) -> bool:
        local_part, domain_part = notation[0], notation[1]
        return bool(
            _LOCAL_PATTERN.match(local_part) and _DOMAIN_PATTERN.match(domain_part)
        )

    def normalize(self, notation: Notation) -> str:
        local_part, domain_part = notation[0], notation[1]
        return f"{local_part.lower()}@{domain_part.lower()}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/capabilities/email/test_rules.py::TestSection341AddrSpec -v`
Expected: All PASS

- [ ] **Step 5: Write failing tests for RFC 6761 rule**

```python
# Append to tests/capabilities/email/test_rules.py

from paxman.capabilities.Email.rules.rfc_6761_ed2012 import Section63localhost


class TestSection63Localhost:
    @pytest.mark.capability
    def test_matches_localhost_email(self):
        rule = Section63localhost()
        assert rule.matches(["admin", "localhost"]) is True

    @pytest.mark.capability
    def test_matches_any_local_part(self):
        rule = Section63localhost()
        assert rule.matches(["anything", "localhost"]) is True

    @pytest.mark.capability
    def test_rejects_non_localhost_domain(self):
        rule = Section63localhost()
        assert rule.matches(["user", "example.com"]) is False

    @pytest.mark.capability
    def test_normalize_preserves_case(self):
        rule = Section63localhost()
        result = rule.normalize(["Admin", "localhost"])
        assert result == "Admin@localhost"

    @pytest.mark.capability
    def test_provenance_attributes(self):
        rule = Section63localhost()
        assert rule.provenance.authority == "IETF"
        assert rule.provenance.specification_name == "RFC 6761"
        assert rule.provenance.publication_year == 2012
        assert rule.provenance.lifecycle == "active"

    @pytest.mark.capability
    def test_rule_name(self):
        rule = Section63localhost()
        assert rule.name == "Section 6.3-localhost"

    @pytest.mark.capability
    def test_strategy_is_regex(self):
        from paxman.core.domain import RuleStrategy

        rule = Section63localhost()
        assert rule.strategy == RuleStrategy.REGEX
```

- [ ] **Step 6: Run test to verify it fails**

Run: `uv run pytest tests/capabilities/email/test_rules.py::TestSection63Localhost -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 7: Implement RFC 6761 rule**

```python
# paxman/capabilities/Email/rules/rfc_6761_ed2012.py

from __future__ import annotations

from paxman.core.domain import Notation, Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="IETF",
    specification_name="RFC 6761",
    kind="specification",
    reference_url="https://tools.ietf.org/html/rfc6761",
    version="2012",
    lifecycle="active",
    publication_year=2012,
)


class Section63localhost(Rule):
    """RFC 6761 Section 6.3 - localhost"""

    name = "Section 6.3-localhost"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "Section 6.3 (localhost)"

    def matches(self, notation: Notation) -> bool:
        domain_part = notation[1]
        return domain_part == "localhost"

    def normalize(self, notation: Notation) -> str:
        local_part = notation[0]
        return f"{local_part}@localhost"
```

- [ ] **Step 8: Run all rule tests**

Run: `uv run pytest tests/capabilities/email/test_rules.py -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add paxman/capabilities/Email/rules/ tests/capabilities/email/test_rules.py
git commit -m "feat(email): add RFC 5322 and RFC 6761 validation rules with tests"
```

---

## Task 11: Update EmailCapability with All Grammars and Rules

**Files:**
- Modify: `paxman/capabilities/Email/capability.py`

- [ ] **Step 1: Update EmailCapability to include all grammars and rules**

```python
# paxman/capabilities/Email/capability.py

from __future__ import annotations

from dataclasses import dataclass

from paxman.capabilities.Email.grammar.localhost_recognition import (
    LocalhostEmailGrammar,
)
from paxman.capabilities.Email.grammar.obfuscated_recognition import (
    ObfuscatedEmailGrammar,
)
from paxman.capabilities.Email.grammar.standard_recognition import (
    StandardEmailGrammar,
)
from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec
from paxman.capabilities.Email.rules.rfc_6761_ed2012 import Section63localhost
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule


@dataclass(frozen=True)
class EmailNotation:
    """Email notation: local_part and domain_part."""

    local_part: str
    domain_part: str

    def as_list(self) -> list[str]:
        """Convert to list[str] for generic Rule interface."""
        return [self.local_part, self.domain_part]


class EmailCapability(Capability):
    """Email canonicalization capability."""

    name = "email"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar]:
        return [
            StandardEmailGrammar(),
            ObfuscatedEmailGrammar(),
            LocalhostEmailGrammar(),
        ]

    def get_rules(self) -> list[Rule]:
        return [
            Section341AddrSpec(),
            Section63localhost(),
        ]
```

- [ ] **Step 2: Update Email __init__.py exports**

```python
# paxman/capabilities/Email/__init__.py

from paxman.capabilities.Email.capability import EmailCapability, EmailNotation

__all__ = ["EmailCapability", "EmailNotation"]
```

- [ ] **Step 3: Commit**

```bash
git add paxman/capabilities/Email/capability.py paxman/capabilities/Email/__init__.py
git commit -m "feat(email): update EmailCapability with all grammars and rules"
```

---

## Task 12: Engine Orchestrator

**Files:**
- Create: `paxman/engine/orchestrator.py`
- Test: `tests/integration/test_pipeline.py`

- [ ] **Step 1: Write failing tests for orchestrator**

```python
# tests/integration/test_pipeline.py

import pytest
from paxman.capabilities.Email.capability import EmailCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.engine.orchestrator import ExecutionResult, run_capability


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


class TestRunCapability:
    @pytest.mark.integration
    def test_standard_email_success(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("Contact user@example.com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"
        assert len(result.candidates) >= 1

    @pytest.mark.integration
    def test_obfuscated_email_success(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract(include_obfuscated=True)
        result = run_capability("Email user at example dot com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.integration
    def test_localhost_email_success(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("Send to admin@localhost", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"

    @pytest.mark.integration
    def test_missing_input(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("no email here", contract)

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_version_stamp_present(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("user@example.com", contract)

        assert result.version_stamp is not None
        assert result.version_stamp.paxman_version == "0.1.0"
        assert len(result.version_stamp.replay_hash) == 64  # SHA-256 hex

    @pytest.mark.integration
    def test_replay_determinism(self):
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        r1 = run_capability("user@example.com", contract)
        r2 = run_capability("user@example.com", contract)

        assert r1.version_stamp.replay_hash == r2.version_stamp.replay_hash
        assert r1.canonicalized_value == r2.canonicalized_value
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_pipeline.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement orchestrator**

```python
# paxman/engine/orchestrator.py

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from paxman.core.capability import Capability
from paxman.core.contract import Contract
from paxman.core.discovery import freeze_registry, get_capability
from paxman.core.domain import Candidate, Resolution, VersionStamp

PAXMAN_VERSION = "0.1.0"


@dataclass(frozen=True)
class ExecutionResult:
    """Final output from paxman.canonicalize()."""

    status: Resolution
    canonicalized_value: str | None
    candidates: tuple[Candidate, ...]
    contract: Contract
    version_stamp: VersionStamp


def run_capability(text: str, contract: Contract) -> ExecutionResult:
    """Run the full pipeline: recognition → validation → result."""
    freeze_registry()
    capability = get_capability(contract.capability_name)
    candidates = _validate(text, capability, contract)
    status = _determine_status(candidates)
    canonical_value = _extract_canonical_value(candidates, status)
    version_stamp = _build_version_stamp(text, candidates, contract, status)
    return ExecutionResult(
        status=status,
        canonicalized_value=canonical_value,
        candidates=tuple(candidates),
        contract=contract,
        version_stamp=version_stamp,
    )


def _validate(text: str, capability: Capability, contract: Contract) -> list[Candidate]:
    """Run recognition then validation, returning all candidates."""
    active_grammar_names = set(contract.active_grammars)
    all_grammars = capability.get_grammars()
    active_grammars = [g for g in all_grammars if g.name in active_grammar_names]

    recognitions: list[tuple[list[str], str]] = []
    for grammar in active_grammars:
        try:
            notations = grammar.recognize(text)
        except Exception as exc:
            from paxman.core.errors import RecognitionError

            raise RecognitionError(
                rule=grammar.name,
                message=f"Grammar failed: {exc}",
                original_error=exc,
            ) from exc
        for notation in notations:
            recognitions.append((notation, grammar.name))

    all_rules = capability.get_rules()
    excluded = set(contract.excluded_rules)
    active_rules = [r for r in all_rules if r.name not in excluded]

    candidates: list[Candidate] = []
    for notation, grammar_name in recognitions:
        for rule in active_rules:
            if contract.year is not None:
                if rule.provenance.publication_year > contract.year:
                    continue
            try:
                if rule.matches(notation):
                    canonical = rule.normalize(notation)
                    candidates.append(
                        Candidate(
                            value=canonical,
                            recognition_rule=grammar_name,
                            validation_rule=rule.name,
                            provenance=[rule.provenance],
                        )
                    )
            except Exception as exc:
                from paxman.core.errors import ValidationError

                raise ValidationError(
                    rule=rule.name,
                    message=f"Validation failed: {exc}",
                    original_error=exc,
                ) from exc

    return candidates


def _determine_status(candidates: list[Candidate]) -> Resolution:
    """Determine resolution status from candidates."""
    if not candidates:
        return Resolution.MISSING
    values = {c.value for c in candidates}
    if len(values) == 1:
        return Resolution.SUCCESS
    return Resolution.AMBIGUOUS


def _extract_canonical_value(
    candidates: list[Candidate], status: Resolution
) -> str | None:
    """Extract canonical value if status is SUCCESS."""
    if status == Resolution.SUCCESS and candidates:
        return candidates[0].value
    return None


def _build_version_stamp(
    text: str,
    candidates: list[Candidate],
    contract: Contract,
    status: Resolution,
) -> VersionStamp:
    """Compute replay-safe version stamp."""
    replay_hash = _compute_replay_hash(text, candidates, contract, status)
    return VersionStamp(paxman_version=PAXMAN_VERSION, replay_hash=replay_hash)


def _compute_replay_hash(
    text: str,
    candidates: list[Candidate],
    contract: Contract,
    status: Resolution,
) -> str:
    """SHA-256 of canonical bytes for deterministic replay."""
    canonical_bytes = {
        "input": text,
        "contract": contract.as_dict(),
        "status": status.value,
        "candidates": sorted(
            [
                {
                    "value": c.value,
                    "recognition_rule": c.recognition_rule,
                    "validation_rule": c.validation_rule,
                    "provenance": sorted(
                        [
                            {
                                "authority": p.authority,
                                "specification_name": p.specification_name,
                                "kind": p.kind,
                                "reference_url": p.reference_url,
                                "version": p.version,
                                "lifecycle": p.lifecycle,
                                "publication_year": p.publication_year,
                            }
                            for p in c.provenance
                        ],
                        key=lambda x: x["authority"],
                    ),
                }
                for c in candidates
            ],
            key=lambda x: (x["value"], x["validation_rule"]),
        ),
    }
    canonical_json = json.dumps(canonical_bytes, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Add create_contract to EmailCapability**

```python
# Append to paxman/capabilities/Email/capability.py

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmailContract:
    """User-facing contract for Email capability."""

    capability_name: str = field(default="email", init=False)
    include_obfuscated: bool = False
    include_localhost: bool = True
    excluded_rules: list[str] = field(default_factory=list)
    year: int | None = None

    @property
    def active_grammars(self) -> list[str]:
        grammars = ["standard_recognition"]
        if self.include_obfuscated:
            grammars.append("obfuscated_recognition")
        if self.include_localhost:
            grammars.append("localhost_recognition")
        return grammars

    def as_dict(self) -> dict:
        return {
            "capability_name": self.capability_name,
            "include_obfuscated": self.include_obfuscated,
            "include_localhost": self.include_localhost,
            "excluded_rules": self.excluded_rules,
            "year": self.year,
        }


# Add class method to EmailCapability
def _create_contract(
    include_obfuscated: bool = False,
    include_localhost: bool = True,
    excluded_rules: list[str] | None = None,
    year: int | None = None,
) -> EmailContract:
    return EmailContract(
        include_obfuscated=include_obfuscated,
        include_localhost=include_localhost,
        excluded_rules=excluded_rules or [],
        year=year,
    )


EmailCapability.create_contract = staticmethod(_create_contract)
```

- [ ] **Step 5: Run integration tests**

Run: `uv run pytest tests/integration/test_pipeline.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add paxman/engine/orchestrator.py paxman/capabilities/Email/capability.py tests/integration/test_pipeline.py
git commit -m "feat(engine): add pipeline orchestrator with ExecutionResult and replay hash"
```

---

## Task 13: Ambiguity Detection Tests

**Files:**
- Test: `tests/integration/test_ambiguity.py`

- [ ] **Step 1: Write ambiguity tests**

```python
# tests/integration/test_ambiguity.py

import pytest
from paxman.capabilities.Email.capability import EmailCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.engine.orchestrator import run_capability


@pytest.fixture(autouse=True)
def _clean_registry():
    reset_registry()
    yield
    reset_registry()


class TestAmbiguityDetection:
    @pytest.mark.integration
    def test_localhost_and_rfc5322_same_value(self):
        """localhost@localhost → both rules agree → SUCCESS."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("admin@localhost", contract)

        # Both RFC 5322 and RFC 6761 reject localhost domain,
        # but RFC 6761 matches. Only one candidate value.
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"

    @pytest.mark.integration
    def test_multiple_emails_produce_multiple_candidates(self):
        """Two different emails → multiple candidates with different values → AMBIGUOUS."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract()
        result = run_capability("a@b.com and c@d.org", contract)

        # Two different canonical values from two recognitions
        assert result.status == Resolution.AMBIGUOUS
        assert result.canonicalized_value is None
        assert len(result.candidates) >= 2
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_ambiguity.py -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_ambiguity.py
git commit -m "test(integration): add ambiguity detection tests"
```

---

## Task 14: Temporal Filtering Tests

**Files:**
- Test: `tests/integration/test_temporal.py`

- [ ] **Step 1: Write temporal filtering tests**

```python
# tests/integration/test_temporal.py

import pytest
from paxman.capabilities.Email.capability import EmailCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution
from paxman.engine.orchestrator import run_capability


@pytest.fixture(autouse=True)
def _clean_registry():
    reset_registry()
    yield
    reset_registry()


class TestTemporalFiltering:
    @pytest.mark.integration
    def test_year_filters_out_future_rules(self):
        """Year=2007 excludes RFC 5322 (2008) and RFC 6761 (2012)."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract(year=2007)
        result = run_capability("user@example.com", contract)

        # No rules active (both published after 2007) → recognized but invalid
        assert result.status == Resolution.MISSING
        assert len(result.candidates) == 0

    @pytest.mark.integration
    def test_year_includes_matching_rules(self):
        """Year=2010 includes RFC 5322 (2008) but excludes RFC 6761 (2012)."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract(year=2010)
        result = run_capability("user@example.com", contract)

        # RFC 5322 active, RFC 6761 excluded
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.integration
    def test_year_none_includes_all_rules(self):
        """No year pin → all rules active."""
        cap = EmailCapability()
        register_capability(cap)

        contract = EmailCapability.create_contract(year=None)
        result = run_capability("admin@localhost", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_temporal.py -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_temporal.py
git commit -m "test(integration): add temporal filtering tests"
```

---

## Task 15: Public API

**Files:**
- Create: `paxman/api/canonicalize.py`
- Modify: `paxman/__init__.py`
- Test: `tests/e2e/test_canonicalize.py`

- [ ] **Step 1: Write failing E2E tests**

```python
# tests/e2e/test_canonicalize.py

import pytest
import paxman
from paxman.capabilities.Email.capability import EmailCapability, EmailContract
from paxman.core.discovery import reset_registry
from paxman.core.domain import Resolution


@pytest.fixture(autouse=True)
def _clean_registry():
    reset_registry()
    yield
    reset_registry()


class TestCanonicalizeE2E:
    @pytest.mark.e2e
    def test_standard_email(self):
        result = paxman.canonicalize("Contact user@example.com", EmailContract())

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"
        assert len(result.candidates) >= 1
        assert result.version_stamp.paxman_version == "0.1.0"

    @pytest.mark.e2e
    def test_obfuscated_email(self):
        contract = EmailContract(include_obfuscated=True)
        result = paxman.canonicalize("Email user at example dot com", contract)

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "user@example.com"

    @pytest.mark.e2e
    def test_localhost_email(self):
        result = paxman.canonicalize("Send to admin@localhost", EmailContract())

        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "admin@localhost"

    @pytest.mark.e2e
    def test_missing_input(self):
        result = paxman.canonicalize("no email here", EmailContract())

        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None

    @pytest.mark.e2e
    def test_replay_determinism(self):
        contract = EmailContract()
        r1 = paxman.canonicalize("user@example.com", contract)
        r2 = paxman.canonicalize("user@example.com", contract)

        assert r1.version_stamp.replay_hash == r2.version_stamp.replay_hash

    @pytest.mark.e2e
    def test_provenance_in_candidates(self):
        result = paxman.canonicalize("user@example.com", EmailContract())

        assert len(result.candidates) >= 1
        candidate = result.candidates[0]
        assert len(candidate.provenance) >= 1
        assert candidate.provenance[0].authority == "IETF"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/e2e/test_canonicalize.py -v`
Expected: FAIL with `ImportError: cannot import name 'canonicalize'`

- [ ] **Step 3: Implement public canonicalize function**

```python
# paxman/api/canonicalize.py

from __future__ import annotations

from paxman.core.contract import Contract
from paxman.core.discovery import freeze_registry
from paxman.engine.orchestrator import ExecutionResult, run_capability


def canonicalize(text: str, contract: Contract) -> ExecutionResult:
    """Canonicalize text against authoritative specifications.

    Args:
        text: Raw input text to canonicalize.
        contract: Capability-specific contract configuration.

    Returns:
        ExecutionResult with status, canonical value, candidates, and version stamp.
    """
    freeze_registry()
    return run_capability(text, contract)
```

- [ ] **Step 4: Update paxman/__init__.py with exports**

```python
# paxman/__init__.py

from paxman.api.canonicalize import canonicalize
from paxman.core.discovery import register_capability

__all__ = ["canonicalize", "register_capability"]
```

- [ ] **Step 5: Run E2E tests**

Run: `uv run pytest tests/e2e/test_canonicalize.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add paxman/api/canonicalize.py paxman/__init__.py tests/e2e/test_canonicalize.py
git commit -m "feat(api): add public canonicalize() function with E2E tests"
```

---

## Task 16: Capability Registration Exports

**Files:**
- Modify: `paxman/capabilities/__init__.py`

- [ ] **Step 1: Update capabilities __init__.py**

```python
# paxman/capabilities/__init__.py

from paxman.capabilities.Email import EmailCapability

__all__ = ["EmailCapability"]
```

- [ ] **Step 2: Verify import works**

Run: `uv run python -c "from paxman.capabilities import EmailCapability; print(EmailCapability.name)"`
Expected: `email`

- [ ] **Step 3: Commit**

```bash
git add paxman/capabilities/__init__.py
git commit -m "feat(capabilities): add Email capability exports"
```

---

## Task 17: Run Full Test Suite and Quality Gates

**Files:**
- No new files

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run ruff linter**

Run: `uv run ruff check paxman/ tests/`
Expected: No errors

- [ ] **Step 3: Run ruff formatter check**

Run: `uv run ruff format --check paxman/ tests/`
Expected: All files formatted

- [ ] **Step 4: Run pyright type checker**

Run: `uv run pyright paxman/`
Expected: No errors (or only pre-existing warnings)

- [ ] **Step 5: Run import-linter**

Run: `uv run importlinter`
Expected: All contracts pass

- [ ] **Step 6: Run tests with coverage**

Run: `uv run pytest tests/ --cov=paxman --cov-report=term-missing`
Expected: Coverage report generated

- [ ] **Step 7: Commit any lint/format fixes**

```bash
git add -A
git commit -m "fix: lint and format fixes from quality gates" || echo "No fixes needed"
```

---

## Task 18: Final Commit and Verification

**Files:**
- No new files

- [ ] **Step 1: Verify directory structure matches spec**

Run: `find paxman/ -name "*.py" | sort`
Expected: Structure matches File Structure section

- [ ] **Step 2: Verify all imports are clean**

Run: `uv run python -c "import paxman; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Run complete test suite one final time**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: Email capability implementation complete

- Core domain: Provenance, Candidate, GrammarRule, Resolution, VersionStamp, Rule, Grammar
- Exception hierarchy: PaxmanError, ContractError, CapabilityError, RecognitionError, ValidationError
- Contract protocol and Capability base class
- Capability registry with freeze semantics
- Email capability: EmailNotation, EmailContract
- Email grammars: standard, obfuscated, localhost
- Email rules: RFC 5322 (addr-spec), RFC 6761 (localhost)
- Engine orchestrator with replay-safe hashing
- Public API: paxman.canonicalize()
- Full test suite: unit, capability, integration, e2e"
```

---

## Self-Review Checklist

- [ ] **Spec coverage:** All 17 ADR design decisions addressed? Yes — see mapping below.
- [ ] **Placeholder scan:** No TBD/TODO/placeholders in any step.
- [ ] **Type consistency:** Capability-specific Notation uses a TypedDict or dataclass (e.g., EmailNotation), while the generic Notation alias remains `list[str]`. `EmailNotation.as_list()` can bridge capability-specific Notation to the generic list[str] contract if needed.
- [ ] **Candidate semantics:** Candidate.recognition_rule and Candidate.validation_rule are string-based rule names for traceability; update documentation/implementation if instance references are desired later.
- [ ] **Import boundaries:** `paxman.core` never imports from `capabilities`; `capabilities` only imports from `core`.
- [ ] **TDD cycle:** Every task follows red-green-refactor with exact test code and commands.

### ADR Design Decision Mapping

| ADR Decision | Task |
|---|---|
| 1. Separate Recognition from Validation | Tasks 8-10 (grammars separate from rules) |
| 2. Notation as Internal Contract | Task 7 (EmailNotation) |
| 3. Provenance Decentralized into Rules | Tasks 10 (PUBLICATION per rule file) |
| 4. Temporal Filtering via Publication Year | Task 14 (temporal tests) |
| 5. Exhaustive Recognition | Task 8 (all grammars run) |
| 6. Replay Hash for Determinism | Task 12 (_compute_replay_hash) |
| 7. Resolution Enum for Status | Task 2 (Resolution enum) |
| 8. Exception Hierarchy | Task 3 (errors.py) |
| 9. Capability Versioning | Task 7 (EmailCapability.version) |
| 10. Engine Versioning | Task 12 (PAXMAN_VERSION) |
| 11. Rule-Provenance Structure | Task 10 (one file = one publication) |
| 12. Three Validation Strategies | Task 2 (RuleStrategy enum) |
| 13. GrammarRule Reference | Task 2 (GrammarRule dataclass) |
| 14. Notation for Placement-Sensitive Rules | Task 7 (EmailNotation with position) |
| 15. Contract Rule Exclusion | Task 12 (excluded_rules filtering) |
| 16. Exhaustive Rule Validation | Task 12 (_validate runs all rules) |
| 17. Engine Responsibility for ExecutionResult | Task 12 (orchestrator builds result) |
