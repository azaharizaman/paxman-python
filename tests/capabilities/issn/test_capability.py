"""ISSN capability wiring — ISSNCapability + format_value (Task 5)."""

import pytest

from paxman.capabilities.ISSN.capability import ISSNCapability
from paxman.capabilities.ISSN.notation import ISSNNotation
from paxman.core.errors import ContractError


@pytest.mark.capability
class TestISSNCapability:
    """ISSNCapability wiring and format_value seam."""

    def test_capability_name_version(self) -> None:
        assert ISSNCapability.name == "issn"
        assert ISSNCapability.version == "1.0.0"

    def test_get_grammars(self) -> None:
        cap = ISSNCapability()
        grammars = cap.get_grammars()
        assert len(grammars) == 1
        assert {g.name for g in grammars} == {"issn_recognition"}

    def test_get_rules(self) -> None:
        cap = ISSNCapability()
        rules = cap.get_rules()
        assert len(rules) == 1
        assert [r.name for r in rules] == ["Section 4-issn-check-digit"]

    def test_create_contract_defaults(self) -> None:
        c = ISSNCapability.create_contract()
        assert c.output_format == "hyphenated"
        assert c.capability_name == "issn"
        assert c.excluded_rules == ()
        assert c.pinned_rules is None
        assert c.year is None
        assert c.extra_grammars == ()
        # No active_grammars gating — inherits None from base
        assert c.active_grammars is None

    def test_create_contract_output_format(self) -> None:
        c_compact = ISSNCapability.create_contract(output_format="compact")
        assert c_compact.output_format == "compact"
        c_urn = ISSNCapability.create_contract(output_format="urn")
        assert c_urn.output_format == "urn"
        with pytest.raises(ContractError):
            ISSNCapability.create_contract(output_format="issn")

    def test_format_value_hyphenated_identity(self) -> None:
        cap = ISSNCapability()
        notation = ISSNNotation(digits="03178471")
        assert cap.format_value("0317-8471", "hyphenated", notation) == "0317-8471"
        assert cap.format_value("0317-8471", None, notation) == "0317-8471"

    def test_format_value_compact(self) -> None:
        cap = ISSNCapability()
        notation = ISSNNotation(digits="03178471")
        assert cap.format_value("0317-8471", "compact", notation) == "03178471"

    def test_format_value_urn(self) -> None:
        cap = ISSNCapability()
        notation = ISSNNotation(digits="03178471")
        assert cap.format_value("0317-8471", "urn", notation) == "urn:issn:0317-8471"

    def test_format_value_urn_with_x(self) -> None:
        cap = ISSNCapability()
        notation = ISSNNotation(digits="1050124X")
        assert cap.format_value("1050-124X", "urn", notation) == "urn:issn:1050-124X"
