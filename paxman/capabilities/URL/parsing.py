"""WHATWG URL parser and serializer (Task 4).

``parse_and_serialize`` implements the WHATWG basic URL parser and
serializer for the URL capability. Fatal validation errors (missing
scheme, empty special-scheme host, invalid port, forbidden host code
points, unclosed IPv6 literal) return ``None`` rather than raising;
recoverable errors canonicalize.

IDNA for special-scheme hosts uses the vendored UTS #46 mapping
(``idna_uts46_mapping``) plus RFC 3492 punycode via the stdlib
``str.encode("punycode")``. Deviation code points are kept as-is
(non-transitional). This is a valid-IDN-scope implementation: the stdlib
punycode encoder may differ from WHATWG's on denormalized inputs, which
is out of scope.
"""

from __future__ import annotations

from bisect import bisect_right

from paxman.capabilities.URL.rules.data.idna_uts46_mapping import (
    IDNA_MAPPED,
    IDNA_STATUS,
)

_SPECIAL_SCHEMES: dict[str, int | None] = {
    "ftp": 21,
    "file": None,
    "http": 80,
    "https": 443,
    "ws": 80,
    "wss": 443,
}

_HEX_DIGITS: frozenset[str] = frozenset("0123456789abcdefABCDEF")

_FORBIDDEN_HOST: frozenset[str] = frozenset(
    " /?#<>@\\[]^|"
    + "".join(chr(code) for code in range(0x20))
    + "".join(chr(code) for code in range(0x7F, 0xA0))
)

# WHATWG percent-encode sets (§4.2): the ASCII members each state encodes.
_PATH_ENCODE: frozenset[str] = frozenset('"<>^`{}')
_QUERY_ENCODE: frozenset[str] = frozenset('"<>')
_FRAGMENT_ENCODE: frozenset[str] = frozenset('"<>`')
_USERINFO_ENCODE: frozenset[str] = frozenset('"#<>?^`{}/:;=@[\\]|')


def _utf8_percent_encode(char: str) -> str:
    """Percent-encode one code point's UTF-8 bytes with uppercase hex."""
    return "".join(f"%{byte:02X}" for byte in char.encode("utf-8"))


def _percent_decode(text: str) -> str:
    """Decode ``%HH`` escapes and re-interpret the bytes as UTF-8."""
    out = bytearray()
    index = 0
    length = len(text)
    while index < length:
        if (
            text[index] == "%"
            and index + 2 < length
            and text[index + 1] in _HEX_DIGITS
            and text[index + 2] in _HEX_DIGITS
        ):
            out.append(int(text[index + 1 : index + 3], 16))
            index += 3
        else:
            out.extend(text[index].encode("utf-8"))
            index += 1
    return out.decode("utf-8", "replace")


def _parse_key(key: str) -> tuple[int, int]:
    """Turn a UTS #46 key (``"00DF"`` or ``"0132..0133"``) into a range."""
    if ".." in key:
        start, end = key.split("..", 1)
        return int(start, 16), int(end, 16)
    value = int(key, 16)
    return value, value


_STATUS_ITEMS: tuple[tuple[int, int, str], ...] = tuple(
    sorted(
        (start, end, status)
        for key, status in IDNA_STATUS.items()
        for start, end in (_parse_key(key),)
    )
)
_STATUS_STARTS: tuple[int, ...] = tuple(item[0] for item in _STATUS_ITEMS)

_MAPPED_ITEMS: tuple[tuple[int, int, tuple[int, ...]], ...] = tuple(
    sorted(
        (start, end, tuple(int(hex_value, 16) for hex_value in targets.split()))
        for key, targets in IDNA_MAPPED.items()
        for start, end in (_parse_key(key),)
    )
)
_MAPPED_STARTS: tuple[int, ...] = tuple(item[0] for item in _MAPPED_ITEMS)


def _status_of(code_point: int) -> str:
    """Look up the UTS #46 status for a code point (defaults to valid)."""
    index = bisect_right(_STATUS_STARTS, code_point) - 1
    if index >= 0:
        start, end, status = _STATUS_ITEMS[index]
        if start <= code_point <= end:
            return status
    return "valid"


def _mapping_of(code_point: int) -> tuple[int, ...]:
    """Look up the UTS #46 mapping target for a code point."""
    index = bisect_right(_MAPPED_STARTS, code_point) - 1
    if index >= 0:
        start, end, targets = _MAPPED_ITEMS[index]
        if start <= code_point <= end:
            return targets
    return (code_point,)


