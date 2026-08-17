"""Tests for the SIUnit capability wiring."""

import pytest

from paxman.api import canonicalize
from paxman.capabilities.SIUnit.capability import SIUnitCapability
from paxman.capabilities.SIUnit.contract import SIUnitContract
from paxman.capabilities.SIUnit.notation import SIUnitNotation
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution


@pytest.mark.capability
@pytest.mark.si_unit
class TestSIUnitCapability:
    """Capability wiring — grammars, rules, factory, exports."""

    def setup_method(self) -> None:
        self.capability = SIUnitCapability()

    def test_metadata(self) -> None:
        # name == "si_unit"; version == "1.0.0"
        assert self.capability.name == "si_unit"
        assert self.capability.version == "1.0.0"

    def test_get_grammars(self) -> None:
        # 3 instances with names {symbol_recognition, name_recognition,
        # compound_recognition}
        names = {g.name for g in self.capability.get_grammars()}
        assert names == {
            "symbol_recognition",
            "name_recognition",
            "compound_recognition",
        }

    def test_get_rules(self) -> None:
        # 7 instances: 5 BIPM sections + 1 ISO compound section +
        # 1 opt-in split-word-prefix rescue rule
        names = {r.name for r in self.capability.get_rules()}
        assert names == {
            "Section 2.3.1-base-units",
            "Section 2.3.2-derived-units",
            "Section 4.1-non-si-units",
            "Section 3.2-prefixes",
            "Section-names",
            "Section 6.5-compounds",
            "Section 3.2-split-word-prefixes",
        }

    def test_create_contract_defaults(self) -> None:
        # create_contract() returns SIUnitContract with defaults
        contract = self.capability.create_contract()
        assert isinstance(contract, SIUnitContract)
        assert contract.excluded_rules == ()
        assert contract.pinned_rules is None
        assert contract.output_format == "symbol"  # DEFAULT_OUTPUT_FORMAT

    def test_create_contract_excluded_rules(self) -> None:
        contract = self.capability.create_contract(excluded_rules=["Section-names"])
        assert contract.excluded_rules == ("Section-names",)

    def test_create_contract_extra_grammars(self) -> None:
        # SEAM: the community opt-in field is forwarded by the factory
        # (surface guard: default () + forwarding through create_contract).
        contract = self.capability.create_contract(
            extra_grammars=["dot_unit_recognition"]
        )
        assert contract.extra_grammars == ("dot_unit_recognition",)
        assert self.capability.create_contract().extra_grammars == ()

    def test_create_contract_keyword_only(self) -> None:
        # ContractFactory conformance: the common block is keyword-only
        with pytest.raises(TypeError):
            self.capability.create_contract("Section-names")  # type: ignore[call-arg]

    def test_format_value_identity(self) -> None:
        # offered formats are empty -> base identity is the contract
        notation = SIUnitNotation(text="kg", shape="symbol")
        assert self.capability.format_value("kg", "symbol", notation) == "kg"


def test_package_exports() -> None:
    # __all__ exports SIUnitCapability, SIUnitContract, SIUnitNotation
    from paxman.capabilities.SIUnit import (
        SIUnitCapability as CapabilityExport,
    )
    from paxman.capabilities.SIUnit import (
        SIUnitContract as ContractExport,
    )
    from paxman.capabilities.SIUnit import (
        SIUnitNotation as NotationExport,
    )

    assert CapabilityExport is SIUnitCapability
    assert ContractExport is SIUnitContract
    assert NotationExport is SIUnitNotation


