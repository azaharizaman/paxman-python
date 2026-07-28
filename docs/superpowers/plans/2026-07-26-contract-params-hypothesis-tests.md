# Contract Parameters + Hypothesis Tests + Test Reorganization

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `output_format` and `two_digit_base_year` contract parameters, add Hypothesis property-based tests, and reorganize test files to match documentation structure.

**Architecture:** Extend the Contract protocol with two new optional parameters (`output_format` for controlling canonical value format, `two_digit_base_year` for interpreting two-digit years). Implement a Date capability that uses these parameters. Add Hypothesis property-based tests for domain objects, grammars, and rules. Reorganize test files to match the per-object structure documented in CONTEXT.md.

**Tech Stack:** Python 3.11, Hypothesis, pytest, dataclasses, ABC, Protocol

---

## File Structure

### Files to Create

```
paxman/capabilities/Date/
├── __init__.py                    # Export DateCapability, DateContract, DateNotation
├── capability.py                  # DateCapability, DateContract, create_contract()
├── notation.py                    # DateNotation frozen dataclass
├── grammar/
│   ├── __init__.py                # Empty package init
│   ├── iso8601_recognition.py     # ISO 8601 date grammar (YYYY-MM-DD)
│   ├── us_recognition.py          # US date grammar (MM/DD/YYYY)
│   └── european_recognition.py    # European date grammar (DD/MM/YYYY)
└── rules/
    ├── __init__.py                # Empty package init
    ├── iso_8601_ed2019.py         # ISO 8601 date rule
    └── us_federal_rules_ed2023.py # US federal date rule

tests/unit/
├── test_provenance.py             # Provenance dataclass tests
├── test_candidate.py              # Candidate dataclass tests
├── test_recognized_rep.py         # RecognizedRep dataclass tests
├── test_version_stamp.py          # VersionStamp tests
└── test_resolution.py             # Resolution enum tests

tests/property/
├── __init__.py                    # Empty package init
├── test_domain_properties.py      # Hypothesis tests for domain objects
├── test_grammar_properties.py     # Hypothesis tests for grammars
└── test_rule_properties.py        # Hypothesis tests for rules
```

### Files to Modify

```
paxman/core/contract.py            # Add output_format, two_digit_base_year
paxman/core/domain.py              # Add Contract parameter to Rule interface
paxman/engine/orchestrator.py      # Pass contract to rule.matches() and rule.normalize()
paxman/capabilities/__init__.py    # Add Date capability export
paxman/capabilities/Email/capability.py  # Update create_contract() signature
paxman/capabilities/Email/contract.py    # Add new parameters with defaults
paxman/capabilities/Email/rules/rfc_5322_ed2008.py  # Update matches/normalize signatures
paxman/capabilities/Email/rules/rfc_6761_ed2012.py  # Update matches/normalize signatures
tests/unit/test_domain.py          # Remove (split into per-object files)
```

---

## Task 1: Extend Contract Protocol

**Files:**
- Modify: `paxman/core/contract.py:1-33`
- Test: `tests/unit/test_contract.py`

- [ ] **Step 1: Write failing tests for new contract parameters**

```python
# tests/unit/test_contract.py - add these tests

def test_contract_has_output_format_property():
    """Contract protocol defines output_format property."""
    assert hasattr(Contract, "output_format")


def test_contract_has_two_digit_base_year_property():
    """Contract protocol defines two_digit_base_year property."""
    assert hasattr(Contract, "two_digit_base_year")


def test_email_contract_output_format_defaults_to_none():
    """EmailContract.output_format defaults to None."""
    contract = EmailContract()
    assert contract.output_format is None


def test_email_contract_two_digit_base_year_defaults_to_none():
    """EmailContract.two_digit_base_year defaults to None."""
    contract = EmailContract()
    assert contract.two_digit_base_year is None


def test_email_contract_with_output_format():
    """EmailContract accepts output_format parameter."""
    contract = EmailContract(output_format="ISO")
    assert contract.output_format == "ISO"


def test_email_contract_with_two_digit_base_year():
    """EmailContract accepts two_digit_base_year parameter."""
    contract = EmailContract(two_digit_base_year=2000)
    assert contract.two_digit_base_year == 2000
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_contract.py -v`
Expected: FAIL with "Contract has no attribute 'output_format'"

- [ ] **Step 3: Add new properties to Contract protocol**

```python
# paxman/core/contract.py

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Contract(Protocol):
    """Base protocol for all capability contracts."""

    @property
    def capability_name(self) -> str:
        """Name of the capability this contract configures."""
        ...

    @property
    def active_grammars(self) -> Sequence[str]:
        """Grammar names to activate."""
        ...

    @property
    def excluded_rules(self) -> Sequence[str]:
        """Rule names to exclude."""
        ...

    @property
    def year(self) -> int | None:
        """Year for temporal filtering (publication_year <= year)."""
        ...

    @property
    def output_format(self) -> str | None:
        """Output format for canonical values (e.g., 'ISO', 'US')."""
        ...

    @property
    def two_digit_base_year(self) -> int | None:
        """Base year for interpreting two-digit years (e.g., 2000 for '25' -> 2025)."""
        ...

    def as_dict(self) -> dict[str, Any]:
        """Serialize contract for replay_hash."""
        ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_contract.py -v`
