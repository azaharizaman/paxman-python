# Architecture Review — paxman-alternative

**Date:** 2026-07-26
**Reviewer:** Sisyphus (automated architecture analysis)

---

## Legend

- **Solid box** = module
- **Dashed line** = seam
- **Red arrow** = leakage
- **Thick dark box** = deep module

---

## Candidate 1: Collapse immutability boilerplate into a frozen base

**Strength:** Strong
**Files:** `paxman/core/domain.py`

### Problem

Every domain object in `domain.py` manually repeats the same immutability pattern: `__slots__`, `object.__setattr__` in `__init__`, guards in `__setattr__`/`__delattr__`, plus manual `__eq__`/`__hash__`. This is ~40 lines per class, 5 classes, ~200 lines of identical mechanical code.

The five classes affected:

| Class | Fields | Boilerplate lines |
|-------|--------|-------------------|
| `Provenance` | 7 fields | ~45 |
| `GrammarRule` | 2 fields | ~30 |
| `RecognizedRep` | 3 fields | ~35 |
| `Candidate` | 4 fields | ~50 |
| `VersionStamp` | 2 fields | ~30 |

### Before / After

```
BEFORE                              AFTER
─────────────────────────          ─────────────────────────

┌─────────────────────┐            ┌─────────────────────┐
│     Provenance      │            │    FrozenBase       │
│ __slots__           │            │ __slots__           │
│ __init__ (setattr)  │            │ __setattr__ (guard) │
│ __setattr__ (guard) │            │ __delattr__ (guard) │
│ __delattr__ (guard) │            │ __eq__ (auto)       │
│ __eq__ (manual)     │            │ __hash__ (auto)     │
│ __hash__ (manual)   │            └──────────┬──────────┘
└─────────────────────┘                       │
┌─────────────────────┐            ┌──────────▼──────────┐
│    GrammarRule      │            │ Provenance          │
│ __slots__           │            │ 5 fields only       │
│ __init__ (setattr)  │            └─────────────────────┘
│ __setattr__ (guard) │            ┌──────────▼──────────┐
│ __delattr__ (guard) │            │ GrammarRule         │
│ __eq__ (manual)     │            │ 2 fields only       │
│ __hash__ (manual)   │            └─────────────────────┘
└─────────────────────┘            ┌──────────▼──────────┐
┌─────────────────────┐            │ RecognizedRep       │
│   RecognizedRep     │            │ 3 fields only       │
│ __slots__           │            └─────────────────────┘
│ __init__ (setattr)  │            ┌──────────▼──────────┐
│ __setattr__ (guard) │            │ Candidate           │
│ __delattr__ (guard) │            │ 4 fields only       │
│ __eq__ (manual)     │            └─────────────────────┘
│ __hash__ (manual)   │            ┌──────────▼──────────┐
└─────────────────────┘            │ VersionStamp        │
┌─────────────────────┐            │ 2 fields only       │
│     Candidate       │            └─────────────────────┘
│ __slots__           │
│ __init__ (setattr)  │            1 base class (~40 lines)
│ __setattr__ (guard) │            + 5 thin subclasses
│ __delattr__ (guard) │            (~10 lines each)
│ __eq__ (manual)     │
│ __hash__ (manual)   │            5 classes × ~40 lines = ~200 lines
└─────────────────────┘
┌─────────────────────┐
│    VersionStamp     │
│ __slots__           │
│ __init__ (setattr)  │
│ __setattr__ (guard) │
│ __delattr__ (guard) │
│ __eq__ (manual)     │
│ __hash__ (manual)   │
└─────────────────────┘

5 classes × ~40 lines = ~200 lines
```

### Solution

Extract a `FrozenBase` class that provides immutability for free via `__slots__` inheritance. Each domain class declares only its fields and their types. `__eq__` and `__hash__` are generated from slot names.

