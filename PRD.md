# Paxman — Product Requirements Document

*Written as if on day zero. Informed by where Paxman is heading.*

---

## 1. Vision

The world is full of data that means the same thing but looks different. The same
email address is written with mixed casing, with surrounding whitespace, with
comments appended. The same calendar date appears as `07/20/2026`, as
`2026-07-20`, as `20 Jul 2026`, as a Unix timestamp. The same monetary amount is
written with a currency symbol, with a three-letter code, with or without
thousands separators.

Every system that receives this data has to decide: *which form is the right
form?* Today that decision is re-litigated inside every application, every
pipeline, every integration. Each team writes its own normalization. Each team
makes subtly different choices. The result is drift: two systems that should
agree do not, and nobody can say which one is correct.

Paxman exists to end that drift.

**Paxman begins as a deterministic canonicalization engine.** It takes information that
is *unambiguously* equivalent and rewrites it into a single, agreed canonical
form — and it refuses to guess when the input does not determine a unique
result. Where other tools *speculate*, Paxman *canonicalizes*. It does not
infer meaning that is not present. It does not orchestrate. It does not
improvise. It makes the determinable determinable, consistently, forever.

---

## 2. The Promise

Paxman promises three things to everyone who depends on it:

1. **One form, agreed by all.** Feed Paxman the same logical input from two
   different starting shapes, and it will produce the exact same canonical
   output every time, everywhere.

2. **No silent guessing.** When the input is ambiguous — when more than one
   canonical reading is possible — Paxman says so explicitly rather than
   picking one and hoping. Refusing is a feature, not a failure.

3. **Perfect recall.** Any canonical execution_result Paxman produces can be replayed
   back into Paxman and reproduced byte-for-byte, with no re-execution and no
   loss. The execution_result is self-describing and trustworthy on its own.

Paxman is not a parser. It is not a formatter. It is not a general-purpose
transformation library. It is the single, principled authority for *"given
this kind of determinable information, what is the one right shape it should
take?"*

---

## 3. The Three Invariants

These invariants are not features. They are the constitution. Every decision,
every line, every extension to Paxman must preserve them. If a change breaks an
invariant, the change is wrong, no matter how convenient.

### Invariant 1 — Boundary

Paxman canonicalizes only. It never speculates beyond what the input and its
contract jointly determine. It never infers information that is not already
present. It never orchestrates, decides business meaning, or invents structure.
The boundary of what Paxman does is *rewrite the determinable into the agreed
shape.*

### Invariant 2 — Determinism

For a given input, contract, set of registered capabilities, and configuration —
Paxman always produces the same execution_result. There is no randomness, no clock
dependence, no hidden state, no environment leakage. Same in, same out, on any
machine, on any day. Determinism is a property of the library itself, not an
option you opt into.

### Invariant 3 — Replay

Every execution_result Paxman emits can be handed back to Paxman and reconstructed
exactly, without re-running any logic. The execution_result carries everything needed to
reproduce itself. Replay is not a reconstruction from memory; it is a faithful,
byte-for-byte return to the original.

---

## 4. Who Paxman Is For

Paxman serves three audiences, and the design honors all three.

- **Users** — engineers and systems that need a trustworthy, repeatable
   canonical form for determinable kinds of data, without building that logic
   themselves.
- **Extenders** — contributors who want to teach Paxman a new *kind* of
   information whose canonical form is uniquely determined (a new domain of
   canonicalization).
- **Forks** — teams who want to take Paxman and build a purpose-specific variant
  under their own direction, without fighting the architecture to do so.

A good architecture is one that serves the user, welcomes the extender, and
frees the forker. Paxman is built so that all three are first-class.

---

## 5. Proposed Architectural Design

Paxman is deliberately small at its core and deliberately open at its edges. The
design separates *what is fixed* from *what is extensible* so sharply that each
side can evolve without disturbing the other.

### 5.1 The Engine (fixed, owned, sealed)

At the center sits the engine. If Paxman were a courtroom, the engine would be
the bench: it never argues a case, it never invents the law, and it never
whispers to one side. It receives what is brought before it, confirms the law
applies, asks the right specialist to render a verdict, records that verdict
word-for-word, and can read the verdict back verbatim years later. The engine is
the unchanging frame inside which all change is permitted.

