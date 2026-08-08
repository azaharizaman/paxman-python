"""Absolute-URI recognition grammar for the URL capability.

Recognizes absolute-URI/IRI spans (RFC 3986 §4.2, RFC 3987 §2.2) as
scheme-anchored shape matches. Shape-only per D7/D8: validity is the
rule layer's job — the grammar never validates the scheme, host, or
port, and carries no scheme table.
"""

from __future__ import annotations

import re

from paxman.capabilities.URL.notation import URLNotation
from paxman.core.domain import Grammar, RecognitionMatch

# Scheme anchor (RFC 3986 §3.1 / RFC 3987 §2.1):
#   ALPHA *( ALPHA / DIGIT / "+" / "-" / "." ) ":"
# Left boundary: not preceded by a scheme-legal character (word rejection).
# Body: URI/IRI code points (RFC 3986 §2 + RFC 3987 §2.2 ucschar) plus
#   tab/newline (Appendix C multi-line URIs); at least ONE body character
#   after the colon (D16).
# Right boundary: whitespace, control characters (except tab/newline),
#   "<", ">", '"' (Appendix C delimiters). Trailing "." kept.
_ABSOLUTE_URI_PATTERN = re.compile(
    r"(?<![A-Za-z0-9+.\-])"
    r"[A-Za-z][A-Za-z0-9+.\-]*:"
    r'[^ <>"\x00-\x08\x0B\x0C\x0E-\x1F\x7F]*[^ <>"\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'
)


class AbsoluteUriRecognition(Grammar[URLNotation]):
    """Absolute-URI recognition: extracts scheme-anchored URI spans."""

    name = "absolute_uri_recognition"

    def recognize(self, text: str) -> list[RecognitionMatch[URLNotation]]:
        """Extract absolute-URI spans from text.

        Shape-only recognition (D7/D8): any syntactically scheme-anchored
        absolute reference is emitted as a span; validity is decided by
        the rule layer, never here.

        Returns:
            Span-bearing RecognitionMatch per absolute-URI occurrence.
        """
        results: list[RecognitionMatch[URLNotation]] = []
        for match in _ABSOLUTE_URI_PATTERN.finditer(text):
            raw_span = match.group(0)
            # Appendix C: drop trailing ")" only while it outnumbers "(";
            # counting once then trimming the run equals the loop, in one pass.
            excess = raw_span.count(")") - raw_span.count("(")
            trim = 0
            while trim < excess and raw_span[-(trim + 1)] == ")":
                trim += 1
            if trim:
                raw_span = raw_span[:-trim]
            # D16: the pattern guarantees at least one body character after
            # the colon, and stripping only removes trailing ")" — so a span
            # reduced to the bare scheme has lost its body and must not be
            # emitted as an absolute-URI match.
            scheme_end = raw_span.find(":")
            if len(raw_span) <= scheme_end + 1:
                continue
            start = match.start()
            end = start + len(raw_span)
            results.append(
                RecognitionMatch(
                    notation=URLNotation(text=raw_span),
                    start=start,
                    end=end,
                    raw_text=raw_span,
                )
            )
        return results
