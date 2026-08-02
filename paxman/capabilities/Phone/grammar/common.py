"""Shared helpers for Phone recognition grammars.

Space, dash, dot, and parentheses are the separators every Phone grammar
tolerates inside a number. ``strip_separators`` normalizes a raw match to
digit-only text, and ``dedup`` collapses duplicate notations so the same
number written in different formats yields a single candidate.
"""

from __future__ import annotations

from collections.abc import Iterable

from paxman.capabilities.Phone.notation import PhoneNotation

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


def dedup(notations: Iterable[PhoneNotation]) -> list[PhoneNotation]:
    """Drop duplicate notations, preserving first-seen order.

    Args:
        notations: Notations produced by a grammar's matcher.

    Returns:
        The notations with duplicates (same ``as_list()`` tuple) removed.
    """
    results: list[PhoneNotation] = []
    seen: set[tuple[str, ...]] = set()
    for notation in notations:
        key = tuple(notation.as_list())
        if key not in seen:
            seen.add(key)
            results.append(notation)
    return results
