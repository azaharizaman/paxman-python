"""Migration Proof Harness — byte-identical RecognitionMatch parity.

Every migration PR must prove the new PipelineGrammar declaration produces
the same list[RecognitionMatch] as the old bespoke recognize() for a
curated corpus plus property-generated inputs.

Corpus must cover:
- Country/name_recognition: normalized-key vs original-case value
- Phone/e164: E164Trim (end = start + len(trimmed)) vs match.end()
- URL: paren-balance (end = start + len(trimmed))
- Money: either-order SYMBOL ? AMOUNT span-merge
- SIUnit: split-prefix classifier
- ISBN: hyphen/space tolerance
"""

from __future__ import annotations

from typing import Any

import pytest

from paxman.capabilities.Country.grammar.alpha2_recognition import Alpha2Grammar
from paxman.capabilities.Country.grammar.alpha3_recognition import Alpha3Grammar
from paxman.capabilities.Country.grammar.name_recognition import NameGrammar
from paxman.capabilities.Country.grammar.numeric_recognition import NumericGrammar
from paxman.capabilities.Currency.grammar.code_recognition import CodeRecognition
from paxman.capabilities.Currency.grammar.symbol_recognition import SymbolRecognition
from paxman.capabilities.Currency.grammar.word_recognition import WordRecognition
from paxman.capabilities.Date.grammar.european_recognition import EuropeanDateGrammar
from paxman.capabilities.Date.grammar.iso8601_recognition import ISO8601DateGrammar
from paxman.capabilities.Date.grammar.slash_iso_recognition import (
    SlashISODateGrammar,
)
from paxman.capabilities.Date.grammar.us_recognition import USDateGrammar
from paxman.capabilities.Email.grammar.localhost_recognition import (
    LocalhostEmailGrammar,
)
from paxman.capabilities.Email.grammar.obfuscated_recognition import (
    ObfuscatedEmailGrammar,
)
from paxman.capabilities.Email.grammar.standard_recognition import (
    StandardEmailGrammar,
)
from paxman.capabilities.IP.grammar.ipv4_recognition import IPv4Grammar
from paxman.capabilities.IP.grammar.ipv6_recognition import IPv6Grammar
from paxman.capabilities.ISBN.grammar.isbn10_recognition import (
    ISBN10RecognitionGrammar,
)
from paxman.capabilities.ISBN.grammar.isbn13_recognition import (
    ISBN13RecognitionGrammar,
)
from paxman.capabilities.Money.grammar.code_recognition import (
    CodeRecognition as MoneyCodeRecognition,
)
from paxman.capabilities.Money.grammar.symbol_recognition import (
    SymbolRecognition as MoneySymbolRecognition,
)
from paxman.capabilities.Money.grammar.word_recognition import (
    WordRecognition as MoneyWordRecognition,
)
from paxman.capabilities.Phone.grammar.e164_recognition import E164Grammar
from paxman.capabilities.Phone.grammar.international_00_recognition import (
    International00Grammar,
)
from paxman.capabilities.Phone.grammar.national_recognition import NationalGrammar
from paxman.capabilities.Phone.grammar.tel_uri_recognition import TelUriGrammar
from paxman.capabilities.SIUnit.grammar.compound_recognition import (
    CompoundRecognition as SiCompoundRecognition,
)
from paxman.capabilities.SIUnit.grammar.name_recognition import (
    NameRecognition as SiNameRecognition,
)
from paxman.capabilities.SIUnit.grammar.symbol_recognition import (
    SymbolRecognition as SiSymbolRecognition,
)
from paxman.capabilities.URL.grammar.absolute_uri_recognition import (
    AbsoluteUriRecognition,
)
from paxman.core.domain import Grammar
from tests.property._legacy_currency_grammars import (
    LegacyCodeRecognition,
    LegacySymbolRecognition,
    LegacyWordRecognition,
)
from tests.property._legacy_money_grammars import (
    LegacyCodeRecognition as LegacyMoneyCodeRecognition,
)
from tests.property._legacy_money_grammars import (
    LegacySymbolRecognition as LegacyMoneySymbolRecognition,
)
from tests.property._legacy_money_grammars import (
    LegacyWordRecognition as LegacyMoneyWordRecognition,
)
from tests.property._legacy_phone_url_grammars import (
    LegacyAbsoluteUriRecognition,
    LegacyE164Grammar,
    LegacyInternational00Grammar,
    LegacyNationalGrammar,
    LegacyTelUriGrammar,
)
from tests.property._legacy_remaining_grammars import (
    LegacyAlpha2Grammar,
    LegacyAlpha3Grammar,
    LegacyEuropeanDateGrammar,
    LegacyIPv4Grammar,
    LegacyIPv6Grammar,
    LegacyISBN10RecognitionGrammar,
    LegacyISBN13RecognitionGrammar,
    LegacyISO8601DateGrammar,
    LegacyLocalhostEmailGrammar,
    LegacyNameGrammar,
    LegacyNumericGrammar,
    LegacyObfuscatedEmailGrammar,
    LegacySlashISODateGrammar,
    LegacyStandardEmailGrammar,
    LegacyUSDateGrammar,
)
from tests.property._legacy_siunit_grammars import (
    LegacyCompoundRecognition as LegacySiCompound,
)
from tests.property._legacy_siunit_grammars import (
    LegacyNameRecognition as LegacySiName,
)
from tests.property._legacy_siunit_grammars import (
    LegacySymbolRecognition as LegacySiSymbol,
)

# Import harness helper — implemented in this task.
from tests.property.grammar_stage_parity import assert_grammar_parity