```python
class FrozenBase:
    """Base class for immutable domain objects."""

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"{type(self).__name__} is immutable")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        slots = type(self).__slots__
        return all(getattr(self, s) == getattr(other, s) for s in slots)

    def __hash__(self) -> int:
        slots = type(self).__slots__
        return hash(tuple(getattr(self, s) for s in slots))
```

Each domain class becomes:

```python
class Provenance(FrozenBase):
    __slots__ = ("authority", "specification_name", "kind",
                 "reference_url", "version", "lifecycle", "publication_year")

    def __init__(self, authority: str, specification_name: str, kind: str,
                 reference_url: str, version: str | None, lifecycle: str,
                 publication_year: int) -> None:
        object.__setattr__(self, "authority", authority)
        # ... remaining fields
```

### Benefits

- **locality:** immutability guarantee lives in one place, not five
- **leverage:** new domain objects become 5-line declarations
- **test surface:** immutability tests written once against the base

---

## Candidate 2: Restore Notation type safety across the grammar→rule seam

**Strength:** Worth exploring
**Files:**
- `paxman/capabilities/Email/grammar/standard_recognition.py`
- `paxman/capabilities/Email/grammar/obfuscated_recognition.py`
- `paxman/capabilities/Email/grammar/localhost_recognition.py`
- `paxman/capabilities/Email/rules/rfc_5322_ed2008.py`
- `paxman/capabilities/Email/rules/rfc_6761_ed2012.py`
- `paxman/capabilities/Email/notation.py`
- `paxman/core/domain.py` (Grammar, Rule ABCs)

### Problem

`EmailNotation` is a proper frozen dataclass with named fields (`local_part`, `domain_part`), but every grammar immediately calls `.as_list()` to produce `list[str]`. Rules then receive untyped `list[str]` and must manually index (`notation[0]`, `notation[1]`). The type safety gained from `EmailNotation` is erased at the grammar→rule seam.

Current code in every grammar:

```python
# grammar/standard_recognition.py
def recognize(self, text: str) -> list[Notation]:
    matches = _STANDARD_PATTERN.findall(text)
    return [
        EmailNotation(
            local_part=match.split("@")[0],
            domain_part=match.split("@")[1],
        ).as_list()          # ← type safety erased here
        for match in matches
    ]
```

Current code in every rule:

```python
# rules/rfc_5322_ed2008.py
def matches(self, notation: Notation) -> bool:
    local_part = notation[0]     # ← manual indexing, no IDE support
    domain_part = notation[1]    # ← off-by-one waiting to happen
    return bool(
        _LOCAL_PATTERN.match(local_part) and _DOMAIN_PATTERN.match(domain_part)
    )
```

### Before / After

```
BEFORE                                  AFTER
──────────────────────────────          ──────────────────────────────

┌──────────────────────┐                ┌──────────────────────┐
│ StandardEmailGrammar │                │ StandardEmailGrammar │
│ .recognize() →       │                │ .recognize() →       │
│   list[Notation]     │                │   list[EmailNotation]│
└──────────┬───────────┘                └──────────┬───────────┘
           │ .as_list()                            │ (typed)
           ▼                                       ▼
┌──────────────────────┐                ┌──────────────────────┐
│     list[str]        │                │   EmailNotation      │
│  (UNTYPE D!)         │                │  .local_part         │
│  notation[0]         │                │  .domain_part        │
│  notation[1]         │                └──────────┬───────────┘
└──────────┬───────────┘                           │ (typed)
           │                                       ▼
           ▼                           ┌──────────────────────┐
┌──────────────────────┐               │   Rule.matches()     │
│   Rule.matches()     │               │  notation.local_part │
│  notation[0]         │               │  notation.domain_part│
│  notation[1]         │               └──────────────────────┘
└──────────────────────┘

Typed notation flows through, no erasure
```

### Solution

Parameterize the `Grammar` and `Rule` ABCs with a Notation type variable. Grammar.recognize returns `list[N]`, Rule.matches/normalize accept `N`. Each capability provides a Notation Protocol or dataclass. Grammars no longer call `.as_list()`.

