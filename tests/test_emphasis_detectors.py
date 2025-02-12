#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from brf2ebrl.common.emphasis_detectors import tag_emphasis


def test_convert_phrase_emphasis():
    #simple phrase tests
    brf = "\u2818\u2836\u2801\u2803\u2809\u2800\u2801\u2803\u2809\u2800\u2801\u2803\u2809\u2800\u2801\u2803\u2809\u2819\u2818\u2804"
    expected_brf = '<strong>⠘⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠘⠄</strong>'
    actual = tag_emphasis(brf)
    expected = expected_brf
    assert actual == expected
    brf = '⠘⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠘⠄⠀⠁⠃⠉'
    expected_brf = '<strong>⠘⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠘⠄</strong>⠀⠁⠃⠉'
    actual = tag_emphasis(brf)
    expected = expected_brf
    assert actual == expected
    brf = '⠘⠶⠐⠼⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠐⠼⠄⠘⠄⠀⠁⠃⠉'
    expected_brf = '<strong>⠘⠶<em class="trans4">⠐⠼⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠐⠼⠄</em>⠘⠄</strong>⠀⠁⠃⠉'
    actual = tag_emphasis(brf)
    expected = expected_brf
    assert actual == expected
        
def test_convert_word_emphasis():
    #simple wordtests
    brf = "⠨⠂⠁⠃⠉⠀"
    expected_brf = '<em>⠨⠂⠁⠃⠉</em>⠀'
    actual = tag_emphasis(brf)
    expected = expected_brf
    assert actual == expected
    brf = '⠐⠼⠂⠁⠃⠉⠀⠁⠃⠉⠀⠐⠼⠂⠸⠂⠁⠃⠉⠀⠁⠃⠉⠙⠀⠁⠃⠉'
    expected_brf = '<em class="trans4">⠐⠼⠂⠁⠃⠉</em>⠀⠁⠃⠉⠀<em class="trans4">⠐⠼⠂<em class="underline">⠸⠂⠁⠃⠉</em></em>⠀⠁⠃⠉⠙⠀⠁⠃⠉'
    actual = tag_emphasis(brf)
    expected = expected_brf
    assert actual == expected
    brf = '⠨⠂⠁⠃⠉⠨⠄⠄⠀⠁'
    expected_brf = '<em>⠨⠂⠁⠃⠉⠨⠄</em>⠄⠀⠁'
    actual = tag_emphasis(brf)
    expected = expected_brf
    assert actual == expected
                
def test_convert_letter_emphasis():
    #simple letter tests
    brf = "⠘⠆⠁⠃⠉"
    expected_brf = '<strong>⠘⠆⠁</strong>⠃⠉'
    actual = tag_emphasis(brf)
    expected = expected_brf
    assert actual == expected
    brf = '⠘⠆⠠⠘⠺⠀'
    expected_brf = '<strong>⠘⠆⠠⠘⠺</strong>⠀'
    actual = tag_emphasis(brf)
    expected = expected_brf
    assert actual == expected
    brf = '⠈⠆⠨⠆⠁⠃⠸⠆⠉'
    expected_brf = '<em>⠨⠆<em class="script">⠈⠆⠁</em></em>⠃<em class="underline">⠸⠆⠉</em>'
    actual = tag_emphasis(brf)
    expected = expected_brf
    assert actual == expected

def test_nested_emphasis():
    brf = "<h2>⠠⠩⠕⠑⠀⠠⠁⠀⠊⠎⠀⠁⠃⠀⠼⠃⠀⠔⠡⠑⠎⠀⠇⠰⠛⠲⠀⠠⠩⠕⠑⠀⠰⠠⠃⠀⠊⠎⠀⠁⠃⠀⠼⠙⠀⠔⠡⠑⠎⠀⠇⠰⠛⠲⠀⠠⠩⠕⠑⠀⠠⠁⠀⠊⠎⠀⠼⠃⠀⠔⠡⠑⠎⠀⠈⠼⠂⠘⠂⠩⠕⠗⠞⠻⠀⠘⠂⠇⠰⠛⠻</h2>"
    actual = tag_emphasis(brf)
    expected = "<h2>⠠⠩⠕⠑⠀⠠⠁⠀⠊⠎⠀⠁⠃⠀⠼⠃⠀⠔⠡⠑⠎⠀⠇⠰⠛⠲⠀⠠⠩⠕⠑⠀⠰⠠⠃⠀⠊⠎⠀⠁⠃⠀⠼⠙⠀⠔⠡⠑⠎⠀⠇⠰⠛⠲⠀⠠⠩⠕⠑⠀⠠⠁⠀⠊⠎⠀⠼⠃⠀⠔⠡⠑⠎⠀<em class=\"trans1\">⠈⠼⠂<strong>⠘⠂⠩⠕⠗⠞⠻</strong></em>⠀<strong>⠘⠂⠇⠰⠛⠻</strong></h2>"
    assert actual == expected
