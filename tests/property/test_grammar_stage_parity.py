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

from paxman.capabilities.Currency.grammar.code_recognition import CodeRecognition
from paxman.capabilities.Currency.grammar.symbol_recognition import SymbolRecognition
from paxman.capabilities.Currency.grammar.word_recognition import WordRecognition
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