```python
from typing import Generic, TypeVar

N = TypeVar("N", bound=list[str])

class Grammar(ABC, Generic[N]):
    name: str

    @abstractmethod
    def recognize(self, text: str) -> list[N]: ...

class Rule(ABC, Generic[N]):
    name: str
    strategy: RuleStrategy
    provenance: Provenance
    citation: str

    @abstractmethod
    def matches(self, notation: N) -> bool: ...

    @abstractmethod
    def normalize(self, notation: N) -> str: ...
```

Email grammars become:

```python
class StandardEmailGrammar(Grammar[EmailNotation]):
    name = "standard_recognition"

    def recognize(self, text: str) -> list[EmailNotation]:
        matches = _STANDARD_PATTERN.findall(text)
        return [
            EmailNotation(
                local_part=match.split("@")[0],
                domain_part=match.split("@")[1],
            )
            for match in matches
        ]
```

Email rules become:

```python
class Section341AddrSpec(Rule[EmailNotation]):
    name = "Section 3.4.1-addr-spec"

    def matches(self, notation: EmailNotation) -> bool:
        return bool(
            _LOCAL_PATTERN.match(notation.local_part)
            and _DOMAIN_PATTERN.match(notation.domain_part)
        )

    def normalize(self, notation: EmailNotation) -> str:
        return f"{notation.local_part.lower()}@{notation.domain_part.lower()}"
```

### Benefits

- **locality:** field access errors caught at type-check time, not runtime
- **leverage:** grammar authors get IDE completion on notation fields
- **interface:** the grammar→rule contract becomes self-documenting

---

## Candidate 3: Extract grammar dispatch from rule evaluation in `_validate`

**Strength:** Worth exploring
**Files:** `paxman/engine/orchestrator.py`

### Problem

The `_validate` function interleaves grammar dispatch, rule filtering (excluded + year), and candidate collection in a single 62-line function. You cannot test grammar recognition independently from rule evaluation. This limits test locality.

Current structure:

```python
def _validate(text, capability, contract) -> tuple[list[Candidate], bool]:
    # PHASE 1: Grammar dispatch (lines 73-93)
    active_grammar_names = set(contract.active_grammars)
    all_grammars = capability.get_grammars()
    active_grammars = [g for g in all_grammars if g.name in active_grammar_names]
    recognitions = []
    for grammar in active_grammars:
        notations = grammar.recognize(text)
        # ... build RecognizedReps

    # PHASE 2: Rule filtering (lines 97-99)
    all_rules = capability.get_rules()
    excluded = set(contract.excluded_rules)
    active_rules = [r for r in all_rules if r.name not in excluded]

    # PHASE 3: Candidate collection (lines 101-126)
    candidates = []
    for recognition in recognitions:
        for rule in active_rules:
            if contract.year and rule.provenance.publication_year > contract.year:
                continue
            if rule.matches(recognition.notation):
                canonical = rule.normalize(recognition.notation)
                candidates.append(Candidate(...))

    return candidates, had_recognitions
```

### Before / After

```
BEFORE                              AFTER
─────────────────────────          ─────────────────────────

┌─────────────────────────┐        ┌─────────────────────────┐
│ _validate(text, cap, ct)│        │ _recognize(text, cap, ct)│
│                         │        │  (testable in isolation) │
│  grammar dispatch       │        └────────────┬────────────┘
│       +                 │                     │
│  rule filtering         │        ┌────────────▼────────────┐
│       +                 │        │ _filter_rules(cap, ct)   │
│  candidate collection   │        │  (testable in isolation) │
│                         │        └────────────┬────────────┘
│  62 lines, one function │                     │
└─────────────────────────┘        ┌────────────▼────────────┐
                                   │ _collect_candidates()    │
                                   │  (testable in isolation) │
                                   └────────────┬────────────┘
                                                │
                                   ┌────────────▼────────────┐
                                   │ run_capability()         │
                                   │  composes the three      │
                                   └──────────────────────────┘

Each sub-phase independently testable
```