We spent many cycles refactoring to find the engine's true shape, and the
aspired sweet spot looks like this.

**The engine is a pure, stateless referee.** It holds no opinion about email or
dates or money. It holds only the rules of engagement. Given an input and a
contract, it performs a fixed sequence of moves, and that sequence is the entire
job of Paxman:

1. **Receive.** Take the raw input and the contract that names its kind.
2. **Resolve.** Ask the registry, deterministically, which single capability
   has declared that it owns this contract. There is no scoring, no ranking, no
   "best match" — exactly one capability claims it, or the engine reports that
   none does.
3. **Delegate.** Hand the input and contract to that capability and receive back
   a structured verdict: either a canonical form with the evidence that produced
   it, or an explicit refusal with the reason why no unique form exists.
4. **Seal.** Wrap the verdict, the contract, and the authority choices into a
   self-describing execution_result — a record that needs nothing outside itself to be
   understood or replayed.
5. **Replay.** Given that execution_result and the same contract, reproduce it exactly,
   without ever re-invoking the capability. Replay is reading the sealed record,
   not re-running the trial.

What makes this the sweet spot is not any single move but the *discipline of the
frame*. The engine is intentionally boring. It contains no branching that
depends on which domain is being canonicalized. It knows nothing about casing,
time zones, or currency. All of that lives elsewhere, behind the one door. This
is why the engine can be sealed: there is nothing inside it worth forking, and
nothing inside it that could drift. The invariants — Boundary, Determinism,
Replay — are not sprinkled across the system; they are *concentrated* in this
one component, and concentration is what makes them provable.

The engine is **owned by Paxman**. Contributors do not rewrite the pipeline.
They do not redefine how verdicts are rendered or how execution_results are sealed. This
is not a limitation — it is the guarantee. Because the frame is sealed, every
extension that plugs into it inherits the three invariants for free, and a
broken extension cannot quietly corrupt the constitution.

### 5.2 Contracts (the shared language)

A *contract* is the agreement between caller and engine. If the engine is the
bench and the capability is the expert witness, the contract is the charge
sheet: it states, in plain terms, what kind of thing is being brought forward.
The caller does not describe *how* to judge it; that would be writing law, and
the caller is not the law. The caller only declares *what* it is.

Concretely, a contract carries one kind of information:

- **The kind.** It names the category of information being canonicalized — this
  is what lets the engine resolve which single capability owns the case. The
  contract is the key to the lookup; without it, the engine would not know which
  door to open.

The contract is **declarative and versioned**. Declarative means the caller
states intent, never behavior — the how lives entirely with the capability
author. Versioned means a contract has an identity Paxman can reason about over
time; as specifications evolve, the contract model can grow without breaking
callers who depend on an earlier shape.

This is what makes the public surface stable and predictable. A caller learns
the contract model once and can canonicalize any supported kind of information
the same way, because every domain speaks through the same declarative
vocabulary. The contract is the one piece of Paxman a user touches directly, so
it is designed to be the simplest possible thing: *name the kind, and step
back.*

### 5.3 Capabilities (the only extension point)

Everything Paxman *knows how to canonicalize* lives behind a single, uniform
interface: a **capability**. The capability is the specialist the engine calls
to the stand — the only place where real domain knowledge is allowed to live. If
the engine is the bench, the capability is the expert witness: it knows
everything about its one subject and nothing about the others.

The aspired shape of a capability is small, honest, and complete. A capability
contains three components and nothing more.

**First, it declares what it owns.** At registration time, a capability makes a
clean, deterministic claim of the contract kinds it answers for — not a
confidence score, not a heuristic. The registry collects these claims into a
fixed table, so that at run time the engine's Resolve step is a pure lookup, not
a negotiation: it reads the table, finds the one capability that claimed this
contract, and calls it. A capability owns its contract kind, and it owns it
wholly — claims do not overlap, so there is never a tie to break.

**Second, it contains the pipeline for canonicalization.** Given an input and
the contract it owns, the capability runs a fixed sequence:

