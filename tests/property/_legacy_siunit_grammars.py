"""Verbatim legacy SIUnit grammars (pre-PipelineGrammar migration).

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

from paxman.capabilities.SIUnit.grammar.data.compound_tokens import (
    COMPOUND_SEPARATORS,
    EXPONENT_CHARACTERS,
)
from paxman.capabilities.SIUnit.grammar.data.prefix_tokens import (
    PREFIX_SYMBOL_TOKENS,
    PREFIX_WORD_TOKENS,
)
from paxman.capabilities.SIUnit.grammar.data.unit_name_tokens import NAME_TOKENS
from paxman.capabilities.SIUnit.grammar.data.unit_symbol_tokens import SYMBOL_TOKENS
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.core.domain import Grammar, RecognitionMatch

# --- symbol_recognition (verbatim) -----------------------------------------

DUAL_ROLE_PREFIX_SYMBOLS = frozenset({"a", "d", "h", "m"})
PREFIX_ONLY_SYMBOLS = frozenset(PREFIX_SYMBOL_TOKENS) - DUAL_ROLE_PREFIX_SYMBOLS

_SYMBOL_LOOKBEHIND = r"(?<![°\w\-+\u2212/·⋅])"
_SYMBOL_LOOKAHEAD = r"(?![\w\-+\u2212/·⋅])"
_SYMBOL_ALT = "|".join(re.escape(t) for t in SYMBOL_TOKENS)
_PREFIX_ONLY_SYMBOL_ALT = "|".join(re.escape(t) for t in sorted(PREFIX_ONLY_SYMBOLS))
_SYMBOL_BODY = (
    r"(?:(?:" + _PREFIX_ONLY_SYMBOL_ALT + r")\s+(?:" + _SYMBOL_ALT + r"))"
    r"|"
    r"(?:(?:" + _SYMBOL_ALT + r"))"
)
_SYMBOL_RE = re.compile(
    _SYMBOL_LOOKBEHIND + r"(?P<tok>" + _SYMBOL_BODY + r")" + _SYMBOL_LOOKAHEAD
)


class LegacySymbolRecognition(Grammar[SIUnitNotation]):
    """Legacy case-exact unit symbol recognition (verbatim)."""

    name = "symbol_recognition"
    semantics = "symbol_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[SIUnitNotation]]:
        matches: list[RecognitionMatch[SIUnitNotation]] = []
        for m in _SYMBOL_RE.finditer(text):
            token = m.group("tok")
            parts = token.split()
            if len(parts) >= 2 and parts[0] in PREFIX_ONLY_SYMBOLS:
                shape = "split_symbol_prefix"
            else:
                shape = "symbol"
            matches.append(
                RecognitionMatch(
                    raw_text=text[m.start() : m.end()],
                    start=m.start(),
                    end=m.end(),
                    notation=SIUnitNotation(text=token, shape=shape),
                )
            )
        return matches


# --- name_recognition (verbatim) -------------------------------------------

PREFIX_WORDS = frozenset(PREFIX_WORD_TOKENS)

_NAME_LOOKBEHIND = r"(?<![°\w\-+\u2212/·⋅])"
_NAME_LOOKAHEAD = r"(?![\w\-+\u2212/·⋅])"
_NAME_ALT = "|".join(re.escape(t) for t in NAME_TOKENS)
_PREFIX_WORD_ALT = "|".join(re.escape(t) for t in PREFIX_WORD_TOKENS)
_NAME_BODY = (
    r"(?:(?:" + _PREFIX_WORD_ALT + r")\s+(?:" + _NAME_ALT + r"))"
    r"|"
    r"(?:" + _NAME_ALT + r")"
)
_NAME_RE = re.compile(
    _NAME_LOOKBEHIND + r"(?P<tok>" + _NAME_BODY + r")" + _NAME_LOOKAHEAD, re.IGNORECASE
)


class LegacyNameRecognition(Grammar[SIUnitNotation]):
    """Legacy case-folded unit name recognition (verbatim)."""

    name = "name_recognition"
    semantics = "name_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[SIUnitNotation]]:
        matches: list[RecognitionMatch[SIUnitNotation]] = []
        for m in _NAME_RE.finditer(text):
            token = m.group("tok").lower()
            parts = token.split()
            if len(parts) >= 2 and parts[0] in PREFIX_WORDS:
                shape = "split_word_prefix"
            else:
                shape = "name"
            matches.append(
                RecognitionMatch(
                    raw_text=text[m.start() : m.end()],
                    start=m.start(),
                    end=m.end(),
                    notation=SIUnitNotation(text=token, shape=shape),
                )
            )
        return matches


# --- compound_recognition (verbatim) ---------------------------------------

_EXPONENT = rf"[{EXPONENT_CHARACTERS}]*"
_UNIT = rf"(?:°?[A-Za-zµΩÅ][A-Za-zµΩÅ0-9]*{_EXPONENT})"
_SEP = f"[{COMPOUND_SEPARATORS}]"
_FACTOR = rf"(?:{_UNIT}|\({_UNIT}(?:{_SEP}{_UNIT}){{0,3}}\))"
_COMPOUND_RE = re.compile(
    rf"(?<![\w\-+\u2212])(?P<body>{_FACTOR}(?:{_SEP}{_FACTOR}){{1,3}})(?![\w\-+\u2212])"
)


class LegacyCompoundRecognition(Grammar[SIUnitNotation]):
    """Legacy product/quotient compound shape recognition (verbatim)."""

    name = "compound_recognition"
    semantics = "compound_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[SIUnitNotation]]:
        return [
            RecognitionMatch(
                raw_text=text[m.start() : m.end()],
                start=m.start(),
                end=m.end(),
                notation=SIUnitNotation(text=m.group("body"), shape="compound"),
            )
            for m in _COMPOUND_RE.finditer(text)
        ]
