import pytest
from brf2ebrf.common.page_numbers import _find_end_of_element


@pytest.mark.parametrize("text, start,expected", [
    ("", 0, 0),
    ("text", 0, 0),
    ("text", 1, 1),
("<h1></h1>", 2, -1),
    ("<h1>", 0, -1),
    ("<h1></h1>", 0, 9),
    ("<h1></h1> text", 0, 9),
    ("<h1>some</h1> text", 0, 13),
    ("<p>text</p>", 0, 11),
    ("<h1><p>text</p> more text", 4, 15),
    ("<p>text</p><h1>", 0, 11),
    ("<h1><b>text</b></h1>", 0, 20),
("<h1><b>text</b></h1>", 4, 15),
    ("<p>text</P>", 0, -1),
    ("<p>text</P></p>", 0, -1),
    ("<p><br/></p>", 0, 12),
    ("<p/>", 0, 4)
])
def test_find_end_of_element(text: str, start:int, expected: int):
    assert _find_end_of_element(text, start) == expected
