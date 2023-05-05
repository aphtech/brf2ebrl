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
    def __init__(self, number_position: PageNumberPosition = PageNumberPosition.NONE):
        super().__init__()
        self._number_position = number_position

    def _find_page_number(self, page_content: str, cells_per_line: int, lines_per_page: int) -> tuple[str, str]:
        if self._number_position:
            lines = page_content.splitlines()
            line_index = 0 if self._number_position.is_top() else (lines_per_page - 1)
            if len(lines) > line_index:
                line = lines[line_index]
                left = self._number_position.is_left()
                if left or len(line) >= cells_per_line:
                    parted = line.partition("  ") if left else line.rpartition("  ")
                    line, page_num = (parted[2].lstrip(), parted[0]) if left else (parted[0].rstrip(), parted[2])
                    if page_num:
                        lines[line_index] = line
                        return "\n".join(lines), page_num
        return page_content, ""

    def __call__(self, text: str, cursor: int, state: str, output_text: str, cells_per_line: int = 40,
                 lines_per_page: int = 25) -> DetectionResult:
        if state == "StartBraillePage":
            end_of_page = text.find("\f", cursor)
            page_content, new_cursor = (text[cursor:end_of_page], end_of_page + 1) if end_of_page >= 0 else (
                text[cursor:], len(text))
            page_content, page_num = self._find_page_number(page_content, cells_per_line, lines_per_page)
            number_data = {"Number": page_num} if page_num else {}
            page_cmd = json.dumps({"BraillePage": number_data})
            output = f"\ue000{page_cmd}\ue001{page_content}"
            return DetectionResult(cursor=new_cursor, state=state, confidence=1.0, text=output_text + output)
        return DetectionResult(cursor + 1, state, 0.0, output_text + text[cursor])
