# How to Add a New Capability

This guide walks you through adding a new domain capability to Paxman. It is written for developers who are new to the project and assumes no prior knowledge of the internal architecture.

By the end of this guide, you will have a fully functional capability with grammars, validation rules, a contract, tests, and integration with the Paxman engine.

---

## Prerequisites

Before starting, understand these concepts:

- **Capability** — a self-contained domain module (like Email) that knows how to recognize and validate values in that domain
- **Grammar** — a recognition rule that scans raw text and extracts structured patterns
- **Validation Rule** — a semantic rule that checks extracted patterns against authoritative specifications
- **Notation** — the intermediate representation that grammars produce and rules consume
- **Contract** — a user-facing configuration object that controls which grammars and rules are active
- **Provenance** — a citation of the authoritative specification that validates a value

---

## Step 1: Plan Your Capability

Before writing code, answer these questions:

1. **What domain are you canonicalizing?** (e.g., phone numbers, URLs, postal codes)
2. **What authoritative specifications govern this domain?** (e.g., RFCs, ISO standards, government registries)
3. **What are the different ways users might write this value?** (e.g., "555-1234", "+1 555 1234", "(555) 123-4567")
4. **What is the canonical output format?** (e.g., E.164 for phone numbers)
5. **What is the intermediate representation?** (e.g., country code, area code, local number)

Document your answers. You will reference them when writing grammars and rules.

---

## Step 2: Create the Directory Structure

Create the following directory structure. Replace `YourDomain` with your capability name (use PascalCase):

```
paxman/capabilities/YourDomain/
├── __init__.py
├── capability.py
├── notation.py
├── grammar/
│   ├── __init__.py
│   └── your_grammar.py
└── rules/
    ├── __init__.py
    └── your_rule.py
```

Also create the test directory:

```
tests/capabilities/yourdomain/
├── __init__.py
├── test_grammar.py
├── test_rules.py
└── test_capability.py
```

Use lowercase for the test directory name.

---

## Step 3: Define the Notation

The Notation is your domain's intermediate representation. It is a frozen dataclass with named fields that represent the components of the value you are canonicalizing.

Create `paxman/capabilities/YourDomain/notation.py`:

1. Import `dataclass` and `frozen` from `dataclasses`
2. Define a frozen dataclass with one field per component of your notation
3. Add an `as_list()` method that returns the fields as a plain list of strings (in order)

The `as_list()` method bridges your typed notation to the generic `list[str]` interface that the engine expects. Grammars will call this method when returning notations.

**Rules for Notation:**

- Every field must be a `str` type
- The dataclass must be frozen (immutable)
- The `as_list()` method must return fields in a consistent, documented order
- Field order matters — rules will access values by position using the list form

**Example patterns:**

- Email: `local_part` + `domain_part` (2 fields)
- Phone number: `country_code` + `area_code` + `local_number` (3 fields)

---

## Step 4: Create a Grammar

Grammars are recognition rules that scan raw text and extract notations. Each grammar handles one specific pattern or format.

Create `paxman/capabilities/YourDomain/grammar/your_grammar.py`:

1. Import `Grammar` from `paxman.core.domain`
2. Import your `YourDomainNotation` from the notation module
3. Define a class that extends `Grammar`
4. Set the `name` class attribute to a snake_case identifier (this name is used by the contract to toggle grammars)
5. Implement the `recognize(text: str) -> list[list[str]]` method

**The `recognize` method must:**

- Accept a single string parameter (the raw input text)
- Return a list of notations (each notation is a list of strings, produced by calling `YourDomainNotation(...).as_list()`)
- Return an empty list if nothing matches
- Never raise exceptions for normal input (use try/except for regex or parsing errors)
- Handle edge cases gracefully (empty strings, partial matches, Unicode)

**Grammar design principles:**

- Each grammar should handle exactly one pattern variant
- Grammars do NOT validate — they only extract
- A single grammar can return multiple notations if the input contains multiple matches
- Grammar names must be unique within the capability

**Common grammar strategies:**

- **Regex** — use compiled regex patterns with `re.findall()` or `re.finditer()`
- **String parsing** — split or scan text for delimiters
- **Hybrid** — combine regex with string operations for complex patterns

---

