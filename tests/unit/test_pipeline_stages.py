"""Unit tests for PipelineState and PipelineGrammar skeleton."""

from __future__ import annotations

import re

import pytest

from paxman.capabilities.Date.notation import DateNotation
from paxman.core.domain import Grammar
from paxman.core.grammar import PipelineGrammar, PipelineState
from paxman.core.grammar.stages import RegexStage, StandardPre

pytestmark = pytest.mark.unit


def _date_notation(m: re.Match[str]) -> DateNotation:
    return DateNotation(N1=m.group(1), N2=m.group(2), N3=m.group(3))


class _ProbeGrammar(PipelineGrammar[DateNotation]):
    """Minimal PipelineGrammar for skeleton test."""

    name = "probe_recognition"
    semantics = "probe_recognition"
    pre = StandardPre(empty_guard=True)
    regex = RegexStage(
        r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)", notation_fn=_date_notation
    )


def test_pipeline_state_is_frozen_slots() -> None:
    state = PipelineState(text="hello", matches=[], scratch={})
    assert state.text == "hello"
    with pytest.raises(AttributeError):
        state.text = "mutated"  # type: ignore[misc]


def test_pipeline_grammar_is_grammar_subclass() -> None:
    g = _ProbeGrammar()
    assert isinstance(g, Grammar)
    assert g.name == "probe_recognition"
    assert g.semantics == "probe_recognition"


def test_pipeline_grammar_recognize_delegates_to_stages() -> None:
    g = _ProbeGrammar()
    results = g.recognize("2026-01-15 foo 2026/01/15")
    assert len(results) == 1
    assert results[0].raw_text == "2026-01-15"
    assert results[0].start == 0
    assert results[0].end == 10


def test_empty_input_early_exit_via_pre() -> None:
    g = _ProbeGrammar()
    assert g.recognize("") == []
    assert g.recognize("   ") == []


def test_grammar_with_no_stages_returns_empty() -> None:
    class _EmptyGrammar(PipelineGrammar[DateNotation]):
        name = "empty_recognition"
        semantics = "empty_recognition"

    assert _EmptyGrammar().recognize("2026-01-15") == []
