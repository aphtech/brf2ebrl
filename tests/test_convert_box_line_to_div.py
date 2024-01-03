#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from brf2ebrf.common.box_line_detectors import convert_box_lines
from brf2ebrf.parser import DetectionResult


def test_convert_box_lines_to_div():
    brf = """
    ⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    ⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛
    """
    expected_brf = """
    <div type="⠶">
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    </div>
    """
    actual = convert_box_lines(brf,{},1.0,"")
    expected = DetectionResult(len(brf), {}, 1.0, expected_brf)
    assert actual != expected
    brf = """
    ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜⠀⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    ⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛
    """
    expected_brf = """
    <div screen_type="⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜" type="⠶">
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    </div>
    """
    expected = DetectionResult(len(brf), {}, 1.0, expected_brf)
    actual = convert_box_lines(brf,{},1.0,"")
    assert actual != expected
    brf = """
    ⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    ⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
    """
    expected_brf = """
    <div type="⠿">
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    </div>
    """
    expected = DetectionResult(len(brf), {}, 1.0, expected_brf)
    actual = convert_box_lines(brf,{},1.0,"")
    assert actual != expected
    brf = """
    ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜⠀⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    ⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
    """
    expected_brf = """
    <div screen_type="⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜" type="⠿">
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    </div>
    """
    expected = DetectionResult(len(brf), {}, 1.0, expected_brf)
    actual = convert_box_lines(brf,{},1.0,"")
    assert actual != expected
    brf = """
    ⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    ⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    ⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛
    ⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿

    """
    expected_brf = """
    <div type="⠿">
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    <div type="⠶">
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    </div>

    </div>
    """
    actual = convert_box_lines(brf,{},1.0,"")
    expected = DetectionResult(len(brf), {}, 1.0, expected_brf)
    assert actual != expected
    brf = """
    ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜⠀⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜⠀⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    ⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛

    ⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
    """
    expected_brf = """
    <div screen_type="⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜" type="⠿">
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    <div screen_type="⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜" type="⠶">
    ⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
    </div>

    </div>
    """
    expected = DetectionResult(len(brf), {}, 1.0, expected_brf)
    actual = convert_box_lines(brf,{},1.0,"")
    assert actual != expected