Expected: PASS

- [ ] **Step 5: Update EmailContract to include new parameters**

```python
# paxman/capabilities/Email/contract.py

"""Email contract for Email capability."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmailContract:
    """User-facing contract for Email capability."""

    capability_name: str = field(default="email", init=False)
    include_obfuscated: bool = False
    include_localhost: bool = True
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    year: int | None = None
    output_format: str | None = None
    two_digit_base_year: int | None = None

    @property
    def active_grammars(self) -> list[str]:
        grammar_rules: dict[str, bool] = {
            "standard_recognition": True,
            "obfuscated_recognition": self.include_obfuscated,
            "localhost_recognition": self.include_localhost,
        }
        return [name for name, active in grammar_rules.items() if active]

    def as_dict(self) -> dict[str, object]:
        return {
            "capability_name": self.capability_name,
            "include_obfuscated": self.include_obfuscated,
            "include_localhost": self.include_localhost,
            "excluded_rules": self.excluded_rules,
            "year": self.year,
            "output_format": self.output_format,
            "two_digit_base_year": self.two_digit_base_year,
        }
```

- [ ] **Step 6: Update EmailCapability.create_contract() signature**

```python
# paxman/capabilities/Email/capability.py - update create_contract()

@staticmethod
def create_contract(
    include_obfuscated: bool = False,
    include_localhost: bool = True,
    excluded_rules: Sequence[str] | None = None,
    year: int | None = None,
    output_format: str | None = None,
    two_digit_base_year: int | None = None,
) -> EmailContract:
    """Create an EmailContract with the given configuration."""
    return EmailContract(
        include_obfuscated=include_obfuscated,
        include_localhost=include_localhost,
        excluded_rules=tuple(excluded_rules) if excluded_rules else (),
        year=year,
        output_format=output_format,
        two_digit_base_year=two_digit_base_year,
    )
```

- [ ] **Step 7: Run all tests to verify no regressions**

Run: `uv run pytest tests/ -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add paxman/core/contract.py paxman/capabilities/Email/contract.py paxman/capabilities/Email/capability.py tests/unit/test_contract.py
git commit -m "feat: add output_format and two_digit_base_year to Contract protocol"
```

---

## Task 2: Update Rule Interface to Accept Contract

**Files:**
- Modify: `paxman/core/domain.py:120-141`
- Modify: `paxman/engine/orchestrator.py:114-138`
- Modify: `paxman/capabilities/Email/rules/rfc_5322_ed2008.py:28-43`
- Modify: `paxman/capabilities/Email/rules/rfc_6761_ed2012.py:23-40`
- Test: `tests/unit/test_domain.py`

- [ ] **Step 1: Write failing tests for Rule interface change**

```python
# tests/unit/test_domain.py - add these tests

def test_rule_matches_accepts_contract():
    """Rule.matches() accepts notation and contract parameters."""
    from paxman.capabilities.Email.notation import EmailNotation
    from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec
    from paxman.capabilities.Email.contract import EmailContract

    rule = Section341AddrSpec()
    notation = EmailNotation(local_part="user", domain_part="example.com")
    contract = EmailContract()
    assert rule.matches(notation, contract) is True


def test_rule_normalize_accepts_contract():
    """Rule.normalize() accepts notation and contract parameters."""
    from paxman.capabilities.Email.notation import EmailNotation
    from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec
    from paxman.capabilities.Email.contract import EmailContract

    rule = Section341AddrSpec()
    notation = EmailNotation(local_part="USER", domain_part="EXAMPLE.COM")
    contract = EmailContract()
    assert rule.normalize(notation, contract) == "user@example.com"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_domain.py -v`
Expected: FAIL with "matches() takes 2 positional arguments but 3 were given"

- [ ] **Step 3: Update Rule ABC to accept contract parameter**

```python
# paxman/core/domain.py - update Rule class

class Rule(ABC, Generic[NotationT]):
    """Base class for validation rules."""

    name: str
    strategy: RuleStrategy
    provenance: Provenance
    citation: str

    @abstractmethod
    def matches(self, notation: NotationT, contract: Contract) -> bool: ...

    @abstractmethod
    def normalize(self, notation: NotationT, contract: Contract) -> str: ...
```

- [ ] **Step 4: Update Email rules to accept contract parameter**

```python
# paxman/capabilities/Email/rules/rfc_5322_ed2008.py

class Section341AddrSpec(Rule[EmailNotation]):
    """RFC 5322 Section 3.4.1 — addr-spec."""

    name = "Section 3.4.1-addr-spec"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "Section 3.4.1 (addr-spec)"

    def matches(self, notation: EmailNotation, contract: Contract) -> bool:
        return bool(
            _LOCAL_PATTERN.match(notation.local_part)
            and _DOMAIN_PATTERN.match(notation.domain_part)
        )

    def normalize(self, notation: EmailNotation, contract: Contract) -> str:
        return f"{notation.local_part.lower()}@{notation.domain_part.lower()}"
```

