"""Artifacts subpackage — self-describing, replayable records of a canonicalization (PRD §5.1, §3).

An artifact carries the verdict, contract, and authority choices; nothing
outside itself is needed to understand or replay it.
"""

from paxman.artifacts.artifact import Artifact
from paxman.artifacts.evidence import Evidence

__all__ = [
    "Artifact",
    "Evidence",
]
