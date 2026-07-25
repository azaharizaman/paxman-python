# ADR-0001: Clean Architecture Pipeline for Paxman

## Status

Accepted

## Context

Paxman is a canonicalization authority resolver that needs to:
1. Recognize values from ambiguous human input
2. Validate against authoritative specifications
3. Report provenance for all canonical values
4. Handle temporal constraints (publication_year filtering)
5. Support extensible capabilities (community-driven)

The original design had tightly coupled layers where the Resolver needed direct access to Provenance to determine validity. This created a maintenance nightmare as the library grows.

## Decision

Adopt a **Domain-Centric Pipeline** model with clean separation between Recognition and Validation layers:

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONTRACT (Application Edge)                          │
│   Email(include_obfuscated=True, year=2007)                                 │
│   • Toggles grammars ON/OFF                                                 │
│   • Pins year for temporal filtering                                         │
│   • Passes parameters to validation rules                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAPABILITY (Domain Core)                            │
│   paxman/capabilities/Email/capability.py                                   │
│   • Defines Notation (e.g., [local_part, domain_part])                      │
│   • Registers default grammars (always on)                                  │
│   • Registers default validation rules                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RECOGNITION (Domain Service)                        │
│   paxman/capabilities/Email/grammar/*.py                                    │
│   • Syntactic extraction (regex patterns)                                   │
│   • Produces Notation (capability-defined shape)                            │
│   • Contract-aware (knows which grammars are active)                        │
│   • Does NOT validate — only recognize                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VALIDATION (Domain Service)                         │
│   paxman/capabilities/Email/rules/*.py                                      │
│   • Semantic rules backed by provenance                                     │
│   • Accepts Notation (not raw input)                                        │
│   • Uses contract parameters (e.g., two_digit_base_year)                    │
│   • Filters by publication_year ≤ contract.year                             │
│   • Produces Candidate with canonical value + provenance                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION RESULT (Output)                           │
│   status, canonicalized_value, candidates, contract, version_stamp          │
│   • MISSING: no RecognizedReps                                              │
│   • INVALID: recognized but no provenance validates                         │
│   • SUCCESS: single canonical value (1+ candidates with same value)         │
│   • AMBIGUOUS: multiple conflicting canonical values                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Code
    │
    ▼
paxman.canonicalize("input", Email(...))
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ENGINE                                   │
│  1. Lookup capability (Email)                                    │
│  2. Get active grammars (from contract)                          │
│  3. Run grammars → RecognizedReps                                │
│  4. Get active rules (filtered by year)                          │
│  5. Run rules → Candidates                                       │
│  6. Determine Resolution status                                  │
│  7. Build ExecutionResult                                        │
│  8. Compute replay_hash                                          │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
ExecutionResult
```

### Key Design Decisions

1. **Separate Recognition from Validation**
   - Recognition = syntactic (regex patterns, contributor-friendly)
   - Validation = semantic (provenance-backed, standards-bound)
   - Benefit: Contributors can add recognition rules without understanding validation logic

2. **Notation as Internal Contract**
   - Each capability defines its own Notation type
   - All grammars for that capability must produce this Notation
   - Benefit: Stable interface between Recognition and Validation

3. **Provenance Decentralized into Rules**
   - Each validation rule carries its own Provenance
   - No global provenance registry needed
   - Benefit: Zero lookups, provenance rides with the data

4. **Temporal Filtering via Publication Year**
   - Contract.year filters validation rules by publication_year
   - Rules with publication_year > contract.year are inactive
   - Benefit: Same input can have different results for different time periods

5. **Exhaustive Recognition**
   - Input passes through ALL active grammars
   - Multiple RecognizedReps can be produced
   - Benefit: Surfaces all possible interpretations for ambiguity detection

6. **Replay Hash for Determinism**
   - SHA-256 of canonical bytes ensures byte-for-byte reproducibility
   - Includes provenance in hash to break on edition changes
   - Benefit: Auditability and reproducibility

7. **Resolution Enum for Status**
   - Use `Resolution` enum instead of string for status
   - INVALID and AMBIGUOUS are output states, not exceptions
   - Benefit: Type-safe status handling, clear semantics

8. **Exception Hierarchy for Actual Errors**
   - `ContractError` for malformed contracts
   - `CapabilityError` for unknown capabilities or registration after freeze
   - `RecognitionError` with rule name for grammar failures
   - `ValidationError` with rule name for validation failures
   - Benefit: Explicit error handling, debuggable for contributors

9. **Capability Versioning**
   - Each capability has version in `capability.py`
   - Independent of engine version
   - Benefit: Capabilities can evolve independently

10. **Engine Versioning**
    - Engine version in `pyproject.toml`
    - Referenced in `VersionStamp.paxman_version`
    - Benefit: Clear versioning for the core library

11. **Rule-Provenance Structure**
    - One rule file = One publication (e.g., `rfc_5322_ed2008.py`)
    - One rule = One section within that publication (e.g., `Section 3.4.1-addr-spec`)
    - Clear citation: "IETF, RFC 5322, Edition 2008, Section 3.4.1"
    - Benefit: Precise provenance tracking, user can see exact source

12. **Three Validation Strategies**
    - `REGEX` — Pattern matching for text validation
    - `LOOKUP_TABLE` — Table lookup for enumerated values
    - `PARSER` — Value parsing for structured data
    - Benefit: Clear separation of validation approaches

13. **Rule Polarity (Sense)**
    - `POSITIVE` — Match means valid
    - `NEGATIVE` — Match means invalid (exclusion)
    - Benefit: Supports both validation and exclusion rules

14. **GrammarRule Reference**
    - `GrammarRule(capability_name, grammar_name)` — reference to grammar that produced RecognizedRep
    - Benefit: Clear traceability from notation back to source grammar

15. **Notation for Placement-Sensitive Rules**
    - Notation exists because some rules are placement-sensitive
    - Dates: `["01", "02", "2026"]` — position matters (DD/MM/YYYY vs MM/DD/YYYY)
    - Email: `["azahari", "@gmail.com"]` — position matters (local vs domain)
    - Resolver consumes notation, outputs canonical_value
    - Benefit: Clear separation of syntactic extraction vs semantic validation

16. **Contract Rule Exclusion**
    - Contracts can exclude specific rules (e.g., `Date(exclude_rule=ISO)`)
    - User can pin behavior by excluding unwanted interpretations
    - Benefit: User controls ambiguity resolution

17. **Exhaustive Rule Validation**
    - ALL rules must be checked, not just first match
    - Incomplete evidence = incomplete citation
    - Benefit: Full provenance trail for every canonical value

18. **Engine Responsibility for ExecutionResult**
    - Capability produces candidates via validation rules
    - Engine shapes ExecutionResult, computes status, replay_hash
    - Capability does NOT create ExecutionResult
    - Benefit: Clear separation of concerns, single responsibility

## Consequences

### Positive
- **Extensible:** New capabilities can be added without modifying core
- **Testable:** Each layer can be tested independently
- **Maintainable:** Clear separation of concerns
- **Auditable:** Full provenance trail for every canonical value
- **Temporal:** Supports historical data with year-based filtering

### Negative
- **Complexity:** More layers than a simple validator
- **Learning curve:** Contributors need to understand Notation concept
- **Performance:** Exhaustive recognition processes all grammars (acceptable for correctness)

### Risks
- **Notation drift:** If capabilities define inconsistent Notation shapes
  - Mitigation: Enforce Notation type in capability.py
- **Provenance staleness:** Rules may reference deprecated specifications
  - Mitigation: lifecycle field in Provenance, year-based filtering

## Alternatives Considered

1. **Single-layer validator:** Rejected — too coupled, no provenance trail
2. **Global provenance registry:** Rejected — creates coupling, requires lookups
3. **Lazy recognition (stop on first match):** Rejected — misses ambiguities
4. **Dynamic Notation per contract:** Rejected — adds complexity, benefits unclear

## References

- refactor.md — Original architecture discussion
- replay_hash.md — Replay hash concept
- CONTEXT.md — Domain glossary

---

## Appendix: Testing Strategy

### Test Layers

1. **Unit Tests** — Individual dataclasses, enums, helpers
2. **Capability Tests** — Grammar recognition + rule validation per capability
3. **Integration Tests** — Full pipeline flow, ambiguity detection, temporal filtering
4. **E2E Tests** — End-to-end user scenarios

### Test Markers

```python
@pytest.mark.unit
@pytest.mark.capability
@pytest.mark.integration
@pytest.mark.e2e
```

---

## Appendix: Architectural Enforcement

### Toolchain

| Tool | Purpose |
|------|---------|
| **ruff** | Linting + formatting |
| **pyright** | Static type checking (strict) |
| **import-linter** | Enforce import boundaries |
| **pytest** | Testing |
| **hypothesis** | Property-based testing |

### Import Rules

```
paxman.core → (no imports from capabilities, engine, api)
paxman.capabilities → (can import from core)
paxman.engine → (can import from core, capabilities)
paxman.api → (can import from everything)
```

### Public API

```python
# paxman/__init__.py

from paxman.api.canonicalize import canonicalize
from paxman.core.discovery import register_capability

__all__ = ["canonicalize", "register_capability"]
```

### Quality Gates

- All code must pass `ruff check`
- All code must pass `pyright --strict`
- All imports must pass `import-linter`
- All tests must pass `pytest`
- Type hints required on all public APIs
