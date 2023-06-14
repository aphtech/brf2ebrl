from brf2ebrf.bana import create_braille_page_detector
from brf2ebrf.common import PageNumberPosition, PageLayout
from brf2ebrf.parser import DetectionResult


def test_find_first_page():
    page_detector = create_braille_page_detector(page_layout=PageLayout(), separator="\u2800" * 3)
    brf = "\u281e\u2811\u280c\u2800\u2803\u2817\u280b\n\u2811\u282d\u281e\u2817\u2801\u2800\u281e\u2811\u282d\u281e\f"
    actual = page_detector(brf, 0, {"StartBraillePage": True}, "")
    expected_brf = "\ue000{\"BraillePage\": {}}\ue001" + brf.rstrip("\f")
    expected = DetectionResult(len(brf) - 1, {"StartBraillePage": False}, 1.0, expected_brf)
    assert actual == expected


def test_assume_all_is_page_when_no_form_feed():
    brf = "\u281e\u2811\u280c\u2800\u2803\u2817\u280b\n\u2811\u282d\u281e\u2817\u2801\u2800\u281e\u2811\u282d\u281e"
    expected = DetectionResult(text="\ue000{\"BraillePage\": {}}\ue001" + brf, cursor=len(brf),
                               state={"StartBraillePage": False}, confidence=1.0)
    actual = create_braille_page_detector(page_layout=PageLayout(), separator="\u2800" * 3)(brf, 0,
                                                                                            {"StartBraillePage": True},
                                                                                            "")
    assert actual == expected


def test_when_state_does_not_apply():
    expected = None
    brf = "\u281e\u2811\u280c\u2800\u2803\u2817\u280b\n\u2811\u282d\u281e\u2817\u2801\u2800\u281e\u2811\u282d\u281e\f"
    actual = create_braille_page_detector(page_layout=PageLayout(), separator="\u2800" * 3)(brf, 0,
                                                                                            {"OtherState": True}, "")
    assert actual == expected


def test_consume_formfeed_in_any_state():
    brf = "\u281e\u2811\u280c\u2800\u281e\u2811\u282d\u281e\f"
    expected = DetectionResult(9, state={"StartBraillePage": True}, confidence=1.0, text=brf)
    actual = create_braille_page_detector(page_layout=PageLayout(), separator="\u2800" * 3)(
        brf, 8, {},
        "\u281e\u2811\u280c\u2800\u281e\u2811\u282d\u281e")
    assert actual == expected


def test_detect_braille_page_number():
    brf = "\n".join(["TE/ TEXT"] * 25)
    expected_brf = "\ue000{\"BraillePage\": {\"Number\": \"#A\"}}\ue001" + brf
    brf += (" " * 30) + "#A"
    expected = DetectionResult(len(brf), {"StartBraillePage": False}, 1.0, expected_brf)
    actual = create_braille_page_detector(page_layout=PageLayout(braille_page_number=PageNumberPosition.BOTTOM_RIGHT))(
        brf, 0, {"StartBraillePage": True}, "")
    assert actual == expected