```python
# paxman/capabilities/Email/rules/rfc_6761_ed2012.py

class Section63localhost(Rule[EmailNotation]):
    """RFC 6761 Section 6.3 — localhost."""

    name = "Section 6.3-localhost"
    strategy = RuleStrategy.REGEX
    provenance = PUBLICATION
    citation = "Section 6.3 (localhost)"

    def matches(self, notation: EmailNotation, contract: Contract) -> bool:
        return notation.domain_part == "localhost"

    def normalize(self, notation: EmailNotation, contract: Contract) -> str:
        return f"{notation.local_part}@localhost"
```

- [ ] **Step 5: Update engine to pass contract to rules**

```python
# paxman/engine/orchestrator.py - update _collect_candidates()

def _collect_candidates(
    recognitions: list[RecognizedRep[Any]], rules: list[Rule[Any]]
) -> list[Candidate]:
    """Match recognitions against rules and collect candidates."""
    candidates: list[Candidate] = []
    for recognition in recognitions:
        for rule in rules:
            try:
                if rule.matches(recognition.notation, recognition.contract):
                    canonical = rule.normalize(recognition.notation, recognition.contract)
                    candidates.append(
                        Candidate(
                            value=canonical,
                            recognition_rule=recognition.grammar.grammar_name,
                            validation_rule=rule.name,
                            provenance=(rule.provenance,),
                        )
                    )
            except Exception as exc:
                raise ValidationError(
                    rule=rule.name,
                    message=f"Validation failed: {exc}",
                    original_error=exc,
                ) from exc
    return candidates
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_domain.py -v`
Expected: PASS

- [ ] **Step 7: Run all tests to verify no regressions**

Run: `uv run pytest tests/ -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add paxman/core/domain.py paxman/engine/orchestrator.py paxman/capabilities/Email/rules/rfc_5322_ed2008.py paxman/capabilities/Email/rules/rfc_6761_ed2012.py tests/unit/test_domain.py
git commit -m "feat: update Rule interface to accept contract parameter"
```

---

## Task 3: Implement Date Capability

**Files:**
- Create: `paxman/capabilities/Date/__init__.py`
- Create: `paxman/capabilities/Date/capability.py`
- Create: `paxman/capabilities/Date/notation.py`
- Create: `paxman/capabilities/Date/grammar/__init__.py`
- Create: `paxman/capabilities/Date/grammar/iso8601_recognition.py`
- Create: `paxman/capabilities/Date/grammar/us_recognition.py`
- Create: `paxman/capabilities/Date/grammar/european_recognition.py`
- Create: `paxman/capabilities/Date/rules/__init__.py`
- Create: `paxman/capabilities/Date/rules/iso_8601_ed2019.py`
- Create: `paxman/capabilities/Date/rules/us_federal_rules_ed2023.py`
- Modify: `paxman/capabilities/__init__.py`
- Test: `tests/capabilities/date/test_grammar.py`
- Test: `tests/capabilities/date/test_rules.py`
- Test: `tests/capabilities/date/test_capability.py`

- [ ] **Step 1: Create DateNotation**

```python
# paxman/capabilities/Date/notation.py

"""Date notation — intermediate representation for date values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DateNotation:
    """Date notation with day, month, and year components."""

    day: str
    month: str
    year: str

    def as_list(self) -> list[str]:
        """Convert to list[str] for generic Rule interface."""
        return [self.day, self.month, self.year]
```

- [ ] **Step 2: Create ISO 8601 grammar**

```python
# paxman/capabilities/Date/grammar/iso8601_recognition.py

"""ISO 8601 date grammar — recognizes YYYY-MM-DD format."""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar

_ISO8601_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


class ISO8601DateGrammar(Grammar[DateNotation]):
    """ISO 8601 date recognition: YYYY-MM-DD."""

    name = "iso8601_recognition"

    def recognize(self, text: str) -> list[DateNotation]:
        """Extract ISO 8601 date patterns from text."""
        matches = _ISO8601_PATTERN.findall(text)
        return [
            DateNotation(day=day, month=month, year=year)
            for year, month, day in matches
        ]
```

- [ ] **Step 3: Create US date grammar**

```python
# paxman/capabilities/Date/grammar/us_recognition.py

"""US date grammar — recognizes MM/DD/YYYY format."""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar

_US_DATE_PATTERN = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


class USDateGrammar(Grammar[DateNotation]):
    """US date recognition: MM/DD/YYYY."""

    name = "us_recognition"

    def recognize(self, text: str) -> list[DateNotation]:
        """Extract US date patterns from text."""
        matches = _US_DATE_PATTERN.findall(text)
        return [
            DateNotation(day=day, month=month, year=year)
            for month, day, year in matches
        ]
```

