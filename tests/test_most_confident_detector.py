from brf2ebrf.common.selectors import most_confident_detector
from brf2ebrf.parser import DetectionResult


def test_select_most_confident_detector():
    detectors = [lambda text, cursor, state, output_text: DetectionResult(cursor + 4, state, 0.2, output_text + "d"), lambda text, cursor, state, output_text: DetectionResult(cursor + 1, state, 0.9, output_text + "a"), lambda text, cursor, state, output_text: DetectionResult(cursor + 2, state, 0.6, output_text + "b"), lambda text, cursor, state, output_text: DetectionResult(cursor + 3, state, 0.3, output_text + "c")]
    assert most_confident_detector("TEST BRF", 0, "Default", "", detectors) == DetectionResult(1, "Default", 0.9, "a")