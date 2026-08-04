"""Historical country name recognition keys.

Contains the historical/deprecated country name representations the
Country name grammar recognizes. This is recognition-only data — keys
are syntax-normalized forms, and no token is mapped to a canonical
entity here. ISO 3166-3 rule data owns every historical
token-to-country decision.

Keys are normalized with normalize_name() at module construction.
"""

from __future__ import annotations

from paxman.capabilities.Country.name_normalization import normalize_name

HISTORICAL_NAME_KEYS: frozenset[str] = frozenset(
    normalize_name(key)
    for key in {
        # --- Name changes (same territory, name changed) ---
        "BURMA",
        "DAHOMEY",
        "EAST TIMOR",
        "FRENCH AFARS AND ISSAS",
        "NEW HEBRIDES",
        "SOUTHERN RHODESIA",
        "UPPER VOLTA",
        "YUGOSLAVIA",
        "ZAIRE",
        # --- Mergers ---
        "GERMAN DEMOCRATIC REPUBLIC",
        "EAST GERMANY",
        "EAST GERMAN",
        "GDR",
        "METROPOLITAN FRANCE",
        "FRANCE, METROPOLITAN",  # ISO 3166-3 official spelling
        # --- Divisions ---
        "CANTON AND ENDERBURY ISLANDS",
        "CZECHOSLOVAKIA",
        "GILBERT ISLANDS",
        "NETHERLANDS ANTILLES",
        "NEUTRAL ZONE",
        "PACIFIC ISLANDS",
        "SERBIA AND MONTENEGRO",
        "USSR",
        "SOVIET UNION",
        "UNION OF SOVIET SOCIALIST REPUBLICS",
        "USSR SOVIET SOCIALIST REPUBLICS",
        "NORTH VIETNAM",
        "VIET-NAM, DEMOCRATIC REPUBLIC OF",  # ISO 3166-3 official spelling
        "VIET CONG",
        "SOUTH YEMEN",
        "YEMEN, DEMOCRATIC",  # ISO 3166-3 official spelling
        "PEOPLES DEMOCRATIC REPUBLIC OF YEMEN",
        # --- Merged into existing ---
        "SIKKIM",
    }
)
