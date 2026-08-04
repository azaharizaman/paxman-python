"""Shared syntax-only normalization for Country name recognition.

Country name grammars use ``normalize_name()`` to decide whether an input
is a known name representation, and Country validation rules use the same
function to look up notation values in their authority tables. Sharing one
normalizer keeps both layers in agreement on lookup keys.

This is syntax normalization only: case folding, Unicode decomposition,
punctuation removal, and whitespace collapsing make no statement about
what a name means. Transliteration, fuzzy matching, synonym resolution,
and canonical-value lookup are out of scope.
"""

from __future__ import annotations

import re
import unicodedata

# Compiled normalizer: keep only letters, digits, and whitespace
# (strip punctuation and other symbols).
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_name(text: str) -> str:
    """Return a syntax-normalized Country name lookup key.

    NFKD-decomposes the input (splits accented chars like ô → o + combining
    mark), strips combining marks and punctuation, collapses whitespace,
    uppercases, and trims outer whitespace. Unicode letters (including CJK)
    and digits are preserved.

    Args:
        text: Raw input text.

    Returns:
        Normalized key suitable for membership and lookup-table matching.
    """
    # NFKD decompose: "ô" → "o" + combining circumflex
    decomposed = unicodedata.normalize("NFKD", text)
    # Keep only alphanumeric and whitespace (strips combining marks + punctuation)
    cleaned = "".join(c for c in decomposed if c.isalnum() or c.isspace())
    # Collapse whitespace
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    # Uppercase and trim
    return cleaned.upper().strip()
