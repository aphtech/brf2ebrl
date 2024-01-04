#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from brf2ebrf.common.box_line_detectors import convert_box_lines, remove_box_lines_processing_instructions
from brf2ebrf.parser import DetectionResult


def test_convert_g_box():
    brf = """
⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛

"""
    expected_brf = '''
<div type="<?box ⠶?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
</div>

'''
    actual = convert_box_lines(brf,0,{},"")
    expected = DetectionResult(len(brf ), {},1.0, expected_brf)
    assert actual == expected

def test_convert_g_color_box():
    brf = """
⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜⠀⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛

"""
    expected_brf = '''
<div screen_type="<?box ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜?>" type="<?box ⠶?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
</div>

'''
    actual = convert_box_lines(brf,0,{},"")
    expected = DetectionResult(len(brf ), {},1.0, expected_brf)
    assert actual == expected



def test_convert_enclosing_color_box():
    brf = """
⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿

"""
    expected_brf = '''
<div type="<?box ⠿?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
</div>

'''
    actual = convert_box_lines(brf,0,{},"")
    expected = DetectionResult(len(brf ), {},1.0, expected_brf)
    assert actual == expected


def test_convert_enclosing_color_box():
    brf = """
⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜⠀⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿

"""
    expected_brf = '''
<div screen_type="<?box ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜?>" type="<?box ⠿?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
</div>

'''
    actual = convert_box_lines(brf,0,{},"")
    expected = DetectionResult(len(brf ), {},1.0, expected_brf)
    assert actual == expected



def test_convert_enclosing_and_g_color_box():
    brf = """
⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛

⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿

"""
    expected_brf = '''
<div type="<?box ⠿?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
<div type="<?box ⠶?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
</div>

</div>

'''
    actual = convert_box_lines(brf,0,{},"")
    expected = DetectionResult(len(brf ), {},1.0, expected_brf)
    assert actual == expected


def test_convert_enclosing_and_g_color_box():
    brf = """
⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜⠀⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜⠀⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛

⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿

"""
    expected_brf = '''
<div screen_type="<?box ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜?>" type="<?box ⠿?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
<div screen_type="<?box ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜?>" type="<?box ⠶?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
</div>

</div>

'''
    actual = convert_box_lines(brf,0,{},"")
    expected = DetectionResult(len(brf ), {},1.0, expected_brf)
    assert actual == expected

def test_remove_box_processing_instructions():
    brf = '''
<div screen_type="<?box ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜?>" type="<?box ⠿?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
<div screen_type="<?box ⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜?>" type="<?box ⠶?>">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
</div>

</div>

'''
    expected_brf = '''
<div screen_type="⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜" type="⠿">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
<div screen_type="⠈⠨⠣⠃⠇⠥⠑⠈⠨⠜" type="⠶">
⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀
</div>

</div>

'''
    actual = remove_box_lines_processing_instructions(brf,0,{},"")
    expected = DetectionResult(len(brf ), {},1.0, expected_brf)
    assert actual == expected