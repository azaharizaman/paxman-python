"""Public API entry point for the paxman canonicalization library."""

from __future__ import annotations

from paxman.core.capability import Capability
from paxman.core.contract import Contract
from paxman.core.discovery import CapabilityError, get_capability
from paxman.engine.orchestrator import ExecutionResult, run_capability


def canonicalize(
    text: str,
    contract: Contract,
) -> ExecutionResult:
    """Canonicalize text using the specified contract.

    This is the main entry point for the paxman library.
    It runs the full pipeline: recognition -> validation -> canonicalization.

    Args:
        text: The input text to canonicalize.
        contract: The contract configuration for this capability.

    Returns:
        ExecutionResult with status, canonicalized_value, candidates, etc.

    Raises:
        ValueError: If no capability matches the contract's capability_name.
    """
    _find_capability(contract.capability_name)
    return run_capability(text, contract)


def _find_capability(name: str) -> Capability:
    """Find a capability by name from the registry.

    Raises:
        ValueError: If no capability with that name is registered.
    """
    try:
        return get_capability(name)
    except CapabilityError as exc:
        raise ValueError(f"No capability found with name '{name}'") from exc
