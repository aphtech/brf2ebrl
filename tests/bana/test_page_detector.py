import math

from brf2ebrf.bana import PageDetector
from brf2ebrf.parser import DetectionResult


def test_find_first_page():
    page_detector = PageDetector()
    brf = "TE/ BRF\nEXTRA TEXT\f"
    actual = page_detector(brf, 0, "StartBraillePage")
    expected_brf = "\ue000{\"BraillePage\": {}}\ue001" + brf.rstrip("\f")
    assert actual.text == expected_brf
    assert actual.cursor == len(brf)
    assert actual.state == "StartBraillePage"
    assert math.isclose(actual.confidence, 1.0)

def test_assume_all_is_page_when_no_form_feed():
    brf ="TE/ TEXT\nEXTRA TEXT"
    expected = DetectionResult(text="\ue000{\"BraillePage\": {}}\ue001" + brf, cursor=len(brf), state="StartBraillePage", confidence=1.0)
    actual = PageDetector()(brf, 0, "StartBraillePage")
    assert actual == expected
