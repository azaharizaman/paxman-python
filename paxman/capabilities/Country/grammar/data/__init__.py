"""Country grammar recognition key sets.

Each module exports a frozenset of syntax-normalized name representation
keys for recognition. The key sets contain no token-to-country mappings —
validation rules own every token-to-country decision.

Locales: english_names.py (ISO 3166-1 English), historical_names.py
(ISO 3166-3 former names), chinese_names.py (CLDR zh), localized_names.py
(CLDR zh/es/fr — the full current CLDR spelling catalog).

New locale files can be added here and imported in name_recognition.py.
"""
