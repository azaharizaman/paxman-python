"""CapabilityContract base class — the unanimous contract surface.

Every capability contract MUST inherit from :class:`CapabilityContract` so
the standard fields, ``output_format`` resolution, and ``as_dict()``
serialization are implemented identically across capabilities.  This is the
homogeneity mandate that makes the contract surface structural rather than
documentary: future contributors cannot accidentally reintroduce the
per-capability drift that previously existed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True)
class CapabilityContract(ABC):
    """Base class for all capability contracts.

    Provides the unanimous contract surface shared by every capability:

    - ``output_format`` is **always optional** and validated/normalized by a
      single base ``__post_init__`` via :func:`resolve_output_format`.
    - ``as_dict()`` always emits the standard replay-deterministic keys plus
      capability-specific keys from ``_extra_dict_fields()``.
    - ``active_grammars`` is capability-specific and must be implemented by
      each subclass.

    Subclasses MUST:

    - Override the ``DEFAULT_OUTPUT_FORMAT`` and ``OFFERED_OUTPUT_FORMATS``
      class variables.
    - Set ``capability_name`` via ``field(default="<name>", init=False)``.
    - Implement the abstract ``active_grammars`` property.
    - Call ``super().__post_init__()`` first if they add their own
      ``__post_init__`` validation.
    - Override ``_extra_dict_fields()`` to emit capability-specific
      ``as_dict()`` keys.

    The class satisfies the :class:`Contract` protocol structurally.
    """

    DEFAULT_OUTPUT_FORMAT: ClassVar[str]
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]]

    capability_name: str = field(init=False)
    excluded_rules: tuple[str, ...] = ()
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None
    output_format: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize ``output_format``.

        Delegates to :func:`resolve_output_format` so every capability
        contract applies the same ``output_format`` policy: ``None``,
        ``"default"``, and the capability's ``DEFAULT_OUTPUT_FORMAT`` all
        resolve to the concrete default; offered alternatives resolve to
        themselves; any other value raises :class:`ContractError`.

        ``resolve_output_format`` is imported here rather than at module level
        to break the import cycle between this module and
        ``paxman.core.contract``, which re-exports ``CapabilityContract``.

        Raises:
            ContractError: If ``output_format`` is not an acceptable value.
        """
        from paxman.core.contract import resolve_output_format

        object.__setattr__(
            self,
            "output_format",
            resolve_output_format(
                self.output_format,
                capability_name=self.capability_name,
                offered_formats=type(self).OFFERED_OUTPUT_FORMATS,
                default_format=type(self).DEFAULT_OUTPUT_FORMAT,
            ),
        )

    @property
    @abstractmethod
    def active_grammars(self) -> Sequence[str]:
        """Grammar names to activate."""
        ...

    def as_dict(self) -> dict[str, Any]:
        """Serialize contract for replay_hash.

        Emits the standard keys, then appends ``_extra_dict_fields()``.  Key
        order is not significant to replay safety (the engine sorts keys
        before hashing); only the key/value set matters.
        """
        return {
            "capability_name": self.capability_name,
            "excluded_rules": self.excluded_rules,
            "pinned_rules": self.pinned_rules,
            "year": self.year,
            "output_format": self.output_format,
            **self._extra_dict_fields(),
        }

    def _extra_dict_fields(self) -> dict[str, Any]:
        """Extension hook for capability-specific ``as_dict()`` keys.

        Subclasses override this to emit their capability-specific fields
        (e.g. ``include_obfuscated``); the returned keys are appended to the
        standard keys produced by the base ``as_dict()``.
        """
        return {}
