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
  types (e.g. `Resolution` with SUCCESS, AMBIGUOUS, INVALID, MISSING), not escapes.
- Type checks must pass with zero errors. Typing is treated as a build gate.

## Determinism (non-negotiable)

- No hidden state. No module-level mutable globals that affect a result.
- No clock, randomness, network, or ambient-environment dependence in any path
  that produces an execution_result. Capabilities may depend only on their input and
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

## Specifications (non-negotiable)

- Specifications are capability-private under each capability's `specs/` directory.
  Each capability owns its own specifications; they are not shared across capabilities.
- A specification's metadata is pure published truth: its `code`, `name`,
  `authority`, `effective_context`, and `base_version` contain no parsing logic,
  no policy application, no behavioral code. The metadata describes what the
  specification is, not what to do with it.
- A specification contains `CitationMatching` entries that define validation
  rules. Each `CitationMatching` may carry a `match()` method implementing the
  matching logic (e.g., `table_lookup`, `regex_matching`). This is the bridge
  between spec data and validation behavior — it lives inside the specification
  because it IS the spec's validation clause, not arbitrary capability logic.
- When a capability cites a specification, it adopts that specification **wholly**.
  Partial adoption of a standard (accepting some entries while rejecting others)
  is forbidden — it would make the output untrustworthy and contradict the promise
  that Paxman answers to real authorities. Cite a specification, or do not; never
  selectively honor it.

## Error Handling

- Ambiguity is expressed as a `Resolution` status (AMBIGUOUS, INVALID, or
  MISSING), not by raising a generic exception or by guessing. These are
  first-class results.
- No empty `except:` blocks. Catch specific exceptions; let the rest propagate.

## Structure & Layout

- Follow the established `src/paxman/` layout. One package per capability domain.
- Each capability contains: `grammar.py` (recognition), `validator.py`
  (validation), `canonicalizer.py` (derivation), and `specs/` (capability-private
  specifications).
- New domains mirror an existing capability package; they do not invent a new
  architecture.
- Do not create files or directories outside the established layout without
  explicit reason.

## Testing

- Every behavior change ships with tests. Tests must be deterministic: same input,
  same outcome, on any machine, on any day.
- Replay must be covered: a produced execution_result reconstructs exactly, with no
  re-execution.

## Style

- Formatting and linting are enforced by the project toolchain (configuration to
  be added). Do not commit reformatted-by-hand code that conflicts with it.
- Keep modules focused. A capability contains exactly three things: Grammar
  (recognition), Validator (validation), and Canonicalizer (derivation), plus its
  private specifications.

## Documentation

- Public types and functions carry docstrings stating purpose, not implementation.
- Do not weaken guarantees in prose. If wording and code disagree, the code is
  wrong until reconciled with the design documents.
