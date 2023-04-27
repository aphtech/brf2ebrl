import pytest
from brf2ebrf.common_detectors import convert_ascii_to_unicode_braille
from brf2ebrf.parser import DetectionResult


@pytest.mark.parametrize("text,cursor,expected_text", [
    ("TEST", 0, "\u281e\u2811\u280e\u281e"),
    ("TEST", 1, "\u2811\u280e\u281e"),
    ("TEST", 2, "\u280e\u281e"),
    ("TEST\nTEST\fTEST", 0, "\u281e\u2811\u280e\u281e\n\u281e\u2811\u280e\u281e\f\u281e\u2811\u280e\u281e")
])
def test_convert_ascii_to_unicode_braille(text: str, cursor: int, expected_text: str):
    assert convert_ascii_to_unicode_braille(text, cursor, "Default") == DetectionResult(expected_text, len(text), "Default",
                                                                                   1.0)
