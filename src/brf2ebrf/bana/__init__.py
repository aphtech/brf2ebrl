"""BANA specific components for processing BRF."""
import json
from collections.abc import Callable
import string
from typing import Optional

from brf2ebrf.common import PageNumberPosition, PageLayout
from brf2ebrf.parser import DetectionResult, DetectionState, Detector

_BRL_WHITESPACE = string.whitespace + "\u2800"


def _find_page_number(
    page_content: str,
    number_position: PageNumberPosition,
    cells_per_line: int,
    lines_per_page: int,
    separator: str,
) -> tuple[str, str]:
    if number_position:
        lines = page_content.splitlines()
        line_index = 0 if number_position.is_top() else (lines_per_page - 1)
        if len(lines) > line_index:
            line = lines[line_index]
            left = number_position.is_left()
            if left or len(line) >= cells_per_line:
                parted = (
                    line.partition(separator) if left else line.rpartition(separator)
                )
                line, page_num = (
                    (parted[2].lstrip(_BRL_WHITESPACE), parted[0])
                    if left
                    else (parted[0].rstrip(_BRL_WHITESPACE), parted[2])
                )
                if parted[1] and page_num:
                    lines[line_index] = line
                    return "\n".join(lines), page_num
    return page_content, ""


def _create_braille_page_command(page_content: str, page_num: str) -> str:
    number_data = {"Number": page_num} if page_num else {}
    page_cmd = json.dumps({"BraillePage": number_data})
    output = f"\ue000{page_cmd}\ue001{page_content}"
    return output


def create_braille_page_detector(
    page_layout: PageLayout,
    separator: str = "   ",
    format_output: Callable[[str, str], str] = _create_braille_page_command,
) -> Detector:
    """Factory function to create a detector for Braille page numbers."""

    def detect_braille_page_number(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> Optional[DetectionResult]:
        if state.get("StartBraillePage", False):
            page_content = text[cursor:].split("\f")[0]
            new_cursor = cursor + len(page_content)
            page_content, page_num = _find_page_number(
                page_content,
                page_layout.braille_page_number,
                page_layout.cells_per_line,
                page_layout.lines_per_page,
                separator,
            )
            output = format_output(page_content, page_num)
            return DetectionResult(
                cursor=new_cursor, state=dict(state, StartBraillePage=False), confidence=1.0, text=output_text + output
            )
        if text.startswith("\f", cursor):
            return DetectionResult(
                cursor + 1,
                dict(state, StartBraillePage=True),
                confidence=1.0,
                text=output_text + text[cursor],
            )
        return None

    return detect_braille_page_number
