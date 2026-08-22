"""IBAN capability — wires grammars and rules together."""

from __future__ import annotations

from collections.abc import Sequence

from paxman.capabilities.IBAN.contract import IBANContract
from paxman.capabilities.IBAN.grammar.iban_recognition import (
    IBANRecognition,
)
from paxman.capabilities.IBAN.notation import IBANNotation
from paxman.capabilities.IBAN.rules.iso_ed2020 import IBANRule
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule


class IBANCapability(Capability[IBANNotation]):
    """IBAN canonicalization capability (scaffold).

    TODO(scaffold): describe what this capability recognizes and the
    authoritative specification(s) it validates against.
    """

    name = "iban"

    def get_grammars(self) -> list[Grammar[IBANNotation]]:
        """Return the default grammar instances."""
        return [IBANRecognition()]

    def get_rules(self) -> list[Rule[IBANNotation]]:
        """Return the default validation rule instances."""
        return [IBANRule()]

    @staticmethod
    def create_contract(
        *,
        excluded_rules: Sequence[str] | None = None,
        pinned_rules: Sequence[str] | None = None,
        year: int | None = None,
        output_format: str | None = None,
        extra_grammars: Sequence[str] | None = None,
    ) -> IBANContract:
        """Factory method for creating contracts with proper defaults.

        Args:
            excluded_rules: Rule names to exclude.
            pinned_rules: Pin to specific rules (takes precedence over
                excluded_rules).
            year: Year for temporal filtering.
            output_format: Output format for canonical values. Optional;
                None/"default"/"electronic" resolve to "electronic".
            extra_grammars: Community grammar names (opt-in) to run
                alongside the shipped grammars, in order (SEAM — the
                surface guard's common block ends with this parameter).

        Returns:
            Configured IBANContract instance.
        """
        return IBANContract(
            excluded_rules=tuple(excluded_rules) if excluded_rules else (),
            pinned_rules=tuple(pinned_rules) if pinned_rules is not None else None,
            year=year,
            output_format=output_format,
            extra_grammars=tuple(extra_grammars) if extra_grammars else (),
        )

    # format_value: NOT overridden — the canonical value IS the default
    # format, and there are no offered alternatives. The Capability base
    # provides the identity formatter. TODO(scaffold): override if you offer
    # alternative output formats.
