import pytest
from dataclasses import FrozenInstanceError
from paxman.capabilities.IBAN.notation import IBANNotation

pytestmark = [pytest.mark.capability]

def test_frozen_slots_hash():
    n = IBANNotation(country_code="DE", check_digits="89", bban="370400440532013000", compact="DE89370400440532013000")
    assert n.country_code == "DE"
    assert hash(n) is not None
    assert hasattr(n, "__slots__")
    with pytest.raises(FrozenInstanceError):
        n.compact = "X"  # type: ignore[misc]

def test_compact_is_concatenation():
    n = IBANNotation(country_code="GB", check_digits="29", bban="NWBK60161331926819", compact="GB29NWBK60161331926819")
    assert n.compact == n.country_code + n.check_digits + n.bban
    assert 15 <= len(n.compact) <= 34