CURATED_CORPUS: list[str] = [
    "United States",  # Country name — original case preservation
    "  united states  ",  # Country name — whitespace + case fold
    "+1 555 123 4567",  # Phone e164 — normal
    "+15551234567 5551234567",  # Phone e164 — runaway trim at 15 digits
    "https://example.com/path_(with_parens)",  # URL paren-balance
    "USD500",  # Money code+amount
    "$500",  # Money bare symbol + amount (shared symbol)
    "500 EUR",  # Money amount + code (either order)
    "kilo gram",  # SIUnit split_word_prefix
    "m/s",  # SIUnit compound
    "9780306406157",  # ISBN13 bare
    "978-0-11-000222-4",  # ISBN13 hyphenated (range message)
    "2026-01-15",  # Date S1
    "user@example.com",  # Email S1
    "192.168.1.1",  # IP S1
]


@pytest.mark.property
def test_curated_corpus_parity_placeholder() -> None:
    """Placeholder — will be parametrized over (grammar, text) pairs.

    RED: assert_grammar_parity does not yet prove any migration; the harness
    itself is GREEN-skipped until Task 5+ wires the first real parity case.
    """
    # Each parametrized case will call:
    #   assert_grammar_parity(old_grammar, new_grammar, text)
    # where equality is (start, end, raw_text, notation).
    assert callable(assert_grammar_parity), (
        "harness helper must be importable for Task 5+ wiring"
    )
    pytest.skip("Harness not yet implemented — wire in Task 5+")


# Currency migration (Task 5): old bespoke recognize() vs new PipelineGrammar
# declaration. Each tuple is (legacy_grammar, new_grammar, text). The corpus
# covers qualified/bare symbols, case-folded codes, case-insensitive words,
# amount/sign-glued rejections, and inside-token rejections — every branch the
# migration must preserve byte-identically.
CURRENCY_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    # Symbol — qualified vs bare, longest/qualified-first precedence.
    (LegacySymbolRecognition(), SymbolRecognition(), "US$"),
    (LegacySymbolRecognition(), SymbolRecognition(), "€"),
    (LegacySymbolRecognition(), SymbolRecognition(), "A$"),
    (LegacySymbolRecognition(), SymbolRecognition(), "CA$"),
    (LegacySymbolRecognition(), SymbolRecognition(), "US$ is the dollar"),
    (LegacySymbolRecognition(), SymbolRecognition(), "A$ is the Australian dollar"),
    (LegacySymbolRecognition(), SymbolRecognition(), "US$5"),  # amount-glued reject
    (LegacySymbolRecognition(), SymbolRecognition(), "$500"),  # amount-glued reject
    (LegacySymbolRecognition(), SymbolRecognition(), "x€"),  # inside-token reject
    (LegacySymbolRecognition(), SymbolRecognition(), "€5"),  # amount-glued reject
    (LegacySymbolRecognition(), SymbolRecognition(), ""),  # empty
    # Code — case folding, whitespace, multi-match, glued rejections.
    (LegacyCodeRecognition(), CodeRecognition(), "USD"),
    (LegacyCodeRecognition(), CodeRecognition(), " usd "),
    (LegacyCodeRecognition(), CodeRecognition(), "GBP, EUR"),
    (LegacyCodeRecognition(), CodeRecognition(), "US$"),  # not 3 letters
    (LegacyCodeRecognition(), CodeRecognition(), "xUSD"),  # inside-token reject
    (LegacyCodeRecognition(), CodeRecognition(), "USD-500"),  # sign-glued reject
    (LegacyCodeRecognition(), CodeRecognition(), "USD500"),  # amount-glued reject
    (LegacyCodeRecognition(), CodeRecognition(), "123"),  # digits
    (LegacyCodeRecognition(), CodeRecognition(), ""),  # empty
    # Word — case-insensitive fold, multi-word, plural/amount rejections.
    (LegacyWordRecognition(), WordRecognition(), "euro"),
    (LegacyWordRecognition(), WordRecognition(), "Euro"),
    (LegacyWordRecognition(), WordRecognition(), "EURO"),
    (LegacyWordRecognition(), WordRecognition(), "US Dollar"),
    (LegacyWordRecognition(), WordRecognition(), "Euro and Dollar"),
    (LegacyWordRecognition(), WordRecognition(), "Dollars"),  # plural reject
    (LegacyWordRecognition(), WordRecognition(), "euro500"),  # amount-glued reject
    (LegacyWordRecognition(), WordRecognition(), "the"),  # non-token reject
    (LegacyWordRecognition(), WordRecognition(), ""),  # empty
]


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), CURRENCY_PARITY_CASES)
def test_currency_grammar_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Currency grammars.

    Proves the PipelineGrammar declarations emit the same spans and notations
    as the old bespoke recognize() bodies (ADR-0008 §4.1 migration gate).
    """
    assert_grammar_parity(legacy, new, text)


# Money migration (Task 6): old bespoke recognize() vs new PipelineGrammar
# declaration using AmountComposer (S4 fused either-order span-merge). Each
# tuple is (legacy_grammar, new_grammar, text). The corpus covers both
# either-order arrangements, qualified/bare symbols, case-insensitive words,
# amount/sign-glued rejections, and inside-token rejections — every branch
# the migration must preserve byte-identically.
MONEY_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    # Code — either order, glued/inside-token rejections.
    (LegacyMoneyCodeRecognition(), MoneyCodeRecognition(), "USD500"),
    (LegacyMoneyCodeRecognition(), MoneyCodeRecognition(), "USD 500"),
    (LegacyMoneyCodeRecognition(), MoneyCodeRecognition(), "500 USD"),
    (LegacyMoneyCodeRecognition(), MoneyCodeRecognition(), "100MYR"),
    (LegacyMoneyCodeRecognition(), MoneyCodeRecognition(), "USD"),  # no amount
    (LegacyMoneyCodeRecognition(), MoneyCodeRecognition(), "usd 500"),  # lowercase
    (LegacyMoneyCodeRecognition(), MoneyCodeRecognition(), "xUSD500"),  # inside
    (LegacyMoneyCodeRecognition(), MoneyCodeRecognition(), ""),  # empty
    # Symbol — qualified vs bare, either order, glued/inside rejections.
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "US$50.79"),
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "$500"),
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "RM100"),
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "€5"),
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "500 €"),
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "1.000,00 €"),
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "US$"),  # no amount
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "$"),  # no amount
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "x€"),  # inside
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), "€5"),  # glued
    (LegacyMoneySymbolRecognition(), MoneySymbolRecognition(), ""),  # empty
    # Word — case-insensitive, either order, plural/glued rejections.
    (LegacyMoneyWordRecognition(), MoneyWordRecognition(), "18 Dollar"),
    (LegacyMoneyWordRecognition(), MoneyWordRecognition(), "500 euro"),
    (LegacyMoneyWordRecognition(), MoneyWordRecognition(), "500 Ringgit"),
    (LegacyMoneyWordRecognition(), MoneyWordRecognition(), "500 Euro"),
    (LegacyMoneyWordRecognition(), MoneyWordRecognition(), "Dollars"),  # plural
    (LegacyMoneyWordRecognition(), MoneyWordRecognition(), "euro500"),  # glued
    (LegacyMoneyWordRecognition(), MoneyWordRecognition(), ""),  # empty
]


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), MONEY_PARITY_CASES)
def test_money_grammar_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Money grammars.

    Proves the AmountComposer (S4) PipelineGrammar declarations emit the same
    spans and notations as the old bespoke recognize() bodies (ADR-0008 §4.1
    migration gate).
    """
    assert_grammar_parity(legacy, new, text)


