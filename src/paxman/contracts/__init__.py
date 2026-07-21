"""Contracts subpackage — the shared, declarative language between caller and engine (PRD §5.2).

A contract names the kind of information and optionally pins an authority
edition. Declarative and versioned; the one surface users touch directly.
"""

from paxman.contracts.authority_pin import AuthorityPin
from paxman.contracts.contract import Contract
from paxman.contracts.kind import Kind
from paxman.contracts.refusal import Refusal
from paxman.contracts.verdict import Verdict

__all__ = [
    "AuthorityPin",
    "Contract",
    "Kind",
    "Refusal",
    "Verdict",
]
