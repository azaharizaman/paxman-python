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
| deterministic   | Same input + contract + capabilities + config → same execution_result.|
| capability      | The only extension point; owns contract kinds, renders verdict/refusal. |
| contract        | Declarative, versioned agreement naming the kind + optional authority pin. |
| authority       | Immutable identity of a real-world publisher (ISO, IETF, Unicode…). Has `code` and `name`. Does not know about editions. |
| specification   | A specific publication or registry published by an authority. Has `authority`, `code`, and `name`. Absorbs Edition via `effective_context` and `base_version`. |
| citation        | Reference to a specific part of a specification that justifies a transformation. Has `section`, `title`, `citation_type`. |
| specification_reference | Citation that explains why one transformation step is trustworthy. Has `authority`, `spec`, `operation`, `citation`. |
| provenance      | Collection of all sources that justified the canonicalization. |
| edition         | A pinned, named revision of a specification. Absorbed into Specification via `effective_context` and `base_version` (no separate class). |
| verdict         | A capability's canonical result: canonical form + evidence. One of the two outcomes in the duality. |
| refusal         | A first-class, reasoned statement that no unique form exists. One of the two outcomes in the duality. |
| execution_result | The self-describing, replayable record the engine seals. Wraps contract + (Verdict | Refusal) + config_digest. |
| replay          | Reconstruct an execution_result exactly, with no re-execution.         |
| sealed core     | `_engine/` + `_registry/` — private, owned by Paxman.          |
| invariant       | One of Boundary, Determinism, Replay — the constitution.       |

Do not drift to synonyms these terms explicitly avoid (e.g. do not call a
verdict an "error" or "failure"; do not call canonicalization "normalization"
at this stage — that is a later roadmap concern).