1. **Grammar (recognition).** The Grammar recognizes patterns in the input and
   produces RecognizedRep objects. Each RecognizedRep carries traceability
   information (grammar_id, grammar_pattern, raw value, shape, captures) so the
   processing chain is fully auditable.

2. **Validator (validation).** The Validator takes the RecognizedRep objects and
   validates them against the capability's private specifications. It collects
   evidence for each candidate, recording which specification sections were
   matched and what operations were performed.

3. **Canonicalizer (derivation).** The Canonicalizer takes the candidates from
   the Validator and derives canonical values for each. It checks for agreement
   among candidates and produces the final ExecutionResult with appropriate
   status (SUCCESS, AMBIGUOUS, INVALID, or MISSING).

The capability never reaches outside itself for the answer. It does not call a
service, consult a clock, or read ambient state. Its output depends only on the
input and the contract. That is what makes its output *deterministic* and its
evidence *sufficient* — given the same two things, it always returns the same
result with the same evidence, and the evidence is enough to reproduce it.

**Third, it owns its specifications.** Each capability contains private
specifications that define what canonical form means for its domain. These are
not shared across capabilities — each domain owns its truth. Specifications are
immutable units of published fact that the capability adopts wholly.

Capabilities are organized one package per domain. The contract kinds Paxman is
built to serve span the everyday categories of determinable information —
addresses, dates, unique identifiers, and the like — and the shape of each
capability package is identical across all of them. Adding a new domain means
copying that shape, not inventing a new architecture.

This is the heart of Paxman's extensibility: **the only thing you are allowed to
add is a capability, and the path for adding one is already paved.** There is no
secret hook, no special-case escape hatch, no fork-the-core requirement. The
capability is the whole game for an extender — and because the engine is sealed,
the extender cannot accidentally break the constitution while playing it.

### 5.4 The Registry (safe by construction)

The registry is the roll call. It is the single place where capabilities declare
themselves before any case is heard, and it is what turns the engine's Resolve
step from a negotiation into a lookup. A capability that is not on the roll
cannot be called to the stand; a capability that is on it is the only one who may
answer for the contract it claims.

The registry has one rule, and the rule is the whole point: **capabilities are
registered before the engine runs, and once the engine begins its work the set
of capabilities is frozen.** After that moment, the roster cannot change.

Why this matters is something hard-won. Extensible systems routinely let
capabilities appear, disappear, or reorder while work is in flight, and the
result is the quiet kind of bug that defeats determinism: the same input yields
a different verdict because a different specialist happened to be registered at
the time. By freezing the roster up front, Paxman removes the possibility
entirely. There is no "later," no "this time it was different because something
registered in between." The capability set that judges the first case is the
capability set that judges the last, for the life of the process.

Freezing also makes the contract-to-capability mapping *observable*. Because the
claims do not overlap and the roster is fixed, anyone can list, ahead of time,
exactly which capability owns which contract. Determinism stops being a hope
documented in prose and becomes a property you can see and enforce: the resolve
is a closed, fixed table, not an open-ended search. The registry is the quiet
guardian of Invariant 2 — and because it sits between engine and capability, it
protects the user without ever asking the user to think about it.

### 5.5 Capability-Private Specifications

Each capability owns its own specifications that define what canonical form
means for its domain. Specifications are capability-private — they are not
shared across capabilities. This prevents drift across domains and ensures each
domain owns its truth.

A specification is the recognition that *truth has a publisher*. For any domain
Paxman canonicalizes, there is usually a real-world authority — a standards body,
a specification, a registry — that defines what the canonical form actually is.
But authorities are not frozen in time, and they are not singular. A date has an
ISO form; a country has an ISO code list that gets revised; a currency has an
assigned code table that expands.

Paxman models this explicitly through **specifications** — capability-private
references to published standards. A specification is not a guess about the
future; it is a pinned reference to a specific published standard. And it is
first-class in the system, not a footnote:

- Each capability contains its own `specs/` directory with its private
  specifications.
- Specifications carry authority information inside them (who published it,
  effective context, base version).
- Citations within specifications define what sections are used for matching.

