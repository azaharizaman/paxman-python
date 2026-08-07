"""Tests for the WHATWG URL parsing helper (Task 4).

Every row of research doc §4 is a parametrized case: fatal errors return
``None``, recoverable errors canonicalize, existing percent-escapes pass
through byte-for-byte, and serialization is a fixed point (idempotent).
"""

from __future__ import annotations

import pytest

from paxman.capabilities.URL.parsing import parse_and_serialize

pytestmark = [pytest.mark.capability, pytest.mark.url]

# §4.1 — fatal validation errors → None
_FATAL_CASES: list[tuple[str, None]] = [
    ("http://example.com:99999/", None),  # port > 65535
    ("http://example.com:80x/", None),  # non-digit port
    ("http://example.com:80:90/", None),  # two port components
    ("http://exa mple.com/", None),  # space in host
    ("http://[::1", None),  # unclosed IPv6
]

# §4.2 — recoverable validation errors → canonicalized
_RECOVERY_CASES: list[tuple[str, str]] = [
    ("http://exa\nmple.com/", "http://example.com/"),
    ("http://example.com:", "http://example.com/"),
    ("http://example.com:0/", "http://example.com:0/"),  # port 0 preserved
    ("http://example.com\\path", "http://example.com/path"),
    ("http://%65xample.com/", "http://example.com/"),  # host percent-decoding
    ("http://example.com/a b", "http://example.com/a%20b"),
    ("http://user name@example.com/", "http://user%20name@example.com/"),
    ("http://[2001:db8::1]/", "http://[2001:db8::1]/"),
    ("file://localhost/etc/hosts", "file:///etc/hosts"),
]

# §4.3 — existing percent-escapes preserved byte-for-byte
_PERCENT_CASES: list[tuple[str, str]] = [
    ("http://example.com/a%2fb", "http://example.com/a%2fb"),  # case kept
    ("http://example.com/%41", "http://example.com/%41"),  # not decoded
    ("http://example.com/~x", "http://example.com/~x"),
    ("http://example.com/%zz", "http://example.com/%zz"),  # invalid escape
    ("http://example.com/a%", "http://example.com/a%"),  # bare %
]

# §4.4 — query and fragment handling
_QUERY_FRAGMENT_CASES: list[tuple[str, str]] = [
    ("http://example.com/?a=b c", "http://example.com/?a=b%20c"),
    ("http://example.com/?x=%7e", "http://example.com/?x=%7e"),
    ("http://example.com/?a+b", "http://example.com/?a+b"),  # + literal
    ("http://example.com/?", "http://example.com/?"),  # empty query
    ("http://example.com/#", "http://example.com/#"),  # empty fragment
    ("http://example.com/#a b", "http://example.com/#a%20b"),
]

# §4.5 — special schemes drop their default port; non-special pass through
_SPECIAL_SCHEME_CASES: list[tuple[str, str]] = [
    ("ftp://example.com:21/a", "ftp://example.com/a"),  # default port dropped
    ("ws://example.com:80/a", "ws://example.com/a"),
]

_NON_SPECIAL_CASES: list[tuple[str, str]] = [
    ("mailto:user@example.com", "mailto:user@example.com"),
    ("GIT://github.com/user/repo", "git://github.com/user/repo"),
    ("ssh://user@host:22/path", "ssh://user@host:22/path"),  # port kept
    ("mailto:user@münchen.de", "mailto:user@m%C3%BCnchen.de"),
    ("data:text/plain,hello world", "data:text/plain,hello world"),  # opaque
    ("git://github.com/user/my repo", "git://github.com/user/my%20repo"),
    ("custom:scheme with space", "custom:scheme with space"),  # opaque
]

# §4.6 — host forms: IPv4, IDNA, authority quirks
_HOST_CASES: list[tuple[str, str]] = [
    ("HTTPS://Example.COM:443/path/../other", "https://example.com/other"),
    ("http://010.010.010.010/", "http://8.8.8.8/"),  # octal
    ("http://192.168.001.001/", "http://192.168.1.1/"),
    ("http:///path", "http://path/"),
    ("http://münchen.de/", "http://xn--mnchen-3ya.de/"),
    ("http://caf%C3%A9.de/", "http://xn--caf-dma.de/"),
    ("http://café.example/", "http://xn--caf-dma.example/"),
]

# §4.7 — no Unicode normalization in paths (D9): NFC input stays NFC-encoded,
# decomposed input stays decomposed — never collapsed.
_NFC_CASES: list[tuple[str, str]] = [
    ("http://example.com/café", "http://example.com/caf%C3%A9"),
    ("http://example.com/cafe\u0301", "http://example.com/cafe%CC%81"),
]

_ALL_CASE_INPUTS: list[str] = [
    raw
    for table in (
        _FATAL_CASES,
        _RECOVERY_CASES,
        _PERCENT_CASES,
        _QUERY_FRAGMENT_CASES,
        _SPECIAL_SCHEME_CASES,
        _NON_SPECIAL_CASES,
        _HOST_CASES,
        _NFC_CASES,
    )
    for raw, _ in table
]

_IDEMPOTENT_OUTPUTS: list[str] = [
    expected
    for table in (
        _RECOVERY_CASES,
        _PERCENT_CASES,
        _QUERY_FRAGMENT_CASES,
        _SPECIAL_SCHEME_CASES,
        _NON_SPECIAL_CASES,
        _HOST_CASES,
        _NFC_CASES,
    )
    for _, expected in table
]


@pytest.mark.parametrize(("raw", "expected"), _FATAL_CASES)
def test_fatal_cases_return_none(raw: str, expected: None) -> None:
    assert parse_and_serialize(raw) is expected


@pytest.mark.parametrize(("raw", "expected"), _RECOVERY_CASES)
def test_recovery_cases_canonicalize(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _PERCENT_CASES)
def test_percent_encoding_preserved(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _QUERY_FRAGMENT_CASES)
def test_query_fragment_verbatim(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _SPECIAL_SCHEME_CASES)
def test_special_scheme_default_port_dropped(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _NON_SPECIAL_CASES)
def test_non_special_schemes_pass_through(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _HOST_CASES)
def test_hosts_and_ipv4(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _NFC_CASES)
def test_no_unicode_normalization(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


def test_milestone() -> None:
    """The §4.6 milestone: case, default port, and dot segments at once."""
    assert (
        parse_and_serialize("HTTPS://Example.COM:443/path/../other")
        == "https://example.com/other"
    )


def test_idempotent() -> None:
    """WHATWG serialization is a fixed point: parsing a serialized URL is a no-op."""
    for output in _IDEMPOTENT_OUTPUTS:
        assert parse_and_serialize(output) == output


def test_never_raises() -> None:
    """parse_and_serialize returns None on fatal errors instead of raising."""
    for raw in _ALL_CASE_INPUTS:
        parse_and_serialize(raw)
