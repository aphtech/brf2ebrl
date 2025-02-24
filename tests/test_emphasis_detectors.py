#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import pytest

from brf2ebrl.common.emphasis_detectors import tag_emphasis


@pytest.mark.parametrize("text,expected_text", [
    # Simple phrase tests
    ("\u2818\u2836\u2801\u2803\u2809\u2800\u2801\u2803\u2809\u2800\u2801\u2803\u2809\u2800\u2801\u2803\u2809\u2819\u2818\u2804", '<strong>⠘⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠘⠄</strong>'),
    ('⠘⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠘⠄⠀⠁⠃⠉', '<strong>⠘⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠘⠄</strong>⠀⠁⠃⠉'),
    ('⠘⠶⠐⠼⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠐⠼⠄⠘⠄⠀⠁⠃⠉', '<strong>⠘⠶<em class="trans4">⠐⠼⠶⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠀⠁⠃⠉⠙⠐⠼⠄</em>⠘⠄</strong>⠀⠁⠃⠉'),
    # Simple word tests
    ("⠨⠂⠁⠃⠉⠀", '<em>⠨⠂⠁⠃⠉</em>⠀'),
    ('⠐⠼⠂⠁⠃⠉⠀⠁⠃⠉⠀⠐⠼⠂⠸⠂⠁⠃⠉⠀⠁⠃⠉⠙⠀⠁⠃⠉', '<em class="trans4">⠐⠼⠂⠁⠃⠉</em>⠀⠁⠃⠉⠀<em class="trans4">⠐⠼⠂<em class="underline">⠸⠂⠁⠃⠉</em></em>⠀⠁⠃⠉⠙⠀⠁⠃⠉'),
    ('⠨⠂⠁⠃⠉⠨⠄⠄⠀⠁', '<em>⠨⠂⠁⠃⠉⠨⠄</em>⠄⠀⠁'),
    #simple letter tests
    ("⠘⠆⠁⠃⠉", '<strong>⠘⠆⠁</strong>⠃⠉'),
    ('⠘⠆⠠⠘⠺⠀', '<strong>⠘⠆⠠⠘⠺</strong>⠀'),
    ('⠈⠆⠨⠆⠁⠃⠸⠆⠉', '<em>⠨⠆<em class="script">⠈⠆⠁</em></em>⠃<em class="underline">⠸⠆⠉</em>'),
    # Misc examples from books
    ("<h2>⠠⠩⠕⠑⠀⠠⠁⠀⠊⠎⠀⠁⠃⠀⠼⠃⠀⠔⠡⠑⠎⠀⠇⠰⠛⠲⠀⠠⠩⠕⠑⠀⠰⠠⠃⠀⠊⠎⠀⠁⠃⠀⠼⠙⠀⠔⠡⠑⠎⠀⠇⠰⠛⠲⠀⠠⠩⠕⠑⠀⠠⠁⠀⠊⠎⠀⠼⠃⠀⠔⠡⠑⠎⠀⠈⠼⠂⠘⠂⠩⠕⠗⠞⠻⠀⠘⠂⠇⠰⠛⠻</h2>", "<h2>⠠⠩⠕⠑⠀⠠⠁⠀⠊⠎⠀⠁⠃⠀⠼⠃⠀⠔⠡⠑⠎⠀⠇⠰⠛⠲⠀⠠⠩⠕⠑⠀⠰⠠⠃⠀⠊⠎⠀⠁⠃⠀⠼⠙⠀⠔⠡⠑⠎⠀⠇⠰⠛⠲⠀⠠⠩⠕⠑⠀⠠⠁⠀⠊⠎⠀⠼⠃⠀⠔⠡⠑⠎⠀<em class=\"trans1\">⠈⠼⠂<strong>⠘⠂⠩⠕⠗⠞⠻</strong></em>⠀<strong>⠘⠂⠇⠰⠛⠻</strong></h2>"),
    ("<li>⠼⠁⠚⠒⠼⠁⠚⠀⠁⠲⠍⠲⠀⠠⠓⠑⠀⠌⠕⠏⠎⠀⠏⠇⠁⠽⠬⠀⠁⠞⠀⠼⠁⠚⠒⠼⠑⠚⠀⠁⠲⠍⠲⠀⠠⠓⠪⠀⠇⠰⠛⠀⠙⠕⠑⠎⠀⠠⠁⠇⠑⠭⠀⠏⠇⠁⠽⠀⠃⠁⠎⠅⠑⠞⠃⠁⠇⠇⠦⠀⠘⠂⠠⠙⠗⠁⠺⠀<span class=\"tn\">⠈⠨⠣⠠⠮⠀⠋⠕⠇⠇⠪⠬⠀⠝⠥⠍⠃⠻⠀⠇⠔⠑⠀⠊⠎⠀⠗⠑⠏⠗⠕⠙⠥⠉⠫⠀⠔⠀⠞⠺⠕⠀⠐⠏⠎⠲⠈⠨⠜</span>⠀⠸⠩</li>", "<li>⠼⠁⠚⠒⠼⠁⠚⠀⠁⠲⠍⠲⠀⠠⠓⠑⠀⠌⠕⠏⠎⠀⠏⠇⠁⠽⠬⠀⠁⠞⠀⠼⠁⠚⠒⠼⠑⠚⠀⠁⠲⠍⠲⠀⠠⠓⠪⠀⠇⠰⠛⠀⠙⠕⠑⠎⠀⠠⠁⠇⠑⠭⠀⠏⠇⠁⠽⠀⠃⠁⠎⠅⠑⠞⠃⠁⠇⠇⠦⠀<strong>⠘⠂⠠⠙⠗⠁⠺</strong>⠀<span class=\"tn\">⠈⠨⠣⠠⠮⠀⠋⠕⠇⠇⠪⠬⠀⠝⠥⠍⠃⠻⠀⠇⠔⠑⠀⠊⠎⠀⠗⠑⠏⠗⠕⠙⠥⠉⠫⠀⠔⠀⠞⠺⠕⠀⠐⠏⠎⠲⠈⠨⠜</span>⠀⠸⠩</li>"),
    ("<p>⠞⠕⠀⠨⠶⠒⠞⠗⠊⠃⠥⠞⠑⠲⠀⠠⠮⠀⠃⠁⠎⠑⠃⠁⠇⠇⠀⠉⠇⠥⠃⠀⠝⠑⠫⠫⠀⠍⠐⠕⠽⠀⠿⠀⠑⠟⠥⠊⠏⠰⠞⠂⠀⠎⠀⠮⠽⠀⠁⠎⠅⠫⠀⠍⠑⠀⠞⠕⠀⠘⠂⠒⠞⠗⠊⠃⠥⠞⠑⠲⠨⠄</p>", "<p>⠞⠕⠀<em>⠨⠶⠒⠞⠗⠊⠃⠥⠞⠑⠲⠀⠠⠮⠀⠃⠁⠎⠑⠃⠁⠇⠇⠀⠉⠇⠥⠃⠀⠝⠑⠫⠫⠀⠍⠐⠕⠽⠀⠿⠀⠑⠟⠥⠊⠏⠰⠞⠂⠀⠎⠀⠮⠽⠀⠁⠎⠅⠫⠀⠍⠑⠀⠞⠕⠀<strong>⠘⠂⠒⠞⠗⠊⠃⠥⠞⠑⠲⠨⠄</strong></em></p>"),
    ("<h2>⠸⠩⠀⠼⠢⠬⠢⠀⠨⠅⠀⠼⠂⠴⠀⠸⠱⠀⠼⠑⠀⠙⠳⠃⠇⠫⠀⠊⠎⠀⠼⠁⠚⠲⠀⠼⠑⠀⠙⠳⠃⠇⠫⠀⠊⠎⠀⠘⠂⠈⠼⠂⠑⠧⠢⠀⠀⠘⠂⠝⠀⠘⠂⠑⠧⠢⠲</h2>", "<h2>⠸⠩⠀⠼⠢⠬⠢⠀⠨⠅⠀⠼⠂⠴⠀⠸⠱⠀⠼⠑⠀⠙⠳⠃⠇⠫⠀⠊⠎⠀⠼⠁⠚⠲⠀⠼⠑⠀⠙⠳⠃⠇⠫⠀⠊⠎⠀<strong>⠘⠂<em class=\"trans1\">⠈⠼⠂⠑⠧⠢</em></strong>⠀⠀<strong>⠘⠂⠝</strong>⠀<strong>⠘⠂⠑⠧⠢⠲</strong></h2>"),
])
def test_detect_emphasis(text, expected_text):
    actual = tag_emphasis(text)
    assert actual == expected_text
