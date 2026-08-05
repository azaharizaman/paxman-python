"""Guard tests for the unanimous capability contract & rule surface.

These tests lock the homogeneity mandate so it cannot regress: every one of
the six built-in capabilities (Email, Date, Country, IP, Money, Phone) must

- inherit :class:`CapabilityContract` (item 1),
- satisfy the :class:`ContractFactory` protocol (item 2),
- expose a keyword-only ``create_contract`` whose parameters begin with the
  unanimous common block ``excluded_rules, pinned_rules, year, output_format``
  (item 3 — guards the signature itself, which the runtime_checkable
  protocol cannot),
- keep ``output_format`` optional and resolving to the concrete default
  (item 4),
- emit a replay-deterministic ``as_dict()`` key set (item 5), and
- never return keys from ``_extra_dict_fields()`` that collide with the
  standard base keys (item 6).
"""

from __future__ import annotations

import inspect
from inspect import Parameter

import pytest

from paxman.capabilities.Country.capability import CountryCapability
from paxman.capabilities.Country.contract import CountryContract
from paxman.capabilities.Country.notation import CountryNotation
from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Date.notation import DateNotation
from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.Email.contract import EmailContract
from paxman.capabilities.Email.notation import EmailNotation
from paxman.capabilities.IP.capability import IPCapability
from paxman.capabilities.IP.contract import IPContract
from paxman.capabilities.IP.notation import IPNotation
from paxman.capabilities.Money.capability import MoneyCapability
from paxman.capabilities.Money.contract import MoneyContract
from paxman.capabilities.Money.notation import MoneyNotation
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.capabilities.Phone.contract import PhoneContract
from paxman.capabilities.Phone.notation import PhoneNotation
from paxman.core.capability import ContractFactory
from paxman.core.capability_contract import CapabilityContract

_COMMON_BLOCK = ("excluded_rules", "pinned_rules", "year", "output_format")

_STANDARD_KEYS = frozenset(
    {"capability_name", "excluded_rules", "pinned_rules", "year", "output_format"}
)

_EMAIL_KEYS = _STANDARD_KEYS | {"include_obfuscated", "include_localhost"}
_DATE_KEYS = _STANDARD_KEYS | {"two_digit_base_year"}
_COUNTRY_KEYS = _STANDARD_KEYS | {"include_localized", "include_historical"}
_IP_KEYS = _STANDARD_KEYS | {"include_ipv6"}
_MONEY_KEYS = _STANDARD_KEYS | {"precision", "dollar_sign_currency"}
_PHONE_KEYS = _STANDARD_KEYS | {"default_country"}

_CAPABILITY_SURFACES = [
    pytest.param(
        EmailCapability,
        EmailContract,
        "email",
        _EMAIL_KEYS,
        id="email",
    ),
    pytest.param(
        DateCapability,
        DateContract,
        "ISO",
        _DATE_KEYS,
        id="date",
    ),
    pytest.param(
        CountryCapability,
        CountryContract,
        "alpha2",
        _COUNTRY_KEYS,
        id="country",
    ),
    pytest.param(
        IPCapability,
        IPContract,
        "ip",
        _IP_KEYS,
        id="ip",
    ),
    pytest.param(
        MoneyCapability,
        MoneyContract,
        "code_amount",
        _MONEY_KEYS,
        id="money",
    ),
    pytest.param(
        PhoneCapability,
        PhoneContract,
        "e164",
        _PHONE_KEYS,
        id="phone",
    ),
]


class TestContractHomogeneity:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_default_format,_expected_keys",
        _CAPABILITY_SURFACES,
    )
    def test_contracts_inherit_capability_contract(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _default_format: str,
        _expected_keys: frozenset[str],
    ) -> None:
        """Every contract class inherits CapabilityContract."""
        assert issubclass(_contract_class, CapabilityContract)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_default_format,_expected_keys",
        _CAPABILITY_SURFACES,
    )
    def test_capabilities_satisfy_contract_factory(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _default_format: str,
        _expected_keys: frozenset[str],
    ) -> None:
        """Every capability class satisfies the ContractFactory protocol."""
        assert isinstance(_capability, ContractFactory)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_default_format,_expected_keys",
        _CAPABILITY_SURFACES,
    )
    def test_create_contract_signature_has_unanimous_common_block(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _default_format: str,
        _expected_keys: frozenset[str],
    ) -> None:
        """create_contract parameters begin with the unanimous common block.

        The runtime_checkable ``ContractFactory`` protocol only checks
        attribute presence, not the signature — so this test pins the actual
        parameter shape: the first four parameters, in order, are
        ``excluded_rules, pinned_rules, year, output_format`` and every
        parameter is keyword-only.
        """
        parameters = list(
            inspect.signature(_capability.create_contract).parameters.values()
        )
        assert [parameter.name for parameter in parameters[:4]] == list(_COMMON_BLOCK)
        assert len(parameters) >= 4
        assert all(parameter.kind == Parameter.KEYWORD_ONLY for parameter in parameters)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_default_format,_expected_keys",
        _CAPABILITY_SURFACES,
    )
    def test_output_format_optional_in_contract_signature(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _default_format: str,
        _expected_keys: frozenset[str],
    ) -> None:
        """output_format defaults to None on every contract __init__."""
        parameters = inspect.signature(_contract_class).parameters
        assert parameters["output_format"].default is None

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_default_format,_expected_keys",
        _CAPABILITY_SURFACES,
    )
    def test_output_format_none_resolves_to_concrete_default(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _default_format: str,
        _expected_keys: frozenset[str],
    ) -> None:
        """A no-arg contract resolves output_format to the concrete default."""
        assert _contract_class().output_format == _default_format

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_default_format,_expected_keys",
        _CAPABILITY_SURFACES,
    )
    def test_as_dict_replay_shape(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _default_format: str,
        _expected_keys: frozenset[str],
    ) -> None:
        """as_dict() emits exactly the expected replay-deterministic key set."""
        assert set(_contract_class().as_dict().keys()) == _expected_keys

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_default_format,_expected_keys",
        _CAPABILITY_SURFACES,
    )
    def test_extra_dict_fields_do_not_collide_with_standard_keys(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _default_format: str,
        _expected_keys: frozenset[str],
    ) -> None:
        """Capability-specific as_dict() keys never shadow the standard keys."""
        assert not (set(_contract_class()._extra_dict_fields()) & _STANDARD_KEYS)


