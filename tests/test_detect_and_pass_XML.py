from brf2ebrf.common.detectors import detect_and_pass_XML
from brf2ebrf.parser import DetectionResult

def test_detect_and_pass_XML():

    brf = "TE/ TEXT<p/>"
    expected_brf = "TE/ TEXT<p/>"
    actual = detect_and_pass_XML(brf, 8, "","TE/ TEXT")
    expected = DetectionResult(12, "", 0.9, expected_brf)
    assert actual == expected

    brf = "<p/> EXTRA TEXT"
    expected_brf = "<p/>"
    actual = detect_and_pass_XML(brf, 0, "","")
    expected = DetectionResult(4, "", 0.9, expected_brf)
    assert actual == expected

    brf = "TE/ TEXT<p/> EXTRA TEXT"
    expected_brf = "TE/ TEXT<p/>"
    actual = detect_and_pass_XML(brf, 8, "","TE/ TEXT")
    expected = DetectionResult(12, "", 0.9, expected_brf)
    assert actual == expected

    brf = "TE/ TEXT<p>TEXT</p>"
    expected_brf = "TE/ TEXT<p>TEXT</p>"
    actual = detect_and_pass_XML(brf, 8, "","TE/ TEXT")
    expected = DetectionResult(19, "", 0.9, expected_brf)
    assert actual == expected

    brf = "<p>TEXT</p>"
    expected_brf = "<p>TEXT</p>"
    actual = detect_and_pass_XML(brf, 0, "","")
    expected = DetectionResult(11, "", 0.9, expected_brf)
    assert actual == expected
    
    
    brf = "TE/ TEXT<p>TEXT</p> Extra Text"
    expected_brf = "TE/ TEXT<p>TEXT</p>"
    actual = detect_and_pass_XML(brf, 8, "","TE/ TEXT")
    expected = DetectionResult(19, "", 0.9, expected_brf)
    assert actual == expected
    

    brf = "TE/ TEXT<p><b>TEXT</b></p>"
    expected_brf = "TE/ TEXT<p><b>TEXT</b></p>"
    actual = detect_and_pass_XML(brf, 8, "","TE/ TEXT")
    expected = DetectionResult(26, "", 0.9, expected_brf)
    assert actual == expected

    brf = "TE/ TEXT<p><b><br/>TEXT</b></p>"
    expected_brf = "TE/ TEXT<p><b><br/>TEXT</b></p>"
    actual = detect_and_pass_XML(brf, 8, "","TE/ TEXT")
    expected = DetectionResult(31, "", 0.9, expected_brf)
    assert actual == expected

    brf = "<p><b><br/>TEXT</b></p>"
    expected_brf = "<p><b><br/>TEXT</b></p>"
    actual = detect_and_pass_XML(brf, 0, "","")
    expected = DetectionResult(23, "", 0.9, expected_brf)
    assert actual == expected


    brf = "TE/ TEXT<p><b><br/>TEXT</b></p> EXTRA TEXT"
    expected_brf = "TE/ TEXT<p><b><br/>TEXT</b></p>"
    actual = detect_and_pass_XML(brf, 8, "","TE/ TEXT")
    expected = DetectionResult(31, "", 0.9, expected_brf)
    assert actual == expected

    brf = "<p><b><br/>TEXT</b></p> EXTRA TEXT <br/>"
    expected_brf = "<p><b><br/>TEXT</b></p>"
    actual = detect_and_pass_XML(brf, 0, "","")
    expected = DetectionResult(23, "", 0.9, expected_brf)
    assert actual == expected


