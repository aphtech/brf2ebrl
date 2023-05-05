import json
from enum import Enum

from brf2ebrf.parser import DetectionResult


class PageNumberPosition(Enum):
    NONE = 0
    TOP_LEFT = 2
    TOP_RIGHT = 3
    BOTTOM_LEFT = 4
    BOTTOM_RIGHT = 5

    def is_top(self) -> bool:
        return self.value.bit_length() == 2

    def is_left(self) -> bool:
        return self.value.bit_count() == 1

    def is_bottom(self) -> bool:
        return self.value.bit_length() == 3

    def is_right(self) -> bool:
        return self.value.bit_count() == 2


class BraillePageDetector:
    def __init__(self, number_position: PageNumberPosition = PageNumberPosition.NONE, cells_per_line: int = 40, lines_per_page: int = 25, space_char: str = " "):
        super().__init__()
        self._number_position = number_position
        self._cells_per_line = cells_per_line
        self._lines_per_page = lines_per_page
        self._space_char = space_char

    def _find_page_number(self, page_content: str) -> tuple[str, str]:
        if self._number_position:
            lines = page_content.splitlines()
            line_index = 0 if self._number_position.is_top() else (self._lines_per_page - 1)
            if len(lines) > line_index:
                line = lines[line_index]
                left = self._number_position.is_left()
                if left or len(line) >= self._cells_per_line:
                    parted = line.partition(self._space_char * 3) if left else line.rpartition(self._space_char * 3)
                    line, page_num = (parted[2].lstrip(self._space_char), parted[0]) if left else (parted[0].rstrip(self._space_char), parted[2])
                    if parted[1] and page_num:
                        lines[line_index] = line
                        return "\n".join(lines), page_num
        return page_content, ""

    def __call__(self, text: str, cursor: int, state: str, output_text: str) -> DetectionResult:
        if state == "StartBraillePage":
            end_of_page = text.find("\f", cursor)
            page_content, new_cursor = (text[cursor:end_of_page], end_of_page + 1) if end_of_page >= 0 else (
                text[cursor:], len(text))
            page_content, page_num = self._find_page_number(page_content)
            number_data = {"Number": page_num} if page_num else {}
            page_cmd = json.dumps({"BraillePage": number_data})
            output = f"\ue000{page_cmd}\ue001{page_content}"
            return DetectionResult(cursor=new_cursor, state=state, confidence=1.0, text=output_text + output)
        return DetectionResult(cursor + 1, state, 0.0, output_text + text[cursor])
