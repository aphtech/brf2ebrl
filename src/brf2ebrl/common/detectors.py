#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Some detectors common to multiple Braille codes/standards."""
import logging
import re
from collections.abc import Iterable
from enum import Enum, auto

import lxml.etree
import lxml.html
from lxml.html.builder import HTML, BODY, HEAD, LINK

from brf2ebrl import ParserContext
from brf2ebrl.parser import DetectionResult, DetectionState, Detector

_ASCII_TO_UNICODE_DICT = str.maketrans(
    r""" A1B'K2L@CIF/MSP"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\0Z7(_?W]#Y)=""",
    "".join([chr(x) for x in range(0x2800, 0x2840)])
)


class BraillePageType(Enum):
    UNSET = 0
    T = auto()
    P = auto()
    NORMAL = auto()


def translate_ascii_to_unicode_braille(text: str, _: ParserContext = ParserContext()) -> str:
    return text.translate(_ASCII_TO_UNICODE_DICT)


def convert_ascii_to_unicode_braille(text: str, cursor: int, state: DetectionState,
                                     output_text: str) -> DetectionResult:
    """Convert only th next character to Unicode Braille."""
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
_BRAILLE_PPN_RE = re.compile("<\\?braille-ppn[ \u2800-\u28ff]*\\?>\n")
_PRINT_PAGE_RE = re.compile("<\\?print-page[ \u2800-\u28ff]*\\?>\n")


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
    elif m := _BRAILLE_PPN_RE.match(text[cursor:]):
        return DetectionResult(cursor=cursor + len(m.group()), state=state, confidence=1.0,
                               text=f"{output_text}{m.group()}")
    elif m := _PRINT_PAGE_RE.match(text[cursor:]):
        return DetectionResult(cursor=cursor + len(m.group()), state=state, confidence=1.0,
                               text=f"{output_text}{m.group()}")
    return None


_BLANK_LINE_RE = re.compile("\n{2,}")


def convert_blank_line_to_pi(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
    """Convert blank braille lines into pi for later use if needed"""
    return DetectionResult(len(text), state, 1.0,
                           output_text + convert_blank_lines_to_processing_instructions(text[cursor:], ParserContext()))


def convert_blank_lines_to_processing_instructions(text: str, _: ParserContext) -> str:
    return _BLANK_LINE_RE.sub(lambda m: "<?blank-line?>".join(["\n"] * len(m.group())),
                              text)


def create_running_head_detector(min_indent: int) -> Detector:
    """Create a detector for running heads."""
    min_indent_re = re.compile(
        f"\u2800{{{min_indent},}}(?P<running_head>[\u2801-\u28ff][\u2800-\u28ff]*)(?P<eol>[\n\f])")

    def detect_running_head(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
        page_can_have_runninghead = state.get("braille_page_count", 0) != 1 or state.get("braille_page_type", BraillePageType.UNSET) == BraillePageType.P
        if state.get("new_braille_page", False) and page_can_have_runninghead and (
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


def xhtml_fixup_detector(input_text: str, _: ParserContext) -> str:
    try:
        root = HTML(
            HEAD(
                LINK(rel="stylesheet", type="text/css", href="css/default.css")
            ),
            BODY(
                *(lxml.html.fragments_fromstring(input_text, parser=lxml.html.xhtml_parser))
            )
        )
    except Exception as e:
        raise ValueError("Parser has not created valid HTML.") from e
    lxml.etree.indent(root)
    heading_id = 1
    page_id = 1
    for element in root.iter():
        if "id" not in element.keys():
            if element.tag in ["h1","h2","h3", "h4", "h5", "h6"]:
                element.set("id", f"h_{heading_id}")
                heading_id += 1
            elif element.get("role") == "doc-pagebreak":
                element.set("id", f"page_{page_id}")
                page_id += 1
    return lxml.html.tostring(root, doctype="<!DOCTYPE html>", pretty_print=True, encoding="unicode", method="xml")

def combine_detectors(detectors: Iterable[Detector]) -> Detector:
    def apply(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
        for i, detector in enumerate(detectors):
            if result := detector(text, cursor, state, output_text):
                logging.debug("Selected index=%s detector=%s", i, detector)
                return result
        return None
    return apply