### Solution

Extract three focused functions:

```python
def _recognize(
    text: str, capability: Capability, contract: Contract
) -> list[RecognizedRep]:
    """Run active grammars and return all recognitions."""
    active_grammar_names = set(contract.active_grammars)
    all_grammars = capability.get_grammars()
    active_grammars = [g for g in all_grammars if g.name in active_grammar_names]

    recognitions: list[RecognizedRep] = []
    for grammar in active_grammars:
        try:
            notations = grammar.recognize(text)
        except Exception as exc:
            raise RecognitionError(
                rule=grammar.name,
                message=f"Grammar failed: {exc}",
                original_error=exc,
            ) from exc
        grammar_ref = GrammarRule(
            capability_name=capability.name, grammar_name=grammar.name
        )
        for notation in notations:
            recognitions.append(
                RecognizedRep(notation=notation, contract=contract, grammar=grammar_ref)
            )
    return recognitions


def _filter_rules(capability: Capability, contract: Contract) -> list[Rule]:
    """Return rules that are not excluded and pass year filter."""
    all_rules = capability.get_rules()
    excluded = set(contract.excluded_rules)
    active_rules = [r for r in all_rules if r.name not in excluded]

    if contract.year is not None:
        active_rules = [
            r for r in active_rules
            if r.provenance.publication_year <= contract.year
        ]
    return active_rules


def _collect_candidates(
    recognitions: list[RecognizedRep], rules: list[Rule]
) -> list[Candidate]:
    """Match recognitions against rules and collect candidates."""
    candidates: list[Candidate] = []
    for recognition in recognitions:
        for rule in rules:
            try:
                if rule.matches(recognition.notation):
                    canonical = rule.normalize(recognition.notation)
                    candidates.append(
                        Candidate(
                            value=canonical,
                            recognition_rule=recognition.grammar.grammar_name,
                            validation_rule=rule.name,
                            provenance=[rule.provenance],
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

`run_capability` composes them:

```python
def run_capability(text: str, contract: Contract) -> ExecutionResult:
    freeze_registry()
    capability = get_capability(contract.capability_name)

    recognitions = _recognize(text, capability, contract)
    had_recognitions = len(recognitions) > 0

    rules = _filter_rules(capability, contract)
    candidates = _collect_candidates(recognitions, rules)

    status = _determine_status(candidates, had_recognitions)
    canonical_value = _extract_canonical_value(candidates, status)
    version_stamp = _build_version_stamp(text, candidates, contract, status)

    return ExecutionResult(
        status=status,
        canonicalized_value=canonical_value,
        candidates=tuple(candidates),
        contract=contract,
        version_stamp=version_stamp,
    )
```

### Benefits

- **locality:** grammar dispatch bugs isolated from rule bugs
- **leverage:** each sub-phase has a focused test surface
- **interface:** function signatures document the pipeline stages explicitly

---

## Candidate 4: Make grammar registration declarative on contracts

**Strength:** Speculative
**Files:**
- `paxman/capabilities/Email/capability.py` (`EmailContract.active_grammars`)
- Future capability contracts

### Problem

Each capability's contract has a procedural `active_grammars` property that maps boolean flags to grammar name lists with if/append logic. Every new grammar requires editing this method. The pattern repeats across capabilities.

Current code in `EmailCapability`:

```python
@dataclass(frozen=True)
class EmailContract:
    capability_name: str = field(default="email", init=False)
    include_obfuscated: bool = False
    include_localhost: bool = True
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    year: int | None = None

    @property
    def active_grammars(self) -> list[str]:
        grammars = ["standard_recognition"]       # ← always on
        if self.include_obfuscated:               # ← procedural
            grammars.append("obfuscated_recognition")
        if self.include_localhost:                # ← procedural
            grammars.append("localhost_recognition")
        return grammars
