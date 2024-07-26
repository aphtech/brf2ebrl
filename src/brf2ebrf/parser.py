#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Main parser framework for the brf2ebrf system."""
import logging
from collections.abc import Iterable, Callable, Mapping
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any


@dataclass(frozen=True)
class Parser:
    name: str
    parse: Callable[[str, Callable[[], None]], str]


DetectionState = Mapping[str, Any]


@dataclass(frozen=True)
class DetectionResult:
    """A detection result for the current parser position."""

    cursor: int
    state: DetectionState
    confidence: float
    text: str


@dataclass(frozen=True)
class LazyDetectionResult(DetectionResult):
    """A detection result which can generate the output text when actually required."""
    text_func: Callable[[], str] = field(compare=False)

    def _create_text(self) -> str:
        return self.text_func()

    text: str = field(init=False, default=cached_property(_create_text))


@dataclass(frozen=True)
class NamedDetectionResult(DetectionResult):
    """Give a name and description to a DetectionResult"""
    detection_result: DetectionResult
    name: str
    description: str = ""

    def _get_cursor(self) -> int:
        return self.detection_result.cursor

    def _get_state(self) -> DetectionState:
        return self.detection_result.state

    def _get_confidence(self) -> float:
        return self.detection_result.confidence

    def _get_text(self) -> str:
        return self.detection_result.text

    cursor: int = field(init=False, default_factory=_get_cursor)
    state: DetectionState = field(init=False, default_factory=_get_state)
    confidence: float = field(init=False, default_factory=_get_confidence)
    text: str = field(init=False, default_factory=_get_text)


Detector = Callable[[str, int, DetectionState, str], DetectionResult | None]
DetectionSelector = Callable[[str, int, DetectionState, str, Iterable[Detector]], DetectionResult]


def detector_parser(name: str, initial_state: DetectionState, detectors: Iterable[Detector], selector: DetectionSelector) -> Parser:
    """A configuration for a single step in a multipass parsing."""

    def run_detectors(text: str, check_cancelled: Callable[[], None]) -> str:
        text_builder, cursor, state = "", 0, initial_state
        while cursor < len(text):
            check_cancelled()
            result = selector(text, cursor, state, text_builder, detectors)
            assert cursor != result.cursor or state != result.state, f"Input conditions not changed by detector, cursor={cursor}, state={state}, selected detector={result}"
            text_builder, cursor, state = result.text, result.cursor, result.state
        return text_builder
    return Parser(name=name, parse=run_detectors)


class ParsingCancelledException(Exception):
    pass


def parse(brf: str, parser_passes: Iterable[Parser], progress_callback: Callable[[int], None] = lambda x: None,
          is_cancelled: Callable[[], bool] = lambda: False) -> str:
    """Perform a parse of the BRF according to the steps in the parser configuration."""

    def check_cancelled():
        if is_cancelled():
            logging.warning("Parsing cancelled.")
            raise ParsingCancelledException()

    logging.info("Starting parsing")
    text = brf
    for i, parser_pass in enumerate(parser_passes):
        check_cancelled()
        progress_callback(i)
        logging.info(f"Processing pass {parser_pass.name}")
        text = parser_pass.parse(text, check_cancelled)
    logging.info(f"Finished parsing")
    return text
