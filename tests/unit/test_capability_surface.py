"""Guard tests for the unanimous capability contract & rule surface.

These tests lock the homogeneity mandate so it cannot regress: every one of
the five built-in capabilities (Email, Date, Country, IP, Phone) must

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
from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Date.contract import DateContract
from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.Email.contract import EmailContract
from paxman.capabilities.IP.capability import IPCapability
from paxman.capabilities.IP.contract import IPContract
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.capabilities.Phone.contract import PhoneContract
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