- [ ] **Step 4: Create European date grammar**

```python
# paxman/capabilities/Date/grammar/european_recognition.py

"""European date grammar — recognizes DD/MM/YYYY format."""

from __future__ import annotations

import re

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar

_EUROPEAN_DATE_PATTERN = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")


class EuropeanDateGrammar(Grammar[DateNotation]):
    """European date recognition: DD.MM.YYYY."""

    name = "european_recognition"

    def recognize(self, text: str) -> list[DateNotation]:
        """Extract European date patterns from text."""
        matches = _EUROPEAN_DATE_PATTERN.findall(text)
        return [
            DateNotation(day=day, month=month, year=year)
            for day, month, year in matches
        ]
```

- [ ] **Step 5: Create ISO 8601 rule**

```python
# paxman/capabilities/Date/rules/iso_8601_ed2019.py

"""ISO 8601 date rule — validates and normalizes dates to ISO format."""

from __future__ import annotations

from datetime import datetime

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISO",
    specification_name="ISO 8601",
    kind="specification",
    reference_url="https://www.iso.org/standard/70907.html",
    version="2019",
    lifecycle="active",
    publication_year=2019,
)


class Section431CalendarDate(Rule[DateNotation]):
    """ISO 8601 Section 4.3.1 — Calendar date."""

    name = "Section 4.3.1-calendar-date"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 4.3.1 (calendar date)"

    def matches(self, notation: DateNotation, contract: Contract) -> bool:
        """Try to parse as ISO 8601 date."""
        try:
            day = int(notation.day)
            month = int(notation.month)
            year = int(notation.year)
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    def normalize(self, notation: DateNotation, contract: Contract) -> str:
        """Normalize to ISO 8601 format."""
        day = int(notation.day)
        month = int(notation.month)
        year = int(notation.year)
        return f"{year:04d}-{month:02d}-{day:02d}"
```

- [ ] **Step 6: Create US federal rule with two_digit_base_year support**

```python
# paxman/capabilities/Date/rules/us_federal_rules_ed2023.py

"""US federal date rule — validates and normalizes dates with two-digit year support."""

from __future__ import annotations

from datetime import datetime

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="US Federal Government",
    specification_name="Federal Rules",
    kind="policy",
    reference_url="https://www.usgs.gov/us-board-on-geographic-names",
    version="2023",
    lifecycle="active",
    publication_year=2023,
)


class Section1DateFormat(Rule[DateNotation]):
    """US federal date format — MM/DD/YYYY with two-digit year support."""

    name = "Section 1-date-format"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 1 (date format)"

    def _interpret_two_digit_year(self, year_str: str, contract: Contract) -> int:
        """Interpret two-digit year using contract's base year."""
        if len(year_str) == 2:
            base_year = contract.two_digit_base_year or 2000
            year_int = int(year_str)
            if year_int < 100:
                return base_year + year_int
        return int(year_str)

    def matches(self, notation: DateNotation, contract: Contract) -> bool:
        """Try to parse as US date with two-digit year support."""
        try:
            day = int(notation.day)
            month = int(notation.month)
            year = self._interpret_two_digit_year(notation.year, contract)
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    def normalize(self, notation: DateNotation, contract: Contract) -> str:
        """Normalize based on output_format contract parameter."""
        day = int(notation.day)
        month = int(notation.month)
        year = self._interpret_two_digit_year(notation.year, contract)

        if contract.output_format == "ISO":
            return f"{year:04d}-{month:02d}-{day:02d}"
        elif contract.output_format == "US":
            return f"{month:02d}/{day:02d}/{year:04d}"
        else:
            # Default to ISO format
            return f"{year:04d}-{month:02d}-{day:02d}"
```

- [ ] **Step 7: Create DateCapability and DateContract**

```python
# paxman/capabilities/Date/capability.py

"""Date canonicalization capability."""

from __future__ import annotations

from collections.abc import Sequence

from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.grammar.european_recognition import (
    EuropeanDateGrammar,
)
from paxman.capabilities.Date.grammar.iso8601_recognition import (
    ISO8601DateGrammar,
)
from paxman.capabilities.Date.grammar.us_recognition import USDateGrammar
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Date.rules.iso_8601_ed2019 import Section431CalendarDate
from paxman.capabilities.Date.rules.us_federal_rules_ed2023 import Section1DateFormat
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule

__all__ = ["DateCapability", "DateContract", "DateNotation"]


class DateCapability(Capability):
    """Date canonicalization capability."""

    name = "date"
    version = "1.0.0"

    def get_grammars(self) -> list[Grammar]:
        return [
            ISO8601DateGrammar(),
            USDateGrammar(),
            EuropeanDateGrammar(),
        ]

    def get_rules(self) -> list[Rule]:
        return [
            Section431CalendarDate(),
            Section1DateFormat(),
        ]

    @staticmethod
    def create_contract(
        excluded_rules: Sequence[str] | None = None,
        year: int | None = None,
        output_format: str | None = None,
        two_digit_base_year: int | None = None,
    ) -> DateContract:
        """Create a DateContract with the given configuration."""
        return DateContract(
            excluded_rules=tuple(excluded_rules) if excluded_rules else (),
            year=year,
            output_format=output_format,
            two_digit_base_year=two_digit_base_year,
        )
```