## Step 5: Create Validation Rules

Validation rules check notations against authoritative specifications. Each rule belongs to one specific publication (e.g., one RFC, one ISO standard).

Create `paxman/capabilities/YourDomain/rules/your_rule.py`:

### 5a: Define the Provenance

At the top of the file, define a module-level `PUBLICATION` constant. This is the provenance for all rules in this file:

- `authority` — the organization that published the spec (e.g., "IETF", "ISO", "W3C")
- `specification_name` — the name and section of the spec (e.g., "RFC 5322 Section 3.4.1")
- `kind` — one of "specification", "registry", or "policy"
- `reference_url` — a URL to the authoritative document
- `version` — the version string (e.g., "2008") or `None` if unversioned
- `lifecycle` — one of "active", "deprecated", or "superseded"
- `publication_year` — the year this specification came into effect (integer)

### 5b: Define the Rule Class

Create a class that extends `Rule`:

1. Set `name` to a snake_case identifier following the pattern `section_number-description` (e.g., `section_3_4_1_addr_spec`)
2. Set `strategy` to the appropriate `RuleStrategy` enum value:
   - `REGEX` — for pattern matching rules
   - `LOOKUP_TABLE` — for table-based validation (e.g., status codes, country codes)
   - `PARSER` — for rules that parse and validate structured input
3. Set `provenance` to the `PUBLICATION` constant defined above
4. Set `citation` to a human-readable citation (e.g., "Section 3.4.1 (addr-spec)")

### 5c: Implement the `matches` method

The `matches` method checks whether a notation is valid according to this rule:

```python
def matches(self, notation: list[str]) -> bool:
```

- Accept a list of strings (the notation)
- Return `True` if the notation is valid according to the specification
- Return `False` if it is not valid
- Never raise exceptions — return `False` for any invalid input
- Access notation fields by position (e.g., `notation[0]` for the first field)

**For regex rules:** Compile the regex once at module level, then use it in `matches`.

**For lookup table rules:** Define a module-level dictionary mapping valid values to canonical forms.

**For parser rules:** Attempt to parse the notation and return `True` if parsing succeeds without errors.

### 5d: Implement the `normalize` method

The `normalize` method converts a valid notation into its canonical string form:

```python
def normalize(self, notation: list[str]) -> str:
```

- Accept a list of strings (the notation)
- Return the canonical string representation
- Only called after `matches` returns `True` (you can assume the notation is valid)
- Apply normalization rules from the specification (e.g., lowercase, remove whitespace, pad with zeros)

---

## Step 6: Create the Capability Class

The Capability class is the entry point that the engine uses to discover your grammars and rules.

Create `paxman/capabilities/YourDomain/capability.py`:

1. Import `Capability` from `paxman.core.capability`
2. Import your grammars and rules
3. Define a class that extends `Capability`
4. Set `name` to a lowercase identifier (e.g., "yourdomain") — this is the name users pass to the contract
5. Set `version` to a semantic version string (e.g., "1.0.0")
6. Implement `get_grammars()` — return a list of grammar instances
7. Implement `get_rules()` — return a list of rule instances
8. Define a `create_contract()` static method that returns a default contract

---

## Step 7: Create the Contract Class

The Contract is a user-facing configuration object that controls which grammars and rules are active.

Define the Contract in `paxman/capabilities/YourDomain/capability.py` (same file as the Capability class):

1. Import `dataclass` and `frozen` from `dataclasses`
2. Define a frozen dataclass that will serve as the contract
3. Add a `capability_name` field with `default="yourdomain"` and `init=False` (users never set this)
4. Add configuration fields for toggling grammars (e.g., `include_obfuscated: bool = False`)
5. Add `excluded_rules: tuple[str, ...] = ()` for excluding specific rules
6. Add `year: int | None = None` for temporal filtering
7. Implement `active_grammars` as a `@property` that builds the grammar list from configuration flags
8. Implement `as_dict()` that returns a dictionary representation (used for replay hash computation)

**The Contract must satisfy the `Contract` protocol:**

- `capability_name: str` — the capability this contract configures
- `active_grammars: Sequence[str]` — list of grammar names to activate
- `excluded_rules: Sequence[str]` — list of rule names to exclude
- `year: int | None` — year for temporal filtering
- `as_dict() -> dict[str, Any]` — serialization for replay hash

