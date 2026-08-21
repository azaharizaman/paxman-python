# Architecture Review — paxman-alternative

**Date:** 2026-07-26
**Reviewer:** Sisyphus (automated architecture analysis)
**Status:** ✅ All candidates implemented (2026-07-26)

---

## Implementation Summary

All four architectural deepening candidates have been implemented. Below are the actual decisions and outcomes:

| Candidate | Original Proposal | Actual Implementation | Status |
|-----------|-------------------|----------------------|--------|
| 1. Dataclass Migration | `FrozenBase` custom class | `@dataclass(frozen=True, slots=True)` | ✅ Complete |
| 2. Typed Notation | `TypeVar("N", bound=list[str])` | `TypeVar("NotationT")` (unbounded) | ✅ Complete |
| 3. Orchestrator Decomposition | 3 extracted functions | 3 extracted functions | ✅ Complete |
| 4. Declarative Grammars | `GrammarActivation` enum | `dict[str, bool]` mapping | ✅ Complete |

### Key Decisions

1. **Candidate 1**: Used stdlib `@dataclass(frozen=True, slots=True)` instead of custom `FrozenBase` — eliminates ~160 lines with zero custom base class
2. **Candidate 2**: Removed `bound=list[str]` constraint — allows capabilities to use any notation type (frozen dataclasses, Protocols, etc.)
3. **Candidate 4**: Used direct `dict[str, bool]` instead of `GrammarActivation` enum — simpler, more Pythonic

---

## Legend

- **Solid box** = module
- **Dashed line** = seam
- **Red arrow** = leakage
- **Thick dark box** = deep module

---

## Candidate 1: Collapse immutability boilerplate into a frozen base ✅ IMPLEMENTED

**Strength:** Strong
**Status:** ✅ Implemented (2026-07-26)
**Files:** `paxman/core/domain.py`

### Problem (RESOLVED)

Every domain object in `domain.py` manually repeats the same immutability pattern: `__slots__`, `object.__setattr__` in `__init__`, guards in `__setattr__`/`__delattr__`, plus manual `__eq__`/`__hash__`. This is ~40 lines per class, 5 classes, ~200 lines of identical mechanical code.

### Actual Implementation

Used stdlib `@dataclass(frozen=True, slots=True)` instead of proposed `FrozenBase` class — simpler, zero custom base class needed.

```python
@dataclass(frozen=True, slots=True)
class Provenance:
    authority: str
    specification_name: str
    kind: str
    reference_url: str
    version: str | None
    lifecycle: str
    publication_year: int
```

**Net reduction:** ~160 lines of boilerplate eliminated across 5 domain classes.

---

## Candidate 2: Restore Notation type safety across the grammar→rule seam ✅ IMPLEMENTED

**Strength:** Worth exploring
**Status:** ✅ Implemented (2026-07-26)
**Files:**
- `paxman/core/domain.py` (Grammar, Rule ABCs)
- `paxman/capabilities/Email/grammar/*.py`
- `paxman/capabilities/Email/rules/*.py`

### Problem (RESOLVED)

`EmailNotation` was a proper frozen dataclass with named fields (`local_part`, `domain_part`), but every grammar immediately called `.as_list()` to produce `list[str]`. Rules then received untyped `list[str]` and had to manually index (`notation[0]`, `notation[1]`). The type safety gained from `EmailNotation` was erased at the grammar→rule seam.

### Actual Implementation

Parameterized `Grammar` and `Rule` ABCs with unbounded `TypeVar("NotationT")` — allows any notation type, not just `list[str]`.

```python
NotationT = TypeVar("NotationT")


class Grammar(ABC, Generic[NotationT]):
    @abstractmethod
    def recognize(self, text: str) -> list[NotationT]: ...


class Rule(ABC, Generic[NotationT]):
    @abstractmethod
    def matches(self, notation: NotationT, contract: Contract) -> bool: ...
    @abstractmethod
    def normalize(self, notation: NotationT, contract: Contract) -> str: ...
```

