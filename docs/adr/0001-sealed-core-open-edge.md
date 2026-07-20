# ADR 0001 — Sealed Core, Open Edge, and Dependency Rules

- **Status:** Accepted
- **Date:** 2026-07-21
- **Deciders:** Paxman authors

## Context

Paxman begins as a deterministic canonicalization engine. Its value is entirely
in its guarantees — Boundary, Determinism, Replay (PRD §3). Those guarantees are
easy to erode accidentally: an AI coding agent or a well-meaning contributor can
quietly import the wrong module, reach into the core, or bundle an authority's
table into a capability. Python's flexibility makes this likely unless the
architecture is enforced structurally, not just described in prose.

We need a rule set that (a) keeps the invariant-protecting logic in exactly one
place, (b) makes the only extension point explicit, (c) prevents the sealed core
from being imported by extensions, and (d) keeps authorities as shared, read-only
truth that no one copies or partially adopts.

## Decision

### 1. Two-layer package boundary

- **Sealed core (private).** `src/paxman/_engine/` and `src/paxman/_registry/`
  carry the underscore prefix to signal "not an extension point." They are owned
  by Paxman; contributors do not modify them.
- **Open edge (public extension).** `src/paxman/capabilities/` is the only place
  real domain knowledge lives. Each domain is its own package sharing one shape.

Shared types (`contracts/`, `artifacts/`) and the shared service (`authorities/`)
are neither core nor extension; they are depended upon by both sides.

### 2. Dependency direction is enforced, not advised

The Import Linter contracts in `.importlinter` encode:

- Capabilities **must not** import `_engine` or `_registry`. The engine calls
  capabilities through the `Capability` Protocol; the reverse edge is forbidden.
- `_engine` **must not** import concrete capability domains. It depends only on
  shared types, the frozen `_registry`, and the `Capability` Protocol.
- `authorities/` **must not** import any internal Paxman package — editions are
  pure published truth.
- `contracts/` and `artifacts/` stay leaf-only (no internal imports).

CI fails if any of these relationships is introduced.

### 3. Authorities are a shared, read-only service

An authority edition is stored once under `authorities/<authority>/` and
referenced by every capability that needs it. A capability MUST NOT bundle,
copy, or re-implement an authority's table. An edition file contains pure
published fact only — no parsing, no policy, no behavior. When a capability cites
an edition, it adopts it **wholly**; partial adoption is forbidden.

### 4. One public entry point

`src/paxman/__init__.py` is the only intended re-export surface. Internal
packages are reached through it, not imported directly by consumers.

### 5. Type and interface discipline

- `mypy` runs in `strict` mode: no `Any` escapes, no implicit optionals, no
  untyped defs. This removes the most common AI-slop shortcuts.
- Extension points are `typing.Protocol` interfaces (`Capability`, and later
  `Registry`, artifact store), so an agent that violates the contract fails type
  checking rather than silently drifting.
- Core data uses `@dataclass(frozen=True, slots=True)` — no Pydantic, no runtime
  type checking (beartype/typeguard avoided). Types are proven at build time.

### 6. Behavioral invariants via property tests

`hypothesis` encodes invariants (e.g. `canonicalize(x) == canonicalize(y)` for
equivalent inputs) rather than example lists, so drift is caught as a property
violation.

## Consequences

**Positive**
- The architecture is enforceable in CI; prose cannot drift from reality.
- AI agents get explicit contracts and import boundaries, which they respect far
  more reliably than instructions alone.
- Authorities cannot be partially adopted or duplicated; provenance stays
  consistent across capabilities.
- Zero runtime dependencies in the core; the library stays portable and auditable.

**Negative / costs**
- Stricter tooling means more friction for casual contributions (intentional).
- Renaming `engine/`/`registry/` to `_engine/`/`_registry/` was a one-time change
  to the scaffold; all future references must use the private names.
- Import Linter contracts must be maintained as the architecture evolves; a new
  forbidden edge requires an explicit ADR amendment, not a silent edit.

## Confirmation

This ADR is confirmed by: `pyproject.toml` (strict ruff/mypy, import-linter,
hypothesis), `.importlinter` (the contracts above), and `ARCHITECTURE.md`
(authorities as shared read-only service; whole-edition adoption). Any change to
these rules requires a new ADR.
