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
from paxman.core.domain import (
    Grammar,
    Provenance,
    RecognitionMatch,
    Resolution,
    Rule,
    RuleStrategy,
)
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

    def recognize(self, text: str) -> list[RecognitionMatch[_TokenNotation]]:
        return [
            RecognitionMatch(
                notation=_TokenNotation(token=text),
                start=0,
                end=len(text),
                raw_text=text,
            )
        ]


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


class _DualTokenGrammar(Grammar[_TokenNotation]):
    """Grammar that recognizes two distinct tokens."""

    name = "dual_token_grammar"

    def recognize(self, text: str) -> list[RecognitionMatch[_TokenNotation]]:
        return [
            RecognitionMatch(
                notation=_TokenNotation(token="alpha"),
                start=0,
                end=5,
                raw_text="alpha",
            ),
            RecognitionMatch(
                notation=_TokenNotation(token="beta"),
                start=5,
                end=9,
                raw_text="beta",
            ),
        ]


class _DualTokenRule(Rule[_TokenNotation]):
    """Rule that collapses both tokens to the same default canonical value."""

    name = "dual_token_rule"
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
    target_grammars = frozenset({"dual_token_grammar"})
    requires_features = frozenset()

    def matches(self, notation: _TokenNotation, contract: Contract) -> bool:
        return True

    def normalize(self, notation: _TokenNotation, contract: Contract) -> str:
        return "default-value"


class _DualFormattingCapability(Capability[_TokenNotation]):
    """Capability whose formatter distinguishes identically-normalized tokens."""

    name = "dual_formatting"
    version = "0.1.0"

    last_calls: list[_FormatCall] = []

    def get_grammars(self) -> list[Grammar[_TokenNotation]]:
        return [_DualTokenGrammar()]

    def get_rules(self) -> list[Rule[_TokenNotation]]:
        return [_DualTokenRule()]

    def format_value(
        self,
        value: str,
        output_format: str | None,
        notation: _TokenNotation,
    ) -> str:
        """Record the call and render a token-specific formatted value."""
        _DualFormattingCapability.last_calls.append(
            _FormatCall(value=value, output_format=output_format, notation=notation)
        )
        return f"formatted-{notation.token}"


class _DualFormattingContract:
    """Minimal contract for the dual-token formatting capability."""

    @property
    def capability_name(self) -> str:
        return "dual_formatting"

    @property
    def active_grammars(self) -> list[str]:
        return ["dual_token_grammar"]

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
        return {"capability_name": "dual_formatting", "output_format": "formatted"}


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

    @pytest.mark.integration
    def test_formatting_runs_before_dedup_and_status(self) -> None:
        """Formatting is applied per candidate before dedup and status.

        Both tokens normalize to the same default value. If the engine
        deduplicated or decided status before formatting, the two candidates
        would collapse into one and the result would be SUCCESS. Because the
        formatter runs first and renders token-specific values, the two
        distinct formatted candidates survive and the status is AMBIGUOUS.
        """
        _DualFormattingCapability.last_calls = []
        register_capability(_DualFormattingCapability())
        contract = _DualFormattingContract()

        # _DualTokenGrammar hardcodes spans for "alphabeta": (0, 5) and (5, 9).
        result = run_capability("alphabeta", contract)

        assert result.status == Resolution.AMBIGUOUS
        assert result.canonicalized_value is None
        assert {c.value for c in result.candidates} == {
            "formatted-alpha",
            "formatted-beta",
        }
        assert len(_DualFormattingCapability.last_calls) == 2
        assert _DualFormattingCapability.last_calls == [
            _FormatCall(
                value="default-value",
                output_format="formatted",
                notation=_TokenNotation(token="alpha"),
            ),
            _FormatCall(
                value="default-value",
                output_format="formatted",
                notation=_TokenNotation(token="beta"),
            ),
        ]
