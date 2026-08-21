"""Verbatim legacy Currency grammars (pre-PipelineGrammar migration).

Snapshot of the bespoke ``recognize()`` logic from commit 1a7c4b2, used by
the Migration Proof Harness (ADR-0008 §4.1) to assert byte-identical
``RecognitionMatch`` output after the staged-pipeline migration. Classes are
renamed ``Legacy*`` to avoid colliding with the migrated grammar classes.

Do NOT edit by hand — this is a frozen reference. The live grammar files are
the source of truth post-migration; this module exists only so the parity
test can compare old vs new behavior.
"""

from __future__ import annotations

import re

from paxman.capabilities.Currency.grammar.data.currency_symbols import SYMBOL_TOKENS
from paxman.capabilities.Currency.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Currency.notation import CurrencyNotation
from paxman.core.domain import Grammar, RecognitionMatch

_SYMBOL_ALTERNATION = "|".join(re.escape(token) for token in SYMBOL_TOKENS)
_SYMBOL_PATTERN = re.compile(
    rf"(?<![\w\-+\u2212])(?:{_SYMBOL_ALTERNATION})(?![\w\-+\u2212])"
)

_WORD_ALTERNATION = "|".join(re.escape(token) for token in WORD_TOKENS)
_WORD_PATTERN = re.compile(
    rf"(?<![\w\-+\u2212])(?:{_WORD_ALTERNATION})(?![\w\-+\u2212])",
    re.IGNORECASE,
)

_CODE_PATTERN = re.compile(r"(?<![\w\-+\u2212])(?P<code>[A-Za-z]{3})(?![\w\-+\u2212])")


def _is_qualified(token: str) -> bool:
    """Whether a symbol token carries an ASCII letter (e.g. "US$")."""
    return any(char.isascii() and char.isalpha() for char in token)


class LegacySymbolRecognition(Grammar[CurrencyNotation]):
    """Legacy standalone CLDR currency symbol recognition (verbatim)."""

    name = "symbol_recognition"
    semantics = "symbol_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[CurrencyNotation]]:
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CurrencyNotation]] = []
        for match in _SYMBOL_PATTERN.finditer(text):
            token = match.group(0)
            matches.append(
                RecognitionMatch(
                    notation=CurrencyNotation(
                        text=token,
                        shape="qualified_symbol" if _is_qualified(token) else "symbol",
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=token,
                )
            )
        return matches


class LegacyCodeRecognition(Grammar[CurrencyNotation]):
    """Legacy standalone ISO 4217 alpha-3 code recognition (verbatim)."""

    name = "code_recognition"
    semantics = "code_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[CurrencyNotation]]:
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CurrencyNotation]] = []
        for match in _CODE_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CurrencyNotation(
                        text=match.group("code").upper(),
                        shape="code",
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


class LegacyWordRecognition(Grammar[CurrencyNotation]):
    """Legacy standalone CLDR currency display-name word recognition (verbatim)."""

    name = "word_recognition"
    semantics = "word_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[CurrencyNotation]]:
        if not text.strip():
            return []
        matches: list[RecognitionMatch[CurrencyNotation]] = []
        for match in _WORD_PATTERN.finditer(text):
            matches.append(
                RecognitionMatch(
                    notation=CurrencyNotation(
                        text=match.group(0).lower(),
                        shape="word",
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