@pytest.mark.capability
@pytest.mark.si_unit
class TestSIUnitCapabilityMultiSolidusAndParens:
    """End-to-end: ISO 80000-1 §6.6.2 multi-solidus rejection + §6.5 parens."""

    @pytest.fixture(autouse=True)
    def _clean_registry(self) -> None:
        """Reset the capability registry before each test (it may be frozen)."""
        reset_registry()
        yield
        reset_registry()

    def test_multi_solidus_invalid_by_default(self) -> None:
        # More than one top-level "/" is INVALID under the default contract
        # (ISO 80000-1 §6.6.2).
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("kg/m/s", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    def test_parenthesized_denominator_success(self) -> None:
        # A parenthesized denominator MUST resolve (ISO 80000-1 §6.6.2
        # prescribes parentheses as the disambiguation).
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("kg/(m·s²)", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "kg/(m·s2)"

    def test_multi_solidus_success_when_allowed(self) -> None:
        # The legacy accept-multi-solidus behavior is preserved when the
        # contract opts in via allow_multi_solidus=True.
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract(allow_multi_solidus=True)
        result = canonicalize("kg/m/s", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "kg/m/s"


@pytest.mark.capability
@pytest.mark.si_unit
class TestSIUnitCapabilitySplitPrefixes:
    """End-to-end: spaced SI prefix handling (word merge + symbol reject).

    Word prefixes across a space ("kilo gram") are not standard SI and are
    rejected by default, but merge to the prefixed symbol when the contract
    opts in via ``allow_split_word_prefixes``. Symbol prefixes across a space
    are rejected when the leading symbol is prefix-ONLY (``k g`` → INVALID:
    a prefix symbol must bind tightly with no space, and leaving it would
    corrupt dimensionality, e.g. ``k g`` must not resolve to ``g``). Dual-role
    prefix symbols that are also unit symbols (``m``, ``h``, ``a``, ``d``) stay
    as separate units, so ``m s`` is valid metre-second and ``m m`` resolves to
    ``m`` (metre) — crucially never collapsing to ``mm`` (10⁻³ m).
    """

    @pytest.fixture(autouse=True)
    def _clean_registry(self) -> None:
        reset_registry()
        yield
        reset_registry()

    # --- Word prefix: strict by default ---
    def test_word_prefix_invalid_by_default(self) -> None:
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("kilo gram", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    # --- Word prefix: merge when opted in ---
    def test_word_prefix_merges_when_allowed(self) -> None:
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract(allow_split_word_prefixes=True)
        result = canonicalize("kilo gram", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "kg"

    def test_word_prefix_merges_megahertz_when_allowed(self) -> None:
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract(allow_split_word_prefixes=True)
        result = canonicalize("mega hertz", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "MHz"

    # --- Symbol prefix: ALWAYS rejected (no flag) ---
    def test_symbol_prefix_always_invalid(self) -> None:
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("k g", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    def test_symbol_prefix_always_invalid_even_when_word_allowed(self) -> None:
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract(allow_split_word_prefixes=True)
        result = canonicalize("k g", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    def test_symbol_prefix_m_m_not_collapsed_to_mm(self) -> None:
        # "m m" is the dual-role prefix "m" (milli + metre). It MUST NOT
        # collapse to "mm" (millimetre, 10⁻³ m). It resolves to "m" (metre)
        # as two unit tokens, never to the prefixed millimetre symbol.
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("m m", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "m"

    def test_dual_role_spaced_prefix_stays_units(self) -> None:
        # "m s" is the valid SI expression "metre second": "m" is also the
        # metre unit (not prefix-only), so the pair stays two units and is
        # AMBIGUOUS — never a rejectable split. Contrast with "k g" below.
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("m s", contract)
        assert result.status == Resolution.AMBIGUOUS
        assert result.canonicalized_value is None

    def test_prefix_only_spaced_symbol_invalid(self) -> None:
        # "k g": "k" is a prefix-ONLY symbol (not a unit), so the only reading
        # is a broken spaced prefix → INVALID; the inner "g" is consumed so it
        # cannot resolve to the gram candidate.
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("k g", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None

    # --- Regression guards: existing behavior preserved ---
    def test_no_space_word_still_success(self) -> None:
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        assert canonicalize("kilogram", contract).canonicalized_value == "kg"
        assert canonicalize("kg", contract).canonicalized_value == "kg"
        assert canonicalize("gram", contract).canonicalized_value == "g"

    def test_phase1_behavior_preserved(self) -> None:
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        assert canonicalize("m/s", contract).canonicalized_value == "m/s"
        assert canonicalize("kg/(m·s²)", contract).canonicalized_value == "kg/(m·s2)"
        assert canonicalize("kg/m/s", contract).status == Resolution.INVALID
