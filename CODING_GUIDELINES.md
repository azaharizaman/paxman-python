# Coding Guidelines

Enforced rules for contributing to Paxman. These rules are strict; reviewers and
automated agents must treat violations as defects, not style preferences.

Paxman begins as a deterministic canonicalization engine. The discipline that
makes the library trustworthy comes from structure, not convention. The rules
below exist to protect the three invariants (see `ARCHITECTURE.md` and `PRD.md`
§3): **Boundary**, **Determinism**, and **Replay**.

## Language & Targets

- Target Python 3.11, 3.12, and 3.13. Do not use syntax or stdlib features that
  are unavailable on 3.11.
- License is MIT. New source files must carry the project's standard license
  header where the toolchain requires it.

## Typing

- Type hints are mandatory on every public function, method, and class attribute.
- No use of `Any` to silence the type checker. Model uncertainty with precise
  types (e.g. `Verdict | Refusal`), not escapes.
- Type checks must pass with zero errors. Typing is treated as a build gate.

## Determinism (non-negotiable)

- No hidden state. No module-level mutable globals that affect a result.
- No clock, randomness, network, or ambient-environment dependence in any path
  that produces an artifact. Capabilities may depend only on their input and
  contract.
- Resolution must be a pure lookup: exactly one capability owns a contract kind;
  claims must not overlap.

## Sealed Core

- The `_engine/` subpackage is owned by Paxman. Do not add branching that depends
  on which domain is being canonicalized.
- Contributors extend only through `capabilities/`. There is no other hook.

## Source Boundary (non-negotiable)

- Any source file inside `src/` MUST NOT import, depend on, or couple its
  behavior to any file or asset outside of `src/`. The `src/` tree is governed by
  tests, lints, checks, and gates that files outside `src/` cannot guarantee; a
  change in one place may not be reflected or verified in the other. Keep `src/`
  self-contained so its code-level guarantees are enforceable.
- Carve-out: prose references inside docstrings or comments to the design
  documents (PRD.md, ARCHITECTURE.md, docs/adr/*) are permitted. They carry no
  code or import dependency, so they do not create the verification gap this rule
  exists to prevent. They are not kept in sync by tooling and may go stale; that
  is acceptable for documentation pointers.

## Authorities (non-negotiable)

- Authorities are a shared, read-only service under `authorities/`. An authority
  edition is stored once and referenced by any capability that needs it; a
  capability MUST NOT bundle, copy, or re-implement an authority's table.
- An authority edition file contains pure published truth only — no parsing
  logic, no policy application, no behavioral code. Behavior lives in the
  capability that cites the edition.
- When a capability cites an authority edition, it adopts that edition **wholly**.
  Partial adoption of a standard (accepting some entries while rejecting others)
  is forbidden — it would make the output untrustworthy and contradict the promise
  that Paxman answers to real authorities. Cite an edition, or do not; never
  selectively honor it.

## Error Handling

- Ambiguity is expressed as a `Refusal`, not by raising a generic exception or by
  guessing. Refusal is a first-class result.
- No empty `except:` blocks. Catch specific exceptions; let the rest propagate.

## Structure & Layout

- Follow the established `src/paxman/` layout. One package per capability domain.
- New domains mirror an existing capability package; they do not invent a new
  architecture.
- Do not create files or directories outside the established layout without
  explicit reason.

## Testing

- Every behavior change ships with tests. Tests must be deterministic: same input,
  same outcome, on any machine, on any day.
- Replay must be covered: a produced artifact reconstructs exactly, with no
  re-execution.

## Style

- Formatting and linting are enforced by the project toolchain (configuration to
  be added). Do not commit reformatted-by-hand code that conflicts with it.
- Keep modules focused. A capability does exactly two things: declare what it
  owns, and render a verdict or refusal.

## Documentation

- Public types and functions carry docstrings stating purpose, not implementation.
- Do not weaken guarantees in prose. If wording and code disagree, the code is
  wrong until reconciled with the design documents.