**Benefit:** Type safety flows from grammar → rule boundary, no more `notation[0]` indexing.

---

## Candidate 3: Extract grammar dispatch from rule evaluation in `_validate` ✅ IMPLEMENTED

**Strength:** Worth exploring
**Status:** ✅ Implemented (2026-07-26)
**Files:** `paxman/engine/orchestrator.py`

### Problem (RESOLVED)

The `_validate` function interleaved grammar dispatch, rule filtering (excluded + year), and candidate collection in a single 62-line function. Grammar recognition could not be tested independently from rule evaluation.

### Actual Implementation

Extracted three focused functions composed by `run_capability()`:

| Function | Purpose | Lines |
|----------|---------|-------|
| `_recognize()` | Run active grammars, return recognitions | ~20 |
| `_filter_rules()` | Apply exclusions and year filter | ~10 |
| `_collect_candidates()` | Match recognitions against rules | ~20 |

**Benefit:** Each pipeline phase independently testable.

---

## Candidate 4: Make grammar registration declarative on contracts ✅ IMPLEMENTED

**Strength:** Speculative
**Status:** ✅ Implemented (2026-07-26)
**Files:** `paxman/capabilities/Email/capability.py`

### Problem (RESOLVED)

Each capability's contract had a procedural `active_grammars` property that mapped boolean flags to grammar name lists with if/append logic. Every new grammar required editing this method.

### Actual Implementation

Used direct `dict[str, bool]` mapping instead of proposed `GrammarActivation` enum — simpler, more Pythonic.

```python
@property
def active_grammars(self) -> list[str]:
    grammar_rules: dict[str, bool] = {
        "standard_recognition": True,
        "obfuscated_recognition": self.include_obfuscated,
        "localhost_recognition": self.include_localhost,
    }
    return [name for name, active in grammar_rules.items() if active]
```

**Benefit:** Adding a grammar requires one dictionary entry in this property.

---

## Implementation Complete

All four architectural deepening candidates have been implemented:

| # | Candidate | Approach | Net Impact |
|---|-----------|----------|------------|
| 1 | Dataclass migration | `@dataclass(frozen=True, slots=True)` | ~160 lines eliminated |
| 2 | Typed notation generics | `Grammar[NotationT]`, `Rule[NotationT]` | Type safety across seam |
| 3 | Orchestrator decomposition | 3 focused functions | Independently testable phases |
| 4 | Declarative grammar registry | `dict[str, bool]` mapping | One entry to add grammar |

**Verification:** 136 tests passing, ruff clean, pyright strict

---

## Appendix: Codebase Context

### Architecture Layers

```text
paxman/core/          Domain objects, protocols, discovery
paxman/capabilities/  Capability implementations (Email, Date, Country)
paxman/engine/        Pipeline orchestrator
paxman/api/           Public API entry points
```

### Import Boundaries (ADR-0001)

```text
paxman.core → (no imports from capabilities, engine, api)
paxman.capabilities → (can import from core)
paxman.engine → (can import from core, capabilities)
paxman.api → (can import from everything)
```

### Hot Spots (Recent Commits)

```text
05732ae refactor(core): address code review findings for Email capability
1a69f7e fix: quality gate fixes (ruff, pyright, import-linter, formatting)
5de47b7 feat(capabilities): add Email capability exports
25db939 feat(api): implement canonicalize() public API
ebf12fa test(integration): add temporal filtering tests
d0a6f2f test(integration): add ambiguity detection tests
0252024 feat(engine): add pipeline orchestrator with ExecutionResult and replay hash
```

### Test Structure

```text
tests/unit/           Domain object immutability and protocol compliance
tests/capabilities/   Grammar recognition and rule normalization
tests/integration/    Full pipeline flow, ambiguity, temporal filtering
tests/e2e/            End-to-end user scenarios
```

### Toolchain

| Tool | Purpose |
|------|---------|
| ruff | Linting + formatting |
| pyright | Static type checking (strict) |
| import-linter | Enforce import boundaries |
| pytest | Testing |
| hypothesis | Property-based testing |
