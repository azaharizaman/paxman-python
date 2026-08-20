"""Contract protocol — ENGINE-INTERNAL since ADR-0007.

Public contracts MUST inherit `CapabilityContract`. This Protocol is retained
only for internal structural typing of the engine boundary and is NOT part of
the public API. Do not import it from `paxman.core` — import `CapabilityContract`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, cast, runtime_checkable

from paxman.core.capability_contract import CapabilityContract as CapabilityContract
from paxman.core.errors import ContractError


@runtime_checkable
class Contract(Protocol):
    """Base protocol for all capability contracts."""

    @property
    def capability_name(self) -> str:
        """Name of the capability this contract configures."""
        ...

    @property
    def active_grammars(self) -> Sequence[str] | None:
        """Grammar names to activate.

        ``None`` (the base-class default) means "all shipped grammars, in
        ``get_grammars()`` declaration order" — the engine falls back to the
        capability's shipped grammar list.
        """
        ...

    @property
    def excluded_rules(self) -> Sequence[str]:
        """Rule names to exclude."""
        ...

    @property
    def pinned_rules(self) -> Sequence[str] | None:
        """Pin to specific rules by name. If set, ONLY these rules run.

        Takes precedence over excluded_rules — when pinned_rules is non-None,
        excluded_rules is ignored. Year filtering still applies after pinning.
        An empty tuple () pins to nothing (no rules run).
        """
        ...

    @property
    def year(self) -> int | None:
        """Year for temporal filtering (publication_year <= year)."""
        ...

    @property
    def output_format(self) -> str | None:
        """Output format for canonical values (e.g., 'ISO', 'US')."""
        ...


def resolve_output_format(
    value: str | None,
    *,
    capability_name: str,
    offered_formats: frozenset[str],
    default_format: str,
) -> str:
    """Validate and normalize an ``output_format`` value.

    ``output_format`` is **always optional**, regardless of capability. The
    only accepted values are:

    - ``None`` (omitted) — equivalent to ``"default"`` and to
      ``default_format``.
    - ``"default"`` — reverts to the capability's default canonical output
      (``default_format``).
    - ``default_format`` — the capability's declared default canonical output;
      equivalent to omitting ``output_format``.
    - Any value in ``offered_formats`` — an explicit alternative format the
      capability supports.

    All of the above resolve to a **concrete** format string (never ``None``).
    The first three are treated identically by rules: they leave the canonical
    value untouched (no reformatting). Any other value — including the strings
    ``""``, ``"None"``, ``"none"``, or a misspelled format name — is a contract
    violation and raises :class:`ContractError`.

    Args:
        value: The configured ``output_format`` value (may be ``None``).
        capability_name: Capability name, used in the error message.
        offered_formats: Alternative output formats the capability offers
            beyond its default canonical format.
        default_format: The capability's declared default canonical output
            format. Every capability must declare one; it is always a concrete
            string.

    Returns:
        The resolved concrete ``output_format`` string.

    Raises:
        ContractError: If ``value`` is not acceptable.
    """
    candidate = cast(object, value)
    if candidate is None or candidate == "default" or candidate == default_format:
        return default_format
    if not isinstance(candidate, str):
        raise ContractError(
            f"output_format for {capability_name} capability must be a string, "
            f"got {value!r}"
        )
    if candidate in offered_formats:
        return candidate
    if offered_formats:
        allowed = f"'default', {default_format!r}, or one of {sorted(offered_formats)}"
    else:
        allowed = (
            f"'default' or {default_format!r} "
            "(this capability has a single canonical output format)"
        )
    raise ContractError(
        f"Invalid output_format for {capability_name} capability: {value!r}. "
        f"Must be {allowed}"
    )
