"""Hypothesis property tests for the URL capability.

Each property locks a mathematical invariant of the WHATWG parser or the
recognition grammar using an independently derived expectation:

- parsing is total and canonical: ``parse_and_serialize`` never raises and
  canonical output is a fixed point (idempotence);
- every serialized value matches the canonical absolute-URI shape (lowercase
  scheme, no surrounding whitespace);
- recognition spans are honest: offsets are bounded by the input and
  ``raw_text`` matches the span exactly;
- the grammar never rejects a span the rule could accept (D7/D8: ``recognize``
  is a superset of the rule's domain; the rule decides validity).

Property tests stay off the registry and the frozen pipeline (tests/AGENTS.md
convention — Money is the documented exception): these drive
``parse_and_serialize`` and the grammar directly.
"""

from __future__ import annotations

import re
import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.URL.grammar.absolute_uri_recognition import (
    AbsoluteUriRecognition,
)
from paxman.capabilities.URL.parsing import parse_and_serialize

# Canonical absolute-URI shape: lowercase scheme, ":", then the serialized
# remainder. ".*" (not ".+") admits bare-scheme URLs such as "a:" — a
# legitimate WHATWG serialization (empty path) that the grammar deliberately
# excludes (D16: at least one body character after the colon).
_CANONICAL_SHAPE = re.compile(r"^[a-z][a-z0-9+.\-]*:.*$")


@pytest.mark.property
@given(text=st.text(alphabet=string.printable, max_size=120))
def test_parsing_is_total_and_canonical(text: str) -> None:
    """parse_and_serialize never raises; canonical output is a fixed point."""
    serialized = parse_and_serialize(text)
    if serialized is not None:
        assert parse_and_serialize(serialized) == serialized


@pytest.mark.property
@given(text=st.text(alphabet=string.printable, max_size=120))
def test_serialized_output_matches_shape(text: str) -> None:
    """Every non-None output matches the canonical absolute-URI shape."""
    serialized = parse_and_serialize(text)
    if serialized is not None:
        assert _CANONICAL_SHAPE.fullmatch(serialized) is not None


@pytest.mark.property
@given(text=st.text(alphabet=string.printable, max_size=120))
def test_span_invariant(text: str) -> None:
    """Every RecognitionMatch span is honest: bounded by the input text."""
    for match in AbsoluteUriRecognition().recognize(text):
        assert 0 <= match.start <= match.end <= len(text)
        assert match.raw_text == text[match.start : match.end]


@pytest.mark.property
@given(text=st.text(alphabet=string.printable, max_size=120))
def test_recognize_subset_of_parseable(text: str) -> None:
    """The grammar never rejects a span the rule could accept (D7/D8).

    ``recognize`` is a superset of the rule's domain: every recognized span
    either parses (the rule validates it) or is a recognized-but-unvalidated
    span (the rule rejects it — INVALID), and any input the parser accepts
    must have been recognized. The sole exception is a bare scheme such as
    ``a:``, which the parser accepts per WHATWG but the grammar deliberately
    excludes (D16: no body after the colon).
    """
    grammar = AbsoluteUriRecognition()
    matches = grammar.recognize(text)
    for match in matches:
        # Never raises; outcome is a value (accepted) or None (unvalidated).
        parse_and_serialize(match.raw_text)
    if parse_and_serialize(text) is not None and not matches:
        assert text.partition(":")[2] == ""
