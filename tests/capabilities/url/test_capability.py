"""Tests for URLCapability: wiring, contract factory, and formatter."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import pytest

from paxman.capabilities.URL.capability import URLCapability
from paxman.capabilities.URL.grammar.absolute_uri_recognition import (
    AbsoluteUriRecognition,
)
from paxman.capabilities.URL.notation import URLNotation
from paxman.capabilities.URL.rules.whatwg_url_standard import WhatwgUrlStandard
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule

pytestmark = [pytest.mark.capability, pytest.mark.url]


class TestURLCapability:
    """URLCapability metadata and grammar/rule wiring."""

    def test_is_capability_subclass(self) -> None:
        """URLCapability is a concrete Capability."""
        cap = URLCapability()
        assert isinstance(cap, Capability)

    def test_name(self) -> None:
        """Capability name is 'url'."""
        assert URLCapability().name == "url"

    def test_get_grammars_returns_url_grammar(self) -> None:
        """get_grammars() returns exactly the absolute-URI grammar."""
        cap = URLCapability()
        grammars = cap.get_grammars()
        assert len(grammars) == 1
        assert isinstance(grammars[0], AbsoluteUriRecognition)
        assert isinstance(grammars[0], Grammar)

    def test_grammar_name(self) -> None:
        """Absolute-URI grammar has expected name."""
        grammar = AbsoluteUriRecognition()
        assert grammar.name == "absolute_uri_recognition"

    def test_get_rules_returns_whatwg_rule(self) -> None:
        """get_rules() returns exactly the WHATWG URL Standard rule."""
        cap = URLCapability()
        rules = cap.get_rules()
        assert len(rules) == 1
        assert isinstance(rules[0], WhatwgUrlStandard)
        assert isinstance(rules[0], Rule)

    def test_rule_name(self) -> None:
        """WHATWG rule has expected name."""
        rule = WhatwgUrlStandard()
        assert rule.name == "WHATWG URL Standard"


class TestURLCapabilityCreateContract:
    """URLCapability.create_contract — the unanimous common block."""

    def test_create_contract_keyword_only(self) -> None:
        """create_contract is static and keyword-only (unanimous surface)."""
        with pytest.raises(TypeError):
            cast(Callable[..., object], URLCapability.create_contract)(
                "url", (), (), None, "url"
            )

    def test_create_contract_defaults(self) -> None:
        """Default create_contract resolves a url contract."""
        contract = URLCapability().create_contract(
            excluded_rules=(),
            pinned_rules=(),
            year=None,
            output_format="url",
        )
        assert contract.capability_name == "url"
        assert contract.active_grammars is None

    def test_create_contract_excludes_rule(self) -> None:
        """Excluded rules propagate into the contract."""
        contract = URLCapability().create_contract(
            excluded_rules=("WHATWG URL Standard",),
            pinned_rules=(),
            year=None,
            output_format="url",
        )
        assert contract.excluded_rules == ("WHATWG URL Standard",)
        assert contract.pinned_rules == ()

    def test_create_contract_pins_rule(self) -> None:
        """Pinned rules propagate into the contract (pinning wins)."""
        contract = URLCapability().create_contract(
            excluded_rules=("WHATWG URL Standard",),
            pinned_rules=("WHATWG URL Standard",),
            year=None,
            output_format="url",
        )
        assert contract.pinned_rules == ("WHATWG URL Standard",)


class TestURLCapabilityFormatValue:
    """URLCapability.formatter — URL offers no alternative formats.

    URL's OFFERED_OUTPUT_FORMATS is empty, so the capability inherits the
    base identity formatter (the WHATWG serialization IS the value, D14).
    Unknown-format rejection is the contract's job (ContractError at
    construction), not the formatter's — see test_contract.py.
    """

    def test_format_value_default_keeps_value(self) -> None:
        """Rendering in the default format leaves the canonical value unchanged."""
        cap = URLCapability()
        notation = URLNotation(text="https://example.com/a b")
        assert cap.format_value("https://example.com/a b", "url", notation) == (
            "https://example.com/a b"
        )

    def test_format_value_unoffered_format_is_identity(self) -> None:
        """An unoffered format still renders identity (base behavior).

        The surface guard (test_capability_surface.py) requires identity
        'regardless of the requested format' for capabilities with empty
        OFFERED_OUTPUT_FORMATS — even None.
        """
        cap = URLCapability()
        notation = URLNotation(text="https://example.com/a b")
        assert cap.format_value("https://example.com/a b", "compact", notation) == (
            "https://example.com/a b"
        )
        assert cap.format_value("https://example.com/a b", None, notation) == (
            "https://example.com/a b"
        )
