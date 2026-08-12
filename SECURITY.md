# Security Policy

## Overview

Paxman is a canonicalization authority resolver designed with correctness and safety as core properties. The system enforces strict type checking, immutable data structures, and deterministic computation to prevent common classes of bugs and ensure predictable behavior.

## Reporting a Vulnerability

If you discover a security vulnerability in Paxman, please report it responsibly:

1. **GitHub Issues**: Open an issue on the project's GitHub repository for non-sensitive bugs that could affect correctness or reliability.
2. **Private Disclosure**: For vulnerabilities that could have security implications (e.g., input validation bypass, denial of service through malformed input, or unexpected behavior in provenance handling), please contact the maintainers directly rather than filing a public issue. If no private contact method is available in the repository, open an issue and note that it should be handled privately.

We will acknowledge reports within 72 hours and provide an estimated timeline for a fix.

## Security Measures

Paxman incorporates several design principles that reduce attack surface:

- **Immutable Domain Objects**: All core data structures (Provenance, Candidate, RecognitionMatch, RecognizedRep, VersionStamp) are immutable. Once created, they cannot be modified, preventing state tampering.

- **Strict Type Checking**: The project enforces strict mode static type checking across all layers, catching type-related errors at development time rather than runtime.

- **Deterministic Computation**: Given the same input and contract configuration, the pipeline always yields the same canonical output — no world-knowledge, no clock, no environment-dependent ordering, no fuzzy logic, no network inference across recognition, validation, and canonicalization. This prevents timing-based side channels and ensures reproducibility.

- **Input Validation**: The system distinguishes between MISSING (no recognition), INVALID (recognized but unvalidated), and SUCCESS/AMBIGUOUS states, ensuring untrusted input is never silently accepted without authoritative validation.

- **Capability Isolation**: Capabilities cannot import from each other, limiting the blast radius of any issues within a single domain module.

## Scope

This security policy covers the Paxman library itself, including:

- Grammar recognition logic
- Validation rule implementations
- Core domain object integrity
- Capability registration and discovery

This policy does not cover third-party specifications or authoritative sources that Paxman references. Provenance citations are informational and do not imply endorsement of external content.

## Supported Versions

Security fixes are applied to the latest released version. Users are encouraged to upgrade to the most recent release to benefit from security patches and correctness improvements.
