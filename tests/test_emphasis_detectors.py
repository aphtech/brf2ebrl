#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from brf2ebrf.common.emphasis_detectors import convert_emphasis
from brf2ebrf.parser import DetectionResult


def test_convert_phrase_emphasis():
    #simple phrase tests
    brf = "\u2818\u2836\u2801\u2803\u2809\u2800\u2801\u2803\u2809\u2800\u2801\u2803\u2809\u2800\u2801\u2803\u2809\u2819\u2818\u2804"
    expected_brf = '<strong>⠘⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠘⠄</strong>'
    actual = convert_emphasis(brf,0,{},"")
    expected = DetectionResult(len(brf ), {}, 1.0, expected_brf)
    assert actual == expected
    brf = '⠘⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠘⠄⠀⠁⠃⠉'
    expected_brf = '<strong>⠘⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠘⠄</strong>⠀⠁⠃⠉'
    actual = convert_emphasis(brf,0,{},"")
    expected = DetectionResult(len(brf ), {}, 1.0, expected_brf)
    assert actual == expected
    brf = '⠘⠶⠐⠼⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠐⠼⠄⠘⠄⠀⠁⠃⠉'
    expected_brf = '<strong>⠘⠶<em class="trans4">⠐⠼⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠐⠼⠄</em>⠘⠄</strong>⠀⠁⠃⠉'
    actual = convert_emphasis(brf,0,{},"")
    expected = DetectionResult(len(brf ), {}, 1.0, expected_brf)
    assert actual == expected
        
def test_convert_word_emphasis():
    #simple wordtests
    brf = "⠨⠂⠁⠃⠉⠀"
    expected_brf = '<em>⠨⠂⠁⠃⠉</em>⠀'
    actual = convert_emphasis(brf,0,{},"")
    expected = DetectionResult(len(brf), {}, 1.0, expected_brf)
    assert actual == expected
    brf = '⠐⠼⠂⠁⠃⠉⠀⠁⠃⠉⠀⠐⠼⠂⠸⠂⠁⠃⠉⠀⠁⠃⠉⠙⠀⠁⠃⠉'
    expected_brf = '<em class="trans4">⠐⠼⠂⠁⠃⠉</em>⠀⠁⠃⠉⠀<em class="trans4">⠐⠼⠂<em class="underline">⠸⠂⠁⠃⠉</em></em>⠀⠁⠃⠉⠙⠀⠁⠃⠉'
    actual = convert_emphasis(brf,0,{},"")
    expected = DetectionResult(len(brf ), {}, 1.0, expected_brf)
    assert actual == expected
    brf = '⠨⠂⠁⠃⠉⠨⠄⠄⠀⠁'
    expected_brf = '<em>⠨⠂⠁⠃⠉⠨⠄</em>⠄⠀⠁'
    actual = convert_emphasis(brf,0,{},"")
    expected = DetectionResult(len(brf ), {}, 1.0, expected_brf)
    assert actual == expected
                
def test_convert_letter_emphasis():
    #simple letter tests
    brf = "⠘⠆⠁⠃⠉"
    expected_brf = '<strong>⠘⠆⠁</strong>⠃⠉'
    actual = convert_emphasis(brf,0,{},"")
    expected = DetectionResult(len(brf ), {}, 1.0, expected_brf)
    assert actual == expected
    brf = '⠘⠆⠠⠘⠺⠀'
    expected_brf = '<strong>⠘⠆⠠⠘⠺</strong>⠀'
    actual = convert_emphasis(brf,0,{},"")
    expected = DetectionResult(len(brf ), {}, 1.0, expected_brf)
    assert actual == expected
    brf = '⠈⠆⠨⠆⠁⠃⠸⠆⠉'
    expected_brf = '<em>⠨⠆<em class="script">⠈⠆⠁</em></em>⠃<em class="underline">⠸⠆⠉</em>'
    actual = convert_emphasis(brf,0,{},"")
    expected = DetectionResult(len(brf ), {}, 1.0, expected_brf)
    assert actual == expected
                                