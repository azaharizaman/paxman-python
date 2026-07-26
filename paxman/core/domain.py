from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum
from typing import Any

from paxman.core.contract import Contract


class RuleStrategy(Enum):
    """Validation strategy for a rule."""

    REGEX = "regex"
    LOOKUP_TABLE = "lookup_table"
    PARSER = "parser"


class Resolution(Enum):
    """Status of the canonicalization execution."""

    MISSING = "missing"
    INVALID = "invalid"
    SUCCESS = "success"
    AMBIGUOUS = "ambiguous"


# Notation type — capability-defined, but list[str] is the generic contract.
# For capability-specific Notation, use a TypedDict or dataclass to capture
# positional semantics.
Notation = list[str]


class Provenance:
    """Authority citation for a validated value."""

    __slots__ = (
        "authority",
        "specification_name",
        "kind",
        "reference_url",
        "version",
        "lifecycle",
        "publication_year",
    )

    authority: str
    specification_name: str
    kind: str
    reference_url: str
    version: str | None
    lifecycle: str
    publication_year: int

    def __init__(
        self,
        authority: str,
        specification_name: str,
        kind: str,
        reference_url: str,
        version: str | None,
        lifecycle: str,
        publication_year: int,
    ) -> None:
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "specification_name", specification_name)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "reference_url", reference_url)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "lifecycle", lifecycle)
        object.__setattr__(self, "publication_year", publication_year)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Provenance is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Provenance is immutable")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Provenance):
            return False
        return (
            self.authority == other.authority
            and self.specification_name == other.specification_name
            and self.kind == other.kind
            and self.reference_url == other.reference_url
            and self.version == other.version
            and self.lifecycle == other.lifecycle
            and self.publication_year == other.publication_year
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.authority,
                self.specification_name,
                self.kind,
                self.reference_url,
                self.version,
                self.lifecycle,
                self.publication_year,
            )
        )


class GrammarRule:
    """Reference to a grammar that produced a RecognizedRep."""

    __slots__ = ("capability_name", "grammar_name")

    capability_name: str
    grammar_name: str

    def __init__(self, capability_name: str, grammar_name: str) -> None:
        object.__setattr__(self, "capability_name", capability_name)
        object.__setattr__(self, "grammar_name", grammar_name)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("GrammarRule is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("GrammarRule is immutable")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GrammarRule):
            return False
        return (
            self.capability_name == other.capability_name
            and self.grammar_name == other.grammar_name
        )

    def __hash__(self) -> int:
        return hash((self.capability_name, self.grammar_name))


class RecognizedRep:
    """Intermediate representation from recognition.

    Pairs a notation (capability-defined shape) with the grammar that
    produced it and the contract that governed recognition, providing
    traceability from validation back to the recognition source.
    """

    __slots__ = ("notation", "contract", "grammar")

    notation: Notation
    contract: Contract
    grammar: GrammarRule

    def __init__(
        self, notation: Notation, contract: Contract, grammar: GrammarRule
    ) -> None:
        object.__setattr__(self, "notation", notation)
        object.__setattr__(self, "contract", contract)
        object.__setattr__(self, "grammar", grammar)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("RecognizedRep is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("RecognizedRep is immutable")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RecognizedRep):
            return False
        return self.notation == other.notation and self.grammar == other.grammar

    def __hash__(self) -> int:
        return hash((tuple(self.notation), self.grammar))


class Candidate:
    """Carries validation output: canonical value + provenance.

    ``recognition_rule`` and ``validation_rule`` are string-based rule names
    for traceability. If a future iteration requires instance references,
    update the Candidate fields and documentation accordingly.
    """

    __slots__ = ("value", "recognition_rule", "validation_rule", "_provenance")

    value: str
    recognition_rule: str
    validation_rule: str
    _provenance: tuple[Provenance, ...]

    def __init__(
        self,
        value: str,
        recognition_rule: str,
        validation_rule: str,
        provenance: Sequence[Provenance],
    ) -> None:
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "recognition_rule", recognition_rule)
        object.__setattr__(self, "validation_rule", validation_rule)
        object.__setattr__(self, "_provenance", tuple(provenance))

    @property
    def provenance(self) -> tuple[Provenance, ...]:
        return object.__getattribute__(self, "_provenance")

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Candidate is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Candidate is immutable")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Candidate):
            return False
        return (
            self.value == other.value
            and self.recognition_rule == other.recognition_rule
            and self.validation_rule == other.validation_rule
            and self.provenance == other.provenance
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.value,
                self.recognition_rule,
                self.validation_rule,
                self.provenance,
            )
        )


class VersionStamp:
    """Replay integrity metadata."""

    __slots__ = ("paxman_version", "replay_hash")

    paxman_version: str
    replay_hash: str

    def __init__(self, paxman_version: str, replay_hash: str) -> None:
        object.__setattr__(self, "paxman_version", paxman_version)
        object.__setattr__(self, "replay_hash", replay_hash)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("VersionStamp is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("VersionStamp is immutable")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionStamp):
            return False
        return (
            self.paxman_version == other.paxman_version
            and self.replay_hash == other.replay_hash
        )

    def __hash__(self) -> int:
        return hash((self.paxman_version, self.replay_hash))


class Rule(ABC):
    """Base class for validation rules."""

    name: str
    strategy: RuleStrategy
    provenance: Provenance
    citation: str

    @abstractmethod
    def matches(self, notation: Notation) -> bool:
        """Check if notation matches this rule's pattern."""
        ...

    @abstractmethod
    def normalize(self, notation: Notation) -> str:
        """Normalize notation to canonical value."""
        ...


class Grammar(ABC):
    """Base class for recognition grammars."""

    name: str

    @abstractmethod
    def recognize(self, text: str) -> list[Notation]:
        """Extract notation candidates from raw text."""
        ...
