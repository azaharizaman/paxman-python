"""Tests for the URL absolute-URI recognition grammar."""

from __future__ import annotations

import pytest

from paxman.capabilities.URL.grammar.absolute_uri_recognition import (
    AbsoluteUriRecognition,
)
from paxman.capabilities.URL.notation import URLNotation

pytestmark = [pytest.mark.capability, pytest.mark.url]


class TestAbsoluteUriRecognition:
    """Recognition behavior for AbsoluteUriRecognition."""

    def test_note_colon_rejected(self) -> None:
        grammar = AbsoluteUriRecognition()
        results = grammar.recognize("Note:")
        assert results == []

    def test_span_in_prose_with_parens(self) -> None:
        grammar = AbsoluteUriRecognition()
        results = grammar.recognize("(https://example.com)")
        assert len(results) == 1
        assert results[0].raw_text == "https://example.com"
        assert results[0].notation == URLNotation(text="https://example.com")

    def test_multiline_span_keeps_tab_newline(self) -> None:
        grammar = AbsoluteUriRecognition()
        results = grammar.recognize("http://exa\nmple.com/")
        assert len(results) == 1
        assert "\n" in results[0].raw_text
        assert results[0].raw_text == "http://exa\nmple.com/"

    def test_trailing_dot_host_included(self) -> None:
        grammar = AbsoluteUriRecognition()
        results = grammar.recognize("http://example.com.")
        assert len(results) == 1
        assert results[0].raw_text == "http://example.com."

    def test_left_boundary_word_rejection(self) -> None:
        grammar = AbsoluteUriRecognition()
        # Shape-only per D7/D8: "ahttps" is a syntactically valid scheme
        # (RFC 3986 §3.1), so the span is recognized; the WHATWG rule
        # rejects unknown/unsupported schemes downstream (INVALID at the
        # rule level, never at recognition).
        results = grammar.recognize("ahttps://example.com")
        assert len(results) == 1
        assert results[0].raw_text == "ahttps://example.com"
        # Genuine word rejection: "1" is scheme-legal but cannot start a
        # scheme, and the lookbehind blocks every candidate start.
        assert grammar.recognize("1https://example.com") == []
        # Scheme-anchored: the "(" is outside the span.
        results = grammar.recognize("(https://example.com")
        assert len(results) == 1
        assert results[0].raw_text == "https://example.com"

    def test_non_ascii_body(self) -> None:
        grammar = AbsoluteUriRecognition()
        results = grammar.recognize("mailto:user@münchen.de")
        assert len(results) == 1
        assert results[0].raw_text == "mailto:user@münchen.de"

    def test_shape_only_never_validates(self) -> None:
        grammar = AbsoluteUriRecognition()
        results = grammar.recognize("https://")
        assert len(results) == 1
        assert results[0].raw_text == "https://"
        results = grammar.recognize("http://99999/")
        assert len(results) == 1
        assert results[0].raw_text == "http://99999/"

    def test_paren_strip_preserves_body(self) -> None:
        grammar = AbsoluteUriRecognition()
        # ")" is body-legal, so an all-paren body would strip down to the
        # bare scheme; D16 requires at least one body character after the
        # colon, so no empty-body match may be emitted.
        assert grammar.recognize("https:))))") == []
        results = grammar.recognize("https://example.com))")
        assert len(results) == 1
        assert results[0].raw_text == "https://example.com"

    def test_span_invariant(self) -> None:
        grammar = AbsoluteUriRecognition()
        prose = [
            "(https://example.com)",
            "see http://example.com. now",
            "mailto:user@münchen.de",
        ]
        for text in prose:
            for match in grammar.recognize(text):
                assert 0 <= match.start <= match.end <= len(text)
                assert len(match.raw_text) == match.end - match.start

    def test_double_quote_right_boundary(self) -> None:
        grammar = AbsoluteUriRecognition()
        # Appendix C of RFC 3986 lists '"' as a URI delimiter: a quoted URI
        # must not swallow its closing quote.
        results = grammar.recognize('"https://example.com/"')
        assert len(results) == 1
        assert results[0].raw_text == "https://example.com/"
        results = grammar.recognize('"https://example.com/" then "mailto:a@b.de"')
        spans = [r.raw_text for r in results]
        assert spans == ["https://example.com/", "mailto:a@b.de"]
