"""URL contract for URL capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from paxman.core.capability_contract import CapabilityContract


@dataclass(frozen=True)
class URLCapabilityContract(CapabilityContract):
    """User-facing contract for URL capability.

    D14 — no feature flags: every recognized URL is validated by the single
    WHATWG URL Standard rule, and the canonical value IS the WHATWG
    serialization (identity formatter). The contract therefore adds no
    capability-specific keys to the replay-hash surface.
    """

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "url"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset()

    capability_name: str = field(default="url", init=False)

    @property
    def active_grammars(self) -> tuple[str, ...]:
        """All grammars active by default.

        Returns:
            The single recognition grammar name.
        """
        return ("absolute_uri_recognition",)

    def _extra_dict_fields(self) -> dict[str, object]:
        """Serialize capability-specific fields for replay hash.

        Returns:
            Empty dict — no feature flags (D14), so no extra contract keys.
        """
        return {}
