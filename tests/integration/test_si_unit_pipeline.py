"""Integration tests for the SI Unit capability pipeline."""

from collections.abc import Iterator

import pytest

from paxman.api import canonicalize
from paxman.capabilities.SIUnit.capability import SIUnitCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution


@pytest.fixture(autouse=True)
def _clean_registry() -> Iterator[None]:
    """Reset the capability registry before and after each test."""
    reset_registry()
    yield
    reset_registry()


class TestSIUnitPipeline:
    """Full-pipeline tests for the SI Unit capability.

    Locked semantics (plan §1 e2e contract):
    - identity-only: no quantities, no magnitudes, no name-compounds
      ("metre per second" does not resolve as a compound — its words are
      recognized separately, yielding AMBIGUOUS). Canonical form is the unit
      symbol (D3) — names resolve to their symbol, "l" canonicalizes to
      "L", compound exponents render as ASCII digits;
    - symbols are case-exact (D6): "pa" and "Kg" are not recognized at
      all -> MISSING, and "KHz" is MISSING not INVALID (R1) — the symbol
      grammar is a case-exact lexicon, so an invalid prefix casing never
      matches;
    - bare prefix symbols ("da", "k") are recognized but no rule resolves
      them -> INVALID; compound shapes over unknown groups ("QQQ/zzz")
      are recognized by the shape grammar but rejected by the ISO 80000-1
      rule -> INVALID;
    - "25°C" is quantity-glued: the degree sign blocks a fallback to bare
      "C", so nothing matches -> MISSING (D7); "USD" is not an SI token
      -> MISSING;
    - "m s" (space, no separator) is two independent symbol recognitions
      carrying distinct canonical values "m" and "s" -> AMBIGUOUS, never
      a compound SUCCESS (R2);
    - INVALID rows carry no candidates (recognized, but no rule validated
      them) and MISSING rows carry no candidates (nothing recognized);
    - provenance: names, symbols, and prefixes resolve via the BIPM SI
      Brochure (9th ed., 2019); product/quotient compounds resolve via
      ISO 80000-1 §6.5.
    """

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "text,expected_status,expected_value",
        [
            # --- SUCCESS rows ---
            ("Kilogram", Resolution.SUCCESS, "kg"),  # BIPM Table 1 (name→symbol)
            ("Kelvin", Resolution.SUCCESS, "K"),  # BIPM Table 1
            ("megahertz", Resolution.SUCCESS, "MHz"),  # BIPM §3.2 (prefix)
            ("m", Resolution.SUCCESS, "m"),  # BIPM Table 1
            ("kg", Resolution.SUCCESS, "kg"),  # BIPM Table 1
            ("cd", Resolution.SUCCESS, "cd"),  # BIPM Table 1
            ("Pa", Resolution.SUCCESS, "Pa"),  # BIPM Tables 3–4
            ("\u00b0C", Resolution.SUCCESS, "\u00b0C"),  # BIPM Tables 3–4
            ("l", Resolution.SUCCESS, "L"),  # BIPM Tables 8–9 (l→L)
            ("L", Resolution.SUCCESS, "L"),  # BIPM Tables 8–9
            ("km", Resolution.SUCCESS, "km"),  # BIPM §3.2
            ("\u00b5g", Resolution.SUCCESS, "\u00b5g"),  # BIPM §3.2
            ("m/s\u00b2", Resolution.SUCCESS, "m/s2"),  # ISO 80000-1 §6.5
            ("km/h", Resolution.SUCCESS, "km/h"),  # ISO 80000-1 §6.5
            ("N\u00b7m", Resolution.SUCCESS, "N\u00b7m"),  # ISO 80000-1 §6.5
            ("kg\u00b7m/s\u00b2", Resolution.SUCCESS, "kg\u00b7m/s2"),  # §6.5
            ("g/cm\u00b3", Resolution.SUCCESS, "g/cm3"),  # ISO 80000-1 §6.5
            ("m\u00b7s\u207b\u00b2", Resolution.SUCCESS, "m\u00b7s-2"),  # §6.5
            # --- INVALID rows ---
            ("da", Resolution.INVALID, None),  # bare prefix (recognized, no rule)
            ("k", Resolution.INVALID, None),  # bare prefix (recognized, no rule)
            ("QQQ/zzz", Resolution.INVALID, None),  # compound shape, unknown groups
            # --- MISSING rows ---
            ("pa", Resolution.MISSING, None),  # case-exact symbols (D6)
            ("KHz", Resolution.MISSING, None),  # refinement R1
            ("Kg", Resolution.MISSING, None),  # case-exact (D6)
            ("25\u00b0C", Resolution.MISSING, None),  # quantity-glued (D7)
            ("USD", Resolution.MISSING, None),  # not an SI token
            # --- AMBIGUOUS row ---
            ("m s", Resolution.AMBIGUOUS, None),  # refinement R2
            # name-compound: words recognized separately -> AMBIGUOUS (R2 analogue)
            ("metre per second", Resolution.AMBIGUOUS, None),
        ],
    )
    def test_e2e_contract(
        self,
        text: str,
        expected_status: Resolution,
        expected_value: str | None,
    ) -> None:
        """Every row of the plan §1 e2e contract through canonicalize()."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize(text, contract)
        assert result.status == expected_status
        assert result.canonicalized_value == expected_value
        if expected_status in (Resolution.MISSING, Resolution.INVALID):
            assert result.candidates == ()

    @pytest.mark.integration
    def test_ambiguous_row_m_s_carries_both_canonical_values(self) -> None:
        """R2: "m s" is AMBIGUOUS, never a compound SUCCESS.

        The compound grammar requires "/", "·" or "⋅" separators, so "m s"
        yields two independent symbol recognitions ("m", "s"); the engine
        preserves overlaps, so both distinct canonical values survive into
        the candidate set and the status is AMBIGUOUS.
        """
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("m s", contract)
        assert result.status == Resolution.AMBIGUOUS
        assert result.canonicalized_value is None
        assert {c.value for c in result.candidates} == {"m", "s"}

    @pytest.mark.integration
    def test_provenance_name_bipm_si_brochure(self) -> None:
        """A name SUCCESS carries BIPM SI Brochure provenance (Section-names)."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("Kilogram", contract)
        assert result.status == Resolution.SUCCESS
        candidate = result.candidates[0]
        assert candidate.validation_rule == "Section-names"
        prov = candidate.provenance[0]
        assert "SI Brochure" in prov.specification_name
        assert prov.authority == "BIPM"

    @pytest.mark.integration
    def test_provenance_prefixed_name_bipm_si_brochure(self) -> None:
        """A prefixed name SUCCESS carries BIPM provenance (prefix rule)."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("megahertz", contract)
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "MHz"
        candidate = result.candidates[0]
        assert candidate.validation_rule == "Section-names"
        prov = candidate.provenance[0]
        assert "SI Brochure" in prov.specification_name
        assert prov.authority == "BIPM"

    @pytest.mark.integration
    def test_provenance_compound_iso_80000_1(self) -> None:
        """A compound SUCCESS carries ISO 80000-1 provenance (§6.5)."""
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("m/s\u00b2", contract)
        assert result.status == Resolution.SUCCESS
        candidate = result.candidates[0]
        assert candidate.validation_rule == "Section 6.5-compounds"
        prov = candidate.provenance[0]
        assert "ISO 80000-1" in prov.specification_name
        assert prov.authority == "ISO"

    @pytest.mark.integration
    def test_frozen_registry_second_call_succeeds(self) -> None:
        """The registry freezes on first canonicalize(); a second call succeeds.

        The engine freezes the registry at pipeline start and never
        re-registers, so two calls through the same registered capability
        both resolve (never a CapabilityError on the second call).
        """
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        first = canonicalize("kg", contract)
        second = canonicalize("m", contract)
        assert first.status == Resolution.SUCCESS
        assert first.canonicalized_value == "kg"
        assert second.status == Resolution.SUCCESS
        assert second.canonicalized_value == "m"

    @pytest.mark.integration
    def test_ambiguous_name_compound_metre_per_second(self) -> None:
        """R2 analogue: a name-compound yields AMBIGUOUS, never SUCCESS.

        "metre per second" is not a compound — the name grammar recognizes
        "metre" and "second" independently, so two distinct canonical values
        ("m", "s") survive into the candidate set and the status is
        AMBIGUOUS. This is the documented headline case; it must stay locked.
        """
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()
        result = canonicalize("metre per second", contract)
        assert result.status == Resolution.AMBIGUOUS
        assert result.canonicalized_value is None
        assert {c.value for c in result.candidates} == {"m", "s"}

    @pytest.mark.integration
    def test_determinism_reproducible_output(self) -> None:
        """Same input + contract yields reproducible output across calls.

        Determinism is a general correctness property (not a byte-identical
        mandate — the replay-hash baseline was removed): an identical input
        and contract must resolve to the same status, canonical value, and
        candidate order on every call. This pins it for an AMBIGUOUS input
        and a SUCCESS input.
        """
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract()

        first = canonicalize("m s", contract)
        second = canonicalize("m s", contract)
        assert first.status == second.status
        assert first.canonicalized_value == second.canonicalized_value
        assert [c.value for c in first.candidates] == [
            c.value for c in second.candidates
        ]

        third = canonicalize("Kilogram", contract)
        fourth = canonicalize("Kilogram", contract)
        assert third.status == fourth.status
        assert third.canonicalized_value == fourth.canonicalized_value

    @pytest.mark.integration
    def test_temporal_filter_year_excludes_base_units(self) -> None:
        """The `year` common param gates rules by publication year.

        All BIPM SI Brochure rules carry publication_year 2019, so a contract
        with year=2018 disables them: "kg" is still recognized by the grammar
        but no rule validates it -> INVALID (not MISSING, not SUCCESS).
        """
        register_capability(SIUnitCapability())
        contract = SIUnitCapability.create_contract(year=2018)
        result = canonicalize("kg", contract)
        assert result.status == Resolution.INVALID
        assert result.canonicalized_value is None
        assert result.candidates == ()
