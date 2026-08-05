"""Tests for ISBN recognition grammars."""

from __future__ import annotations

import pytest

from paxman.capabilities.ISBN.grammar.isbn10_recognition import (
    ISBN10RecognitionGrammar,
)
from paxman.capabilities.ISBN.grammar.isbn13_recognition import (
    ISBN13RecognitionGrammar,
)
from paxman.capabilities.ISBN.notation import ISBNNotation

pytestmark = [pytest.mark.capability]


class TestISBN13RecognitionGrammar:
    """Tests for ISBN13RecognitionGrammar."""

    @pytest.mark.capability
    def test_recognizes_isbn13_digits_only(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("9780306406157")
        assert len(results) == 1
        assert results[0].notation == ISBNNotation(
            shape="isbn13", digits="9780306406157"
        )
        assert results[0].start == 0
        assert results[0].end == 13
        assert results[0].raw_text == "9780306406157"

    @pytest.mark.capability
    def test_recognizes_isbn13_with_hyphens(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("978-0-306-40615-7")
        assert len(results) == 1
        assert results[0].notation.digits == "9780306406157"

    @pytest.mark.capability
    def test_recognizes_isbn13_with_spaces(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("978 0 306 40615 7")
        assert len(results) == 1
        assert results[0].notation.digits == "9780306406157"

    @pytest.mark.capability
    def test_recognizes_isbn13_with_label(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("ISBN 9780306406157")
        assert len(results) == 1
        assert results[0].notation.digits == "9780306406157"

    @pytest.mark.capability
    def test_recognizes_isbn13_with_label_and_hyphens(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("ISBN-13: 978-0-306-40615-7")
        assert len(results) == 1
        assert results[0].notation.digits == "9780306406157"

    @pytest.mark.capability
    def test_rejects_isbn13_glued_label(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("ISBN9780306406157")
        assert results == []

    @pytest.mark.capability
    def test_rejects_isbn13_14_digits(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("97803064061577")
        assert results == []

    @pytest.mark.capability
    def test_rejects_isbn13_embedded_in_word(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("abc9780306406157xyz")
        assert results == []

    @pytest.mark.capability
    def test_recognizes_multiple_isbn13(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("9780306406157 9780201310054")
        assert len(results) == 2
        assert results[0].start == 0
        assert results[0].end == 13
        assert results[1].start > results[0].start

    @pytest.mark.capability
    def test_span_invariants(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("9780306406157")
        assert len(results) == 1
        match = results[0]
        assert len(match.raw_text) == match.end - match.start
        assert 0 <= match.start <= match.end

    @pytest.mark.capability
    def test_returns_empty_for_empty_input(self) -> None:
        grammar = ISBN13RecognitionGrammar()
        results = grammar.recognize("")
        assert results == []


class TestISBN10RecognitionGrammar:
    """Tests for ISBN10RecognitionGrammar."""

    @pytest.mark.capability
    def test_recognizes_isbn10_digits_only(self) -> None:
        grammar = ISBN10RecognitionGrammar()
        results = grammar.recognize("0306406152")
        assert len(results) == 1
        assert results[0].notation == ISBNNotation(shape="isbn10", digits="0306406152")

    @pytest.mark.capability
    def test_recognizes_isbn10_with_hyphens(self) -> None:
        grammar = ISBN10RecognitionGrammar()
        results = grammar.recognize("0-306-40615-2")
        assert len(results) == 1
        assert results[0].notation.digits == "0306406152"

    @pytest.mark.capability
    def test_recognizes_isbn10_with_uppercase_x(self) -> None:
        grammar = ISBN10RecognitionGrammar()
        results = grammar.recognize("080442957X")
        assert len(results) == 1
        assert results[0].notation.digits == "080442957X"

    @pytest.mark.capability
    def test_recognizes_isbn10_with_lowercase_x(self) -> None:
        grammar = ISBN10RecognitionGrammar()
        results = grammar.recognize("080442957x")
        assert len(results) == 1
        assert results[0].notation.digits == "080442957X"

    @pytest.mark.capability
    def test_recognizes_isbn10_with_label(self) -> None:
        grammar = ISBN10RecognitionGrammar()
        results = grammar.recognize("ISBN-10 0-306-40615-2")
        assert len(results) == 1
        assert results[0].notation.digits == "0306406152"

    @pytest.mark.capability
    def test_rejects_isbn10_11_digits(self) -> None:
        grammar = ISBN10RecognitionGrammar()
        results = grammar.recognize("03064061523")
        assert results == []

    @pytest.mark.capability
    def test_span_invariants(self) -> None:
        grammar = ISBN10RecognitionGrammar()
        results = grammar.recognize("0306406152")
        assert len(results) == 1
        match = results[0]
        assert len(match.raw_text) == match.end - match.start
        assert 0 <= match.start <= match.end

    @pytest.mark.capability
    def test_returns_empty_for_empty_input(self) -> None:
        grammar = ISBN10RecognitionGrammar()
        results = grammar.recognize("")
        assert results == []
