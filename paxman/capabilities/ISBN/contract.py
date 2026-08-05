"""ISBN contract — user-facing configuration for ISBN capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from paxman.core.contract import CapabilityContract


@dataclass(frozen=True)
class ISBNContract(CapabilityContract):
    """User-facing configuration for ISBN capability.

    Attributes:
        capability_name: Fixed to "isbn" (not user-settable).
        output_format: Canonical output format ("isbn13" default, "hyphenated"
            offered). Optional — None/"default"/"isbn13" all resolve to
            "isbn13".
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over excluded_rules).
        year: Year for temporal filtering.
        include_isbn10: Enable legacy ISBN-10 input recognition.
        include_range_validation: Gate the Range Message validation rule.
    """

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "isbn13"
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset({"hyphenated"})

    capability_name: str = field(default="isbn", init=False)

    # Capability-specific fields
    include_isbn10: bool = True
    include_range_validation: bool = False

    @property
    def active_grammars(self) -> list[str]:
        """isbn13 grammar always active; isbn10 gated by include_isbn10.

        Returns:
            List of grammar names to activate.
        """
        grammars = ["isbn13_recognition"]
        if self.include_isbn10:
            grammars.append("isbn10_recognition")
        return grammars

    def _extra_dict_fields(self) -> dict[str, object]:
        """Serialize capability-specific fields for replay hash.

        Returns:
            Dictionary of include_isbn10 and include_range_validation flags.
        """
        return {
            "include_isbn10": self.include_isbn10,
            "include_range_validation": self.include_range_validation,
        }
