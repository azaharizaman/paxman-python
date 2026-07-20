# AGENTS.md

Orientation for automated agents operating in this repository.

## Start here

Before doing anything else, read these two documents in full:

- [`README.md`](./README.md) — what Paxman is, its targets (Python 3.11–3.13,
  MIT), project status, and the folder structure with per-folder purpose.
- [`CODING_GUIDELINES.md`](./CODING_GUIDELINES.md) — the enforced rules for
  contributing code: style, typing, testing, and the strict discipline expected.

## What this repo is

Paxman begins as a deterministic canonicalization engine. It is scaffolded but
not yet implemented: the package layout and empty stub files exist under
`src/paxman/`, but no concrete logic has been written.

## How to work here

- Respect the sealed core. The `_engine/` subpackage is owned by Paxman and is not
  an extension point. Do not add behavior there unless the task explicitly
  requires changing the core.
- The only supported extension mechanism is a **capability**. New domains go in
  `src/paxman/capabilities/<domain>/`, mirroring an existing package shape.
- Never weaken the guarantees described in the documentation. If a task seems to
  require guessing, inferring, or external I/O, stop and surface the conflict.
- Follow `CODING_GUIDELINES.md` for every change. Enforced rules are strict.
- Do not create files or folders outside the established layout without reason.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (via the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical roles: `needs-triage`, `needs-info`, `ready-for-agent`,
`ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.
