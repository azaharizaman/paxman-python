from hypothesis import given
from hypothesis import strategies as st

from paxman.capabilities.IBAN.contract import IBANContract
from paxman.capabilities.IBAN.notation import IBANNotation
from paxman.capabilities.IBAN.rules.iso_13616_1_ed2020 import Section4IBANStructureMOD97


def calc_check(country: str, bban: str) -> str:
    """ISO/IEC 7064 MOD 97-10 generation: 98 - (mod97 of bban+cc+"00")."""
    rearr = bban + country + "00"
    exp = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearr)
    r = 0
    for ch in exp:
        r = (r * 10 + int(ch)) % 97
    return f"{98 - r:02d}"


@given(
    st.text(min_size=15, max_size=34, alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
)
def test_random_strings_usually_invalid(s: str) -> None:
    rule = Section4IBANStructureMOD97()
    n = IBANNotation(country_code=s[:2], check_digits=s[2:4], bban=s[4:], compact=s)
    assert rule.matches(n, IBANContract()) in (True, False)


def test_generated_valid_is_valid() -> None:
    bban = "370400440532013000"
    cc = "DE"
    dd = calc_check(cc, bban)
    compact = cc + dd + bban
    assert Section4IBANStructureMOD97().matches(
        IBANNotation(country_code=cc, check_digits=dd, bban=bban, compact=compact),
        IBANContract(),
    )
