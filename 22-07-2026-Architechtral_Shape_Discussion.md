# Architectural Shape Discussion - 22 July 2026

This document captures the architectural decisions made during today's discussion about Paxman's redesigned shape. The previous architecture was deleted due to over-complication; this represents the new, slimmer direction.

---

## Key Decisions

### 1. Capability is Ownership Declaration

The Capability Protocol declares what it owns, not how it works:

```python
class Capability(Protocol):
    contracts: type[Contract]        # What contract types it accepts
    grammars: tuple[Grammar, ...]    # Recognition patterns
    validator: Validator             # Validation + evidence capture
    canonicalizer: Canonicalizer     # Output formatting + agreement check
```

**Decision:** Capability exposes grammars, validator, canonicalizer as owned components. Business logic lives inside these components, not at the Protocol level.

### 2. Contract is the Caller Interface

Each capability defines its own contract type extending a base Protocol:

```python
class Contract(Protocol):
    """Base interface. Controls validation and output format."""
    ...

class DateContract(Contract):
    format: str = "ISO"           # "ISO" | "US" | "EU" | "UNIX_TIMESTAMP"
    pin_spec: str | None = None
    exclude_spec: str | None = None
    pin_year: str | None = None
```

**API:**
```python
paxman.canonicalize("01/02/2026", DateContract(format="US"))
paxman.canonicalize("input", EmailContract(include_obfuscated=False))
```

**Decision:** Contract flows outward - affects BOTH validation criteria AND output format. Contract does NOT touch the input itself.

**Contract affects Validation:**
- `pin_year` determines which specs/citations are active
- Example: CountryCapability with `pin_year=1981` → "Russia Federation" Invalid (was Soviet Union)
- Example: CountryCapability with `pin_year=2000` → "Russia Federation" Valid, "Soviet Union" Invalid

### 3. ExecutionResult is the End Product

Four statuses, not two:

```python
class Resolution(StrEnum):
    SUCCESS = "SUCCESS"      # Single canonical value determined
    AMBIGUOUS = "AMBIGUOUS"  # Multiple valid canonical values exist
    INVALID = "INVALID"      # Input does not match spec shape
    MISSING = "MISSING"      # No capability claims this contract type
```

```python
@dataclass(frozen=True)
class ExecutionResult:
    status: Resolution
    contract: Contract
    canonical_value: str | None = None                 # SUCCESS only (copy of candidates[0].canonical_value)
    candidates: tuple[Candidate, ...]                  # SUCCESS: 1, AMBIGUOUS: 2+, INVALID/MISSING: empty
```

**Decision:** All statuses use the same shape — candidates count determines meaning:
- SUCCESS: `len(candidates) == 1` → `canonical_value` is set, `candidates[0].canonical_value` is the canonical form
- AMBIGUOUS: `len(candidates) >= 2` → multiple valid canonical forms
- INVALID: `len(candidates) == 0` → input doesn't match any spec
- MISSING: `len(candidates) == 0` → no capability claims this contract type

Provenance lives inside each Candidate, accessed via `candidates[i].provenance`.

### 4. Candidates Carry Raw and Canonical Values

A Candidate carries both the raw matched value and its canonical form:

```python
@dataclass(frozen=True)
class Candidate:
    value: str              # Raw matched value (from recognition)
    canonical_value: str    # Result after canonicalization
    provenance: Provenance
```

**Example flow:**
```
Input: "01/02/26"
  → Grammar recognizes date pattern
  → Validator produces 2 candidates:
    - Candidate 1: value="01/02/26", canonical_value="2026-02-01" (DD/MM/YY interpretation)
    - Candidate 2: value="01/02/26", canonical_value="2026-01-02" (MM/DD/YY interpretation)
  → Canonicalizer checks agreement: different canonical_values → AMBIGUOUS
```

### 5. Specifications are Capability-Private

Specs live inside each capability package, not shared:

```
capabilities/
├── email/
│   ├── specs/
│   │   ├── rfc5322.py
│   │   └── rfc5321.py
├── http_status/
│   └── specs/
│       └── rfc7231.py  # Declares clauses: ["6.1", "6.2"]
├── wireless/
│   └── specs/
│       └── rfc7231.py  # Same filename, different clauses: ["5.1", "5.3"]
```

**Decision:** No shared `authorities/` or `specifications/` package. Each capability owns its specs. Duplication is acceptable because sharing is rare.

### 6. Specification Owns CitationMatchings (Validation Rules)

Specs contain CitationMatchings, not separate ValidationRules:

