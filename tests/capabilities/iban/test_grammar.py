import pytest

from paxman.capabilities.IBAN.grammar.iban_recognition import IBANRecognitionGrammar

pytestmark = [pytest.mark.capability]

GRAMMAR = IBANRecognitionGrammar()


def test_valid_electronic():
    m = GRAMMAR.recognize("DE89370400440532013000")
    assert len(m) == 1
    n = m[0].notation
    assert n.compact == "DE89370400440532013000"
    assert n.country_code == "DE" and n.check_digits == "89"
    assert m[0].raw_text == "DE89370400440532013000"
    assert m[0].end - m[0].start == len(m[0].raw_text)


def test_paper_groups_of_four():
    m = GRAMMAR.recognize("DE89 3704 0044 0532 0130 00")
    assert m[0].notation.compact == "DE89370400440532013000"


def test_case_insensitive_and_label():
    for txt in [
        "de89370400440532013000",
        "IBAN: DE89 3704 0044 0532 0130 00",
        "iban:gb29nwbk60161331926819",
        "IBAN - FR14 2004 1010 0505 0001 3M02 606",
        "IBAN DE89370400440532013000",
    ]:
        assert len(GRAMMAR.recognize(txt)) == 1


def test_lowercase_label_and_compact():
    m = GRAMMAR.recognize("iban: gb29 nwbk 6016 1331 9268 19")
    assert m[0].notation.compact == "GB29NWBK60161331926819"


def test_word_guard_blocks_left_and_label_glue():
    assert GRAMMAR.recognize("XDE89370400440532013000") == []
    assert GRAMMAR.recognize("IBANDE89370400440532013000") == []


def test_alnum_tail_absorbed_documented():
    m = GRAMMAR.recognize("DE89370400440532013000Y")
    assert len(m) == 1
    assert m[0].notation.compact == "DE89370400440532013000Y"


def test_min_and_max_length_bounds():
    assert GRAMMAR.recognize("NO938601111794") == []
    assert len(GRAMMAR.recognize("NO93 8601 1117 947")) == 1
    assert GRAMMAR.recognize("DE89" + "A" * 31) == []


def test_multi_whitespace_rejected_narrow_tolerance():
    assert GRAMMAR.recognize("DE89  3704 0044 0532 0130 00") == []
    assert GRAMMAR.recognize("DE89\t3704 0044") == []


def test_multiple_matches():
    txt = "DE89 3704 0044 0532 0130 00 / GB29 NWBK 6016 1331 9268 19"
    assert len(GRAMMAR.recognize(txt)) == 2


def test_semantics_and_name():
    assert GRAMMAR.name == "iban_recognition"
    assert GRAMMAR.semantics == "iban_recognition"
    assert GRAMMAR.single_value is True


def test_span_invariants():
    txt = "Pay to DE89 3704 0044 0532 0130 00 now"
    m = GRAMMAR.recognize(txt)[0]
    assert txt[m.start : m.end] == m.raw_text
