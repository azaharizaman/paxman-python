"""Historical country name lookup table.

Maps historical/deprecated country names to their canonical historical
entity name per ISO 3166-3. Values align with FORMER_NAME_TO_ALPHA2 keys
used by SectionHistoricalNames for validation.

Normalized key format: UPPERCASE, punctuation stripped,
whitespace collapsed to single spaces.
"""

from __future__ import annotations

HISTORICAL_NAME_TO_CANONICAL: dict[str, str] = {
    # --- Name changes (same territory, name changed) ---
    "BURMA": "BURMA",
    "DAHOMEY": "DAHOMEY",
    "EAST TIMOR": "EAST TIMOR",
    "FRENCH AFARS AND ISSAS": "FRENCH AFARS AND ISSAS",
    "NEW HEBRIDES": "NEW HEBRIDES",
    "SOUTHERN RHODESIA": "SOUTHERN RHODESIA",
    "UPPER VOLTA": "UPPER VOLTA",
    "YUGOSLAVIA": "YUGOSLAVIA",
    "ZAIRE": "ZAIRE",
    # --- Mergers ---
    "GERMAN DEMOCRATIC REPUBLIC": "GERMAN DEMOCRATIC REPUBLIC",
    "EAST GERMANY": "GERMAN DEMOCRATIC REPUBLIC",
    "EAST GERMAN": "GERMAN DEMOCRATIC REPUBLIC",
    "GDR": "GERMAN DEMOCRATIC REPUBLIC",
    "METROPOLITAN FRANCE": "FRANCE, METROPOLITAN",
    # --- Divisions ---
    "CANTON AND ENDERBURY ISLANDS": "CANTON AND ENDERBURY ISLANDS",
    "CZECHOSLOVAKIA": "CZECHOSLOVAKIA",
    "GILBERT ISLANDS": "GILBERT ISLANDS",
    "NETHERLANDS ANTILLES": "NETHERLANDS ANTILLES",
    "NEUTRAL ZONE": "NEUTRAL ZONE",
    "PACIFIC ISLANDS": "PACIFIC ISLANDS",
    "SERBIA AND MONTENEGRO": "SERBIA AND MONTENEGRO",
    "USSR": "USSR",
    "SOVIET UNION": "USSR",
    "UNION OF SOVIET SOCIALIST REPUBLICS": "USSR",
    "USSR SOVIET SOCIALIST REPUBLICS": "USSR",
    "NORTH VIETNAM": "VIET-NAM, DEMOCRATIC REPUBLIC OF",
    "VIET CONG": "VIET-NAM, DEMOCRATIC REPUBLIC OF",
    "SOUTH YEMEN": "YEMEN, DEMOCRATIC",
    "PEOPLES DEMOCRATIC REPUBLIC OF YEMEN": "YEMEN, DEMOCRATIC",
    # --- Merged into existing ---
    "SIKKIM": "SIKKIM",
}
