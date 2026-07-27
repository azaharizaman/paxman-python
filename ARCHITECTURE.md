# Paxman Architecture

Paxman is a canonicalization authority resolver — a library that takes ambiguous human input and returns what authoritative specifications say that input means, with full provenance. This document describes the architectural principles, structural layers, and design decisions that shape the system.

---

## Core Principles

### Determinism

Paxman never guesses. Given the same input and the same contract configuration, the output is always byte-identical. This property is enforced through deterministic computation at every stage — from grammar recognition to status determination to the final replay hash. The system is designed to be replay-safe: identical inputs always produce identical outputs, enabling auditability and reproducibility.

### Provenance-First

Every canonicalized value carries full provenance — a citation of the authoritative specification, registry, or policy that validates it. Provenance is not optional metadata; it is a structural requirement. If no authority can validate a recognized input, the system reports INVALID rather than returning an unvalidated value. This ensures that users always know *why* a value is considered canonical.

### Separation of Recognition and Validation

Paxman strictly separates the act of finding values in text (recognition) from the act of determining whether those values are valid (validation). This separation is the foundation of the architecture:

- **Recognition** (syntactic): Grammars scan raw text and extract structured representations. They do not validate — they only find.
- **Validation** (semantic): Rules accept structured representations and determine whether authoritative specifications validate them. They produce canonical values with provenance.

This separation means that a single input can be recognized by multiple grammars and validated by multiple rules, enabling ambiguity detection when different authoritative sources disagree.

### Capability Isolation

Each domain (Email, Date, Country, etc.) is encapsulated as a **Capability** — an independent module that defines its own intermediate representation, recognition rules, and validation rules. Capabilities cannot import from each other. The engine and core domain provide the orchestration layer; capabilities provide the domain expertise.

---

## Structural Layers

Paxman is organized into four layers, each with a distinct responsibility. Dependencies flow inward — outer layers depend on inner layers, never the reverse.

### Core Domain

The innermost layer defines the shared vocabulary and abstract contracts that all other layers consume. It contains:

- **Abstract base classes** for Grammars (recognition) and Rules (validation)
- **Immutable value objects** representing provenance, candidates, recognized representations, and version stamps
- **Enums** for resolution status (MISSING, INVALID, SUCCESS, AMBIGUOUS) and rule strategies (REGEX, LOOKUP_TABLE, PARSER)
- **The Contract protocol** — a structural interface that all capability contracts must satisfy
- **The Capability abstract class** — a base class that all capability implementations must extend
- **The discovery registry** — a module-level registry that manages capability registration and lookup
- **Exception hierarchy** — typed errors for different failure modes

The core layer has no knowledge of specific capabilities. It defines *what* a capability is, not *how* any particular capability works.

### Capabilities

Each capability is a self-contained domain module that provides:

- **A Notation type** — a typed intermediate representation specific to the domain (e.g., email local part and domain part, date N1/N2/N3)
- **Grammars** — recognition rules that extract the notation from raw text
- **Validation Rules** — semantic rules that validate the notation against authoritative specifications
- **A Contract** — a user-facing configuration object that toggles grammars, excludes rules, and passes parameters

Capabilities are registered with the discovery registry before the first canonicalization call. The registry freezes at the start of each pipeline run, ensuring that the set of available capabilities is stable during execution.

### Engine

The engine is the orchestration layer that coordinates the full pipeline. It:

1. Freezes the capability registry
2. Looks up the requested capability by name
3. Runs the recognition phase — iterating over active grammars to extract notations
4. Runs the validation phase — testing each notation against active rules
5. Determines the resolution status based on candidate outcomes
6. Computes a deterministic replay hash for integrity verification
7. Assembles the final execution result

The engine is capability-agnostic. It does not know what a "grammar" or "rule" does — it only knows that grammars produce notations and rules produce candidates.

### Public API

The outermost layer exposes the user-facing interface. It is intentionally minimal — a single entry point that accepts input text and a contract, and returns a fully-resolved execution result with provenance and replay metadata.

---

## Key Architectural Patterns

### Protocol-Based Contracts

Contracts are defined as structural protocols (`Contract`), not inheritance-based base classes. Any class that satisfies the structural interface — providing the required attributes and methods — qualifies as a contract. This allows capability authors to design contract objects that fit their domain (using dataclasses, Pydantic models, etc.) without being constrained by a base class hierarchy. This prioritizes **user flexibility** and **decoupling**.

### ABC-Based Capabilities

In contrast to contracts, Capabilities are defined as Abstract Base Classes (`Capability`). This prioritizes **internal rigidity** and **reliability**. Since capabilities are internal components managed by the engine's registry, strict inheritance ensures they adhere to the required structure (`get_grammars()`, `get_rules()`) and prevents runtime errors during discovery.

### Capability as Factory

Capabilities do not hold state. They are factories that produce grammars and rules on demand. The engine queries a capability for its available grammars and rules, then filters them based on the contract configuration. This design keeps capabilities lightweight and makes the filtering logic centralized in the engine.

### Notation Bridging