# SIUnit migration (Task 7): old bespoke recognize() vs new PipelineGrammar
# declarations (S3 lexicon + S5 split-prefix classifier + S4 compound). Each
# tuple is (legacy_grammar, new_grammar, text). The corpus covers attached
# symbols, prefix-only split symbols (rejectable spans), dual-role spaced
# units (two units, not a split), the ° degree guard, case-folded names,
# word-prefix splits, multi-word names, and compound shapes — every branch
# the migration must preserve byte-identically.
SIUNIT_SYMBOL_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacySiSymbol(), SiSymbolRecognition(), "kg"),
    (LegacySiSymbol(), SiSymbolRecognition(), "MHz"),
    (LegacySiSymbol(), SiSymbolRecognition(), "k g"),  # split_symbol_prefix
    (LegacySiSymbol(), SiSymbolRecognition(), "da m"),  # split_symbol_prefix
    (LegacySiSymbol(), SiSymbolRecognition(), "µ g"),  # split_symbol_prefix
    (LegacySiSymbol(), SiSymbolRecognition(), "m s"),  # two units, not split
    (LegacySiSymbol(), SiSymbolRecognition(), "N m"),  # two units, not split
    (LegacySiSymbol(), SiSymbolRecognition(), "m/s"),  # symbol "m" only
    (LegacySiSymbol(), SiSymbolRecognition(), "m/s²"),  # symbol "m" only
    (LegacySiSymbol(), SiSymbolRecognition(), "kg/m/s"),  # symbol "kg" only
    (LegacySiSymbol(), SiSymbolRecognition(), "m·kg"),  # symbol "m" only
    (LegacySiSymbol(), SiSymbolRecognition(), "kPa"),  # prefixed symbol
    (LegacySiSymbol(), SiSymbolRecognition(), "°C"),  # degree special name
    (LegacySiSymbol(), SiSymbolRecognition(), "25°C"),  # degree guard reject
    (LegacySiSymbol(), SiSymbolRecognition(), "xkg"),  # inside-token reject
    (LegacySiSymbol(), SiSymbolRecognition(), "kg5"),  # digit-glued reject
    (LegacySiSymbol(), SiSymbolRecognition(), "2m"),  # digit-glued reject
    (LegacySiSymbol(), SiSymbolRecognition(), "   kg   "),  # whitespace span
    (LegacySiSymbol(), SiSymbolRecognition(), "kilo gram"),  # not a symbol
    (LegacySiSymbol(), SiSymbolRecognition(), "degree celsius"),  # not a symbol
    (LegacySiSymbol(), SiSymbolRecognition(), "Pa"),
    (LegacySiSymbol(), SiSymbolRecognition(), "min"),
    (LegacySiSymbol(), SiSymbolRecognition(), "da"),  # bare prefix
    (LegacySiSymbol(), SiSymbolRecognition(), "k"),  # bare prefix
    (LegacySiSymbol(), SiSymbolRecognition(), ""),  # empty
]

SIUNIT_NAME_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacySiName(), SiNameRecognition(), "kilogram"),
    (LegacySiName(), SiNameRecognition(), "Kilogram"),  # case fold
    (LegacySiName(), SiNameRecognition(), "KILOGRAM"),  # case fold
    (LegacySiName(), SiNameRecognition(), "kelvin"),
    (LegacySiName(), SiNameRecognition(), "degree celsius"),  # name, not split
    (LegacySiName(), SiNameRecognition(), "Degree Celsius"),  # case fold
    (LegacySiName(), SiNameRecognition(), "megahertz"),
    (LegacySiName(), SiNameRecognition(), "kilometre"),
    (LegacySiName(), SiNameRecognition(), "kilo gram"),  # split_word_prefix
    (LegacySiName(), SiNameRecognition(), "kelvin pascal"),  # two names
    (LegacySiName(), SiNameRecognition(), "5kilogram"),  # digit-glued reject
    (LegacySiName(), SiNameRecognition(), "kilogram5"),  # digit-glued reject
    (LegacySiName(), SiNameRecognition(), "xkelvin"),  # inside-token reject
    (LegacySiName(), SiNameRecognition(), "kg"),  # not a name
    (LegacySiName(), SiNameRecognition(), "kilograms"),  # plural reject
    (LegacySiName(), SiNameRecognition(), ""),  # empty
]