---

## Step 8: Create Package Init Files

### Capability package init

Create `paxman/capabilities/YourDomain/__init__.py`:

Export the Capability class, Contract class, and Notation type:

```python
from paxman.capabilities.YourDomain.capability import YourDomainCapability, YourDomainContract
from paxman.capabilities.YourDomain.notation import YourDomainNotation

__all__ = ["YourDomainCapability", "YourDomainContract", "YourDomainNotation"]
```

### Grammar and Rules package inits

Create `paxman/capabilities/YourDomain/grammar/__init__.py` and `paxman/capabilities/YourDomain/rules/__init__.py`:

These can be empty files (just a docstring or `pass`). They exist to make the directories proper Python packages.

### Test package inits

Create `tests/capabilities/yourdomain/__init__.py`:

This can be an empty file.

---

## Step 9: Register the Capability

The engine discovers capabilities through a registry. You must register your capability before using it.

In `paxman/capabilities/__init__.py`, add an import for your capability:

```python
from paxman.capabilities.YourDomain import YourDomainCapability as YourDomain
```

This makes your capability importable as:

```python
from paxman.capabilities import YourDomain
```

Users register the capability before first use:

```python
import paxman
from paxman.capabilities import YourDomain

paxman.register_capability(YourDomain())
```

---

## Step 10: Write Tests

Tests are organized into four layers. You must write tests for all layers.

### 10a: Grammar Tests

Create `tests/capabilities/yourdomain/test_grammar.py`:

For each grammar class, create a test class with these test methods:

1. `test_recognizes_valid_input` — happy path, grammar finds the expected pattern
2. `test_recognizes_variant_input` — edge cases (different delimiters, whitespace, case)
3. `test_recognizes_multiple` — input contains multiple matches
4. `test_ignores_incompatible_format` — grammar does not match patterns it should not handle
5. `test_returns_empty_for_empty_input` — empty string returns empty list

**Test pattern:**

- Instantiate the grammar directly (no fixtures needed)
- Call `grammar.recognize(text)`
- Assert the length of the result list
- Assert each result matches the expected list of strings

### 10b: Rule Tests

Create `tests/capabilities/yourdomain/test_rules.py`:

For each rule class, create a test class with these test methods:

1. `test_matches_valid_input` — happy path, notation is valid
2. `test_matches_variant_valid` — edge cases that should still be valid
3. `test_rejects_invalid_input` — notation that should not match
4. `test_normalize_produces_canonical` — verify exact canonical output
5. `test_provenance_attributes` — verify authority, spec name, year, lifecycle
6. `test_rule_name` — verify name follows convention
7. `test_strategy` — verify the rule strategy enum

**Test pattern:**

- Instantiate the rule directly
- Call `rule.matches(notation)` and assert `True` or `False`
- Call `rule.normalize(notation)` and assert exact string output
- Access `rule.provenance.*` fields and assert expected values

### 10c: Capability Tests

Create `tests/capabilities/yourdomain/test_capability.py`:

Two sections in one file:

**Notation tests:**

1. `test_creates_with_fields` — verify field access
2. `test_is_frozen` — verify immutability (assigning raises error)
3. `test_as_list_returns_correct` — verify list conversion
4. `test_as_list_preserves_order` — verify field order matches list order
5. `test_equality` — verify value equality
6. `test_hashable` — verify it can be used in sets or as dict keys

**Capability wiring tests:**

1. `test_is_capability_subclass` — verify isinstance check
2. `test_name` — verify name matches expected value
3. `test_version` — verify version matches expected value
4. `test_get_grammars_returns_all` — verify grammar count
5. `test_get_rules_returns_all` — verify rule count
6. `test_grammar_name` — verify grammar names follow convention
7. `test_rule_name` — verify rule names follow convention

### 10d: Integration Tests

Create or extend `tests/integration/test_pipeline.py`:

Add tests that exercise the full pipeline through `run_capability()`:

1. `test_success` — recognized and validated, single canonical value
2. `test_missing` — nothing recognized
3. `test_invalid` — recognized but not validated
4. `test_ambiguity` — multiple conflicting canonical values
5. `test_version_stamp` — verify replay hash is present and deterministic

