# DEVELOPMENT DOCUMENTS — NON-SHIPPING

**Scope:** This `docs/development/` directory and all of its subfolders contain development-related documents only.

## Status

These documents are **not part of the shipped release** of Paxman. They will not be included in published distributions (sdist/wheel) or any release artifact.

## Maintenance Disclaimer

- These documents may **drift out of sync** with the actual implementation as Paxman evolves.
- It is **not the maintainers' responsibility** to keep these documents accurate or up to date.
- These documents may be **removed at any time** without notice or a migration path.

## Hard Guidance for Code and Docs

Any code file, inline documentation, docstring, or other documentation in the repository
(including files outside this directory) **must NOT** reference these documents — neither by
filename nor by quoting or paraphrasing any part of their contents.

Treat the contents of `docs/development/` as ephemeral working notes that may disappear or
become stale. Do not create dependencies on them.

## Not Authoritative

These documents do **not** define the project's overall architecture. For architecture-related
documentation, refer to `ARCHITECTURE.md`.

These documents do **not** record decisions that persist beyond the scope of the file or the
development stage in which the document is considered active. For decisions persisted across the
project's lifetime, refer to the ADRs in `docs/adr/`.

Once an implementation has landed, the documents in this folder and its subfolders are considered
**outdated**.

## PR Review Policy

PR reviewers **must skip** the documents in this folder and its subfolders when writing review
comments, **except** in the following cases:

- The implementation for the particular file in question has **not yet landed**.
- The reviewer is **specifically requested** to review one or more of these files.
- The reviewer **cites** these documents solely to clarify a point they are making (not as
  authoritative or binding guidance).
