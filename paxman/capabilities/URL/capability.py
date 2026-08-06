"""URL capability — wires grammars and rules together."""

from __future__ import annotations

from paxman.capabilities.URL.notation import URLNotation
from paxman.core.capability import Capability

__all__ = ["URLCapability"]


class URLCapability(Capability[URLNotation]):
    """URL canonicalization capability."""

    name = "url"
    version = "1.0.0"

    # Task 7: full capability body — get_grammars(), get_rules(),
    # static create_contract(), format_value().
