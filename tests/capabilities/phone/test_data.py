"""Tests for Phone lookup table data integrity."""

from paxman.capabilities.Phone.rules.data.e164_country_codes import (
    ASSIGNED_COUNTRY_CODES,
)
from paxman.capabilities.Phone.rules.data.nanp_tables import N11_CODES, SERVICE_NPAS


class TestE164CountryCodes:
    """Tests for the E.164 country code table."""

    def test_verified_count(self) -> None:
        """The table is locked to the verified count of assigned codes.

        The count survived the 2026 reconciliation: 979 (UIPRS) added and
        684 (American Samoa — a NANP +1-684 code, never a standalone E.164
        code) removed.
        """
        assert len(ASSIGNED_COUNTRY_CODES) == 217

    def test_all_keys_are_1_to_3_digits(self) -> None:
        """Every country code is 1-3 digits long."""
        for code in ASSIGNED_COUNTRY_CODES:
            assert code.isdigit()
            assert 1 <= len(code) <= 3

    def test_no_code_is_prefix_of_another(self) -> None:
        """Longest-prefix matching must be deterministic.

        No assigned country code may be a prefix of another assigned code;
        otherwise split_country_code's longest-prefix search would be
        ambiguous (e.g., 1 vs 12, 80 vs 800).
        """
        codes = sorted(ASSIGNED_COUNTRY_CODES)
        for i, short in enumerate(codes):
            for long in codes[i + 1 :]:
                assert not long.startswith(short), (
                    f"{long} starts with {short} — ambiguous country code"
                )

    def test_known_codes_present(self) -> None:
        """Spot-check a handful of assigned codes across zones."""
        assert "1" in ASSIGNED_COUNTRY_CODES  # NANP
        assert "44" in ASSIGNED_COUNTRY_CODES  # UK
        assert "886" in ASSIGNED_COUNTRY_CODES  # Taiwan
        assert "800" in ASSIGNED_COUNTRY_CODES  # International Freephone
        assert "979" in ASSIGNED_COUNTRY_CODES  # International Premium Rate Service

    def test_unassigned_codes_absent(self) -> None:
        """Codes known to be unassigned are not in the table."""
        assert "999" not in ASSIGNED_COUNTRY_CODES
        assert "0" not in ASSIGNED_COUNTRY_CODES
        assert "15" not in ASSIGNED_COUNTRY_CODES
        # 684 is American Samoa's NANP area code (+1-684), not a standalone
        # E.164 country code (standalone +684 was withdrawn in 2004).
        assert "684" not in ASSIGNED_COUNTRY_CODES
        # 997 was reserved for Kazakhstan but abandoned in November 2023.
        assert "997" not in ASSIGNED_COUNTRY_CODES


class TestNanpTables:
    """Tests for NANP lookup tables."""

    def test_n11_codes_exact(self) -> None:
        """N11 service codes are exactly the 8 reserved codes."""
        assert {"211", "311", "411", "511", "611", "711", "811", "911"} == N11_CODES

    def test_service_npas_exact(self) -> None:
        """Service NPAs are exactly the toll-free and premium codes."""
        assert {"800", "833", "844", "855", "866", "877", "888", "900"} == SERVICE_NPAS