```python
# paxman/capabilities/Date/contract.py

"""Date contract for Date capability."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DateContract:
    """User-facing contract for Date capability."""

    capability_name: str = field(default="date", init=False)
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    year: int | None = None
    output_format: str | None = None
    two_digit_base_year: int | None = None

    @property
    def active_grammars(self) -> list[str]:
        return [
            "iso8601_recognition",
            "us_recognition",
            "european_recognition",
        ]

    def as_dict(self) -> dict[str, object]:
        return {
            "capability_name": self.capability_name,
            "excluded_rules": self.excluded_rules,
            "year": self.year,
            "output_format": self.output_format,
            "two_digit_base_year": self.two_digit_base_year,
        }
```

- [ ] **Step 8: Create package init files**

```python
# paxman/capabilities/Date/__init__.py

from paxman.capabilities.Date.capability import DateCapability, DateContract
from paxman.capabilities.Date.notation import DateNotation

__all__ = ["DateCapability", "DateContract", "DateNotation"]
```

```python
# paxman/capabilities/Date/grammar/__init__.py

"""Date grammars."""
```

```python
# paxman/capabilities/Date/rules/__init__.py

"""Date rules."""
```

- [ ] **Step 9: Register Date capability**

```python
# paxman/capabilities/__init__.py

"""Paxman capabilities."""

from paxman.capabilities.Date.capability import DateCapability as Date
from paxman.capabilities.Email.capability import EmailCapability as Email

__all__ = ["Date", "Email"]
```

- [ ] **Step 10: Write grammar tests**

```python
# tests/capabilities/date/test_grammar.py

"""Tests for Date grammars."""

from __future__ import annotations

import pytest

from paxman.capabilities.Date.grammar.iso8601_recognition import ISO8601DateGrammar
from paxman.capabilities.Date.grammar.us_recognition import USDateGrammar
from paxman.capabilities.Date.grammar.european_recognition import EuropeanDateGrammar


class TestISO8601DateGrammar:
    """Tests for ISO 8601 date grammar."""

    def test_recognizes_valid_input(self):
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("2026-07-26")
        assert len(result) == 1
        assert result[0].as_list() == ["26", "07", "2026"]

    def test_recognizes_multiple(self):
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("Dates: 2026-07-26 and 2025-12-31")
        assert len(result) == 2

    def test_returns_empty_for_empty_input(self):
        grammar = ISO8601DateGrammar()
        result = grammar.recognize("")
        assert result == []


class TestUSDateGrammar:
    """Tests for US date grammar."""

    def test_recognizes_valid_input(self):
        grammar = USDateGrammar()
        result = grammar.recognize("07/26/2026")
        assert len(result) == 1
        assert result[0].as_list() == ["26", "07", "2026"]

    def test_recognizes_variant_input(self):
        grammar = USDateGrammar()
        result = grammar.recognize("7/26/2026")
        assert len(result) == 1


class TestEuropeanDateGrammar:
    """Tests for European date grammar."""

    def test_recognizes_valid_input(self):
        grammar = EuropeanDateGrammar()
        result = grammar.recognize("26.07.2026")
        assert len(result) == 1
        assert result[0].as_list() == ["26", "07", "2026"]
```

- [ ] **Step 11: Write rule tests**

```python
# tests/capabilities/date/test_rules.py

"""Tests for Date rules."""

from __future__ import annotations

import pytest

from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Date.rules.iso_8601_ed2019 import Section431CalendarDate
from paxman.capabilities.Date.rules.us_federal_rules_ed2023 import Section1DateFormat


class TestSection431CalendarDate:
    """Tests for ISO 8601 calendar date rule."""

    def test_matches_valid_input(self):
        rule = Section431CalendarDate()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract()
        assert rule.matches(notation, contract) is True

    def test_rejects_invalid_input(self):
        rule = Section431CalendarDate()
        notation = DateNotation(day="32", month="13", year="2026")
        contract = DateContract()
        assert rule.matches(notation, contract) is False

    def test_normalize_produces_canonical(self):
        rule = Section431CalendarDate()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract()
        assert rule.normalize(notation, contract) == "2026-07-26"


class TestSection1DateFormat:
    """Tests for US federal date format rule."""

    def test_matches_valid_input(self):
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract()
        assert rule.matches(notation, contract) is True

    def test_two_digit_year_with_base_year(self):
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="26")
        contract = DateContract(two_digit_base_year=2000)
        assert rule.matches(notation, contract) is True
        assert rule.normalize(notation, contract) == "2026-07-26"

    def test_output_format_iso(self):
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract(output_format="ISO")
        assert rule.normalize(notation, contract) == "2026-07-26"

    def test_output_format_us(self):
        rule = Section1DateFormat()
        notation = DateNotation(day="26", month="07", year="2026")
        contract = DateContract(output_format="US")
        assert rule.normalize(notation, contract) == "07/26/2026"
```

