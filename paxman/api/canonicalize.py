"""Public API entry point for the paxman canonicalization library."""

from __future__ import annotations

from paxman.core.capability_contract import CapabilityContract
from paxman.engine.orchestrator import ExecutionResult, run_capability


def canonicalize(
    text: str,
    contract: CapabilityContract,
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
        TypeError: If text is not a str.
        CapabilityError: If no capability matches the contract's capability_name.
    """
    if not isinstance(text, str):
        raise TypeError(f"canonicalize() expects str, got {type(text).__name__}")
    return run_capability(text, contract)
