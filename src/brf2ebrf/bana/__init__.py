"""BANA specific components for processing BRF."""
import json
import re
from collections.abc import Callable
import string

from brf2ebrf.common import PageNumberPosition, PageLayout
from brf2ebrf.parser import DetectionResult, DetectionState, Detector

_BRL_WHITESPACE = string.whitespace + "\u2800"


def _find_page_number(
        page_content: str,
        number_position: PageNumberPosition,
        cells_per_line: int,
        lines_per_page: int,
        separator: str,
        number_filter: Callable[[str], bool] = lambda n: True,
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
                if parted[1] and page_num and number_filter(page_num):
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
    braille_page_number_pattern = re.compile(
        "[\u280f\u281e]?\u283c[\u2801\u2803\u2809\u2819\u2811\u280b\u281b\u2813\u280a\u281a]+")

    def detect_braille_page_number(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        if state.get("StartBraillePage", False):
            page_content = text[cursor:].split("\f")[0]
            new_cursor = cursor + len(page_content)
            page_content, page_num = _find_page_number(
                page_content,
                page_layout.braille_page_number,
                page_layout.cells_per_line,
                page_layout.lines_per_page,
                separator,
                lambda n: bool(braille_page_number_pattern.fullmatch(n)),
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


_CONTINUATION_LETTERS = "\u2801\u2803\u2809\u2819\u2811\u280b\u281b\u2813\u280a\u281a\u2805\u2807\u280d\u281d\u2815\u280f\u281f\u2817\u280e\u281e\u2825\u2827\u283a\u282d\u283d\u2835"


def _convert_int_to_continuation_letter(x: int) -> str:
    """Creates the continuation letter string representing the integer value."""
    result = ""
    while letter := x % len(_CONTINUATION_LETTERS):
        result = _CONTINUATION_LETTERS[letter - 1] + result
        x = x // len(_CONTINUATION_LETTERS)
    return result


def _is_continuation_number(page_num: str, prev_page_num: str, continuation: int) -> bool:
    return prev_page_num and page_num == _convert_int_to_continuation_letter(continuation) + prev_page_num


_PRINT_PAGE_NUMBER_LINE_RE = re.compile("\u2824{5,}(?P<ppn>[\u2800-\u28ff]+)")


def _is_print_page_number_line(line: str) -> str | None:
    match = _PRINT_PAGE_NUMBER_LINE_RE.fullmatch(line)
    return match.group("ppn") if match else None


def create_print_page_detector(page_layout: PageLayout, separator: str = "\u2800" * 3) -> Detector:
    """Create a detector for print page numbers."""

    def detect_print_page_number(text: str, cursor: int, state: DetectionState,
                                 output_text: str) -> DetectionResult | None:
        if ord(text[cursor]) in range(0x2800, 0x2900):
            page_content = text[cursor:].partition("\f")[0]
            new_cursor = cursor + len(page_content)
            page_content, page_num = _find_page_number(page_content, page_layout.print_page_number,
                                                       page_layout.cells_per_line, page_layout.lines_per_page,
                                                       separator)
            s_ppn = state.get("ppn", "")
            s_cont = state.get("continuation", 0)
            result = ""
            if page_num:
                s_cont += 1
                if not _is_continuation_number(page_num, s_ppn, s_cont):
                    s_cont = 0
                    s_ppn = page_num
                    result += f"<?print-page {page_num}?>"
            lines = []
            for line in page_content.splitlines():
                if len(line) == page_layout.cells_per_line and (ppn := _is_print_page_number_line(line)):
                    s_ppn = ppn
                    s_cont = 0
                    lines.append(f"<?print-page {ppn}?>")
                else:
                    lines.append(line)
            result += "\n".join(lines)
            return DetectionResult(new_cursor, dict(state, ppn=s_ppn, continuation=s_cont), 0.9,
                                   f"{output_text}{result}")
        return None

    return detect_print_page_number
