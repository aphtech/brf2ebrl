#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest

from brf2ebrl import ParserContext
from brf2ebrl.common.detectors import convert_ascii_to_unicode_braille, \
    translate_ascii_to_unicode_braille
from brf2ebrl.common.selectors import most_confident_detector
from brf2ebrl.parser import DetectionResult, parse, detector_parser, Parser


@pytest.mark.parametrize("text,expected_text", [
    ("TEST", "\u281e\u2811\u280e\u281e"),
    ("TEST\nTEST\fTEST", "\u281e\u2811\u280e\u281e\n\u281e\u2811\u280e\u281e\f\u281e\u2811\u280e\u281e"),
    ("\"S TEXT", "\u2810\u280e\u2800\u281e\u2811\u282d\u281e"),
    (r""" A1B'K2L@CIF/MSP"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\0Z7(_?W]#Y)=""", "".join([chr(x) for x in range(0x2800, 0x2840)]))
])
def test_translate_ascii_to_unicode_braille(text: str, expected_text: str):
    assert translate_ascii_to_unicode_braille(text, ParserContext()) == expected_text


@pytest.mark.parametrize("text,cursor,expected_text", [
    ("TEST", 0, "\u281e"),
    ("TEST", 1, "\u2811"),
    ("TEST TEST", 4, "\u2800"),
    ("TEST\nTEST", 4, "\n")
])
def test_convert_ascii_to_unicode_braille(text: str, cursor: int, expected_text: str):
    assert convert_ascii_to_unicode_braille(text, cursor, {}, "") == DetectionResult(cursor + 1, {}, 1.0, expected_text)



@pytest.mark.parametrize("text", [
    "SOME TEXT",
    "( M TEXT 9 ! TEST",
    "BRL DOCU;T",
    "TEST\nDOCU;mT\f"
])
def test_conversion_by_character_vs_bulk(text: str):
    assert parse(text, [Parser("Test conversion bulk", translate_ascii_to_unicode_braille)]) == parse(text, [detector_parser("Test convert by character", {}, [convert_ascii_to_unicode_braille], most_confident_detector)])