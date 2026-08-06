"""Integration tests for the URL capability pipeline."""

import pytest

from paxman.api import canonicalize
from paxman.capabilities.URL.capability import URLCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution


@pytest.fixture(autouse=True)
def _fresh_registry() -> None:
    """Reset the capability registry before and after each test."""
    reset_registry()
    yield
    reset_registry()


class TestURLPipeline:
    """Full-pipeline tests for the URL capability.

    Locked semantics (research doc §4, plan §1):
    - the WHATWG basic URL parser is a silent-recovery state machine (D8):
      recoverable issues (tab/newline in host, empty port, octal IPv4,
      backslash path, ``file://localhost`` host) canonicalize; fatal ones
      (port > 65535, unclosed IPv6 literal) yield INVALID;
    - percent-encoding is preserved byte-for-byte (``%zz``, bare ``%``) and
      case is kept (``%2f`` != ``%2F``); empty ``?`` and empty ``#`` survive;
    - opaque schemes (``mailto:``) are returned verbatim;
    - IDNA: ``münchen.de`` -> ``xn--mnchen-3ya.de`` (UTS #46), ``ß`` per
      deviation;
    - no Unicode normalization: ``café`` != ``cafe\\u0301`` (two distinct
      canonical outputs).
    """

    @pytest.mark.integration
    def test_milestone_full_pipeline(self) -> None:
        """The §1 milestone resolves end-to-end through canonicalize().

        Plan Task 9 asserts the milestone through the real pipeline surface:
        the plan's pseudo-fields (``result.value``, ``result.match``,
        ``result.rule``, ``result.provenance``, ``result.output_format``)
        are expressed via the actual ``ExecutionResult``/``Candidate`` shape
        — ``canonicalized_value``, ``recognition_rule``/``validation_rule``,
        ``provenance``, and ``contract`` (same adaptation as test_rule.py).
        """
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("HTTPS://Example.COM:443/path/../other", contract)
        assert result.contract.capability_name == "url"
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "https://example.com/other"
        assert len(result.candidates) == 1
        assert result.candidates[0].recognition_rule == "absolute_uri_recognition"
        assert result.candidates[0].validation_rule == "WHATWG URL Standard"
        assert result.candidates[0].provenance[0].authority == "WHATWG"
        assert result.contract.output_format == "url"

    @pytest.mark.integration
    def test_missing(self) -> None:
        """Nothing recognized."""
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("no url here", contract)
        assert result.status == Resolution.MISSING

    @pytest.mark.integration
    def test_invalid_fatal(self) -> None:
        """Port > 65535 is a fatal WHATWG error: recognized, never INVALID.

        The grammar recognizes the span (shape-only); the rule rejects it
        (``matches()`` False), so the pipeline reports INVALID with no
        candidates.
        """
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("http://example.com:99999/", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None
        assert result.candidates == ()

    @pytest.mark.integration
    def test_invalid_unterminated_ipv6(self) -> None:
        """Unclosed IPv6 literal is fatal: INVALID."""
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("http://[::1", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None
        assert result.candidates == ()

    @pytest.mark.integration
    def test_silent_recovery_success(self) -> None:
        """D8: the recognition kept the newline span; the rule recovered.

        ``http://exa\\nmple.com/`` canonicalizes to ``http://example.com/``
        (tab/newline stripped pre-parse) — a silent recovery, never fatal.
        """
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("http://exa\nmple.com/", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "http://example.com/"

    @pytest.mark.integration
    def test_verbatim_opaque(self) -> None:
        """§4.5: opaque schemes are preserved verbatim."""
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize("mailto:user@example.com", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "mailto:user@example.com"

    @pytest.mark.integration
    def test_determinism(self) -> None:
        """Same input + same contract -> byte-identical result every call."""
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result1 = canonicalize("HTTPS://Example.COM:443/path/../other", contract)
        result2 = canonicalize("HTTPS://Example.COM:443/path/../other", contract)
        assert result1.version_stamp.replay_hash == result2.version_stamp.replay_hash
        assert len(result1.version_stamp.replay_hash) == 64  # SHA-256 hex

    @pytest.mark.integration
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # §4.3 percent-encoding preserved byte-for-byte (invalid escapes
            # and bare % kept; case kept)
            ("http://example.com/%zz", "http://example.com/%zz"),
            ("http://example.com/a%", "http://example.com/a%"),
            # §4.4 empty query / empty fragment preserved
            ("http://example.com/?", "http://example.com/?"),
            ("http://example.com/#", "http://example.com/#"),
            # §4.2 port 0 preserved (empty port dropped, 0 kept)
            ("http://example.com:0/", "http://example.com:0/"),
            # §4.6 IPv4 leading-zero octal -> decimal
            ("http://010.010.010.010/", "http://8.8.8.8/"),
            # §4.2 backslash -> "/" (silent recovery)
            ("http://example.com\\path", "http://example.com/path"),
            # §4.2 file://localhost host dropped
            ("file://localhost/etc/hosts", "file:///etc/hosts"),
            # §4.6 IDNA: münchen.de -> xn--mnchen-3ya.de
            ("http://münchen.de/", "http://xn--mnchen-3ya.de/"),
            # §4.7 no Unicode normalization — two distinct outputs
            ("http://example.com/café", "http://example.com/caf%C3%A9"),
            (
                "http://example.com/cafe\u0301",
                "http://example.com/cafe%CC%81",
            ),
        ],
    )
    def test_evidence_through_pipeline(self, raw: str, expected: str) -> None:
        """Every §4 evidence row resolves through canonicalize() to the
        WHATWG serialization (node-verified byte-for-byte)."""
        register_capability(URLCapability())
        contract = URLCapability.create_contract()
        result = canonicalize(raw, contract)
        assert result.status == Resolution.SUCCESS, raw
        assert result.canonicalized_value == expected
