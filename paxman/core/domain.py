from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Generic, TypeVar, cast

from paxman.core.contract import Contract

NotationT = TypeVar("NotationT")


def _contains_only_strings(values: Iterable[Any]) -> bool:
    """Return whether every reflected metadata value is a string."""
    return all(isinstance(value, str) for value in values)


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
class RecognitionMatch(Generic[NotationT]):
    """A span-bearing recognition produced by a grammar.

    Grammars emit these instead of bare notations so the engine can
    deduplicate overlapping matches and order recognitions deterministically
    without losing positional information.

    ``start`` and ``end`` are half-open character offsets into the input
    text passed to ``Grammar.recognize()``; ``raw_text`` is the matched
    substring, so ``len(raw_text) == end - start`` always holds.
    """

    notation: NotationT
    start: int
    end: int
    raw_text: str

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError(
                f"Invalid span start={self.start}, end={self.end}: "
                "expected 0 <= start <= end"
            )
        if len(self.raw_text) != self.end - self.start:
            raise ValueError(
                f"raw_text {self.raw_text!r} length {len(self.raw_text)} "
                f"does not match span [{self.start}, {self.end})"
            )


@dataclass(frozen=True, slots=True)
class RecognizedRep(Generic[NotationT]):
    """Intermediate representation from recognition.

    Pairs a notation (capability-defined shape) with the grammar that
    produced it and the contract that governed recognition, providing
    traceability from validation back to the recognition source. Carries
    the producing match's span so the engine's recognition order and
    dedup decisions remain traceable end to end.
    """

    notation: NotationT
    contract: Contract
    grammar: GrammarRule
    start: int
    end: int
    raw_text: str

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
    target_grammars: ClassVar[frozenset[str]]
    requires_features: ClassVar[frozenset[str]]

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Enforce Rule metadata at class-definition time."""
        super().__init_subclass__(**kwargs)
        required = (
            "name",
            "strategy",
            "provenance",
            "citation",
            "target_grammars",
            "requires_features",
        )
        missing = [attr for attr in required if not hasattr(cls, attr)]
        if missing:
            raise TypeError(
                f"{cls.__name__} must define Rule metadata: {', '.join(missing)}"
            )
        for attribute in ("target_grammars", "requires_features"):
            value: Any = vars(cls).get(attribute, getattr(cls, attribute))
            if type(value) is not frozenset:
                raise TypeError(f"{cls.__name__}.{attribute} must be frozenset[str]")
            if not _contains_only_strings(
                vars(cls).get(attribute, getattr(cls, attribute))
            ):
                raise TypeError(f"{cls.__name__}.{attribute} must be frozenset[str]")
        if not cls.target_grammars:
            raise TypeError(f"{cls.__name__}.target_grammars must be non-empty")

    @abstractmethod
    def matches(self, notation: NotationT, contract: Contract) -> bool: ...

    @abstractmethod
    def normalize(self, notation: NotationT, contract: Contract) -> str: ...


class Grammar(ABC, Generic[NotationT]):
    """Base class for recognition grammars."""

    name: str

    @abstractmethod
    def recognize(self, text: str) -> list[RecognitionMatch[NotationT]]:
        """Extract span-bearing recognition matches from raw text.

        Grammars MUST return their matches with positional spans; the engine
        owns deduplication and ordering. See RecognitionMatch.
        """
        ...
