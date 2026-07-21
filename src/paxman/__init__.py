"""Paxman — a deterministic canonicalization library.

Root package and the ONLY public re-export surface (see ADR 0001). Begins as a
deterministic canonicalization engine (see PRD §1, §11). Internal packages use a
leading underscore (_engine, _registry) to signal they are not extension points;
capabilities, contracts, artifacts, and authorities are the open edge and shared
services. Nothing outside this package should import an internal module directly.
"""

from paxman._engine.engine import Engine, EngineConfig
from paxman._registry.registry import Registry
from paxman.contracts.contract import Contract
from paxman.contracts.kind import Kind
from paxman.contracts.refusal import Refusal
from paxman.contracts.verdict import Verdict

__all__ = [
    "Contract",
    "Engine",
    "EngineConfig",
    "Kind",
    "Refusal",
    "Registry",
    "Verdict",
]