SIUNIT_COMPOUND_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacySiCompound(), SiCompoundRecognition(), "m/s²"),
    (LegacySiCompound(), SiCompoundRecognition(), "m/s2"),
    (LegacySiCompound(), SiCompoundRecognition(), "km/h"),
    (LegacySiCompound(), SiCompoundRecognition(), "N·m"),
    (LegacySiCompound(), SiCompoundRecognition(), "N⋅m"),
    (LegacySiCompound(), SiCompoundRecognition(), "kg·m/s²"),
    (LegacySiCompound(), SiCompoundRecognition(), "g/cm³"),
    (LegacySiCompound(), SiCompoundRecognition(), "m·s⁻²"),
    (LegacySiCompound(), SiCompoundRecognition(), "m/°C"),
    (LegacySiCompound(), SiCompoundRecognition(), "µg/mL"),
    (LegacySiCompound(), SiCompoundRecognition(), "QQQ/zzz"),  # shape-only
    (LegacySiCompound(), SiCompoundRecognition(), "m/sx"),  # shape-only
    (LegacySiCompound(), SiCompoundRecognition(), "xN·m"),  # shape-only
    (LegacySiCompound(), SiCompoundRecognition(), "m"),  # single unit reject
    (LegacySiCompound(), SiCompoundRecognition(), "m s"),  # space reject
    (LegacySiCompound(), SiCompoundRecognition(), "5m/s"),  # digit-glued reject
    (LegacySiCompound(), SiCompoundRecognition(), ""),  # empty
]


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), SIUNIT_SYMBOL_PARITY_CASES)
def test_siunit_symbol_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated SIUnit symbol grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), SIUNIT_NAME_PARITY_CASES)
def test_siunit_name_parity(legacy: Grammar[Any], new: Grammar[Any], text: str) -> None:
    """Byte-identical RecognitionMatch parity for migrated SIUnit name grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), SIUNIT_COMPOUND_PARITY_CASES)
def test_siunit_compound_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated SIUnit compound grammar."""
    assert_grammar_parity(legacy, new, text)


# Phone migration (Task 8): old bespoke recognize() vs new PipelineGrammar
# declarations (S5 RegexStage + PostStage trim). Each tuple is
# (legacy_grammar, new_grammar, text). The corpus covers the E.164 15-digit
# window trim, the 00-prefix lookbehind (incl. "+00" / digit / dot rejections),
# the tel-URI scheme + extension, the NANP national 4-chain lookbehind, and
# every branch the migration must preserve byte-identically.
PHONE_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    # E.164 — normal forms + separators.
    (LegacyE164Grammar(), E164Grammar(), "+15551234567"),
    (LegacyE164Grammar(), E164Grammar(), "+1 555 123 4567"),
    (LegacyE164Grammar(), E164Grammar(), "+44-20-7946-0958"),
    (LegacyE164Grammar(), E164Grammar(), "+1.555.123.4567"),
    (LegacyE164Grammar(), E164Grammar(), "+1 (555) 123-4567"),
    # E.164 — runaway trim at the 15-digit window (end = start + len(trimmed)).
    (LegacyE164Grammar(), E164Grammar(), "+15551234567 5551234567"),
    # E.164 — oversized first run is NOT truncated (validation rejects later).
    (LegacyE164Grammar(), E164Grammar(), "+12345678901234567890"),
    # E.164 — rejections (no plus, national, word-char-before-+).
    (LegacyE164Grammar(), E164Grammar(), "15551234567"),
    (LegacyE164Grammar(), E164Grammar(), "(555) 123-4567"),
    (LegacyE164Grammar(), E164Grammar(), "user+123@example.com"),
    (LegacyE164Grammar(), E164Grammar(), "a+123"),
    (LegacyE164Grammar(), E164Grammar(), "x+11=y"),
    (LegacyE164Grammar(), E164Grammar(), "1+11=12"),
    # E.164 — in-text span + multiple + trailing period.
    (LegacyE164Grammar(), E164Grammar(), "Call +1 555 123 4567 now"),
    (LegacyE164Grammar(), E164Grammar(), "+15551234567 or +442079460958"),
    (LegacyE164Grammar(), E164Grammar(), "End of +15551234567."),
    (LegacyE164Grammar(), E164Grammar(), ""),  # empty
    # tel-URI — normal, dashes, extension, in-text, uppercase scheme.
    (LegacyTelUriGrammar(), TelUriGrammar(), "tel:+15551234567"),
    (LegacyTelUriGrammar(), TelUriGrammar(), "tel:+1-201-555-0123"),
    (LegacyTelUriGrammar(), TelUriGrammar(), "tel:+15551234567;ext=890"),
    (LegacyTelUriGrammar(), TelUriGrammar(), "Reach me at tel:+15551234567 now"),
    (LegacyTelUriGrammar(), TelUriGrammar(), "TEL:+15551234567"),
    # tel-URI — rejections (no scheme, no-plus local, scheme inside word).
    (LegacyTelUriGrammar(), TelUriGrammar(), "+15551234567"),
    (LegacyTelUriGrammar(), TelUriGrammar(), "tel:2125550123"),
    (LegacyTelUriGrammar(), TelUriGrammar(), "tel:15551234567"),
    (LegacyTelUriGrammar(), TelUriGrammar(), "tel:44 20 7946 0958"),
    (LegacyTelUriGrammar(), TelUriGrammar(), "hotel:+15551234567"),
    (LegacyTelUriGrammar(), TelUriGrammar(), "xtel:+15551234567"),
    (LegacyTelUriGrammar(), TelUriGrammar(), ""),  # empty
    # International 00 — normal, compact, in-text, trailing period.
    (LegacyInternational00Grammar(), International00Grammar(), "00 44 20 7946 0958"),
    (LegacyInternational00Grammar(), International00Grammar(), "00442079460958"),
    (
        LegacyInternational00Grammar(),
        International00Grammar(),
        "Dial 00 44 20 7946 0958 from abroad",
    ),
    (LegacyInternational00Grammar(), International00Grammar(), "00 44 20 7946 0958."),
    # International 00 — rejections (plus, single zero, digit/dot/word before).
    (LegacyInternational00Grammar(), International00Grammar(), "+442079460958"),
    (LegacyInternational00Grammar(), International00Grammar(), "0 44 20 7946 0958"),
    (LegacyInternational00Grammar(), International00Grammar(), "100442079460958"),
    (LegacyInternational00Grammar(), International00Grammar(), "+00442079460958"),
    (LegacyInternational00Grammar(), International00Grammar(), "0.00442079460958"),
    (LegacyInternational00Grammar(), International00Grammar(), "user00123@example.com"),
    (LegacyInternational00Grammar(), International00Grammar(), "x0044 20 7946 0958"),
    (LegacyInternational00Grammar(), International00Grammar(), ""),  # empty
    # National — parens, dashes, dots, spaces, trunk, in-text.
    (LegacyNationalGrammar(), NationalGrammar(), "(555) 123-4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "555-123-4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "555.123.4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "555 123 4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "1-555-123-4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "1 (555) 123-4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "Call (555) 123-4567 today"),
    # National — rejections (international in all separator shapes, tel-URI, short).
    (LegacyNationalGrammar(), NationalGrammar(), "+15551234567"),
    (LegacyNationalGrammar(), NationalGrammar(), "+1-555-123-4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "+1 555 123 4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "+1.555.123.4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "+1 (555) 123-4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "tel:+1-201-555-0123"),
    (LegacyNationalGrammar(), NationalGrammar(), "tel:+15551234567"),
    (LegacyNationalGrammar(), NationalGrammar(), "tel:+1 (555) 123-4567"),
    (LegacyNationalGrammar(), NationalGrammar(), "555-1234"),
    (LegacyNationalGrammar(), NationalGrammar(), ""),  # empty
]