**Critical:** All integration tests must use the `_clean_registry` autouse fixture:

```python
@pytest.fixture(autouse=True)
def _clean_registry():
    reset_registry()
    yield
    reset_registry()
```

### 10e: End-to-End Tests

Create or extend `tests/e2e/test_canonicalize.py`:

Test through the public API (`paxman.api.canonicalize`):

1. `test_canonicalize_success` — full happy path
2. `test_canonicalize_missing` — no match
3. `test_canonicalize_with_options` — contract configuration

---

## Step 11: Verify Quality Gates

Before considering your capability complete, verify all quality gates pass:

### Type Checking

```bash
uv run pyright --strict
```

Must pass with zero errors. No `# type: ignore` or `# noqa` comments are allowed.

### Linting and Formatting

```bash
uv run ruff check paxman/ tests/
uv run ruff format --check paxman/ tests/
```

Must pass with zero errors.

### Import Boundaries

```bash
uv run import-linter
```

Must pass. Your capability must not import from other capabilities. It may only import from `paxman.core`.

### Tests

```bash
uv run pytest tests/ -v
```

All tests must pass. No skipped tests without explicit justification.

---

## Step 12: Common Patterns and Pitfalls

### Pattern: One Provenance Per File

Each rule file defines a single `PUBLICATION` constant at module level. If you have multiple rules from the same specification, they share that provenance. If rules come from different specifications, put them in separate files.

### Pattern: Grammar Names Are Identifiers

Grammar names are snake_case strings used by the contract to toggle grammars. They must be unique within the capability. Follow the pattern `{format}_recognition` (e.g., `standard_recognition`, `obfuscated_recognition`).

### Pattern: Rule Names Follow Section Convention

Rule names follow the pattern `section_{number}_{description}` (e.g., `section_3_4_1_addr_spec`). This makes it easy to map rules back to the specification.

### Pattern: Notation Fields Are Positional

Rules access notation fields by position (index 0, 1, 2...). Your `as_list()` method must return fields in a consistent order, and your rules must access them at the correct indices.

### Pitfall: Grammar Regex Must Be Compiled Once

Compile regex patterns at module level, not inside the `recognize` method. Recompiling on every call is wasteful and can cause subtle bugs with cached groups.

### Pitfall: Rules Must Not Raise Exceptions

The `matches` method must return `False` for any invalid input, never raise. The `normalize` method is only called after `matches` returns `True`, but it should still handle edge cases defensively.

### Pitfall: Contract Fields Must Have Defaults

Users should be able to construct a contract with zero arguments: `YourDomainContract()`. All fields except `capability_name` must have sensible defaults.

### Pitfall: Import Boundaries Are Enforced

Your capability cannot import from `paxman.capabilities.OtherCapability`. If you need shared utilities, they belong in `paxman.core` or a separate shared module.

---

## Checklist

Use this checklist to verify your capability is complete:

- [ ] Notation is a frozen dataclass with `as_list()` method
- [ ] Each grammar extends `Grammar` and implements `recognize(text) -> list[list[str]]`
- [ ] Each rule extends `Rule` and implements `matches(notation) -> bool` and `normalize(notation) -> str`
- [ ] Each rule file has a `PUBLICATION` provenance constant
- [ ] Capability extends `Capability` and implements `get_grammars()` and `get_rules()`
- [ ] Contract is a frozen dataclass satisfying the `Contract` protocol
- [ ] Package `__init__.py` files export the public API
- [ ] Capability is registered in `paxman/capabilities/__init__.py`
- [ ] Grammar tests cover happy path, edge cases, multiple matches, and empty input
- [ ] Rule tests cover valid input, invalid input, normalization, provenance, and naming
- [ ] Notation tests cover creation, immutability, list conversion, and equality
- [ ] Capability tests cover subclass check, name, version, grammar count, and rule count
- [ ] Integration tests use the `_clean_registry` fixture
- [ ] End-to-end tests exercise the public API
- [ ] `pyright --strict` passes with zero errors
- [ ] `ruff check` passes with zero errors
- [ ] `ruff format --check` passes with zero errors
- [ ] `import-linter` passes
- [ ] All tests pass with `uv run pytest`
