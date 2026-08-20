"""Stage Protocol and concrete stage types for the recognition pipeline."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar

from paxman.core.domain import RecognitionMatch
from paxman.core.grammar.boundary import BoundaryGuard

NotationT = TypeVar("NotationT")


@dataclass(frozen=True, slots=True)
class PipelineState(Generic[NotationT]):
    """Mutable-through-replacement state threaded through stages."""

    text: str
    matches: list[RecognitionMatch[NotationT]] = field(
        default_factory=lambda: list[RecognitionMatch[NotationT]]()
    )
    scratch: dict[str, object] = field(default_factory=lambda: dict[str, object]())


class Stage(Protocol[NotationT]):
    """Inter-stage contract — each stage consumes and returns a PipelineState."""

    def run(self, state: PipelineState[NotationT]) -> PipelineState[NotationT]: ...


@dataclass(frozen=True, slots=True)
class StandardPre(Generic[NotationT]):
    """Pre-processing stage: empty/whitespace early-exit, optional normalizer."""

    empty_guard: bool = True

    def run(self, state: PipelineState[NotationT]) -> PipelineState[NotationT]:
        if self.empty_guard and not state.text.strip():
            return PipelineState(
                text=state.text, matches=[], scratch=dict(state.scratch)
            )
        return state


@dataclass(frozen=True, slots=True)
class RegexStage(Generic[NotationT]):
    """Regex parser stage: pure shape scan via finditer."""

    pattern: str
    notation_fn: Callable[[re.Match[str]], NotationT] | None = None
    _compiled: re.Pattern[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_compiled", re.compile(self.pattern))

    def run(self, state: PipelineState[NotationT]) -> PipelineState[NotationT]:
        if self.notation_fn is None:
            return state
        new_matches: list[RecognitionMatch[NotationT]] = list(state.matches)
        for m in self._compiled.finditer(state.text):
            notation = self.notation_fn(m)
            new_matches.append(
                RecognitionMatch(
                    notation=notation,
                    start=m.start(),
                    end=m.end(),
                    raw_text=m.group(0),
                )
            )
        return PipelineState(
            text=state.text, matches=new_matches, scratch=dict(state.scratch)
        )


@dataclass(frozen=True, slots=True)
class LexiconStage(Generic[NotationT]):
    """Lexicon parser stage: alternation scan guarded by a BoundaryGuard."""

    tokens: frozenset[str] | set[str] | list[str] | tuple[str, ...]
    boundary: BoundaryGuard
    longest_first: bool = True
    notation_fn: Callable[[str], NotationT] | None = None
    flags: int = 0

    def run(self, state: PipelineState[NotationT]) -> PipelineState[NotationT]:
        if self.notation_fn is None:
            return state
        from paxman.core.grammar.lexicon import LexiconAlternation

        alt = LexiconAlternation(tokens=self.tokens, longest_first=self.longest_first)
        pat = self.boundary.wrap(alt.alternation, self.flags)
        new_matches: list[RecognitionMatch[NotationT]] = list(state.matches)
        for m in pat.finditer(state.text):
            token = m.group(0)
            new_matches.append(
                RecognitionMatch(
                    notation=self.notation_fn(token),
                    start=m.start(),
                    end=m.end(),
                    raw_text=token,
                )
            )
        return PipelineState(
            text=state.text, matches=new_matches, scratch=dict(state.scratch)
        )


@dataclass(frozen=True, slots=True)
class WholeInputLookup(Generic[NotationT]):
    """S2 whole-input membership — a LexiconStage variant for Country/name_recognition.

    The entire (trimmed) input is looked up against a set of normalized keys.
    The emitted match carries the *original* trimmed text and span (D7), not the
    normalized key. ``normalizer`` is required: Country must pass its
    ``normalize_name`` so that the lookup key is derived deterministically rather
    than by a hard-coded ``lower()`` that would break other capabilities.
    """

    keys: frozenset[str] | set[str]
    normalizer: Callable[[str], str]
    notation_fn: Callable[[str], NotationT] | None = None

    def run(self, state: PipelineState[NotationT]) -> PipelineState[NotationT]:
        if self.notation_fn is None:
            return state
        trimmed = state.text.strip()
        if not trimmed:
            return state
        normalized = self.normalizer(trimmed)
        if normalized in self.keys:
            start = len(state.text) - len(state.text.lstrip())
            end = start + len(trimmed)
            new_matches: list[RecognitionMatch[NotationT]] = list(state.matches)
            new_matches.append(
                RecognitionMatch(
                    notation=self.notation_fn(trimmed),
                    start=start,
                    end=end,
                    raw_text=trimmed,
                )
            )
            return PipelineState(
                text=state.text, matches=new_matches, scratch=dict(state.scratch)
            )
        return state