# URL migration (Task 8): old bespoke recognize() vs new PipelineGrammar
# declaration (S5 RegexStage + PostStage paren-balance/D16 drop). Each tuple
# is (legacy_grammar, new_grammar, text). The corpus covers the Appendix C
# paren-balance trim, the D16 bare-scheme drop, the scheme-char left
# boundary, multi-line spans, and shape-only recognition — every branch the
# migration must preserve byte-identically.
URL_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    # Paren-balance trim + bare-scheme drop.
    (
        LegacyAbsoluteUriRecognition(),
        AbsoluteUriRecognition(),
        "https://example.com/path_(with_parens)",
    ),
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "Note:"),  # bare scheme
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "(https://example.com)"),
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "http://exa\nmple.com/"),
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "http://example.com."),
    # Left boundary: word rejection keeps "ahttps" span, digit start rejected.
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "ahttps://example.com"),
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "1https://example.com"),
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "(https://example.com"),
    # Non-ASCII body + shape-only recognition.
    (
        LegacyAbsoluteUriRecognition(),
        AbsoluteUriRecognition(),
        "mailto:user@münchen.de",
    ),
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "https://"),
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "http://99999/"),
    # All-paren body collapses to bare scheme -> dropped.
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "https:))))"),
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), "https://example.com))"),
    # Double-quote right boundary.
    (
        LegacyAbsoluteUriRecognition(),
        AbsoluteUriRecognition(),
        '"https://example.com/"',
    ),
    (LegacyAbsoluteUriRecognition(), AbsoluteUriRecognition(), ""),  # empty
]


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), PHONE_PARITY_CASES)
def test_phone_grammar_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Phone grammars."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), URL_PARITY_CASES)
def test_url_grammar_parity(legacy: Grammar[Any], new: Grammar[Any], text: str) -> None:
    """Byte-identical RecognitionMatch parity for migrated URL grammar."""
    assert_grammar_parity(legacy, new, text)


# ---------------------------------------------------------------------------
# Remaining S1+S2 grammars (Task 9): Date, Email, IP, ISBN, Country.
# Old bespoke recognize() (legacy snapshot) vs new PipelineGrammar
# declaration. Each tuple is (legacy_grammar, new_grammar, text). The corpus
# covers valid matches, rejections (inside-token, digit-glued, word-glued),
# empty, whitespace, and representative capability-test inputs — every branch
# the migration must preserve byte-identically.
# ---------------------------------------------------------------------------

