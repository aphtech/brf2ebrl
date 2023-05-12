"""Main parser framework for the brf2ebrf system."""
from collections.abc import Iterable, Callable
from dataclasses import dataclass, field
from functools import cached_property


@dataclass(frozen=True)
class DetectionResult:
    """A detection result for the current parser position."""

    cursor: int
    state: str
    confidence: float
    text: str


@dataclass(frozen=True)
class LazyDetectionResult(DetectionResult):
    """A detection result which can generate the output text when actually required."""
    text_func: Callable[[], str] = field(compare=False)

    def _create_text(self) -> str:
        return self.text_func()

    text: str = field(init=False, default=cached_property(_create_text))


Detector = Callable[[str, int, str, str], DetectionResult]
DetectionSelector = Callable[[str, int, str, str, Iterable[Detector]], DetectionResult]


@dataclass(frozen=True)
class ParserPass:
    """A configuration for a single step in a multipass parsing."""
    initial_state: str
    detectors: Iterable[Detector]
    selector: DetectionSelector


def parse(brf: str, parser_passes: Iterable[ParserPass]) -> str:
    """Perform a parse of the BRF according to the steps in the parser configuration."""
    text = brf
    for parser_pass in parser_passes:
        text_builder, cursor, state, selector = "", 0, parser_pass.initial_state, parser_pass.selector
        while cursor < len(text):
            result = selector(text, cursor, state, text_builder, parser_pass.detectors)
            text_builder, cursor, state = result.text, result.cursor, result.state
        text = text_builder
    return text
