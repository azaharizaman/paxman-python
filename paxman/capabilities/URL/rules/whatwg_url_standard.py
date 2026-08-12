"""WHATWG URL Standard rule: canonical URL serialization.

The WHATWG URL Standard defines the basic URL parser (Section 4.4) and the
URL serializer. This rule validates that a recognized notation is a
parseable URL and canonicalizes it to the standard serialization, e.g.
``HTTPS://Example.COM:443/path/../other`` -> ``https://example.com/other``.
"""

from __future__ import annotations

from paxman.capabilities.URL.notation import URLNotation
from paxman.capabilities.URL.parsing import parse_and_serialize
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="WHATWG",
    specification_name="URL Standard",
    kind="specification",
    reference_url="https://url.spec.whatwg.org/",
    version="Living Standard",
    lifecycle="active",
    publication_year=2026,
)


class WhatwgUrlStandard(Rule[URLNotation]):
    """WHATWG URL Standard Section 4.4: basic URL parser.

    Validates that the notation parses under the WHATWG basic URL parser
    and normalizes it to the standard serialization. Fatal validation
    errors (e.g. an out-of-range port or a malformed IPv6 literal) yield
    no resolution: ``matches()`` is False, so the pipeline reports INVALID
    for recognized input. Recoverable errors canonicalize (e.g. an empty
    port is dropped, host percent-encoding is applied, IPv4 parts are
    decoded from octal/hex to decimal).
    """

    name = "WHATWG URL Standard"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 4.4 (basic URL parser); RFC 3986 §3.1 / RFC 3987 §2 grammar"
    target_semantics = frozenset({"absolute_uri_recognition"})
    requires_features = frozenset()

    def matches(self, notation: URLNotation, contract: Contract) -> bool:
        """Check if the notation parses per the WHATWG basic URL parser.

        Args:
            notation: URL notation to validate.
            contract: Contract configuration.

        Returns:
            True when the basic URL parser succeeds; False on fatal
            validation errors.
        """
        return parse_and_serialize(notation.text) is not None

    def normalize(self, notation: URLNotation, contract: Contract) -> str:
        """Normalize to the WHATWG standard serialization.

        Args:
            notation: Validated notation.
            contract: Contract configuration.

        Returns:
            The canonical serialization of the parsed URL.

        Note:
            Never raises. Falls back to the input text when parsing fails —
            unreachable after ``matches()`` (which requires a successful
            parse); this is a defensive best-effort for direct misuse.
        """
        serialized = parse_and_serialize(notation.text)
        if serialized is None:
            return notation.text  # unreachable post-matches(); defensive best-effort
        return serialized
