"""Main parser framework for the brf2ebrf system."""
import logging
from collections.abc import Iterable, Callable, Mapping
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

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


Detector = Callable[[str, int, DetectionState, str], DetectionResult | None]
DetectionSelector = Callable[[str, int, DetectionState, str, Iterable[Detector]], DetectionResult]


@dataclass(frozen=True)
class ParserPass:
    """A configuration for a single step in a multipass parsing."""
    name: str
    initial_state: DetectionState
    detectors: Iterable[Detector]
    selector: DetectionSelector


def parse(brf: str, parser_passes: Iterable[ParserPass]) -> str:
    """Perform a parse of the BRF according to the steps in the parser configuration."""
    logging.info("Starting parsing")
    text = brf
    for parser_pass in parser_passes:
        logging.info(f"Processing pass {parser_pass.name}")
        text_builder, cursor, state, selector = "", 0, parser_pass.initial_state, parser_pass.selector
        while cursor < len(text):
            result = selector(text, cursor, state, text_builder, parser_pass.detectors)
            assert cursor != result.cursor or state != result.state, f"Input conditions not changed by detector, cursor={cursor}, state={state}, selected detector={result}"
            text_builder, cursor, state = result.text, result.cursor, result.state
        text = text_builder
    logging.info(f"Finished parsing")
    return text