```

### Before / After

```
BEFORE (cross-section)                 AFTER (cross-section)
───────────────────────────           ───────────────────────────

┌───────────────────────────┐         ┌───────────────────────────┐
│ if self.include_obfuscated│         │ GRAMMAR_MAP = {           │
│   grammars.append(...)    │         │   "standard": True,       │
├───────────────────────────┤         │   "obfuscated":           │
│ if self.include_localhost │         │     "include_obfuscated", │
│   grammars.append(...)    │         │   "localhost":            │
├───────────────────────────┤         │     "include_localhost",  │
│ # always: standard        │         │ }                         │
└───────────────────────────┘         │ active_grammars computed  │
                                      │ from map                  │
Procedural:                           ├───────────────────────────┤
each new grammar = new if/append      │ new grammar = one entry   │
                                      └───────────────────────────┘

                                      Declarative:
                                      new grammar = one map entry
```

### Solution

Declare a grammar registry on the capability or contract: a mapping from grammar name to activation condition (always-on, or bound to a contract field). The `active_grammars` property computes from this registry.

```python
from enum import Enum

class GrammarActivation(Enum):
    """How a grammar is activated."""
    ALWAYS = "always"           # Grammar is always active
    FIELD = "field"             # Grammar is active when contract field is True

# On the Capability class:
GRAMMAR_REGISTRY = {
    "standard_recognition": GrammarActivation.ALWAYS,
    "obfuscated_recognition": GrammarActivation.FIELD,
    "localhost_recognition": GrammarActivation.FIELD,
}

# On the Contract:
FIELD_MAP = {
    "obfuscated_recognition": "include_obfuscated",
    "localhost_recognition": "include_localhost",
}
```

The `active_grammars` property becomes a loop:

```python
@property
def active_grammars(self) -> list[str]:
    grammars = []
    for name, activation in GRAMMAR_REGISTRY.items():
        if activation == GrammarActivation.ALWAYS:
            grammars.append(name)
        elif activation == GrammarActivation.FIELD:
            field_name = FIELD_MAP[name]
            if getattr(self, field_name, False):
                grammars.append(name)
    return grammars
```

### Benefits

- **locality:** grammar activation logic lives in a single data structure
- **leverage:** capability authors add one line, not a method edit
- **test surface:** registry can be asserted against directly

---

## Top Recommendation

### Collapse immutability boilerplate into a frozen base

This is the deepest seam in the codebase. Five domain objects repeat ~40 lines of identical immutability machinery. A `FrozenBase` class concentrates this in one place. Every future domain object benefits. The deletion test passes: removing the base and inlining the pattern back would re-spread the complexity, confirming the base concentrates it.

**Start here because:**

1. It touches `paxman/core/domain.py` only — zero downstream API changes
2. It has zero risk of breaking existing behavior (pure mechanical extraction)
3. It makes Candidate 2 (Notation type safety) easier by establishing a generic-parameterized base pattern
4. It creates a template for future domain objects as the library grows

---

## Appendix: Codebase Context

### Architecture Layers

```
paxman/core/          Domain objects, protocols, discovery
paxman/capabilities/  Capability implementations (Email, Date, Country)
paxman/engine/        Pipeline orchestrator
paxman/api/           Public API entry points
```

### Import Boundaries (ADR-0001)

```
paxman.core → (no imports from capabilities, engine, api)
paxman.capabilities → (can import from core)
paxman.engine → (can import from core, capabilities)
paxman.api → (can import from everything)
```

### Hot Spots (Recent Commits)

```
05732ae refactor(core): address code review findings for Email capability
1a69f7e fix: quality gate fixes (ruff, pyright, import-linter, formatting)
5de47b7 feat(capabilities): add Email capability exports
25db939 feat(api): implement canonicalize() public API
ebf12fa test(integration): add temporal filtering tests
d0a6f2f test(integration): add ambiguity detection tests
0252024 feat(engine): add pipeline orchestrator with ExecutionResult and replay hash
```

### Test Structure

```
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