- [ ] **Step 12: Write capability tests**

```python
# tests/capabilities/date/test_capability.py

"""Tests for Date capability."""

from __future__ import annotations

import pytest

from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.notation import DateNotation
from paxman.core.capability import Capability


class TestDateNotation:
    """Tests for DateNotation."""

    def test_creates_with_fields(self):
        notation = DateNotation(day="26", month="07", year="2026")
        assert notation.day == "26"
        assert notation.month == "07"
        assert notation.year == "2026"

    def test_is_frozen(self):
        notation = DateNotation(day="26", month="07", year="2026")
        with pytest.raises(AttributeError):
            notation.day = "01"  # type: ignore[misc]

    def test_as_list_returns_correct(self):
        notation = DateNotation(day="26", month="07", year="2026")
        assert notation.as_list() == ["26", "07", "2026"]

    def test_equality(self):
        n1 = DateNotation(day="26", month="07", year="2026")
        n2 = DateNotation(day="26", month="07", year="2026")
        assert n1 == n2

    def test_hashable(self):
        notation = DateNotation(day="26", month="07", year="2026")
        assert hash(notation) is not None


class TestDateCapability:
    """Tests for DateCapability."""

    def test_is_capability_subclass(self):
        assert issubclass(DateCapability, Capability)

    def test_name(self):
        cap = DateCapability()
        assert cap.name == "date"

    def test_version(self):
        cap = DateCapability()
        assert cap.version == "1.0.0"

    def test_get_grammars_returns_all(self):
        cap = DateCapability()
        assert len(cap.get_grammars()) == 3

    def test_get_rules_returns_all(self):
        cap = DateCapability()
        assert len(cap.get_rules()) == 2


class TestDateContract:
    """Tests for DateContract."""

    def test_defaults(self):
        contract = DateContract()
        assert contract.capability_name == "date"
        assert contract.output_format is None
        assert contract.two_digit_base_year is None

    def test_with_parameters(self):
        contract = DateContract(output_format="ISO", two_digit_base_year=2000)
        assert contract.output_format == "ISO"
        assert contract.two_digit_base_year == 2000
```

- [ ] **Step 13: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: PASS

- [ ] **Step 14: Commit**

```bash
git add paxman/capabilities/Date/ tests/capabilities/date/
git commit -m "feat: implement Date capability with output_format and two_digit_base_year"
```

---

## Task 4: Add Hypothesis Property-Based Tests

**Files:**
- Create: `tests/property/__init__.py`
- Create: `tests/property/test_domain_properties.py`
- Create: `tests/property/test_grammar_properties.py`
- Create: `tests/property/test_rule_properties.py`

- [ ] **Step 1: Create property test directory**

```bash
mkdir -p tests/property
touch tests/property/__init__.py
```

- [ ] **Step 2: Write domain object property tests**

```python
# tests/property/test_domain_properties.py

"""Hypothesis property-based tests for domain objects."""

from __future__ import annotations

from hypothesis import given, strategies as st
from paxman.core.domain import Provenance, Candidate, VersionStamp, Resolution


@given(
    authority=st.text(min_size=1, max_size=50),
    spec_name=st.text(min_size=1, max_size=100),
    kind=st.sampled_from(["specification", "registry", "policy"]),
    url=st.url(),
    version=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    lifecycle=st.sampled_from(["active", "deprecated", "superseded"]),
    year=st.integers(min_value=1900, max_value=2100),
)
def test_provenance_is_immutable(
    authority: str,
    spec_name: str,
    kind: str,
    url: str,
    version: str | None,
    lifecycle: str,
    year: int,
):
    prov = Provenance(
        authority=authority,
        specification_name=spec_name,
        kind=kind,
        reference_url=url,
        version=version,
        lifecycle=lifecycle,
        publication_year=year,
    )
    # Verify immutability
    try:
        prov.authority = "changed"  # type: ignore[misc]
        assert False, "Should have raised AttributeError"
    except AttributeError:
        pass


@given(
    value=st.text(min_size=1, max_size=100),
    recognition_rule=st.text(min_size=1, max_size=50),
    validation_rule=st.text(min_size=1, max_size=50),
)
def test_candidate_is_immutable(
    value: str,
    recognition_rule: str,
    validation_rule: str,
):
    candidate = Candidate(
        value=value,
        recognition_rule=recognition_rule,
        validation_rule=validation_rule,
        provenance=[],
    )
    # Verify immutability
    try:
        candidate.value = "changed"  # type: ignore[misc]
        assert False, "Should have raised AttributeError"
    except AttributeError:
        pass


def test_resolution_enum_values():
    """Resolution enum has exactly 4 values."""
    assert len(Resolution) == 4
    assert Resolution.MISSING.value == "missing"
    assert Resolution.INVALID.value == "invalid"
    assert Resolution.SUCCESS.value == "success"
    assert Resolution.AMBIGUOUS.value == "ambiguous"
```

