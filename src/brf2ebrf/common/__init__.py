from dataclasses import dataclass
from enum import Enum


class PageNumberPosition(Enum):
    """The position of a page number on the page."""

    NONE = 0
    TOP_LEFT = 2
    TOP_RIGHT = 3
    BOTTOM_LEFT = 4
    BOTTOM_RIGHT = 5

    def is_top(self) -> bool:
        """Is the page number at the top of the page."""
        return self.value.bit_length() == 2

    def is_left(self) -> bool:
        """Is the page number at the left of the page."""
        return self.value.bit_count() == 1

    def is_bottom(self) -> bool:
        """Is the page number at the bottom of the page."""
        return self.value.bit_length() == 3

    def is_right(self) -> bool:
        """Is the page number at the right of the page."""
        return self.value.bit_count() == 2


@dataclass(frozen=True)
class PageLayout:
    cells_per_line: int = 40
    lines_per_page: int = 25
    braille_page_number: PageNumberPosition = PageNumberPosition.NONE