DATE_ISO_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyISO8601DateGrammar(), ISO8601DateGrammar(), "2026-01-15"),
    (LegacyISO8601DateGrammar(), ISO8601DateGrammar(), "2026/01/15"),  # no match
    (
        LegacyISO8601DateGrammar(),
        ISO8601DateGrammar(),
        "12026-01-15",
    ),  # digit-glued reject
    (
        LegacyISO8601DateGrammar(),
        ISO8601DateGrammar(),
        "2026-01-261",
    ),  # digit-glued reject
    (
        LegacyISO8601DateGrammar(),
        ISO8601DateGrammar(),
        "Dates: 2026-07-26 and 2025-12-31",
    ),
    (LegacyISO8601DateGrammar(), ISO8601DateGrammar(), "x 2026-07-26 y"),
    (
        LegacyISO8601DateGrammar(),
        ISO8601DateGrammar(),
        "  2026-01-15  ",
    ),  # whitespace span
    (LegacyISO8601DateGrammar(), ISO8601DateGrammar(), ""),  # empty
    (LegacyISO8601DateGrammar(), ISO8601DateGrammar(), "No dates here"),  # no match
]

DATE_US_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyUSDateGrammar(), USDateGrammar(), "07/26/2026"),  # 4-digit year
    (LegacyUSDateGrammar(), USDateGrammar(), "07/26/26"),  # 2-digit year
    (LegacyUSDateGrammar(), USDateGrammar(), "7/26/2026"),  # single-digit month
    (LegacyUSDateGrammar(), USDateGrammar(), "1207/26/2026"),  # digit-glued reject
    (LegacyUSDateGrammar(), USDateGrammar(), "07/26/20261"),  # digit-glued reject
    (
        LegacyUSDateGrammar(),
        USDateGrammar(),
        "Dates: 07/26/2026 and 12/31/2025",
    ),  # 4-digit x2
    (
        LegacyUSDateGrammar(),
        USDateGrammar(),
        "Dates: 07/26/26 and 12/31/25",
    ),  # 2-digit x2
    (LegacyUSDateGrammar(), USDateGrammar(), "x 07/26/2026 y"),
    (LegacyUSDateGrammar(), USDateGrammar(), ""),  # empty
    (LegacyUSDateGrammar(), USDateGrammar(), "No dates here"),  # no match
]

DATE_EUROPEAN_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyEuropeanDateGrammar(), EuropeanDateGrammar(), "26/07/2026"),  # 4-digit year
    (LegacyEuropeanDateGrammar(), EuropeanDateGrammar(), "26/07/26"),  # 2-digit year
    (LegacyEuropeanDateGrammar(), EuropeanDateGrammar(), "6/7/2026"),  # single-digit
    (LegacyEuropeanDateGrammar(), EuropeanDateGrammar(), "1226/07/2026"),  # reject
    (LegacyEuropeanDateGrammar(), EuropeanDateGrammar(), "26/07/20261"),  # reject
    (
        LegacyEuropeanDateGrammar(),
        EuropeanDateGrammar(),
        "Dates: 26/07/2026 and 31/12/2025",
    ),
    (LegacyEuropeanDateGrammar(), EuropeanDateGrammar(), "x 26/07/2026 y"),
    (LegacyEuropeanDateGrammar(), EuropeanDateGrammar(), ""),  # empty
    (LegacyEuropeanDateGrammar(), EuropeanDateGrammar(), "No dates here"),  # no match
]

DATE_SLASH_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacySlashISODateGrammar(), SlashISODateGrammar(), "2026/07/26"),
    (LegacySlashISODateGrammar(), SlashISODateGrammar(), "2026/7/6"),  # single-digit
    (
        LegacySlashISODateGrammar(),
        SlashISODateGrammar(),
        "07/26/2026",
    ),  # no match (US order)
    (LegacySlashISODateGrammar(), SlashISODateGrammar(), "12026/07/26"),  # reject
    (LegacySlashISODateGrammar(), SlashISODateGrammar(), "2026/07/261"),  # reject
    (
        LegacySlashISODateGrammar(),
        SlashISODateGrammar(),
        "Dates: 2026/07/26 and 2025/12/31",
    ),
    (LegacySlashISODateGrammar(), SlashISODateGrammar(), "x 2026/07/26 y"),
    (LegacySlashISODateGrammar(), SlashISODateGrammar(), ""),  # empty
]

EMAIL_STANDARD_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (
        LegacyStandardEmailGrammar(),
        StandardEmailGrammar(),
        "Contact us at user@example.com",
    ),
    (
        LegacyStandardEmailGrammar(),
        StandardEmailGrammar(),
        "Send to first.last@domain.co.uk",
    ),
    (LegacyStandardEmailGrammar(), StandardEmailGrammar(), "user+tag@gmail.com"),
    (
        LegacyStandardEmailGrammar(),
        StandardEmailGrammar(),
        "Email a@b.com or c@d.org",
    ),  # two
    (LegacyStandardEmailGrammar(), StandardEmailGrammar(), "not an email"),  # no match
    (
        LegacyStandardEmailGrammar(),
        StandardEmailGrammar(),
        "user at example dot com",
    ),  # no match
    (LegacyStandardEmailGrammar(), StandardEmailGrammar(), ""),  # empty
]

EMAIL_OBFUSCATED_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (
        LegacyObfuscatedEmailGrammar(),
        ObfuscatedEmailGrammar(),
        "Contact user at example dot com",
    ),
    (
        LegacyObfuscatedEmailGrammar(),
        ObfuscatedEmailGrammar(),
        "Email user at gmail.com",
    ),
    (
        LegacyObfuscatedEmailGrammar(),
        ObfuscatedEmailGrammar(),
        "user@example.com",
    ),  # no match
    (
        LegacyObfuscatedEmailGrammar(),
        ObfuscatedEmailGrammar(),
        "no email here",
    ),  # no match
    (LegacyObfuscatedEmailGrammar(), ObfuscatedEmailGrammar(), ""),  # empty
]

