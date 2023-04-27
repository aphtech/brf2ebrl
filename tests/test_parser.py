from collections.abc import Iterable

import pytest
from brf2ebrf.parser import parse, ParserPass, Detector, DetectionResult


def _remove_detector(_: str, cursor: int, state: str) -> DetectionResult:
    return DetectionResult("", cursor + 1, state, 1.0)


@pytest.mark.parametrize("input_text,initial_state,detectors,expected_text", [
    ("TEST BRF", "Default", [lambda text, cursor, state: DetectionResult(text[cursor], cursor + 1, state, 1.0)], "TEST BRF"),
    ("TEST BRF", "Default", [lambda text, cursor, state: DetectionResult(text[cursor] * 2, cursor + 1, state, 1.0)], "TTEESSTT  BBRRFF")
])
def test_single_pass_parser(input_text: str, initial_state, detectors: Iterable[Detector], expected_text: str):
    assert parse(input_text, [ParserPass(initial_state, detectors, lambda text, cursor, state, dets: next(iter(dets), _remove_detector)(text, cursor, state))]) == expected_text
