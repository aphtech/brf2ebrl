import pytest
from brf2ebrf.common_detectors import convert_ascii_to_unicode_braille_bulk, convert_ascii_to_unicode_braille
from brf2ebrf.common_selectors import most_confident_detector
from brf2ebrf.parser import DetectionResult, parse, ParserPass


@pytest.mark.parametrize("text,cursor,expected_text", [
    ("TEST", 0, "\u281e\u2811\u280e\u281e"),
    ("TEST", 1, "\u2811\u280e\u281e"),
    ("TEST", 2, "\u280e\u281e"),
    ("TEST\nTEST\fTEST", 0, "\u281e\u2811\u280e\u281e\n\u281e\u2811\u280e\u281e\f\u281e\u2811\u280e\u281e"),
    ("\"S TEXT", 0, "\u2810\u280e\u2800\u281e\u2811\u282d\u281e"),
    (r""" A1B'K2L@CIF/MSP"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\0Z7(_?W]#Y)=""", 0, "".join([chr(x) for x in range(0x2800, 0x2840)]))
])
def test_convert_ascii_to_unicode_braille_bulk(text: str, cursor: int, expected_text: str):
    assert convert_ascii_to_unicode_braille_bulk(text, cursor, "Default", "") == DetectionResult(expected_text, len(text), "Default",
                                                                                             1.0)


@pytest.mark.parametrize("text,cursor,expected_text", [
    ("TEST", 0, "\u281e"),
    ("TEST", 1, "\u2811"),
    ("TEST TEST", 4, "\u2800"),
    ("TEST\nTEST", 4, "\n")
])
def test_convert_ascii_to_unicode_braille(text: str, cursor: int, expected_text: str):
    assert convert_ascii_to_unicode_braille(text, cursor, "Default", "") == DetectionResult(expected_text, cursor + 1, "Default", 1.0)



@pytest.mark.parametrize("text", [
    "SOME TEXT",
    "( M TEXT 9 ! TEST",
    "BRL DOCU;T",
    "TEST\nDOCU;mT\f"
])
def test_conversion_by_character_vs_bulk(text: str):
    assert parse(text, [ParserPass("Default", [convert_ascii_to_unicode_braille_bulk], most_confident_detector)]) == parse(text, [ParserPass("Default", [convert_ascii_to_unicode_braille], most_confident_detector)])