from brf2ebrl.common import PageLayout, PageNumberPosition
from brf2ebrl.common.detectors import _ASCII_TO_UNICODE_DICT
from brf2ebrl.common.graphic_detectors import (
    _find_matching_ppn_in_positioned_words,
    find_matching_ppn_in_blocks,
)


class _FakePdfPage:
    def __init__(self, words, width=600.0, height=800.0):
        self._words = words
        self.width = width
        self.height = height

    def extract_words(self):
        return self._words


def _to_unicode_braille(ascii_ppn: str) -> str:
    return ascii_ppn.upper().translate(_ASCII_TO_UNICODE_DICT)


def test_positioned_matching_prefers_header_right_for_top_right_layout():
    expected = _to_unicode_braille("#B")
    other = _to_unicode_braille("#A")

    page = _FakePdfPage(
        [
            {"text": "#b", "x0": 545.0, "x1": 575.0, "top": 16.0, "bottom": 24.0},
            {"text": "#a", "x0": 290.0, "x1": 320.0, "top": 325.0, "bottom": 334.0},
        ]
    )
    layout = PageLayout(
        cells_per_line=40,
        lines_per_page=25,
        odd_print_page_number=PageNumberPosition.TOP_RIGHT,
        even_print_page_number=PageNumberPosition.TOP_RIGHT,
    )

    match = _find_matching_ppn_in_positioned_words(page, [other, expected], layout, page_count=1)

    assert match == expected


def test_positioned_matching_rejects_left_candidate_for_top_right_layout():
    only_candidate = _to_unicode_braille("#C")

    page = _FakePdfPage(
        [
            {"text": "#c", "x0": 35.0, "x1": 60.0, "top": 18.0, "bottom": 26.0},
        ]
    )
    layout = PageLayout(
        cells_per_line=40,
        lines_per_page=25,
        odd_print_page_number=PageNumberPosition.TOP_RIGHT,
        even_print_page_number=PageNumberPosition.TOP_RIGHT,
    )

    match = _find_matching_ppn_in_positioned_words(page, [only_candidate], layout, page_count=1)

    assert match is None


def test_text_block_matching_still_matches_known_ppn():
    expected = _to_unicode_braille("#H")
    blocks = ["Figure 2", "see #h for details"]

    match = find_matching_ppn_in_blocks(blocks, [expected])

    assert match == expected
