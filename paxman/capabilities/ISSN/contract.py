"""ISSN contract configuration."""

from dataclasses import dataclass, field
from typing import ClassVar

from paxman.core.contract import CapabilityContract


@dataclass(frozen=True)
class ISSNContract(CapabilityContract):
    """Contract for the ISSN capability."""

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "hyphenated"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset({"compact", "urn"})

    capability_name: str = field(default="issn", init=False)
