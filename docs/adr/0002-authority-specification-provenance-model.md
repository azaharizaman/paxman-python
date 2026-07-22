# Authority → Specification → Provenance Model

Paxman models real-world authority through a three-layer hierarchy: Authority (publisher), Specification (what they publish), and CitationMatching (validation rules within a specification). Edition is absorbed into Specification via `effective_context` and `base_version`, forming a DAG rather than a separate class. Evidence records which specifications and citation matchings justified a transformation.

## Status

Accepted (updated: reconciled with 22 July 2026 architectural shape)

## Context

The PRD describes "Authoritative Editions" (§5.5) but the code had empty stubs. We needed to design the domain model before implementing EngineConfig and engine lookup.

The original model proposed Authority → Edition as a two-layer hierarchy. Through grill-with-docs, we discovered that Edition doesn't belong directly to Authority — it belongs to a specific Specification published by that authority. For example, W3C publishes HTML, CSS, XML — each evolving independently.

The execution_result output carries a `status` (SUCCESS, AMBIGUOUS, INVALID, MISSING), the `contract` that was asked, an optional `canonical_value` for SUCCESS, and a tuple of `Candidate` objects each carrying their own `Provenance` chain. This makes the result fully self-describing and replayable.

## Decision

### Authority

Immutable identity of a publisher. Contains `code` (machine identifier, used for deterministic lookup) and `name` (human-readable).

```python
@dataclass(frozen=True)
class Authority:
    code: str              # "ISO", "IETF", "Unicode"
    name: str              # "International Organization for Standardization"
```

### Specification

Represents both the overarching standard and specific temporal releases. Absorbs Edition via `effective_context` and `base_version`. Contains `CitationMatching` entries that define validation rules.

```python
@dataclass(frozen=True)
class Specification:
    code: str                           # "RFC 9110", "ISO 3166-1"
    name: str                           # "HTTP Semantic"
    authority: Authority                # Who published it
    effective_context: str | None = None # "2022", "2024a" — when this spec became active
    base_version: "Specification | None" = None  # Parent spec for version chains (DAG)
    citations: tuple["CitationMatching", ...] = ()  # Validation rules (sections/clauses)

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
```

### CitationMatching

A section/clause within a specification that defines a validation rule. Contains `match()` implementing the actual matching logic (e.g., `table_lookup`, `regex_matching`). This is the bridge between spec data and validation behavior.

```python
@dataclass(frozen=True)
class CitationMatching:
    section: str                        # "15", "2.2", "0" (for registries)
    title: str                          # "Status Code"
    citation_type: str                  # "native" | "referenced" | "derived"
    operation: str                      # "table_lookup" | "regex_matching"

    def match(self, raw: str) -> "Candidate | None":
        """Validate input against this citation's rule.
        Returns Candidate if valid, None otherwise.
        """
        ...
```

### Evidence

Records one specification clause that justified a transformation. Carries the specification and the citation matching that was used. The `operation` is accessed via `citation.operation`.

```python
@dataclass(frozen=True)
class Evidence:
    spec: Specification                 # Which specification was applied
    citation: CitationMatching          # Which citation matching produced this result
```

### Provenance

Collection of all evidence that justified the canonicalization of a single candidate.

```python
@dataclass(frozen=True)
class Provenance:
    evidence: tuple[Evidence, ...]
```

### Candidate

A valid canonical form with its supporting evidence.

```python
@dataclass(frozen=True)
class Candidate:
    value: str                          # Raw matched value (from recognition)
    canonical_value: str                # Result after canonicalization
    provenance: Provenance
```

### ExecutionResult

The self-describing, replayable record the engine seals. Immutable — carries everything needed for reconstruction.

```python
class Resolution(StrEnum):
    SUCCESS = "SUCCESS"
    AMBIGUOUS = "AMBIGUOUS"
    INVALID = "INVALID"
    MISSING = "MISSING"

@dataclass(frozen=True)
class ExecutionResult:
    status: Resolution
    contract: Contract
    canonical_value: str | None = None              # SUCCESS only
    candidates: tuple[Candidate, ...] = ()          # SUCCESS: 1, AMBIGUOUS: 2+, INVALID/MISSING: empty
```

## Considered Options

### Edition as separate class vs absorbed into Specification

**Considered:** Separate `Edition(specification, identifier)` class.

**Rejected:** Unified Specification class is cleaner because:
- Forms a uniform DAG (any node points to parent regardless of abstraction level)
- Polymorphic flexibility (same metadata for broad standard or specific release)
- Simpler serialization (flat, predictable without deep nesting)

### AuthorityPin on Contract vs Evidence-based provenance

**Considered:** `AuthorityPin(authority, edition)` on the Contract to pin which authority edition to use.

**Rejected:** AuthorityPin moved to capability-specific contract fields (e.g., `DateContract.pin_spec`). Provenance is now carried inside each `Candidate` via the Evidence chain (Capability → Specification → CitationMatching), making it more granular and auditable.

### Mutable ExecutionResult vs frozen ExecutionResult

**Considered:** Mutable `@dataclass` with `List[Dict[str, Any]]` for candidates and loose status typing.

**Rejected:** Frozen `@dataclass` with `tuple[Candidate, ...]` and `Resolution` StrEnum is safer because:
- Enforces immutability (no post-creation mutation)
- `tuple` instead of `List` — structural guarantee of frozen state
- `Resolution` StrEnum instead of raw `str` — type-safe status values
- `Candidate` dataclass instead of `Dict[str, Any]` — typed, validated structure
- Supports Invariant 3 (Replay): frozen objects serialize deterministically

### SpecificationReference as separate class vs Evidence + CitationMatching

**Considered:** `SpecificationReference(authority, spec, operation, citation)` as a standalone provenance record.

**Rejected:** The `SpecificationReference` concept is absorbed into `Evidence` + `CitationMatching`. `Evidence` carries the spec and citation matching; `operation` lives on `CitationMatching` where it belongs (it's a property of the matching rule, not the evidence). This is simpler and more auditable — you can trace exactly which citation matching produced each piece of evidence.

## Consequences

- Capabilities declare which Specification they implement, not which Authority
- Authority is a pure identity type (code + name) — no behavior, no temporal state
- Edition information is encoded in Specification via `effective_context` and `base_version` DAG
- Specifications must have `effective_context` set (directly or via base_version chain) — `datetime.now()` is forbidden (violates Determinism invariant)
- Evidence carries spec + citation matching; operation is accessed via `citation.operation`
- Provenance is a tuple of Evidence — immutable, typed, no bare lists
- ExecutionResult is frozen — no mutation after creation, supports deterministic replay
- The old `SpecificationReference`, `AuthorityPin`, and mutable `ExecutionResult` shapes are superseded by this ADR
