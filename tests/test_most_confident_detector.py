from brf2ebrf.common_selectors import most_confident_detector
from brf2ebrf.parser import DetectionResult


def test_select_most_confident_detector():
    detectors = [lambda text, cursor, state, output_text: DetectionResult(output_text + "d", cursor + 4, state, 0.2), lambda text, cursor, state, output_text: DetectionResult(output_text + "a", cursor + 1, state, 0.9), lambda text, cursor, state, output_text: DetectionResult(output_text + "b", cursor + 2, state, 0.6), lambda text, cursor, state, output_text: DetectionResult(output_text + "c", cursor + 3, state, 0.3)]
    assert most_confident_detector("TEST BRF", 0, "Default", "", detectors) == DetectionResult("a", 1, "Default", 0.9)