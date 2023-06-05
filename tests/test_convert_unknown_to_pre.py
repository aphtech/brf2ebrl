from brf2ebrf.common.detectors import convert_unknown_to_pre
from brf2ebrf.parser import DetectionResult

def test_convert_unknown_to_pre():
    brf = "TE/ TEXT\n"
    expected_brf = "<pre>TE/ TEXT</pre>\n"
    actual = convert_unknown_to_pre(brf, 0, "","")
    expected = DetectionResult(9, "", 0.4, expected_brf)
    assert actual == expected

    brf = "TE/ TEXT"
    expected_brf = "<pre>TE/ TEXT</pre>"
    actual = convert_unknown_to_pre(brf, 0, "", "")
    expected = DetectionResult(8, "", 0.4, expected_brf)
    assert actual == expected

    brf = "TE/ TEXT<?blank-line?>EXTRA TEXT"
    expected_brf = "<pre>TE/ TEXT</pre><?blank-line?>"
    actual = convert_unknown_to_pre(brf, 0, "", "")
    expected = DetectionResult(22, "", 0.4, expected_brf)
    assert actual == expected

    brf = "TE/ TEXT<p>ALREADY MARKED</p>EXTRA TEXT"
    expected_brf = "<pre>TE/ TEXT</pre><p>ALREADY MARKED</p>"
    actual = convert_unknown_to_pre(brf, 0, "", "")
    expected = DetectionResult(29, "", 0.4, expected_brf)
    assert actual == expected
