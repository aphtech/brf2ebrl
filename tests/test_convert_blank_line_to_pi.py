from brf2ebrf.common.detectors import convert_blank_line_to_pi
from brf2ebrf.parser import DetectionResult


def test_convert_blank_line_to_pi():
    brf = "TE/ TEXT\n\n"
    expected_brf = "TE/ TEXT<?blank-line?>"
    actual = convert_blank_line_to_pi(brf, 8, "", "TE/ TEXT")
    expected = DetectionResult(9, "", 1.0, expected_brf)
    assert actual == expected
