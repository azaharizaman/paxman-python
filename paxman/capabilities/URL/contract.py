"""URL contract for URL capability."""

from __future__ import annotations

from dataclasses import dataclass

from paxman.core.capability_contract import CapabilityContract


@dataclass(frozen=True)
class URLCapabilityContract(CapabilityContract):
    """User-facing contract for URL capability."""

    # Task 6: full contract body — DEFAULT_OUTPUT_FORMAT = "url",
    # OFFERED_OUTPUT_FORMATS, capability_name field, active_grammars,
    # _extra_dict_fields().