```python
@dataclass(frozen=True)
class Specification:
    code: str                           # "RFC 9110"
    name: str                           # "HTTP Semantic"
    authority: Authority                # IETF
    effective_context: str | None = None
    base_version: Specification | None = None
    citations: tuple[CitationMatching, ...]     # The validation rules

    @property
    def resolved_year(self) -> str:
        """Derive effective year from this spec or parent chain.
        Raises ValueError if no effective_context exists in the chain.
        """
        if self.effective_context:
            return self.effective_context
        if self.base_version:
            return self.base_version.resolved_year
        raise ValueError(
            f"Specification {self.code} has no effective_context and no base_version; "
            f"cannot determine resolved year deterministically"
        )

    def _resolve_year_with_guard(self, _visited: set[int] | None = None) -> str:
        """Internal resolver with circular reference protection.
        Raises ValueError if cycle detected or no effective_context in chain.
        """
        if _visited is None:
            _visited = set()
        obj_id = id(self)
        if obj_id in _visited:
            raise ValueError(f"Circular reference detected in Specification chain: {self.code}")
        _visited.add(obj_id)
        if self.effective_context:
            return self.effective_context
        if self.base_version:
            return self.base_version._resolve_year_with_guard(_visited)
        raise ValueError(
            f"Specification {self.code} has no effective_context and no base_version; "
            f"cannot determine resolved year deterministically"
        )

    def lifetime(self) -> tuple[str, str | None]:
        """Returns (start, end) of active period."""
        start = self.effective_context or "forever"
        end = self.base_version.effective_context if self.base_version else None
        return (start, end)
```

**CitationMatching is the validation rule:**
- Defines the part or section of a specification's content/clause/subheading that RecognizedRep's raw values will be matched against

```python
@dataclass(frozen=True)
class CitationMatching:
    section: str                        # "15", "2.2", "0" (for registries)
    title: str                          # "Status Code"
    citation_type: str                  # "native" | "referenced" | "derived"
    operation: str                      # "table_lookup" | "regex_matching"

    def match(self, raw: str) -> Candidate | None:
        """Validate input against this citation's rule."""
        ...
```

**citation_type meanings:**
- `native` — content is in the spec itself
- `referenced` — spec references another source
- `derived` — compiled from multiple parts of the spec

**Examples:**

| Capability | Spec | Section | Type | Operation |
|------------|------|---------|------|-----------|
| HttpStatusCode | RFC 9110 | 15 | derived | table_lookup |
| HttpStatusCode | IANA Registry | 0 | native | table_lookup |
| IpAddress | RFC 4291 | 2.2 | native | regex_matching |

**CitationMatching.match() does the work:**
- `table_lookup` — looks up value in a compiled table
- `regex_matching` — matches against a regex pattern

**Evidence records the CitationMatching (operation is accessed via `citation.operation`):**
```python
Evidence(
    spec=rfc9110,
    citation=citation_matching,  # section 15, derived, table_lookup
)
```

**Version chain example:**
```
RFC 2016 (1997) → RFC 2616 (1999) → RFC 7231 (2014) → RFC 9110 (2022)
```

**User pinning:**
- `pin_spec="RFC 7231"` → specific spec
- `pin_year="2020"` → finds spec active at that time
- No pin → uses latest/current

### 7. Grammar is Recognition Layer

Grammars recognize what Paxman has been taught to see:

```python
class Grammar(Protocol):
    """Recognizes input patterns. Can be contributed by users."""
    id: str
    name: str
    recognition_rules: tuple[RecognitionRule, ...]

    def recognize(self, raw: str, contract: "Contract") -> tuple[RecognizedRep, ...]:
        """Cycle through recognition rules and return matches.
        Contract is provided for format-aware recognition (e.g., date format
        hints), but Grammar does NOT consult specifications — that is the
        Validator's job.
        """
        ...

class RecognitionRule(Protocol):
    """A single recognition rule. Can use regex, parser, or custom logic."""
    id: str
    name: str

    def match(self, raw: str) -> tuple[RecognizedRep, ...]:
        """Try to match input. Returns matches if successful."""
        ...
```

**Key decisions:**
- Capability has many Grammars
- Each Grammar has many RecognitionRules
- Rules can use regex, parsers, custom logic
- If one rule fails, try next rule, then next Grammar
- **Grammar is contract-aware** — receives the contract for format hints (e.g., date format), but does NOT consult specifications — that is the Validator's job
- Grammars can be user-contributed to make Paxman smarter

**RecognizedRep carries traceability:**
```python
@dataclass(frozen=True)
class RecognizedRep:
    grammar_id: str              # Which grammar matched
    recognition_rule_id: str     # Which rule matched
    raw: str                     # The matched input
    shape: str | None            # Optional shape tag
    captures: Mapping[str, str] | None  # Regex group captures
```

### 8. Validator is Validation + Evidence Layer

Validators determine if recognized input matches specs:

```python
class Validator(Protocol):
    """Validates recognized reps against specs. Collects evidence."""
    def validate(self, rep: RecognizedRep, contract: Contract) -> tuple[Candidate, ...]: ...
```

**Key decisions:**
- Validator has Specifications, each Specification has CitationMatchings
- Each CitationMatching is a validation rule that cites a specific spec clause
- Validation can be regex, table lookup, custom logic
- Contract affects validation criteria (pin_year, pin_spec, etc.)
- Evidence accumulates from passing CitationMatchings

