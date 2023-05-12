"""Some common selectors for brf2ebrf."""
from collections.abc import Iterable

from brf2ebrf.parser import Detector, DetectionResult


def most_confident_detector(text: str, cursor: int, state: str, output_text: str,
                            detectors: Iterable[Detector]) -> DetectionResult:
    """Selects the deector reporting the highest confidence level."""
    return max(map(lambda x: x(text, cursor, state, output_text), detectors), key=lambda d: d.confidence)
