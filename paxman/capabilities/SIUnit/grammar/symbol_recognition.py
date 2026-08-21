"""Symbol recognition grammar for SI Unit (staged pipeline).

Recognizes unit symbols exactly as written (case-exact): base symbols
("m", "kg"), derived special-name symbols ("Pa", "°C"), non-SI symbols
("min", "L"), prefix symbols ("k", "M") and prefixed units ("km", "MHz").
Each recognition emits a span-bearing RecognitionMatch over the symbol
text. Recognition only: no validation, no canonicalization (D1/D2/D6).

The single bespoke regex from the legacy grammar is reproduced exactly
as a ``RegexStage`` body guarded by ``BoundaryGuard.degree_word_sign()``
(preserving the ``°`` degree prefix in the lookbehind). The split-prefix
shape ("k g" -> ``split_symbol_prefix``) is computed inline in the
notation factory, byte-identically to the legacy ``recognize()``.
"""

from __future__ import annotations

import re

from paxman.capabilities.SIUnit.grammar.data.prefix_tokens import PREFIX_SYMBOL_TOKENS
from paxman.capabilities.SIUnit.grammar.data.unit_symbol_tokens import SYMBOL_TOKENS
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.core.grammar import BoundaryGuard, PipelineGrammar, RegexStage, StandardPre

# Prefix symbols that coincide with a standalone unit symbol (a fixed SI
# fact): "m" (milli + metre), "h" (hecto + hour), "a" (atto + annum/are),
# "d" (deci + day). A spaced pair led by one of these is ambiguous between a
# broken prefix and a valid two-unit expression (e.g. "m s" = metre second),
# so it stays two units — never a rejectable split.
DUAL_ROLE_PREFIX_SYMBOLS = frozenset({"a", "d", "h", "m"})
# Prefix-ONLY symbols (e.g. "k", "da", "µ") for O(1) split detection. The
# generated SYMBOL_TOKENS table leaks every prefix symbol as a standalone
# token, so prefix-only cannot be derived by set difference against it; the
# four dual-role symbols above are subtracted explicitly instead.
PREFIX_ONLY_SYMBOLS = frozenset(PREFIX_SYMBOL_TOKENS) - DUAL_ROLE_PREFIX_SYMBOLS

# Word chars, signs, and the compound separators block a token: they
# never merge into a symbol and never split a compound (D2). The degree
# sign is in the block set too, so "25°C" cannot fall back to a bare "C"
# (coulomb) after the "°C" token is rejected. The left boundary is a
# lookbehind and the right a lookahead — a lookahead placed before the
# token would see the token's own first character (a word char) and
# reject the match before the token is even consumed.
_SYMBOL_ALT = "|".join(re.escape(t) for t in SYMBOL_TOKENS)
_PREFIX_ONLY_SYMBOL_ALT = "|".join(re.escape(t) for t in sorted(PREFIX_ONLY_SYMBOLS))
# A prefix-only symbol split across whitespace from its unit ("k g") is captured
# as ONE span so the inner unit ("g") is consumed and never emitted as a
# competing candidate. The split is always rejected by the rules (a prefix
# symbol must bind tightly with no space — "k g" is not "kg"). Dual-role
# prefix symbols (m, h, a, d) are excluded so spaced unit pairs like "m s"
# (metre second) survive as two units. A single outer named group wraps the
# non-capturing alternatives so the whole token is captured as one span.
_SYMBOL_BODY = (
    r"(?:(?:" + _PREFIX_ONLY_SYMBOL_ALT + r")\s+(?:" + _SYMBOL_ALT + r"))"
    r"|"
    r"(?:(?:" + _SYMBOL_ALT + r"))"
)
# The degree_word_sign guard preserves the ° in the lookbehind exactly as the
# legacy grammar's _LOOKBEHIND/_LOOKAHEAD literals did — no hard-coded
# lookaround in this file (ADR-0008 D5).
_GUARD = BoundaryGuard.degree_word_sign()
_SYMBOL_PATTERN = (
    _GUARD.lookbehind + r"(?P<tok>" + _SYMBOL_BODY + r")" + _GUARD.lookahead
)


def _symbol_notation(match: re.Match[str]) -> SIUnitNotation:
    """Map a matched symbol token to its split/attached notation.

    Mirrors the legacy recognize(): a prefix-only symbol followed by a space
    and a unit symbol (e.g. "k g") is a rejectable split; otherwise the token
    is an attached symbol. Case is preserved (symbols are case-exact).
    """
    token = match.group("tok")
    parts = token.split()
    if len(parts) >= 2 and parts[0] in PREFIX_ONLY_SYMBOLS:
        shape = "split_symbol_prefix"
    else:
        shape = "symbol"
    return SIUnitNotation(text=token, shape=shape)


class SymbolRecognition(PipelineGrammar[SIUnitNotation]):
    """Grammar: symbol_recognition — case-exact unit symbol tokens."""

    name = "symbol_recognition"
    semantics = "symbol_recognition"  # SEAM (ADR-0003): identity id

    pre = StandardPre[SIUnitNotation](empty_guard=True)
    regex = RegexStage[SIUnitNotation](
        pattern=_SYMBOL_PATTERN,
        notation_fn=_symbol_notation,
    )