**Validator → CitationMatching flow:**
```
Validator.validate(rep: RecognizedRep, contract: Contract)
  → For each Specification (filtered by contract.pin_spec/pin_year):
      → For each CitationMatching in spec.citations:
          → Call citation_matching.match(rep.raw)
          → If match succeeds: collect Candidate with evidence
  → Return tuple of Candidates
```

**Evidence chain:** Capability → Specification → CitationMatching

**Pipeline separation:**
```
Grammar layer = "What is this input?" (format-aware via contract, spec-unaware)
Validation layer = "Does this match the spec?" (spec-aware, evidence-producing)
```

### 10. Canonicalizer Checks Agreement

The Canonicalizer derives canonical value for each candidate:

```python
class Canonicalizer(Protocol):
    """Derives canonical value for each candidate and checks agreement."""
    def canonicalize(self, candidates: tuple[Candidate, ...], contract: Contract) -> Resolution:
        """For each candidate, derive canonical value.
        If all candidates produce same value -> SUCCESS
        If candidates produce different values -> AMBIGUOUS
        """
        ...
```

**Agreement logic:**
- For each Candidate, derive its canonical value using the contract
- If all candidates produce the same canonical value → `SUCCESS`
- If candidates produce different values → `AMBIGUOUS`
- AMBIGUOUS returns the candidates with their evidence

**Money canonical value (example):**
```python
# Money canonical value is two-part:
@dataclass(frozen=True)
class MoneyValue:
    currency: str       # "MYR", "USD", etc.
    amount: Decimal     # 1300.50
```

### 11. Pipeline is Grammar → Validator → Canonicalizer

```
Input + Contract
    ↓
Grammar.recognize() → cycles through RecognitionRules
    ↓
RecognizedRep(s) with traceability
    ↓
Validator.validate() → cycles through ValidationRules
    ↓
Candidate(s) + Evidence
    ↓
Canonicalizer.canonicalize() → Resolution (SUCCESS/AMBIGUOUS)
    ↓
Engine seals into ExecutionResult
```

**Boundary:**
- Capability returns: Resolution + Candidates + Provenance
- Engine wraps into: ExecutionResult (adds contract, config_digest)

### 12. Engine is Stateless Referee

```python
class Engine:
    def canonicalize(self, raw: str, contract: Contract) -> ExecutionResult:
        # 1. RESOLVE: find capability for contract type
        # 2. MISSING: no capability found
        # 3. RECOGNIZE: run through grammars
        # 4. VALIDATE: check against specs, collect evidence
        #    (Contract affects which citations are active via pin_year, pin_spec, etc.)
        # 5. INVALID: no valid candidates
        # 6. CANONICALIZE: derive canonical values and check agreement
        # 7. SEAL: wrap into ExecutionResult

    def replay(self, result: ExecutionResult, contract: Contract) -> ExecutionResult:
        """Placeholder for future replay verification.
        Currently returns result unchanged.
        Reserved for: config_digest verification, determinism checks.
        """
        return result
```

**Decision:** Engine handles MISSING and INVALID directly. SUCCESS and AMBIGUOUS come from capability output.

### 13. Registry is Frozen Lookup

```python
class Registry:
    def register(self, capability: Capability) -> None:
        # Map contract types to capability

    def resolve(self, contract_type: type[Contract]) -> Capability | None:
        # Pure lookup, no scoring/ranking
```

**Decision:** Registry maps `type(contract)` → capability, not `Kind` → capability. Frozen after engine starts.

---

## What Was Removed

| Previous Concept | Reason for Removal |
|------------------|-------------------|
| `Kind` wrapper | Replaced by capability-specific contract types |
| `Verdict \| Refusal` union | Replaced by 4-status Resolution |
| Shared `authorities/` package | Specs are capability-private |
| Shared `specifications/` package | Specs are capability-private |
| `AuthorityPin` on Contract | Pinning moves to capability-specific contracts |
| `render()` on Capability | Logic lives in Grammar/Validator/Canonicalizer |

## What Was Added

| New Concept | Purpose |
|-------------|---------|
| `Grammar` Protocol | Recognition layer - user-contributed patterns |
| `RecognitionRule` Protocol | Individual matching rules (regex, parser, etc.) |
| `CitationMatching` dataclass | Validation rule within Specification (section, type, operation, match) |
| `RecognizedRep` with traceability | grammar_id + recognition_rule_id for audit trail |

---

## Open Questions

1. **Contract format options** - What formats are available per capability? (ISO, US, EU, etc.) - TBD during implementation

2. **CitationMatching.match() internals** - Where are tables stored? How does regex_matching work?

---

## Example Output Structures

See `sratch.json` for concrete examples of ExecutionResult shapes for:
- Email canonicalization (SUCCESS)
- Country name normalization (SUCCESS)
- Currency formatting (SUCCESS)
- Date parsing (AMBIGUOUS with candidates)
