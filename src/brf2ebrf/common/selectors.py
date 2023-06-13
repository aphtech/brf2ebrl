"""Some common selectors for brf2ebrf."""
from collections.abc import Iterable

from brf2ebrf.parser import Detector, DetectionResult, DetectionState


def most_confident_detector(text: str, cursor: int, state: DetectionState, output_text: str,
                            detectors: Iterable[Detector]) -> DetectionResult:
    """Selects the detector reporting the highest confidence level."""
    return max(filter(lambda x: x is not None, map(lambda x: x(text, cursor, state, output_text), detectors)), key=lambda d: d.confidence, default=DetectionResult(cursor + 1, state, 0.0, output_text + text[cursor]))