EMAIL_LOCALHOST_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyLocalhostEmailGrammar(), LocalhostEmailGrammar(), "Send to admin@localhost"),
    (LegacyLocalhostEmailGrammar(), LocalhostEmailGrammar(), "user@localhost:8080"),
    (
        LegacyLocalhostEmailGrammar(),
        LocalhostEmailGrammar(),
        "user@example.com",
    ),  # no match
    (
        LegacyLocalhostEmailGrammar(),
        LocalhostEmailGrammar(),
        "no email here",
    ),  # no match
    (LegacyLocalhostEmailGrammar(), LocalhostEmailGrammar(), ""),  # empty
]

IPV4_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyIPv4Grammar(), IPv4Grammar(), "192.168.1.1"),
    (LegacyIPv4Grammar(), IPv4Grammar(), "10.0.0.1"),
    (LegacyIPv4Grammar(), IPv4Grammar(), "foo 192.168.1.1 bar"),
    (LegacyIPv4Grammar(), IPv4Grammar(), "192.168.1.1 and 10.0.0.1"),  # two
    (LegacyIPv4Grammar(), IPv4Grammar(), "256.1.1.1"),  # regex-valid (no range check)
    (LegacyIPv4Grammar(), IPv4Grammar(), "not an ip"),  # no match
    (LegacyIPv4Grammar(), IPv4Grammar(), ""),  # empty
]

IPV6_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (
        LegacyIPv6Grammar(),
        IPv6Grammar(),
        "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
    ),  # full
    (LegacyIPv6Grammar(), IPv6Grammar(), "2001:db8:85a3::8a2e:370:7334"),  # compressed
    (LegacyIPv6Grammar(), IPv6Grammar(), "::1"),  # loopback
    (LegacyIPv6Grammar(), IPv6Grammar(), "fe80::1"),  # link-local
    (LegacyIPv6Grammar(), IPv6Grammar(), "::"),  # all-zeros
    (LegacyIPv6Grammar(), IPv6Grammar(), "See 2001:db8::1 here"),  # in-text
    (LegacyIPv6Grammar(), IPv6Grammar(), "not ipv6"),  # no match
    (LegacyIPv6Grammar(), IPv6Grammar(), ""),  # empty
]

ISBN13_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyISBN13RecognitionGrammar(), ISBN13RecognitionGrammar(), "9780306406157"),
    (LegacyISBN13RecognitionGrammar(), ISBN13RecognitionGrammar(), "978-0-11-000222-4"),
    (
        LegacyISBN13RecognitionGrammar(),
        ISBN13RecognitionGrammar(),
        "ISBN 9780306406157",
    ),
    (
        LegacyISBN13RecognitionGrammar(),
        ISBN13RecognitionGrammar(),
        "ISBN: 978-0-11-000222-4",
    ),
    (
        LegacyISBN13RecognitionGrammar(),
        ISBN13RecognitionGrammar(),
        "foo 9780306406157 bar",
    ),
    (
        LegacyISBN13RecognitionGrammar(),
        ISBN13RecognitionGrammar(),
        "978030640615",
    ),  # 12 digits
    (
        LegacyISBN13RecognitionGrammar(),
        ISBN13RecognitionGrammar(),
        "x9780306406157",
    ),  # glued
    (LegacyISBN13RecognitionGrammar(), ISBN13RecognitionGrammar(), ""),  # empty
]

ISBN10_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyISBN10RecognitionGrammar(), ISBN10RecognitionGrammar(), "0306406152"),
    (LegacyISBN10RecognitionGrammar(), ISBN10RecognitionGrammar(), "0-306-40615-2"),
    (LegacyISBN10RecognitionGrammar(), ISBN10RecognitionGrammar(), "ISBN 0306406152"),
    (
        LegacyISBN10RecognitionGrammar(),
        ISBN10RecognitionGrammar(),
        "ISBN: 0-306-40615-2",
    ),
    (
        LegacyISBN10RecognitionGrammar(),
        ISBN10RecognitionGrammar(),
        "foo 0306406152 bar",
    ),
    (
        LegacyISBN10RecognitionGrammar(),
        ISBN10RecognitionGrammar(),
        "030640615",
    ),  # 9 digits
    (LegacyISBN10RecognitionGrammar(), ISBN10RecognitionGrammar(), ""),  # empty
]

COUNTRY_ALPHA2_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyAlpha2Grammar(), Alpha2Grammar(), "US"),
    (LegacyAlpha2Grammar(), Alpha2Grammar(), "us"),  # case fold
    (LegacyAlpha2Grammar(), Alpha2Grammar(), "GB"),
    (LegacyAlpha2Grammar(), Alpha2Grammar(), "US and GB"),  # two
    (LegacyAlpha2Grammar(), Alpha2Grammar(), "USA"),  # 3 letters, no match
    (LegacyAlpha2Grammar(), Alpha2Grammar(), "xUS"),  # inside-token reject
    (LegacyAlpha2Grammar(), Alpha2Grammar(), "  US  "),  # whitespace span
    (LegacyAlpha2Grammar(), Alpha2Grammar(), ""),  # empty
]

COUNTRY_ALPHA3_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyAlpha3Grammar(), Alpha3Grammar(), "USA"),
    (LegacyAlpha3Grammar(), Alpha3Grammar(), "usa"),  # case fold
    (LegacyAlpha3Grammar(), Alpha3Grammar(), "GBR"),
    (LegacyAlpha3Grammar(), Alpha3Grammar(), "US"),  # 2 letters, no match
    (LegacyAlpha3Grammar(), Alpha3Grammar(), "xUSA"),  # inside-token reject
    (LegacyAlpha3Grammar(), Alpha3Grammar(), ""),  # empty
]

