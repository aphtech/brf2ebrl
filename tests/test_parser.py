import pytest
from brf2ebrf.parser import parse, ParserPass, Detector, DetectionResult


@pytest.mark.parametrize("input_text,detector,expected_text", [
    ("TEST BRF", lambda text, cursor, state: DetectionResult(text[cursor], cursor + 1, state, 1.0), "TEST BRF"),
    ("TEST BRF", lambda text, cursor, state: DetectionResult(text[cursor] * 2, cursor + 1, state, 1.0), "TTEESSTT  BBRRFF")
])
def test_parser(input_text: str, detector: Detector, expected_text: str):
    assert parse(input_text, [ParserPass("Default", [detector], lambda text, cursor, state, detectors: detectors[0](text, cursor, state))]) == expected_text
