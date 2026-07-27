"""Tests for IP recognition grammars."""

from __future__ import annotations

import pytest

from paxman.capabilities.IP.grammar.ipv4_recognition import IPv4Grammar
from paxman.capabilities.IP.grammar.ipv6_recognition import IPv6Grammar
from paxman.capabilities.IP.notation import IPNotation


class TestIPv4Grammar:
    """Tests for IPv4Grammar."""

    @pytest.mark.capability
    def test_recognizes_standard_ipv4(self) -> None:
        grammar = IPv4Grammar()
        results = grammar.recognize("Server at 192.168.1.1")
        assert len(results) == 1
        assert results[0] == IPNotation(address="192.168.1.1")

    @pytest.mark.capability
    def test_recognizes_ipv4_with_leading_zeros(self) -> None:
        grammar = IPv4Grammar()
        results = grammar.recognize("Address: 010.020.030.040")
        assert len(results) == 1
        assert results[0] == IPNotation(address="010.020.030.040")

    @pytest.mark.capability
    def test_recognizes_loopback(self) -> None:
        grammar = IPv4Grammar()
        results = grammar.recognize("Connect to 127.0.0.1")
        assert len(results) == 1
        assert results[0] == IPNotation(address="127.0.0.1")

    @pytest.mark.capability
    def test_recognizes_multiple_ipv4(self) -> None:
        grammar = IPv4Grammar()
        results = grammar.recognize("From 10.0.0.1 to 10.0.0.2")
        assert len(results) == 2
        assert results[0] == IPNotation(address="10.0.0.1")
        assert results[1] == IPNotation(address="10.0.0.2")

    @pytest.mark.capability
    def test_ignores_non_ip_text(self) -> None:
        grammar = IPv4Grammar()
        results = grammar.recognize("no ip here")
        assert len(results) == 0

    @pytest.mark.capability
    def test_returns_empty_for_empty_input(self) -> None:
        grammar = IPv4Grammar()
        results = grammar.recognize("")
        assert len(results) == 0

    @pytest.mark.capability
    def test_recognizes_ipv4_in_sentence(self) -> None:
        grammar = IPv4Grammar()
        results = grammar.recognize(
            "The default gateway is 192.168.1.1 and DNS is 8.8.8.8"
        )
        assert len(results) == 2


class TestIPv6Grammar:
    """Tests for IPv6Grammar."""

    @pytest.mark.capability
    def test_recognizes_full_ipv6(self) -> None:
        grammar = IPv6Grammar()
        results = grammar.recognize("Address: 2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        assert len(results) >= 1
        addresses = [r.address for r in results]
        assert "2001:0db8:85a3:0000:0000:8a2e:0370:7334" in addresses

    @pytest.mark.capability
    def test_recognizes_compressed_ipv6(self) -> None:
        grammar = IPv6Grammar()
        results = grammar.recognize("Address: 2001:db8:85a3::8a2e:370:7334")
        assert len(results) >= 1

    @pytest.mark.capability
    def test_recognizes_loopback(self) -> None:
        grammar = IPv6Grammar()
        results = grammar.recognize("Connect to ::1")
        assert len(results) >= 1
        addresses = [r.address for r in results]
        assert "::1" in addresses

    @pytest.mark.capability
    def test_recognizes_link_local(self) -> None:
        grammar = IPv6Grammar()
        results = grammar.recognize("fe80::1 is the gateway")
        assert len(results) >= 1

    @pytest.mark.capability
    def test_ignores_non_ip_text(self) -> None:
        grammar = IPv6Grammar()
        results = grammar.recognize("no ip here")
        assert len(results) == 0

    @pytest.mark.capability
    def test_returns_empty_for_empty_input(self) -> None:
        grammar = IPv6Grammar()
        results = grammar.recognize("")
        assert len(results) == 0

    @pytest.mark.capability
    def test_no_duplicates(self) -> None:
        grammar = IPv6Grammar()
        results = grammar.recognize("::1 and ::1")
        addresses = [r.address for r in results]
        assert addresses.count("::1") == 1
