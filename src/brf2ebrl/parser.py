#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Main parser framework for the brf2ebrl system."""
import enum
import logging
from collections.abc import Iterable, Callable, Mapping
from dataclasses import dataclass, field
from enum import IntEnum
from functools import cached_property
from typing import Any


class EBrailleParserOptions(enum.StrEnum):
    page_layout = "page_layout"
    images_path = "images_path"
    detect_running_heads = "detect_running_heads"
    metadata_entries = "metadata_entries"


class NotifyLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    CRITICAL = 50


@dataclass(frozen=True)
class ParserContext:
    is_cancelled: Callable[[], bool] = field(default=lambda: False)
    notify: Callable[[NotifyLevel, Callable[[], str]], None] = field(default=lambda l,t: None)
    options: dict[str, Any] = field(default_factory=dict)
    def check_cancelled(self):
        if self.is_cancelled():
            raise ParsingCancelledException()
    def notify_str(self, level: NotifyLevel, msg: str):
        self.notify(level, lambda: msg)


@dataclass(frozen=True)
class Parser:
    name: str
    parse: Callable[[str, ParserContext], str]


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

    def run_detectors(text: str, parser_context: ParserContext) -> str:
        text_builder, cursor, state = "", 0, initial_state
        while cursor < len(text):
            parser_context.check_cancelled()
            result = selector(text, cursor, state, text_builder, detectors)
            assert cursor != result.cursor or state != result.state, f"Input conditions not changed by detector, cursor={cursor}, state={state}, selected detector={result}"
            text_builder, cursor, state = result.text, result.cursor, result.state
        return text_builder
    return Parser(name=name, parse=run_detectors)


class ParsingCancelledException(Exception):
    pass

class ParserException(Exception):
    def __init__(self, text: str):
        self.text = text
        self.file_name = None

def parse(brf: str, parser_passes: Iterable[Parser], progress_callback: Callable[[int], None] = lambda x: None,
          parser_context: ParserContext = ParserContext()) -> str:
    """Perform a parse of the BRF according to the steps in the parser configuration."""
    logging.info("Starting parsing")
    text = brf
    for i, parser_pass in enumerate(parser_passes):
        parser_context.check_cancelled()
        progress_callback(i)
        logging.info(f"Processing pass {parser_pass.name}")
        try:
            text = parser_pass.parse(text, parser_context)
        except ParsingCancelledException as e:
            raise e
        except Exception as e:
            raise ParserException(text=text) from e
    logging.info(f"Finished parsing")
    return text
