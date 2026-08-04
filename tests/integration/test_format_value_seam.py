"""Integration tests proving the engine routes formatting through the capability.

The engine must invoke ``Capability.format_value()`` on each rule-normalized
canonical value, before candidate deduplication, status, and replay hashing.
This test-only capability rewrites the canonical value so the seam is
observable end to end, and records the arguments it received so the test can
prove the engine passes the original notation and the contract's resolved
output format.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from paxman.core.capability import Capability
from paxman.core.contract import Contract
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Grammar, Provenance, Resolution, Rule, RuleStrategy
from paxman.engine.orchestrator import run_capability


@dataclass(frozen=True)
class _TokenNotation:
    """Minimal notation for the test-only formatting capability."""

    token: str


@dataclass(frozen=True)
class _FormatCall:
    """Record of the arguments the capability formatter received."""

    value: str
    output_format: str | None
    notation: _TokenNotation


class _TokenGrammar(Grammar[_TokenNotation]):
    """Grammar that recognizes a single fixed token."""

    name = "token_grammar"

    def recognize(self, text: str) -> list[_TokenNotation]:
        return [_TokenNotation(token=text)]


class _TokenRule(Rule[_TokenNotation]):
    """Rule that always matches and normalizes to a default value."""

    name = "token_rule"
    strategy = RuleStrategy.REGEX
    provenance = Provenance(
        authority="test",
        specification_name="test",
        kind="test",
        reference_url="https://test",
        version=None,
        lifecycle="active",
        publication_year=2024,
    )
    citation = "test"
    target_grammars = frozenset({"token_grammar"})
    requires_features = frozenset()

    def matches(self, notation: _TokenNotation, contract: Contract) -> bool:
        return True

    def normalize(self, notation: _TokenNotation, contract: Contract) -> str:
        return "default-value"


class _FormattingCapability(Capability[_TokenNotation]):
    """Test-only capability whose formatter rewrites the canonical value."""

    name = "formatting"
    version = "0.1.0"

    last_call: _FormatCall | None = None

    def get_grammars(self) -> list[Grammar[_TokenNotation]]:
        return [_TokenGrammar()]

    def get_rules(self) -> list[Rule[_TokenNotation]]:
        return [_TokenRule()]

    def format_value(
        self,
        value: str,
        output_format: str | None,
        notation: _TokenNotation,
    ) -> str:
        """Record the arguments and return a fixed formatted value."""
        _FormattingCapability.last_call = _FormatCall(
            value=value, output_format=output_format, notation=notation
        )
        return "formatted-value"


class _FormattingContract:
    """Minimal contract for the test-only formatting capability."""

    @property
    def capability_name(self) -> str:
        return "formatting"

    @property
    def active_grammars(self) -> list[str]:
        return ["token_grammar"]

    @property
    def excluded_rules(self) -> list[str]:
        return []

    @property
    def pinned_rules(self) -> list[str] | None:
        return None

    @property
    def year(self) -> int | None:
        return None

    @property
    def output_format(self) -> str | None:
        return "formatted"

    def as_dict(self) -> dict[str, object]:
        return {"capability_name": "formatting", "output_format": "formatted"}


@pytest.fixture(autouse=True)
def _clean_registry():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


class TestFormatValueSeam:
    @pytest.mark.integration
    def test_engine_routes_through_capability_formatter(self) -> None:
        """The engine applies the formatter and feeds it the right inputs."""
        _FormattingCapability.last_call = None
        register_capability(_FormattingCapability())
        contract = _FormattingContract()

        result = run_capability("token", contract)

        assert result.status == Resolution.SUCCESS
        assert result.candidates[0].value == "formatted-value"
        assert result.canonicalized_value == "formatted-value"

        call = _FormattingCapability.last_call
        assert call is not None
        assert call.value == "default-value"
        assert call.output_format == "formatted"
        assert call.notation == _TokenNotation(token="token")