Each capability defines a typed Notation (a data class with named fields) that provides domain-specific structure. However, the Rule and Grammar abstract interfaces operate on a generic list-of-strings representation. Capabilities bridge this gap by providing a conversion method from the typed notation to the generic form. This gives type safety at the capability level while maintaining a uniform interface for the engine.

### Contract Parameters

Contracts pass configuration parameters to validation rules, enabling rules to adapt their behavior based on user preferences.

**Base Contract Parameters:**
- **`output_format`**: Controls the canonical value format (e.g., `"ISO"` for `YYYY-MM-DD`, `"US"` for `MM/DD/YYYY`). Rules check this parameter during normalization to produce the desired output format.
- **`pinned_rules`**: Pins to specific validation rules by name. When set, ONLY those rules run — `excluded_rules` is ignored. Takes precedence over `excluded_rules`.

**Date-Specific Parameters:**
- **`two_digit_base_year`**: Specifies the base year for interpreting two-digit years (e.g., `2000` means `"26"` becomes `2026`). Only available on Date contracts, not part of the base Contract protocol. Used by US and European grammars to resolve ambiguous year values.

These parameters are passed through the contract to rule methods (`matches()` and `normalize()`), allowing rules to be contract-aware without direct coupling to specific capabilities.

### Immutability

All domain objects are immutable. Once created, they cannot be modified. This is enforced through `@dataclass(frozen=True, slots=True)` — stdlib dataclasses that prevent attribute assignment and use efficient slot-based storage. Immutability ensures that objects can be safely shared, hashed, and used as dictionary keys without defensive copying.

### Temporal Filtering

Rules carry a publication year from their authoritative specification. When a contract specifies a year, the engine filters out rules whose publication year exceeds that year. This allows users to pin to a specific historical version of a specification, excluding rules from newer revisions.

### Replay Integrity

Every execution produces a VersionStamp containing a deterministic SHA-256 hash computed from the input text, contract configuration, resolution status, and all candidate values. This hash enables replay verification — confirming that the same input and configuration produce the same output, byte-for-byte.

---

## Resolution Semantics

The system produces one of four resolution statuses:

| Status | Meaning |
|--------|---------|
| **MISSING** | No grammars recognized anything in the input. The input does not match any known pattern. |
| **INVALID** | Grammars recognized the input, but no validation rule could validate it against an authoritative specification. |
| **SUCCESS** | One or more rules validated the input, and all agree on the same canonical value. |
| **AMBIGUOUS** | Multiple rules validated the input but produced different canonical values. The system cannot determine which is correct. |

Ambiguity is detected at the value level, not the candidate level. Multiple candidates with the same canonical value still produce SUCCESS. Ambiguity requires genuinely different canonical outputs from different authoritative sources.

---

## Error Handling

The exception hierarchy separates different failure modes:

- **CapabilityError** — the requested capability is unknown or the registry is in an invalid state
- **ContractError** — the contract configuration is malformed or missing required fields
- **RecognitionError** — a grammar failed during recognition (e.g., malformed regex), wrapping the original exception
- **ValidationError** — a rule failed during validation (e.g., unexpected data), wrapping the original exception

Recognition and validation errors carry the name of the offending rule and the original exception, enabling targeted debugging without losing context.

---

## Quality Enforcement

Paxman enforces architectural invariants through tooling:

- **Static type checking** in strict mode ensures type safety across all layers
- **Import boundary enforcement** prevents capability-to-capability dependencies and ensures the core layer remains independent
- **Linting and formatting** enforce consistent code style
- **Property-based testing** validates domain object contracts (immutability, equality, hashability)

These tools run as part of the development workflow and block merges when invariants are violated.

---

## Date Capability Design

The Date capability demonstrates the system's handling of ambiguous inputs through multiple grammars and validation rules.

### Grammars

Three grammars recognize date patterns with different position mappings:

| Grammar | Delimiter | N1 (first) | N2 (second) | N3 (third) | Notes |
|---------|-----------|------------|-------------|------------|-------|
| ISO | `-` | year | month | day | 4-digit year only |
| US | `/` | month | day | year | Supports 2-digit years |
| European | `/` | day | month | year | Supports 2-digit years |

European and US grammars both use `/` as delimiter. Ambiguity arises from different position mappings, not delimiters.

### Validation Rules

Three rules validate date notations against authoritative specifications:

| Rule | Standard | Canonical Output |
|------|----------|------------------|
| ISO 8601 | ISO 8601:2019 | `YYYY-MM-DD` |
| US federal | US government standard | `YYYY-MM-DD` |
| EN 50160 | European EN 50160 | `YYYY-MM-DD` |

All rules normalize to ISO 8601 format (`YYYY-MM-DD`) regardless of input grammar.

### Ambiguity Detection

When the same input is recognized by multiple grammars, each grammar produces notation with different position mappings. For example, `"01/02/2026"` is recognized by both US and European grammars:
- US grammar: N1=month=01, N2=day=02, N3=year=2026
- European grammar: N1=day=01, N2=month=02, N3=year=2026

Each grammar's notation flows to its corresponding validation rule. If both rules validate and produce different canonical values, the system reports AMBIGUOUS.
