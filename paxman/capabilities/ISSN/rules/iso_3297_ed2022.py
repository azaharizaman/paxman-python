"""ISO 3297:2022 rule: ISSN structure + mod-11 check digit."""

from paxman.capabilities.ISSN.notation import ISSNNotation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="ISSN International Centre",
    specification_name="ISO 3297:2022",
    kind="specification",
    reference_url="https://www.iso.org/standard/84536.html",
    version="2022",
    lifecycle="active",
    publication_year=2022,
)


def _issn_check(digits: str) -> str:
    """Compute expected check char for 8-char digits (weights 8→2, X=10)."""
    total = sum(int(d) * (8 - i) for i, d in enumerate(digits[:7]))
    check = (11 - total % 11) % 11
    return "X" if check == 10 else str(check)


class Section4CheckDigit(Rule[ISSNNotation]):
    """ISO 3297 Section 4 — ISSN check digit (8→2, X=10)."""

    name = "Section 4-issn-check-digit"
    strategy = RuleStrategy.PARSER
    provenance = PUBLICATION
    citation = "Section 4 (check digit)"
    target_semantics = frozenset({"issn_recognition"})
    requires_features = frozenset()

    def matches(self, notation: ISSNNotation, contract: Contract) -> bool:
        if len(notation.digits) != 8:
            return False
        if not notation.digits[:7].isdigit():
            return False
        last = notation.digits[7].upper()
        if last not in "0123456789X":
            return False
        return last == _issn_check(notation.digits)

    def normalize(self, notation: ISSNNotation, contract: Contract) -> str:
        digits = notation.digits.upper()
        return f"{digits[:4]}-{digits[4:]}"
