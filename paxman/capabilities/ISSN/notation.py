"""ISSN notation: normalized digit string."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ISSNNotation:
    """ISSN normalized digit string.

    ``digits`` is the 8-character string, hyphen/space stripped, uppercased
    (``x`` → ``X``). The grammar never computes or validates the check digit;
    rules own that (grammar/rule boundary per HOW_TO_ADD_NEW_CAPABILITY.md §4).
    """

    digits: str
