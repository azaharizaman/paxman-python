# paxman/capabilities/Phone/rules/data/nanp_tables.py
"""North American Numbering Plan (NANP) lookup tables.

Structure rules derived from the NANP (administered by NANPA).
Source: https://www.nanpa.com/
"""

from __future__ import annotations

# N11 service codes — NOT assignable as NPA or NXX (911, 411, etc.)
N11_CODES: frozenset[str] = frozenset(
    {"211", "311", "411", "511", "611", "711", "811", "911"}
)

# Service NPAs assigned by NANPA: toll-free + premium rate
SERVICE_NPAS: frozenset[str] = frozenset(
    {"800", "833", "844", "855", "866", "877", "888", "900"}
)