# ---------------------------------------------------------------------------
# format_value surface: one formatter per capability, offered formats handled
# ---------------------------------------------------------------------------

# Real instances + concrete notations per capability. The canonical value is
# the rule-produced default representation; expectations are independent
# literals (not derived from the formatter under test).
_FORMAT_SURFACES = [
    pytest.param(
        EmailCapability,
        EmailContract,
        "user@example.com",
        EmailNotation(local_part="user", domain_part="example.com"),
        id="email",
    ),
    pytest.param(
        DateCapability,
        DateContract,
        "2026-01-15",
        DateNotation(N1="2026", N2="01", N3="15"),
        id="date",
    ),
    pytest.param(
        CountryCapability,
        CountryContract,
        "DE",
        CountryNotation(shape="alpha2", value="DE"),
        id="country",
    ),
    pytest.param(
        IPCapability,
        IPContract,
        "192.0.2.1",
        IPNotation(address="192.0.2.1"),
        id="ip",
    ),
    pytest.param(
        MoneyCapability,
        MoneyContract,
        "USD 500.00",
        MoneyNotation(
            currency_part="USD",
            amount_part="500",
            currency_shape="code",
            amount_shape="integer",
        ),
        id="money",
    ),
    pytest.param(
        PhoneCapability,
        PhoneContract,
        "+15551234567",
        PhoneNotation(shape="e164", value="15551234567"),
        id="phone",
    ),
]

# Capabilities with non-empty OFFERED_OUTPUT_FORMATS, and the independent
# literal each offered format must render for the sample canonical value.
_FORMATTED_EXPECTATIONS = [
    pytest.param(
        DateCapability,
        DateContract,
        "2026-01-15",
        DateNotation(N1="2026", N2="01", N3="15"),
        {"US": "01/15/2026"},
        id="date",
    ),
    pytest.param(
        CountryCapability,
        CountryContract,
        "DE",
        CountryNotation(shape="alpha2", value="DE"),
        {"alpha3": "DEU", "numeric": "276", "name": "GERMANY"},
        id="country",
    ),
    pytest.param(
        MoneyCapability,
        MoneyContract,
        "USD 500.00",
        MoneyNotation(
            currency_part="USD",
            amount_part="500",
            currency_shape="code",
            amount_shape="integer",
        ),
        {"compact": "USD500.00"},
        id="money",
    ),
    pytest.param(
        PhoneCapability,
        PhoneContract,
        "+15551234567",
        PhoneNotation(shape="e164", value="15551234567"),
        {"rfc3966": "tel:+15551234567", "national": "5551234567"},
        id="phone",
    ),
]

# Capabilities that offer no alternative formats: their formatter must be the
# identity regardless of the requested format.
_IDENTITY_SURFACES = [
    pytest.param(
        EmailCapability,
        EmailContract,
        "user@example.com",
        EmailNotation(local_part="user", domain_part="example.com"),
        id="email",
    ),
    pytest.param(
        IPCapability,
        IPContract,
        "192.0.2.1",
        IPNotation(address="192.0.2.1"),
        id="ip",
    ),
]


class TestFormatValueSurface:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_canonical,_notation",
        _FORMAT_SURFACES,
    )
    def test_formatter_default_agrees_with_contract_default(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _canonical: str,
        _notation: object,
    ) -> None:
        """Rendering in the contract's default format keeps the value."""
        capability = _capability()
        default_format = _contract_class.DEFAULT_OUTPUT_FORMAT
        assert capability.format_value(_canonical, default_format, _notation) == (
            _canonical
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_canonical,_notation,_expected_by_format",
        _FORMATTED_EXPECTATIONS,
    )
    def test_every_offered_format_renders_expected_value(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _canonical: str,
        _notation: object,
        _expected_by_format: dict[str, str],
    ) -> None:
        """Each offered format is handled by the formatter.

        The expectation table must cover exactly the capability's offered
        formats: a newly offered format with no expectation (or a stale
        expectation for a withdrawn format) fails the set-equality guard.
        """
        assert set(_contract_class.OFFERED_OUTPUT_FORMATS) == set(_expected_by_format)
        capability = _capability()
        for output_format, expected in _expected_by_format.items():
            assert (
                capability.format_value(_canonical, output_format, _notation)
                == expected
            )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "_capability,_contract_class,_canonical,_notation",
        _IDENTITY_SURFACES,
    )
    def test_no_offered_format_capabilities_are_identity(
        self,
        _capability: type[object],
        _contract_class: type[object],
        _canonical: str,
        _notation: object,
    ) -> None:
        """Email/IP offer no formats; the formatter leaves the value unchanged."""
        assert not _contract_class.OFFERED_OUTPUT_FORMATS
        capability = _capability()
        assert (
            capability.format_value(
                _canonical, _contract_class.DEFAULT_OUTPUT_FORMAT, _notation
            )
            == _canonical
        )
        assert capability.format_value(_canonical, None, _notation) == _canonical
