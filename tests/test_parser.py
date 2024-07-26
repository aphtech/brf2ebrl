#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Iterable

import pytest
from brf2ebrf.parser import parse, detector_parser, Detector, DetectionResult, DetectionSelector, DetectionState


def _remove_detector(_: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    return DetectionResult(cursor + 1, state, 1.0, output_text)


def _first_detector_selector(text: str, cursor: int, state: DetectionState, output_text: str, detectors: Iterable[Detector]) -> DetectionResult:
    return next(iter(detectors), _remove_detector)(text, cursor, state, output_text)


@pytest.mark.parametrize("input_text,initial_state,detectors,selector,expected_text", [
    ("TEST BRF", {}, [lambda text, cursor, state, output_text: DetectionResult(cursor + 1, state, 1.0, output_text + text[cursor])], _first_detector_selector, "TEST BRF"),
    ("TEST BRF", {}, [lambda text, cursor, state, output_text: DetectionResult(cursor + 1, state, 1.0, output_text + text[cursor] * 2)], _first_detector_selector, "TTEESSTT  BBRRFF")
])
def test_single_pass_parser(input_text: str, initial_state: DetectionState, detectors: Iterable[Detector], selector: DetectionSelector, expected_text: str):
    assert parse(input_text, [detector_parser("Test single pass", initial_state, detectors, selector)]) == expected_text
