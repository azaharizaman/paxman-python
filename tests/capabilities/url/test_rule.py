"""Tests for the WHATWG URL Standard rule."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from paxman.capabilities.URL.notation import URLNotation
from paxman.capabilities.URL.rules.whatwg_url_standard import (
    PUBLICATION,
    WhatwgUrlStandard,
)
from paxman.core.domain import RuleStrategy

pytestmark = [pytest.mark.capability, pytest.mark.url]


@dataclass(frozen=True)
class _RuleContract:
    """Minimal Contract-protocol double for rule-level tests.

    The WHATWG rule never reads the contract (PARSER strategy: pure
    parse-to-serialize on the notation), so a structural double suffices
    until Task 6 lands the real URLCapabilityContract.
    """

    capability_name: str = "url"
    active_grammars: tuple[str, ...] = ("absolute_uri_recognition",)
    excluded_rules: tuple[str, ...] = ()
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None
    output_format: str | None = "url"
    _dict: dict[str, Any] = field(default_factory=dict, compare=False)

    def as_dict(self) -> dict[str, Any]:
        return dict(self._dict)


class TestWhatwgUrlStandard:
    """WHATWG URL Standard rule tests."""

    def setup_method(self) -> None:
        self.rule = WhatwgUrlStandard()
        self.contract = _RuleContract()

    def test_rule_metadata(self) -> None:
        """Rule metadata matches §1 (homogeneity contract, Money style)."""
        assert self.rule.name == "WHATWG URL Standard"
        assert self.rule.strategy == RuleStrategy.PARSER
        assert self.rule.target_grammars == frozenset({"absolute_uri_recognition"})
        assert self.rule.requires_features == frozenset()
        assert (
            self.rule.citation
            == "Section 4.4 (basic URL parser); RFC 3986 §3.1 / RFC 3987 §2 grammar"
        )

    def test_provenance_attributes(self) -> None:
        """Provenance carries the WHATWG URL Standard citation (§1)."""
        assert self.rule.provenance.authority == "WHATWG"
        assert self.rule.provenance.specification_name == "URL Standard"
        assert self.rule.provenance.kind == "specification"
        assert self.rule.provenance.reference_url == "https://url.spec.whatwg.org/"
        assert self.rule.provenance.version == "Living Standard"
        assert self.rule.provenance.lifecycle == "active"
        assert self.rule.provenance.publication_year == 2026

    def test_success_provenance(self) -> None:
        """The rule's provenance IS the module PUBLICATION (attached to every
        resolution by the pipeline)."""
        assert self.rule.provenance is PUBLICATION

    def test_surface_matches_and_normalize(self) -> None:
        """Real pipeline surface: matches() -> bool, normalize() -> str.

        The plan's §1 `validate() -> list[Resolution]` interface does not
        exist in this codebase — the Rule ABC requires matches/normalize
        and the orchestrator calls exactly those (orchestrator.py
        _collect_candidates). Adapted accordingly.
        """
        notation = URLNotation("https://example.com/")
        assert isinstance(self.rule.matches(notation, self.contract), bool)
        assert isinstance(self.rule.normalize(notation, self.contract), str)

    def test_success_case(self) -> None:
        """Milestone case resolves to the WHATWG canonical serialization."""
        notation = URLNotation("HTTPS://Example.COM:443/path/../other")
        assert self.rule.matches(notation, self.contract) is True
        assert (
            self.rule.normalize(notation, self.contract) == "https://example.com/other"
        )

    def test_milestone_via_rule(self) -> None:
        """Plan §3 milestone asserted through the rule (not just the parser)."""
        notation = URLNotation("HTTPS://Example.COM:443/path/../other")
        assert (
            self.rule.normalize(notation, self.contract) == "https://example.com/other"
        )

    def test_silent_recovery_succeeds(self) -> None:
        """D8: tab/newline stripped pre-parse is a silent recovery — canonical
        value returned, never a fatal error."""
        notation = URLNotation("http://exa\nmple.com/")
        assert self.rule.matches(notation, self.contract) is True
        assert self.rule.normalize(notation, self.contract) == "http://example.com/"

    @pytest.mark.parametrize(
        "raw",
        [
            # §4.1 fatal validation errors — recognized but never canonicalized
            "http://example.com:99999/",  # port > 65535
            "http://example.com:80x/",  # non-digit in port
            "http://example.com:80:90/",  # two port components
            "http://exa mple.com/",  # space in host
            "http://[::1",  # unclosed IPv6 literal
        ],
    )
    def test_fatal_validation_no_matches(self, raw: str) -> None:
        """Fatal WHATWG errors yield no resolution — matches() False, so the
        pipeline reports INVALID for recognized input (plan §1)."""
        notation = URLNotation(raw)
        assert self.rule.matches(notation, self.contract) is False

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # §4.2 silent recoveries — canonical value, recovery not fatal
            ("http://example.com:", "http://example.com/"),  # empty port dropped
            ("http://example.com:0/", "http://example.com:0/"),  # port 0 preserved
            ("http://example.com\\path", "http://example.com/path"),  # backslash -> /
            ("http://%65xample.com/", "http://example.com/"),  # host percent-decoding
            ("http://example.com/a b", "http://example.com/a%20b"),  # path space
            (
                "http://user name@example.com/",
                "http://user%20name@example.com/",
            ),  # userinfo space
            ("http://[2001:db8::1]/", "http://[2001:db8::1]/"),  # IPv6 preserved
            ("file://localhost/etc/hosts", "file:///etc/hosts"),  # file host dropped
            # §4.3 percent-encoding preserved byte-for-byte
            ("http://example.com/a%2fb", "http://example.com/a%2fb"),
            ("http://example.com/%41", "http://example.com/%41"),
            ("http://example.com/~x", "http://example.com/~x"),
            ("http://example.com/%zz", "http://example.com/%zz"),
            ("http://example.com/a%", "http://example.com/a%"),
            # §4.4 query/fragment verbatim
            ("http://example.com/?a=b c", "http://example.com/?a=b%20c"),
            ("http://example.com/?x=%7e", "http://example.com/?x=%7e"),
            ("http://example.com/?a+b", "http://example.com/?a+b"),
            ("http://example.com/?", "http://example.com/?"),
            ("http://example.com/#", "http://example.com/#"),
            ("http://example.com/#a b", "http://example.com/#a%20b"),
            # §4.5 non-special schemes
            ("mailto:user@example.com", "mailto:user@example.com"),
            ("GIT://github.com/user/repo", "git://github.com/user/repo"),
            ("ssh://user@host:22/path", "ssh://user@host:22/path"),
            ("ftp://example.com:21/a", "ftp://example.com/a"),
            ("ws://example.com:80/a", "ws://example.com/a"),
            ("mailto:user@münchen.de", "mailto:user@m%C3%BCnchen.de"),
            ("data:text/plain,hello world", "data:text/plain,hello world"),
            ("git://github.com/user/my repo", "git://github.com/user/my%20repo"),
            ("custom:scheme with space", "custom:scheme with space"),
            # §4.6 hosts / IPv4
            ("http://010.010.010.010/", "http://8.8.8.8/"),  # octal -> decimal
            ("http://192.168.001.001/", "http://192.168.1.1/"),
            ("http:///path", "http://path/"),
            ("http://münchen.de/", "http://xn--mnchen-3ya.de/"),
            ("http://caf%C3%A9.de/", "http://xn--caf-dma.de/"),
            ("http://café.example/", "http://xn--caf-dma.example/"),
            ("http://faß.de/", "http://xn--fa-hia.de/"),  # ß UTS #46 deviation
            # §4.7 no Unicode normalization — two distinct outputs
            ("http://example.com/café", "http://example.com/caf%C3%A9"),
            (
                "http://example.com/cafe\u0301",
                "http://example.com/cafe%CC%81",
            ),  # NFD stays distinct
        ],
    )
    def test_normalize_canonical(self, raw: str, expected: str) -> None:
        """Every §4 evidence row canonicalizes to the WHATWG serialization
        (node-verified byte-for-byte)."""
        notation = URLNotation(raw)
        assert self.rule.matches(notation, self.contract) is True
        assert self.rule.normalize(notation, self.contract) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            # full §4 corpus — every input above plus the fatal rows
            "http://example.com:99999/",
            "http://example.com:80x/",
            "http://example.com:80:90/",
            "http://exa mple.com/",
            "http://[::1",
            "http://exa\nmple.com/",
            "http://example.com:",
            "http://example.com:0/",
            "http://example.com\\path",
            "http://%65xample.com/",
            "http://example.com/a b",
            "http://user name@example.com/",
            "http://[2001:db8::1]/",
            "file://localhost/etc/hosts",
            "http://example.com/a%2fb",
            "http://example.com/%41",
            "http://example.com/~x",
            "http://example.com/%zz",
            "http://example.com/a%",
            "http://example.com/?a=b c",
            "http://example.com/?x=%7e",
            "http://example.com/?a+b",
            "http://example.com/?",
            "http://example.com/#",
            "http://example.com/#a b",
            "mailto:user@example.com",
            "GIT://github.com/user/repo",
            "ssh://user@host:22/path",
            "ftp://example.com:21/a",
            "ws://example.com:80/a",
            "mailto:user@münchen.de",
            "data:text/plain,hello world",
            "git://github.com/user/my repo",
            "custom:scheme with space",
            "http://010.010.010.010/",
            "http://192.168.001.001/",
            "http:///path",
            "http://münchen.de/",
            "http://caf%C3%A9.de/",
            "http://café.example/",
            "http://faß.de/",
            "http://example.com/café",
            "http://example.com/cafe\u0301",
        ],
    )
    def test_never_raises(self, raw: str) -> None:
        """No §4 corpus input makes matches() or normalize() raise."""
        notation = URLNotation(raw)
        self.rule.matches(notation, self.contract)
        self.rule.normalize(notation, self.contract)
