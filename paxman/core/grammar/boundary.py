"""BoundaryGuard family — parameterized lookarounds replacing 10 distinct literals.

Each guard produces a compiled alternation-ready regex via `wrap(alternation)`,
or exposes its `(lookbehind, lookahead)` pair for `LexiconStage` injection.
No grammar file hard-codes a lookaround literal after migration — each grammar
references a `BoundaryGuard` instance (ADR-0008 D5).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundaryGuard:
    """A parameterized boundary guard producing lookaround-wrapped patterns."""

    lookbehind: str
    lookahead: str

    def wrap(self, alternation: str, flags: int = 0) -> re.Pattern[str]:
        """Wrap an alternation with this guard's lookarounds and compile.

        Args:
            alternation: The escaped ``|``-joined token alternation.
            flags: Optional ``re`` flags (e.g. ``re.IGNORECASE``) passed to
                ``re.compile`` so case-insensitive lexicon grammars (Currency
                word, Money word) preserve the old ``re.IGNORECASE`` behavior.
        """
        return re.compile(rf"{self.lookbehind}(?:{alternation}){self.lookahead}", flags)

    # Factory constructors — one per distinct semantic variant.
    @classmethod
    def word_sign(cls) -> BoundaryGuard:
        return cls(lookbehind=r"(?<![\w\-+\u2212])", lookahead=r"(?![\w\-+\u2212])")

    @classmethod
    def degree_word_sign(cls) -> BoundaryGuard:
        # SIUnit degree prefix: ° must be preserved in the lookbehind.
        return cls(
            lookbehind=r"(?<![°\w\-+\u2212/·⋅])", lookahead=r"(?![\w\-+\u2212/·⋅])"
        )

    @classmethod
    def digit(cls) -> BoundaryGuard:
        return cls(lookbehind=r"(?<!\d)", lookahead=r"(?!\d)")

    @classmethod
    def word_only(cls) -> BoundaryGuard:
        return cls(lookbehind=r"(?<!\w)", lookahead=r"(?!\w)")

    @classmethod
    def e164(cls) -> BoundaryGuard:
        return cls(lookbehind=r"(?<![\w:.])", lookahead=r"")

    @classmethod
    def e164_00(cls) -> BoundaryGuard:
        """International 00-prefix: like e164() but also excludes a leading "+".

        Contradictory "+00..." input is left to the e164 grammar; the 00
        grammar must not treat it as a 00-prefixed number.
        """
        return cls(lookbehind=r"(?<![\w:.+])", lookahead=r"")

    @classmethod
    def scheme_char(cls) -> BoundaryGuard:
        return cls(lookbehind=r"(?<![A-Za-z0-9+.\-])", lookahead=r"")

    @classmethod
    def phone_national(cls) -> BoundaryGuard:
        # 4-lookbehind chain: blocks a national number that is itself preceded
        # by a digit/+, a separator, an opening paren, or a digit/paren pair.
        return cls(
            lookbehind=(
                r"(?<![\d+])"
                r"(?<![\d+][\s.\-])"
                r"(?<![\d+][\s.\-]\()"
                r"(?<![\d+]\()"
            ),
            lookahead=r"(?!\d)",
        )

    @classmethod
    def ipv6_token(cls) -> BoundaryGuard:
        # Token boundary for IPv6: start/end of string or a delimiter class.
        return cls(
            lookbehind=r"(?:^|(?<=[\s,;([ ]))",
            lookahead=r"(?:$|(?=[\s,;().\]]))",
        )