def _idna_map(text: str) -> str | None:
    """Apply the UTS #46 mapping (non-transitional, STD3 rules off)."""
    out: list[str] = []
    for char in text:
        status = _status_of(ord(char))
        if status in ("valid", "deviation", "disallowed_STD3_valid"):
            out.append(char)
        elif status in ("mapped", "disallowed_STD3_mapped"):
            out.extend(chr(target) for target in _mapping_of(ord(char)))
        elif status == "ignored":
            continue
        else:
            return None
    return "".join(out)


def _domain_to_ascii(mapped: str) -> str | None:
    """Punycode non-ASCII labels via stdlib RFC 3492 (``xn--`` prefix)."""
    labels: list[str] = []
    for label in mapped.split("."):
        if label == "":
            labels.append("")
        elif any(ord(char) > 0x7F for char in label):
            try:
                labels.append("xn--" + label.encode("punycode").decode("ascii"))
            except UnicodeError:
                return None
        else:
            labels.append(label)
    return ".".join(labels)


def _parse_ipv6_literal(host: str) -> str | None:
    """Validate a bracketed IPv6 literal; keep the canonical form verbatim."""
    if not host.endswith("]"):
        return None
    inside = host[1:-1]
    if not inside or inside.count("::") > 1:
        return None
    if any(char not in "0123456789abcdefABCDEF:" for char in inside):
        return None
    return host


def _parse_ipv4_number(part: str) -> int | None:
    """Parse one IPv4 part in its base (hex/octal/decimal), else None."""
    if part.startswith(("0x", "0X")):
        hex_digits = part[2:]
        if hex_digits == "":
            return 0
        try:
            return int(hex_digits, 16)
        except ValueError:
            return None
    if len(part) > 1 and part.startswith("0"):
        try:
            return int(part, 8)
        except ValueError:
            return None
    if part == "" or not part.isdigit():
        return None
    return int(part, 10)


def _ends_in_number(ascii_domain: str) -> bool:
    """True when the last dot-separated label is numeric (WHATWG check).

    A trailing dot is stripped first; a label counts when it is all ASCII
    digits or ``0x``/``0X`` followed by zero or more ASCII hex digits.
    """
    parts = ascii_domain.split(".")
    if parts[-1] == "":
        parts.pop()
    if not parts:
        return False
    last = parts[-1]
    if last.isascii() and last.isdigit():
        return True
    return last.startswith(("0x", "0X")) and all(
        char in _HEX_DIGITS for char in last[2:]
    )


def _parse_ipv4(host: str) -> str | None:
    """Canonicalize a dotted IPv4 host per WHATWG, or None if invalid.

    Parts parse in their base (hex/octal/decimal), a trailing dot is
    stripped, and the parts combine into one 32-bit value serialized as
    a dotted quad.
    """
    parts = host.split(".")
    if parts[-1] == "":
        if len(parts) > 1:
            parts.pop()
        else:
            return None
    if len(parts) > 4:
        return None
    numbers: list[int] = []
    for part in parts:
        value = _parse_ipv4_number(part)
        if value is None:
            return None
        numbers.append(value)
    if any(number > 255 for number in numbers[:-1]):
        return None
    if numbers[-1] >= 256 ** (5 - len(numbers)):
        return None
    combined = numbers[-1]
    for index, number in enumerate(numbers[:-1]):
        combined += number * 256 ** (3 - index)
    octets = [(combined >> shift) & 0xFF for shift in (24, 16, 8, 0)]
    return ".".join(str(octet) for octet in octets)


def _parse_host(host: str, special: bool) -> str | None:
    """Parse a host: IPv6 literal, IPv4, or (special) IDNA domain."""
    if host.startswith("["):
        return _parse_ipv6_literal(host)
    if any(char in _FORBIDDEN_HOST for char in host):
        return None
    if not special:
        return host
    decoded = _percent_decode(host)
    if any(char in _FORBIDDEN_HOST for char in decoded):
        return None
    mapped = _idna_map(decoded)
    if mapped is None:
        return None
    ascii_domain = _domain_to_ascii(mapped)
    if ascii_domain is None:
        return None
    if _ends_in_number(ascii_domain):
        ipv4 = _parse_ipv4(ascii_domain)
        if ipv4 is None:
            return None
        return ipv4
    return ascii_domain


class _Parsed:
    """Mutable accumulator mirroring the WHATWG URL record."""

    __slots__ = (
        "scheme",
        "username",
        "password",
        "host",
        "port",
        "path",
        "query",
        "fragment",
    )

    def __init__(self, scheme: str) -> None:
        self.scheme = scheme
        self.username = ""
        self.password = ""
        self.host: str | None = None
        self.port: int | None = None
        self.path: list[str] = []
        self.query: str | None = None
        self.fragment: str | None = None


