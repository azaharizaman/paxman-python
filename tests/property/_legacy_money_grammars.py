"""Verbatim legacy Money grammars (pre-PipelineGrammar migration).

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
from typing import cast

from paxman.capabilities.Money.grammar import AMOUNT_PATTERN, classify_amount_shape
from paxman.capabilities.Money.grammar.data.currency_symbols import SYMBOL_TOKENS
from paxman.capabilities.Money.grammar.data.currency_words import WORD_TOKENS
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.core.domain import Grammar, RecognitionMatch

_SYMBOL_ALTERNATION = "|".join(re.escape(token) for token in SYMBOL_TOKENS)
_SYMBOL_PATTERN = re.compile(
    rf"(?<![\w\-+\u2212])(?:(?P<prefix_symbol>{_SYMBOL_ALTERNATION})"
    rf" ?(?P<prefix_amount>{AMOUNT_PATTERN})"
    rf"|(?P<suffix_amount>{AMOUNT_PATTERN}) ?(?P<suffix_symbol>{_SYMBOL_ALTERNATION}))"
    rf"(?![\w\-+\u2212])"
)

_WORD_ALTERNATION = "|".join(re.escape(token) for token in WORD_TOKENS)
_WORD_PATTERN = re.compile(
    rf"(?<![\w\-+\u2212])(?:(?P<prefix_word>{_WORD_ALTERNATION})"
    rf" ?(?P<prefix_amount>{AMOUNT_PATTERN})"
    rf"|(?P<suffix_amount>{AMOUNT_PATTERN}) ?(?P<suffix_word>{_WORD_ALTERNATION}))"
    rf"(?![\w\-+\u2212])",
    re.IGNORECASE,
)

_CODE_PATTERN = re.compile(
    rf"(?<![\w\-+\u2212])"
    rf"(?:(?P<prefix_code>[A-Z]{{3}}) ?(?P<prefix_amount>{AMOUNT_PATTERN})"
    rf"|(?P<suffix_amount>{AMOUNT_PATTERN}) ?(?P<suffix_code>[A-Z]{{3}}))"
    rf"(?![\w\-+\u2212])"
)


def _is_qualified(token: str) -> bool:
    """A symbol is qualified when it contains an ASCII letter (US$, RM)."""
    return any(ch.isascii() and ch.isalpha() for ch in token)


class LegacyCodeRecognition(Grammar[MoneyNotation]):
    """Legacy ISO 4217 alpha-3 code + amount recognition (verbatim)."""

    name = "code_recognition"
    semantics = "code_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[MoneyNotation]]:
        if not text.strip():
            return []
        matches: list[RecognitionMatch[MoneyNotation]] = []
        for match in _CODE_PATTERN.finditer(text):
            currency = cast(
                str, match.group("prefix_code") or match.group("suffix_code")
            )
            amount = cast(
                str, match.group("prefix_amount") or match.group("suffix_amount")
            )
            matches.append(
                RecognitionMatch(
                    notation=MoneyNotation(
                        currency_part=currency,
                        amount_part=amount,
                        currency_shape="code",
                        amount_shape=classify_amount_shape(amount),
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


class LegacySymbolRecognition(Grammar[MoneyNotation]):
    """Legacy CLDR currency symbol + amount recognition (verbatim)."""

    name = "symbol_recognition"
    semantics = "symbol_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[MoneyNotation]]:
        if not text.strip():
            return []
        matches: list[RecognitionMatch[MoneyNotation]] = []
        for match in _SYMBOL_PATTERN.finditer(text):
            symbol = cast(
                str, match.group("prefix_symbol") or match.group("suffix_symbol")
            )
            amount = cast(
                str, match.group("prefix_amount") or match.group("suffix_amount")
            )
            matches.append(
                RecognitionMatch(
                    notation=MoneyNotation(
                        currency_part=symbol,
                        amount_part=amount,
                        currency_shape=(
                            "qualified_symbol" if _is_qualified(symbol) else "symbol"
                        ),
                        amount_shape=classify_amount_shape(amount),
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches


class LegacyWordRecognition(Grammar[MoneyNotation]):
    """Legacy CLDR currency display-name word + amount recognition (verbatim)."""

    name = "word_recognition"
    semantics = "word_recognition"
    single_value = True

    def recognize(self, text: str) -> list[RecognitionMatch[MoneyNotation]]:
        if not text.strip():
            return []
        matches: list[RecognitionMatch[MoneyNotation]] = []
        for match in _WORD_PATTERN.finditer(text):
            word = cast(str, match.group("prefix_word") or match.group("suffix_word"))
            amount = cast(
                str, match.group("prefix_amount") or match.group("suffix_amount")
            )
            matches.append(
                RecognitionMatch(
                    notation=MoneyNotation(
                        currency_part=word,
                        amount_part=amount,
                        currency_shape="word",
                        amount_shape=classify_amount_shape(amount),
                    ),
                    start=match.start(),
                    end=match.end(),
                    raw_text=match.group(0),
                )
            )
        return matches
