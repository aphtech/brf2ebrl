#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Some detectors common to multiple Braille codes/standards."""
import re
from enum import Enum, auto
from typing import Callable

from brf2ebrf.parser import DetectionResult, DetectionState, Detector

_ASCII_TO_UNICODE_DICT = str.maketrans(
    r""" A1B'K2L@CIF/MSP"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\0Z7(_?W]#Y)=""",
    "".join([chr(x) for x in range(0x2800, 0x2840)])
)


class BraillePageType(Enum):
    UNSET = 0
    T = auto()
    P = auto()
    NORMAL = auto()


def convert_ascii_to_unicode_braille_bulk(text: str, cursor: int, state: DetectionState,
                                          output_text: str) -> DetectionResult:
    """Convert the entire BRF into unicode Braille in a single step."""
    return DetectionResult(len(text), state, 1.0, output_text + translate_ascii_to_unicode_braille(text[cursor:]))


def translate_ascii_to_unicode_braille(text: str, check_cancelled: Callable[[], None] = lambda: None) -> str:
    return text.translate(_ASCII_TO_UNICODE_DICT)


def convert_ascii_to_unicode_braille(text: str, cursor: int, state: DetectionState,
                                     output_text: str) -> DetectionResult:
    """Convert only th next character to unicode Braille."""
    return DetectionResult(cursor + 1, state, 1.0, output_text + text[cursor].translate(_ASCII_TO_UNICODE_DICT))


def detect_and_pass_processing_instructions(text: str, cursor: int, state: DetectionState,
                                            output_text: str) -> DetectionResult | None:
    """Detect and pass through processing instructions"""
    if text.startswith("<?", cursor):
        end_of_pi = text.find("?>", cursor) + 2
        if end_of_pi >= 4:
            return DetectionResult(end_of_pi, state, confidence=0.9, text=output_text + text[cursor:end_of_pi])
    return None


_BRAILLE_PAGE_PI_RE = re.compile("<\\?braille-page (?P<braille_page_num>[\u2800-\u28ff]*)\\?>\n")
_PRINT_PAGE_RE = re.compile("<\\?print-page[ \u2800-\u28ff]*\\?>")


def braille_page_counter_detector(text: str, cursor: int, state: DetectionState,
                                  output_text: str) -> DetectionResult | None:
    """Detector to count Braille pages in the state."""
    if m := _BRAILLE_PAGE_PI_RE.match(text[cursor:]):
        prev_braille_page_type = state.get("braille_page_type", BraillePageType.UNSET)
        brl_page_num = m.group("braille_page_num")
        braille_page_type = BraillePageType.T if brl_page_num.startswith(
            "\u281e") else BraillePageType.P if brl_page_num.startswith(
            "\u280f") else BraillePageType.NORMAL if brl_page_num else prev_braille_page_type
        page_count = state.get("braille_page_count", 0) + 1 if prev_braille_page_type == braille_page_type else 1
        return DetectionResult(cursor + len(m.group()),
                               dict(state, braille_page_type=braille_page_type, braille_page_count=page_count,
                                    new_braille_page=True), 1.0, f"{output_text}{m.group()}")
    elif m := _PRINT_PAGE_RE.match(text[cursor:]):
        return DetectionResult(cursor=cursor + len(m.group()), state=state, confidence=1.0,
                               text=f"{output_text}{m.group()}")
    return None


_BLANK_LINE_RE = re.compile("\n{2,}")


def convert_blank_line_to_pi(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
    """Convert blank braille lines into pi for later use if needed"""
    return DetectionResult(len(text), state, 1.0,
                           output_text + _BLANK_LINE_RE.sub(lambda m: "<?blank-line?>".join(["\n"] * len(m.group())),
                                                            text[cursor:]))


def create_running_head_detector(min_indent: int) -> Detector:
    """Create a detector for running heads."""
    min_indent_re = re.compile(
        f"\u2800{{{min_indent},}}(?P<running_head>[\u2801-\u28ff][\u2800-\u28ff]*)(?P<eol>[\n\f])")

    def detect_running_head(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
        if state.get("new_braille_page", False) and state.get("braille_page_count", 0) != 1 and (
                m := min_indent_re.match(text[cursor:])):
            running_head = m.group("running_head")
            return DetectionResult(cursor + m.end(), dict(state, new_braille_page=False), 1.0,
                                   f"{output_text}<?running-head {running_head}?>{m.group('eol')}")
        next_page_index = text.find("<?braille-page", cursor)
        return DetectionResult(next_page_index, dict(state, new_braille_page=False), 1.0, output_text + text[
                                                                                                        cursor:next_page_index]) if next_page_index > cursor else DetectionResult(
            len(text), dict(state, new_braille_page=False), 1.0,
            output_text + text[cursor:]) if next_page_index < 0 else None

    return detect_running_head


_XHTML_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/strict.dtd">
<html xmlns="http://www.w3.org/TR/xhtml1/strict" >
<body>
"""

_XHTML_FOOTER = """</body>
</html>
"""


def xhtml_fixup_detector(input_text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    return DetectionResult(
        len(input_text), state, 1.0, f"{output_text}{_XHTML_HEADER}{input_text[cursor:]}{_XHTML_FOOTER}"
    )
