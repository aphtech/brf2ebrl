import pytest
from brf2ebrf.common import PageNumberPosition


@pytest.mark.parametrize("position,top,left,bottom,right", [(PageNumberPosition.NONE, False, False, False, False), (PageNumberPosition.TOP_LEFT, True, True, False, False), (PageNumberPosition.TOP_RIGHT, True, False, False, True), (PageNumberPosition.BOTTOM_LEFT, False, True, True, False), (PageNumberPosition.BOTTOM_RIGHT, False, False, True, True)])
def test_top_left(position, top, left, bottom, right):
    assert position.is_top() == top
    assert position.is_left() == left
    assert position.is_bottom() == bottom
    assert position.is_right() == right