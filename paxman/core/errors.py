"""Core exception hierarchy for Paxman."""


class PaxmanError(Exception):
    """Base exception for all Paxman errors."""


class ContractError(PaxmanError):
    """Raised when contract is malformed or invalid."""


class CapabilityError(PaxmanError):
    """Raised when no capability can claim the process."""


class RecognitionError(PaxmanError):
    """Raised when grammar fails to parse input.

    ``original_error`` is the underlying exception for failures inside
    ``Grammar.recognize()``; it is ``None`` for structural failures the
    engine itself detects (e.g. a malformed match returned by a grammar).
    """

    def __init__(
        self, rule: str, message: str, original_error: Exception | None = None
    ) -> None:
        self.rule = rule
        self.original_error = original_error
        super().__init__(f"[{rule}] {message}")


class ValidationError(PaxmanError):
    """Raised when validation rule encounters unexpected error."""

    def __init__(self, rule: str, message: str, original_error: Exception) -> None:
        self.rule = rule
        self.original_error = original_error
        super().__init__(f"[{rule}] {message}")
