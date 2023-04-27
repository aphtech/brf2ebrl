from collections.abc import Iterable

from brf2ebrf.parser import Detector, DetectionResult


def most_confident_detector(text: str, cursor: int, state: str, detectors: Iterable[Detector]) -> DetectionResult:
    return max([x(text, cursor, state) for x in detectors], key=lambda d: d.confidence)