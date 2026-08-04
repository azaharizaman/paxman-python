"""ISO 3166-3:2020 formerly used country names.

Source: https://www.iso.org/standard/72484.html
ISO 3166-3 lists formerly used country names that were deleted from
ISO 3166-1 since its first publication in 1974. Each entry represents
a historical country's own canonical identifier — its former alpha-2 code.

The successor state mappings (e.g., USSR → RU) are world knowledge recorded
in ISO 3166-3's "new country names" column but are NOT used for
canonicalization. Paxman validates that the input is a valid formerly used
name and returns the historical entity's own canonical alpha-2 code.

Total: 30 formerly used countries with 31 codes (CS appears twice —
once for Czechoslovakia, once for Serbia and Montenegro).

FORMER_NUMERIC_TO_ALPHA2 provides retired M49 codes for historical round-trip support.
"""

from __future__ import annotations

# Formerly used country name → former alpha-2 code
# The former alpha-2 code IS the canonical value for the historical entity.
# Format: {uppercased_name: former_alpha2_code}
FORMER_NAME_TO_ALPHA2: dict[str, str] = {
    # --- Name changes (same territory, name changed) ---
    "BURMA": "BU",  # → Myanmar (MM)
    "DAHOMEY": "DY",  # → Benin (BJ)
    "EAST TIMOR": "TP",  # → Timor-Leste (TL)
    "FRENCH AFARS AND ISSAS": "AI",  # → Djibouti (DJ)
    "NEW HEBRIDES": "NH",  # → Vanuatu (VU)
    "SOUTHERN RHODESIA": "RH",  # → Zimbabwe (ZW)
    "UPPER VOLTA": "HV",  # → Burkina Faso (BF)
    "YUGOSLAVIA": "YU",  # → Serbia and Montenegro (CS)
    "ZAIRE": "ZR",  # → Congo, Dem. Rep. (CD)
    # --- Mergers (territory merged into another country) ---
    "GERMAN DEMOCRATIC REPUBLIC": "DD",  # → Germany (DE)
    "EAST GERMANY": "DD",  # Common alternate name
    "EAST GERMAN": "DD",  # Common alternate name
    "GDR": "DD",  # Common alternate name
    "FRANCE, METROPOLITAN": "FX",  # → France (FR)
    "METROPOLITAN FRANCE": "FX",  # Common alternate name
    # --- Divisions (territory divided into multiple countries) ---
    "CANTON AND ENDERBURY ISLANDS": "CT",  # → Kiribati (KI)
    "CZECHOSLOVAKIA": "CS",  # → Czechia (CZ) + Slovakia (SK)
    "GILBERT ISLANDS": "GE",  # → Kiribati (KI)
    "NETHERLANDS ANTILLES": "AN",  # → BQ + CW + SX
    "NEUTRAL ZONE": "NT",  # Divided between Iraq (IQ) + Saudi Arabia (SA)
    "PACIFIC ISLANDS": "PC",  # → MH + FM + MP + PW
    "SERBIA AND MONTENEGRO": "CS",  # → Montenegro (ME) + Serbia (RS)
    "USSR": "SU",  # → 15 successor states
    "SOVIET UNION": "SU",  # ISO 3166-3 official alternate name
    "UNION OF SOVIET SOCIALIST REPUBLICS": "SU",  # Full official name
    "USSR SOVIET SOCIALIST REPUBLICS": "SU",  # Common alternate name
    "VIET-NAM, DEMOCRATIC REPUBLIC OF": "VD",  # → Viet Nam (VN)
    "NORTH VIETNAM": "VD",  # Common alternate name
    "VIET CONG": "VD",  # Common alternate name
    "YEMEN, DEMOCRATIC": "YD",  # → Yemen (YE)
    "SOUTH YEMEN": "YD",  # Common alternate name
    "PEOPLES DEMOCRATIC REPUBLIC OF YEMEN": "YD",  # Common alternate name
    # --- Merged into existing countries ---
    "SIKKIM": "SK",  # → India (IN)
}

# Former alpha-2 codes that are NOT currently assigned in ISO 3166-1
# (for round-trip validation — these codes can be validated by
# SectionHistoricalNames when include_historical=True)
FORMER_ALPHA2_CODES: frozenset[str] = frozenset(
    {
        "BU",  # Burma → reassignable after 50-year transition
        "DY",  # Dahomey → reassignable
        "CS",  # Czechoslovakia / Serbia and Montenegro → round-trip support
        "TP",  # East Timor → reassignable
        "DD",  # German Democratic Republic → reassignable
        "FX",  # France, Metropolitan → reassignable
        "NH",  # New Hebrides → reassignable
        "RH",  # Southern Rhodesia → reassignable
        "HV",  # Upper Volta → reassignable
        "SU",  # USSR → reassignable
        "YU",  # Yugoslavia → reassignable
        "ZR",  # Zaire → reassignable
        "AN",  # Netherlands Antilles → reassignable
        "NT",  # Neutral Zone → reassignable
        "PC",  # Pacific Islands → reassignable
        "CT",  # Canton and Enderbury Islands → reassignable
        "VD",  # Viet-Nam, Dem. Rep. → reassignable
        "YD",  # Yemen, Democratic → reassignable
        # Note: CS (Czechoslovakia / Serbia and Montenegro) was added for
        # round-trip support (numeric code 200 is no longer active). GE
        # (Gilbert Islands) is intentionally omitted — the name change was
        # temporary and the alpha-2 code was never reassigned.
    }
)

# Former numeric (M49) codes that were retired from ISO 3166-1
# M49 numeric → former alpha-2 code for retired/inactive entries.
# Retained for round-trip support when include_historical=True.
FORMER_NUMERIC_TO_ALPHA2: dict[str, str] = {
    "200": "CS",  # Czechoslovakia (CSHH) → split into CZ + SK;
    # Serbia and Montenegro (CSXX) → split into ME + RS
    "530": "AN",  # Netherlands Antilles → dissolved into BQ + CW + SX
}
