"""WHATWG conformance cases for the URL parsing helper (Task 4 review).

Every row is verified against the WHATWG reference implementation
(Node's ``URL``, ``/usr/bin/node``): fatal validation errors return
``None``, non-special hosts are kept verbatim, and percent-encoding
follows the per-state WHATWG encode sets. These cases extend the frozen
Task 4 contract with boundary behavior the contract does not cover.
"""

from __future__ import annotations

import pytest

from paxman.capabilities.URL.parsing import parse_and_serialize

pytestmark = [pytest.mark.capability, pytest.mark.url]

# Host parsing, special schemes — the "ends in a number" check gates IPv4
# parsing; a failed IPv4 parse is fatal (Node's ``new URL`` throws).
_FATAL_HOST_CASES: list[tuple[str, None]] = [
    ("http://example.1/", None),  # ends in number, IPv4 parse fails
    ("http://999.1.1.1/", None),  # non-last part out of range
    ("http://09.0.0.1/", None),  # invalid octal part
    ("http://08.0.0.1/", None),  # invalid octal part
    ("http://m%C3%BCnchen.1/", None),  # non-ASCII input ending in a number
    ("http://1.2.3.4.5/", None),  # too many parts
    ("http://1.2.3.4.5", None),  # too many parts, no trailing slash
    ("http://1..2/", None),  # empty middle part
    ("http://4294967296/", None),  # >= 2**32
    ("http://1.2.3.256/", None),  # last-part bound for 4 parts
]

# IPv4 canonicalization — WHATWG integer combining, trailing dot, octal/hex.
_IPV4_CASES: list[tuple[str, str]] = [
    ("http://1.2/", "http://1.0.0.2/"),
    ("http://1/", "http://0.0.0.1/"),
    ("http://127./", "http://0.0.0.127/"),
    ("http://0x/", "http://0.0.0.0/"),
    ("http://0x.1/", "http://0.0.0.1/"),
    ("http://1.2.3.4./", "http://1.2.3.4/"),
    ("http://4294967295/", "http://255.255.255.255/"),
]

# Non-special schemes: hosts are kept verbatim (no IPv4, no IDNA).
_NON_SPECIAL_HOST_CASES: list[tuple[str, str]] = [
    ("git://127.1", "git://127.1"),
    ("git://example.1/", "git://example.1/"),
    ("git://1.2.3.4.5/", "git://1.2.3.4.5/"),
]

# Path state: query set plus "?" "^" "`" "{" "}" — applies to special and
# non-special (with authority) paths alike.
_PATH_ENCODE_CASES: list[tuple[str, str]] = [
    ('http://example.com/a"b', "http://example.com/a%22b"),
    ("http://example.com/a{b}c", "http://example.com/a%7Bb%7Dc"),
    ("http://example.com/a`b", "http://example.com/a%60b"),
    ("http://example.com/a^b", "http://example.com/a%5Eb"),
    ("http://example.com/a<b", "http://example.com/a%3Cb"),
    ("http://example.com/a>b", "http://example.com/a%3Eb"),
    ("git://example.com/a{b}", "git://example.com/a%7Bb%7D"),
]

# Query state: the backtick is NOT in the query set (stays verbatim).
_QUERY_ENCODE_CASES: list[tuple[str, str]] = [
    ("http://example.com/?a`b", "http://example.com/?a`b"),
    ('http://example.com/?a"b', "http://example.com/?a%22b"),
]

# Fragment state: the fragment set includes the backtick.
_FRAGMENT_ENCODE_CASES: list[tuple[str, str]] = [
    ("http://example.com/#a`b", "http://example.com/#a%60b"),
    ('http://example.com/#a"b', "http://example.com/#a%22b"),
]

# Opaque path state: C0 controls are encoded; space and quote are not.
_OPAQUE_ENCODE_CASES: list[tuple[str, str]] = [
    ("data:a\x01b", "data:a%01b"),
    ("data:a\x7fb", "data:a%7Fb"),
    ('data:a"b', 'data:a"b'),
]

# Userinfo state: the userinfo set includes ":" (and other delimiters).
_USERINFO_CASES: list[tuple[str, str]] = [
    ("http://a:b:c@example.com/", "http://a:b%3Ac@example.com/"),
    ("http://user:@example.com/", "http://user@example.com/"),
]

# A trailing dot on a domain is preserved; only IPv4 shapes strip it.
_DOMAIN_TRAILING_DOT_CASES: list[tuple[str, str]] = [
    ("http://example.com./", "http://example.com./"),
]


@pytest.mark.parametrize(("raw", "expected"), _FATAL_HOST_CASES)
def test_fatal_host_forms_return_none(raw: str, expected: None) -> None:
    assert parse_and_serialize(raw) is expected


@pytest.mark.parametrize(("raw", "expected"), _IPV4_CASES)
def test_ipv4_canonicalization(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _NON_SPECIAL_HOST_CASES)
def test_non_special_hosts_verbatim(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _PATH_ENCODE_CASES)
def test_path_percent_encoding(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _QUERY_ENCODE_CASES)
def test_query_percent_encoding(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _FRAGMENT_ENCODE_CASES)
def test_fragment_percent_encoding(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _OPAQUE_ENCODE_CASES)
def test_opaque_path_percent_encoding(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _USERINFO_CASES)
def test_userinfo_percent_encoding(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _DOMAIN_TRAILING_DOT_CASES)
def test_domain_trailing_dot_preserved(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected
