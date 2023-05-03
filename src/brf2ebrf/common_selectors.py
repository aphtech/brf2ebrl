from collections.abc import Iterable

from brf2ebrf.parser import Detector, DetectionResult


def most_confident_detector(text: str, cursor: int, state: str, output_text: str, detectors: Iterable[Detector]) -> DetectionResult:
    return max([x(text, cursor, state, output_text) for x in detectors], key=lambda d: d.confidence)