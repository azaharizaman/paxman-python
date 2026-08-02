from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar, cast

from paxman.core.contract import Contract

NotationT = TypeVar("NotationT")


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


@dataclass(frozen=True, slots=True)
class Provenance:
    """Authority citation for a validated value."""

    authority: str
    specification_name: str
    kind: str
    reference_url: str
    version: str | None
    lifecycle: str
    publication_year: int


@dataclass(frozen=True, slots=True)
class GrammarRule:
    """Reference to a grammar that produced a RecognizedRep."""

    capability_name: str
    grammar_name: str

    def __post_init__(self) -> None:
        """Enforce lowercase naming convention for capability and grammar names."""
        if self.capability_name != self.capability_name.lower():
            raise ValueError(
                f"capability_name must be lowercase, got {self.capability_name!r}"
            )
        if self.grammar_name != self.grammar_name.lower():
            raise ValueError(
                f"grammar_name must be lowercase, got {self.grammar_name!r}"
            )


@dataclass(frozen=True, slots=True)
class RecognizedRep(Generic[NotationT]):
    """Intermediate representation from recognition.

    Pairs a notation (capability-defined shape) with the grammar that
    produced it and the contract that governed recognition, providing
    traceability from validation back to the recognition source.
    """

    notation: NotationT
    contract: Contract
    grammar: GrammarRule

    def __hash__(self) -> int:
        """Hash is safe for unhashable notation types like list."""
        notation = self.notation
        if isinstance(notation, list):
            notation_key = tuple(cast(list[str], notation))
        else:
            notation_key = notation
        return hash((notation_key, self.grammar))


@dataclass(frozen=True, slots=True)
class Candidate:
    """Carries validation output: canonical value + provenance.

    ``recognition_rule`` and ``validation_rule`` are string-based rule names
    for traceability. If a future iteration requires instance references,
    update the Candidate fields and documentation accordingly.
    """

    value: str
    recognition_rule: str
    validation_rule: str
    _provenance: tuple[Provenance, ...] = field(init=False)

    @property
    def provenance(self) -> tuple[Provenance, ...]:
        return object.__getattribute__(self, "_provenance")

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


@dataclass(frozen=True, slots=True)
class VersionStamp:
    """Replay integrity metadata."""

    paxman_version: str
    replay_hash: str


class Rule(ABC, Generic[NotationT]):
    """Base class for validation rules."""

    name: str
    strategy: RuleStrategy
    provenance: Provenance
    citation: str

    @abstractmethod
    def matches(self, notation: NotationT, contract: Contract) -> bool: ...

    @abstractmethod
    def normalize(self, notation: NotationT, contract: Contract) -> str: ...


class Grammar(ABC, Generic[NotationT]):
    """Base class for recognition grammars."""

    name: str

    @abstractmethod
    def recognize(self, text: str) -> list[NotationT]: ...