def _split_port(text: str) -> tuple[str, str | None]:
    """Split ``host[:port]`` at the first ``:`` outside ``[...]`` brackets."""
    depth = 0
    for index, char in enumerate(text):
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
        elif char == ":" and depth == 0:
            return text[:index], text[index + 1 :]
    return text, None


def _encode_userinfo(text: str) -> str:
    """Percent-encode a username or password with the userinfo set."""
    out: list[str] = []
    for char in text:
        code = ord(char)
        if (
            code == 0x20
            or code < 0x20
            or 0x7F <= code <= 0x9F
            or char in _USERINFO_ENCODE
        ):
            out.append(f"%{code:02X}")
        elif code > 0x7F:
            out.append(_utf8_percent_encode(char))
        else:
            out.append(char)
    return "".join(out)


def _build_authority(scheme: str, authority: str) -> _Parsed | None:
    """Parse credentials and host:port out of authority content."""
    parsed = _Parsed(scheme)
    at = authority.rfind("@")
    if at >= 0:
        credentials = authority[:at].replace("@", "%40")
        username, _, password = credentials.partition(":")
        parsed.username = _encode_userinfo(username)
        parsed.password = _encode_userinfo(password)
        rest = authority[at + 1 :]
    else:
        rest = authority
    host_part, port_string = _split_port(rest)
    host = _parse_host(host_part, scheme in _SPECIAL_SCHEMES)
    if host is None:
        return None
    parsed.host = host
    if port_string is not None and port_string != "":
        if not port_string.isdigit():
            return None
        port = int(port_string)
        if port > 65535:
            return None
        default = _SPECIAL_SCHEMES.get(scheme)
        if default is None or port != default:
            parsed.port = port
    return parsed


def _parse_query_fragment(
    source: str, start: int, stop_char: str | None, encode_set: frozenset[str]
) -> str:
    """Collect query/fragment text until ``stop_char`` or EOF, encoding chars."""
    out: list[str] = []
    length = len(source)
    index = start
    while index < length:
        char = source[index]
        if stop_char is not None and char == stop_char:
            break
        code = ord(char)
        if code == 0x20 or code < 0x20 or 0x7F <= code <= 0x9F or char in encode_set:
            out.append(f"%{code:02X}")
        elif code > 0x7F:
            out.append(_utf8_percent_encode(char))
        else:
            out.append(char)
        index += 1
    return "".join(out)


def _parse_path_and_rest(parsed: _Parsed, source: str, pos: int, special: bool) -> None:
    """Parse path segments (dot-segment removal) plus query and fragment."""
    length = len(source)
    segments: list[str] = []
    buffer: list[str] = []
    pending_separator = False

    def append_segment(segment: str) -> None:
        if segment == ".":
            return
        if segment == "..":
            if segments:
                segments.pop()
            return
        segments.append(segment)

    if pos < length and (source[pos] == "/" or (special and source[pos] == "\\")):
        pos += 1
        pending_separator = True
    while True:
        if pos >= length:
            if buffer:
                append_segment("".join(buffer))
            elif pending_separator:
                append_segment("")
            break
        char = source[pos]
        if char == "/" or (special and char == "\\"):
            append_segment("".join(buffer))
            buffer.clear()
            pending_separator = True
            pos += 1
            continue
        if char == "?":
            if buffer:
                append_segment("".join(buffer))
            elif pending_separator:
                append_segment("")
            parsed.query = _parse_query_fragment(source, pos + 1, "#", _QUERY_ENCODE)
            hash_pos = source.find("#", pos + 1)
            if hash_pos >= 0:
                parsed.fragment = _parse_query_fragment(
                    source, hash_pos + 1, None, _FRAGMENT_ENCODE
                )
            break
        if char == "#":
            if buffer:
                append_segment("".join(buffer))
            elif pending_separator:
                append_segment("")
            parsed.fragment = _parse_query_fragment(
                source, pos + 1, None, _FRAGMENT_ENCODE
            )
            break
        code = ord(char)
        if code == 0x20 or code < 0x20 or 0x7F <= code <= 0x9F or char in _PATH_ENCODE:
            buffer.append(f"%{code:02X}")
        elif code > 0x7F:
            buffer.append(_utf8_percent_encode(char))
        else:
            buffer.append(char)
        pending_separator = False
        pos += 1
    parsed.path = segments


