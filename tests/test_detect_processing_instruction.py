from brf2ebrf.common.detectors import detect_and_pass_processing_instructions
from brf2ebrf.parser import DetectionResult


def test_insert_processing_instruction_in_output():
    brf = "TE/ TEXT<?brlpage #A?>EXTRA TEXT"
    expected_brf = "TE/ TEXT<?brlpage #A?>"
    actual = detect_and_pass_processing_instructions(brf, 8, {}, "TE/ TEXT")
    expected = DetectionResult(len(expected_brf), {}, 0.9, expected_brf)
    assert actual == expected