- [ ] **Step 3: Write grammar property tests**

```python
# tests/property/test_grammar_properties.py

"""Hypothesis property-based tests for grammars."""

from __future__ import annotations

from hypothesis import given, strategies as st
from paxman.capabilities.Email.grammar.standard_recognition import StandardEmailGrammar


@given(
    local_part=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="._%+-"),
        min_size=1,
        max_size=64,
    ),
    domain_part=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-."),
        min_size=3,
        max_size=253,
    ),
)
def test_standard_email_grammar_returns_list(local_part: str, domain_part: str):
    """StandardEmailGrammar.recognize() always returns a list."""
    grammar = StandardEmailGrammar()
    # Ensure domain has at least one dot
    if "." not in domain_part:
        domain_part = "example.com"
    result = grammar.recognize(f"{local_part}@{domain_part}")
    assert isinstance(result, list)
```

- [ ] **Step 4: Write rule property tests**

```python
# tests/property/test_rule_properties.py

"""Hypothesis property-based tests for rules."""

from __future__ import annotations

from hypothesis import given, strategies as st
from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Date.rules.iso_8601_ed2019 import Section431CalendarDate


@given(
    day=st.integers(min_value=1, max_value=31),
    month=st.integers(min_value=1, max_value=12),
    year=st.integers(min_value=1900, max_value=2100),
)
def test_iso8601_rule_matches_valid_dates(day: int, month: int, year: int):
    """ISO 8601 rule matches valid dates."""
    rule = Section431CalendarDate()
    notation = DateNotation(
        day=str(day),
        month=str(month),
        year=str(year),
    )
    contract = DateContract()
    # Rule should not raise exceptions
    result = rule.matches(notation, contract)
    assert isinstance(result, bool)


def test_iso8601_rule_normalize_always_returns_string():
    """ISO 8601 rule normalize() always returns a string."""
    rule = Section431CalendarDate()
    notation = DateNotation(day="26", month="07", year="2026")
    contract = DateContract()
    result = rule.normalize(notation, contract)
    assert isinstance(result, str)
```

- [ ] **Step 5: Run property tests**

Run: `uv run pytest tests/property/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/property/
git commit -m "test: add Hypothesis property-based tests"
```

---

## Task 5: Reorganize Test Files

**Files:**
- Create: `tests/unit/test_provenance.py`
- Create: `tests/unit/test_candidate.py`
- Create: `tests/unit/test_recognized_rep.py`
- Create: `tests/unit/test_version_stamp.py`
- Create: `tests/unit/test_resolution.py`
- Modify: `tests/unit/test_domain.py` (remove, content moved to above files)

- [ ] **Step 1: Create test_provenance.py**

```python
# tests/unit/test_provenance.py

"""Tests for Provenance dataclass."""

from __future__ import annotations

import pytest

from paxman.core.domain import Provenance


class TestProvenance:
    """Tests for Provenance."""

    def test_creates_with_fields(self):
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        assert prov.authority == "IETF"
        assert prov.specification_name == "RFC 5322"
        assert prov.kind == "specification"
        assert prov.reference_url == "https://tools.ietf.org/html/rfc5322"
        assert prov.version == "2008"
        assert prov.lifecycle == "active"
        assert prov.publication_year == 2008

    def test_is_frozen(self):
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
            prov.authority = "ISO"  # type: ignore[misc]

    def test_equality(self):
        p1 = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        p2 = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        assert p1 == p2

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
```

- [ ] **Step 2: Create test_candidate.py**

```python
# tests/unit/test_candidate.py

"""Tests for Candidate dataclass."""

from __future__ import annotations

import pytest

from paxman.core.domain import Candidate, Provenance


class TestCandidate:
    """Tests for Candidate."""

    def test_creates_with_fields(self):
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        candidate = Candidate(
            value="user@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        assert candidate.value == "user@example.com"
        assert candidate.recognition_rule == "standard_recognition"
        assert candidate.validation_rule == "Section 3.4.1-addr-spec"
        assert len(candidate.provenance) == 1

    def test_is_frozen(self):
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        candidate = Candidate(
            value="user@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        with pytest.raises(AttributeError):
            candidate.value = "changed"  # type: ignore[misc]

    def test_provenance_is_tuple(self):
        prov = Provenance(
            authority="IETF",
            specification_name="RFC 5322",
            kind="specification",
            reference_url="https://tools.ietf.org/html/rfc5322",
            version="2008",
            lifecycle="active",
            publication_year=2008,
        )
        candidate = Candidate(
            value="user@example.com",
            recognition_rule="standard_recognition",
            validation_rule="Section 3.4.1-addr-spec",
            provenance=[prov],
        )
        assert isinstance(candidate.provenance, tuple)
```

- [ ] **Step 3: Create test_recognized_rep.py**

