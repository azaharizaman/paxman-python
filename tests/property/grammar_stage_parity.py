"""Helper for Migration Proof Harness."""

from __future__ import annotations

from typing import Any

from paxman.core.domain import Grammar


def assert_grammar_parity(old: Grammar[Any], new: Grammar[Any], text: str) -> None:
    """Assert byte-identical RecognitionMatch lists.

    The migration gate (ADR-0008 §4.1) requires that a new
    ``PipelineGrammar`` declaration produces the same ``list[RecognitionMatch]``
    as the old bespoke ``recognize()`` for a given input: identical length and,
    element-wise, identical ``start``, ``end``, ``raw_text``, and ``notation``.
    """
    old_matches = old.recognize(text)
    new_matches = new.recognize(text)
    assert len(old_matches) == len(new_matches), (
        f"len mismatch for {text!r}: {old_matches} vs {new_matches}"
    )
    for o, n in zip(old_matches, new_matches, strict=True):
        assert o.start == n.start, f"start mismatch for {text!r}: {o} vs {n}"
        assert o.end == n.end, f"end mismatch for {text!r}: {o} vs {n}"
        assert o.raw_text == n.raw_text, (
            f"raw_text mismatch for {text!r}: {o.raw_text!r} vs {n.raw_text!r}"
        )
        assert o.notation == n.notation, (
            f"notation mismatch for {text!r}: {o.notation!r} vs {n.notation!r}"
        )
