from collections.abc import Iterable

import pytest
from brf2ebrf.parser import parse, ParserPass, Detector, DetectionResult, DetectionSelector


def _remove_detector(_: str, cursor: int, state: str) -> DetectionResult:
    return DetectionResult("", cursor + 1, state, 1.0)


def _first_detector_selector(text: str, cursor: int, state: str, detectors: Iterable[Detector]) -> DetectionResult:
    return next(iter(detectors), _remove_detector)(text, cursor, state)


@pytest.mark.parametrize("input_text,initial_state,detectors,selector,expected_text", [
    ("TEST BRF", "Default", [lambda text, cursor, state: DetectionResult(text[cursor], cursor + 1, state, 1.0)], _first_detector_selector, "TEST BRF"),
    ("TEST BRF", "Default", [lambda text, cursor, state: DetectionResult(text[cursor] * 2, cursor + 1, state, 1.0)], _first_detector_selector, "TTEESSTT  BBRRFF")
])
def test_single_pass_parser(input_text: str, initial_state, detectors: Iterable[Detector], selector: DetectionSelector, expected_text: str):
    assert parse(input_text, [ParserPass(initial_state, detectors, selector)]) == expected_text
