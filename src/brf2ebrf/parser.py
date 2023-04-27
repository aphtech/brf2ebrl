from collections.abc import Iterable, Sequence, Callable
from dataclasses import dataclass

@dataclass(frozen=True)
class DetectionResult:
    text: str
    cursor: int
    state: str
    confidence: float


Detector = Callable[[str, int, str], DetectionResult]
DetectionSelector = Callable[[str, int, str, Sequence[Detector]], DetectionResult]


@dataclass(frozen=True)
class ParserPass:
    initial_state: str
    detectors: Sequence[Detector]
    selector: DetectionSelector


def parse(brf: str, parser_passes: Iterable[ParserPass]) -> str:
    text = brf
    for parser_pass in parser_passes:
        cursor, state, selector = 0, parser_pass.initial_state, parser_pass.selector
        text_builder = ""
        while cursor < len(text):
            result = selector(text, cursor, state, parser_pass.detectors)
            text_builder, cursor, state = text_builder + result.text, result.cursor, result.state
        text = text_builder
    return text
