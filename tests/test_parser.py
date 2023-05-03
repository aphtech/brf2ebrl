from collections.abc import Iterable

import pytest
from brf2ebrf.parser import parse, ParserPass, Detector, DetectionResult, DetectionSelector


def _remove_detector(_: str, cursor: int, state: str, output_text: str) -> DetectionResult:
    return DetectionResult(output_text, cursor + 1, state, 1.0)


def _first_detector_selector(text: str, cursor: int, state: str, output_text: str, detectors: Iterable[Detector]) -> DetectionResult:
    return next(iter(detectors), _remove_detector)(text, cursor, state, output_text)


@pytest.mark.parametrize("input_text,initial_state,detectors,selector,expected_text", [
    ("TEST BRF", "Default", [lambda text, cursor, state, output_text: DetectionResult(output_text + text[cursor], cursor + 1, state, 1.0)], _first_detector_selector, "TEST BRF"),
    ("TEST BRF", "Default", [lambda text, cursor, state, output_text: DetectionResult(output_text + text[cursor] * 2, cursor + 1, state, 1.0)], _first_detector_selector, "TTEESSTT  BBRRFF")
])
def test_single_pass_parser(input_text: str, initial_state, detectors: Iterable[Detector], selector: DetectionSelector, expected_text: str):
    assert parse(input_text, [ParserPass(initial_state, detectors, selector)]) == expected_text
