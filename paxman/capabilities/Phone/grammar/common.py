"""Shared helpers for Phone recognition grammars.

Space, dash, dot, and parentheses are the separators every Phone grammar
tolerates inside a number. ``strip_separators`` normalizes a raw match to
digit-only text. Grammar-level value dedup was removed in the recognition-
homogeneity migration: the engine dedups contained matches by span and
identical candidates by value.
"""

from __future__ import annotations

# Digits are preserved; space, dash, dot, and parentheses are removed.
_SEPARATORS = str.maketrans("", "", " ().-")
# E.164 / tel-URI matches also carry a leading "+" to strip.
_SEPARATORS_WITH_PLUS = str.maketrans("", "", "+ ().-")


def strip_separators(value: str, *, plus: bool = False) -> str:
    """Remove phone separators from a raw match.

    Args:
        value: Raw match text (digits, separators, optional leading "+").
        plus: Also strip a leading "+" (E.164 and tel-URI matches).

    Returns:
        The digit-only number.
    """
    if plus:
        return value.translate(_SEPARATORS_WITH_PLUS)
    return value.translate(_SEPARATORS)
