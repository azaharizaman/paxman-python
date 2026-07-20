"""Paxman — a deterministic canonicalization library.

Root package and the ONLY public re-export surface (see ADR 0001). Begins as a
deterministic canonicalization engine (see PRD §1, §11). Internal packages use a
leading underscore (_engine, _registry) to signal they are not extension points;
capabilities, contracts, artifacts, and authorities are the open edge and shared
services. Nothing outside this package should import an internal module directly.
"""
