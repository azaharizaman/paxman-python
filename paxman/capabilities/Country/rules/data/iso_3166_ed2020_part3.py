"""ISO 3166-3:2020 formerly used country names.

Source: https://www.iso.org/standard/63545.html
Section 4.2: Formerly used names of countries
"""

from __future__ import annotations

# Historical names to current alpha-2
# Format: {historical_name: current_alpha2_code}
HISTORICAL_TO_ALPHA2: dict[str, str] = {
    "BURMA": "MM",
    "CEYLON": "LK",
    "SIAM": "TH",
    "PERSIA": "IR",
    "RHODESIA": "ZW",
    "SWAZILAND": "SZ",
    "ABYSSINIA": "ET",
    "GOLD COAST": "GH",
    "UPPER VOLTA": "BF",
    "DUTCH EAST INDIES": "ID",
    "NEW HEBRIDES": "VU",
    "DANZIG": "PL",
    "PRUSSIA": "DE",
    "USSR": "RU",
    "CZECHOSLOVAKIA": "CZ",
    "YUGOSLAVIA": "RS",
    "EAST GERMANY": "DE",
    "WEST GERMANY": "DE",
    "TANGANYIKA": "TZ",
    "ZANZIBAR": "TZ",
    "SOUTH RHODESIA": "ZW",
    "NORTH RHODESIA": "ZM",
    "NYASALAND": "MW",
    "FORMOSA": "TW",
    "MANCHURIA": "CN",
    "TIBET": "CN",
}
