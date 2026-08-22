import pytest
from paxman.core.errors import ContractError
from paxman.capabilities.IBAN.contract import IBANContract

pytestmark = [pytest.mark.capability]

def test_default_output_format_resolves():
    c = IBANContract()
    assert c.output_format == "electronic"
    assert c.capability_name == "iban"
    assert IBANContract.DEFAULT_OUTPUT_FORMAT == "electronic"
    assert IBANContract.OFFERED_OUTPUT_FORMATS == frozenset({"paper"})

def test_paper_offered():
    c = IBANContract(output_format="paper")
    assert c.output_format == "paper"

def test_default_alias_via_none_and_default_string():
    for alias in (None, "default", "electronic"):
        c = IBANContract(output_format=alias)
        assert c.output_format == "electronic"

def test_invalid_output_format_raises():
    with pytest.raises(ContractError):
        IBANContract(output_format="hyphenated")  # ISSN-ism, not IBAN
    with pytest.raises(ContractError):
        IBANContract(output_format="compact")  # alias not offered; must normalize outside

def test_frozen_contract():
    from dataclasses import FrozenInstanceError
    c = IBANContract()
    with pytest.raises(FrozenInstanceError):
        c.output_format = "paper"  # type: ignore[misc]
