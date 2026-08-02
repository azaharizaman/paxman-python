"""Capability discovery registry.

Stores registered capabilities by name. Freezes after the first
``canonicalize()`` call so no new capabilities can be registered.
"""

from __future__ import annotations

from typing import Any

from paxman.core.capability import Capability
from paxman.core.errors import CapabilityError

_registry: dict[str, Capability[Any]] = {}
_frozen: bool = False


def register_capability(capability: Any) -> None:
    """Register a capability.

    The parameter is ``Any`` because this is a runtime validation entry
    point: untyped callers may pass non-Capability objects and the
    isinstance guard below provides the safety net.

    Raises:
        CapabilityError: If the registry is frozen, the argument is not a
            Capability instance, or a capability with the same name is
            already registered.
    """
    global _frozen
    if _frozen:
        raise CapabilityError(
            "Registry is frozen. Cannot register after first canonicalize() call."
        )
    if not isinstance(capability, Capability):
        raise CapabilityError(
            f"Expected Capability instance, got {type(capability).__name__}"
        )
    if capability.name in _registry:
        raise CapabilityError(f"Capability '{capability.name}' already registered.")
    _registry[capability.name] = capability


def get_capability(name: str) -> Capability[Any]:
    """Look up a capability by name.

    Raises:
        CapabilityError: If no capability with that name is registered.
    """
    if name not in _registry:
        raise CapabilityError(f"Unknown capability: '{name}'")
    return _registry[name]


def freeze_registry() -> None:
    """Freeze the registry so no more capabilities can be registered."""
    global _frozen
    _frozen = True


def is_registry_frozen() -> bool:
    """Check if the registry is frozen."""
    return _frozen


def reset_registry() -> None:
    """Reset the registry (for testing only)."""
    global _frozen
    _registry.clear()
    _frozen = False
