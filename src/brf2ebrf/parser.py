from collections.abc import Iterable, Callable
from dataclasses import dataclass

@dataclass(frozen=True)
class DetectionResult:
    text: str
    cursor: int
    state: str
    confidence: float


Detector = Callable[[str, int, str], DetectionResult]
DetectionSelector = Callable[[Iterable[Detector]], Detector]


@dataclass(frozen=True)
class ParserPass:
    initial_state: str
    detectors: Iterable[Detector]
    selector: DetectionSelector


def parse(brf: str, parser_passes: Iterable[ParserPass]) -> str:
    return brf