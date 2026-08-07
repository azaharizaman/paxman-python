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

# C1 controls (U+0080-U+009F) are UTF-8 percent-encoded like any other
# non-ASCII code point — never single-byte %80-%9F. The C0 set covers
# only 0x00-0x1F plus U+007F; everything above U+007E is UTF-8 encoded.
# Verified against Node's URL.
_C1_ENCODE_CASES: list[tuple[str, str]] = [
    ("http://example.com/\u0080", "http://example.com/%C2%80"),
    ("http://example.com/?a=\u009f", "http://example.com/?a=%C2%9F"),
    ("http://user\u0081name@example.com/", "http://user%C2%81name@example.com/"),
    ("data:text/plain,\u0090", "data:text/plain,%C2%90"),
    ("http://example.com/\u007f/", "http://example.com/%7F/"),  # DEL: single byte
]

# Only ASCII digits are numeric in the WHATWG host/port states: Node throws
# on Unicode digits (e.g. Arabic-Indic) in ports and IPv4 parts.
_FATAL_UNICODE_DIGIT_CASES: list[tuple[str, None]] = [
    ("http://example.com:\u0669\u0669/", None),  # Arabic-Indic digits in port
    ("http://[::ffff:1.\u0662.\u0663.\u0664]/", None),  # embedded IPv4
    ("http://[::ffff:\u0661.2.3.4]/", None),  # embedded IPv4, leading digit
]

# A trailing dot on a domain is preserved; only IPv4 shapes strip it.
_DOMAIN_TRAILING_DOT_CASES: list[tuple[str, str]] = [
    ("http://example.com./", "http://example.com./"),
]

# IPv6 literals: bracketed canonical serialization per WHATWG host parser
# (lowercase hex, longest-zero-run compression, embedded IPv4 combined into
# the final two pieces). All expected values verified against Node's URL.
_IPV6_CASES: list[tuple[str, str]] = [
    ("http://[2001:db8::1]/", "http://[2001:db8::1]/"),
    ("http://[::]/", "http://[::]/"),
    ("http://[0:0:0:0:0:0:0:1]/", "http://[::1]/"),
    ("http://[0:0:0:0:0:0:0:0]/", "http://[::]/"),
    ("http://[2001:db8:0:0:0:0:0:1]/", "http://[2001:db8::1]/"),
    ("http://[1:2:3:4:5:6:7:8]/", "http://[1:2:3:4:5:6:7:8]/"),
    ("http://[1:2:3:4:5:6::7]/", "http://[1:2:3:4:5:6:0:7]/"),
    ("http://[1:2:3:4:5:6:7::]/", "http://[1:2:3:4:5:6:7:0]/"),
    ("http://[1::]/", "http://[1::]/"),
    ("http://[1::1]/", "http://[1::1]/"),
    ("http://[1:2::3:4]/", "http://[1:2::3:4]/"),
    (
        "http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]/",
        "http://[2001:db8:85a3::8a2e:370:7334]/",
    ),
    ("http://[::ffff:192.168.1.1]/", "http://[::ffff:c0a8:101]/"),
    ("http://[::ffff:0a00:1]/", "http://[::ffff:a00:1]/"),
    ("http://[::ffff:1.2.3.4]/", "http://[::ffff:102:304]/"),
    ("http://[::ffff:0.0.0.0]/", "http://[::ffff:0:0]/"),
    ("http://[::ffff:255.255.255.255]/", "http://[::ffff:ffff:ffff]/"),
    ("http://[::192.168.1.1]/", "http://[::c0a8:101]/"),
    ("http://[1:2:3:4:5:6:192.168.1.1]/", "http://[1:2:3:4:5:6:c0a8:101]/"),
    ("http://[2001:db8::192.168.1.1]/", "http://[2001:db8::c0a8:101]/"),
]

# IPv6 literals that hit a fatal host-parse error (Node's URL throws).
_FATAL_IPV6_CASES: list[tuple[str, None]] = [
    ("http://[1:2:3:4:5:6:7:8:]/", None),  # trailing colon
    ("http://[1:2:3:4:5:6:7:8:9]/", None),  # nine pieces
    ("http://[1:2:3:4:5:6:7:8:9:10]/", None),  # ten pieces
    ("http://[0:0:0:0:0:0:0:1:0]/", None),  # nine pieces
    ("http://[1:2:3:4::5:6:7:8]/", None),  # :: plus nine piece slots
    ("http://[1:2:3:4:5::6:7:8]/", None),  # :: plus nine piece slots
    ("http://[1:2:3:4:5:6:7::8]/", None),  # :: plus nine piece slots
    ("http://[::1::2]/", None),  # two compressors
    ("http://[::1::]/", None),  # trailing compressor
    ("http://[::1:]/", None),  # trailing colon after ::1
    ("http://[g::1]/", None),  # non-hex piece
    ("http://[1234]/", None),  # too few pieces, no compressor
    ("http://[1:2:3]/", None),  # too few pieces, no compressor
    ("http://[1:2:3!:4]/", None),  # invalid character
    ("http://[fe80::1%25eth0]/", None),  # zone identifier rejected
    ("http://[fe80::1%eth0]/", None),  # zone identifier rejected
    ("http://[::ffff:127.00.0.1]/", None),  # leading zero in IPv4 piece
    ("http://[::ffff:127.0.0.4000]/", None),  # IPv4 piece out of range
    ("http://[::ffff:1.2.3.256]/", None),  # last IPv4 piece out of range
    ("http://[::ffff:127.0.0]/", None),  # three IPv4 pieces
    ("http://[::ffff:127.0.0.1.2]/", None),  # five IPv4 pieces
    ("http://[1:2:3:4:5:192.168.1.1]/", None),  # IPv4 too early
]

# IDNA / punycode hosts that hit a fatal UTS #46 validation error.
_FATAL_IDNA_CASES: list[tuple[str, None]] = [
    ("http://xn--abc-def/", None),  # decoded label mixes RTL (U+069F) + LTR
    ("http://ڟabc.com/", None),  # raw RTL input round-trips to xn--abc-def
    ("http://exa%C2%A0mple.com/", None),  # U+00A0 maps to space -> forbidden
    ("https://exa%C2%A0mple.com/", None),  # same on https
    ("http://exa mple.com/", None),  # raw space in host
]

# Valid IDN hosts: UTS #46 acceptance with canonical punycode output.
_IDNA_ACCEPT_CASES: list[tuple[str, str]] = [
    ("http://עברית.com/", "http://xn--5dbqzzl.com/"),  # Hebrew RTL
    ("http://münchen.de/", "http://xn--mnchen-3ya.de/"),  # Latin with umlaut
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


@pytest.mark.parametrize(("raw", "expected"), _IPV6_CASES)
def test_ipv6_canonicalization(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _FATAL_IPV6_CASES)
def test_fatal_ipv6_forms_return_none(raw: str, expected: None) -> None:
    assert parse_and_serialize(raw) is expected


@pytest.mark.parametrize(("raw", "expected"), _FATAL_IDNA_CASES)
def test_fatal_idna_forms_return_none(raw: str, expected: None) -> None:
    assert parse_and_serialize(raw) is expected


@pytest.mark.parametrize(("raw", "expected"), _IDNA_ACCEPT_CASES)
def test_idna_host_canonicalization(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _C1_ENCODE_CASES)
def test_c1_controls_utf8_percent_encoded(raw: str, expected: str) -> None:
    assert parse_and_serialize(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), _FATAL_UNICODE_DIGIT_CASES)
def test_unicode_digits_not_numeric(raw: str, expected: None) -> None:
    assert parse_and_serialize(raw) is expected