def _parse_opaque(parsed: _Parsed, source: str, start: int) -> None:
    """Parse an opaque path: one verbatim segment, non-ASCII UTF-8 encoded."""
    out: list[str] = []
    length = len(source)
    index = start
    while index < length:
        char = source[index]
        if char == "?":
            parsed.path = ["".join(out)]
            parsed.query = _parse_query_fragment(source, index + 1, "#", _QUERY_ENCODE)
            hash_pos = source.find("#", index + 1)
            if hash_pos >= 0:
                parsed.fragment = _parse_query_fragment(
                    source, hash_pos + 1, None, _FRAGMENT_ENCODE
                )
            return
        if char == "#":
            parsed.path = ["".join(out)]
            parsed.fragment = _parse_query_fragment(
                source, index + 1, None, _FRAGMENT_ENCODE
            )
            return
        code = ord(char)
        if code < 0x20 or 0x7F <= code <= 0x9F:
            out.append(f"%{code:02X}")
        elif code > 0x7F:
            out.append(_utf8_percent_encode(char))
        else:
            out.append(char)
        index += 1
    parsed.path = ["".join(out)]


def _is_valid_scheme(scheme: str) -> bool:
    """Check ``[A-Za-z][A-Za-z0-9+.-]*`` (ASCII only)."""
    first = scheme[0]
    if not first.isascii() or not first.isalpha():
        return False
    return all(c.isascii() and (c.isalnum() or c in "+.-") for c in scheme)


def _parse_file(source: str, length: int, colon: int) -> _Parsed | None:
    """File scheme: host defaults to empty; ``//`` enables host parsing."""
    parsed = _Parsed("file")
    parsed.host = ""
    pos = colon + 1
    if pos < length and source[pos] in "/\\":
        pos += 1
        if pos < length and source[pos] in "/\\":
            host_start = pos + 1
            end = host_start
            while end < length and source[end] not in "/\\?#":
                end += 1
            host = source[host_start:end]
            if host == "localhost":
                host = ""
            parsed_host = _parse_host(host, True)
            if parsed_host is None:
                return None
            parsed.host = parsed_host
            pos = end
    _parse_path_and_rest(parsed, source, pos, special=True)
    return parsed


def _parse_special(source: str, length: int, colon: int, scheme: str) -> _Parsed | None:
    """Special (non-file) scheme: skip leading slashes, host is required."""
    pos = colon + 1
    while pos < length and source[pos] in "/\\":
        pos += 1
    end = pos
    while end < length and source[end] not in "/?#\\":
        end += 1
    parsed = _build_authority(scheme, source[pos:end])
    if parsed is None:
        return None
    if parsed.host == "":
        return None
    _parse_path_and_rest(parsed, source, end, special=True)
    return parsed


def _parse_non_special(
    source: str, length: int, colon: int, scheme: str
) -> _Parsed | None:
    """Non-special scheme: ``//`` authority or opaque path."""
    if source.startswith("//", colon + 1):
        pos = colon + 3
        end = pos
        while end < length and source[end] not in "/?#":
            end += 1
        parsed = _build_authority(scheme, source[pos:end])
        if parsed is None:
            return None
        _parse_path_and_rest(parsed, source, end, special=False)
        return parsed
    parsed = _Parsed(scheme)
    _parse_opaque(parsed, source, colon + 1)
    return parsed


def _parse(source: str) -> _Parsed | None:
    """Run the WHATWG state machine over ``source``."""
    length = len(source)
    colon = source.find(":")
    if colon <= 0:
        return None
    raw_scheme = source[:colon]
    if not _is_valid_scheme(raw_scheme):
        return None
    scheme = raw_scheme.lower()
    if scheme == "file":
        return _parse_file(source, length, colon)
    if scheme in _SPECIAL_SCHEMES:
        return _parse_special(source, length, colon, scheme)
    return _parse_non_special(source, length, colon, scheme)


def _serialize(parsed: _Parsed) -> str:
    """Serialize a parsed URL record per the WHATWG serializer."""
    out = parsed.scheme + ":"
    if parsed.host is not None:
        out += "//"
        if parsed.username or parsed.password:
            out += parsed.username
            if parsed.password:
                out += ":" + parsed.password
            out += "@"
        out += parsed.host
        if parsed.port is not None:
            out += ":" + str(parsed.port)
        if parsed.scheme in _SPECIAL_SCHEMES or parsed.path:
            out += "/" + "/".join(parsed.path)
    else:
        out += "/".join(parsed.path)
    if parsed.query is not None:
        out += "?" + parsed.query
    if parsed.fragment is not None:
        out += "#" + parsed.fragment
    return out


def parse_and_serialize(raw: str) -> str | None:
    """Parse ``raw`` per the WHATWG URL standard and serialize the result.

    Fatal validation errors return ``None``; recoverable errors
    canonicalize. Tab/newline/carriage-return code points are stripped
    before parsing. IDNA and punycode handling are described in the
    module docstring.
    """
    source = raw.replace("\t", "").replace("\n", "").replace("\r", "")
    parsed = _parse(source)
    if parsed is None:
        return None
    return _serialize(parsed)
