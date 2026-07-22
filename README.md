# Paxman

**A deterministic canonicalization library.**

Paxman begins as a deterministic canonicalization engine (see [`PRD.md`](./PRD.md)).
It rewrites information that is *unambiguously* equivalent into a single, agreed
canonical form — and refuses to guess when the input does not determine a unique
result. Paxman does not normalize, infer, orchestrate, or improvise. It makes the
determinable determinable, consistently, forever.

- **One form, agreed by all** — same logical input, same canonical output, every time.
- **No silent guessing** — ambiguity results in clear status (AMBIGUOUS, INVALID, MISSING).
- **Perfect recall** — every execution_result replays to itself byte-for-byte.

> Paxman *begins* as a canonicalization engine. The scope may expand; the
> guarantees will not. See [`PRD.md`](./PRD.md) §11 for the roadmap.

## Project Status

Day zero. This repository is scaffolded: the package layout, public documents,
and empty stub files exist, but no concrete implementation has been written yet.
See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the high-level design and
[`CODING_GUIDELINES.md`](./CODING_GUIDELINES.md) for how to contribute.

## Targets & License

- **Python:** 3.11, 3.12, 3.13
- **License:** MIT

## Development Guardrails

Paxman's architecture is enforced by tooling, not just prose — chosen to resist
architectural drift during agentic coding:

- **Ruff** (lint + format), **MyPy** (`strict`), **Import Linter** (sealed-core
  import contracts), **pytest** + **pytest-cov**, **Hypothesis** (property/invariant
  tests). Zero runtime dependencies; core uses `dataclasses`, not frameworks.
- Internal packages are underscore-prefixed (`_engine/`, `_registry/`) to mark
  them private. See [`ARCHITECTURE.md`](./ARCHITECTURE.md) and
  [`docs/adr/0001-sealed-core-open-edge.md`](./docs/adr/0001-sealed-core-open-edge.md).
- Run guardrails with: `ruff check src`, `ruff format src`, `mypy`, and
  `PYTHONPATH=src lint-imports` (the `src/` layout requires `PYTHONPATH` so
  import-linter can resolve the `paxman` package).

## Documentation

| File | Purpose |
| --- | --- |
| [`PRD.md`](./PRD.md) | Product Requirements Document — vision, promise, invariants, roadmap. |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | High-level architecture: what and why. |
| [`CODING_GUIDELINES.md`](./CODING_GUIDELINES.md) | Rules for contributing code. |

## Folder Structure

The layout below mirrors the architecture described in
[`ARCHITECTURE.md`](./ARCHITECTURE.md) and [`PRD.md`](./PRD.md) §5. Every folder
exists as an empty stub at this stage.

```
src/paxman/                      # The Paxman library package (root) — sole public entry point.
├── _engine/                     # The sealed, fixed core (private). Owned by Paxman; not extensible.
├── contracts/                   # The declarative, versioned shared language (caller ↔ engine).
├── capabilities/                # The ONLY extension point. One package per domain.
│   ├── email/                   # Example domain: email address canonicalization.
│   │   ├── grammar.py           # Pattern recognition for email inputs.
│   │   ├── validator.py         # Validation against email specifications.
│   │   ├── canonicalizer.py     # Derivation of canonical email form.
│   │   └── specs/               # Capability-private email specifications.
│   ├── date/                    # Example domain: date canonicalization.
│   │   ├── grammar.py           # Pattern recognition for date inputs.
│   │   ├── validator.py         # Validation against date specifications.
│   │   ├── canonicalizer.py     # Derivation of canonical date form.
│   │   └── specs/               # Capability-private date specifications.
│   └── identifier/              # Example domain: unique identifier canonicalization.
│       ├── grammar.py           # Pattern recognition for identifier inputs.
│       ├── validator.py         # Validation against identifier specifications.
│       ├── canonicalizer.py     # Derivation of canonical identifier form.
│       └── specs/               # Capability-private identifier specifications.
├── _registry/                   # The frozen roll call (private) mapping contracts to capabilities.
└── execution_results/           # Self-describing, replayable records of a canonicalization.
```

### Folder descriptions

- **`src/paxman/`** — The library root package. Exposes the public surface
  (`canonicalize(...)`) and aggregates the subpackages below. This is the only
  import boundary users and extenders rely on.

- **`src/paxman/_engine/`** — The **sealed core** (private, underscore-prefixed).
  A pure, stateless referee that runs the fixed canonicalization pipeline
  (Receive → Resolve → Delegate → Seal → Replay). It holds no domain opinion and
  is owned by Paxman; contributors do not modify it and capabilities must not
  import it. This is where the three invariants are concentrated (PRD §5.1).

- **`src/paxman/contracts/`** — The **shared language** between caller and engine.
  A contract is declarative and versioned: it names the *kind* of information and
  optionally *pins an authority edition*. It carries no behavior — the caller
  states intent, never how (PRD §5.2).

- **`src/paxman/capabilities/`** — The **only extension point**. A uniform
  interface every domain specialist implements: Grammar (recognition), Validator
  (validation), and Canonicalizer (derivation). Each domain (e.g. `email/`,
  `date/`, `identifier/`) is its own package sharing the same shape, so adding a
  domain means mirroring, not inventing. Each capability also owns its private
  specifications (PRD §5.3).

- **`src/paxman/_registry/`** — The **frozen roll call** (private). Capabilities
  register before the engine runs; the roster is then frozen for the process
  lifetime. This turns resolution into a closed lookup and guards Determinism
  (PRD §5.4). Capabilities must not import it.

- **`src/paxman/execution_results/`** — **Self-describing records**. An execution_result wraps the
  status (SUCCESS, AMBIGUOUS, INVALID, or MISSING), contract, and candidates with
  their provenance so it needs nothing outside itself to be understood or
  replayed. Each candidate carries raw matched value, canonical value after
  canonicalization, and evidence chain (PRD §5.1, §3).

- **Capability-private specifications** — Each capability owns its own
  specifications that define what canonical form means for its domain. These are
  not shared across capabilities (PRD §5.5).
