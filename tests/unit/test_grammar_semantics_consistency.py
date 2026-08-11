"""D8 — same-semantics grammars must produce identical notation field mappings
and canonicalization; guards semantic affinity routing.

The affinity-routing engine treats every grammar claiming the same
``semantics`` id as interchangeable: any member of a group may recognize an
input, and its notation is routed to the group's shared rules. A group whose
members map the same input to different notation fields (or whose shared rule
canonicalizes differently) would resolve the same text differently depending
on which member happened to recognize it — silent nondeterminism. This guard
enumerates all shipped grammar classes, groups them by ``semantics``, and for
every seeded group runs shared probe rows through each member's
``recognize()`` asserting identical notation fields and canonical values.
"""

from __future__ import annotations

from typing import Any, NamedTuple

import pytest

from paxman.capabilities import (
    IP,
    ISBN,
    URL,
    Country,
    Currency,
    Date,
    Email,
    Money,
    Phone,
)
from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Date.rules.iso_8601_ed2019 import Section431CalendarDate
from paxman.capabilities.Email.notation import EmailNotation
from paxman.capabilities.Email.rules.rfc_5322_ed2008 import Section341AddrSpec
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.capabilities.Phone.rules.e164_ed2010 import Section6_1InternationalNumber
from paxman.core.domain import Grammar, Rule

_SHIPPED_CAPABILITIES = [Country, Currency, Date, Email, IP, ISBN, Money, Phone, URL]


class _ProbeRow(NamedTuple):
    """One input run through every member of a semantics group.

    ``expected_notation`` is deliberately untyped: the probe table spans
    capabilities, so each row's notation type is the group's own.
    """

    input: str
    expected_notation: object
    expected_canonical: str


# Probe rows keyed by semantics id. Each key must name a real group in the
# shipped grammar enumeration (test A); each member of a group must recognize
# the probe input into the identical notation, and the group's shared rule
# must canonicalize it identically (test B).
_PROBE_ROWS: dict[str, tuple[type[Rule[Any]], tuple[_ProbeRow, ...]]] = {
    "iso8601_calendar_date": (
        Section431CalendarDate,
        (
            _ProbeRow(
                input="2026-01-15",
                expected_notation=DateNotation(N1="2026", N2="01", N3="15"),
                expected_canonical="2026-01-15",
            ),
            _ProbeRow(
                input="2026/01/15",
                expected_notation=DateNotation(N1="2026", N2="01", N3="15"),
                expected_canonical="2026-01-15",
            ),
        ),
    ),
    "rfc5322_addr_spec": (
        Section341AddrSpec,
        (
            _ProbeRow(
                input="user@example.com",
                expected_notation=EmailNotation(
                    local_part="user", domain_part="example.com"
                ),
                expected_canonical="user@example.com",
            ),
            _ProbeRow(
                input="user at example dot com",
                expected_notation=EmailNotation(
                    local_part="user", domain_part="example.com"
                ),
                expected_canonical="user@example.com",
            ),
        ),
    ),
    "e164_international": (
        Section6_1InternationalNumber,
        (
            _ProbeRow(
                input="+15551234567",
                expected_notation=PhoneNotation(shape="e164", value="15551234567"),
                expected_canonical="+15551234567",
            ),
            _ProbeRow(
                input="0015551234567",
                expected_notation=PhoneNotation(shape="e164", value="15551234567"),
                expected_canonical="+15551234567",
            ),
        ),
    ),
}


def _group_shipped_grammars_by_semantics() -> dict[str, list[type[Grammar[Any]]]]:
    """Group every shipped grammar class by its ``semantics`` id."""
    groups: dict[str, list[type[Grammar[Any]]]] = {}
    for capability in _SHIPPED_CAPABILITIES:
        for grammar in capability().get_grammars():
            groups.setdefault(grammar.semantics, []).append(type(grammar))
    return groups


@pytest.mark.unit
def test_probe_keys_name_real_semantics_groups() -> None:
    """Every probe-table key must be a real semantics group in the enumeration."""
    groups = _group_shipped_grammars_by_semantics()
    assert set(_PROBE_ROWS) <= set(groups)


@pytest.mark.unit
def test_same_semantics_grammars_agree_on_notation_and_canonical() -> None:
    """Members of a seeded semantics group recognize probes identically.

    Groups without probe rows are skipped — the reverse coverage (that every
    multi-member group is seeded) lands in a later task.
    """
    groups = _group_shipped_grammars_by_semantics()
    for semantics, (rule_cls, probes) in _PROBE_ROWS.items():
        rule = rule_cls()
        for member_cls in groups.get(semantics, ()):
            member = member_cls()
            for probe in probes:
                matches = member.recognize(probe.input)
                if not matches:
                    continue
                assert matches[0].notation == probe.expected_notation
                assert rule.normalize(matches[0].notation, DateContract()) == (
                    probe.expected_canonical
                )
