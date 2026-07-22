# Architecture

This document describes Paxman's architecture at a high level: **what** the
system is made of and **why** it is shaped that way. It deliberately avoids
*how* — implementation, code, and algorithms belong to the engineering phase,
not here.

The authoritative product context is [`PRD.md`](./PRD.md). This document is the
architectural companion to it.

## Purpose

Paxman begins as a deterministic canonicalization engine. Its job is to rewrite
information that is *unambiguously* equivalent into a single, agreed canonical
form, and to refuse — explicitly — when the input does not determine a unique
result. The architecture exists to make that guarantee structural, not
documentary.

## The Three Invariants

Every component below is justified by its role in preserving the three
invariants defined in the PRD (§3). They are the constitution; nothing may break
them.

- **Invariant 1 — Boundary.** Paxman canonicalizes only. It never speculates
  beyond what the input and its contract jointly determine, and it never infers
  information not already present.
- **Invariant 2 — Determinism.** For a given input, contract, registered
  capability set, and configuration, Paxman always produces the same execution_result.
  No randomness, no clock, no hidden state, no environment leakage.
- **Invariant 3 — Replay.** Every execution_result Paxman emits can be handed back and
  reconstructed exactly, without re-running any logic.

## Components (What)

### Engine — the sealed core (`_engine/`)

The center of the system. A pure, stateless referee that runs a fixed
canonicalization pipeline: receive the input and contract, resolve the single
owning capability, delegate for a verdict, seal the result into an execution_result, and
replay when asked. The engine holds no domain opinion and is owned by Paxman.
Concentrating the invariants here is what makes them provable. Its package carries
a leading underscore to signal it is not an extension point.

### Contracts — the shared language

The declarative, versioned agreement between caller and engine. A contract names
the *kind* of information and may *pin an authority edition*. It carries intent,
never behavior, and is the one surface users touch directly.

### Capabilities — the only extension point

The sole place real domain knowledge lives. A capability declares the contract
kinds it owns and contains the full pipeline for canonicalization: Grammar
(recognition), Validator (validation), and Canonicalizer (derivation). Each
domain is its own package sharing one uniform shape, so extension is mirroring,
not invention. Because the engine is sealed, a broken capability cannot corrupt
the constitution.

### Registry — the frozen roll call (`_registry/`)

The single place where capabilities declare themselves before the engine runs.
Once the engine begins, the roster is frozen for the life of the process. This
turns resolution into a closed lookup and makes the contract-to-capability
mapping observable — directly guarding Determinism. Like the engine, its package
carries a leading underscore to signal it is not an extension point.

### ExecutionResults — self-describing records

The output of canonicalization. An execution_result wraps the status (SUCCESS,
AMBIGUOUS, INVALID, or MISSING), contract, and candidates with their provenance
so it needs nothing outside itself to be understood or replayed. Each candidate
carries raw matched value, canonical value after canonicalization, and evidence
chain. The result is self-contained for replay.

### Specifications — capability-private truth

Each capability owns its own specifications that define what canonical form
means for its domain. Specifications are capability-private (not shared across
capabilities) and carry authority information inside them. A specification
contains code, name, authority (who published it), effective context, base
version, and citations that define what sections of the spec are used for
matching.

Specifications are immutable units of truth within their capability. They carry
published fact — no logic, no parsing, no policy application lives inside them.
A capability cites specifications and adopts them **wholly**: when Paxman honors
a specification, it honors all of it. There is no partial adoption — picking and
choosing which entries of a standard to accept would make the output
untrustworthy and would break the promise that Paxman answers to real
authorities rather than inventing its own.

## Why This Shape

- **One sealed core, one open edge.** Invariant-protecting logic lives in exactly
  one place; everything else plugs in through one well-lit door. This is what
  lets the core and the edges evolve independently.
- **Uniform extension shape.** Every capability looks the same: Grammar, Validator,
  Canonicalizer. One pattern to learn, so the mental model does not grow with
  the number of domains.
- **No hidden behavior.** Freezing, determinism, and replay are enforced by
  structure, not by prose.
- **Declarative contracts.** Callers describe *what*; capability authors own the
  *how*. The split is what keeps the engine domain-agnostic.
- **Self-describing execution_results.** Output carries its own provenance, so replay
  needs no external context.
- **Capability-private specifications.** Each capability owns its truth,
  preventing drift across domains.

The net effect: a newcomer can hold the whole system in their head — engine in
the middle, contracts in, capabilities around the edge with their own
specifications, registry keeping order, execution_results coming out fully
described.

## Guardrails (Why they exist)

The architecture above is only trustworthy if it is enforced, not merely
described. Paxman therefore relies on a layer of tooling that constrains
*structure* and *behavior*, not just style. The rationale for each:

- **Strict typing (MyPy, `strict` mode).** Removes the "it works" shortcuts that
  erode architecture — no `Any` escapes, no implicit optionals, no untyped
  definitions. Types become the contract an agent cannot silently violate.
- **Protocol-based interfaces.** Every extension point is defined by an explicit
  interface contract (for example the capability interface, grammar protocol,
  validator protocol, canonicalizer protocol, and later the registry
  and execution_result-store interfaces). An agent that drifts from the interface fails
  type checking rather than compiling into drift.
- **Import contracts (Import Linter).** Encodes the sealed-core / open-edge
  boundary as a CI failure: capabilities never import the core; the core never
  imports concrete domains; capabilities keep their specifications private. This is the
  single most effective defense against architectural erosion.
- **Property-based tests (Hypothesis).** Encode invariants — "equivalent inputs
  yield the same canonical form" — instead of example lists, so behavioral drift
  surfaces as a property violation.
- **Private internal packages.** The sealed core uses a leading underscore
  (`_engine/`, `_registry/`) so contributors and agents can see at a glance what
  is not an extension point.

These guardrails are chosen to discourage architectural drift during agentic
coding specifically: explicit contracts and import boundaries are respected far
more reliably than prose instructions. Details live in `pyproject.toml`,
`.importlinter`, and `docs/adr/0001-sealed-core-open-edge.md`.

## Non-Negotiables

The following are fixed commitments of the architecture. They are not
trade-offs to be revisited; they are the load-bearing walls.

- The `_engine` and `_registry` subpackages remain sealed, private, and
  domain-agnostic; capabilities never import them.
- The only extension mechanism is a capability; no other hook exists.
- The registry freezes before the engine runs and stays frozen.
- A result is either canonical (with candidates) or has a clear status (INVALID,
  MISSING, AMBIGUOUS) — never a guess.
- ExecutionResults are self-describing and replayable without re-execution.
- Specifications are capability-private: each capability owns its own
  specifications, never sharing across domains.
- A specification is pure published truth and is adopted wholly — never
  partially. Citing a standard means honoring all of it.

## Key-Tradeoff

*Reserved.* No key trade-offs are accepted at this stage; the architecture is
intentionally minimal and the invariants take precedence over every convenience.
This section will document explicit trade-offs only if and when the roadmap
(PRD §11) expands Paxman into deterministic or evidence-guided normalization and
a genuine权衡 must be recorded.