COUNTRY_NUMERIC_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyNumericGrammar(), NumericGrammar(), "840"),
    (LegacyNumericGrammar(), NumericGrammar(), "4"),
    (LegacyNumericGrammar(), NumericGrammar(), "004"),
    (LegacyNumericGrammar(), NumericGrammar(), "840 and 124"),  # two
    (LegacyNumericGrammar(), NumericGrammar(), "1234"),  # 4 digits, no match
    (LegacyNumericGrammar(), NumericGrammar(), "US"),  # letters, no match
    (LegacyNumericGrammar(), NumericGrammar(), ""),  # empty
]

COUNTRY_NAME_PARITY_CASES: list[tuple[Grammar[Any], Grammar[Any], str]] = [
    (LegacyNameGrammar(), NameGrammar(), "United States"),  # original case preserved
    (LegacyNameGrammar(), NameGrammar(), "  united states  "),  # whitespace + case fold
    (LegacyNameGrammar(), NameGrammar(), "USA"),  # not a name
    (LegacyNameGrammar(), NameGrammar(), "Alemania"),  # localized name
    (LegacyNameGrammar(), NameGrammar(), "Burma"),  # historical name
    (LegacyNameGrammar(), NameGrammar(), "840"),  # numeric, not name
    (LegacyNameGrammar(), NameGrammar(), "XYZ"),  # unknown name
    (LegacyNameGrammar(), NameGrammar(), ""),  # empty
]


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), DATE_ISO_PARITY_CASES)
def test_date_iso8601_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Date ISO-8601 grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), DATE_US_PARITY_CASES)
def test_date_us_parity(legacy: Grammar[Any], new: Grammar[Any], text: str) -> None:
    """Byte-identical RecognitionMatch parity for migrated Date US grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), DATE_EUROPEAN_PARITY_CASES)
def test_date_european_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Date European grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), DATE_SLASH_PARITY_CASES)
def test_date_slash_iso_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Date slash-ISO grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), EMAIL_STANDARD_PARITY_CASES)
def test_email_standard_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Email standard grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), EMAIL_OBFUSCATED_PARITY_CASES)
def test_email_obfuscated_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Email obfuscated grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), EMAIL_LOCALHOST_PARITY_CASES)
def test_email_localhost_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Email localhost grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), IPV4_PARITY_CASES)
def test_ipv4_parity(legacy: Grammar[Any], new: Grammar[Any], text: str) -> None:
    """Byte-identical RecognitionMatch parity for migrated IPv4 grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), IPV6_PARITY_CASES)
def test_ipv6_parity(legacy: Grammar[Any], new: Grammar[Any], text: str) -> None:
    """Byte-identical RecognitionMatch parity for migrated IPv6 grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), ISBN13_PARITY_CASES)
def test_isbn13_parity(legacy: Grammar[Any], new: Grammar[Any], text: str) -> None:
    """Byte-identical RecognitionMatch parity for migrated ISBN-13 grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), ISBN10_PARITY_CASES)
def test_isbn10_parity(legacy: Grammar[Any], new: Grammar[Any], text: str) -> None:
    """Byte-identical RecognitionMatch parity for migrated ISBN-10 grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), COUNTRY_ALPHA2_PARITY_CASES)
def test_country_alpha2_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Country alpha-2 grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), COUNTRY_ALPHA3_PARITY_CASES)
def test_country_alpha3_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Country alpha-3 grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), COUNTRY_NUMERIC_PARITY_CASES)
def test_country_numeric_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Country numeric grammar."""
    assert_grammar_parity(legacy, new, text)


@pytest.mark.property
@pytest.mark.parametrize(("legacy", "new", "text"), COUNTRY_NAME_PARITY_CASES)
def test_country_name_parity(
    legacy: Grammar[Any], new: Grammar[Any], text: str
) -> None:
    """Byte-identical RecognitionMatch parity for migrated Country name grammar."""
    assert_grammar_parity(legacy, new, text)


# NOTE: US/European date grammars merged two separate ``finditer`` loops
# (4-digit then 2-digit year) into a single ``(\\d{4}|\\d{2})`` alternation.
# Legacy ``recognize()`` returned matches grouped by year length
# (all 4-digit first, then 2-digit), while the staged pipeline returns
# document order. The engine sorts by ``start`` before dedup, so
# end-to-end ``canonicalize()`` is identical; direct ``recognize()`` order
# is now document-order. This test locks the new contract and proves the
# sorted multiset is still parity-equivalent.


def test_us_date_document_order() -> None:
    """Staged US grammar emits document order; legacy grouped by year length."""
    text = "01/02/26 foo 01/02/2026"
    legacy = LegacyUSDateGrammar()
    new = USDateGrammar()
    legacy_matches = legacy.recognize(text)
    new_matches = new.recognize(text)
    # Staged is document order
    assert [m.raw_text for m in new_matches] == ["01/02/26", "01/02/2026"]
    # Legacy is grouped (4-digit first)
    assert [m.raw_text for m in legacy_matches] == ["01/02/2026", "01/02/26"]
    # Sorted by start they are equivalent
    assert sorted(new_matches, key=lambda m: m.start) == sorted(
        legacy_matches, key=lambda m: m.start
    )


def test_european_date_document_order() -> None:
    """Staged European grammar emits document order; legacy grouped."""
    text = "26/07/26 foo 26/07/2026"
    legacy = LegacyEuropeanDateGrammar()
    new = EuropeanDateGrammar()
    legacy_matches = legacy.recognize(text)
    new_matches = new.recognize(text)
    assert [m.raw_text for m in new_matches] == ["26/07/26", "26/07/2026"]
    assert [m.raw_text for m in legacy_matches] == ["26/07/2026", "26/07/26"]
    assert sorted(new_matches, key=lambda m: m.start) == sorted(
        legacy_matches, key=lambda m: m.start
    )