Specifications solve a tension that would otherwise tear the promise apart. On
one hand, Paxman must honor real-world authority — it cannot invent its own
canonical forms. On the other hand, it must be reproducible — the same input
must always yield the same execution_result. If the authority were read live, "same in,
same out" would break the day the standard was revised. Specifications resolve
both at once: Paxman defers to genuine external authority through
capability-private specifications, so replay always reconstructs the result
against the exact same standard.

This is also what keeps a fork honest. A variant that trusts a different
authority does not fork the pipeline to express that — it simply provides
different specifications within its capability. The sealed engine still
guarantees the invariants — Boundary, Determinism, and Replay; only the declared
standard changes. Specifications are how Paxman stays both *humble* (it answers
to real authorities) and *deterministic* (it never quietly changes its answer).

---

## 6. Why This Architecture Is Clean

The architecture earns its cleanliness from a small number of deliberate
choices:

- **One sealed core, one open edge.** The invariant-protecting logic lives in
  exactly one place. Everything else plugs in through one well-lit door.
- **Uniform extension shape.** Every capability looks the same: Grammar,
  Validator, Canonicalizer. There is one pattern to learn, not seventeen.
- **No hidden behavior.** Freezing, determinism, and replay are enforced by
  structure, not by convention or documentation alone.
- **Declarative contracts.** Callers describe *what* they want canonicalized;
  they never write *how*. The how lives with the capability author.
- **Self-describing execution_results.** Output carries its own provenance and can be
  replayed without external context.
- **Capability-private specifications.** Each capability owns its truth,
  preventing drift across domains.

The result is an architecture a newcomer can hold in their head: engine in the
middle, contracts in, capabilities around the edge with their own
specifications, registry keeping order, execution_results coming out the other
side fully described.

---

## 7. Why This Architecture Is Easy to Extend

For a contributor adding a new domain:

- Mirror an existing capability package. The file layout (Grammar, Validator,
  Canonicalizer, specs/), the interface, and the contract shape are already
  established.
- Implement the three components every capability must have. Nothing else is
  required.
- Register the capability before the engine runs. The system handles the rest.

There is no need to understand the engine internals. There is no need to modify
shared code. There is no risk of accidentally breaking another domain, because
capabilities are isolated by contract and own their private specifications. The
blast radius of a new contribution is exactly one package.

For a user consuming Paxman:

- Learn the contract model once.
- Call the canonical entry point.
- Receive an execution_result that is trustworthy and replayable.

The mental model does not grow with the number of supported domains.

---

## 8. Why This Architecture Is Easy to Fork

Paxman is built to be taken. A team that wants a variant — a stricter policy, a
different set of domains, a domain-specific authority — can fork and reshape
without wrestling the core:

- The engine stays intact and continues to guarantee the invariants.
- New or replaced capabilities slot in through the same door every other
  capability uses.
- Contracts and editions let a fork express its own authoritative choices
  without forking the pipeline.
- The sealed core means a fork cannot easily drift into non-deterministic or
  non-replayable territory even by accident.

In other words, forking Paxman gives you a *hardened foundation* rather than a
*starting scramble*. You inherit correctness; you spend your effort on scope.

---

## 9. What Paxman Deliberately Is Not

To protect the invariants and the promise, Paxman refuses certain roles:

- It is not an inference engine. It will not decide what an ambiguous input
  "probably" means.
- It is not a general transformation or ETL framework.
- It is not a network or I/O service. Determinism forbids hidden external
  dependence.
- It is not a business-rules engine. Canonical form is about shape and
  authority, not about what you should *do* with the data.

Saying no here is what keeps Paxman trustworthy.

---

## 10. Success Looks Like

- A caller canonicalizes the same logical input from any of its equivalent
  shapes and receives an identical execution_result.
- An ambiguous input produces an explicit "I will not guess" result, with clear
  reason, rather than a silent wrong answer.
- Any execution_result replays to itself exactly, with no re-execution.
- A new contributor ships a new domain by mirroring one existing package and
  registering it — without touching the engine.
- A fork ships a purpose-built variant on the same sealed, invariant-protecting
  core.

---

## 11. Paxman Roadmap

