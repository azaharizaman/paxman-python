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
  capability set, and configuration, Paxman always produces the same artifact.
  No randomness, no clock, no hidden state, no environment leakage.
- **Invariant 3 — Replay.** Every artifact Paxman emits can be handed back and
  reconstructed exactly, without re-running any logic.

## Components (What)

### Engine — the sealed core

The center of the system. A pure, stateless referee that runs a fixed
canonicalization pipeline: receive the input and contract, resolve the single
owning capability, delegate for a verdict, seal the result into an artifact, and
replay when asked. The engine holds no domain opinion and is owned by Paxman.
Concentrating the invariants here is what makes them provable.

### Contracts — the shared language

The declarative, versioned agreement between caller and engine. A contract names
the *kind* of information and may *pin an authority edition*. It carries intent,
never behavior, and is the one surface users touch directly.

### Capabilities — the only extension point

The sole place real domain knowledge lives. A capability declares the contract
kinds it owns and renders a verdict (with evidence) or a refusal. Each domain is
its own package sharing one uniform shape, so extension is mirroring, not
invention. Because the engine is sealed, a broken capability cannot corrupt the
constitution.

### Registry — the frozen roll call

The single place where capabilities declare themselves before the engine runs.
Once the engine begins, the roster is frozen for the life of the process. This
turns resolution into a closed lookup and makes the contract-to-capability
mapping observable — directly guarding Determinism.

### Artifacts — self-describing records

The output of canonicalization. An artifact wraps the verdict, contract, and
authority choices so it needs nothing outside itself to be understood or
replayed. Evidence accompanies a canonical verdict so trust and reconstruction
need no re-execution. Refusal is stored here as a first-class result.

### Authorities & Editions — truth as published

Real-world standards bodies (ISO, RFC, Unicode, IANA, …) define what canonical
form means. Paxman defers to them through *editions* — named, pinned references
to specific published standards. Editions let Paxman stay humble (answering to
real authorities) and deterministic (recording exactly which standard was used,
so replay reconstructs against it).

## Why This Shape

- **One sealed core, one open edge.** Invariant-protecting logic lives in exactly
  one place; everything else plugs in through one well-lit door. This is what
  lets the core and the edges evolve independently.
- **Uniform extension shape.** Every capability looks the same. One pattern to
  learn, so the mental model does not grow with the number of domains.
- **No hidden behavior.** Freezing, determinism, and replay are enforced by
  structure, not by prose.
- **Declarative contracts.** Callers describe *what*; capability authors own the
  *how*. The split is what keeps the engine domain-agnostic.
- **Self-describing artifacts.** Output carries its own provenance, so replay
  needs no external context.

The net effect: a newcomer can hold the whole system in their head — engine in
the middle, contracts in, capabilities around the edge, registry keeping order,
artifacts coming out fully described.

## Non-Negotiables

The following are fixed commitments of the architecture. They are not
trade-offs to be revisited; they are the load-bearing walls.

- The engine subpackage remains sealed and domain-agnostic.
- The only extension mechanism is a capability; no other hook exists.
- The registry freezes before the engine runs and stays frozen.
- A verdict is either canonical (with evidence) or a refusal — never a guess.
- Artifacts are self-describing and replayable without re-execution.

## Key-Tradeoff

*Reserved.* No key trade-offs are accepted at this stage; the architecture is
intentionally minimal and the invariants take precedence over every convenience.
This section will document explicit trade-offs only if and when the roadmap
(PRD §11) expands Paxman into deterministic or evidence-guided normalization and
a genuine权衡 must be recorded.
