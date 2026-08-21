"""Country notation — intermediate representation for country recognition."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Compiled normalizer: collapse whitespace runs.
_WHITESPACE_RE = re.compile(r"\s+")

# Separator characters treated as word boundaries: hyphen, en dash, and
# slash. Mapping them to a space (rather than stripping them) makes
# "GUINEA-BISSAU", "GUINEA\u2013BISSAU", "GUINEA/BISSAU", and "GUINEA BISSAU"
# collapse to one lookup key while keeping punctuation removal intact.
_SEPARATOR_TO_SPACE = str.maketrans(
    {
        "-": " ",
        "\u2013": " ",  # en dash
        "/": " ",
    }
)


@dataclass(frozen=True, slots=True)
class CountryNotation:
    """Intermediate representation for country recognition.

    Attributes:
        shape: Discriminator set by grammar ("alpha2", "alpha3", "numeric", "name").
        value: Raw input value (e.g., "US", "USA", "840", "United States").
    """

    shape: str
    value: str


def normalize_name(text: str) -> str:
    """Return a syntax-normalized Country name lookup key.

    NFKD-decomposes the input (splits accented chars like ô → o + combining
    mark), folds hyphens, en dashes, and slashes into word boundaries,
    strips combining marks and punctuation, collapses whitespace, uppercases,
    and trims outer whitespace. Unicode letters (including CJK) and digits
    are preserved.

    This is syntax normalization only: case folding, Unicode decomposition,
    separator-to-word-boundary folding, punctuation removal, and whitespace
    collapsing make no statement about what a name means. Transliteration,
    fuzzy matching, synonym resolution, and canonical-value lookup are out of
    scope.

    Args:
        text: Raw input text.

    Returns:
        Normalized key suitable for membership and lookup-table matching.
    """
    # NFKD decompose: "ô" → "o" + combining circumflex
    decomposed = unicodedata.normalize("NFKD", text)
    # Fold separators into word boundaries so separated variants share a key
    with_separators = decomposed.translate(_SEPARATOR_TO_SPACE)
    # Keep only alphanumeric and whitespace (strips combining marks + punctuation)
    cleaned = "".join(c for c in with_separators if c.isalnum() or c.isspace())
    # Collapse whitespace
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    # Uppercase and trim
    return cleaned.upper().strip()
