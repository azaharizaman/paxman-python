# CONTEXT.md

Domain context for Paxman. This is a single-context repo; the canonical domain
vocabulary and decisions live in the documents below. Read the relevant one
before exploring or changing the codebase.

## Authoritative sources

- **[`PRD.md`](./PRD.md)** — product requirements: vision, the three invariants
  (Boundary, Determinism, Replay), the architecture (§5), and the roadmap
  (canonicalization first, normalization later).
- **[`ARCHITECTURE.md`](./ARCHITECTURE.md)** — high-level architecture: what and
  why, the guardrails, non-negotiables.
- **[`docs/adr/`](./docs/adr/)** — Architecture Decision Records. Start with
  [`0001-sealed-core-open-edge.md`](./docs/adr/0001-sealed-core-open-edge.md).

## Core vocabulary (use these terms exactly)

| Term            | Meaning                                                        |
| --------------- | ------------------------------------------------------------- |
| canonicalize    | Rewrite unambiguously-equivalent input into one agreed form.  |
| deterministic   | Same input + contract + capabilities + config → same artifact.|
| capability      | The only extension point; owns contract kinds, renders verdict/refusal. |
| contract        | Declarative, versioned agreement naming the kind + authority pin. |
| authority       | Real-world publisher of canonical form (ISO, RFC, Unicode, IANA…). |
| edition         | A pinned, named version of an authority.                      |
| verdict         | A capability's canonical result, carried with evidence.       |
| refusal         | A first-class, reasoned statement that no unique form exists. |
| artifact        | The self-describing, replayable record the engine seals.       |
| replay          | Reconstruct an artifact exactly, with no re-execution.         |
| sealed core     | `_engine/` + `_registry/` — private, owned by Paxman.          |
| invariant       | One of Boundary, Determinism, Replay — the constitution.       |

Do not drift to synonyms these terms explicitly avoid (e.g. do not call a
verdict an "error" or "failure"; do not call canonicalization "normalization"
at this stage — that is a later roadmap concern).