```python
# tests/unit/test_recognized_rep.py

"""Tests for RecognizedRep dataclass."""

from __future__ import annotations

import pytest

from paxman.capabilities.Email.contract import EmailContract
from paxman.capabilities.Email.notation import EmailNotation
from paxman.core.domain import GrammarRule, RecognizedRep


class TestRecognizedRep:
    """Tests for RecognizedRep."""

    def test_creates_with_fields(self):
        notation = EmailNotation(local_part="user", domain_part="example.com")
        contract = EmailContract()
        grammar = GrammarRule(capability_name="email", grammar_name="standard_recognition")
        rep = RecognizedRep(notation=notation, contract=contract, grammar=grammar)
        assert rep.notation == notation
        assert rep.contract == contract
        assert rep.grammar == grammar

    def test_is_frozen(self):
        notation = EmailNotation(local_part="user", domain_part="example.com")
        contract = EmailContract()
        grammar = GrammarRule(capability_name="email", grammar_name="standard_recognition")
        rep = RecognizedRep(notation=notation, contract=contract, grammar=grammar)
        with pytest.raises(AttributeError):
            rep.notation = "changed"  # type: ignore[misc]

    def test_hashable(self):
        notation = EmailNotation(local_part="user", domain_part="example.com")
        contract = EmailContract()
        grammar = GrammarRule(capability_name="email", grammar_name="standard_recognition")
        rep = RecognizedRep(notation=notation, contract=contract, grammar=grammar)
        assert hash(rep) is not None
```

- [ ] **Step 4: Create test_version_stamp.py**

```python
# tests/unit/test_version_stamp.py

"""Tests for VersionStamp dataclass."""

from __future__ import annotations

import pytest

from paxman.core.domain import VersionStamp


class TestVersionStamp:
    """Tests for VersionStamp."""

    def test_creates_with_fields(self):
        stamp = VersionStamp(paxman_version="1.0.0", replay_hash="abc123")
        assert stamp.paxman_version == "1.0.0"
        assert stamp.replay_hash == "abc123"

    def test_is_frozen(self):
        stamp = VersionStamp(paxman_version="1.0.0", replay_hash="abc123")
        with pytest.raises(AttributeError):
            stamp.paxman_version = "2.0.0"  # type: ignore[misc]

    def test_equality(self):
        s1 = VersionStamp(paxman_version="1.0.0", replay_hash="abc123")
        s2 = VersionStamp(paxman_version="1.0.0", replay_hash="abc123")
        assert s1 == s2

    def test_hashable(self):
        stamp = VersionStamp(paxman_version="1.0.0", replay_hash="abc123")
        assert hash(stamp) is not None
```

- [ ] **Step 5: Create test_resolution.py**

```python
# tests/unit/test_resolution.py

"""Tests for Resolution enum."""

from __future__ import annotations

from paxman.core.domain import Resolution


class TestResolution:
    """Tests for Resolution."""

    def test_has_four_values(self):
        assert len(Resolution) == 4

    def test_missing_value(self):
        assert Resolution.MISSING.value == "missing"

    def test_invalid_value(self):
        assert Resolution.INVALID.value == "invalid"

    def test_success_value(self):
        assert Resolution.SUCCESS.value == "success"

    def test_ambiguous_value(self):
        assert Resolution.AMBIGUOUS.value == "ambiguous"
```

- [ ] **Step 6: Update test_domain.py to import from new files**

```python
# tests/unit/test_domain.py - update to import from new modules

"""Tests for domain objects."""

from __future__ import annotations

# Re-export from new modules for backward compatibility
from tests.unit.test_provenance import TestProvenance
from tests.unit.test_candidate import TestCandidate
from tests.unit.test_recognized_rep import TestRecognizedRep
from tests.unit.test_version_stamp import TestVersionStamp
from tests.unit.test_resolution import TestResolution
```

- [ ] **Step 7: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add tests/unit/
git commit -m "refactor: reorganize test files to match documentation structure"
```

---

## Task 6: Update Documentation

**Files:**
- Modify: `CONTEXT.md`
- Modify: `ARCHITECTURE.md`

- [ ] **Step 1: Update CONTEXT.md to mark implemented items**

```markdown
### Contract
User-facing configuration object that:
- **Toggles grammars ON/OFF** (e.g., `include_obfuscated=True`)
- **Pins year** to filter validation rules by `publication_year`
- **Passes parameters** to validation rules (e.g., `output_format=ISO`, `two_digit_base_year=2000`)
- Does NOT define Notation (that's internal to Capability)
```

- [ ] **Step 2: Update ARCHITECTURE.md to document new features**

Add section about contract parameters and two-digit year interpretation.

- [ ] **Step 3: Commit**

```bash
git add CONTEXT.md ARCHITECTURE.md
git commit -m "docs: update documentation to reflect implemented features"
```

---

## Verification

After completing all tasks, run:

```bash
# Run all tests
uv run pytest tests/ -v

# Run type checking
uv run pyright --strict

# Run linting
uv run ruff check paxman/ tests/
uv run ruff format --check paxman/ tests/

# Run import boundary checks
uv run import-linter lint
```

All commands should pass with zero errors.