This PRD was written on day zero, and the vocabulary it chooses is not an
accident. **Paxman deliberately begins with canonicalization rather than general
normalization. Canonicalization is the largest problem that can be solved with
complete determinism from day one.** By restricting itself to transformations
whose canonical result is uniquely determined by the input and contract, Paxman
establishes its architectural invariants — Boundary, Determinism, and Replay —
before attempting broader forms of normalization. As the platform matures,
additional normalization capabilities may be introduced, but only if they
preserve these invariants. **The scope may expand; the guarantees will not.**

### Why canonicalization first

The strategy is a deliberate reduction of scope to protect the product's
identity during its formative years. Suppose someone asks:

> "Can Paxman turn `$100` into `AUD 100.00`?"

On day zero the honest answer is:

> No. There isn't enough information.

That is an incredibly powerful guarantee. The moment Paxman starts "helpfully"
using locale, language, surrounding text, heuristics, or external knowledge, it
has entered a very different engineering problem — one where the clean
boundary between *determined* and *assumed* dissolves. By constraining V1 to
canonicalization, Paxman commits to solving only problems where a single,
objectively correct answer exists.

This also makes the invariants provable rather than aspirational. Contrast the
two framings:

- *"Paxman normalizes."* — which immediately raises: which schema? which
  ontology? which business rules? which confidence threshold?
- *"Paxman canonicalizes."* — and Boundary, Determinism, and Replay fit
  naturally, almost proving themselves.

### Three stages of growth

The product expands in progressively larger steps, each one preserving the
core deterministic model rather than eroding it:

| Stage | Product                       | Guarantee                                              |
| ----- | ----------------------------- | ------------------------------------------------------ |
| 1     | Canonicalization              | 100% deterministic                                     |
| 2     | Deterministic normalization   | Deterministic whenever sufficient evidence exists      |
| 3     | Evidence-guided normalization | Deterministic-first, with optional assisted resolution |

Stage 1 is the day-zero identity. Stage 2 introduces normalization that remains
deterministic wherever the evidence uniquely determines a result. Stage 3 may
add optional, explicitly-assisted resolution for cases that need it — but it is
*deterministic-first*, never probabilistic-by-default.

### A clean API evolution

The same discipline shows up in the surface. Today the operation with the
strongest possible guarantees is:

```text
Paxman.canonicalize(...)
```

Years later, the platform may introduce:

```text
Paxman.normalize(...)
```

which internally may invoke planning, evidence evaluation, multiple
capabilities, adapters, and richer workflows. Users immediately understand
these are different operations with different promises — because the name
carries the guarantee. `canonicalize()` now, `normalize()` much later.

### Future-proofing the wording

Because the roadmap already looks past canonicalization, the PRD is careful
never to say Paxman is *fundamentally* a canonicalization engine — only that it
*begins* as one. Canonicalization is the smallest useful problem that fully
satisfies Paxman's invariants; future capabilities may expand Paxman into
deterministic normalization without weakening them. The document says *starts
here*, not *ends here*, leaving room to grow without ever making a future
version appear to contradict the original vision.

### What this answers for future contributors

This section resolves the questions a newcomer will inevitably ask:

- *Why isn't Paxman solving harder problems?* — because the hard problems break
  the guarantee that makes Paxman worth trusting.
- *Why is it refusing certain inputs?* — because refusing is how it protects
  determinism.
- *Why not use AI / infer / guess?* — because those introduce assumptions the
  contract does not determine.
- *Why is the scope intentionally narrow?* — because a mathematically clean core
  with uncompromising guarantees is the foundation every later capability must
  preserve.

The strategy is stronger than a broader "normalization engine" positioning.
Many projects fail by attacking the general problem first. Paxman instead
establishes a deterministic core, then expands outward only once those
guarantees are firmly established — so every new capability inherits the
constitution rather than negotiating around it.

---

## 12. Closing

Paxman starts, on day zero, with a clear promise and an uncompromising
constitution. The architecture is small where it must be firm and open where it
must grow. It serves the user who wants a trustworthy answer, the contributor
who wants to teach it something new, and the team who wants to take it somewhere
Paxman's authors never imagined — all without sacrificing the one thing that
makes Paxman matter: you can always trust the output, and you can always
reproduce it.
