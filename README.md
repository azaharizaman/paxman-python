# Paxman

**A deterministic canonicalization library.**

Paxman begins as a deterministic canonicalization engine (see [`PRD.md`](./PRD.md)).
It rewrites information that is *unambiguously* equivalent into a single, agreed
canonical form — and refuses to guess when the input does not determine a unique
result. Paxman does not normalize, infer, orchestrate, or improvise. It makes the
determinable determinable, consistently, forever.

- **One form, agreed by all** — same logical input, same canonical output, every time.
- **No silent guessing** — ambiguity is refused explicitly, with reason.
- **Perfect recall** — every artifact replays to itself byte-for-byte.

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
src/paxman/                      # The Paxman library package (root).
├── engine/                      # The sealed, fixed core. Owned by Paxman; not extensible.
├── contracts/                   # The declarative, versioned shared language (caller ↔ engine).
├── capabilities/                # The ONLY extension point. One package per domain.
│   ├── email/                   # Example domain: email address canonicalization.
│   ├── date/                    # Example domain: date canonicalization.
│   └── identifier/              # Example domain: unique identifier canonicalization.
├── registry/                    # The frozen roll call that maps contracts to capabilities.
├── artifacts/                   # Self-describing, replayable records of a canonicalization.
└── authorities/                 # Real-world standards bodies and their pinned editions.
```

### Folder descriptions

- **`src/paxman/`** — The library root package. Exposes the public surface
  (`canonicalize(...)`) and aggregates the subpackages below. This is the only
  import boundary users and extenders rely on.

- **`src/paxman/engine/`** — The **sealed core**. A pure, stateless referee that
  runs the fixed canonicalization pipeline (Receive → Resolve → Delegate → Seal →
  Replay). It holds no domain opinion and is owned by Paxman; contributors do not
  modify it. This is where the three invariants are concentrated (PRD §5.1).

- **`src/paxman/contracts/`** — The **shared language** between caller and engine.
  A contract is declarative and versioned: it names the *kind* of information and
  optionally *pins an authority edition*. It carries no behavior — the caller
  states intent, never how (PRD §5.2).

- **`src/paxman/capabilities/`** — The **only extension point**. A uniform
  interface every domain specialist implements: declare owned contract kinds, then
  render a verdict (with evidence) or a refusal. Each domain (e.g. `email/`,
  `date/`, `identifier/`) is its own package sharing the same shape, so adding a
  domain means mirroring, not inventing (PRD §5.3).

- **`src/paxman/registry/`** — The **frozen roll call**. Capabilities register
  before the engine runs; the roster is then frozen for the process lifetime. This
  turns resolution into a closed lookup and guards Determinism (PRD §5.4).

- **`src/paxman/artifacts/`** — **Self-describing records**. An artifact wraps the
  verdict, contract, and authority choices so it needs nothing outside itself to
  be understood or replayed. Includes the evidence that lets replay reconstruct a
  result without re-execution (PRD §5.1, §3).

- **`src/paxman/authorities/`** — **Truth as published**. Models real-world
  authorities (ISO, RFC, Unicode, IANA, …) and their named, pinned *editions*, so
  Paxman can defer to genuine standards while staying reproducible (PRD §5.5).
