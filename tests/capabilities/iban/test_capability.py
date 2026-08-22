import pytest

from paxman.capabilities.IBAN.capability import IBANCapability
from paxman.capabilities.IBAN.notation import IBANNotation

pytestmark = [pytest.mark.capability]

CAP = IBANCapability()


def test_wiring_counts() -> None:
    assert CAP.name == "iban"
    assert len(CAP.get_grammars()) == 1
    assert CAP.get_grammars()[0].name == "iban_recognition"
    assert len(CAP.get_rules()) == 1
    assert CAP.get_rules()[0].name == "Section 4-iban-structure-mod97"


def test_create_contract_defaults() -> None:
    c = CAP.create_contract()
    assert c.output_format == "electronic"
    assert c.excluded_rules == ()
    assert c.pinned_rules is None


def test_format_value_paper_roundtrip() -> None:
    cases = {
        "DE89370400440532013000": "DE89 3704 0044 0532 0130 00",
        "GB29NWBK60161331926819": "GB29 NWBK 6016 1331 9268 19",
        "NO9386011117947": "NO93 8601 1117 947",
        "LC55HEMM000100010012001200023015": "LC55 HEMM 0001 0001 0012 0012 0002 3015",
    }
    for electronic, paper in cases.items():
        n = IBANNotation(
            country_code=electronic[:2],
            check_digits=electronic[2:4],
            bban=electronic[4:],
            compact=electronic,
        )
        assert CAP.format_value(electronic, "paper", n) == paper
        assert CAP.format_value(electronic, None, n) == electronic
        assert CAP.format_value(electronic, "electronic", n) == electronic
        assert CAP.format_value(paper.replace(" ", ""), "paper", n) == paper
